#!/usr/bin/env python3
"""A/B diff: exponential vs power-law forgetting (Thread 2).

Tabulates the OLD exponential curve e^(-λt) against the NEW power-law curve
D(t) = (1 + t/τ)^(-β) that `salience.accessibility` now uses, so the behavioral
deviation is explicit and reproducible. The half-life anchor (D=0.5 at 29 days) is
identical for both; the difference is entirely in the tail.

Run:  python tools/forgetting_ab.py
Deterministic, offline, no model. Output captured in
docs/validation/forgetting_curve/README.md.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cdms.config import Config  # noqa: E402


def exp_decay(cfg: Config, t: float) -> float:
    return math.exp(-cfg.decay_lambda * t)


def pow_decay(cfg: Config, t: float) -> float:
    return (1.0 + t / cfg.decay_tau) ** (-cfg.forgetting_shape)


def exp_evict_day(cfg: Config, s0: float, reinforce: float = 1.0) -> float:
    """t where s0 * reinforce * e^(-λt) = floor."""
    return math.log(s0 * reinforce / cfg.retention_floor) / cfg.decay_lambda


def pow_evict_day(cfg: Config, s0: float, reinforce: float = 1.0) -> float:
    """t where s0 * reinforce * (1 + t/τ)^(-β) = floor."""
    return cfg.decay_tau * ((s0 * reinforce / cfg.retention_floor) ** (1.0 / cfg.forgetting_shape) - 1.0)


def main() -> int:
    cfg = Config()
    H, beta, tau, floor = cfg.decay_halflife_days, cfg.forgetting_shape, cfg.decay_tau, cfg.retention_floor
    print("=" * 72)
    print("FORGETTING CURVE A/B  —  exponential (old) vs power-law (new)")
    print("=" * 72)
    print(f"half-life       = {H:g} days  (anchor: D=0.5 here for BOTH curves)")
    print(f"forgetting_shape= {beta:g}  (β; β→∞ recovers the exponential)")
    print(f"decay_tau       = {tau:.4f} days  (derived: H/(2^(1/β)-1))")
    print(f"decay_lambda    = {cfg.decay_lambda:.6f} /day  (β→∞ limit rate)")
    print(f"eviction floor  = {floor:g}")
    print()

    print("RETENTION  D(t)  — fraction of S0 still accessible at age t (c=0):")
    print(f"  {'age (days)':>11} | {'exponential':>12} | {'power-law':>12} | {'ratio P/E':>10}")
    print(f"  {'-'*11}-+-{'-'*12}-+-{'-'*12}-+-{'-'*10}")
    for t in (1, 7, 14, 29, 58, 90, 145, 180, 365, 730):
        e, p = exp_decay(cfg, t), pow_decay(cfg, t)
        marker = "  <- half-life" if t == 29 else ""
        print(f"  {t:>11} | {e:>12.5f} | {p:>12.5f} | {p/e:>10.2f}{marker}")
    print()
    print("  Reading: below the half-life the power law forgets recent traces a touch")
    print("  FASTER (ratio < 1); past it the scale-free tail retains FAR more (ratio ≫ 1).")
    print()

    print("EVICTION HORIZON  — day an unreinforced trace falls below the floor:")
    print(f"  {'S0':>6} | {'context':>22} | {'exp day':>9} | {'power day':>10} | {'x longer':>9}")
    print(f"  {'-'*6}-+-{'-'*22}-+-{'-'*9}-+-{'-'*10}-+-{'-'*9}")
    rows = [
        (0.3, "low-salience turn"),
        (1.0, "typical high-salience"),
        (2.0, "very high-salience"),
        (3.0, "floored catastrophe"),
    ]
    for s0, label in rows:
        ed, pd = exp_evict_day(cfg, s0), pow_evict_day(cfg, s0)
        print(f"  {s0:>6.1f} | {label:>22} | {ed:>9.1f} | {pd:>10.1f} | {pd/ed:>8.2f}x")
    # one reinforced example (c=c*, reinforcement saturates at the cap)
    s0, r = 3.0, cfg.reinforce_cap
    ed, pd = exp_evict_day(cfg, s0, r), pow_evict_day(cfg, s0, r)
    print(f"  {s0:>6.1f} | {'catastrophe, 5x recall':>22} | {ed:>9.1f} | {pd:>10.1f} | {pd/ed:>8.2f}x")
    print()
    print("  The deviation is concentrated in the long tail: important, reinforced, or")
    print("  high-salience memories persist substantially longer; recent noise does not.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
