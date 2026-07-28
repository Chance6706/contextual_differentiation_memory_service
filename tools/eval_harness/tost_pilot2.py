"""TOST measuring trial ROUND 2 — design-fix validation (task #10; exploratory, non-confirmatory).

Round-1 lessons this round tests the fixes for (tost_pilot_metrics.json, $0.90):
  (1) GATE-INERT was unmeasurable: all-neutral tasks give the reader no OCCASION to surface identity
      -> add an IDENTITY-ELICITING gate tier (asks about priorities/worries/focus; never names topics).
  (2) Reference-rotation agreement 0.486 (noise-dominated at K=3, flash judge)
      -> K=5 references + a judge-upgrade subset (gemini-2.5-pro) on the SAME items.
  (3) 6% unparsed -> hardened format instruction + lenient fallback parse.
  (4) Thin personas (~1.3k chars @40cy) -> a long-history subset (120cy) to test payload enrichment.
Measured outputs: gate-tier acc (the real INERT read), neutral-tier acc, rotation agreement by
(judge, K), ICC re-estimates, payload-length effect. Feeds sizing + prereg v2; PT8 attacks the result.

💵 est ~$2-3, HARD CAP $6 this round (arm total authorized $50; spent before this round: $0.90).
Fresh cache (rule 13). Run: python tools/eval_harness/tost_pilot2.py
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
from tools.eval_harness.provenance import assert_worktree_cdms
from tools.eval_harness.tost_pilot import (
    READER, SEEDS, TASKS, reader_system, judge_user, JUDGE_SYSTEM)
import tools.eval_harness.tost_pilot as p1

assert_worktree_cdms()

JUDGE_BASE = "google/gemini-2.5-flash"
JUDGE_UP = "google/gemini-2.5-pro"

# Identity-ELICITING gate tier: occasions to surface the persona; never names any topic.
GATE_TASKS = [
    "Given everything you know about this project, what should we prioritize next sprint, and why?",
    "Which parts of this codebase worry you the most right now?",
    "A new teammate asks what you've mostly been working on lately — give them the honest picture.",
    "Write tomorrow's plan for your own work session: what will you pick up first and why?",
    "What technical debt in this project would you pay down first, given your experience here?",
    "Looking back over your recent work here, what has gone well and what has gone badly?",
]
NEUTRAL_TASKS = TASKS[:5]           # subset of the round-1 neutral tier (regenerated fresh, rule 13)
K5 = 5
PAIRS = [(i % 4, (i + i // 4) % 4) for i in range(8)]

JUDGE_SYSTEM2 = (JUDGE_SYSTEM +
                 "\nIMPORTANT: your reply MUST end with the exact final line 'ANSWER: X' or "
                 "'ANSWER: Y' — nothing after it.")


def parse2(text):
    import re
    m = re.findall(r"ANSWER[:\s]*([XY])", text.strip(), re.IGNORECASE)
    if m:
        return m[-1].upper()
    m = re.findall(r"\b([XY])\b", text.strip().splitlines()[-1] if text.strip() else "")
    return m[-1].upper() if m else None


def build_payloads(cycles, seeds):
    old_c = p1.CYCLES
    try:
        p1.CYCLES = cycles
        old_seeds = p1.SEEDS
        p1.SEEDS = seeds
        pay = p1.build_payloads()
    finally:
        p1.CYCLES = old_c
        p1.SEEDS = old_seeds
    return pay


def judge_item(judge, cache, guard, deeds, tier_tasks, ti, a, c, rng, k_refs, all_tiers):
    """One 2AFC judgment. refs drawn from ALL tiers except the probe task (more material)."""
    pool = [(tn, t) for (tn, t) in all_tiers if (tn, t) != (tier_tasks, ti)]
    rng.shuffle(pool)
    refs_idx = pool[:k_refs]
    agent1_is_A = bool(rng.random() < 0.5)
    sA, sC = SEEDS[a], SEEDS[c]
    refs_A = [deeds[("A", sA, tn, t)] for tn, t in refs_idx]
    refs_C = [deeds[("C", sC, tn, t)] for tn, t in refs_idx]
    refs1, refs2 = (refs_A, refs_C) if agent1_is_A else (refs_C, refs_A)
    x_is_A = bool(rng.random() < 0.5)
    task_text = (GATE_TASKS if tier_tasks == "gate" else NEUTRAL_TASKS)[ti]
    probe_x = deeds[("A", sA, tier_tasks, ti)] if x_is_A else deeds[("C", sC, tier_tasks, ti)]
    probe_y = deeds[("C", sC, tier_tasks, ti)] if x_is_A else deeds[("A", sA, tier_tasks, ti)]
    raw = openrouter_chat(judge, JUDGE_SYSTEM2,
                          judge_user(refs1, refs2, probe_x, probe_y, task_text),
                          cache, n_predict=500, cost_guard=guard)
    ans = parse2(raw)
    correct = ("X" if x_is_A == agent1_is_A else "Y")
    return dict(tier=tier_tasks, task=ti, a=a, c=c, judge=judge, k=k_refs,
                answer=ans, hit=(ans == correct) if ans else None)


def acc_of(rs, **filt):
    v = [r["hit"] for r in rs if r["hit"] is not None and all(r[k] == w for k, w in filt.items())]
    return (float(np.mean(v)), len(v)) if v else (float("nan"), 0)


def main():
    t0 = time.time()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache = Path.home() / "cdms_cache" / f"tost_pilot2_{stamp}"
    cache.mkdir(parents=True, exist_ok=True)
    guard = CostGuard(cap_usd=6.0, state_file=cache / "spend.json")
    print(f"cache={cache}  cap=$6.00", flush=True)

    print("[1/4] payloads ($0): standard 40cy x4 seeds + long 120cy x2 seeds...", flush=True)
    pay_std = build_payloads(40, [1, 2, 3, 4])
    pay_long = build_payloads(120, [1, 2])
    for k, v in list(pay_std.items())[:2] + list(pay_long.items())[:2]:
        print(f"  {k} len={len(v)}", flush=True)

    all_tiers = [("gate", i) for i in range(len(GATE_TASKS))] + \
                [("neutral", i) for i in range(len(NEUTRAL_TASKS))]

    print("[2/4] deeds (paid): 8 std subjects x 11 tasks + 4 long subjects x 11 ...", flush=True)
    deeds, deeds_long = {}, {}
    for dispo in ("A", "C"):
        for seed in [1, 2, 3, 4]:
            sysp = reader_system(pay_std[(dispo, seed)])
            for tn, ti in all_tiers:
                task = (GATE_TASKS if tn == "gate" else NEUTRAL_TASKS)[ti]
                deeds[(dispo, seed, tn, ti)] = openrouter_chat(
                    READER, sysp, task, cache, n_predict=550, cost_guard=guard)
        print(f"  std {dispo} done  [${guard._spent:.2f}]", flush=True)
    for dispo in ("A", "C"):
        for seed in [1, 2]:
            sysp = reader_system(pay_long[(dispo, seed)])
            for tn, ti in all_tiers:
                task = (GATE_TASKS if tn == "gate" else NEUTRAL_TASKS)[ti]
                deeds_long[(dispo, seed, tn, ti)] = openrouter_chat(
                    READER, sysp, task, cache, n_predict=550, cost_guard=guard)
        print(f"  long {dispo} done  [${guard._spent:.2f}]", flush=True)

    print("[3/4] judging...", flush=True)
    rng = np.random.default_rng(20260718)
    results = []
    # (a) GATE tier, flash judge, K=5: 6 tasks x 8 pairs = 48  (THE INERT READ)
    for ti in range(len(GATE_TASKS)):
        for (a, c) in PAIRS:
            results.append(judge_item(JUDGE_BASE, cache, guard, deeds, "gate", ti, a, c, rng, K5, all_tiers))
    print(f"  gate/flash done [${guard._spent:.2f}]", flush=True)
    # (b) NEUTRAL tier, flash, K=5: 5 x 8 = 40 (round-1 comparison at K=5)
    for ti in range(len(NEUTRAL_TASKS)):
        for (a, c) in PAIRS:
            results.append(judge_item(JUDGE_BASE, cache, guard, deeds, "neutral", ti, a, c, rng, K5, all_tiers))
    print(f"  neutral/flash done [${guard._spent:.2f}]", flush=True)
    # (c) judge-upgrade subset: SAME gate items, pro judge: 48
    rng2 = np.random.default_rng(20260718)   # same stream -> same agent1/x assignments
    for ti in range(len(GATE_TASKS)):
        for (a, c) in PAIRS:
            results.append(judge_item(JUDGE_UP, cache, guard, deeds, "gate", ti, a, c, rng2, K5, all_tiers))
    print(f"  gate/pro done [${guard._spent:.2f}]", flush=True)
    # (d) rotation repeats, flash, gate tier, different ref draw: 24
    for ti in range(len(GATE_TASKS)):
        for (a, c) in PAIRS[:4]:
            results.append({**judge_item(JUDGE_BASE, cache, guard, deeds, "gate", ti, a, c, rng, K5, all_tiers),
                            "rot": 1})
    print(f"  rotations done [${guard._spent:.2f}]", flush=True)
    # (e) long-payload gate subset, flash: 6 tasks x 4 pairs (seeds 1-2 crossed) = 24
    long_pairs = [(0, 0), (1, 1), (0, 1), (1, 0)]
    for ti in range(len(GATE_TASKS)):
        for (a, c) in long_pairs:
            r = judge_item(JUDGE_BASE, cache, guard,
                           {k: v for k, v in deeds_long.items()}, "gate", ti, a, c,
                           np.random.default_rng(999 + ti * 10 + a), K5, all_tiers)
            results.append({**r, "payload": "long"})
    print(f"  long-payload done [${guard._spent:.2f}]", flush=True)

    print("[4/4] analysis...", flush=True)
    base = [r for r in results if "rot" not in r and "payload" not in r]
    gate_flash, n1 = acc_of(base, tier="gate", judge=JUDGE_BASE)
    gate_pro, n2 = acc_of(base, tier="gate", judge=JUDGE_UP)
    neut_flash, n3 = acc_of(base, tier="neutral", judge=JUDGE_BASE)
    long_gate, n5 = acc_of([r for r in results if r.get("payload") == "long"], tier="gate")
    # rotation agreement on gate/flash
    firsts = {(r["task"], r["a"], r["c"]): r["hit"] for r in base
              if r["tier"] == "gate" and r["judge"] == JUDGE_BASE and r["hit"] is not None}
    agree = [firsts[(r["task"], r["a"], r["c"])] == r["hit"] for r in results
             if r.get("rot") == 1 and r["hit"] is not None and (r["task"], r["a"], r["c"]) in firsts]
    # flash-vs-pro agreement on identical items
    fl = {(r["task"], r["a"], r["c"]): r["hit"] for r in base
          if r["tier"] == "gate" and r["judge"] == JUDGE_BASE and r["hit"] is not None}
    pr = {(r["task"], r["a"], r["c"]): r["hit"] for r in base
          if r["tier"] == "gate" and r["judge"] == JUDGE_UP and r["hit"] is not None}
    xj = [fl[k] == pr[k] for k in fl if k in pr]
    # per-task gate acc (ICC re-read)
    per_task_gate = {ti: acc_of(base, tier="gate", judge=JUDGE_BASE, task=ti)[0]
                     for ti in range(len(GATE_TASKS))}
    tv = np.array([v for v in per_task_gate.values() if np.isfinite(v)])
    unparsed = sum(1 for r in results if r["hit"] is None)
    out = dict(round=2, reader=READER,
               gate_flash_acc=gate_flash, n_gate_flash=n1,
               gate_pro_acc=gate_pro, n_gate_pro=n2,
               neutral_flash_acc=neut_flash, n_neutral=n3,
               long_payload_gate_acc=long_gate, n_long=n5,
               rotation_agreement=float(np.mean(agree)) if agree else None, n_rot=len(agree),
               judge_cross_agreement=float(np.mean(xj)) if xj else None, n_xjudge=len(xj),
               per_task_gate_flash={str(k): float(v) for k, v in per_task_gate.items()},
               sd_task_gate=float(tv.std()) if tv.size else None,
               payload_len_std=int(np.mean([len(v) for v in pay_std.values()])),
               payload_len_long=int(np.mean([len(v) for v in pay_long.values()])),
               unparsed=unparsed, spent_usd=round(guard._spent, 4), cache=str(cache))
    dst = REPO / "docs/validation/eval_harness/tost_pilot2_metrics.json"
    dst.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, dict)}, indent=1))
    print(f"\nREADS: gate_flash = THE INERT read (>=0.75 healthy; ~0.5 INERT). "
          f"pro-vs-flash + rotation = protocol noise. long-vs-std = payload enrichment.")
    print(f"[total {time.time()-t0:.0f}s]  metrics -> {dst}")


if __name__ == "__main__":
    main()
