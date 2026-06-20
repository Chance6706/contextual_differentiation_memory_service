# Forgetting curve A/B — exponential → power-law

_Thread 2 of the "precision like nature" effort. Validates the deliberate deviation
from a single exponential to a scale-free power-law forgetting curve. See
[`docs/DEVIATIONS.md`](../../DEVIATIONS.md) for the deviation rationale and
[`docs/PARAMETER_BASIS.md`](../../PARAMETER_BASIS.md) for the parameter classification._

## Supposition

A single exponential `e^(-λt)` is the textbook Ebbinghaus form, but human forgetting
is empirically fit **better by a power law** (Wixted & Ebbesen 1991), and a power law
is **scale-free** — self-similar across timescales, the recursive/fractal property the
project was missing. The hypothesis: replacing the decay term with a power-law family
`D(t) = (1 + t/τ)^(-β)`, with τ derived to pin the existing 29-day half-life, will
(a) leave near-term behavior and all existing invariants intact, and (b) give old,
important memories a heavy tail so identity-bearing traces persist far longer, while
recent clutter still fades fast.

Two falsifiable sub-claims:
1. **Anchor preserved** — `D(0)=1` and `D(29 days)=0.5` for every β, and the exponential
   is recovered exactly as β→∞ (the change generalizes, never contradicts, the old model).
2. **Deviation is tail-only** — the curves differ negligibly before the half-life and
   diverge increasingly after it; no test corpus that consolidates near age≈0 is affected.

## Procedure

- Curve: `salience.accessibility` now computes `D(t) = (1 + t/τ)^(-β)` with β =
  `forgetting_shape` = 2.0 and τ = `decay_tau` = `halflife / (2^(1/β) − 1)` ≈ 70.01 d.
- A/B reference: the prior exponential `e^(-λt)`, λ = `decay_lambda` = ln2/29.
- Harness: `python tools/forgetting_ab.py` (deterministic, offline) tabulates retention
  `D(t)` and eviction horizons for both curves across representative ages and S0 values.
- Eviction horizon (closed form, c=0): exponential `t* = ln(S0/floor)/λ`; power-law
  `t* = τ·[(S0/floor)^(1/β) − 1]`, floor = `retention_floor` = 0.10.
- Regression: `tests/test_forgetting_curve.py` locks anchors, monotonicity, heavier tail,
  faster early decay, β→∞ limit, and the eviction-horizon closed form.

## Results

```
RETENTION  D(t)  — fraction of S0 still accessible at age t (c=0):
   age (days) |  exponential |    power-law |  ratio P/E
  ------------+--------------+--------------+-----------
            1 |      0.97638 |      0.97203 |       1.00
            7 |      0.84594 |      0.82647 |       0.98
           14 |      0.71561 |      0.69448 |       0.97
           29 |      0.50000 |      0.50000 |       1.00  <- half-life
           58 |      0.25000 |      0.29912 |       1.20
           90 |      0.11635 |      0.19144 |       1.65
          145 |      0.03125 |      0.10603 |       3.39
          180 |      0.01354 |      0.07842 |       5.79
          365 |      0.00016 |      0.02590 |     159.28
          730 |      0.00000 |      0.00766 |  289604.81

EVICTION HORIZON  — day an unreinforced trace falls below the floor:
      S0 |                context |   exp day |  power day |  x longer
  -------+------------------------+-----------+------------+----------
     0.3 |      low-salience turn |      46.0 |       51.3 |     1.12x
     1.0 |  typical high-salience |      96.3 |      151.4 |     1.57x
     2.0 |     very high-salience |     125.3 |      243.1 |     1.94x
     3.0 |    floored catastrophe |     142.3 |      313.5 |     2.20x
     3.0 | catastrophe, 5x recall |     171.3 |      472.3 |     2.76x
```

### Reading

- **Anchor holds:** both curves pass through `(0, 1.0)` and `(29, 0.5)` exactly; the
  β=1e6 limit reproduces the exponential to ≥4 decimals (`test_large_shape_converges_to_exponential`).
- **Tail-only deviation:** below the half-life the ratio P/E is ≤ 1.00 (power law forgets
  recent traces a hair faster); past it the scale-free tail dominates — a 1-year-old trace
  retains 2.6% under the power law vs 0.016% under the exponential (≈159×).
- **Survival scales with importance:** eviction horizons stretch most for high-salience and
  reinforced traces (catastrophe 142→313 d; reinforced catastrophe 171→472 d) and least for
  low-salience noise (46→51 d). The system forgets clutter on roughly the old schedule but
  keeps what mattered far longer.

### CI / corpus impact (verified)

No behavioral test broke. Every test/validation corpus consolidates within ~1 hour of each
turn (`tools/drift_trajectory.py:358`) or at age≈0, where `D(age) ≈ 1` for **both** curves
and temporal eviction never fires — so gist formation, trait overlap (0.00), and the
self-validating drift harness are curve-independent. The only shape-sensitive assertion was
`test_consolidate.py` probing age=365, updated to the intent-preserving "faded below the
eviction floor" (true for both curves) rather than a curve-specific magnitude.

## Verdict

**CONFIRMED.** The power-law curve preserves the half-life anchor and the exponential limit,
leaves near-term dynamics and all existing invariants intact, and concentrates the change in
a heavy, scale-free tail that lengthens the survival of important memories proportionally to
their salience and reinforcement. Reproduce with `python tools/forgetting_ab.py`.
