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
| **Modesty (gate 3)** | DECOY-clean responses ownership vs modesty | **MODESTY = 0%** (209/212 INTEGRATE) | **PASS** |
| **σ + K** | direct paired-lift SD → power sim | σ=0.170 [95%u 0.211] → K 28 / 43 | see ceiling note |
| **κ / attrition** | over-generation buffer | κ=0.935 (build); 1 facet excluded (origin-becoming) | ok |

**ALL THREE decoy gates PASS → decoy validated** (no revision triggered; bounded-revision rule not invoked).
The passing margins on floor (0.085) and parity (|ΔS|=0.049) are thin — the parity margin (0.001) is at the
threshold and a fresh confirmatory draw could tip it; `signature-skill` is the main parity contributor
(R_surf 1.00 vs D_surf 0.59), worth watching on the confirmatory.

### Gate 3 (modesty manipulation check) — detail

Two **independent blind coders** classified all 212 DECOY-clean (OBSERVED) self-concept responses for the
*mechanism* of non-ownership: INTEGRATE_ATTRIBUTE (plain "a teammate wrote `starboard_loop`, I integrate
it" — clean ownership toggle) vs MODESTY_DEFERENCE (declines via humility/newness/credit — confound) vs
OTHER. Coder A: 209 / 0 / 3. Coder B (adversarial re-code, modesty-hunting bias): 206 / 0 / 6. **Both found
MODESTY_DEFERENCE = 0%.** Raw agreement 98.6% (3 disagreements, all benign INTEGRATE↔OTHER, none modesty);
Cohen's κ = 0.66 (clears the ≥0.60 bar; deflated by the kappa paradox since one category dominates — the
load-bearing modesty category is in *perfect* agreement at 0). The closest-to-modesty case (id150, "I don't
claim authorship of `starboard_loop`, which was developed by another team member, I actively integrate it")
was coded INTEGRATE by both: the not-claiming is justified factually + paired with active integration, not
humility. **Conclusion: the decoy is a clean ownership toggle, not a modesty confound** — gate 3 passes
robustly. Artifacts: `gate3_input.jsonl`, `gate3_codes_coderA.jsonl`, `gate3_codes_coderB.jsonl`.

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

## σ → K vs the construct ceiling — DECIDED (MDE≈0.10 at K=19)

- Direct paired-lift between-facet **σ = 0.170** (95% upper 0.211); decomposed σ_between **0.124** (point) /
  **0.176** (conservative), within-facet binomial W=0.0135.
- n-matched K/class @ MDE 0.08: **28** (point σ) / **43** (conservative σ).
- Fresh self-concept supply = 34 taxonomy dims − 15 pilot draws = **19** (pilot facets excluded, no
  double-dip). §5 pre-committed to capping K at this ≈19 supply.
- **Variant-recovery analysis** (`tools/framing_variant_recovery.py`, pressure-tested 2026-06-30): adding
  rephrasing variants shrinks only the within-facet binomial term, **not σ_between** (the irreducible
  facet-to-facet variance). At 19 facets the MDE *floor* (variants→∞) is ≈0.07 (point) / **0.10
  (conservative)**. Recovering 0.08 would need V≈8 variants and even then succeeds with only **P≈0.65** (σ
  barely identified at K=14; ~30% of facet-bootstraps admit *no* feasible V); under the conservative σ it is
  impossible. The earlier "V=6 recovers 0.08" was integer-luck off a per-cell-n bias — **not decision-grade**
  (see that module's pressure-test record + the rho→1 regime caveat: K must come from the direct paired SD,
  not the frozen component sim, here). DELIBERATE DEVIATION from the §5 "MDE 0.08 [LOCKED]" *ambition*.
- **DECISION (Josh, 2026-06-30): accept K=19 @ effective MDE≈0.10; do NOT inflate variants.** Rationale: the
  observed lift +0.186 is ~2× the achievable MDE either way, so the ~0.02 of resolution that a 4× heavier
  run *might* buy (at coin-flip-plus reliability) is not worth the cost. Variants remain a documented but
  unused lever. The confirmatory therefore runs the pilot's design (V=2) on 19 fresh self-concept facets.

## Data artifacts (excluded, faithfully)

- **5 generation failures** (empty responses): all `signature-skill/REAL/probe` from the 5 larger models'
  cold-load first-call TimeoutError. Excluded as **missing data** (not "not surfaced" — else S_REAL would
  be deflated). Analyzer fix committed before this run.
- **Invalid / escalate** (excluded from the adoption denominator, reported): self-concept 5 invalid +
  2 escalate; process 13 invalid + 1 escalate. Panel totals: 16 OWNED, 80 SELF_ATTRIBUTED, 770 OBSERVED,
  18 mechanical-INVALID, 14 no-plurality ties, 378 ABSENT.

## Remaining before the §5 confirmatory LOCK

1. ✅ **Gate 3 (modesty)** — DONE: modesty 0% (two blind coders, κ=0.66, 98.6% agreement) → decoy is a clean
   ownership toggle. All three gates pass.
2. ✅ **K / MDE posture** — DECIDED (Josh): K=19 @ effective MDE≈0.10, no variant inflation.
3. ⏳ **Final LOCK (Josh sign-off):** freeze decoy byte-strings + K=19 + the 2-D breach boundary (REAL 0.27 /
   DECOY 0.085), register the deviations in `DEVIATIONS.md`, then run the confirmatory on 19 fresh
   self-concept facets (fresh cache, rule 13). Nothing methodological is open; this is the freeze step.

## Pressure-test record (rule 12)

- Analyzer + judge adversarially reviewed before touching this data; MUST_FIX (judge cost-cap raising the
  wrong exception type → silent past-budget corruption; one-stage→locked two-stage+permutation; min-surf
  floor) and SHOULD_FIX (token single-sourcing, sample-SD/K handoff, arg parsing) all applied + selftested.
- Missing-data (timeout) handling added when the artifact was found in this run's data, with a selftest.
- **Inherent limitations:** pilot K (14 admitted self-concept) → σ has a wide CI (hence the conservative-σ
  K column); parity gate passes by 0.001 (fragile to the confirmatory draw); modesty gate not yet run.
