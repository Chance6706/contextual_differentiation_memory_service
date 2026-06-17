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

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

from .config import Config
from .db import Database
from .embeddings import Embedder, cosine, get_embedder
from .models import Episodic, Gist, Scar, new_id
from .salience import (
    accessibility,
    age_days,
    allocate_capped_proportional,
    conserve_budget,
    hierarchical_competition,
)

# Genuine catastrophe markers. Auto scar-elevation requires one of these — a
# negative-valence high-salience turn alone is NOT a crisis (a failed compile or
# "no results found" is routine). Deliberate pins go through pin_scar() instead.
_CATASTROPHE = (
    "data loss", "lost data", "lost work", "rm -rf", "force push", "force-push",
    "overwrote", "wiped the", "dropped the database", "dropped table",
    "deleted the prod", "deleted production", "deleted the database",
    "prod is down", "production down", "production is down",
    "broke production", "broke main", "irreversible", "cannot recover",
    "could not recover", "corrupted the", "exposed credential",
    "exposed secret", "exposed the key", "leaked the secret", "leaked credential",
)

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
        now = now or datetime.now(timezone.utc)
        rep = ConsolidationReport()
        # Verify the embedder's vector space matches the store before writing any
        # gist/scar vectors (refuses to mix hash- and model-space embeddings).
        self.db.reconcile_embedder(self.embedder.fingerprint())

        # Advance the consolidation-cycle counter. Gist decay is measured in these
        # cycles (activity), NOT wall-clock — so being away never ages identity.
        cycle = int(self.db.get_meta("cycle", "0") or "0") + 1
        self.db.set_meta("cycle", cycle)

        episodes = self.db.all_episodic()
        if episodes:
            self._elevate_scars(episodes, rep)
            episodes = self.db.all_episodic()  # refresh after scar removal

            self._dedup(episodes, rep)
            episodes = self.db.all_episodic()

            evicted = self._evict(episodes, now, rep)
            episodes = [e for e in episodes if e.id not in evicted]

            self._compete_and_renormalize(episodes, rep)
            episodes = self.db.all_episodic()

            self._aggregate_gists(episodes, rep, now, cycle)
        else:
            rep.notes.append("no episodic memories; gist maintenance only")

        # Gentle activity-based L2 decay (only fades traits idle across many cycles).
        self._decay_gists(rep, cycle)

        rep.episodes_remaining = len(self.db.all_episodic())
        return rep

    # -- Step 1: Flashbulb scar elevation ---------------------------------- #
    def _elevate_scars(self, episodes: list[Episodic], rep: ConsolidationReport) -> None:
        for e in episodes:
            # A scar requires a genuine catastrophe signal AND negative valence AND
            # high salience. Routine failures (failed compiles, "no results") are
            # negative+salient but are NOT crises — they must not be auto-pinned.
            #
            # Critically, the catastrophe marker must appear in what was actually
            # DONE or what actually HAPPENED (action_taken / outcome_feedback), not
            # in the trigger_prompt. Otherwise mere discussion ("explain why rm -rf
            # is dangerous", "the docs warn force push can cause data loss") gets
            # permanently pinned — a false-positive that floods L3 and (via the
            # SessionStart cap) can evict real guardrails. The deed/result is the
            # reliable crisis signal; the question that prompted it is not.
            deed = f"{e.action_taken}\n{e.outcome_feedback}".lower()
            is_catastrophe = any(m in deed for m in _CATASTROPHE)
            if (is_catastrophe
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
                self.db.insert_scar(scar, emb)
                self.db.delete_episodic([e.id])
                rep.scars_created += 1

    # -- Step 2a: Deduplication / supersession ----------------------------- #
    def _dedup(self, episodes: list[Episodic], rep: ConsolidationReport) -> None:
        vecs = self._embeddings_for(episodes)
        if not episodes:
            return
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
                    # supersede: fold access + salience into the survivor, drop the dup
                    survivor = self.db.get_episodic(keep_e[j].id)
                    if survivor is not None:
                        merged = max(survivor.base_salience, e.base_salience)
                        self.db.set_salience([(survivor.id, merged)])
                        self.db.touch_episodic(survivor.id, survivor.timestamp)
                    to_delete.append(e.id)
                    continue
            keep_mat[m] = v
            keep_e.append(e)
            m += 1
        if to_delete:
            rep.deduped = self.db.delete_episodic(to_delete)

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
        clusters = self._greedy_cluster(list(zip(episodes, vecs)))
        rep.clusters = len(clusters)
        ema = self.cfg.gist_valence_ema

        for members in clusters:
            if len(members) < self.cfg.min_cluster_support:
                continue
            tuple_ = self._extract_tuple(members)
            if tuple_ is None:
                continue
            subject, _relation, object_, valence = tuple_
            existing = self.db.find_gist_by_so(subject, object_)
            if existing:
                # Gists are keyed on (subject, object); the relation is DERIVED from a
                # running valence, so new contradicting evidence can FLIP the trait.
                old_relation = existing.relation
                existing.frequency += 1
                existing.support_count = max(existing.support_count, len(members))
                existing.survived_cycles += 1
                existing.valence = (1 - ema) * existing.valence + ema * valence
                existing.relation = self.cfg.relation_from_valence(existing.valence)
                existing.last_reinforced = now_iso
                existing.last_cycle = cycle
                emb = self.embedder.embed_one(existing.search_text())
                self.db.insert_gist(existing, emb)
                rep.gists_reinforced += 1
                if existing.relation != old_relation:
                    rep.gists_flipped += 1
                gid = existing.id
            else:
                relation = self.cfg.relation_from_valence(valence)
                g = Gist(id=new_id("gist"), subject=subject, relation=relation, object=object_,
                         valence=valence, frequency=1, support_count=len(members),
                         project=members[0][0].project, last_reinforced=now_iso, last_cycle=cycle)
                emb = self.embedder.embed_one(g.search_text())
                self.db.insert_gist(g, emb)
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

    # -- helpers ----------------------------------------------------------- #
    def _embeddings_for(self, episodes: list[Episodic]) -> list[np.ndarray]:
        vecs: list[np.ndarray] = []
        for e in episodes:
            v = self.db.get_embedding("episodic", e.id)
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
