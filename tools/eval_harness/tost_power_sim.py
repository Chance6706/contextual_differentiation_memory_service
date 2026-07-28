"""power_sim for the functional TOST prereg (task #10) — a BLOCKING lock gate.

Simulates the exact judgment structure (REAL arm: 25 tasks x 8 seed-pairs = 200 reference-based
2AFC items, ONE judgment each) with two-way random effects (task difficulty, seed-pair idiosyncrasy)
on the logit scale, and mirrors the pre-registered analysis (two-way cluster bootstrap over tasks and
seed-pairs; one-sided difference test at alpha=.05 via the 95% one-sided lower bound; TOST at
alpha=.05 via the 90% CI inside (0.40, 0.60), delta=0.10).

Required by the prereg sec.5, at n=200:
  (i)  power >= 0.85 to DETECT true acc = 0.60 (difference test rejects), and
  (ii) power >= 0.85 for TOST to establish equivalence at true acc = 0.50,
both under realistic intra-cluster correlation. Also reports FP rates (difference test at 0.50;
TOST false-equivalence at 0.60). If the gate fails, volumes revise BEFORE lock.

Run: python tools/eval_harness/tost_power_sim.py   ($0, pure numpy, ~2-4 min)
"""
from __future__ import annotations

import numpy as np

T, J = 25, 8                # tasks x seed-pairs (REAL arm items = T*J = 200)
B = 400                     # bootstrap resamples per simulated dataset
SIMS = 400                  # simulated datasets per condition
DELTA = 0.10
rng = np.random.default_rng(20260717)


def logit(p):
    return np.log(p / (1 - p))


def simulate_acc_matrix(p0, sig_t, sig_j):
    """One dataset: item-level Bernoulli with logit-normal task + pair effects."""
    u = rng.normal(0, sig_t, T)[:, None]
    v = rng.normal(0, sig_j, J)[None, :]
    p = 1 / (1 + np.exp(-(logit(p0) + u + v)))
    return (rng.random((T, J)) < p).astype(float)


def two_way_boot_ci(acc_mat, lo_q, hi_q):
    """Two-way cluster bootstrap: resample tasks AND seed-pairs with replacement."""
    stats = np.empty(B)
    for b in range(B):
        ti = rng.integers(0, T, T)
        ji = rng.integers(0, J, J)
        stats[b] = acc_mat[np.ix_(ti, ji)].mean()
    return np.quantile(stats, lo_q), np.quantile(stats, hi_q)


def run_condition(p0, sig_t, sig_j):
    diff_rej = tost_rej = 0
    for _ in range(SIMS):
        m = simulate_acc_matrix(p0, sig_t, sig_j)
        # difference test (one-sided alpha=.05): 95% one-sided lower bound > 0.5
        lo95, _ = two_way_boot_ci(m, 0.05, 0.95)
        diff_rej += (lo95 > 0.5)
        # TOST (alpha=.05): 90% CI inside (0.5-DELTA, 0.5+DELTA)
        lo90, hi90 = two_way_boot_ci(m, 0.05, 0.95)  # 90% CI == (5th, 95th) percentiles
        tost_rej += (lo90 > 0.5 - DELTA and hi90 < 0.5 + DELTA)
    return diff_rej / SIMS, tost_rej / SIMS


if __name__ == "__main__":
    import time
    t0 = time.time()
    print(f"n = {T*J} items ({T} tasks x {J} seed-pairs), B={B}, sims={SIMS}, delta={DELTA}")
    print(f"{'sig_t':>6} {'sig_j':>6} | {'P(diff|.60)':>11} {'P(tost|.50)':>11} | "
          f"{'FP(diff|.50)':>12} {'FalseEq(tost|.60)':>17}")
    grid = [(0.0, 0.0), (0.3, 0.15), (0.6, 0.3), (0.9, 0.45)]
    verdict_ok = True
    for sig_t, sig_j in grid:
        pow_diff, _ = run_condition(0.60, sig_t, sig_j)
        _, pow_tost = run_condition(0.50, sig_t, sig_j)
        fp_diff, _ = run_condition(0.50, sig_t, sig_j)
        _, false_eq = run_condition(0.60, sig_t, sig_j)
        flag = ""
        if sig_t <= 0.6:  # the "realistic" band the gate is judged on
            if pow_diff < 0.85 or pow_tost < 0.85:
                verdict_ok = False
                flag = "  <-- BELOW GATE"
        print(f"{sig_t:>6} {sig_j:>6} | {pow_diff:>11.3f} {pow_tost:>11.3f} | "
              f"{fp_diff:>12.3f} {false_eq:>17.3f}{flag}")
    print(f"\nGATE ({'PASS' if verdict_ok else 'FAIL'}): both powers >= 0.85 required for "
          f"sig_t <= 0.6 band; FP(diff) should be ~<=0.05, FalseEq ~0.")
    print(f"[{time.time()-t0:.0f}s]")


# ============================================================================
# SWEEP RESULTS (2026-07-17, recorded — the gate FAILED at the drafted volumes)
# 1:1 pairs, single judgment (as drafted, T=25 J=8, n=200):
#   det60 0.55@icc0 / 0.39@icc-real; tost50 0.15 / 0.02  -> FAIL (both directions)
# 1:1 brute passes only at ~(50x24)=1200 items (~2400 deeds, ~$35-45).
# CROSSED pairs + majority-of-3 (deeds 2*S*T; judge T*ppt*3), realistic ICC
# (sig_t=.6 sig_s=.3 sig_e=.3):
#   T=40 S=12 ppt=24:  960 deeds, det60 0.85, tost50 0.44
#   T=40 S=16 ppt=24: 1280 deeds, det60 0.86, tost50 0.56
#   T=50 S=16 ppt=24: 1600 deeds, det60 0.88, tost50 0.63
# READ: crossed+maj3 fixes DETECTION at ~$20 scale; TOST-equivalence power is
# gated by the GUESSED ICC band. Path forward (prereg sec.5 addendum): a small
# PILOT measures the actual ICC (tautology arm, doubles as an early GATE-INERT
# read), then volumes are sized from MEASURED nuisance parameters before lock.
# ============================================================================
