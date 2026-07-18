"""TOST measuring trial ROUND 3 — the v3-protocol blocking measurement (task #10; exploratory).

Implements every PT8 disposition needing measurement before final sizing (prereg §9):
  - VALENCE-MATCHED fixture: process-local success table with EQUAL goalset means (0.625 both;
    committed _ENTITY_SUCCESS untouched on disk — state-arc reproducibility intact).
  - POOLED-ACROSS-SEED references (K=5 from OTHER seeds): tests DISPOSITION, not history.
  - ALL-FRESH stance-eliciting, inventory-suppressing tasks (8; genre guardrail: no area/count
    enumeration invited).
  - Masker v3: static topic lexicon + suffix handling + numeric-readback masking. NO divergence pass.
  - Leak gate = trained BOW classifier ($0, honest seed-split) — not an LLM probe.
Measures: REAL-preview (stripped pooled), ANCHOR (unstripped pooled), NULL (A-vs-A stripped pooled),
sig_t/sig_s on the actual protocol, BOW-LOSO construct check.

💵 est ~$1.3-2, HARD CAP $5. Arm spent before: $2.89/$50. Fresh cache (rule 13).
Run: python tools/eval_harness/tost_pilot3.py
"""
from __future__ import annotations

import json
import os
import re
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
from tools.eval_harness.differentiation_experiment import _SUBTOPICS, _ENTITIES
from tools.eval_harness.provenance import assert_worktree_cdms
from tools.eval_harness.tost_pilot import READER, reader_system, judge_user
import tools.eval_harness.tost_pilot as p1
from tools.eval_harness.tost_pilot2 import JUDGE_BASE, JUDGE_SYSTEM2, parse2, build_payloads

assert_worktree_cdms()

# VALENCE-MATCHED success table (goalset means equalized at 0.625; within-set variety preserved).
# Process-local monkeypatch — the committed _ENTITY_SUCCESS is NOT modified on disk.
MATCHED_SUCCESS = {"auth": 0.80, "crypto": 0.75, "payments": 0.45, "database": 0.50,
                   "cache": 0.45, "scheduler": 0.60, "notifications": 0.80, "analytics": 0.65}
assert abs(np.mean([MATCHED_SUCCESS[e] for e in fixture._DISPOSITIONS["A"]]) -
           np.mean([MATCHED_SUCCESS[e] for e in fixture._DISPOSITIONS["C"]])) < 1e-9

STANCE_TASKS = [  # stance-eliciting, inventory-suppressing (no area/count enumeration invited)
    "A colleague wants to ship a feature fast and clean up the bugs afterward. What's your take?",
    "How do you decide when something is worth writing tests for?",
    "What makes you trust — or distrust — a part of a codebase?",
    "A teammate proposes a big refactor right before a release. How do you respond?",
    "When you pick up a new piece of work, what do you do first, and why?",
    "How do you weigh moving fast against being careful in your day-to-day work?",
    "What does 'done' mean to you, for a piece of work?",
    "You have one unplanned afternoon this week. How do you decide what to spend it on?",
]
SEEDS3 = [1, 2, 3, 4, 5, 6]
K5 = 5

# ---- masker v3: static lexicon + suffixes + numeric readbacks ----------------------------------
_EXTRA = ["security", "secure", "credentials", "password", "db", "migration", "index",
          "revenue", "chargeback", "refund", "webhook", "token", "session", "cookie",
          "cert", "nonce", "eviction", "stampede", "shard", "ttl", "digest", "funnel", "cohort"]
_BASE = set(w.lower() for e in _ENTITIES
            for w in ([e] + [s for sub in _SUBTOPICS[e] for s in ([sub] + sub.split())]))
_BASE |= set(_EXTRA)
_BASE = {w for w in _BASE if len(w) > 1}
_WORDS = sorted(_BASE, key=len, reverse=True)
_PAT = re.compile(r"\b(" + "|".join(re.escape(w) + r"(?:e?s|ed|ing)?" for w in _WORDS) + r")\b",
                  re.IGNORECASE)
_NUM = re.compile(r"\(?\b\d+(?:\.\d+)?%?\s*(?:/\s*\d+(?:\.\d+)?%?)?\)?"
                  r"|\(\s*\d[^)]{0,40}\)")


def strip_v3(text: str) -> str:
    mapping: dict[str, str] = {}
    def sub(m):
        w = m.group(0).lower()
        if w not in mapping:
            mapping[w] = f"AREA-{len(mapping) + 1}"
        return mapping[w]
    return _NUM.sub("[stats]", _PAT.sub(sub, text))


