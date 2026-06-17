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


class MemoryService:
    def __init__(self, cfg: Config, db: Optional[Database] = None, embedder: Optional[Embedder] = None):
        self.cfg = cfg
        self.db = db or Database(cfg)
        self.embedder = embedder or get_embedder(cfg)

    # ------------------------------------------------------------------ #
    # Write path
    # ------------------------------------------------------------------ #
    def ingest(self, ev: TurnEvent) -> Episodic:
        text = "\n".join(p for p in (ev.trigger_prompt, ev.action_taken, ev.outcome_feedback) if p)
        emb = self.embedder.embed_one(text)

        # Surprise proxy: novelty = cosine distance to the nearest existing episode.
        novelty = self._novelty(emb)
        signals = self._signals(ev, novelty)
        s0 = compute_s0(signals, self.cfg)

        rec = Episodic(
            id=new_id("ep"),
            trigger_prompt=ev.trigger_prompt,
            action_taken=ev.action_taken,
            outcome_feedback=ev.outcome_feedback,
            valence=signals.affect,
            base_salience=s0,
            session_id=ev.session_id,
            project=ev.project,
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
        updates: list[tuple[str, float]] = []
        for nid, dist in neighbors:
            if nid == rec.id:
                continue
            sim = 1.0 - dist  # cosine similarity
            old = self.db.get_episodic(nid)
            if old is None:
                continue
            boosted = associative_boost(old.base_salience, rec.base_salience, sim, self.cfg)
            if boosted != old.base_salience:
                updates.append((nid, boosted))
        if updates:
            self.db.set_salience(updates)

    # ------------------------------------------------------------------ #
    # Explicit pins (scars) and facts (gist)
    # ------------------------------------------------------------------ #
    def pin_scar(self, crisis_trigger: str, remediation_rule: str, project: str = "") -> Scar:
        scar = Scar(id=new_id("scar"), crisis_trigger=crisis_trigger,
                    remediation_rule=remediation_rule, project=project)
        emb = self.embedder.embed_one(scar.search_text())
        self.db.insert_scar(scar, emb)
        return scar

    def upsert_fact(self, subject: str, relation: str, object_: str,
                    valence: float = 0.0, project: str = "") -> Gist:
        existing = self.db.find_gist_by_tuple(subject, relation, object_)
        if existing:
            existing.frequency += 1
            existing.support_count += 1
            emb = self.embedder.embed_one(existing.search_text())
            self.db.insert_gist(existing, emb)
            return existing
        g = Gist(id=new_id("gist"), subject=subject, relation=relation, object=object_,
                 valence=valence, project=project)
        emb = self.embedder.embed_one(g.search_text())
        self.db.insert_gist(g, emb)
        return g

    # ------------------------------------------------------------------ #
    # Read path
    # ------------------------------------------------------------------ #
    def retrieve(self, query: str, top_k: Optional[int] = None,
                 tiers: tuple[str, ...] = ("scar", "gist", "episodic"),
                 reinforce: bool = True) -> list[SearchHit]:
        top_k = top_k or self.cfg.default_top_k
        qvec = self.embedder.embed_one(query)
        pool = max(top_k * 3, 20)

        hits: list[SearchHit] = []
        for tier in tiers:
            rrf = self._rrf(tier, qvec, query, pool)
            if not rrf:
                continue
            hits.extend(self._materialize(tier, rrf))

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
                             "session_id": rec.session_id},
                ))
        elif tier == "gist":
            gmap = {g.id: g for g in self.db.all_gist()}
            for mid, base in rrf.items():
                g = gmap.get(mid)
                if g is None:
                    continue
                out.append(SearchHit(
                    id=mid, tier="gist", text=g.render(), score=base * weight,
                    accessibility=weight,
                    payload={"subject": g.subject, "relation": g.relation, "object": g.object,
                             "support_count": g.support_count, "frequency": g.frequency},
                ))
        else:  # scar
            smap = {s.id: s for s in self.db.all_scars()}
            for mid, base in rrf.items():
                s = smap.get(mid)
                if s is None:
                    continue
                out.append(SearchHit(
                    id=mid, tier="scar", text=f"⚠ {s.crisis_trigger} → {s.remediation_rule}",
                    score=base * weight, accessibility=weight,
                    payload={"crisis_trigger": s.crisis_trigger, "remediation_rule": s.remediation_rule},
                ))
        return out

    # ------------------------------------------------------------------ #
    # Timeline / paths / links
    # ------------------------------------------------------------------ #
    def history(self, limit: int = 20, session_id: Optional[str] = None) -> list[Episodic]:
        eps = self.db.all_episodic()
        if session_id:
            eps = [e for e in eps if e.session_id == session_id]
        eps.sort(key=lambda e: e.timestamp, reverse=True)
        return eps[:limit]

    def list_paths(self) -> list[tuple[str, str, int]]:
        return self.db.list_paths()

    def create_link(self, source_id: str, target_id: str) -> bool:
        self.db.add_support_edge(source_id, target_id)
        return True

    def close(self) -> None:
        self.db.close()
