"""THE FUNCTIONAL TOST — main confirmatory run (task #10; FUNCTIONAL_TOST_PREREG.md v3-FINAL).

The terminal falsifier of the CDMS-A individuation thesis. Implements the locked design exactly:
valence-matched fixture, S=24 seeds/disposition, T=20 frozen eliciting tasks, pooled K=5 refs,
masker v3, flash judge primary + pro subset, SETS 3-way bootstrap B=10,000, mechanized verdict with
gate precedence. Per-item JSONL for every arm; caches RETAINED (no burn — feeds the pre-authorized
$0 re-analysis paths).

💵 est ~$13-16, HARD CAP $30 (CostGuard). Arm total ≤ $50 (spent $5.04 through pilots).
Wall-clock ≈ 2.5-4 h. Fresh cache (rule 13). Run: python tools/eval_harness/tost_main.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

os.environ.setdefault("CDMS_EVAL_MODE", "1")
os.environ.setdefault("CDMS_EMBED_BACKEND", "fastembed")

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from openrouter_chat import openrouter_chat
from openrouter_cost_guard import CostGuard
import tools.eval_harness.differentiation_experiment as fixture
from tools.eval_harness.provenance import assert_worktree_cdms
from tools.eval_harness.tost_pilot import READER, reader_system, judge_user, TASKS as NEUTRAL10
from tools.eval_harness.tost_pilot2 import (GATE_TASKS, JUDGE_BASE, JUDGE_SYSTEM2, parse2,
                                            build_payloads)
from tools.eval_harness.tost_pilot3 import MATCHED_SUCCESS, strip_v3, bow_2afc, bow_tokens

assert_worktree_cdms()

JUDGE_PRO = "google/gemini-2.5-pro"
SEEDS = list(range(1, 25))                    # S = 24
TASKS20 = GATE_TASKS + [                      # 6 measured + 14 fresh, same eliciting genre (FROZEN)
    "If you had to hand this project to someone else next week, what would you warn them about?",
    "What would you most want to automate or make self-serve in this project, and why?",
    "Where do you think this project will hurt most in six months if nothing changes?",
    "You get one uninterrupted day on this project - what do you spend it on, and what do you deliberately ignore?",
    "A stakeholder asks for a status update in three sentences. Give it.",
    "What is the riskiest change you would still argue is worth making soon?",
    "Which recent work here are you most confident in, and which least?",
    "What would you cut from the roadmap if the team lost half its time, and what stays?",
    "Write a short note to your future self about what to keep an eye on here.",
    "What kind of bug report would worry you most right now?",
    "If you could add one safeguard to this project this week, what would it be?",
    "What part of the work here do you find yourself putting off, and why?",
    "A new tool budget arrives - what do you buy or set up first for this project?",
    "What would 'a great next month' look like for this project?",
]
assert len(TASKS20) == 20
FRESH14 = list(range(6, 20))                  # robustness-gate subset (indices of the 14 fresh)
NEUTRAL5 = NEUTRAL10[:5]
DELTA = 0.10
B_MAIN = 10_000


def jitem(src, tasks, ti, sa, sc, refs_idx, a1A, xA, judge, cache, guard, n_pred=500, reasoning=None):
    """One 2AFC judgment with pinned balance booleans + one re-ask on unparse."""
    rA = [src[("A", s, t)] for s, t in refs_idx]
    rC = [src[("C", s, t)] for s, t in refs_idx]
    r1, r2 = (rA, rC) if a1A else (rC, rA)
    px = src[("A", sa, ti)] if xA else src[("C", sc, ti)]
    py = src[("C", sc, ti)] if xA else src[("A", sa, ti)]
    user = judge_user(r1, r2, px, py, tasks[ti])
    kw = dict(cache=cache, n_predict=n_pred, cost_guard=guard)
    if reasoning:
        kw["reasoning"] = reasoning
    raw = openrouter_chat(judge, JUDGE_SYSTEM2, user, **kw)
    ans = parse2(raw)
    reasked = False
    if ans is None:
        reasked = True
        raw2 = openrouter_chat(judge, JUDGE_SYSTEM2,
                               user + "\n\nReply with only ANSWER: X or ANSWER: Y", **kw)
        ans = parse2(raw2)
    correct = "X" if xA == a1A else "Y"
    return dict(answer=ans, correct=correct, hit=(ans == correct) if ans else None,
                reasked=reasked)


def pooled_refs(rng, ti, sa, sc, n_tasks, k=5):
    pool = [(s, t) for s in SEEDS for t in range(n_tasks) if s not in (sa, sc) and t != ti]
    rng.shuffle(pool)
    return pool[:k]


def sets_boot(items_arr, lo_q, hi_q, nboot, rng):
    Tn = len(TASKS20)
    stats = []
    for _ in range(nboot):
        ti = set(rng.integers(0, Tn, Tn))
        ai = set(rng.integers(1, 25, 24))
        ci = set(rng.integers(1, 25, 24))
        m = np.array([r[0] in ti and r[1] in ai and r[2] in ci for r in items_arr])
        if m.sum() < 20:
            continue
        stats.append(items_arr[m, 3].mean())
    return float(np.quantile(stats, lo_q)), float(np.quantile(stats, hi_q))


def main():
    t0 = time.time()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache = Path.home() / "cdms_cache" / f"tost_main_{stamp}"
    cache.mkdir(parents=True, exist_ok=True)
    guard = CostGuard(cap_usd=30.0, state_file=cache / "spend.json")
    items_path = REPO / "docs/validation/eval_harness/tost_main_items.jsonl"
    fitems = open(items_path, "w")
    def log_item(arm, **kw):
        fitems.write(json.dumps(dict(arm=arm, **kw)) + "\n")
        fitems.flush()
    print(f"cache={cache} cap=$30", flush=True)

    print("[1/5] payloads ($0, 48 subjects, ~20 min)...", flush=True)
    old = fixture._ENTITY_SUCCESS
    try:
        fixture._ENTITY_SUCCESS = MATCHED_SUCCESS
        pay = build_payloads(40, SEEDS)
    finally:
        fixture._ENTITY_SUCCESS = old
    print(f"  done, mean len {int(np.mean([len(v) for v in pay.values()]))}", flush=True)

    print("[2/5] deeds: 960 eliciting + 80 neutral (paid)...", flush=True)
    deeds, deeds_neutral = {}, {}
    for d in ("A", "C"):
        for s in SEEDS:
            sysp = reader_system(pay[(d, s)])
            for ti, task in enumerate(TASKS20):
                deeds[(d, s, ti)] = openrouter_chat(READER, sysp, task, cache,
                                                    n_predict=550, cost_guard=guard)
            if s <= 8:
                for ti, task in enumerate(NEUTRAL5):
                    deeds_neutral[(d, s, ti)] = openrouter_chat(READER, sysp, task, cache,
                                                                n_predict=550, cost_guard=guard)
        print(f"  {d} done [${guard._spent:.2f}]", flush=True)
    stripped = {k: strip_v3(v) for k, v in deeds.items()}
    stripped_neutral = {k: strip_v3(v) for k, v in deeds_neutral.items()}

    print("[3/5] judging...", flush=True)
    rng = np.random.default_rng(20260723)
    # ---- REAL: 800 stripped pooled (balanced booleans) ----
    real = []
    idx = 0
    for ti in range(20):
        for i in range(40):
            sa, sc = SEEDS[i % 24], SEEDS[(i + 1 + i // 24) % 24]
            refs = pooled_refs(rng, ti, sa, sc, 20)
            a1A, xA = (idx % 2 == 0), ((idx // 2) % 2 == 0)
            r = jitem(stripped, TASKS20, ti, sa, sc, refs, a1A, xA, JUDGE_BASE, cache, guard)
            real.append((ti, sa, sc, r["hit"], r["reasked"]))
            log_item("REAL", task=ti, sa=sa, sc=sc, a1A=a1A, xA=xA, **r)
            idx += 1
        print(f"  REAL task {ti+1}/20 [${guard._spent:.2f}]", flush=True)
    # ---- EXPRESSION gate: 48 same-seed unstripped ----
    expr = []
    for k in range(48):
        ti, sa = k % 20, SEEDS[k % 24]
        sc = sa
        pool = [(sa, t) for t in range(20) if t != ti]
        rng.shuffle(pool)
        refs = pool[:5]
        a1A, xA = (k % 2 == 0), ((k // 2) % 2 == 0)
        r = jitem(deeds, TASKS20, ti, sa, sc, refs, a1A, xA, JUDGE_BASE, cache, guard)
        expr.append(r["hit"])
        log_item("EXPRESSION", task=ti, seed=sa, a1A=a1A, xA=xA, **r)
    print(f"  EXPRESSION done [${guard._spent:.2f}]", flush=True)
    # ---- POOLED-UNSTRIPPED: 100 ----
    pun = []
    for k in range(100):
        ti = k % 20
        sa, sc = SEEDS[k % 24], SEEDS[(k + 7) % 24]
        refs = pooled_refs(rng, ti, sa, sc, 20)
        a1A, xA = (k % 2 == 0), ((k // 2) % 2 == 0)
        r = jitem(deeds, TASKS20, ti, sa, sc, refs, a1A, xA, JUDGE_BASE, cache, guard)
        pun.append(r["hit"])
        log_item("POOLED_UNSTRIPPED", task=ti, sa=sa, sc=sc, a1A=a1A, xA=xA, **r)
    print(f"  POOLED-UNSTRIPPED done [${guard._spent:.2f}]", flush=True)
    # ---- NULL: 100 A-vs-A stripped pooled (X-rate balance) ----
    null_x = []
    for k in range(100):
        ti = k % 20
        sa, sb = SEEDS[k % 24], SEEDS[(k + 11) % 24]
        pool = [(s, t) for s in SEEDS for t in range(20) if s not in (sa, sb) and t != ti]
        rng.shuffle(pool)
        refs = pool[:5]
        rA = [stripped[("A", s, t)] for s, t in refs]
        rC = [stripped[("C", s, t)] for s, t in refs]
        x_first = (k % 2 == 0)
        pa, pb = stripped[("A", sa, ti)], stripped[("A", sb, ti)]
        raw = openrouter_chat(JUDGE_BASE, JUDGE_SYSTEM2,
                              judge_user(rA, rC, pa if x_first else pb, pb if x_first else pa,
                                         TASKS20[ti]),
                              cache, n_predict=500, cost_guard=guard)
        ans = parse2(raw)
        if ans:
            null_x.append(ans == "X")
        log_item("NULL", task=ti, sa=sa, sb=sb, x_first=x_first, answer=ans)
    print(f"  NULL done [${guard._spent:.2f}]", flush=True)
    # ---- PRO subset: first 100 REAL items re-judged ----
    pro = []
    rng2 = np.random.default_rng(20260724)
    for k in range(100):
        ti = k % 20
        i = k % 40
        sa, sc = SEEDS[i % 24], SEEDS[(i + 1 + i // 24) % 24]
        refs = pooled_refs(rng2, ti, sa, sc, 20)
        a1A, xA = (k % 2 == 0), ((k // 2) % 2 == 0)
        try:
            r = jitem(stripped, TASKS20, ti, sa, sc, refs, a1A, xA, JUDGE_PRO, cache, guard,
                      n_pred=2000, reasoning={"effort": "low"})
        except Exception as e:
            r = dict(answer=None, correct="?", hit=None, reasked=False)
        pro.append(r["hit"])
        log_item("PRO", task=ti, sa=sa, sc=sc, **{k2: v for k2, v in r.items()})
    print(f"  PRO done [${guard._spent:.2f}]", flush=True)
    # ---- NEUTRAL secondary: 48 stripped pooled on neutral tasks ----
    neu = []
    for k in range(48):
        ti = k % 5
        sa, sc = (k % 8) + 1, ((k + 3) % 8) + 1
        pool = [(s, t) for s in range(1, 9) for t in range(5) if s not in (sa, sc) and t != ti]
        rng.shuffle(pool)
        refs = pool[:5]
        a1A, xA = (k % 2 == 0), ((k // 2) % 2 == 0)
        r = jitem(stripped_neutral, NEUTRAL5, ti, sa, sc, refs, a1A, xA, JUDGE_BASE, cache, guard)
        neu.append(r["hit"])
        log_item("NEUTRAL", task=ti, sa=sa, sc=sc, **r)
    fitems.close()
    print(f"  NEUTRAL done [${guard._spent:.2f}]", flush=True)

    print("[4/5] analysis...", flush=True)
    arr = np.array([(t, a, c, h) for (t, a, c, h, _) in real if h is not None], dtype=float)
    n_unparsed = sum(1 for (*_, h, _) in real if h is None)
    unparse_rate = n_unparsed / len(real)
    acc = float(arr[:, 3].mean())
    brng = np.random.default_rng(99)
    lo90, hi90 = sets_boot(arr, 0.05, 0.95, B_MAIN, brng)
    diff_rej = lo90 > 0.5
    tost_rej = (lo90 > 0.5 - DELTA) and (hi90 < 0.5 + DELTA)
    # impute-as-miss sensitivity
    arr_miss = np.array([(t, a, c, (h if h is not None else 0.0))
                         for (t, a, c, h, _) in real], dtype=float)
    lo90m, hi90m = sets_boot(arr_miss, 0.05, 0.95, 2000, brng)
    diff_m, tost_m = lo90m > 0.5, (lo90m > 0.4 and hi90m < 0.6)
    # fresh-14 robustness
    arr14 = arr[np.isin(arr[:, 0], FRESH14)]
    lo14, _ = sets_boot(arr14, 0.05, 0.95, 2000, brng)
    # sig_t guard
    per_task = [arr[arr[:, 0] == t, 3].mean() for t in range(20) if (arr[:, 0] == t).sum() > 5]
    tv = np.array(per_task)
    n_pt = len(arr) / 20
    sd_corr = max(0.0, tv.var() - acc * (1 - acc) / n_pt) ** 0.5
    sig_t_est = sd_corr / max(acc * (1 - acc), 1e-6)
    # gates
    e_ok = [h for h in expr if h is not None]
    expr_acc = float(np.mean(e_ok))
    expr_lb = float(np.quantile([np.mean(np.random.default_rng(i).choice(e_ok, len(e_ok)))
                                 for i in range(2000)], 0.05))
    nx = float(np.mean(null_x)) if null_x else float("nan")
    band = [np.mean(np.random.default_rng(i).random(len(null_x)) < 0.5) for i in range(1000)]
    null_ok = (np.quantile(band, 0.025) <= nx <= np.quantile(band, 0.975))
    # BOW gates ($0)
    leak_items = [(ti, SEEDS[k % 24], SEEDS[(k + 5) % 24]) for ti in range(20) for k in (0, 8)]
    bow_leak = bow_2afc(stripped, leak_items, lambda s, t, ti, sa, sc: s in SEEDS[:12] and s not in (sa, sc))
    bow_loso = bow_2afc(stripped, leak_items, lambda s, t, ti, sa, sc: s not in (sa, sc))
    pro_acc = float(np.mean([h for h in pro if h is not None])) if any(h is not None for h in pro) else float("nan")
    neu_acc = float(np.mean([h for h in neu if h is not None]))

    # ---- verdict mechanization (precedence per §1) ----
    if unparse_rate > 0.12:
        verdict = "PROTOCOL-FAILURE (unparse > 12%)"
    elif not null_ok:
        verdict = "INVALID (GATE-MANUFACTURE: null outside permutation band)"
    elif expr_lb < 0.80:
        verdict = "EXPRESSION-INERT (reader does not enact the payload; no thesis verdict)"
    else:
        if diff_rej and not tost_rej:
            branch = "DISTINGUISHABLE"
            if not (lo14 > 0.5):
                branch = "INCONCLUSIVE (fresh-14 robustness gate failed)"
        elif tost_rej and not diff_rej:
            branch = "EQUIVALENT — THESIS FALSE, HALT"
            if sig_t_est > 0.4:
                branch = "INCONCLUSIVE (sig_t guard: task heterogeneity too high for a trustworthy equivalence)"
        else:
            branch = "INCONCLUSIVE"
        if branch.startswith(("DISTINGUISHABLE", "EQUIVALENT")):
            agree = (diff_rej == diff_m) and (tost_rej == tost_m)
            if not agree:
                branch = "INCONCLUSIVE (unparse dual-analysis disagreement)"
        verdict = branch

    out = dict(design="v3-FINAL", acc_real=acc, n_real=int(len(arr)), ci90=[lo90, hi90],
               diff_rejects=bool(diff_rej), tost_rejects=bool(tost_rej),
               impute_ci90=[lo90m, hi90m], fresh14_lb=lo14, sig_t_est=float(sig_t_est),
               unparse_rate=round(unparse_rate, 4),
               expression_acc=expr_acc, expression_lb90=expr_lb,
               pooled_unstripped_acc=float(np.mean([h for h in pun if h is not None])),
               null_x_rate=nx, null_in_band=bool(null_ok),
               bow_leak=bow_leak, bow_loso=bow_loso,
               pro_subset_acc=pro_acc, neutral_acc=neu_acc,
               verdict=verdict, spent_usd=round(guard._spent, 4), cache=str(cache))
    dst = REPO / "docs/validation/eval_harness/tost_main_metrics.json"
    dst.write_text(json.dumps(out, indent=1))
    print("[5/5] " + json.dumps(out, indent=1), flush=True)
    print(f"\nVERDICT: {verdict}")
    print(f"[total {time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
