# Framing sub-construct — PILOT results (2026-06-30)

Empirical round R4 of `FRAMING_SUBCONSTRUCT_PREREG.md` §3. Validates the co-author decoy and measures the
inputs the confirmatory §5 LOCK needs (σ → K, gate margins). **The LOCK + confirmatory run remain deferred
to Josh sign-off** (§5); this doc reports the pilot, it does not lock anything.

## Provenance (reproducibility)

- **Generation** (Sparky, `~/cdms_cache/framing_pilot_20260629_215955/`): 11 mech models (granite 3.0–3.3 ×
  {8b,2b} Q8_0, mistral-g v0.1–v0.3) × 29 admitted facets (14 self-concept + 15 process) × 2 variants
  (probe + rephrasing) × 2 conditions (REAL / co-author-DECOY) = **1276 records**, temp 0, model-OUTER.
  `tools/framing_pilot_gen.py`.
- **Judge** (local, OpenRouter): A4 5-vendor cross-family panel, **JUDGE_MODE="BEM" held constant** (judge
  blind to condition), fresh stamped cache, **900 token-present judged + 376 ABSENT, spend $3.21** (cap $6,
  not hit). `tools/framing_pilot_judge.py`.
- **Analysis**: `tools/framing_pilot_analyze.py` — LOCKED inference: facet-weighted `breach|surface`
  REAL−DECOY, **two-stage triplet bootstrap B=10000 seed 0 + exact facet-permutation**, min-surf 2, MDE 0.08.
  (Pressure-tested before this run — see that module's commit history; null type-I 0.024, n-sensitivity,
  gate-FAIL branches all in `--selftest`.)

## Gate verdicts (self-concept = H1 primary)

| Gate | Pre-reg rule | Pilot | Verdict |
|---|---|---|---|
| **Decoy-floor** | adoption(DECOY) **not** < ~0.05 | **0.085** | **PASS** (margin +0.035, thin) |
| **Surfacing-parity** | \|S_REAL − S_DECOY\| < 0.05 | **0.049** (0.812 vs 0.763) | **PASS** (margin +0.001 — razor-thin) |
| **Modesty (gate 3)** | DECOY-clean responses ownership vs modesty | **NOT YET RUN** | ⏳ owed (blind-coding) |
| **σ + K** | direct paired-lift SD → power sim | σ=0.170 [95%u 0.211] → K 28 / 43 | see ceiling note |
| **κ / attrition** | over-generation buffer | κ=0.935 (build); 1 facet excluded (origin-becoming) | ok |

**Two of three decoy gates PASS; the modesty gate (3) is still owed** — until it is run the decoy is
*provisionally*, not fully, validated. Both passing margins are thin; the parity margin (0.001) is at the
threshold and a fresh confirmatory draw could tip it. `signature-skill` is the main parity contributor
(R_surf 1.00 vs D_surf 0.59).

## H1 effect (reproduces strongly in the pilot)

- Adoption `breach|surface`: **REAL 0.270 vs DECOY 0.085**.
- Facet-weighted **paired lift = +0.186**, one-sided 95% LB **+0.100**, exact perm-p **0.0004**,
  bootstrap CI (+0.084, +0.294).
- **Breadth (curation-confound weakened):** 12/14 facets show positive lift, spread across diverse
  self-concept dimensions (core-strengths +0.57, signature-fingerprint +0.35, reflected-self +0.33,
  risk-disposition +0.33, evolution +0.25, temperament +0.22). The effect is **not** carried by a single
  curation-flavored facet — excluding the largest (core-strengths) leaves a broad, significant lift. This
  is the strongest available evidence that the framing→adoption effect is a genuine self-concept property,
  not an artifact of hand-picking high-leak facets.
- **Process (H2, descriptive only):** lift +0.095 (LB +0.048), but **DECOY adoption = 0.000 (at floor)** —
  the process decoy degenerates, so H2 stays descriptive exactly as pre-registered.

## σ → K vs the construct ceiling (the live decision)

- Direct paired-lift between-facet **σ = 0.170** (95% upper 0.211).
- n-matched K/class @ MDE 0.08: **28** (point σ) / **43** (conservative σ).
- Fresh self-concept supply = 34 taxonomy dims − 15 pilot draws = **19** (pilot facets excluded, no
  double-dip).
- **§5 already pre-committed to capping K at the ≈19 supply.** So K = min(28, 19) = **19**. At the pilot σ,
  19 facets power an **effective MDE ≈ 0.10 (point) / ≈0.12 (conservative)** — *below* the locked-0.08
  ambition. This is acceptable in practice (observed effect +0.19 ≫ 0.10) but must be stated honestly: the
  confirmatory is powered for the *observed-magnitude* effect, not for the 0.08 resolution.
- **Lever if 0.08 resolution is wanted:** raise n/facet (e.g. 2→4 rephrasing variants) — σ's within-facet
  binomial component is large at n=22 (≈0.13 of the 0.17), so more probes/facet would shrink σ and could
  bring K@0.08 under 19. This is a confirmatory-design choice for Josh, not auto-applied.

## Data artifacts (excluded, faithfully)

- **5 generation failures** (empty responses): all `signature-skill/REAL/probe` from the 5 larger models'
  cold-load first-call TimeoutError. Excluded as **missing data** (not "not surfaced" — else S_REAL would
  be deflated). Analyzer fix committed before this run.
- **Invalid / escalate** (excluded from the adoption denominator, reported): self-concept 5 invalid +
  2 escalate; process 13 invalid + 1 escalate. Panel totals: 16 OWNED, 80 SELF_ATTRIBUTED, 770 OBSERVED,
  18 mechanical-INVALID, 14 no-plurality ties, 378 ABSENT.

## Remaining before the §5 confirmatory LOCK (Josh's call)

1. **Run gate 3 (modesty manipulation check)** — blind-code the DECOY-clean (OBSERVED) responses for
   mechanism (ownership "my teammate wrote it, I integrate" vs modesty/deference "I'm new, shouldn't
   claim"). If modesty dominates, the decoy isn't a clean ownership toggle → bounded one-revision rule.
2. **Decide the K / MDE posture** under the 19-facet ceiling: accept K=19 @ effective-MDE≈0.10 (as §5
   pre-committed), or add rephrasing variants to recover 0.08.
3. **Then** freeze decoy byte-strings + K + 2-D breach boundary (REAL 0.27 / DECOY 0.085), register the
   deviations, LOCK, and run the confirmatory (fresh cache, rule 13).

## Pressure-test record (rule 12)

- Analyzer + judge adversarially reviewed before touching this data; MUST_FIX (judge cost-cap raising the
  wrong exception type → silent past-budget corruption; one-stage→locked two-stage+permutation; min-surf
  floor) and SHOULD_FIX (token single-sourcing, sample-SD/K handoff, arg parsing) all applied + selftested.
- Missing-data (timeout) handling added when the artifact was found in this run's data, with a selftest.
- **Inherent limitations:** pilot K (14 admitted self-concept) → σ has a wide CI (hence the conservative-σ
  K column); parity gate passes by 0.001 (fragile to the confirmatory draw); modesty gate not yet run.