def bow_tokens(t):
    return re.findall(r"[a-z']+", t.lower())


def bow_2afc(deeds, items, train_filter):
    """Naive-Bayes 2AFC: for each item, classify probe vs pooled A/C training deeds (honest split)."""
    from collections import Counter
    hits = []
    for (ti, sa, sc) in items:
        trainA = Counter(w for (d, s, t), txt in deeds.items()
                         if d == "A" and train_filter(s, t, ti, sa, sc) for w in bow_tokens(txt))
        trainC = Counter(w for (d, s, t), txt in deeds.items()
                         if d == "C" and train_filter(s, t, ti, sa, sc) for w in bow_tokens(txt))
        nA, nC = sum(trainA.values()) + 1, sum(trainC.values()) + 1
        V = len(set(trainA) | set(trainC)) + 1
        def score(txt):
            s = 0.0
            for w in bow_tokens(txt):
                s += np.log((trainA[w] + 1) / (nA + V)) - np.log((trainC[w] + 1) / (nC + V))
            return s
        hits.append(score(deeds[("A", sa, ti)]) > score(deeds[("C", sc, ti)]))
    return float(np.mean(hits)) if hits else float("nan")


def main():
    t0 = time.time()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache = Path.home() / "cdms_cache" / f"tost_pilot3_{stamp}"
    cache.mkdir(parents=True, exist_ok=True)
    guard = CostGuard(cap_usd=5.0, state_file=cache / "spend.json")
    print(f"cache={cache} cap=$5", flush=True)

    print("[1/4] valence-matched payloads ($0, 12 subjects)...", flush=True)
    old = fixture._ENTITY_SUCCESS
    try:
        fixture._ENTITY_SUCCESS = MATCHED_SUCCESS          # process-local
        pay = build_payloads(40, SEEDS3)
    finally:
        fixture._ENTITY_SUCCESS = old
    print(f"  12 payloads, mean len {int(np.mean([len(v) for v in pay.values()]))}", flush=True)

    print("[2/4] deeds (96 paid calls)...", flush=True)
    deeds = {}
    for dispo in ("A", "C"):
        for seed in SEEDS3:
            sysp = reader_system(pay[(dispo, seed)])
            for ti, task in enumerate(STANCE_TASKS):
                deeds[(dispo, seed, ti)] = openrouter_chat(
                    READER, sysp, task, cache, n_predict=550, cost_guard=guard)
        print(f"  {dispo} done [${guard._spent:.2f}]", flush=True)
    stripped = {k: strip_v3(v) for k, v in deeds.items()}

    print("[3/4] judging: REAL 48 + ANCHOR 16 + NULL 16 (pooled refs, K=5)...", flush=True)
    rng = np.random.default_rng(20260721)
    def judge_pooled(src, ti, sa, sc, label_swap_stream):
        """Pooled refs: K=5 (seed, task) draws per side, seed != probe seeds, task != probe task."""
        pool = [(s, t) for s in SEEDS3 for t in range(len(STANCE_TASKS))
                if s not in (sa, sc) and t != ti]
        rng.shuffle(pool)
        refs_idx = pool[:K5]
        agent1_is_A = bool(label_swap_stream.random() < 0.5)
        refs_A = [src[("A", s, t)] for s, t in refs_idx]
        refs_C = [src[("C", s, t)] for s, t in refs_idx]
        refs1, refs2 = (refs_A, refs_C) if agent1_is_A else (refs_C, refs_A)
        x_is_A = bool(label_swap_stream.random() < 0.5)
        probe_x = src[("A", sa, ti)] if x_is_A else src[("C", sc, ti)]
        probe_y = src[("C", sc, ti)] if x_is_A else src[("A", sa, ti)]
        raw = openrouter_chat(JUDGE_BASE, JUDGE_SYSTEM2,
                              judge_user(refs1, refs2, probe_x, probe_y, STANCE_TASKS[ti]),
                              cache, n_predict=500, cost_guard=guard)
        ans = parse2(raw)
        return (ans == ("X" if x_is_A == agent1_is_A else "Y")) if ans else None

    swap = np.random.default_rng(777)
    real_items, real = [], []
    for ti in range(len(STANCE_TASKS)):
        for k in range(6):
            sa, sc = SEEDS3[k], SEEDS3[(k + ti) % 6]
            real_items.append((ti, sa, sc))
            real.append(dict(task=ti, sa=sa, sc=sc, hit=judge_pooled(stripped, ti, sa, sc, swap)))
    print(f"  REAL done [${guard._spent:.2f}]", flush=True)
    anchor = [judge_pooled(deeds, ti, SEEDS3[k], SEEDS3[(k + ti + 1) % 6], swap)
              for ti in range(len(STANCE_TASKS)) for k in range(2)]
    print(f"  ANCHOR done [${guard._spent:.2f}]", flush=True)
    # NULL: A-vs-A — probe pair from two A seeds; "correct" undefined → measure P(judge says X) balance
    # via a same-disposition item where refs1=A-pool and both probes are A: judge SHOULD be ~50/50.
    null_hits = []
    for ti in range(len(STANCE_TASKS)):
        for k in range(2):
            sa, sb = SEEDS3[k], SEEDS3[(k + 3) % 6]
            pool = [(s, t) for s in SEEDS3 for t in range(len(STANCE_TASKS))
                    if s not in (sa, sb) and t != ti]
            rng.shuffle(pool)
            refs_idx = pool[:K5]
            refs_A = [stripped[("A", s, t)] for s, t in refs_idx]
            refs_C = [stripped[("C", s, t)] for s, t in refs_idx]
            x_first = bool(swap.random() < 0.5)
            pa, pb = stripped[("A", sa, ti)], stripped[("A", sb, ti)]
            raw = openrouter_chat(JUDGE_BASE, JUDGE_SYSTEM2,
                                  judge_user(refs_A, refs_C, pa if x_first else pb,
                                             pb if x_first else pa, STANCE_TASKS[ti]),
                                  cache, n_predict=500, cost_guard=guard)
            ans = parse2(raw)
            if ans:
                null_hits.append(ans == "X")   # both probes are A → "X" rate should be ~0.5
    print(f"  NULL done [${guard._spent:.2f}]", flush=True)

    print("[4/4] analysis ($0)...", flush=True)
    rh = [r["hit"] for r in real if r["hit"] is not None]
    acc_real = float(np.mean(rh)) if rh else float("nan")
    acc_anchor = float(np.mean([h for h in anchor if h is not None]))
    null_x = float(np.mean(null_hits)) if null_hits else float("nan")
    per_task = {ti: float(np.mean([r["hit"] for r in real if r["task"] == ti and r["hit"] is not None]))
                for ti in range(len(STANCE_TASKS))}
    tv = np.array([v for v in per_task.values() if np.isfinite(v)])
    n_pt = max(1.0, len(rh) / len(STANCE_TASKS))
    sd_t_corr = max(0.0, tv.var() - acc_real * (1 - acc_real) / n_pt) ** 0.5
    # BOW checks ($0): LOSO construct check + leak gate (train seeds 1-3, test 4-6)
    bow_loso = bow_2afc(stripped, real_items,
                        lambda s, t, ti, sa, sc: s not in (sa, sc))
    leak_items = [(ti, s, s2) for ti in range(len(STANCE_TASKS)) for s, s2 in [(4, 5), (5, 6), (6, 4)]]
    bow_leak = bow_2afc(stripped, leak_items, lambda s, t, ti, sa, sc: s in (1, 2, 3))
    # per-item JSONL (PT8-legit M5)
    with open(REPO / "docs/validation/eval_harness/tost_pilot3_items.jsonl", "w") as f:
        for r in real:
            f.write(json.dumps({**r, "arm": "REAL"}) + "\n")
    out = dict(round=3, acc_real_stripped_pooled=acc_real, n_real=len(rh),
               acc_anchor_unstripped_pooled=acc_anchor,
               null_x_rate=null_x, n_null=len(null_hits),
               per_task_real={str(k): v for k, v in per_task.items()},
               sd_task_raw=float(tv.std()), sd_task_noise_corrected=float(sd_t_corr),
               bow_loso_2afc=bow_loso, bow_leak_heldout=bow_leak,
               unparsed=sum(1 for r in real if r["hit"] is None),
               payload_len=int(np.mean([len(v) for v in pay.values()])),
               spent_usd=round(guard._spent, 4), cache=str(cache))
    dst = REPO / "docs/validation/eval_harness/tost_pilot3_metrics.json"
    dst.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, dict)}, indent=1))
    print("\nREADS: acc_real = the DE-CONFOUNDED preview (valence-matched + pooled refs + strip).")
    print("anchor high = identity expression intact; null_x ~0.5 = no manufacture; bow_leak ~0.5 = strip OK.")
    print(f"[total {time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
