# Fixture: heterogeneous

## What this fixture exercises
V2.full wins ORDER strongly on phi4/qwen2.5/mistral-nemo (+40pp each) but
loses badly on gemma-std and heretic (Gemma family flips: 3→0 safe). The
per-mode min-max range spans well over 20pp, which per pre-reg §7
"Per-cell analysis is the unit (R2 fix)" mandates an explicit per-model
breakdown table.

## Files
- `T1_v1.txt` — V1 baseline.
- `T1_v2.txt` — V2.full candidate.

## Expected aggregator verdict

**Step 1: FAIL.** Heterogeneity across the 5 models is the headline:
phi4/qwen2.5/mistral-nemo show V2 directionally up +40pp; gemma-std and
heretic show V2 directionally down −15pp. The ORDER min-max range across
the 5 models exceeds 0.20 and MUST be flagged per pre-reg §7 R2.

- `step1_passes: false`
- `heterogeneity_flagged: ["ORDER"]` — the per-mode min-max range across the
  5 models is ≥ 0.55, well past the 20pp threshold.
- The aggregator surfaces the heterogeneity in its per-mode heterogeneity
  table and the per-(mode, condition, model) detail block for ORDER × V2.full.
- `regression_failures: []` (regression-only modes unchanged)
- `headline: "V2.full effect is family-dependent: wins +40pp on phi4/qwen2.5/mistral-nemo but loses -15pp on gemma-std/heretic; heterogeneity flagged; Step 1 not satisfied; V1 remains shipped."`

**Note on oracle update.** Earlier this README asserted that the per-cell
gemma + heretic losses fire the strict Wilson loss gate. At N=20 with
V1=3/20, V2=0/20, the Wilson 95% CIs are [0.05, 0.36] vs [0.00, 0.16] — they
OVERLAP at [0.05, 0.16], so the strict-Wilson loss gate does not fire on
those cells in isolation. The aggregator records the cells as TIE and
surfaces the heterogeneity range instead. Step 1 FAIL conclusion is unchanged
(either via "no cross-model wins" or "no model wins on a heterogeneous
range"); the headline framing shifts from "loss-gate fails" to "heterogeneity
flagged + no wins".
