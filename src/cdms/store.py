"""The Ego runtime: read and write paths over the three-tier store.

This is where the database, the CPU embedder, and the cognitive maths meet:

* :meth:`MemoryService.ingest` — the write path. Computes surprisal-gated
  salience S0, writes the episode, and applies a local associative boost to
  related faded memories.
* :meth:`MemoryService.retrieve` — the read path. Hybrid (vector + keyword)
  recall fused with Reciprocal Rank Fusion, filtered and weighted by Ebbinghaus
  accessibility, with retrieval-induced reinforcement written back.

Because Claude Code is a closed hosted model, we cannot read its logit entropy
(the spec's ``H(p)`` uncertainty gate). We therefore approximate the salience
drivers from signals the lifecycle hooks *can* observe: embedding novelty,
deterministic tool outcomes, self-reference patterns, and affect lexicon.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional

from .config import Config
from .db import Database
from .embeddings import Embedder, get_embedder
from .models import Episodic, Gist, Scar, SearchHit, new_id, utc_now_iso
from .salience import (
    SalienceSignals,
    accessibility,
    age_days,
    associative_boost,
    compute_s0,
)

# Cross-tier ranking weights: scars (pinned guardrails) outrank consolidated gist,
# which outranks raw episodic recall.
_TIER_WEIGHT = {"scar": 3.0, "gist": 1.6, "episodic": 1.0}

# NEVER-AUTHORS-A-SELF-TUPLE (Bem firewall, code-enforced 2026-06-25). The model must never persist a
# fact whose SUBJECT is the assistant/itself — that is the one residual write-to-self channel a
# pressure-test found: consolidation already forces subject=project, but the MCP store(kind="fact") tool
# lets a model supply an arbitrary subject straight into upsert_fact. A self-subject gist renders verbatim
# into the persona block ("claude handles well X"), so we refuse it at the write choke point. This is a
# DENYLIST of direct self-references (normalized) — it closes the obvious hole; it is NOT a complete
# semantic guard against deliberate paraphrase ("this AI engineer"), and any such write would still render
# visibly anomalous in the persona block + observer. "you"/"user" are NOT self (they are the human) and are
# intentionally allowed. A project literally named "claude" is unaffected: consolidation (not upsert_fact)
# mints project-subject gists, so this guard only touches the model-supplied MCP path.
_SELF_SUBJECTS = frozenset({
    "i", "me", "my", "mine", "myself", "self", "yourself",
    "assistant", "the assistant", "an assistant", "this assistant", "your assistant",
    "ai", "the ai", "an ai", "this ai", "the ai assistant",
    "model", "the model", "this model", "the assistant model", "language model", "the language model",
    "claude", "i claude", "claude the assistant",
})


def _is_self_subject(subject: str) -> bool:
    """True if `subject` is a direct self/assistant reference (normalized: lowercased, punctuation->space,
    whitespace collapsed). Used to refuse model-authored facts about the assistant itself."""
    s = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (subject or "").lower())).strip()
    return s in _SELF_SUBJECTS

_NEG_AFFECT = {
    "error", "errors", "fail", "failed", "failure", "crash", "crashed", "broke",
    "broken", "wrong", "bug", "exception", "denied", "conflict", "regression",
    "panic", "fatal", "abort", "timeout", "corrupt", "lost", "danger",
}
_POS_AFFECT = {
    "success", "succeeded", "passed", "pass", "fixed", "works", "working",
    "resolved", "done", "great", "correct", "green", "clean", "merged",
}
_SELF_REF = {
    "claude.md", "instruction", "instructions", "rule", "rules", "prefer",
    "preference", "always", "never", "remember", "convention", "policy",
    "guideline", "you should", "do not", "don't", "must", "from now on",
}
_CONTINGENT_TOOLS = {"bash", "edit", "write", "multiedit", "notebookedit", "applypatch"}

# Secret patterns redacted at capture time. Tool output (e.g. an `env` dump) can
# carry live credentials; without this they would be persisted to plaintext
# SQLite and re-injected into context at every SessionStart indefinitely. This is
# a best-effort scrubber for the common high-signal shapes, not a guarantee.
_SECRET_PATTERNS = [
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                       # AWS access key id
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),  # GitHub tokens
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),           # Slack tokens
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),                    # OpenAI-style keys
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"),                # Anthropic (hyphens break the sk- rule above)
    re.compile(r"\bsk-(?:proj|svcacct|admin)-[A-Za-z0-9_-]{20,}"),  # OpenAI project/service keys (hyphenated)
    re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),                 # Google API key
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),  # JWT
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
               re.DOTALL),
    # Azure storage connection string: keep the AccountKey= name, redact the value.
    re.compile(r"(?i)\b(AccountKey)=([A-Za-z0-9+/=]{20,})"),
    # KEY/SECRET/TOKEN/PASSWORD assignments: redact the value, keep the name.
    # Quantifiers BOUNDED ({0,64}) so the name-prefix/suffix around the keyword cannot
    # drive catastrophic backtracking on adversarial input even if length-clipping is ever
    # bypassed (Cycle-5 C-MED-5); 64 chars is far longer than any real env-var name.
    re.compile(r"(?i)\b([A-Z0-9_]{0,64}(?:SECRET|TOKEN|PASSWORD|PASSWD|PWD|API[_-]?KEY|ACCESS[_-]?KEY)"
               r"[A-Z0-9_]{0,64})\s*[=:]\s*['\"]?([^\s'\"]{6,})"),
]


def redact_secrets(text: str) -> str:
    """Scrub high-signal credential shapes from captured text."""
    if not text:
        return text
    out = text
    for pat in _SECRET_PATTERNS:
        if pat.groups >= 2:
            out = pat.sub(lambda m: f"{m.group(1)}=[REDACTED]", out)
        else:
            out = pat.sub("[REDACTED]", out)
    return out


@dataclass
class TurnEvent:
    """A captured interaction turn, assembled by hooks or the MCP store tool."""
    trigger_prompt: str
    action_taken: str
    outcome_feedback: str = ""
    tool_name: str = ""
    success: Optional[bool] = None       # deterministic contingency, if known
    session_id: str = ""
    project: str = ""
    goal_hint: Optional[float] = None     # [0,1] explicit goal-relevance, if known
    valence_hint: Optional[float] = None  # [-1,1] explicit affect, if known
    timestamp: Optional[str] = None       # ISO-8601; backfill real historical time on import
    provenance: str = "trusted"           # Layer 3 origin trust; the hook capture path classifies it.
                                          # Manual / MCP-store / seeded turns default to trusted.


class MemoryService:
    def __init__(self, cfg: Config, db: Optional[Database] = None, embedder: Optional[Embedder] = None):
        self.cfg = cfg
        self.db = db or Database(cfg)
        self.embedder = embedder or get_embedder(cfg)
        self._reconciled = False

    def _reconcile_embedder(self) -> None:
        """Verify the embedder's vector space matches the store, once per service.

        Called lazily on the first vector-producing operation (not in __init__),
        so the SessionStart read path — pure DB reads, no model — never loads the
        model or triggers this check.
        """
        if self._reconciled:
            return
        self.db.reconcile_embedder(self.embedder.fingerprint())
        self._reconciled = True

    # ------------------------------------------------------------------ #
    # Write path
    # ------------------------------------------------------------------ #
    def _clip(self, text: str) -> str:
        """Bound a stored field: redact secrets, then cap length (anti-DoS)."""
        return redact_secrets(text or "")[: self.cfg.max_field_chars]

    def ingest(self, ev: TurnEvent) -> Episodic:
        self._reconcile_embedder()
        # Scrub credentials and cap size before anything is persisted / embedded /
        # re-injected (a multi-MB field would otherwise freeze the embed + bloat DB).
        ev.trigger_prompt = self._clip(ev.trigger_prompt)
        ev.action_taken = self._clip(ev.action_taken)
        ev.outcome_feedback = self._clip(ev.outcome_feedback)
        text = "\n".join(p for p in (ev.trigger_prompt, ev.action_taken, ev.outcome_feedback) if p)
        emb = self.embedder.embed_one(text)

        # Surprise proxy: novelty = cosine distance to the nearest existing episode.
        novelty = self._novelty(emb)
        signals = self._signals(ev, novelty)
        s0 = compute_s0(signals, self.cfg)

        # Flashbulb encoding: a genuine catastrophe — the catastrophe lexicon matches the
        # deed/result AND the valence is already crisis-negative — is maximally memorable by
        # definition. Its natural S0 often lands just under the elevation gate (a real data-loss
        # crisis measured 2.8 vs crisis_threshold 3.0), so no scar ever forms and the disaster is
        # silently forgotten. Floor it to the threshold so a real guardrail elevates; benign/positive
        # events are untouched (both gates must hold). Gated so operators can restore strict behavior.
        if self.cfg.flashbulb_floor_catastrophes and signals.affect <= self.cfg.crisis_valence_max:
            from .consolidate import _matches_catastrophe
            if _matches_catastrophe(f"{ev.action_taken}\n{ev.outcome_feedback}"):
                s0 = max(s0, self.cfg.crisis_threshold)
        # A5 toggle (docs/DEVIATIONS.md M4): when `peak_floor_positives` is True, mirror the floor
        # for STRONG-POSITIVE peaks (affect >= peak_valence_min). FLOOR ONLY — scar elevation in
        # consolidate.py is independently gated on `valence <= crisis_valence_max`, so a positive
        # event never mints a scar even when this toggle is on. Off by default; conservative
        # threshold (0.7) when on. The catastrophe-lexicon analog for positives is a TODO; today
        # the gate is affect-only, which is why the threshold is set high.
        if (self.cfg.peak_floor_positives
                and signals.affect >= self.cfg.peak_valence_min):
            s0 = max(s0, self.cfg.crisis_threshold)

        rec = Episodic(
            id=new_id("ep"),
            trigger_prompt=ev.trigger_prompt,
            action_taken=ev.action_taken,
            outcome_feedback=ev.outcome_feedback,
            valence=signals.affect,
            base_salience=s0,
            session_id=ev.session_id,
            project=ev.project,
            timestamp=ev.timestamp or utc_now_iso(),
            provenance=ev.provenance,
        )
        self.db.insert_episodic(rec, emb)
        self._associate(rec, emb)
        return rec

    def _novelty(self, emb) -> float:
        hits = self.db.knn("episodic", emb, 1)
        if not hits:
            return 1.0
        dist = hits[0][1]  # cosine distance in [0, 2]; ~0 means near-duplicate
        return max(0.0, min(1.0, dist))

    def _signals(self, ev: TurnEvent, novelty: float) -> SalienceSignals:
        blob = f"{ev.trigger_prompt}\n{ev.action_taken}\n{ev.outcome_feedback}".lower()

        # Contingency: did our action change the world, and do we know the outcome?
        if ev.success is not None:
            contingency = 1.0 if ev.success else 0.8  # a known failure is still highly contingent
        elif ev.tool_name.lower() in _CONTINGENT_TOOLS:
            contingency = 0.6
        else:
            contingency = 0.1

        # Self-reference: does this touch the agent's own rules / identity?
        self_ref = 1.0 if any(k in blob for k in _SELF_REF) else 0.0

        # Affect: explicit hint, else lexicon-derived signed valence.
        if ev.valence_hint is not None:
            affect = max(-1.0, min(1.0, ev.valence_hint))
        else:
            affect = self._lexical_valence(blob, ev.success)

        # Goal relevance: explicit hint, else inferred from whether the tool mutates state.
        if ev.goal_hint is not None:
            goal = max(0.0, min(1.0, ev.goal_hint))
        else:
            goal = 0.9 if ev.tool_name.lower() in _CONTINGENT_TOOLS else 0.5

        return SalienceSignals(
            goal=goal, surprise=novelty, contingency=contingency,
            self_ref=self_ref, affect=affect,
        )

    @staticmethod
    def _lexical_valence(blob: str, success: Optional[bool]) -> float:
        if success is True:
            base = 0.4
        elif success is False:
            base = -0.5
        else:
            base = 0.0
        neg = sum(blob.count(w) for w in _NEG_AFFECT)
        pos = sum(blob.count(w) for w in _POS_AFFECT)
        if neg or pos:
            base += 0.25 * (pos - neg)
        return max(-1.0, min(1.0, base))

    def _associate(self, rec: Episodic, emb) -> None:
        """Retroactively boost related faded episodes (conserved-budget shield).

        We apply only the *local* association boost here on the cheap write path;
        the global renormalization to K_budget runs during consolidation. This
        keeps writes fast while still letting the present rewrite the past.
        """
        neighbors = self.db.knn("episodic", emb, 6)
        deltas: list[tuple[str, float, float]] = []   # (id, base_salience, positive boost delta)
        for nid, dist in neighbors:
            if nid == rec.id:
                continue
            sim = 1.0 - dist  # cosine similarity
            old = self.db.get_episodic(nid)
            if old is None:
                continue
            boosted = associative_boost(old.base_salience, rec.base_salience, sim, self.cfg)
            d = boosted - old.base_salience
            if d > 0:
                deltas.append((nid, old.base_salience, d))
        if not deltas:
            return
        # Cap the TOTAL associative boost a single write may inject: at most
        # assoc_boost_cap_frac * its own base_salience, spread across the neighbourhood.
        # A write cannot redistribute more importance than a fraction of what it carries, so
        # one (or a flood of) high-salience writes can't amplify a region unboundedly between
        # consolidations (consolidation's conserve_budget then rebalances) — Cycle-8 M-M-3.
        total = sum(d for _, _, d in deltas)
        cap = self.cfg.assoc_boost_cap_frac * rec.base_salience
        scale = cap / total if total > cap else 1.0
        # Cycle-9 #1: associative boost is a recall-ranking signal, never a scar-manufacturing
        # one. It must not, on its own, lift a neighbour ACROSS the crisis threshold — otherwise
        # a flood of benign-but-embedding-similar writes can tip a planted sub-crisis catastrophe
        # over the scar-elevation gate (base_salience >= crisis_threshold) and mint a permanent
        # guardrail the memory never earned on its own salience. If a neighbour is below crisis on
        # its own, cap its boosted value strictly below crisis; a memory that reached crisis via its
        # own S0 is left to grow. (Boost saturates ~+0.6 even for the worst-case valid config and
        # ~+0.2 by default — KNN crowding bounds it — so this only ever bites a target already
        # within that band of crisis; it is the hard backstop, not the primary limiter.)
        ceiling = math.nextafter(self.cfg.crisis_threshold, 0.0)
        updates: list[tuple[str, float]] = []
        for nid, base, d in deltas:
            val = base + d * scale
            if base < self.cfg.crisis_threshold:
                val = min(val, ceiling)
            updates.append((nid, val))
        self.db.set_salience(updates)

    # ------------------------------------------------------------------ #
    # Explicit pins (scars) and facts (gist)
    # ------------------------------------------------------------------ #
    def pin_scar(self, crisis_trigger: str, remediation_rule: str, project: str = "") -> Scar:
        self._reconcile_embedder()
        # Redact + cap: scars are re-injected into context at every SessionStart.
        scar = Scar(id=new_id("scar"), crisis_trigger=self._clip(crisis_trigger),
                    remediation_rule=self._clip(remediation_rule), project=project)
        emb = self.embedder.embed_one(scar.search_text())
        # Dedup: a near-identical guardrail already pinned (same project) is returned
        # as-is instead of inserting a duplicate permanent row.
        dup = self.db.find_duplicate_scar(emb, project, self.cfg.scar_dedup_sim_threshold)
        if dup is not None:
            return dup
        self.db.insert_scar(scar, emb)
        return scar

    def upsert_fact(self, subject: str, relation: str, object_: str,
                    valence: float = 0.0, project: str = "") -> Gist:
        self._reconcile_embedder()
        # Redact + cap each field (facts feed the PersonaTree, rendered into context).
        subject, relation, object_ = self._clip(subject), self._clip(relation), self._clip(object_)
        # Bem firewall: the model may never author a fact ABOUT ITSELF. Refuse a self-referential subject
        # (the MCP store(kind="fact") path lets a model supply an arbitrary subject; consolidation already
        # forces subject=project and never reaches here). See _SELF_SUBJECTS.
        if _is_self_subject(subject):
            raise ValueError(
                f"never-authors-a-self-tuple: refusing to persist a fact with the assistant as subject "
                f"(subject={subject!r}). Memory records the project/user/workspace, not the assistant itself.")
        cycle = int(self.db.get_meta("cycle", "0") or "0")
        existing = self.db.find_gist_by_so(subject, object_, project)
        if existing:
            existing.frequency += 1
            existing.support_count += 1
            existing.relation = relation        # explicit facts keep their stated relation
            existing.valence = (1 - self.cfg.gist_valence_ema) * existing.valence + self.cfg.gist_valence_ema * valence
            existing.last_reinforced = utc_now_iso()
            existing.last_cycle = cycle
            emb = self.embedder.embed_one(existing.search_text())
            self.db.insert_gist(existing, emb)
            return existing
        g = Gist(id=new_id("gist"), subject=subject, relation=relation, object=object_,
                 valence=valence, project=project, last_cycle=cycle)
        emb = self.embedder.embed_one(g.search_text())
        self.db.insert_gist(g, emb)
        return g

    # ------------------------------------------------------------------ #
    # Read path
    # ------------------------------------------------------------------ #
    def retrieve(self, query: str, top_k: Optional[int] = None,
                 tiers: tuple[str, ...] = ("scar", "gist", "episodic"),
                 reinforce: bool = True, project: str = "") -> list[SearchHit]:
        # Clamp: a negative top_k would slice off the END of the results (returning
        # fewer memories than exist with no error); 0/None means "use the default".
        top_k = max(1, top_k or self.cfg.default_top_k)
        self._reconcile_embedder()  # querying with a mismatched backend recalls nothing
        qvec = self.embedder.embed_one(query)
        pool = max(top_k * 3, 20)

        hits: list[SearchHit] = []
        for tier in tiers:
            rrf = self._rrf(tier, qvec, query, pool)
            if not rrf:
                continue
            hits.extend(self._materialize(tier, rrf))

        # Project scoping: when a project is given, recall only its own + global
        # ("") memories — otherwise a model in project B recalls project A's raw
        # content (cross-project exfiltration). Empty project = unscoped (CLI).
        if project:
            hits = [h for h in hits if h.payload.get("project", "") in ("", project)]
        # Accessibility filtering + reinforcement happen on episodic tier only.
        hits = [h for h in hits if not (h.tier == "episodic" and h.accessibility < self.cfg.retention_floor)]
        hits.sort(key=lambda h: h.score, reverse=True)
        hits = hits[:top_k]

        if reinforce:
            now = utc_now_iso()
            for h in hits:
                if h.tier == "episodic":
                    self.db.touch_episodic(h.id, now)
        return hits

    def _rrf(self, tier: str, qvec, query: str, k: int) -> dict[str, float]:
        """Reciprocal Rank Fusion of vector KNN and FTS5 BM25 within a tier."""
        rk = self.cfg.rrf_k
        scores: dict[str, float] = {}
        for rank, (mid, _dist) in enumerate(self.db.knn(tier, qvec, k), start=1):
            scores[mid] = scores.get(mid, 0.0) + 1.0 / (rk + rank)
        for rank, (mid, _bm) in enumerate(self.db.fts(tier, query, k), start=1):
            scores[mid] = scores.get(mid, 0.0) + 1.0 / (rk + rank)
        return scores

    def _materialize(self, tier: str, rrf: dict[str, float]) -> list[SearchHit]:
        out: list[SearchHit] = []
        weight = _TIER_WEIGHT[tier]
        if tier == "episodic":
            for mid, base in rrf.items():
                rec = self.db.get_episodic(mid)
                if rec is None:
                    continue
                acc = accessibility(rec.base_salience, age_days(rec.timestamp),
                                    rec.access_count, self.cfg)
                # weight RRF by (0.5 + accessibility) so faded memories rank lower
                out.append(SearchHit(
                    id=mid, tier="episodic", text=rec.search_text(),
                    score=base * weight * (0.5 + acc), accessibility=acc,
                    payload={"timestamp": rec.timestamp, "valence": rec.valence,
                             "salience": rec.base_salience, "access_count": rec.access_count,
                             "session_id": rec.session_id, "project": rec.project},
                ))
        elif tier == "gist":
            gmap = self.db.get_gists_by_ids(rrf.keys())   # only the hit ids, not a full scan
            for mid, base in rrf.items():
                g = gmap.get(mid)
                if g is None:
                    continue
                out.append(SearchHit(
                    id=mid, tier="gist", text=g.render(), score=base * weight,
                    accessibility=weight,
                    payload={"subject": g.subject, "relation": g.relation, "object": g.object,
                             "support_count": g.support_count, "frequency": g.frequency,
                             "project": g.project},
                ))
        else:  # scar
            smap = self.db.get_scars_by_ids(rrf.keys())   # only the hit ids, not a full scan
            for mid, base in rrf.items():
                s = smap.get(mid)
                if s is None:
                    continue
                out.append(SearchHit(
                    id=mid, tier="scar", text=f"⚠ {s.crisis_trigger} → {s.remediation_rule}",
                    score=base * weight, accessibility=weight,
                    payload={"crisis_trigger": s.crisis_trigger, "remediation_rule": s.remediation_rule,
                             "project": s.project},
                ))
        return out

    # ------------------------------------------------------------------ #
    # Timeline / paths / links
    # ------------------------------------------------------------------ #
    def history(self, limit: int = 20, session_id: Optional[str] = None) -> list[Episodic]:
        # SQL ORDER BY ... LIMIT (Cycle-9 S-5) instead of loading the whole table to slice in
        # Python — the timeline only wants a small recent window. (max(1, limit) guards against
        # a negative limit; recent_episodic clamps it too.)
        return self.db.recent_episodic(max(1, limit), session_id)

    def list_paths(self) -> list[tuple[str, str, int]]:
        return self.db.list_paths()

    def create_link(self, source_id: str, target_id: str) -> bool:
        # Validate both endpoints exist before linking — otherwise dangling/typo'd
        # edges silently inflate support_count and pollute provenance (foreign_keys
        # is a no-op on the FK-less edges table). Source = an L1 leaf or L2 gist;
        # target = an L2 gist. Returns whether an edge was actually created.
        if not (self.db.exists("episodic", source_id) or self.db.exists("gist", source_id)):
            return False
        if not self.db.exists("gist", target_id):
            return False
        return self.db.add_support_edge(source_id, target_id)

    # ------------------------------------------------------------------ #
    # Deletion / right-to-forget (operator-only; not exposed to the model)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _project_match(stored: str, target: str) -> bool:
        """Match a forget-by-project selector against a stored project path,
        tolerant of trailing slashes, backslashes, and subdirectory cwds.

        Hooks capture the raw per-tool ``cwd`` (often a subdirectory) while the MCP
        path uses the resolved launch cwd, so an exact-string match leaked content
        under ``/proj/`` or ``/proj/sub`` when the operator said forget ``/proj``.
        """
        def norm(p: str) -> str:
            return (p or "").replace("\\", "/").rstrip("/")
        s, t = norm(stored), norm(target)
        return s == t or (bool(t) and s.startswith(t + "/"))

    def forget(self, project: Optional[str] = None, session: Optional[str] = None,
               ids: Optional[list[str]] = None) -> dict:
        """Delete memory by project, by session, and/or by explicit ids across all
        three tiers, the spool, and on-disk free pages. Returns the count actually
        removed per tier. At least one selector must be given (callers must not
        blanket-wipe the store by accident).

        Held under the cross-process lock so a concurrent consolidation cannot
        rebuild gists from episodes mid-delete (resurrecting forgotten content).
        """
        if project is None and session is None and not ids:
            raise ValueError("forget requires at least one of: project, session, ids")
        from .lock import cross_process_lock

        with cross_process_lock(self.cfg.lock_path):
            ids = set(ids or [])
            ep, gi, sc = set(), set(), set()
            for e in self.db.all_episodic():
                if e.id in ids or (project is not None and self._project_match(e.project, project)) or \
                   (session is not None and e.session_id == session):
                    ep.add(e.id)
            for g in self.db.all_gist():
                if g.id in ids or (project is not None and self._project_match(g.project, project)):
                    gi.add(g.id)
            for s in self.db.all_scars():
                if s.id in ids or (project is not None and self._project_match(s.project, project)):
                    sc.add(s.id)
            # NOTE: a session/id forget intentionally does NOT delete gists. The Cycle-7
            # attempt to orphan-delete "fully session-derived" gists via the support-edge
            # table was REVERTED — `delete_episodic` prunes a gist's edges when a supporter
            # is *evicted*, so the residual edges underestimate provenance and a later
            # session-forget would erase genuine MULTI-session traits (identity loss, the
            # double-review H1). Correctly scoping a session-forget to gists needs persisted
            # per-gist session provenance; until then gists are forgettable by project/id
            # only (A2-M1 re-deferred — see docs/REDTEAM_FINDINGS.md).
            res = {
                "episodic": self.db.delete_episodic(ep),
                "gist": self.db.delete_gist(gi),
                "scars": self.db.delete_scar(sc),
                "spooled": self._forget_from_spool(project, session),
            }
            # Scrub freed pages + WAL so deleted content is not forensically
            # recoverable from the db file (only meaningful with secure_delete, but
            # VACUUM also cleans pages freed before this store enabled it).
            self.db.vacuum()
            return res

    def _forget_from_spool(self, project: Optional[str], session: Optional[str]) -> int:
        """Drop matching not-yet-ingested events from the spool. Raw spooled tool
        output is PRE-redaction, so a `forget` that ignored the spool would let
        secrets survive and re-ingest on the next drain. Matched by cwd/session.
        """
        import json
        import os
        from pathlib import Path

        q = self.cfg.queue_path
        if not q.exists():
            return 0
        claimed = Path(f"{q}.forget-{os.getpid()}.tmp")
        try:
            os.replace(q, claimed)
        except (FileNotFoundError, PermissionError):
            return 0
        dropped = 0
        kept: list[str] = []
        try:
            for raw in claimed.read_text(encoding="utf-8").splitlines():
                if not raw.strip():
                    continue
                try:
                    ev = json.loads(raw)
                except json.JSONDecodeError:
                    kept.append(raw)  # unparseable: leave for the drain to skip
                    continue
                if isinstance(ev, dict) and (
                    (project is not None and self._project_match(ev.get("cwd", "") or "", project))
                    or (session is not None and (ev.get("session_id", "") or "") == session)
                ):
                    dropped += 1
                    continue
                kept.append(raw)
            if kept:
                from .spool import spool_event_lines
                spool_event_lines(self.cfg, kept)
        finally:
            try:
                claimed.unlink()
            except OSError:
                pass
        return dropped

    def close(self) -> None:
        self.db.close()
