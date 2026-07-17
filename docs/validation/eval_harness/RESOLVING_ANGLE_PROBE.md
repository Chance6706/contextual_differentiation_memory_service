# The resolving-angle probe — a held-out discriminative-projection search for the identity "figure"

**STATUS: DRAFT v2 (2026-07-17) — reshaped after the PT4 three-agent pressure-test. NOT run. This reshape
goes through its OWN rule-12 double pressure-test → lock → run. $0 local (fastembed; dedicated research venv,
GPU for exploration / CPU for canonical/reproducibility).** On branch `research/differentiation`.

## What the PT4 round changed (construct / epistemics / overfit — all folded here)
- **The v1 opposed-TOPIC poles were a topic classifier.** The separating direction was cos **0.943** with the
  pure-topic axis → "FIGURE RESOLVES" would have been the **goalset tautology** reincarnated (the same failure
  that made the erasure arm ENDPOINT-DEGENERATE: survivor ≡ goalset). **Fix (PT4-construct):** the primary now
  isolates **relational stance on SHARED topics** — topic content identical, so any separating direction is
  **topic-orthogonal by construction**. The within-topic relational arm was separable and topic-orthogonal in
  PT4-construct's check (held-out acc 1.000, cos −0.037) — *on simulated/pooled vectors; confirming it on the
  real ingest→consolidate→gist-state loop is THIS run, not a foregone conclusion.*
- **The v1 guards could hallucinate a figure ~98–99.9% of the time on pure noise** (PT4-overfit). Not via a
  learner carving noise (held-out CV was calibrated, mean acc ≈0.50) but via three channels the guards left
  open: a **single-shuffle null ~95% inert**, **no null-calibrated threshold**, and an **uncontrolled
  multiple-comparisons menu**. Plus two miscalibrated trajectory nulls. **Fixes:** permutation-distribution
  null, one pre-registered primary + matched controls, matched-pairs trajectory null. (Detail in §5.)
- **The thesis had no falsifier** (PT4-epistemics): every negative relocated ("it's not in the state → try
  drift → try the projection → …"). **Fix:** a **terminal functional TOST** (task #10) is bound as the
  thesis-level stop — the negative may relocate *once* (state → behavior), and behavior is the final court (§7).
- **Isotropy-correction was cleared** (PT4-overfit NIT 8, an honest negative): whitening is label-blind, so it
  injects no held-out leakage. Raw stays primary; isotropy is a diagnostic only.

## 0. Why — the anamorphic reframe (Josh)
Four structural attempts (frozen NULL → erasure degenerate → tiered negative → drift homogenization) each read
the memory state along a **pre-chosen axis** (entity set, relation, prose, coupling) and saw "one small piece,"
never a coherent figure. But salience is **non-orthogonal** (the temperament dials collapse to ~5–6 DoF; the S0
drivers covary), so identity — if it's there — is a **low-dimensional projection of an entangled
high-dimensional structure**, like a shadow-art assemblage that resolves into a figure from *one* angle and
looks like junk from every other. We've hit this resistance before (the hollow-face self-attribution framing: a
"self" coherent at the prior-forced angle, collapsing at the oblique). So instead of measuring along fixed axes,
this probe **searches for the resolving projection** — but v2 fixes the angle it searches in: **not** "which
domain you inhabit" (that resolves trivially = the tautology) but **"who you are toward a shared domain"** — the
relational stance. This is both the topic-orthogonal signal PT4 demanded and the more faithful reading of the
Jung Josh cited: *"the self appears in your deeds and deeds always mean relationship."*

Publication-neutral name: **held-out discriminative identity projection.** ("Resolving angle" is the intuition
only; no loaded terminology in any writeup — cf. the isotropy-correction naming rule, DEVIATIONS.md.)

