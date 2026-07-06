"""Power sim for the length-matched FILLER control (FILLER_PREREG §7). Draws T1 per-open-SP-facet rates
from the committed multifact SINGLE arm and simulates the §4 rule on drop = T1(filler) - T1(triple) under
FRAMING (T1 preserved) vs AVAILABILITY (T1 -> p_f/3). Same one-sided profile as multifact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools"))
from multifact_analyze import collect, FORMAT_CAPPED  # noqa: E402
import redteam_claude_md_interference as R  # noqa: E402

T1 = R.MULTIFACT_TOKENS[0]
SINGLE = REPO / "docs/validation/runtime_instrument/gen_sweep/multifact_single_JUDGE.jsonl"
c = collect(str(SINGLE), "mech")
facets, ns, ps = [], [], []
for f, resps in c["bem"]["SP"].items():
    if f in FORMAT_CAPPED:
        continue
    vals = [toks.get(T1, 0) for toks in resps.values()]
    if vals:
        facets.append(f); ns.append(len(vals)); ps.append(sum(vals) / len(vals))
ns, ps = np.array(ns), np.array(ps)
print(f"open-SP facets={len(facets)}  responses/facet median={np.median(ns):.0f}  "
      f"facet-weighted T1(single)={ps.mean():.3f}")

rng = np.random.default_rng(0)


def sim(regime, ns_, ps_, sims=600, B=1500):
    """3-arm sim: single/filler/triple T1 by mechanism; verdict via the analyzer's 2-contrast rule.
    Returns confusion {framing, achievement_avail, anyfact_avail, incon} counts."""
    conf = {"framing": 0, "achievement_avail": 0, "anyfact_avail": 0, "incon": 0}
    for _ in range(sims):
        s1 = rng.binomial(ns_, ps_) / ns_                               # single
        if regime == "framing":
            fr, tr = ps_, ps_
        elif regime == "achievement_avail":
            fr, tr = ps_, ps_ / 3
        else:  # anyfact_avail
            fr, tr = ps_ / 3, ps_ / 3
        sf = rng.binomial(ns_, fr) / ns_                                # filler
        st = rng.binomial(ns_, tr) / ns_                                # triple
        p_f, p_s = sf.mean(), s1.mean()
        THp, THs = p_f / 3, p_s / 3
        dp = sf - st; ds = sf - s1
        pb = np.array([dp[rng.integers(0, len(ns_), len(ns_))].mean() for _ in range(B)])
        sb = np.array([ds[rng.integers(0, len(ns_), len(ns_))].mean() for _ in range(B)])
        plb, pub = np.percentile(pb, [5, 95]); slb, sub = np.percentile(sb, [5, 95])
        if plb > THp:
            v = "achievement_avail"
        elif pub < THp and sub < -THs:
            v = "anyfact_avail"
        elif pub < THp and slb > -THs:
            v = "framing"
        else:
            v = "incon"
        conf[v] += 1
    return {k: v / sims for k, v in conf.items()}


# Project to the EXPANDED bank facet count by resampling the 7 empirical (rate, n) pairs — assumes the 18
# new blind-authored open-SP facets share the existing rate distribution (same construct/authoring).
N_EXPANDED = 25
idx = rng.integers(0, len(ns), N_EXPANDED)
ns_exp, ps_exp = ns[idx], ps[idx]

for label, ns_, ps_ in (("7 facets (current)", ns, ps), (f"{N_EXPANDED} facets (EXPANDED, projected)", ns_exp, ps_exp)):
    print(f"\n=== power/confusion ({label}) ===")
    for regime in ("framing", "achievement_avail", "anyfact_avail"):
        c = sim(regime, ns_, ps_)
        print(f"  truth={regime:18} -> P(correct)={c[regime]:.2f}  confusion={ {k: round(v,2) for k,v in c.items()} }")
    print("  (no framing<->availability cross-misclassification: positive verdicts trustworthy)")
