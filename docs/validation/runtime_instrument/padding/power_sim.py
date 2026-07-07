"""Power sim for the TOKENLESS padding control (PADDING_PREREG §6). Unlike the filler sim (which had to
PROJECT 7 facet rates to 25), this draws the REAL per-open-SP-facet T1 rates from the committed
filler-epoch single arm (25 facets, same bank, same estimand) and simulates the §4 TOST rule on
Delta = T1(padded) - T1(single), margin M = p_s/3.

Regimes: length_clean (Delta=0), boost/suppress at +/-M (the margin edge — worst case) and +/-2M
(the availability-masking magnitude 2p/3, the effect size that would actually threaten the multifact
composition)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools"))
from multifact_analyze import collect  # noqa: E402
import probes_sp_expansion as bank  # noqa: E402
import redteam_claude_md_interference as R  # noqa: E402

T1 = R.MULTIFACT_TOKENS[0]
SINGLE = REPO / "docs/validation/runtime_instrument/gen_sweep/filler_single_JUDGE.jsonl"
c = collect(str(SINGLE), "mech", bank)
open_set = set(bank.FORMAT_OPEN)
facets, ns, ps = [], [], []
for f, resps in c["bem"]["SP"].items():
    if f not in open_set:
        continue
    vals = [toks.get(T1, 0) for toks in resps.values()]
    if vals:
        facets.append(f); ns.append(len(vals)); ps.append(sum(vals) / len(vals))
ns, ps = np.array(ns), np.array(ps)
print(f"open-SP facets={len(facets)} (REAL rates, filler-epoch single arm)  "
      f"responses/facet median={np.median(ns):.0f}  facet-weighted T1(single)={ps.mean():.3f}")

rng = np.random.default_rng(0)


def sim(delta, sims=600, B=1500):
    """2-arm sim: single at empirical rates, padded at rates+delta (clipped to [0,1]); verdict via the
    §4 TOST rule. Returns fraction of each verdict."""
    conf = {"length_clean": 0, "effect_pos": 0, "effect_neg": 0, "incon": 0}
    for _ in range(sims):
        s1 = rng.binomial(ns, ps) / ns
        sp = rng.binomial(ns, np.clip(ps + delta, 0, 1)) / ns
        M = s1.mean() / 3.0
        d = sp - s1
        db = np.array([d[rng.integers(0, len(ns), len(ns))].mean() for _ in range(B)])
        lb, ub = np.percentile(db, [5, 95])
        if lb >= M:
            v = "effect_pos"
        elif ub <= -M:
            v = "effect_neg"
        elif lb > -M and ub < M:
            v = "length_clean"
        else:
            v = "incon"
        conf[v] += 1
    return {k: v / sims for k, v in conf.items()}


p_bar = ps.mean()
M0 = p_bar / 3.0
for label, delta in (("length_clean (Delta=0)", 0.0),
                     (f"boost at margin (+M={M0:.3f})", M0),
                     (f"boost at 2M (+{2*M0:.3f}, availability-masking size)", 2 * M0),
                     (f"suppress at margin (-M)", -M0),
                     (f"suppress at 2M (-{2*M0:.3f})", -2 * M0)):
    r = sim(delta)
    print(f"  truth={label:<46} -> {{lc:{r['length_clean']:.2f} e+:{r['effect_pos']:.2f} "
          f"e-:{r['effect_neg']:.2f} inc:{r['incon']:.2f}}}")
print("  (verify: no length_clean<->effect cross-misclassification; at-margin truths land INCONCLUSIVE "
      "or the correct side, never the opposite verdict)")
