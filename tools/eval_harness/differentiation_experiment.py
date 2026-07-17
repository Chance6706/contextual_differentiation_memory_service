"""Differentiation-over-time experiment (CORE THESIS). See DIFFERENTIATION_PREREG.md.

THE THESIS (sharpened with Josh): Identity = f(History) means the DISCARD POLICY *is* the disposition.
The SAME history, filtered through DIFFERENT dispositions' salience, yields DIFFERENT identities —
because what each disposition finds salient differs. Differentiation comes from the salience function
on IDENTICAL input, not from different input.

A disposition = a GOAL SET. On-topic events get high goal_hint (-> high G_goal -> high S0 -> survive);
off-topic events get low goal_hint (-> evict first). CDMS lever: S0 = G_goal*(surprise+contingency+
self_ref+affect); goal_hint sets G_goal. So a self CONCENTRATES on its goal-topics under disposition-
salience, but keeps everything under `none` (nothing evicts) and a generic subset under `uniform`.

The experiment is one cube — identity[disposition, history, condition] — read two ways:
  * DRIFT-AGAINST-SELF (fix disposition+history, vary CONDITION): does disposition-salience move the
    singular self from its `none` baseline, more/in a different direction than uniform/random?
  * CROSS-DISPOSITION (fix condition, vary DISPOSITION): similar (A·B) vs different (A·C) vs null (A·U).
    Under disposition-salience expect similar > different; under none/uniform they COLLAPSE to all-similar
    (disposition ignored -> same self). ONLY disposition-salience should recover similar > different.

Identity = {(relation, canonical_entity)} gist tuples (individuation_experiment metric; canonical to
kill object-label noise). Real embedder (fastembed) — asserted. Conditions: none / uniform / random /
disposition-salience (U = dispositionless skips condition 4). Histories are SHARED (identical events
across dispositions) and span ALL topics; seeds = the histories, for CIs.
"""
from __future__ import annotations

import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent
from tools.eval_harness.provenance import assert_worktree_cdms

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)
_DAYS_PER_CYCLE = 7
TURNS_PER_CYCLE = 10

# Entities + DISTINCT subtopics so episodes are embedding-distinct (else dedup folds them; see prereg §build).
_SUBTOPICS = {
    "auth":          ["token refresh", "oauth callback", "session cookie", "MFA enrollment", "password reset", "device trust"],
    "crypto":        ["key rotation", "cert pinning", "nonce reuse", "cipher upgrade", "signature check", "entropy pool"],
    "payments":      ["refund flow", "idempotency key", "webhook retry", "ledger reconcile", "chargeback", "currency round"],
    "database":      ["query planner", "index migration", "connection pool", "replication lag", "schema change", "vacuum job"],
    "cache":         ["eviction policy", "cache stampede", "key sharding", "TTL tuning", "warm-up path", "invalidation"],
    "scheduler":     ["cron parser", "retry backoff", "job dedup", "priority queue", "leader election", "clock skew"],
    "notifications": ["push token", "batch digest", "quiet hours", "delivery receipt", "template render", "opt-out"],
    "analytics":     ["event schema", "funnel query", "cohort roll-up", "sampling bias", "dashboard cache", "backfill"],
}
_ENTITIES = list(_SUBTOPICS)
_GOOD = ["refactored", "hardened", "optimized", "added a test for", "cleanly fixed", "documented", "profiled"]
_BAD = ["broke", "hit a null reference in", "regressed", "hotpatched", "got a compile error in", "corrupted"]

# Per-entity success tendency — FIXED and disposition-INDEPENDENT (the history is shared; disposition
# changes only what is found SALIENT, never what happened). Determines each entity's relation.
_ENTITY_SUCCESS = {"auth": 0.85, "crypto": 0.80, "payments": 0.45, "database": 0.75,
                   "cache": 0.35, "scheduler": 0.60, "notifications": 0.70, "analytics": 0.50}

# Dispositions = GOAL SETS. B shares 3/4 topics with A (SIMILAR); C is disjoint from A (DIFFERENT); U = none.
_DISPOSITIONS = {
    "A": {"auth", "crypto", "payments", "database"},
    "B": {"auth", "crypto", "payments", "cache"},           # 3/4 shared with A -> SIMILAR (Jaccard ~0.6)
    "C": {"cache", "scheduler", "notifications", "analytics"},  # disjoint from A -> DIFFERENT (Jaccard ~0)
}
_GOAL_HI, _GOAL_LO = 1.0, 0.08
_PROJECT = "work"


