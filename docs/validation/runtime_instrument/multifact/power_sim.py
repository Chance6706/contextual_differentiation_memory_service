"""Power sim for the multi-fact scaffold (MULTIFACT_PREREG §8). Draws SP per-facet single-arm rates from
the clean-strata mech data, simulates the paired per-token DROP under AVAILABILITY (triple per-token=p/3,
pick-one) vs FRAMING (triple per-token=p, independent), and reports P(correct verdict) under the §7 rule.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools"))
from gen_sweep_aggregate import breach_corrected, TOK, MAP  # noqa: E402
from probes_cleanstrata import FACET_OF_CLEANSTRATA, CLASS_OF_CLEANSTRATA, PROBES_CLEANSTRATA, REPHRASINGS_CLEANSTRATA  # noqa: E402
from multifact_analyze import FORMAT_CAPPED  # noqa: E402  (power on FORMAT-OPEN SP facets only)

# clean-strata SP per-facet single-arm breach_ALL (surfacing in denominator) + response counts
JUDGE = REPO / "docs/validation/runtime_instrument/gen_sweep/cleanstrata_JUDGE.jsonl"
t2f = {}
for i in range(len(PROBES_CLEANSTRATA)):
    for t in [PROBES_CLEANSTRATA[i]] + REPHRASINGS_CLEANSTRATA.get(i, []):
        t2f[t.strip()] = FACET_OF_CLEANSTRATA[i]

sp = {}  # facet -> [n_responses, n_breach]
for ln in open(JUDGE, encoding="utf-8"):
    ln = ln.strip()
    if not ln:
        continue
    r = json.loads(ln)
    if r.get("mode") != "BEM" or MAP.get(r.get("generation", "?"), ("?",))[0] != "mech":
        continue
    f = t2f.get((r.get("probe") or "").strip())
    if f is None or CLASS_OF_CLEANSTRATA[f] != "SP" or f in FORMAT_CAPPED:
        continue                              # FORMAT-OPEN SP facets only (genre-confound fix)
    s = sp.setdefault(f, [0, 0])
    s[0] += 1
    if TOK.search(r.get("response") or "") and breach_corrected(r):
        s[1] += 1

facets = sorted(sp)
n_resp = np.array([sp[f][0] for f in facets])
p_facet = np.array([sp[f][1] / sp[f][0] for f in facets])
print(f"SP facets={len(facets)}  responses/facet median={np.median(n_resp):.0f}  "
      f"facet-weighted p={p_facet.mean():.3f}")

rng = np.random.default_rng(0)


def sim(regime, sims=600, B=1500):
    correct = 0
    for _ in range(sims):
        # single arm: per-facet breach ~ Binomial(n, p)
        s1 = rng.binomial(n_resp, p_facet) / n_resp
        # triple arm per-token rate by regime
        pt = p_facet / 3 if regime == "availability" else p_facet
        # per response, 3 token draws; per-token adoption = mean; multiplicity = P(>=2)
        # approximate facet per-token triple ~ Binomial(3n, pt)/(3n); multiplicity via 3 indep draws
        s3_pt = rng.binomial(3 * n_resp, pt) / (3 * n_resp)
        if regime == "availability":
            mult = np.zeros(len(facets))  # pick-one -> never >=2
        else:
            # P(>=2 of 3 at pt) per response, facet-mean
            mult = 3 * pt**2 * (1 - pt) + pt**3
            mult = rng.binomial(n_resp, mult) / n_resp
        p = s1.mean()
        THETA = p / 3
        # paired drop bootstrap
        d = s1 - s3_pt
        db = np.array([d[rng.integers(0, len(facets), len(facets))].mean() for _ in range(B)])
        dlb, dub = np.percentile(db, [5, 95])
        mb = np.array([mult[rng.integers(0, len(facets), len(facets))].mean() for _ in range(B)])
        mlb, mub = np.percentile(mb, [5, 95])
        avail = (dlb > THETA) and (mub < 0.05)
        fram = (dub < THETA) or (mlb > 0)
        verdict = "availability" if (avail and not fram) else "framing" if (fram and not avail) else "incon"
        correct += (verdict == regime)
    return correct / sims


print(f"power P(correct verdict): availability={sim('availability'):.2f}  framing={sim('framing'):.2f}")
