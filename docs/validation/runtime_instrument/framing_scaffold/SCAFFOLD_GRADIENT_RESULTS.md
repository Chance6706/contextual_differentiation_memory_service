# Framing scaffold-gradient — MECH ARM results (declared → implied → raw)

**Status: mech arm COMPLETE (2026-07-01). Non-mech local grid pending roster/quant sign-off.**
Pre-registration: `../FRAMING_SCAFFOLD_GRADIENT_PREREG.md` (Option 2, curation-gradient external-validity test
of the declared confirmatory). Estimand/inference/gates REUSED verbatim from the confirmatory lock — only the
preamble (curation level) varies.

## What was run

- **Gen** (Sparky, `~/cdms_cache/framing_scaffold_20260630_170754`): 11 mech models
  (granite 3.0/3.1/3.2/3.3 × {8b,2b} + mistral-g v0.1/v0.2/v0.3) × 34 frozen confirmatory facets × 2 variants
  × 2 conditions (REAL/DECOY) × 2 curation levels (implied, raw) = **2992 records**, temp=0, cold-load warmup
  (0 empties). `declared` reuses the frozen confirmatory judged file (byte-identical preamble).
- **Judge** (local A′ panel, `framing_pilot_judge.py --cap 10 --stamp scaffold_mech`): 1886 token-present
  judged + 1106 ABSENT; **spend $6.323** (cap not hit → no truncation; all surfaced records judged).
- **Analyze** (`gradient_analyze.py`): locked confirmatory estimand per level (self-concept H1), B=10000 seed 0,
  declared = re-run on `framing_confirm/confirm_JUDGE.jsonl` with the SAME analyzer/seed (apples-to-apples).

## Result — self-concept (H1), locked confirmatory estimand

| level     | facets | lift (R−D) | one-sided95 LB | perm-p | adopt REAL | adopt DECOY | parity-equiv | 2-D REAL | verdict     |
|-----------|:------:|:----------:|:--------------:|:------:|:----------:|:-----------:|:------------:|:--------:|-------------|
| declared  |   19   | **+0.165** |    +0.097      | 0.0000 |   0.269    |    0.105    |     PASS     |  HIGH    | CONFIRMED   |
| implied   |   19   | **+0.074** |    +0.019      | 0.0008 |   0.254    |    0.180    |     PASS     |  HIGH    | CONFIRMED   |
| raw       |   18   | **−0.032** |    −0.101      | 0.8204 |   0.092    |    0.123    |   **FAIL**   | INCONCL. | DESCRIPTIVE |

(declared reproduces the locked +0.165 / LB +0.097 exactly — analyzer/seed sanity check passes.)

## Interpretation — the framing effect is CURATION-DEPENDENT (monotone attenuation, then collapse)

- **declared → implied: SURVIVES, ~halved.** The lift stays significant (LB +0.019 > 0, perm-p 0.0008, H1
  CONFIRMED) but drops from +0.165 to +0.074. The attenuation is driven almost entirely by **DECOY adoption
  RISING** (0.105 → 0.180) while REAL stays ~flat (0.269 → 0.254): when ownership is only *implied by activity
  type* (author-work vs consumer-work) rather than *declared*, the consumer-work DECOY starts drawing
  first-person self-attribution too, so the contrast narrows. External validity holds one curation step out.
- **implied → raw: COLLAPSES.** REAL adoption craters (0.269 → 0.092), the lift goes to noise (−0.032, perm-p
  0.82), surfacing itself drops (0.75 → 0.56), and the parity-equivalence gate FAILS (90% CI (−0.051,+0.020),
  the −0.051 pokes just outside −0.05) → estimand not clean → DESCRIPTIVE (the locked rule's correct verdict).
  When the ownership evidence is a **raw VCS log** (identity header kept, but P authors the commits vs a
  teammate does), models largely stop wrapping the token in first-person ownership. Note raw REAL breach 0.092
  is INCONCLUSIVE (between 0.05 and 0.15), not firmly retired — strong attenuation, not a proven zero.
- **Firewall reading:** the self-attribution risk concentrates in **curated** PersonaTree-style memory (declared
  ownership). Raw log ingestion barely elicits first-person adoption. Consistent with (and reassuring for) the
  [[project-cdms-hermes-seed-identity-leak]] concern that the danger sits in curated identity assertions.

## Caveats / limits carried

- All confirmatory disclaimers + the **effort confound** (DEVIATIONS I2: REAL = deep+owns vs DECOY =
  shallow+not-owns → lift is (ownership+effort), an upper bound on pure ownership; inherent to the instrument,
  P0). Result is **qualitative survival**, NOT a magnitude ladder (self-token counts match within-level but
  binding/curation differ across levels).
- raw is "messy" in three ways at once (lower surfacing, more INVALID judge cells 14/15 vs declared 10/6,
  parity-fail) — per pre-reg this is a *reportable negative* (a level whose manipulation doesn't cleanly work
  is itself the finding); no preamble revision taken.
- Mech arm only (granite + mistral-g). Generalization across families/sizes/MoE = the non-mech local grid,
  pending roster + laguna-xs.2 MoE quant sign-off.

## Data
- `scaffold_mech_gen.jsonl` (2992 gen records, `scaffold` ∈ {implied,raw}), `scaffold_mech_JUDGE.jsonl`
  (1886 judged + 1106 ABSENT), `gradient_analyze.py` (per-level driver). declared source =
  `../framing_confirm/confirm_JUDGE.jsonl`.
