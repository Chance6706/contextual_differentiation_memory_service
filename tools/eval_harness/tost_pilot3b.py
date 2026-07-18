"""TOST pilot 3b — anchor-collapse disambiguator (exploratory; ~$1.3, cap $3).

Pilot 3's UNSTRIPPED anchor fell 1.000 -> 0.50 under three simultaneous changes (valence-matched
fixture, stance-genre tasks, pooled refs). Factorial on the ANCHOR measurement (unstripped, pooled
refs, flash judge) to isolate the killer:
  cell R (refs):    eliciting tasks x UNMATCHED fixture, pooled refs  [deeds = pilot2 cache, $0]
  cell F (fixture): eliciting tasks x MATCHED fixture,   pooled refs  [new deeds]
  cell G (genre):   stance tasks    x UNMATCHED fixture, pooled refs  [new deeds]
Reference points: pilot2 (eliciting, unmatched, SAME-seed refs) = 1.000; pilot3 (stance, matched,
pooled) = 0.50. Reading: R vs 1.000 = the refs effect; F vs R = the fixture effect; G vs R = the
genre effect.
Run: python tools/eval_harness/tost_pilot3b.py
"""
from __future__ import annotations

import json, os, sys, time
from datetime import datetime
from pathlib import Path

os.environ.setdefault("CDMS_EVAL_MODE", "1")
os.environ.setdefault("CDMS_EMBED_BACKEND", "fastembed")
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(REPO / "tools"))

from openrouter_chat import openrouter_chat
from openrouter_cost_guard import CostGuard
import tools.eval_harness.differentiation_experiment as fixture
from tools.eval_harness.provenance import assert_worktree_cdms
from tools.eval_harness.tost_pilot import READER, reader_system, judge_user
from tools.eval_harness.tost_pilot2 import GATE_TASKS, JUDGE_BASE, JUDGE_SYSTEM2, parse2, build_payloads
from tools.eval_harness.tost_pilot3 import MATCHED_SUCCESS, STANCE_TASKS

assert_worktree_cdms()
SEEDS4 = [1, 2, 3, 4]


def judge_pooled(src, tasks, ti, sa, sc, guard, cache, rng):
    pool = [(s, t) for s in SEEDS4 for t in range(len(tasks)) if s not in (sa, sc) and t != ti]
    rng.shuffle(pool)
    refs_idx = pool[:5]
    a1A = bool(rng.random() < 0.5)
    rA = [src[("A", s, t)] for s, t in refs_idx]
    rC = [src[("C", s, t)] for s, t in refs_idx]
    r1, r2 = (rA, rC) if a1A else (rC, rA)
    xA = bool(rng.random() < 0.5)
    px = src[("A", sa, ti)] if xA else src[("C", sc, ti)]
    py = src[("C", sc, ti)] if xA else src[("A", sa, ti)]
    raw = openrouter_chat(JUDGE_BASE, JUDGE_SYSTEM2, judge_user(r1, r2, px, py, tasks[ti]),
                          cache, n_predict=500, cost_guard=guard)
    ans = parse2(raw)
    return (ans == ("X" if xA == a1A else "Y")) if ans else None


def gen_deeds(payloads, tasks, cache, guard, seeds=SEEDS4):
    out = {}
    for d in ("A", "C"):
        for s in seeds:
            sysp = reader_system(payloads[(d, s)])
            for ti, task in enumerate(tasks):
                out[(d, s, ti)] = openrouter_chat(READER, sysp, task, cache,
                                                  n_predict=550, cost_guard=guard)
    return out


def run_cell(name, deeds, tasks, guard, cache, n_items=24):
    rng = np.random.default_rng(hash(name) % 2**31)
    hits = []
    k = 0
    for ti in range(len(tasks)):
        for _ in range(max(1, n_items // len(tasks))):
            sa, sc = SEEDS4[k % 4], SEEDS4[(k + 1 + k // 4) % 4]
            h = judge_pooled(deeds, tasks, ti, sa, sc, guard, cache, rng)
            if h is not None:
                hits.append(h)
            k += 1
    return float(np.mean(hits)), len(hits)


def main():
    t0 = time.time()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache = Path.home() / "cdms_cache" / f"tost_pilot3b_{stamp}"
    cache.mkdir(parents=True, exist_ok=True)
    guard = CostGuard(cap_usd=3.0, state_file=cache / "spend.json")
    pilot2_cache = Path.home() / "cdms_cache" / "tost_pilot2_20260717_224533"

    print("[1/3] payloads ($0): unmatched x4 + matched x4...", flush=True)
    pay_unmatched = build_payloads(40, SEEDS4)
    old = fixture._ENTITY_SUCCESS
    try:
        fixture._ENTITY_SUCCESS = MATCHED_SUCCESS
        pay_matched = build_payloads(40, SEEDS4)
    finally:
        fixture._ENTITY_SUCCESS = old

    print("[2/3] deeds: cell R from pilot2 cache ($0); cells F,G fresh...", flush=True)
    deeds_R = gen_deeds(pay_unmatched, GATE_TASKS, pilot2_cache, guard)  # cache HITS, $0
    print(f"  R loaded [${guard._spent:.2f}]", flush=True)
    deeds_F = gen_deeds(pay_matched, GATE_TASKS, cache, guard)
    print(f"  F done [${guard._spent:.2f}]", flush=True)
    deeds_G = gen_deeds(pay_unmatched, STANCE_TASKS, cache, guard)
    print(f"  G done [${guard._spent:.2f}]", flush=True)

    print("[3/3] judging 3 cells x 24 (unstripped, pooled refs)...", flush=True)
    accR, nR = run_cell("R", deeds_R, GATE_TASKS, guard, cache)
    print(f"  R(elicit,unmatched,pooled) = {accR:.3f} (n={nR}) [${guard._spent:.2f}]", flush=True)
    accF, nF = run_cell("F", deeds_F, GATE_TASKS, guard, cache)
    print(f"  F(elicit,MATCHED,pooled)   = {accF:.3f} (n={nF}) [${guard._spent:.2f}]", flush=True)
    accG, nG = run_cell("G", deeds_G, STANCE_TASKS, guard, cache)
    print(f"  G(STANCE,unmatched,pooled) = {accG:.3f} (n={nG}) [${guard._spent:.2f}]", flush=True)

    out = dict(round="3b", cell_R_refs=accR, n_R=nR, cell_F_fixture=accF, n_F=nF,
               cell_G_genre=accG, n_G=nG,
               ref_pilot2_sameseed=1.0, ref_pilot3_all_new=0.5,
               spent_usd=round(guard._spent, 4), cache=str(cache))
    (REPO / "docs/validation/eval_harness/tost_pilot3b_metrics.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print("\nREAD: R<<1.0 => pooled-refs did it; F<<R => valence-matching did it; G<<R => genre did it.")
    print(f"[total {time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