## 1. Question (on the 2×2)
- **(a) PRIMARY — is there a topic-orthogonal relational figure?** Does a **linear, regularized projection of the
  surviving-gist state** separate two subjects who share the **same topics** but hold **opposite relational
  stance** (valence → relation), on **held-out seeds**, beating a **≥1000-shuffle permutation null** AND a
  **matched-identical null** — while the **known-tautology topic contrast fires** (power confirmed) and the
  primary's direction is **orthogonal to the tautology direction**?
- **(b) Dose-response** — does a graded **valence ladder** on the shared topics (all-positive → all-negative
  stance) order **monotonically** along that projection?
- **(c) Trajectory** — over cycles, how does the relational figure evolve (the differentiation-over-time curve),
  measured against a matched-pairs permutation null?

## 2. Design — the 2×2 factorial (topic × valence)
Two subjects (poles A, B) are handed to a linear readout; what distinguishes the four cells is **what differs
between A and B**. Fixture: subjects ingest valence-signed episodes over the topic set; **relation is derived
from valence** (`relation_from_valence`: positive→handles_well, negative→has_trouble_with), so opposite valence
on a shared topic = opposite relational identity toward the same work.

|                    | **aligned valence**                                                                 | **opposed valence**                                                                            |
|--------------------|-------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **shared topic**   | **① NULL control** — same topics, same stance ⇒ identical dispositions (differ only by seed). Must **NOT** separate held-out. | **② PRIMARY (confirmatory)** — same topics, opposite stance ⇒ only relational identity differs; any separating direction is **topic-orthogonal by construction.** |
| **opposed topic**  | **③ KNOWN-TAUTOLOGY / positive control** — different topics, same stance ⇒ pure topic detection. Must separate; **flagged known-tautology, never an individuation claim.** | **④ CONFOUND / decomposition** — differ in *both* (the v1 opposed-poles design); separates but confounded — interpretable only against ② and ③. |

- **Cells = one primary + two controls + one decomposition arm** (NOT four hypotheses). This is what reconciles
  a factorial with PT4-overfit's multiple-comparisons finding: ① and ③ are pre-registered **validity gates**
  (null-must-be-null, tautology-must-fire), not comparisons to fish in. The confirmatory family is **cell ②
  alone**; ④ and any pooling/dial variants are explicitly exploratory under FDR.