def _shared_history(seed: int, cycles: int) -> list[list[dict]]:
    """The IDENTICAL event stream every disposition receives (only goal-salience differs downstream).
    Each cycle: TURNS_PER_CYCLE events spread across ALL entities. Deterministic per seed."""
    rng = random.Random(f"hist:{seed}")
    hist = []
    for c in range(1, cycles + 1):
        batch = []
        for _ in range(TURNS_PER_CYCLE):
            ent = rng.choice(_ENTITIES)
            sub = rng.choice(_SUBTOPICS[ent])
            success = rng.random() < _ENTITY_SUCCESS[ent]
            verb = rng.choice(_GOOD if success else _BAD)
            batch.append({"entity": ent, "sub": sub, "success": success, "verb": verb,
                          "affect": (0.6 if success else -0.6)})
        hist.append(batch)
    return hist


def _shared_history_pair(seed: int, f: float, cycles: int) -> tuple:
    """Two histories that SHARE the first f fraction of cycles (identical events), then DIVERGE into
    independent streams — the fulcrum axis (how overlap scales with shared life). f=1 -> identical;
    f=0 -> fully independent lives."""
    n_shared = int(round(f * cycles))
    prefix = _shared_history(seed, cycles)                    # common life up to the split
    suf1 = _shared_history(seed + 20_000, cycles)             # subject 1's divergent life
    suf2 = _shared_history(seed + 30_000, cycles)             # subject 2's divergent life
    h1 = prefix[:n_shared] + suf1[n_shared:cycles]
    h2 = prefix[:n_shared] + suf2[n_shared:cycles]
    return h1, h2


def _goal_hint(entity: str, dispo: str, condition: str):
    """Disposition-salience gates events by the disposition's goal set. Every other condition ignores
    the disposition (that is the whole point — they must produce the SAME self across dispositions)."""
    if condition != "disposition-salience" or dispo == "U":
        return None
    return _GOAL_HI if entity in _DISPOSITIONS[dispo] else _GOAL_LO


_POLICY = {
    "none":                 {"retention_floor": 0.0},
    "uniform":              {},
    "random":               {"discard_policy": "random"},
    "disposition-salience": {},
}

# --- ERASURE arm (CORE THESIS; DIFFERENTIATION_ERASURE_PREREG.md, LOCKED) --------------------------
# The frozen-history cube fed ALL topics every cycle, so nothing ever went idle and nothing was
# forgotten (committed NULL). Here the disposition drives BEHAVIOUR: after a SHARED PAST (all topics,
# identical across dispositions), each self only keeps LIVING its goal topics; off-goal topics go idle,
# their episodes age out, and their gists idle-decay (~137-396 cycles). Identity = what SURVIVES the
# neglect. The forgetting-policy ablation (salience / none / random) is orthogonal to the behaviour.
_ERASURE_POLICY = {
    "salience": {},                        # shipped defaults: retention_floor=0.10, discard=salience
    "none":     {"retention_floor": 0.0},  # episodes never evict -> off-goal gists reinforced forever -> no decay
    "random":   {"discard_policy": "random"},  # rate-matched random episode eviction (goal-blind forgetting)
}


def _entities_of(idset: set) -> frozenset:
    """The bare entity set behind a {(relation, entity)} identity (drops the noisy relation label)."""
    return frozenset(e for (_, e) in idset)


def _cfg_for(home: Path, condition: str, seed: int, gate_floor: float = 0.25) -> Config:
    cfg = Config(home=home)
    for k, v in _POLICY[condition].items():
        setattr(cfg, k, v)
    if condition == "random":
        cfg.discard_random_seed = seed
    cfg.goal_gate_floor = gate_floor   # 0.25 = as-shipped (bounded tilt); ~0 = mechanism ceiling (filter)
    cfg.ensure_home()
    return cfg


def _canonical_entity(gist) -> str:
    blob = f"{gist.object} {getattr(gist, 'exemplar', '') or ''}".lower()
    for e in _ENTITIES:
        if e in blob:
            return e
    return gist.object


def identity(svc: MemoryService) -> set:
    """RAW identity: every (relation, canonical_entity) trait present in the store."""
    return {(g.relation, _canonical_entity(g)) for g in svc.db.all_gist()}


def surfaced_identity(svc: MemoryService) -> set:
    """SURFACED identity: what CDMS actually injects at SessionStart — top_gist(limit=12), pre-sorted by
    (support+frequency+survived). With goal_gate_floor in force the individuation lives in the WEIGHTING,
    so this budget-limited, salience-ranked view is the faithful lens (vs the raw set which keeps ~all)."""
    return {(g.relation, _canonical_entity(g)) for g in svc.db.top_gist(limit=12, project=_PROJECT)}


