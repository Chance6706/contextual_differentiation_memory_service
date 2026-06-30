"""FROZEN power simulation for the framing-sub-construct lift pre-registration
(`docs/validation/runtime_instrument/FRAMING_SUBCONSTRUCT_PREREG.md`). Locked at pre-reg sign-off; the
pilot plugs its measured (sigma_D, rho) — or its directly-measured paired-lift SD — into this script to
set the confirmatory K.

WHY two-stage (round-2 statistical pressure-test MUST_FIX #1): the facet-weighted paired-lift variance is
  Var(L) = (1/K) * [ sigma_between^2 + E_f( p_R(1-p_R)/n + p_D(1-p_D)/n ) ]
The second (within-facet binomial) term is NON-NEGLIGIBLE at the realistic per-facet n (~22 mech responses
for breach_ALL) and is ABSENT from a sigma-only "K = 2*(z)^2*sigma^2/mde^2" formula — it adds ~10-18 facets
to K. REAL and DECOY are independent draws so their within-facet noise ADDS (pairing does not reduce it);
pairing only helps via between-facet covariance (rho), which VANISHES exactly when the decoy works as
intended (sigma_D -> 0). So the decoy-works regime is rho-independent and sets the binding K.

Estimand = facet-weighted UNCONDITIONAL breach_ALL lift (round-2 methodological MUST_FIX M1: within-facet
REAL-DECOY cancels the coherence confound that motivated conditioning; conditioning reintroduces a
differential-selection collider). Test = one-sided facet-level normal LB>0 (a fast, mildly-conservative
proxy for the two-stage bootstrap; the agent verified analytic ~= sim within 2-4 facets).

Usage:
  python tools/framing_lift_power_sim.py [--mu_R 0.15] [--sigma_R 0.15] [--n 22] [--mde 0.10]
                                         [--reps 4000] [--seed 0] [--grid]
"""
from __future__ import annotations

import sys
import numpy as np

Z = 1.645  # one-sided alpha=0.05


def _draw_pairs(K, mu_R, sigma_R, mu_D, sigma_D, rho, rng):
    cov = [[sigma_R**2, rho * sigma_R * sigma_D], [rho * sigma_R * sigma_D, sigma_D**2]]
    xy = rng.multivariate_normal([mu_R, mu_D], cov, size=K)
    return np.clip(xy, 1e-3, 1 - 1e-3)


def power(K, mu_R, sigma_R, mde, n, sigma_D, rho, reps, rng):
    """P(one-sided facet-level LB>0) at a true mean lift = mde."""
    mu_D = mu_R - mde
    rej = 0
    for _ in range(reps):
        p = _draw_pairs(K, mu_R, sigma_R, mu_D, sigma_D, rho, rng)
        kR = rng.binomial(n, p[:, 0]); kD = rng.binomial(n, p[:, 1])
        lift = kR / n - kD / n
        stat = lift.mean(); se = lift.std(ddof=1) / np.sqrt(K)
        if stat - Z * se > 0:
            rej += 1
    return rej / reps


def required_K(mu_R, sigma_R, mde, n, sigma_D, rho, reps, rng, target=0.80, lo=10, hi=80):
    for K in range(lo, hi + 1):
        if power(K, mu_R, sigma_R, mde, n, sigma_D, rho, reps, rng) >= target:
            return K
    return hi + 1  # > hi (exceeds the ~40-dim construct ceiling band)


def main():
    a = sys.argv[1:]
    def opt(name, default, cast=float):
        return cast(a[a.index(name) + 1]) if name in a else default
    mu_R = opt("--mu_R", 0.15); sigma_R = opt("--sigma_R", 0.15)
    n = opt("--n", 22, int); mde = opt("--mde", 0.10)
    reps = opt("--reps", 4000, int); seed = opt("--seed", 0, int)
    rng = np.random.default_rng(seed)

    print(f"breach_ALL paired-lift power  | mu_R={mu_R} sigma_R={sigma_R} n/facet={n} MDE={mde} "
          f"reps={reps}")
    if "--grid" in a:
        print(f"\nrequired K/class for 80% power, by decoy regime (sigma_D) x correlation (rho):")
        print(f"  {'sigma_D':<10}{'rho=0.2':>9}{'rho=0.5':>9}{'rho=0.8':>9}")
        for sigma_D, label in ((0.03, "0.03 (decoy works)"), (0.10, "0.10 (small)"), (sigma_R, "~sigma_R")):
            row = [required_K(mu_R, sigma_R, mde, n, sigma_D, rho, reps, np.random.default_rng(seed))
                   for rho in (0.2, 0.5, 0.8)]
            print(f"  {label:<18}" + "".join(f"{('>80' if k > 80 else k):>9}" for k in row))
        print("\n  decoy-works row is the binding, rho-independent envelope -> lock K there (or at pilot upper-CI).")
    else:
        for K in (25, 30, 35, 40, 45):
            pw = power(K, mu_R, sigma_R, mde, n, 0.03, 0.2, reps, rng)
            print(f"  K={K:<3} -> power={pw:.2f} (decoy-works regime)")


if __name__ == "__main__":
    main()
