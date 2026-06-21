# Fixture: mixed

## What this fixture exercises
V2.full wins ORDER and OVERRIDE decisively (+20pp on every model), but BEM
gets WORSE: cdms-token leaks rise by ≥10pp across multiple cells (mistral-nemo
goes 4→9, qwen2.5 goes 1→5, etc.). The classic asymmetric trade-off.

## Files
- `T1_v1.txt` — V1 baseline.
- `T1_v2.txt` — V2.full candidate.

## Expected aggregator verdict

**Step 1: FAIL.** Two readings, same conclusion:
1. **Directional reading** (raw delta ≥ +10pp): V2.full wins 2 of 3 win-able
   modes (ORDER + OVERRIDE) but LOSES on BEM (leak rate ≥+10pp worse on
   several models); the BEM regression is the gate violation.
2. **Strict-Wilson reading** (per spec, pre-reg §7 R1): Wilson 95% CIs at N=20
   overlap on most cells, so the per-cell verdicts come back TIE rather than
   WIN/LOSE for ORDER/OVERRIDE/BEM; Step 1 fails for insufficient wins.

The bottom-line `step1_passes: false` is robust to either reading.

- `step1_passes: false`
- `headline: "V2.full directionally wins ORDER + OVERRIDE but regresses on BEM; Step 1 not satisfied; V1 remains shipped."`

**Note on oracle update.** Earlier this README asserted
`wins_per_mode = {ORDER:True, OVERRIDE:True, BEM:False}` and
`regression_failures = ["BEM"]`. The aggregator follows the spec's strict
Wilson rule, so at N=20 the per-cell verdicts may not match the directional
prediction; the Step 1 FAIL bottom line is unchanged.