- **Decomposition (Josh's "how / which-direction / why"):** topic-share ≈ ③, relation-share ≈ ②,
  interaction ≈ ④ − (② + ③). Directly estimates how much of any separation is topic (tautology) vs relational
  stance (real).
- **Identity representation** per (seed, cell, cycle): a **structured, per-canonical-topic** representation
  (concatenate/stack the surviving-gist vectors per topic slot), **not** the support-weighted mean of the whole
  state (mean-pooling was PT4-construct MUST_FIX#2 — it lets a topic-detector win). Computed on the **FULL
  surviving-gist state**, not the top-12 SURFACED `<memory:persona>` set (Jung: the persona is the *mask*; the
  self, if anywhere, is in the full state incl. the un-surfaced "shadow" gists). **Raw is primary; isotropy
  correction is a reported diagnostic only** (leakage retired, PT4-overfit NIT 8).
- **Valence ladder (for ②'s dose-response):** 100% positive → 75/25 → 50/50 → 25/75 → 100% negative stance on
  the shared topics (≥5 rungs). **Rungs 1 & 5 are FRESH held-out seeds, not the trained poles** (pinning them
  to the in-sample training extremes inflated FP 0.018→0.146, PT4-overfit SHOULD_FIX#5).
- **Seeds ≫ 16**, disjoint train/test folds; report the **null sd** (n=16 is a fat-tailed floor, sd≈0.10 —
  PT4-overfit SHOULD_FIX#7). Cycles long enough to reach steady survivor state.
- **BUILD NOTE:** the current generator (`_erasure_history`) may not vary valence independently of topic;
  driving a per-topic valence sign is a build requirement for this fixture (flagged, not assumed present).

## 3. The three standing reference shapes (STANDING OUTPUT CONTRACT — Josh)
Every differentiation experiment emits, side by side and each **explicitly marked**, three shapes; the real
measurement is only ever read *between* the two anchors:
- **NULL** (cell ①, "known-null, must not separate") — the noise floor; what *no signal* looks like.
- **KNOWN-TAUTOLOGY** (cell ③, "known-tautology, NOT individuation") — the ceiling of trivial-by-construction
  separation. Earns its keep three ways: **magnitude anchor** (real effect reported as a fraction of it),
  **direction anchor / active gate** (yields the topic-classifier axis the real direction must be orthogonal
  to), and **power check** (if it fails to separate, the substrate is too crushed to trust a null on ②).
- **REAL** (cell ②) — the actual question, read as a *position*: above NULL, orthogonal-to and (expected) below
  KNOWN-TAUTOLOGY.

The known-tautology is **never stamped as a positive individuation finding** (same anti-laundering discipline as
the `DIFFERENTIATES` → `SEPARATION-PRESENT (INTERPRETATION GATED)` purge in `differentiation_cube.py`). This
contract binds this experiment (natively, via the 2×2) and every future one, alongside the trajectory contract.

## 4. Pipeline
1. **Find the projection** on TRAINING seeds: a **linear, regularized** readout (mean-difference direction, or
   L2-logistic / LDA — linear only, few DoF; **L2 strength / shrinkage pre-registered**, PT4-overfit SHOULD_FIX#6).
2. **Held-out generalization** on fresh seeds (k-fold; k pre-registered). Report accuracy/AUC + CI.
3. **Permutation-distribution null (≥1000 shuffles)** — the real held-out statistic's **permutation p-value**;
   the **decision threshold = the permutation null's upper quantile, pre-registered** (NOT an absolute bar; a
   single shuffle is ~95% inert and any fixed bar fires 6–15% on noise — PT4-overfit MUST_FIX#1,#2). Cell ② must
   also **exceed cell ①'s matched-null separation.**
4. **Orthogonality gate** — cell ②'s discriminative direction vs the cell-③ tautology direction: **|cos| < τ**
   (τ pre-registered, e.g. 0.2). High cos ⇒ the goalset in disguise.
5. **Dose-response** — project the valence-ladder rungs; monotonic order tested by **exact permutation**
   (fresh held-out endpoints, §2).
6. **Trajectory (per the standing contract).** Full per-cycle trajectory of the projection + identity-repr
   distances, as DATA **and** PLOTS. **Between-disposition divergence is tested against a MATCHED-PAIRS
   PERMUTATION null** (permute pole labels on matched-cycle trajectory pairs) — **NOT** the within-self spread
   (which is √2-miscalibrated: two walks diverge 1.41× faster than one departs baseline → 19.7% FP,
   PT4-overfit MUST_FIX#4). **Circumambulation / non-monotonicity is DROPPED as a figure signal** (it fires
   100% on pure random walks — zero evidential value). Trajectory shape must beat the matched-pairs null AND
   generalize held-out.

## 5. Overfitting / validity bar (LOAD-BEARING — PT4-overfit showed v1 hallucinated ~98–99.9% on noise)
- **ONE pre-registered confirmatory primary = cell ②** (readout × representation × pole-pair all fixed);
  everything else (④, poolings, dial sweeps) **exploratory under FDR.** The v1 menu gave FP 0.47→0.72→0.98→0.999.
- **Permutation-distribution null + null-calibrated threshold** (§4.3), not single-shuffle, not an absolute bar.
- **Matched real controls, not synthetic shuffles alone:** cell ① (identical pair) is the null gate; cell ③
  (tautology) is the power gate.
- **Linear + regularized readout only; all hyperparameters pre-registered; seeds ≫16 with null sd reported.**
- **Raw primary; isotropy diagnostic only** — report both, but the leakage fear is retired; don't inflate
  raw-vs-iso effect-size claims.
- **Pre-register everything BEFORE looking at any projection value** — method, folds, ladder, thresholds, τ, the
  FDR family. No post-hoc method/fold/rung/cell selection.
- **The border-line double-edge (Jung 1935, para 431: a "border-line phenomenon needing special conditions to
  become observable").** Credence to the difficulty (a threshold phenomenon; only a *stacking* of non-orthogonal
  vectors crosses the margin) AND the exact statement of the danger (a phenomenon that only appears once
  conditions are tuned is the easiest to hallucinate). The gates above are that guard; a figure that survives
  only in-sample under tuned conditions is, by definition, indistinguishable from an artifact.

## 6. Verdicts (mechanized from data + pre-registered thresholds — no laundering, no stamped positives)
- **FIGURE RESOLVES:** cell ② beats its ≥1000-perm null (p<threshold) AND exceeds cell ①'s matched null AND
  |cos(②, ③-direction)| < τ AND the valence ladder dose-responds monotonically — **conditional on cell ③
  firing** (power confirmed). ⇒ relational identity IS a projectable trace of the memory state; the four
  negatives were wrong angles. Then the trajectory curve is the real differentiation-over-time result.
- **NO FIGURE:** cell ③ fires (powered) but cell ② sits at its permutation null ⇒ the state holds **no
  topic-orthogonal relational identity trace.** Reported **plainly as a negative** (NOT "the definitional
  locus"). Routes to the terminal functional TOST (§7) as the thesis-level court.
- **UNDERPOWERED / INCONCLUSIVE:** cell ③ (tautology) does NOT separate ⇒ the substrate lacks power (the 0.07
  cone crushed even topic signal); **no verdict on cell ②.**
- **INVALID / OVERFIT:** cell ① (null) separates above its permutation null ⇒ the pipeline manufactures
  structure; fix before any claim.

## 7. Terminal falsifier — the thesis-level stop (binds task #10; the epistemics M1 fix)
The probe is the **cheap in-state look**; it **routes** the thesis but does not **decide** it. The negative is
permitted to relocate **exactly once** (state → behavior); **behavior is the terminal court** — no further
relocation.
- **FIGURE RESOLVES here** → the state carries a trace; still confirm functionally (a state trace could be
  epiphenomenal).
- **NO FIGURE here** → the thesis survives **only if** the powered functional **TOST** (task #10, ~200/arm,
  blind judge disjoint from the reader) **rejects equivalence** — i.e., A-enacted vs B-enacted deeds ARE
  distinguishable beyond a pre-registered margin ⇒ individuation is **behavioral, not state-readable.**
- **If the functional TOST FAILS to reject** (deeds within the equivalence margin = indistinguishable) ⇒ the
  thesis is **FALSE at this substrate and the program HALTS.** Pre-registered now, so a null cannot be
  re-relocated.

## 8. Cost + staging
- **$0 local.** Embeds on **fastembed-gpu** in a **dedicated research venv** (isolated onnxruntime-gpu/fastembed;
  product venv untouched, 0-VRAM substrate preserved); keep **canonical / reproducibility** re-runs on **CPU**
  for byte-determinism (CPU↔GPU float drift can tip 0.90-threshold gist merges).
- **Run BEFORE the paid functional arm** — the cheap "is there a figure in the state at all" test; either
  outcome is decision-bearing (FIGURE-RESOLVES rescues the structural approach; a rigorous NO-FIGURE justifies
  paying a reader).
- Reshaped DRAFT → **its own rule-12 double pressure-test** (attack: does the 2×2 fixture actually vary valence
  independent of topic; is the orthogonality gate the right τ; does the structured representation reintroduce
  topic; is the matched-pairs trajectory null truly calibrated; power at seeds≫16) → **lock** → build (research
  venv) → run.

## 9. Pressure-test record (rule-12) — RESERVED for the v2 reshape round.
