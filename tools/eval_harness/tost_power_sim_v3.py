"""power_sim v3 — the committed lock-gate artifact for FUNCTIONAL_TOST_PREREG.md §5 (task #10).

Simulates the v3 design exactly: T=20 tasks x S=24 seeds/disposition, crossed pairs (40/task,
n=800), single temp-0 judgment/item, logit-normal random effects (task sig_t, per-side seed sig_s,
item sig_e), and the PINNED estimator: 3-way (task, seedA, seedC) SETS-variant cluster bootstrap;
difference test = 95% one-sided lower bound > 0.5; TOST = 90% CI inside (0.40, 0.60), delta=0.10.

Measured nuisance (pilots 1-3c): sig_s ~ 0 (stripped, pooled twice); post-strip sig_t ~ 0-0.4 band;
sig_e ~ 0.3 (rotation agreement 0.76-0.91). PT8-stats independent rebuild: det@0.60 0.91-0.93,
tost@0.50 0.88-0.89 at sig_t=0.4 (SETS conservative-to-nominal at the operating point; 1-way task
bootstrap INVALID - false-eq 0.185; PROD variant over-conservative 0.55).

Run to verify (~10 min CPU): python tools/eval_harness/tost_power_sim_v3.py
"""
from __future__ import annotations

import numpy as np

T, S, PPT = 20, 24, 40          # tasks, seeds/disposition, sampled pairs per task (n = T*PPT = 800)
DELTA = 0.10
B, SIMS = 300, 300              # verification scale; the RUN analysis uses B=10,000
rng = np.random.default_rng(20260722)


def logit(p):
    return np.log(p / (1 - p))


def simulate(p0, sig_t, sig_s, sig_e):
    u = rng.normal(0, sig_t, T)
    aA = rng.normal(0, sig_s, S)
    bC = rng.normal(0, sig_s, S)
    items = []
    for t in range(T):
        aa = rng.permutation(S)
        cc = rng.permutation(S)
        for i in range(PPT):
            a, c = aa[i % S], cc[(i + 1 + i // S) % S]
            p = 1 / (1 + np.exp(-(logit(p0) + u[t] + aA[a] + bC[c] + rng.normal(0, sig_e))))
            items.append((t, a, c, rng.random() < p))
    return np.array(items, dtype=float)


def sets_boot_ci(items, lo_q=0.05, hi_q=0.95, nboot=B):
    stats = []
    for _ in range(nboot):
        ti = set(rng.integers(0, T, T))
        ai = set(rng.integers(0, S, S))
        ci = set(rng.integers(0, S, S))
        m = np.array([r[0] in ti and r[1] in ai and r[2] in ci for r in items])
        if m.sum() < 20:
            continue
        stats.append(items[m, 3].mean())
    return np.quantile(stats, lo_q), np.quantile(stats, hi_q)


def condition(p0, sig_t, sig_s, sig_e):
    det = tost = 0
    for _ in range(SIMS):
        it = simulate(p0, sig_t, sig_s, sig_e)
        lo, hi = sets_boot_ci(it)
        det += (lo > 0.5)
        tost += (lo > 0.5 - DELTA and hi < 0.5 + DELTA)
    return det / SIMS, tost / SIMS


if __name__ == "__main__":
    import time
    t0 = time.time()
    print(f"v3 design: T={T} S={S} ppt={PPT} n={T*PPT}; SETS 3-way bootstrap; delta={DELTA}")
    print(f"{'sig_t':>6} {'sig_s':>6} {'sig_e':>6} | {'det@.60':>8} {'tost@.50':>9} "
          f"{'FPdiff@.50':>10} {'FalseEq@.65':>11}")
    ok = True
    for sig_t, sig_s, sig_e in [(0.0, 0.05, 0.3), (0.4, 0.05, 0.3), (0.4, 0.15, 0.6), (0.8, 0.05, 0.3)]:
        d, _ = condition(0.60, sig_t, sig_s, sig_e)
        _, tq = condition(0.50, sig_t, sig_s, sig_e)
        fp, _ = condition(0.50, sig_t, sig_s, sig_e)
        _, fe = condition(0.65, sig_t, sig_s, sig_e)
        flag = ""
        if sig_t <= 0.4 and (d < 0.85 or tq < 0.85):
            ok = False
            flag = " <-- BELOW GATE"
        print(f"{sig_t:>6} {sig_s:>6} {sig_e:>6} | {d:>8.3f} {tq:>9.3f} {fp:>10.3f} {fe:>11.3f}{flag}")
    print(f"GATE ({'PASS' if ok else 'FAIL'}): powers >= 0.85 required in the measured band (sig_t<=0.4).")
    print(f"[{time.time()-t0:.0f}s]")
