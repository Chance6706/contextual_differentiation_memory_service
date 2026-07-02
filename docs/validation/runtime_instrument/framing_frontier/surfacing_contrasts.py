"""Stage-1 surfacing analysis for the frontier thinking-factor arm (EXPLORATORY).

Pre-committed summary FIRST: within-pair sign of (think - nothink) surfacing across the
6 matched pairs, one-sided sign test (ties dropped). Then the post-hoc same-ID toggle
decomposition with the disclaim-rate and first-person-near-token proxy regexes (these
regexes are the audit trail for the numbers quoted in FRONTIER_THINKING_RESULTS.md §1 —
crude by design; the judged instrument, not these, carries the adoption claims).

Usage: python surfacing_contrasts.py GEN_DEDUP.jsonl
"""
import json
import re
import sys
from collections import defaultdict
from math import comb

PAIRS = [  # (nothink label, think label)
    ("deepseek-v3.2:nothink", "deepseek-v3.2:think"),
    ("sonnet-5:nothink", "sonnet-5:think"),
    ("opus-4.8:nothink", "opus-4.8:think"),
    ("qwen3-235b-2507", "qwen3-235b-thinking-2507"),
    ("qwen3-max", "qwen3-max-thinking"),
    ("gpt-5.2-chat", "gpt-5.2"),
]
SAME_ID = {"deepseek-v3.2:nothink", "sonnet-5:nothink", "opus-4.8:nothink"}
DISC = re.compile(r"(?i)\b(i don't have (direct |verified |personal )?memor|as an ai|i'm an ai"
                  r"|i am an ai|no persistent memory|i cannot actually remember|don't actually (have|retain))")
FIRSTTOK = re.compile(r"(?i)\b(i|my|me)\b[^.]{0,80}starboard_loop")

recs = defaultdict(list)
for ln in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(ln)
    recs[r["model"]].append(r)


def stats(model):
    rs = recs[model]
    n = len(rs)
    surf = sum(bool(r["surfaced"]) for r in rs) / n
    disc = sum(bool(DISC.search(r["response"] or "")) for r in rs) / n
    real = [r for r in rs if r["condition"] == "REAL"]
    ftok = sum(bool(FIRSTTOK.search(r["response"] or "")) for r in real) / len(real)
    return surf, disc, ftok, n


signs = []
print(f"{'pair':44s} {'surf off':>8s} {'surf on':>8s} {'dS':>7s} {'disc off':>8s} {'disc on':>8s} {'same-ID':>7s}")
for off, on in PAIRS:
    so, do, fo, _ = stats(off)
    sn, dn, fn, _ = stats(on)
    d = sn - so
    signs.append(0 if abs(d) < 1e-12 else (1 if d < 0 else -1))  # 1 = suppression
    print(f"{off + ' -> ' + on:44s} {so:>8.3f} {sn:>8.3f} {d:>+7.3f} {do:>8.3f} {dn:>8.3f} "
          f"{'YES' if off in SAME_ID else 'no':>7s}")

neg = sum(1 for s in signs if s == 1)
pos = sum(1 for s in signs if s == -1)
tie = signs.count(0)
n = neg + pos
p = sum(comb(n, k) for k in range(neg, n + 1)) / 2 ** n if n else float("nan")
print(f"\nPRE-COMMITTED Stage-1 sign test (think < nothink): {neg} neg / {pos} pos / {tie} tie "
      f"-> one-sided p = {p:.4f} (ties dropped, n={n})")
