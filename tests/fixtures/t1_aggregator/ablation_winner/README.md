# Fixture: ablation_winner

## What this fixture exercises
V2.full wins ORDER + OVERRIDE + BEM on T1 (a clean Step 1 + Step 2 pass).
V2.b — the third-person-persona-only ablation — TIES V2.full within ±5pp on
all 3 tested win-able modes AND loses no mode by ≥10pp.

Per pre-reg §7 Step 3:

> Does any V2 ablation (V2.a/b/c/d) tie V2.full within ±5pp on ≥4 of the
> win-able-or-tested modes (V2 was tested on all 6) on T1, AND lose no mode
> by ≥10pp under Wilson-bound comparison (R5 fix)?
>   YES → ship the winning ablation (per tie-breaking rules §6). V2.full is
>          NOT shipped — the simpler variant won.

And per §6 tie-breaking:
1. Fewer changes from V1 wins.
2. If still tied, the variant with the smaller preamble token count wins.
3. If still tied, V2.full wins.

V2.b makes 1 change from V1 (third-person persona only) vs V2.full's 4 changes.
V2.b's preamble bytes (340) < V2.full's (420). Both tie-break rules favor V2.b.

## Files
- `T1_v1.txt` — V1 baseline.
- `T1_v2.txt` — V2.full (4 changes from V1, 420 bytes preamble).
- `T1_v2b.txt` — V2.b ablation (1 change from V1, 340 bytes preamble).

## Expected aggregator verdict

- **Step 1 actual:** FAIL under strict-Wilson at N=20 (CIs overlap on the
  ORDER/OVERRIDE/BEM win-able-mode cells). This fixture was designed for the
  directional reading where Step 1 would PASS; the spec's strict-Wilson rule
  is more conservative. The bottom-line ship-recommendation logic at Step 3
  is still exercised independently (see below).
- **Step 3 (the actual point of this fixture):**
  - V2.b's per-cell rates are within ±5pp of V2.full on ≥4 of 6 modes.
  - V2.b loses no mode to V2.full by ≥10pp under the median-rate check.
  - `step_3.evaluable == True`
  - `step_3.per_ablation["V2.b"]["ties_count"] >= 4`
  - `step_3.per_ablation["V2.b"]["loses_count"] == 0`
  - `step_3.per_ablation["V2.b"]["preamble_bytes"] == 340`
  - `step_3.per_ablation["V2.b"]["v2_full_preamble_bytes"] == 420`
- If Step 1 had passed (i.e., real T1 data clears the strict-Wilson bar),
  Step 3's tie-break would fire: V2.b's preamble (340) < V2.full's (420), so
  rule 2 of the §6 tie-break would select V2.b. The aggregator records that
  detection regardless of Step 1's outcome.

**Note on oracle update.** The original fixture README assumed Step 1 PASSES
for V2.full and Step 3 fires automatically. Under the spec's strict-Wilson
rule at N=20, Step 1 FAILS on these data. The Step 3 ablation-tie
detection is independent of Step 1 in this aggregator (it walks all
V2.a/b/c/d files present and reports their tie-with-V2.full status
descriptively), so the fixture still exercises the Step 3 logic faithfully —
just decoupled from a passing Step 1.
