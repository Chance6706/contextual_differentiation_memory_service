# Fixture: regression

## What this fixture exercises
V2.full breaks the INSTR mode (regression-only). V1 baseline is ceiling (20/20
on-task for every model); V2.full drops to 10/20 on 4 of 5 models — a 50pp
regression on a mode that V2 cannot win, only break.

Per pre-reg §7 mode classification, INSTR is "regression-only" — V2 is held to
a "must not break" standard there. The 50pp drop is well past the ≥10pp Wilson
symmetric failure threshold.

## Files
- `T1_v1.txt` — V1 baseline (all INSTR cells at 1.00 on-task).
- `T1_v2.txt` — V2.full candidate (INSTR drops to 0.50 on 4 of 5 models).

## Expected aggregator verdict

**Step 1: FAIL regardless of ORDER win.** V2.full wins ORDER decisively (+20pp
on every model) — but the INSTR regression fires the failure gate. Pre-reg §7
Step 1 fail condition: "FAIL no gate (no mode — win-able OR regression-only —
where V1 exceeds V2.full's gate-failure threshold)."

- `step1_passes: false`
- `regression_failures: ["INSTR"]` — at N=20, V1=20/20 [0.84, 1.00] vs
  V2=10/20 [0.30, 0.70] IS Wilson-disjoint (V2_hi 0.70 < V1_lo 0.84), so
  the strict-Wilson failure gate fires cleanly on the INSTR mode.
- ORDER wins are directional only under strict Wilson at N=20 (CIs overlap
  by ~0.02-0.03 on every model), so `wins_per_mode["ORDER"]` is reported
  as False even though the raw deltas favor V2.
- `headline: "V2.full directionally wins ORDER but REGRESSES on INSTR (on-task drops 1.00 → 0.50, Wilson-disjoint); Step 1 fails on regression gate; V1 remains shipped."`
- Per-cell Wilson half-widths must accompany every reported INSTR drop.

**Note on oracle update.** Earlier this README asserted
`wins_per_mode["ORDER"]=True`. Strict Wilson at N=20 is conservative; the
INSTR regression gate fire (the headline result) is unchanged.
