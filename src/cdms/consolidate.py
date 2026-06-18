"""Asynchronous sleep-consolidation: the physical lifecycle of memory.

Triggered at a "rest boundary" (session end / terminal idle), this runs the five
algorithmic steps that turn a noisy episodic log into a compact, differentiated
identity:

    1. Flashbulb scar elevation   — pin crisis episodes as permanent guardrails
    2. Temporal eviction          — delete episodes that have decayed out of reach
    3. Hierarchical competition   — session- then epoch-level softmax to protect
                                    highlights from quiet periods
    4. Conserved-budget renorm    — SHY-style proportional downscaling to K_budget
    5. Mechanical tuple aggregation— geometry-only gist extraction (no LLM imagination)

Step 5 deliberately extracts structural invariants from the raw logs rather than
asking an LLM to "summarize", which would invite generative self-fiction. The
optional Dreamer LLM is used *only* to render prose at read time, never to author
the authoritative tuple.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

from .config import Config
from .db import Database
from .embeddings import Embedder, cosine, get_embedder
from .lock import cross_process_lock
from .models import Episodic, Gist, Scar, new_id, utc_now_iso
from .salience import (
    accessibility,
    age_days,
    allocate_capped_proportional,
    conserve_budget,
    hierarchical_competition,
)

# Harm OUTCOMES that, on their own, prove a catastrophe actually happened. Auto
# scar-elevation requires one of these (or a dangerous command that DID cause
# harm — see below). A negative-valence high-salience turn alone is NOT a crisis
# (a failed compile or "no results found" is routine). Pins go via pin_scar().
_CATASTROPHE_HARM = (
    "data loss", "lost data", "lost work", "overwrote", "wiped the",
    "dropped the database", "dropped table", "deleted the prod", "deleted production",
    "deleted the database", "prod is down", "production down", "production is down",
    "broke production", "broke main", "irreversible", "cannot recover",
    "could not recover", "corrupted the", "exposed credential",
    "exposed secret", "exposed the key", "leaked the secret", "leaked credential",
)

# Dangerous COMMANDS. Their mere presence is NOT a catastrophe — `git reset --hard
# to discard local edits` and `git push --force` are routine. They only elevate
# when the deed ALSO records actual harm (a harm token below). This was the
# Cycle-2 overcorrection: the regex/command tier matched the scary verb alone and
# auto-pinned benign-but-frustrating routine work as a permanent scar.
_DANGER_CMD = ("rm -rf", "force push", "force-push")
_CATASTROPHE_RE = re.compile(
    r"drop\s+(table|schema|database)"
    r"|truncate\s+table"
    r"|push\s+(--force|-f)\b|--force(-with-lease)?\b.*\bpush|\bpush\b.*--force"
    r"|reset\s+--hard"
    r"|delete\s+from\s+\w+\s*;?\s*$"
    r"|(credential|secret|token|api[_ ]?key|password)s?\b.*\b(git history|public repo|committed|pushed)"
    r"|committed\b.*\b(credential|secret|token|api[_ ]?key|password)",
    re.IGNORECASE,
)
# Tokens that indicate a dangerous command actually DID harm (vs. was used safely).
_HARM_TOKENS = (
    "lost", "wiped", "gone", "irreversible", "unrecoverable", "cannot recover",
    "could not recover", "destroyed", "overwrote", "overwritten", "deleted",
    "corrupted", "down", "outage", "leaked", "exposed", "by accident", "by mistake",
    "too late", "no backup",
)


def _matches_catastrophe(text: str) -> bool:
    low = text.lower()
    if any(m in low for m in _CATASTROPHE_HARM):
        return True
    danger = any(c in low for c in _DANGER_CMD) or bool(_CATASTROPHE_RE.search(text))
    return danger and any(h in low for h in _HARM_TOKENS)

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "of", "to", "in", "on",
    "for", "with", "is", "are", "was", "were", "be", "been", "it", "this", "that",
    "i", "you", "we", "they", "he", "she", "as", "at", "by", "from", "up", "out",
    "so", "do", "does", "did", "not", "no", "yes", "can", "will", "would", "should",
    "have", "has", "had", "get", "got", "use", "used", "using", "run", "ran",
    "file", "files", "code", "line", "lines", "add", "added", "set", "new", "now",
    "make", "made", "want", "need", "like", "just", "also", "into", "out", "your",
    "what", "when", "where", "which", "how", "why", "all", "any", "more", "some",
    # generic dev/outcome filler that must not become a gist "object"
    "work", "working", "about", "cleanly", "correctly", "green", "red", "agreement",
    "workflow", "convention", "working", "note", "noted", "remember", "every",
    "before", "after", "small", "issue", "log", "exception", "build", "commit",
    "passed", "failed", "works", "correct", "updated", "update", "thing", "stuff",
    # conversational + transcript/tool-call filler seen on real Claude Code logs
    "let", "lets", "session", "activity", "assistant", "turn", "tool", "file_path",
    "started", "going", "looks", "good", "okay", "yeah", "sure", "please",
}


@dataclass
class ConsolidationReport:
    scars_created: int = 0
    episodes_evicted: int = 0
    deduped: int = 0
    gists_created: int = 0
    gists_reinforced: int = 0
    gists_flipped: int = 0
    gists_decayed: int = 0
    episodes_remaining: int = 0
    clusters: int = 0
    skipped: bool = False
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "scars_created": self.scars_created,
            "episodes_evicted": self.episodes_evicted,
            "deduped": self.deduped,
            "gists_created": self.gists_created,
            "gists_reinforced": self.gists_reinforced,
            "gists_flipped": self.gists_flipped,
            "gists_decayed": self.gists_decayed,
            "episodes_remaining": self.episodes_remaining,
            "clusters": self.clusters,
            "notes": self.notes,
        }


class Consolidator:
    def __init__(self, cfg: Config, db: Database | None = None, embedder: Embedder | None = None):
        self.cfg = cfg
        self.db = db or Database(cfg)
        self.embedder = embedder or get_embedder(cfg)

    def run(self, now: datetime | None = None) -> ConsolidationReport:
        # Serialize the whole pass across processes. Two concurrent consolidations
        # (hook + cron + daemon on the shared store) otherwise produce duplicate
        # gists, lose/double-count the decay cycle counter, and a concurrent forget
        # can be undone by a pass rebuilding gists from episodes it is deleting. If
        # another pass is already running we SKIP (a second pass is redundant work
        # on a moving set) rather than block a hook past its timeout.
        try:
            with cross_process_lock(self.cfg.lock_path):
                return self._run_locked(now)
        except TimeoutError:
            rep = ConsolidationReport()
            rep.skipped = True
            rep.notes.append("skipped: another consolidation/forget pass holds the lock")
            # A1-M1: a skip was previously silent (log file only). Record a durable,
            # operator-visible signal — a counter + last-skip timestamp in meta (surfaced
            # by `cdms stats`) and a stderr warning — so repeated skips (a wedged
            # consolidation/forget) are noticeable instead of invisibly stalling identity.
            n = -1
            try:
                n = int(self.db.get_meta("consolidations_skipped", "0") or "0") + 1
                self.db.set_meta("consolidations_skipped", n)
                self.db.set_meta("last_consolidation_skip", utc_now_iso())
            except Exception:
                pass
            print(f"cdms: consolidation skipped (lock busy); total skipped={n}. "
                  f"Repeated skips may mean a consolidation/forget is wedged.", file=sys.stderr)
            return rep

    def _run_locked(self, now: datetime | None = None) -> ConsolidationReport:
        now = now or datetime.now(timezone.utc)
        rep = ConsolidationReport()
        # Verify the embedder's vector space matches the store before writing any
        # gist/scar vectors (refuses to mix hash- and model-space embeddings).
        self.db.reconcile_embedder(self.embedder.fingerprint())

        # Compute the consolidation-cycle counter (gist decay is measured in these
        # cycles, NOT wall-clock — so being away never ages identity). The counter
        # is PERSISTED at the very end, after the pass succeeds: consolidation is
        # not atomic across its steps, so advancing it up-front meant a crash mid-
        # pass aged the decay clock without reinforcing this cycle's gists, eroding
        # identity over repeated interruptions. Persisting last makes a crashed pass
        # a no-op for the decay clock.
        cycle = int(self.db.get_meta("cycle", "0") or "0") + 1

        # Load the live episodic set ONCE (in rowid order) and track removals in
        # memory, instead of re-materializing the whole table after every step
        # (the dominant consolidation cost at scale was 5x all_episodic() loads).
        # In-memory filtering preserves the exact rowid order, so clustering/dedup
        # behaviour is identical to the prior re-query approach.
        episodes = self.db.all_episodic()
        remaining = 0
        if episodes:
            removed = self._elevate_scars(episodes, rep)
            episodes = [e for e in episodes if e.id not in removed]

            deduped = self._dedup(episodes, rep)
            episodes = [e for e in episodes if e.id not in deduped]

            evicted = self._evict(episodes, now, rep)
            episodes = [e for e in episodes if e.id not in evicted]

            self._compete_and_renormalize(episodes, rep)  # mutates DB salience only
            self._aggregate_gists(episodes, rep, now, cycle)  # uses vecs/valence, not salience
            remaining = len(episodes)
        else:
            rep.notes.append("no episodic memories; gist maintenance only")

        # Gentle activity-based L2 decay (only fades traits idle across many cycles).
        # NOTE (Cycle-3 X2, characterized tradeoff, NOT changed): one consolidation ==
        # one decay cycle, by design — this is the activity clock that makes wall-clock
        # absence harmless. An adversary who can force many rapid empty consolidations
        # can therefore age the clock; that requires the privileged ability to invoke
        # consolidation repeatedly, and gating advancement on "real work" would break
        # the validated invariant (see test_absence_does_not_age_identity + the drift
        # EROSION control). Documented in REDTEAM_FINDINGS, deliberately not "fixed".
        self._decay_gists(rep, cycle)

        # Persist the advanced cycle counter only now that the pass has completed.
        self.db.set_meta("cycle", cycle)

        rep.episodes_remaining = remaining
        return rep

    # -- Step 1: Flashbulb scar elevation ---------------------------------- #
    def _is_catastrophe(self, e: Episodic) -> bool:
        """True if a genuine crisis actually HAPPENED — the marker must be in what was
        DONE or what RESULTED (action_taken / outcome_feedback), not the trigger.

        Scanning the deed/result (not the prompt) excludes both casual discussion
        ("explain why rm -rf is dangerous") and emotional-but-false beliefs ("I think
        I deleted prod!" → outcome: "false alarm"). The catastrophe matcher combines
        the literal lexicon with a regex tier so verb-order/phrasing variants
        ("git push --force", "DROP SCHEMA", credentials in git history) are caught —
        fixing the brittle false-negatives without reintroducing the trigger-path
        false-positives. A real disaster narrated only in the trigger should be
        pinned deliberately via `store kind=scar`.
        """
        return _matches_catastrophe(f"{e.action_taken}\n{e.outcome_feedback}")

    def _elevate_scars(self, episodes: list[Episodic], rep: ConsolidationReport) -> set[str]:
        removed: set[str] = set()
        for e in episodes:
            if (self._is_catastrophe(e)
                    and e.valence <= self.cfg.crisis_valence_max
                    and e.base_salience >= self.cfg.crisis_threshold):
                scar = Scar(
                    id=new_id("scar"),
                    crisis_trigger=e.trigger_prompt[:500],
                    remediation_rule=(e.outcome_feedback or e.action_taken)[:500],
                    project=e.project,
                    origin="elevated",
                )
                emb = self.db.get_embedding("episodic", e.id)
                if emb is None:
                    emb = self.embedder.embed_one(scar.search_text())
                # Dedup: a recurring catastrophe (same near-identical deed/project)
                # must not mint a fresh permanent scar every cycle. If one already
                # exists, consume the episode (promote it out of episodic) without
                # adding a duplicate L3 row.
                if self.db.find_duplicate_scar(emb, e.project, self.cfg.scar_dedup_sim_threshold) is not None:
                    self.db.delete_episodic([e.id])
                    removed.add(e.id)
                    continue
                self.db.insert_scar(scar, emb)
                self.db.delete_episodic([e.id])
                removed.add(e.id)
                rep.scars_created += 1
        return removed

    # -- Step 2a: Deduplication / supersession ----------------------------- #
    def _dedup(self, episodes: list[Episodic], rep: ConsolidationReport) -> set[str]:
        if not episodes:
            return set()
        vecs = self._embeddings_for(episodes)
        # Vectorized: compare each episode to all survivors via one matmul (embeddings
        # are unit-norm, so dot == cosine). Survivors live in a preallocated matrix to
        # avoid O(n^2) Python cosine calls — this scales to tens of thousands of turns.
        dim = int(vecs[0].shape[0])
        keep_mat = np.empty((len(episodes), dim), dtype=np.float32)
        keep_e: list[Episodic] = []
        to_delete: list[str] = []
        thr = self.cfg.dedup_sim_threshold
        m = 0
        for e, v in zip(episodes, vecs):
            v = np.asarray(v, dtype=np.float32)
            if m > 0:
                sims = keep_mat[:m] @ v
                j = int(np.argmax(sims))
                if float(sims[j]) >= thr:
                    # supersede: fold access + salience into the survivor, drop the dup.
                    # Fold the dup's FULL access_count (not just +1) so the survivor keeps
                    # the merged reinforcement history (Cycle-5 C-MED-1).
                    survivor = self.db.get_episodic(keep_e[j].id)
                    if survivor is not None:
                        merged = max(survivor.base_salience, e.base_salience)
                        self.db.set_salience([(survivor.id, merged)])
                        self.db.bump_access(survivor.id, max(1, e.access_count), survivor.timestamp)
                    to_delete.append(e.id)
                    continue
            keep_mat[m] = v
            keep_e.append(e)
            m += 1
        if to_delete:
            rep.deduped = self.db.delete_episodic(to_delete)
        return set(to_delete)

    # -- Step 2: Temporal eviction ----------------------------------------- #
    def _evict(self, episodes: list[Episodic], now: datetime, rep: ConsolidationReport) -> set[str]:
        doomed: list[str] = []
        for e in episodes:
            acc = accessibility(e.base_salience, age_days(e.timestamp, now), e.access_count, self.cfg)
            if acc < self.cfg.retention_floor:
                doomed.append(e.id)
        rep.episodes_evicted = self.db.delete_episodic(doomed)
        return set(doomed)

    # -- Step 3 + 4: Competition then conserved-budget renormalization ----- #
    def _compete_and_renormalize(self, episodes: list[Episodic], rep: ConsolidationReport) -> None:
        if not episodes:
            return
        # Step 3: hierarchical softmax competition over sessions / epoch.
        grouped: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for e in episodes:
            grouped[e.session_id or "_"].append((e.id, e.base_salience))
        comp = hierarchical_competition(grouped)
        # Fold competition score in multiplicatively (winners retain more salience).
        boosted = {e.id: e.base_salience * (0.5 + comp.get(e.id, 0.0)) for e in episodes}
        proj_of = {e.id: (e.project or "_") for e in episodes}

        # Step 4: capped per-project budget — allocate K across projects with a cap
        # (so a busy primary keeps focus without starving the others), then SHY-style
        # proportional renormalization WITHIN each project to its allocated share.
        proj_weight: dict[str, float] = defaultdict(float)
        for eid, s in boosted.items():
            proj_weight[proj_of[eid]] += s
        alloc = allocate_capped_proportional(
            dict(proj_weight), self.cfg.salience_budget, self.cfg.project_budget_cap)

        updates: list[tuple[str, float]] = []
        for proj, share in alloc.items():
            members = [eid for eid in boosted if proj_of[eid] == proj]
            renorm = conserve_budget([boosted[eid] for eid in members], share)
            updates.extend(zip(members, renorm))
        self.db.set_salience(updates)
        rep.notes.append(
            f"capped per-project budget (cap={self.cfg.project_budget_cap:.0%}): "
            f"{len(alloc)} project(s) -> K={self.cfg.salience_budget:g}")

    # -- Step 5: Mechanical tuple aggregation (gist extraction) ------------ #
    def _aggregate_gists(self, episodes: list[Episodic], rep: ConsolidationReport,
                         now: datetime, cycle: int) -> None:
        if len(episodes) < self.cfg.min_cluster_support:
            return
        now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        vecs = self._embeddings_for(episodes)
        ema = self.cfg.gist_valence_ema

        # Partition episodes by project BEFORE clustering. all_episodic() spans every
        # project, so an unpartitioned clustering pass merges episodes from different
        # projects into one gist (cross-project identity contamination: project A's
        # failures flipped project B's trait). Clustering, identity, and the gist's
        # project column are all scoped per project here.
        by_project: dict[str, list[tuple[Episodic, np.ndarray]]] = defaultdict(list)
        for e, v in zip(episodes, vecs):
            by_project[e.project or ""].append((e, v))

        total_clusters = 0
        for proj, items in by_project.items():
            if len(items) < self.cfg.min_cluster_support:
                continue
            clusters = self._greedy_cluster(items)
            total_clusters += len(clusters)
            self._gists_from_clusters(clusters, proj, rep, now_iso, cycle, ema)
        rep.clusters = total_clusters

    def _gists_from_clusters(self, clusters, proj, rep, now_iso, cycle, ema) -> None:
        for members in clusters:
            if len(members) < self.cfg.min_cluster_support:
                continue
            tuple_ = self._extract_tuple(members)
            if tuple_ is None:
                continue
            subject, _relation, object_, valence = tuple_
            centroid = self._centroid([v for _e, v in members])

            # Identity resolution (fixes gist proliferation over time): try the exact
            # (subject, object, project) key first, then fall back to the nearest
            # EXISTING gist of this subject+project by episode-space centroid. Top-2
            # term selection is noisy — near-tied frequencies reshuffle the object
            # string cycle-to-cycle and vocabulary drifts — so a literal-string key
            # alone shatters one topic into many siblings that never accrue support.
            existing = self.db.find_gist_by_so(subject, object_, proj)
            if existing is None:
                existing = self._match_gist_by_embedding(subject, centroid, object_, proj)
            if existing:
                # The relation is DERIVED from a running valence, so new contradicting
                # evidence can FLIP the trait. Continuity is carried by the stable gist
                # id; the human-readable OBJECT label is refreshed to track current
                # content (a frozen label went stale — e.g. still saying "login oauth"
                # for work that had drifted entirely to billing). The centroid blend is
                # support-WEIGHTED so an established trait's location moves slowly
                # (anti identity-creep) rather than chasing the latest cluster 50/50.
                old_relation = existing.relation
                old_support = max(1, existing.support_count)
                existing.frequency += 1
                existing.support_count = max(existing.support_count, len(members))
                existing.survived_cycles += 1
                existing.valence = (1 - ema) * existing.valence + ema * valence
                existing.relation = self.cfg.relation_from_valence(existing.valence)
                existing.object = object_
                existing.last_reinforced = now_iso
                existing.last_cycle = cycle
                old_c = self.db.get_gist_centroid(existing.id)
                blended = centroid if old_c is None else self._blend_centroid(
                    old_c, old_support, centroid, len(members))
                emb = self.embedder.embed_one(existing.search_text())
                self.db.insert_gist(existing, emb, blended)
                rep.gists_reinforced += 1
                if existing.relation != old_relation:
                    rep.gists_flipped += 1
                gid = existing.id
            else:
                relation = self.cfg.relation_from_valence(valence)
                g = Gist(id=new_id("gist"), subject=subject, relation=relation, object=object_,
                         valence=valence, frequency=1, support_count=len(members),
                         project=proj, last_reinforced=now_iso, last_cycle=cycle)
                emb = self.embedder.embed_one(g.search_text())
                self.db.insert_gist(g, emb, centroid)
                rep.gists_created += 1
                gid = g.id
            # traceable support edges L1 -> L2
            for e, _v in members:
                self.db.add_support_edge(e.id, gid)

    # -- Step 6: Gentle activity-based L2 decay (plasticity) --------------- #
    def _decay_gists(self, rep: ConsolidationReport, cycle: int) -> None:
        """Disused traits fade — but only through ACTIVE consolidation cycles in
        which they are never reinforced, never through wall-clock absence. A gist's
        effective strength = support * decay_per_cycle ^ (idle cycles). Below the
        floor it is forgotten. Heavily-supported / recently-reinforced traits
        persist for hundreds of idle cycles (continuity); identity is not lost just
        because the user stepped away from the keyboard."""
        doomed: list[str] = []
        for g in self.db.all_gist():
            idle = max(0, cycle - g.last_cycle)
            strength = g.support_count * (self.cfg.gist_decay_per_cycle ** idle)
            if strength < self.cfg.gist_retention_floor:
                doomed.append(g.id)
        if doomed:
            rep.gists_decayed = self.db.delete_gist(doomed)

    def _greedy_cluster(self, items: list[tuple[Episodic, np.ndarray]]) -> list[list[tuple[Episodic, np.ndarray]]]:
        # Greedy single-pass clustering against running centroid means. Vectorized:
        # each item's similarity to all current centroids is one matmul (centroids are
        # means, hence not unit-norm, so divide by their norms to get cosine). Behaviour
        # is identical to the per-item Python loop, but O(n) matmuls instead of O(n*k)
        # Python cosine calls.
        clusters: list[list[tuple[Episodic, np.ndarray]]] = []
        n = len(items)
        if n == 0:
            return clusters
        dim = int(items[0][1].shape[0])
        cent = np.empty((n, dim), dtype=np.float32)   # running per-cluster mean
        counts = np.zeros(n, dtype=np.float32)
        thr = self.cfg.cluster_sim_threshold
        k = 0
        for e, v in items:
            v = np.asarray(v, dtype=np.float32)
            if k > 0:
                C = cent[:k]
                norms = np.linalg.norm(C, axis=1)
                norms[norms == 0.0] = 1.0
                sims = (C @ v) / norms                # v is unit-norm -> this is cosine
                j = int(np.argmax(sims))
                if float(sims[j]) >= thr:
                    clusters[j].append((e, v))
                    counts[j] += 1.0
                    cent[j] += (v - cent[j]) / counts[j]   # incremental mean (== np.mean of members)
                    continue
            clusters.append([(e, v)])
            cent[k] = v
            counts[k] = 1.0
            k += 1
        return clusters

    def _extract_tuple(self, members: list[tuple[Episodic, np.ndarray]]) -> tuple[str, str, str, float] | None:
        """Geometry-first, lexicon-only SRO extraction (no generative imagination).

        Subject  = the stable entity (project/workspace).
        Object   = the cluster's dominant content term(s).
        Relation = derived from the cluster's mean affect sign (outcome valence).
        """
        eps = [e for e, _ in members]
        valence = float(np.mean([e.valence for e in eps]))

        # Object terms come from what the work is ABOUT (trigger + action), not the
        # outcome — outcomes are full of generic success/failure boilerplate that
        # would otherwise leak in as spurious objects.
        counts: dict[str, int] = defaultdict(int)
        for e in eps:
            for tok in _content_terms(f"{e.trigger_prompt} {e.action_taken}"):
                counts[tok] += 1
        if not counts:
            return None
        # Pick up to two dominant terms, skipping singular/plural duplicates of an
        # already-chosen term ("tiles"/"tile" -> one) so objects read cleanly.
        picked: list[str] = []
        for tok, _c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            if any(tok == p or tok == p + "s" or p == tok + "s" for p in picked):
                continue
            picked.append(tok)
            if len(picked) == 2:
                break
        object_ = " ".join(picked)
        if not object_:
            return None

        subject = (eps[0].project.replace("\\", "/").rstrip("/").split("/")[-1] or "workspace")
        relation = self.cfg.relation_from_valence(valence)
        return subject, relation, object_, valence

    @staticmethod
    def _centroid(vecs: list[np.ndarray]) -> np.ndarray:
        """Unit-norm mean of episode vectors — the cluster's location in embedding
        space, used as a vocabulary-independent identity for the gist."""
        m = np.mean(np.stack([np.asarray(v, dtype=np.float32) for v in vecs]), axis=0)
        n = float(np.linalg.norm(m))
        return (m / n).astype(np.float32) if n > 0.0 else m.astype(np.float32)

    @staticmethod
    def _blend_centroid(old_c: np.ndarray, w_old: float,
                        new_c: np.ndarray, w_new: float) -> np.ndarray:
        """Support-weighted blend of an existing gist centroid with a new cluster's,
        so a heavily-supported trait's location drifts slowly (resists identity-creep)
        while a lightly-supported one still adapts."""
        m = w_old * np.asarray(old_c, dtype=np.float32) + w_new * np.asarray(new_c, dtype=np.float32)
        n = float(np.linalg.norm(m))
        return (m / n).astype(np.float32) if n > 0.0 else m.astype(np.float32)

    def _match_gist_by_embedding(self, subject: str, centroid: np.ndarray,
                                 object_: str, project: str = "") -> Gist | None:
        """Nearest existing gist of ``(subject, project)`` that is the SAME trait
        under a reshuffled/overlapping object label.

        Two guards must BOTH hold, because neither is sufficient alone under a
        weak (e.g. hashing) embedder: (1) the episode-space centroid is within the
        match threshold (unit-norm, so dot == cosine), and (2) the object labels
        share at least one content term. Centroid-alone over-merges distinct
        sub-traits that share project vocabulary (collapsing differentiation);
        term-overlap-alone merges unrelated traits that share a common word. The
        conjunction merges only genuine reshuffles of one topic (e.g. {parser,
        lexer} vs {parser,grammar}) while keeping distinct traits separate.
        """
        new_terms = set(object_.split())
        if not new_terms:
            return None
        best: Gist | None = None
        best_sim = self.cfg.gist_match_sim_threshold
        for g, gc in self.db.gist_centroids(subject, project):
            if not (new_terms & set(g.object.split())):
                continue  # no shared object term -> a distinct trait, never merge
            sim = float(np.dot(centroid, gc))
            if sim >= best_sim:
                best_sim = sim
                best = g
        return best

    # -- helpers ----------------------------------------------------------- #
    def _embeddings_for(self, episodes: list[Episodic]) -> list[np.ndarray]:
        have = self.db.get_embeddings_bulk([e.id for e in episodes])  # one query, not N
        vecs: list[np.ndarray] = []
        for e in episodes:
            v = have.get(e.id)
            if v is None:
                v = self.embedder.embed_one(e.search_text())
            vecs.append(np.asarray(v, dtype=np.float32))
        return vecs

    def close(self) -> None:
        self.db.close()


def _content_terms(text: str) -> list[str]:
    out = []
    for raw in "".join(c.lower() if (c.isalnum() or c in "._/-") else " " for c in text).split():
        tok = raw.strip("._/-")
        if len(tok) > 2 and tok not in _STOPWORDS and not tok.isdigit():
            out.append(tok)
    return out