def topic_profile(svc: MemoryService) -> dict:
    """Which entities the identity covers (for the mechanism check: does the self CONCENTRATE?)."""
    prof = {}
    for g in svc.db.all_gist():
        prof[_canonical_entity(g)] = prof.get(_canonical_entity(g), 0) + 1
    return prof


def run_subject(dispo: str, condition: str, home: Path, seed: int, embedder, cycles: int,
                hist: list = None, gate_floor: float = 0.25, snapshot_every: int = 0) -> dict:
    """Ingest the SHARED history under (disposition, condition, gate_floor); return the FINAL raw +
    surfaced identity (and an optional per-cycle trajectory if snapshot_every>0)."""
    cfg = _cfg_for(home, condition, seed, gate_floor)
    svc = MemoryService(cfg, embedder=embedder)
    hist = hist if hist is not None else _shared_history(seed, cycles)
    traj, ingested, evicted = [], 0, 0
    for c, batch in enumerate(hist[:cycles], start=1):
        now = _EPOCH + timedelta(days=(c - 1) * _DAYS_PER_CYCLE)
        for i, ev in enumerate(batch):
            ts = (now + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            svc.ingest(TurnEvent(
                trigger_prompt=f"work on the {ev['entity']} {ev['sub']}",
                action_taken=f"{ev['verb']} the {ev['entity']} {ev['sub']}",
                outcome_feedback=("clean result" if ev["success"] else "broke, needed a fix"),
                tool_name="Edit", success=ev["success"], valence_hint=ev["affect"],
                goal_hint=_goal_hint(ev["entity"], dispo, condition),
                session_id=f"{dispo}-c{c}", project=_PROJECT, timestamp=ts))
        ingested += len(batch)
        rep = Consolidator(cfg, db=svc.db, embedder=embedder).run(now=now)
        evicted += rep.episodes_evicted
        if snapshot_every and (c % snapshot_every == 0 or c == cycles):
            traj.append({"cycle": c, "cum_turns": ingested,
                         "raw": identity(svc), "surfaced": surfaced_identity(svc), "evicted": evicted})
    out = {"dispo": dispo, "condition": condition, "gate_floor": gate_floor, "seed": seed,
           "raw": identity(svc), "surfaced": surfaced_identity(svc), "evicted": evicted, "traj": traj}
    svc.close()
    return out


# --- ERASURE arm implementation -------------------------------------------------------------------

def _erasure_history(seed: int, dispo: str, cycles: int, share_frac: float) -> tuple[list, int]:
    """Phased event stream for the erasure arm. Returns (history, n_shared).

    Phase 1 SHARED PAST (first n_shared cycles): all 8 topics recur -> every topic forms a gist. The
      stream is disposition-INDEPENDENT (seeded on `seed` only) so A/B/C/U share an IDENTICAL past.
    Phase 2 DRIFT+TAIL (remaining cycles): only the disposition's goal topics recur (disposition-
      specific stream); off-goal topics never reappear -> go idle -> age out -> gists decay. U
      (dispositionless) keeps ALL topics through the tail (no selective neglect) — the within-salience
      null: erasure needs a disposition to do the neglecting.
    """
    n_shared = max(1, int(round(share_frac * cycles)))
    goalset = _DISPOSITIONS.get(dispo)                       # None for U
    rng_shared = random.Random(f"erase-shared:{seed}")       # common past (all dispositions)
    rng_drift = random.Random(f"erase-drift:{seed}:{dispo}")  # divergent life (per disposition)
    hist = []
    for c in range(1, cycles + 1):
        if c <= n_shared:
            pool, rng, phase = _ENTITIES, rng_shared, "shared"
        elif goalset is None:                                # U keeps living everything
            pool, rng, phase = _ENTITIES, rng_drift, "drift"
        else:
            pool, rng, phase = sorted(goalset), rng_drift, "drift"
        batch = []
        for _ in range(TURNS_PER_CYCLE):
            ent = rng.choice(pool)
            sub = rng.choice(_SUBTOPICS[ent])
            success = rng.random() < _ENTITY_SUCCESS[ent]
            verb = rng.choice(_GOOD if success else _BAD)
            batch.append({"entity": ent, "sub": sub, "success": success, "verb": verb,
                          "affect": (0.6 if success else -0.6), "phase": phase})
        hist.append(batch)
    return hist, n_shared


def _erasure_goal_hint(entity: str, dispo: str):
    """Disposition salience: on-goal HI (survives, gf-independent), off-goal LO (faded; gf gates HOW
    hard the anti-amnesia floor protects it). U carries no disposition -> None (neutral goal ~0.9)."""
    goalset = _DISPOSITIONS.get(dispo)
    if goalset is None:
        return None
    return _GOAL_HI if entity in goalset else _GOAL_LO


def _erasure_cfg_for(home: Path, policy: str, seed: int, gate_floor: float) -> Config:
    cfg = Config(home=home)
    for k, v in _ERASURE_POLICY[policy].items():
        setattr(cfg, k, v)
    if policy == "random":
        cfg.discard_random_seed = seed
    cfg.goal_gate_floor = gate_floor
    cfg.ensure_home()
    return cfg


def run_erasure_subject(dispo: str, policy: str, home: Path, seed: int, embedder, cycles: int,
                        share_frac: float = 0.12, gate_floor: float = 0.25,
                        snapshot_every: int = 0) -> dict:
    """Live the SHARED PAST then DRIFT under a forgetting policy; return the SURVIVING identity plus the
    erasure telemetry the F3 precondition needs (gists_decayed, off-goal entity count at the shared-past
    PEAK vs the end) and an optional per-cycle trajectory (the 'how it differentiates over time' view)."""
    cfg = _erasure_cfg_for(home, policy, seed, gate_floor)
    svc = MemoryService(cfg, embedder=embedder)
    hist, n_shared = _erasure_history(seed, dispo, cycles, share_frac)
    goalset = set(_DISPOSITIONS.get(dispo) or ())

    def _offgoal_supports() -> list:
        """Support_count of every OFF-goal gist right now (desc) — the 'tier' that neglect must erase.
        Lets us verify a HIGH-tier gist (support near the decay cap) actually gets evicted by 500cy."""
        return sorted((g.support_count for g in svc.db.all_gist() if _canonical_entity(g) not in goalset),
                      reverse=True)

    traj, gists_decayed_total = [], 0
    peak_raw, peak_ents, peak_offgoal_support = set(), frozenset(), []
    for c, batch in enumerate(hist, start=1):
        now = _EPOCH + timedelta(days=(c - 1) * _DAYS_PER_CYCLE)
        for i, ev in enumerate(batch):
            ts = (now + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            svc.ingest(TurnEvent(
                trigger_prompt=f"work on the {ev['entity']} {ev['sub']}",
                action_taken=f"{ev['verb']} the {ev['entity']} {ev['sub']}",
                outcome_feedback=("clean result" if ev["success"] else "broke, needed a fix"),
                tool_name="Edit", success=ev["success"], valence_hint=ev["affect"],
                goal_hint=_erasure_goal_hint(ev["entity"], dispo),
                session_id=f"{dispo}-c{c}", project=_PROJECT, timestamp=ts))
        rep = Consolidator(cfg, db=svc.db, embedder=embedder).run(now=now)
        gists_decayed_total += rep.gists_decayed
        if c == n_shared:                          # PEAK: end of the shared past, before neglect
            peak_raw = identity(svc)
            peak_ents = _entities_of(peak_raw)
            peak_offgoal_support = _offgoal_supports()
        if snapshot_every and (c % snapshot_every == 0 or c == cycles):
            r = identity(svc)
            traj.append({"cycle": c, "phase": batch[0]["phase"], "n_ents": len(_entities_of(r)),
                         "gists_decayed": gists_decayed_total,
                         "raw": r, "surfaced": surfaced_identity(svc)})
    final_raw = identity(svc)
    final_ents = _entities_of(final_raw)
    out = {"dispo": dispo, "policy": policy, "gate_floor": gate_floor, "seed": seed,
           "raw": final_raw, "surfaced": surfaced_identity(svc),
           "peak_raw": peak_raw, "peak_ents": sorted(peak_ents), "final_ents": sorted(final_ents),
           "goalset": sorted(goalset), "n_shared": n_shared, "gists_decayed": gists_decayed_total,
           # F3 topic-disappearance telemetry: off-goal entities present at the peak vs the end.
           "offgoal_peak_n": len(peak_ents - goalset), "offgoal_final_n": len(final_ents - goalset),
           # High-tier-eviction evidence: off-goal gist support at the peak (max = the top tier neglect erased).
           "peak_offgoal_support": peak_offgoal_support, "final_offgoal_support": _offgoal_supports(),
           "traj": traj}
    svc.close()
    return out
