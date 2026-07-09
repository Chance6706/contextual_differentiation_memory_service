"""Power simulation for CONSERVATION_PREREG.md §6 (committed pre-lock).

Simulates the pre-registered per-arm decision (paired facet bootstrap TOST of D = fw(arm) -
fw(anchor) over the 7 REPRO facets, band M) from the EMPIRICAL committed frame-epoch facet rates
(frame_triple_JUDGE.jsonl, mech, 7f):

    cs-A1 0.5909 · cs-A2 0.0909 · cs-A8 0.0909 · cs-A9 0.1818 · cs-A10 0.0455
    cs-A11 0.1818 · cs-A20 0.0909   (fw = 0.1818, n = 22/facet; P1 pools 3 seeds -> 66/facet)

Truth grid: multiplicative r in {1.0 (conserved), 0.7, 1.3 (band-edge-ish), 0.5, 1.5 (broken)}.
Anchor held FIXED at the committed sample (that is literally what the analysis pairs against);
test arm drawn binomially at rate r*p_f (capped at 1). Between-seed independence is assumed for
P1 pooling (disclosed optimism: real decode noise may correlate within model).

Run:  python docs/validation/runtime_instrument/conservation/power_sim.py
"""
from __future__ import annotations

import random

RATES = {"cs-A1": 0.5909, "cs-A2": 0.0909, "cs-A8": 0.0909, "cs-A9": 0.1818,
         "cs-A10": 0.0455, "cs-A11": 0.1818, "cs-A20": 0.0909}
ANCHOR_N = 22
SIMS, BOOT = 500, 2000
BANDS = (0.061, 0.075)          # floor M; plausible 3*sigma_P0 M
ARM_NS = {"P2/P3/P4 (n=22/f)": 22, "P1 (3 seeds, n=66/f)": 66,
          "P1+ext (5 seeds, n=110/f)": 110}   # the pre-registered INCONCLUSIVE extension path (N12)


def fw(by_facet):
    rates = [sum(v) / len(v) for v in by_facet.values()]
    return sum(rates) / len(rates)


def paired_tost(fac_a, fac_b, band, rng):
    facets = sorted(fac_a)
    base = fw(fac_a) - fw(fac_b)
    diffs = []
    for _ in range(BOOT):
        samp = [rng.choice(facets) for _ in facets]
        ra = sum(sum(fac_a[f]) / len(fac_a[f]) for f in samp) / len(samp)
        rb = sum(sum(fac_b[f]) / len(fac_b[f]) for f in samp) / len(samp)
        diffs.append(ra - rb)
    diffs.sort()
    lo, hi = diffs[int(0.025 * BOOT)], diffs[int(0.975 * BOOT) - 1]
    lb, ub = diffs[int(0.05 * BOOT)], diffs[int(0.95 * BOOT) - 1]
    if lb > -band and ub < band:
        return "CONSERVED"
    if (lo > 0 or hi < 0) and abs(base) > band:
        return "BROKEN"
    return "INCONCLUSIVE"


def main():
    rng = random.Random(0)
    # fixed anchor sample drawn once from the empirical rates at the committed counts
    anchor = {f: [1 if rng.random() < p else 0 for _ in range(ANCHOR_N)]
              for f, p in RATES.items()}
    # re-center: force the anchor sample's per-facet rates to the exact empirical counts
    for f, p in RATES.items():
        k = round(p * ANCHOR_N)
        anchor[f] = [1] * k + [0] * (ANCHOR_N - k)

    print(f"anchor fw = {fw(anchor):.4f}")
    for band in BANDS:
        print(f"\n=== band M = +/-{band} ===")
        print(f"{'arm':<22} {'truth r':>8} {'CONSERVED':>10} {'BROKEN':>8} {'INCONCL':>8}")
        for arm_name, n in ARM_NS.items():
            for r in (1.0, 0.7, 1.3, 0.5, 1.5):
                counts = {"CONSERVED": 0, "BROKEN": 0, "INCONCLUSIVE": 0}
                for s in range(SIMS):
                    srng = random.Random(1000 + s)
                    test = {f: [1 if srng.random() < min(1.0, r * p) else 0 for _ in range(n)]
                            for f, p in RATES.items()}
                    counts[paired_tost(test, anchor, band, srng)] += 1
                print(f"{arm_name:<22} {r:>8.1f} {counts['CONSERVED']/SIMS:>10.2f} "
                      f"{counts['BROKEN']/SIMS:>8.2f} {counts['INCONCLUSIVE']/SIMS:>8.2f}")


if __name__ == "__main__":
    main()
