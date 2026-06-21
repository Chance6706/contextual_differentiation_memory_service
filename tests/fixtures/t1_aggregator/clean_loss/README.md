# Fixture: clean_loss

## What this fixture exercises
V2.full effectively identical to V1 on every win-able mode (within ±5pp tie band).
The simplest null case: V2 brought nothing measurable, so it shouldn't ship.

## Files
- `T1_v1.txt` — V1 baseline.
- `T1_v2.txt` — V2.full candidate (only ±1-cell jitter from V1).

## Expected aggregator verdict

**Step 1: FAIL** (no win-able mode crosses the gate).
- `step1_passes: false`
- `wins_per_mode: {"ORDER": False, "OVERRIDE": False, "BEM": False}`
- `regression_failures: []`
- `headline: "V2.full ties V1 on all win-able modes; no shipping rationale; V1 remains shipped."`
- Per pre-reg §7 decision tree: "V2 is NOT shipped as default. V1 remains shipped."
