# The resolving-angle probe — a held-out discriminative-projection search for the identity "figure"

**STATUS: DRAFT (2026-07-17) — NOT run. Goes through the rule-12 double pressure-test (overfitting/label-leakage
FIRST) → lock → run. $0 local (fastembed).** On branch `research/differentiation`.

## 0. Why — the anamorphic reframe (Josh)
Four structural attempts (frozen NULL → erasure degenerate → tiered negative → drift homogenization) each read
the memory state along a **pre-chosen axis** (entity set, relation, prose, coupling) and saw "one small piece,"
never a coherent figure. But salience is **non-orthogonal** (the temperament dials collapse to ~5–6 DoF; the
S0 drivers covary), so identity — if it's there — is a **low-dimensional projection of an entangled
high-dimensional structure**, like a shadow-art assemblage that resolves into a figure from *one* angle and looks
like junk from every other. We've hit this resistance before (the hollow-face self-attribution framing: a "self"
coherent at the prior-forced angle, collapsing at the oblique). So instead of measuring along fixed axes, this
probe **searches for the resolving projection** — the direction that casts the figure — and holds it to a strict
generalization bar so we don't paint a face onto scrap.

Publication-neutral name: **held-out discriminative identity projection.** ("Resolving angle" is the intuition
only; no loaded terminology in any writeup — cf. the isotropy-correction naming rule.)

## 1. Question
(a) Does a **linear projection of the surviving-gist state generalize** to separate two *opposed* dispositions on
**held-out seeds** — i.e., is there a figure at all? (b) If so, do **graded increments** between the poles
**dose-respond monotonically** along that projection? (c) Over cycles, do adjacent increments' identities
**converge or diverge** in the projection — the differentiation-over-time curve, finally measured at the right
angle.

## 2. Design
- **Opposed-endpoint dispositions (the anchor — Josh):** A-pole = a **backend/security** domain (auth, crypto,
  payments, database); B-pole = an **opposed frontend/product** domain (UI, notifications, design, dashboards).
  Genuinely different domains → the discriminative direction can separate them along their *distinguishing*
  dimension even if their raw cosine sits in the crowded cone (the projection amplifies the separating axis and
  ignores the shared "software" bulk — this is exactly what a fixed-axis metric cannot do).
- **Increment ladder:** graded interpolation of the goal-set from 100% A → 75/25 → 50/50 → 25/75 → 100% B (≥5
  rungs). Secondary axis (optional, per Josh): sweep a **temperament dial** across its range (does the salience
  *genotype*, not just what you work on, move the projection?).
- **Identity representation** per (seed, disposition, cycle): the **support-weighted mean of surviving-gist
  centroids** (one vector). Computed on **both raw and isotropy-corrected** embeddings (mean-centering the
  artifact-vs-real diagnostic). Richer poolings (per-canonical-topic concatenation) are a pre-registered option.
- Seeds ≥ 16 (disjoint train/test folds); cycles long enough to reach steady survivor state.

## 3. Pipeline
1. **Find the projection** on TRAINING seeds: a **LINEAR, regularized** readout (mean-difference direction, or
   L2-regularized logistic / LDA — *linear only*, few DoF, no deep nets) separating A-pole from B-pole identity
   representations.
2. **Held-out generalization (overfitting guard #1, primary):** does the projection separate A from B on
   **fresh held-out seeds** (k-fold CV, report accuracy/AUC + CI)? If it does NOT generalize at *max contrast*,
   there is **no figure** → stop; the behavioral-only conclusion stands.
3. **Dose-response (guard #2 + the measurement):** project the **increment** identities onto the direction; do
   they order **monotonically** A→B with the rung? Report the curve + a monotonicity test. A spurious direction
   won't order graded increments.
4. **Convergence/divergence over cycles (Josh's temporal question):** for **adjacent** rungs, plot
   projection-distance (and full identity-repr distance) vs **cycle** — do near dispositions *diverge*
   (individuation grows) or *converge* (collapse)? This is the differentiation-over-time curve at the resolving
   angle.

## 4. Overfitting bar (LOAD-BEARING — the highest apophenia risk we've faced; a discriminative learner will
carve A from B from pure noise given enough dims + few seeds)
- **Linear + regularized readout only.** No high-capacity models.
- **Held-out fresh-seed generalization is the gate** (guard #1). Nothing is claimed off in-sample separation.
- **LABEL-SHUFFLE null (guard #3):** shuffle A/B labels, re-run the whole pipeline; the shuffled "projection"
  must **fail** to generalize held-out. If a shuffled-label direction ALSO generalizes, the pipeline
  manufactures structure → INVALID, stop.
- **Monotonic dose-response required** (guard #2) — a real axis orders the increments; noise doesn't.
- **Report raw AND isotropy-corrected** — quantify how much separation is removable artifact vs real proximity.
- **Pre-register** the readout method, the k-fold seed splits, the increment ladder, and the decision
  thresholds BEFORE looking at any projection value. No post-hoc method/fold/rung selection.

## 5. Verdicts
- **FIGURE RESOLVES:** the direction generalizes held-out at max contrast AND dose-responds monotonically AND
  the shuffle null fails → identity IS a (findable) projection of the memory state; the four negatives were
  wrong angles. Then the convergence/divergence curve is the real differentiation-over-time result.
- **NO FIGURE:** fails held-out generalization even at max contrast → individuation is not a readable property of
  the memory state (the structural negative is confirmed *rigorously*, by a search that would have found a figure
  if one existed) → the behavioral/functional arm is the only remaining locus.
- **OVERFIT ARTIFACT:** shuffle null also generalizes → the instrument is unsound; fix before any claim.

## 6. Cost + staging
- **$0 local.** Run the increment/seed embeds on **fastembed-gpu** (frees the CPU — the source of this session's
  pileups); keep any **canonical/reproducibility** re-run on **CPU** (the shipped 0-VRAM substrate) for
  determinism.
- **Run BEFORE the paid functional arm.** This is the cheap test of "is there a figure in the state at all" — a
  FIGURE-RESOLVES rescues the structural approach; a rigorous NO-FIGURE justifies paying a reader to look at the
  behavioral projection instead. Either outcome is decision-bearing.
- Draft → rule-12 pressure-test (attack: overfitting, label leakage across folds, isotropy-correction as a DoF,
  the monotonicity test's power, the identity-representation pooling choice) → lock → run.
