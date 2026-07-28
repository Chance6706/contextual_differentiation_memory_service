"""Differentiation measurement — the store-level Jaccard path (the salience-vs-random control).

The thesis metric (individuation_experiment): a psyche's identity = the set of (relation, object)
gist tuples its history + forgetting produced. Two distinct histories should yield LOW cross-psyche
overlap. The sharp control: does forgetting BY SALIENCE (cdms-full) differentiate MORE (lower overlap)
than forgetting AT RANDOM (cdms-random-discard)? Per-condition overlap is a store-level SCALAR, so this
lives outside the per-query analyzer; CIs come from bootstrapping over SEEDS.

FINDING (2026-07-16, measured): in a SINGLE consolidation pass the discard policy does NOT move
gist-level differentiation — cdms-full / cdms-forgetting / cdms-random-discard give identical overlap
at every seed. Gists aggregate during the pass and persist in their own tier, so evicting EPISODES
(what the discard policy changes) leaves the already-formed traits untouched. The salience-vs-random
differentiation effect is therefore inherently MULTI-CYCLE: it needs repeated cycles where gists decay
(activity-based) and are reinforced only when their supporting episodes RECUR — so salience-retained
recurrences keep a trait alive while random-dropped ones let it fade. The multi-cycle driver (the drift
trajectory) is the correct design for the sharp control; single-pass is a null by construction, not a
measured null about salience. See EVAL_HARNESS_PREREG §11 — this reshapes how differentiation is run.
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
from tools.eval_harness.adapter import _CONDITION_OVERRIDES

_NOW = datetime(2026, 7, 15, tzinfo=timezone.utc)   # fixed reference (deterministic, no wall-clock)
_POS = "passed cleanly, all green, works correctly"
_NEG = "failed with an error, exception in the log, build is red"

# Two psyches with DISTINCT entity/valence histories -> distinct trait sets.
PSYCHE_A = {"project": "alpha", "entities": ["auth", "parser", "cache", "scheduler"],
            "success_rate": 0.85}
PSYCHE_B = {"project": "beta", "entities": ["viewport", "deploy", "docs", "webhook"],
            "success_rate": 0.30}


def _gen(spec: dict, n: int, seed: int) -> list[TurnEvent]:
    rng = random.Random(seed)
    turns = []
    for i in range(n):
        age = 2.0 + 38.0 * (1.0 - i / max(1, n - 1)) * rng.uniform(0.6, 1.0)
        ts = (_NOW - timedelta(days=age)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ent = rng.choice(spec["entities"])
        success = rng.random() < spec["success_rate"]
        verb = rng.choice(["improved", "refactored", "extended"] if success
                          else ["debugged", "reverted", "patched"])
        turns.append(TurnEvent(
            trigger_prompt=f"work on the {ent}",
            action_taken=f"{verb} the {ent} module",
            outcome_feedback=_POS if success else _NEG,
            tool_name="Edit", success=success, session_id=f"{spec['project']}-{i // 20}",
            project=spec["project"], timestamp=ts))
    rng.shuffle(turns)
    return turns


def trait_set(svc: MemoryService) -> set:
    """The differentiated traits: (relation, object) gist tuples (individuation_experiment metric)."""
    return {(g.relation, g.object) for g in svc.db.all_gist()}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0


def _build(spec: dict, home: Path, condition: str, seed: int, embedder) -> MemoryService:
    cfg = Config(home=home)
    for k, v in _CONDITION_OVERRIDES.get(condition, {}).items():
        setattr(cfg, k, seed if k == "discard_random_seed" else v)  # vary the random seed
    cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    for ev in _gen(spec, 40, seed):
        svc.ingest(ev)
    Consolidator(cfg, db=svc.db, embedder=embedder).run(now=_NOW)
    return svc


def measure_overlap(condition: str, seed: int, base: Path) -> dict:
    """Cross-psyche (relation,object) Jaccard overlap for one condition+seed. Lower = more
    differentiated. Returns overlap + each psyche's trait count (a sanity guard: 0 traits = no gists).

    NOTE (the single-pass null, see module docstring): overlap here is IDENTICAL across
    cdms-full / cdms-forgetting / cdms-random-discard — a single pass forms gists before it evicts
    episodes, so the discard policy cannot move the traits. This function measures the thesis metric
    (two distinct histories -> low overlap); the salience-vs-random SHARP CONTROL lives in
    measure_selfshape below, which needs multiple cycles to bite."""
    os.environ["CDMS_EVAL_MODE"] = "1"   # differentiation exercises the (eval-gated) discard policies
    os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")
    emb = Embedder(Config(home=base))
    a = _build(PSYCHE_A, base / f"{condition}-{seed}-a", condition, seed, emb)
    b = _build(PSYCHE_B, base / f"{condition}-{seed}-b", condition, seed, emb)
    ta, tb = trait_set(a), trait_set(b)
    a.close(); b.close()
    return {"condition": condition, "seed": seed, "overlap": jaccard(ta, tb),
            "traits_a": len(ta), "traits_b": len(tb)}


# ── Multi-cycle within-psyche SHARP CONTROL: does forgetting BY SALIENCE shape identity ──
# differently than forgetting AT RANDOM? Same history, two discard policies, N aging cycles.
# The effect is real but SUBTLE under default params (few episodes cross the retention floor,
# gists rarely decay) — measured, not asserted. A stronger demonstration needs tuned aging/decay
# and is a downstream EXPERIMENT (Josh's call), not harness machinery.
_CYCLES = 8
_SALIENT = ["auth", "parser", "cache"]   # recur every cycle (candidates to reinforce)


def _gen_cycle(cycle: int, cycle_now: datetime, seed: int) -> list[TurnEvent]:
    """One cycle's batch: recurring salient work + per-cycle one-off noise (the churn the
    discard policy prunes). Timestamps walk back from cycle_now so later cycles age earlier ones."""
    rng = random.Random(seed * 100 + cycle)
    spec = [(e, True) for e in _SALIENT for _ in range(3)]
    spec += [(f"noise{cycle}_{j}", rng.random() < 0.5) for j in range(6)]
    rng.shuffle(spec)
    out = []
    for k, (ent, success) in enumerate(spec):
        ts = (cycle_now - timedelta(hours=k)).strftime("%Y-%m-%dT%H:%M:%SZ")
        verb = rng.choice(["improved", "refactored"]) if success else rng.choice(["debugged", "reverted"])
        out.append(TurnEvent(
            trigger_prompt=f"work on {ent}", action_taken=f"{verb} the {ent} module",
            outcome_feedback=_POS if success else _NEG, tool_name="Edit", success=success,
            session_id=f"c{cycle}", project="alpha", timestamp=ts))
    return out


def _build_multicycle(home: Path, policy: str, seed: int, embedder, cycles: int) -> tuple[set, int, int]:
    """Run `cycles` consolidation cycles under one discard policy, aging episodes each cycle so
    eviction bites. Returns (final trait set, total episodes evicted, total gists decayed)."""
    cfg = Config(home=home)
    cfg.discard_policy = policy
    if policy == "random":
        cfg.discard_random_seed = seed
    cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    evicted = decayed = 0
    for c in range(1, cycles + 1):
        cycle_now = _NOW - timedelta(days=(cycles - c) * 20)   # walk from ~(cycles*20)d ago to _NOW
        for ev in _gen_cycle(c, cycle_now, seed):
            svc.ingest(ev)
        rep = Consolidator(cfg, db=svc.db, embedder=embedder).run(now=cycle_now)
        evicted += rep.episodes_evicted
        decayed += rep.gists_decayed
    traits = trait_set(svc)
    svc.close()
    return traits, evicted, decayed


def measure_selfshape(seed: int, base: Path, cycles: int = _CYCLES) -> dict:
    """The sharp control: build the SAME multi-cycle history twice — once forgetting by salience,
    once at random — and report how much the final trait sets DIVERGE. self_overlap < 1.0 means the
    forgetting POLICY shaped identity (salience kept different traits alive than random did)."""
    os.environ["CDMS_EVAL_MODE"] = "1"
    os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")
    emb = Embedder(Config(home=base))
    ts_sal, ev_s, dc_s = _build_multicycle(base / f"sal-{seed}", "salience", seed, emb, cycles)
    ts_rnd, ev_r, dc_r = _build_multicycle(base / f"rnd-{seed}", "random", seed, emb, cycles)
    return {"seed": seed, "cycles": cycles,
            "self_overlap": jaccard(ts_sal, ts_rnd),            # 1.0 = policy had no effect
            "diverged": ts_sal != ts_rnd,
            "traits_salience": len(ts_sal), "traits_random": len(ts_rnd),
            "evicted_salience": ev_s, "evicted_random": ev_r,
            "decayed_salience": dc_s, "decayed_random": dc_r}
