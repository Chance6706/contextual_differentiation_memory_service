"""TOST measuring trial 2b — the STRIP dress rehearsal ($~0.2; exploratory, non-confirmatory).

Re-derives the pilot-2 eliciting-tier deeds via cache hits ($0), applies the deterministic
content-strip masker, then (a) GATE-LEAK: can a probe recover the goalset domain from stripped
deeds? (must be ~chance; unstripped = positive control), and (b) re-judges the stripped 2AFC items
-> post-strip accuracy + per-task spread = the LAST unknown the main-run sizing needs.

Arm spend before this: $2.73 of $50. Cap this round: $2.
Run: python tools/eval_harness/tost_pilot2b.py <pilot2_cache_dir_name>
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
from tools.eval_harness.differentiation_experiment import _SUBTOPICS, _ENTITIES
from tools.eval_harness.provenance import assert_worktree_cdms
from tools.eval_harness.tost_pilot import READER, reader_system, judge_user
from tools.eval_harness.tost_pilot2 import (
    GATE_TASKS, JUDGE_BASE, JUDGE_SYSTEM2, PAIRS, K5, parse2, build_payloads)

assert_worktree_cdms()

# ---- deterministic content-strip masker --------------------------------------------------------
_VARIANTS = {
    "auth": ["auth", "authentication", "authenticating", "authenticated", "authorization", "login", "logins"],
    "crypto": ["crypto", "cryptography", "cryptographic", "encryption", "encrypted", "cipher", "ciphers"],
    "payments": ["payments", "payment", "billing", "checkout"],
    "database": ["database", "databases", "db", "sql", "queries", "query"],
    "cache": ["cache", "caches", "caching", "cached"],
    "scheduler": ["scheduler", "scheduling", "scheduled", "schedules", "cron", "jobs", "job"],
    "notifications": ["notifications", "notification", "notify", "notifying", "push"],
    "analytics": ["analytics", "analytic", "metrics", "telemetry", "events", "event"],
}
_LEXICON = []
for ent in _ENTITIES:
    _LEXICON += _VARIANTS.get(ent, [ent])
    for sub in _SUBTOPICS[ent]:
        _LEXICON.append(sub)
        _LEXICON += sub.split()
_LEXICON = sorted(set(w.lower() for w in _LEXICON if len(w) > 2), key=len, reverse=True)


def strip_content(text: str) -> str:
    """Replace topic lexemes with consistent per-deed placeholders AREA-1..k (order of appearance)."""
    mapping: dict[str, str] = {}
    def sub(m):
        w = m.group(0).lower()
        if w not in mapping:
            mapping[w] = f"AREA-{len(mapping) + 1}"
        return mapping[w]
    pat = re.compile(r"\b(" + "|".join(re.escape(w) for w in _LEXICON) + r")\b", re.IGNORECASE)
    return pat.sub(sub, text)


LEAK_SYSTEM = ("You will see a work response with some terms masked. Guess which domain set the "
               "author mostly works in: (1) authentication/cryptography/payments/databases, or "
               "(2) caching/scheduling/notifications/analytics. End with exactly ANSWER: 1 or ANSWER: 2")


def main():
    t0 = time.time()
    pilot2_cache = Path.home() / "cdms_cache" / (sys.argv[1] if len(sys.argv) > 1 else "tost_pilot2_20260717_224533")
    assert pilot2_cache.exists(), pilot2_cache
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache = Path.home() / "cdms_cache" / f"tost_pilot2b_{stamp}"
    cache.mkdir(parents=True, exist_ok=True)
    guard = CostGuard(cap_usd=2.0, state_file=cache / "spend.json")

    print("[1/4] payloads ($0) + deeds via cache hits ($0)...", flush=True)
    pay = build_payloads(40, [1, 2, 3, 4])
    deeds = {}
    for dispo in ("A", "C"):
        for seed in [1, 2, 3, 4]:
            sysp = reader_system(pay[(dispo, seed)])
            for ti, task in enumerate(GATE_TASKS):
                # identical args as pilot2 -> cache HIT in the pilot2 cache dir (no spend)
                deeds[(dispo, seed, ti)] = openrouter_chat(
                    READER, sysp, task, pilot2_cache, n_predict=550, cost_guard=guard)
    print(f"  {len(deeds)} deeds loaded  [spent ${guard._spent:.2f} — should be ~0]", flush=True)

    stripped = {k: strip_content(v) for k, v in deeds.items()}
    ex = stripped[("A", 1, 0)]
    n_masked = ex.count("AREA-")
    print(f"  strip example: {n_masked} masks in A-s1-t0; head: {ex[:180]!r}", flush=True)

    print("[2/4] GATE-LEAK probe (~64 calls)...", flush=True)
    leak = {"stripped": [], "unstripped": []}
    rng = np.random.default_rng(20260720)
    for dispo in ("A", "C"):
        for seed in [1, 2, 3, 4]:
            for ti in rng.choice(len(GATE_TASKS), 4, replace=False):
                for mode, src in (("stripped", stripped), ("unstripped", deeds)):
                    raw = openrouter_chat(JUDGE_BASE, LEAK_SYSTEM, src[(dispo, seed, int(ti))],
                                          cache, n_predict=300, cost_guard=guard)
                    m = re.findall(r"ANSWER[:\s]*([12])", raw, re.IGNORECASE)
                    if m:
                        got = m[-1]
                        truth = "1" if dispo == "A" else "2"
                        leak[mode].append(got == truth)
    leak_s = float(np.mean(leak["stripped"])) if leak["stripped"] else float("nan")
    leak_u = float(np.mean(leak["unstripped"])) if leak["unstripped"] else float("nan")
    print(f"  leak: stripped={leak_s:.3f} (n={len(leak['stripped'])}; ~0.5 = strip works)  "
          f"unstripped={leak_u:.3f} (positive control)", flush=True)

    print("[3/4] stripped 2AFC (48 + 24 rotations)...", flush=True)
    results = []
    rngj = np.random.default_rng(20260718)   # mirror pilot2 assignment stream
    SEEDS_ = [1, 2, 3, 4]
    for ti in range(len(GATE_TASKS)):
        for pi, (a, c) in enumerate(PAIRS):
            for rot in range(2 if pi < 4 else 1):
                ref_pool = [t for t in range(len(GATE_TASKS)) if t != ti]
                rngj.shuffle(ref_pool)
                refs_idx = ref_pool[:K5] if len(ref_pool) >= K5 else ref_pool
                agent1_is_A = bool(rngj.random() < 0.5)
                sA, sC = SEEDS_[a], SEEDS_[c]
                refs_A = [stripped[("A", sA, rt)] for rt in refs_idx]
                refs_C = [stripped[("C", sC, rt)] for rt in refs_idx]
                refs1, refs2 = (refs_A, refs_C) if agent1_is_A else (refs_C, refs_A)
                x_is_A = bool(rngj.random() < 0.5)
                probe_x = stripped[("A", sA, ti)] if x_is_A else stripped[("C", sC, ti)]
                probe_y = stripped[("C", sC, ti)] if x_is_A else stripped[("A", sA, ti)]
                raw = openrouter_chat(JUDGE_BASE, JUDGE_SYSTEM2,
                                      judge_user(refs1, refs2, probe_x, probe_y, GATE_TASKS[ti]),
                                      cache, n_predict=500, cost_guard=guard)
                ans = parse2(raw)
                correct = ("X" if x_is_A == agent1_is_A else "Y")
                results.append(dict(task=ti, a=a, c=c, rot=rot,
                                    hit=(ans == correct) if ans else None))
    ok = [r for r in results if r["hit"] is not None and r["rot"] == 0]
    hits = np.array([r["hit"] for r in ok], float)
    acc = float(hits.mean()) if len(hits) else float("nan")
    per_task = {ti: float(np.mean([r["hit"] for r in ok if r["task"] == ti]))
                for ti in range(len(GATE_TASKS))}
    tv = np.array(list(per_task.values()))
    n_pt = max(1.0, len(ok) / len(GATE_TASKS))
    sd_corr = max(0.0, tv.var() - acc * (1 - acc) / n_pt) ** 0.5
    firsts = {(r["task"], r["a"], r["c"]): r["hit"] for r in results if r["rot"] == 0 and r["hit"] is not None}
    agree = [firsts[(r["task"], r["a"], r["c"])] == r["hit"] for r in results
             if r["rot"] == 1 and r["hit"] is not None and (r["task"], r["a"], r["c"]) in firsts]

    print("[4/4] write metrics...", flush=True)
    out = dict(round="2b", stripped_acc=acc, n=len(ok),
               per_task_stripped={str(k): v for k, v in per_task.items()},
               sd_task_raw=float(tv.std()), sd_task_noise_corrected=float(sd_corr),
               sig_t_logit_approx=float(sd_corr / max(acc * (1 - acc), 1e-6)),
               rotation_agreement=float(np.mean(agree)) if agree else None, n_rot=len(agree),
               leak_stripped=leak_s, leak_unstripped=leak_u,
               n_leak=len(leak["stripped"]),
               unparsed=sum(1 for r in results if r["hit"] is None),
               spent_usd=round(guard._spent, 4), cache=str(cache))
    dst = REPO / "docs/validation/eval_harness/tost_pilot2b_metrics.json"
    dst.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, dict)}, indent=1))
    print(f"\nREADS: stripped_acc = the confirmatory question's dress rehearsal (1.00 unstripped anchor);")
    print(f"leak_stripped ~0.5 = masker works; sig_t = the last sizing unknown.")
    print(f"[total {time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
