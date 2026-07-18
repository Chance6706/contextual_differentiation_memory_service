"""PLASTICITY LADDER characterization-lite run (task #16) — pre-scoped NEGATIVE characterization.

NOT a search: PT7 established (reproduced) that the ladder is squeezed — low-alpha residual = noise
(capstone), high-alpha geometry collapses (offdiag_std 8x down), and on-pattern emergent coupling is
observationally equivalent to a stronger imposed weight (identifiability limit, ~6% survives
residualization). This run commits the POWERED dose-response curve of that squeeze:
  per rung: offdiag variance (collapse curve), REAL coupling T (same-disp - diff-disp),
  KNOWN-TAUTOLOGY support T (power anchor), relabel rate, spread trajectory;
  primary = max-T across rungs vs the permutation distribution OF the max (shared label perm);
  plus residualized T (vs [1, w(x)w]) and an OFF-pattern injection recovery gate (statistic-level).
S1 bar: no statistic reads gist text — slots are BIRTH-frozen nearest-ground-truth-anchor (geometry).

All stores live and die inside UnguardedSandbox (double-key armed, crash-safe burn). Output =
aggregated scalars only (docs/validation/eval_harness/plasticity_ladder_metrics.json) — no raw
vectors, no gist text. Runtime ~45-60 min CPU. Run: python tools/eval_harness/plasticity_ladder_run.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import timedelta
from itertools import combinations
from pathlib import Path

os.environ.setdefault("CDMS_EVAL_MODE", "1")
os.environ.setdefault("CDMS_UNGUARDED_DRIFT", "1")
os.environ.setdefault("CDMS_EMBED_BACKEND", "fastembed")

import numpy as np

REPO = Path(__file__).resolve().parents[2]
# src FIRST: the eval venv editable-installs cdms from a SIBLING clone; without this pin the
# runner would silently measure the wrong codebase (caught live by assert_worktree_cdms, 2026-07-17).
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent
from tools.eval_harness.differentiation_experiment import (
    _shared_history, _goal_hint, _DISPOSITIONS, _ENTITIES, _SUBTOPICS,
    _EPOCH, _DAYS_PER_CYCLE, _PROJECT, _cfg_for)
from tools.eval_harness.unguarded_sandbox import UnguardedSandbox, drift_gists, RUNGS, _unit

# ---- pinned run config (characterization-lite; verdict pre-known, curve is the deliverable) ----
SEEDS = list(range(1, 17))          # 16
CYCLES = 40
DISPOS = ("A", "C")
GATE_FLOOR = 0.25
N_PERM = 1000
INJ_DELTA = 0.05                    # off-pattern injection magnitude (power gate)
K = len(_ENTITIES)
ENTS = sorted(_ENTITIES)


def entity_anchors(emb):
    return {e: _unit(np.mean([np.asarray(emb.embed_one(
        f"work on the {e} {s}\nrefactored the {e} {s}\nclean result"), np.float64)
        for s in _SUBTOPICS[e]], axis=0)) for e in ENTS}


def nearest(cen, anchors):
    cen = _unit(np.asarray(cen, np.float64))
    return max(anchors, key=lambda e: float(np.dot(cen, anchors[e])))


def run_subject(sb, dispo, rung, seed, emb, anchors):
    cfg = _cfg_for(sb.home(f"{rung}-{dispo}-s{seed}"), "disposition-salience", seed, GATE_FLOOR)
    svc = MemoryService(cfg, embedder=emb)
    sb.register(svc)
    rc = RUNGS[rung]
    hist = _shared_history(seed, CYCLES)
    birth_slot, prev_live, relabels = {}, {}, 0
    prev_supp: dict = {}
    spread_traj = []
    for c, batch in enumerate(hist[:CYCLES], start=1):
        now = _EPOCH + timedelta(days=(c - 1) * _DAYS_PER_CYCLE)
        bvecs = []
        for i, ev in enumerate(batch):
            ts = (now + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            fb = "clean result" if ev["success"] else "broke, needed a fix"
            svc.ingest(TurnEvent(
                trigger_prompt=f"work on the {ev['entity']} {ev['sub']}",
                action_taken=f"{ev['verb']} the {ev['entity']} {ev['sub']}",
                outcome_feedback=fb, tool_name="Edit", success=ev["success"],
                valence_hint=ev["affect"],
                goal_hint=_goal_hint(ev["entity"], dispo, "disposition-salience"),
                session_id=f"{dispo}-c{c}", project=_PROJECT, timestamp=ts))
            bvecs.append(np.asarray(emb.embed_one(
                f"work on the {ev['entity']} {ev['sub']}\n"
                f"{ev['verb']} the {ev['entity']} {ev['sub']}\n{fb}"), np.float64))
        Consolidator(cfg, db=svc.db, embedder=emb).run(now=now)
        if rc["alpha"] > 0:
            drift_gists(sb, svc, _unit(np.mean(bvecs, axis=0)), rc["alpha"],
                        resistance=rc["resistance"], cap=rc["cap"],
                        touched_only=rc["touched_only"], touched_supports=prev_supp)
        gists = svc.db.all_gist()
        prev_supp = {g.id: g.support_count for g in gists}
        cens = {}
        for g in gists:
            cc = svc.db.get_gist_centroid(g.id)
            if cc is None:
                continue
            cens[g.id] = _unit(np.asarray(cc, np.float64))
            live = nearest(cens[g.id], anchors)
            if g.id not in birth_slot:
                birth_slot[g.id] = live            # MF2: slot frozen at BIRTH
            if g.id in prev_live and prev_live[g.id] != live:
                relabels += 1
            prev_live[g.id] = live
        vs = list(cens.values())
        spread = (float(np.mean([np.linalg.norm(a - b) for a, b in combinations(vs, 2)]))
                  if len(vs) > 1 else 0.0)
        spread_traj.append(spread)
    # per-BIRTH-slot representative centroid + support
    slot_v = {e: [] for e in ENTS}
    slot_s = {e: 0.0 for e in ENTS}
    for g in svc.db.all_gist():
        cc = svc.db.get_gist_centroid(g.id)
        if cc is None or g.id not in birth_slot:
            continue
        slot_v[birth_slot[g.id]].append(_unit(np.asarray(cc, np.float64)))
        slot_s[birth_slot[g.id]] += g.support_count
    M = np.full((K, K), np.nan)
    reps = {e: (_unit(np.mean(slot_v[e], axis=0)) if slot_v[e] else None) for e in ENTS}
    for i, ei in enumerate(ENTS):
        for j, ej in enumerate(ENTS):
            if reps[ei] is not None and reps[ej] is not None:
                M[i, j] = float(np.dot(reps[ei], reps[ej]))
    svc.close()
    off = M[np.triu_indices(K, 1)]
    return dict(offdiag=off.tolist(), support=[slot_s[e] for e in ENTS],
                relabels=relabels, spread_traj=spread_traj)


def corr(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() >= 3 else np.nan


def w_pattern(dispo):
    w = np.array([1.0 if e in _DISPOSITIONS[dispo] else GATE_FLOOR for e in ENTS])
    return np.outer(w, w)[np.triu_indices(K, 1)]


def resid(vec, dispo):
    """OLS-residualize an offdiag vector against [1, w(x)w] of the (possibly permuted) label."""
    v = np.asarray(vec, float)
    X = np.column_stack([np.ones(v.size), w_pattern(dispo)])
    m = np.isfinite(v)
    beta, *_ = np.linalg.lstsq(X[m], v[m], rcond=None)
    out = np.full_like(v, np.nan)
    out[m] = v[m] - X[m] @ beta
    return out


def T_stat(vecs, labels):
    """same-disp mean corr - diff-disp mean corr over subject offdiag vectors."""
    same, diff = [], []
    for i, j in combinations(range(len(vecs)), 2):
        (same if labels[i] == labels[j] else diff).append(corr(vecs[i], vecs[j]))
    return float(np.nanmean(same) - np.nanmean(diff))


def main():
    t0 = time.time()
    out = {"config": dict(seeds=len(SEEDS), cycles=CYCLES, gate_floor=GATE_FLOOR,
                          n_perm=N_PERM, inj_delta=INJ_DELTA, rungs=RUNGS)}
    with UnguardedSandbox() as sb:
        emb = Embedder(Config(home=sb.home("embedder")))
        assert emb.backend == "fastembed", emb.backend
        anchors = entity_anchors(emb)
        data = {}
        for rung in RUNGS:
            for d in DISPOS:
                for s in SEEDS:
                    data[(rung, d, s)] = run_subject(sb, d, rung, s, emb, anchors)
                    print(f"[{time.time()-t0:7.1f}s] {rung} {d} seed{s} done", flush=True)
    # ---- analysis (outside the sandbox; aggregated scalars only) ----
    labels = [d for d in DISPOS for _ in SEEDS]
    rng = np.random.default_rng(20260717)
    perms = [rng.permutation(len(labels)) for _ in range(N_PERM)]  # SHARED across rungs
    rows, maxT_null = {}, np.full(N_PERM, -np.inf)
    obs_maxT = -np.inf
    for rung in RUNGS:
        vecs = [data[(rung, d, s)]["offdiag"] for d in DISPOS for s in SEEDS]
        supps = [data[(rung, d, s)]["support"] for d in DISPOS for s in SEEDS]
        T = T_stat(vecs, labels)
        Ts = T_stat(supps, labels)
        rvecs = [resid(v, l) for v, l in zip(vecs, labels)]
        Tr = T_stat(rvecs, labels)
        offstd = float(np.nanmean([np.nanstd(v) for v in vecs]))
        rel = float(np.mean([data[(rung, d, s)]["relabels"] for d in DISPOS for s in SEEDS]))
        traj = np.array([data[(rung, d, s)]["spread_traj"] for d in DISPOS for s in SEEDS])
        obs_maxT = max(obs_maxT, T)
        for k, p in enumerate(perms):
            pl = [labels[i] for i in p]
            maxT_null[k] = max(maxT_null[k], T_stat(vecs, pl))
        # OFF-pattern injection recovery (power gate, statistic-level): add delta to CROSS-block
        # pairs for A-labeled subjects, re-test residualized T.
        cross = np.array([(ENTS[i] in _DISPOSITIONS["A"]) != (ENTS[j] in _DISPOSITIONS["A"])
                          for i, j in combinations(range(K), 2)])
        ivecs = [np.asarray(v, float) + (INJ_DELTA * cross if l == "A" else 0)
                 for v, l in zip(vecs, labels)]
        Ti = T_stat([resid(v, l) for v, l in zip(ivecs, labels)], labels)
        rows[rung] = dict(T=T, T_resid=Tr, T_supp=Ts, offdiag_std=offstd, relabel_mean=rel,
                          spread_final_mean=float(traj[:, -1].mean()),
                          spread_traj_mean=traj.mean(axis=0).round(4).tolist(),
                          inj_T_resid=Ti, inj_recovered=bool(Ti > Tr + INJ_DELTA / 2))
    p_max = float((1 + np.sum(maxT_null >= obs_maxT)) / (1 + N_PERM))
    out["rungs_result"] = rows
    out["primary"] = dict(obs_maxT=obs_maxT, p_max=p_max,
                          null_q95=float(np.quantile(maxT_null, 0.95)))
    dst = REPO / "docs/validation/eval_harness/plasticity_ladder_metrics.json"
    dst.write_text(json.dumps(out, indent=1))
    print(f"\n{'rung':4} {'T':>8} {'T_resid':>8} {'T_supp':>8} {'offdiag_std':>11} "
          f"{'relabels':>8} {'inj_ok':>6}")
    for rung, r in rows.items():
        print(f"{rung:4} {r['T']:+8.3f} {r['T_resid']:+8.3f} {r['T_supp']:+8.3f} "
              f"{r['offdiag_std']:11.4f} {r['relabel_mean']:8.1f} {str(r['inj_recovered']):>6}")
    print(f"\nPRIMARY max-T={obs_maxT:+.3f}  p={p_max:.4f}  (null 95q {out['primary']['null_q95']:+.3f})")
    print(f"[total {time.time()-t0:.0f}s] metrics -> {dst}")


if __name__ == "__main__":
    main()
