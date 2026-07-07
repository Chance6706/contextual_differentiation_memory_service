"""Power sim for the ATTRIBUTION-FRAME decomposition (FRAME_PREREG s6).

PRIMARY-A (subject-slot minimal pair): the P-subject leg's per-facet per-(response,token) adoption
rates are drawn from the COMMITTED filler-epoch filler arm (the same scaffold this run re-generates);
the team leg is simulated at reduction levels. Reports P(SUBJECT-SLOT-CAUSAL: LB95>0), P(GT pass:
both team tokens <=0.05), P(CROSS-ENTITY-LEAK flag: adopt_team LB95>0.05).

PRIMARY-B / SECONDARY TOST power is inherited from the padding sim (same rule, same 25-facet single-arm
rates, same margin) — reproduced here for the record with the fresh padding-epoch single arm.
"""
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
G = REPO / "docs/validation/runtime_instrument/gen_sweep"
open_set = set(bank.FORMAT_OPEN)
rng = np.random.default_rng(0)

# --- PRIMARY-A rates: filler-epoch filler arm, per-facet adoption over (response, token) pairs ---
cf = collect(str(G / "filler_filler_JUDGE.jsonl"), "mech", bank)
facets, ns, ps = [], [], []
for f, resps in cf["bem"]["SP"].items():
    if f not in open_set:
        continue
    vals = [toks.get(t, 0) for toks in resps.values() for t in R.FILLER_TOKENS]
    facets.append(f); ns.append(len(vals)); ps.append(sum(vals) / len(vals))
ns, ps = np.array(ns), np.array(ps)
print(f"PRIMARY-A P-leg: {len(facets)} facets, pooled 2-token adoption fw={ps.mean():.3f} "
      f"(filler epoch; per-token 0.133/0.084)")


def sim_a(reduction, sims=600, B=1500):
    """team rate = P rate * reduction. Returns P(causal), P(GT pass), P(leak)."""
    causal = gt = leak = 0
    for _ in range(sims):
        pf = rng.binomial(ns, ps) / ns
        pt = rng.binomial(ns, np.clip(ps * reduction, 0, 1)) / ns
        d = pf - pt
        db = np.array([d[rng.integers(0, len(ns), len(ns))].mean() for _ in range(B)])
        if np.percentile(db, 5) > 0:
            causal += 1
        tb = np.array([pt[rng.integers(0, len(ns), len(ns))].mean() for _ in range(B)])
        if np.percentile(tb, 5) > 0.05:
            leak += 1
        # GT approximated per pooled token rate (each token ~ half the pool at reduction level)
        if pt.mean() <= 0.05:
            gt += 1
    return causal / sims, gt / sims, leak / sims


print("\n=== PRIMARY-A: subject-slot causality + GT + leak-flag ===")
for label, red in (("null (team = P rates)", 1.0), ("30% reduction", 0.7), ("50% reduction", 0.5),
                   ("80% reduction", 0.2), ("full collapse (to ~0.02 floor)", 0.02 / max(ps.mean(), 1e-9))):
    c, g, l = sim_a(red)
    print(f"  truth={label:<34} P(SUBJECT-SLOT-CAUSAL)={c:.2f}  P(GT pass)={g:.2f}  P(LEAK flag)={l:.2f}")

# --- PRIMARY-B / SECONDARY: TOST power on the padding-epoch single arm (same rule as padding sim) ---
cs = collect(str(G / "padding_single_JUDGE.jsonl"), "mech", bank)
fac2, ns2, ps2 = [], [], []
for f, resps in cs["bem"]["SP"].items():
    if f not in open_set:
        continue
    vals = [toks.get(T1, 0) for toks in resps.values()]
    fac2.append(f); ns2.append(len(vals)); ps2.append(sum(vals) / len(vals))
ns2, ps2 = np.array(ns2), np.array(ps2)
print(f"\n=== PRIMARY-B/SECONDARY TOST (padding-epoch single rates, fw={ps2.mean():.3f}) ===")


def sim_tost(delta, sims=600, B=1500):
    conf = {"length_clean": 0, "effect_pos": 0, "effect_neg": 0, "incon": 0}
    for _ in range(sims):
        s1 = rng.binomial(ns2, ps2) / ns2
        sp = rng.binomial(ns2, np.clip(ps2 + delta, 0, 1)) / ns2
        M = s1.mean() / 3.0
        d = sp - s1
        db = np.array([d[rng.integers(0, len(ns2), len(ns2))].mean() for _ in range(B)])
        lb, ub = np.percentile(db, [5, 95])
        v = ("effect_pos" if lb >= M else "effect_neg" if ub <= -M
             else "length_clean" if (lb > -M and ub < M) else "incon")
        conf[v] += 1
    return {k: v / sims for k, v in conf.items()}


M0 = ps2.mean() / 3.0
for label, delta in (("clean (Delta=0)", 0.0), (f"boost 2M (+{2*M0:.3f})", 2 * M0),
                     (f"suppress 2M (-{2*M0:.3f})", -2 * M0)):
    r = sim_tost(delta)
    print(f"  truth={label:<26} -> lc:{r['length_clean']:.2f} e+:{r['effect_pos']:.2f} "
          f"e-:{r['effect_neg']:.2f} inc:{r['incon']:.2f}")
