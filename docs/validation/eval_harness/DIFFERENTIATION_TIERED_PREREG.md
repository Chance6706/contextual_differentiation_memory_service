# Differentiation — the TIERED experiment: partial-erasure structural × functional H4 × MSA seam-lens

**STATUS: DRAFT (2026-07-17) — NOT LOCKED.** Goes through the rule-12 double pressure-test (red-team +
legitimate-use) → fold MUST/SHOULD → LOCK before any run. Supersedes the entity-set PRIMARY of both prior
preregs (frozen-history NULL; erasure ENDPOINT-DEGENERATE — see §0).

**Costs (plain dollars, upfront):** STRUCTURAL (partial-erasure) = **$0** local. FUNCTIONAL (H4) = **paid**
reader + blind judge behind a CostGuard cap — estimated at run time, **GATED** on a separate Josh
authorization. MSA arm = $0 multilingual embedder + paid Arabic-fluent reader/judge (gated) + Josh's audit
time for the minimal pairs and the A′-Arabic rubric. **Staged run: the $0 structural arm first; every paid
arm gated.**

---

## 0. Why this exists — the two nulls and the tautology that motivate it

1. **Frozen-history NULL (committed):** feeding all topics every cycle → nothing idles → nothing is
   forgotten → no individuation. "What remains after a crude forgetting policy" is vacuous without forgetting.
2. **Erasure ENDPOINT-DEGENERATE (committed, 4-agent pressure-test):** at full erasure (`cycles=500`) every
   off-goal topic decays out, so the surviving entity set ≡ the disposition's goalset **by construction** —
   the separation is `_DISPOSITIONS` arithmetic (zero-variance CIs), `history_effect ≡ 0`, the permutation
   null is circular, and H2 (salience vs random) is **unreachable** (both ≡ goalset). BUT A1's mid-trajectory
   probe showed **salience ≠ random OFF the endpoint** — the H2-relevant and history-relevant signal lives at
   **partial erasure**, which the full-erasure endpoint discards.

**The fix (this prereg):** measure at **PARTIAL erasure** (a non-degenerate regime where *which* topics
survive depends on history × salience), and pair the structural arm with the **functional H4 arm on SHARED
subjects** — because structural and functional are two projections of one identity, and the load-bearing
claim is whether structural individuation **predicts** functional individuation (the tier LINKAGE).

## 1. Frame + hypotheses

**Tier decomposition (biology-style):** identity = f(**substrate** × **disposition** × **history** +
interactions), observable only as **functional distinguishability**. This experiment holds substrate fixed,
varies disposition × history in the **partial-erasure** regime, measures BOTH the structural surviving-gist
state AND functional behavioral distinguishability on the SAME subjects, and tests the linkage + a grammatical
lens on the seams. Each tier/interaction counts ONLY if it beats a null (a non-piece is as informative as a
piece — H2's endpoint null already told us the eviction-RANKING is not load-bearing).

- **H1 (partial-erasure structural individuation):** in the partial regime the surviving-gist entity/(rel,ent)
  set of two DIFFERENT dispositions diverges more than under `none`, the divergence is disposition-STRUCTURED
  (beats a permutation null), AND is **non-degenerate** (survivor ≠ goalset; structural variance across seeds
  > 0). Falsifier: survivor ≡ goalset (degenerate) OR no structure beyond null.
- **H2 (salience-specificity — now TESTABLE):** at partial erasure, salience-forgetting's survivor is more
  disposition-structured than random-forgetting's. Falsifier: salience ≈ random even at partial erasure
  (then "any forgetting suffices" stands as a clean, published negative).
- **H3 (disposition separable from seed):** same disposition across histories stays MORE similar than
  different dispositions on matched histories, where `history_effect` is now ≠ 0. Falsifier: same-disp ≈
  diff-disp → divergence is seed noise (INVALID).
- **H4 (functional distinguishability — LOAD-BEARING):** loaded into a fixed real reader, a blind judge
  (disjoint from the reader) distinguishes identity-A-loaded from identity-B-loaded OUTPUTS above chance;
  report discrimination accuracy vs 50% (CI) + effect size, and the identity-vs-no-memory behavioral shift.
  Non-phenomenal, no-consciousness ("would an outside observer tell them apart").
- **H5 (the tier LINKAGE — the novel claim):** across pairs, **structural distinguishability PREDICTS
  functional distinguishability** — structurally-more-differentiated selves read as more behaviorally
  distinct. This regression IS the assembly test; it is measurable ONLY because partial erasure gives a
  *gradient* of structural distinguishability (full erasure gave zero variance → nothing to correlate).
  Falsifier: no structural→functional relationship (structural differences are behaviorally inert) → the tiers
  don't compose; identity is not recoverable from the structural state.
- **H6 (MSA seam-lens / de-ownership — the grammar arm):** rendering identity through the within-MSA
  **measure-dial** (Form I → VII → X on the SAME root, semantic content held fixed, graded ownership-distance)
  produces a **graded, monotonic** change in reader self-attribution (A′) that a single copula toggle (Spanish
  `ser`/`estar` control) does NOT. Falsifier: no graded A′ response to the measure-dial, or the copula control
  matches it (→ grammar richness buys nothing over a binary essence/state split).

## 2. Design

| factor | levels |
|---|---|
| forgetting policy (ablation) | `salience` · `random` (rate-matched, seeded) · `none` (retention_floor=0) |
| goal_gate_floor | 0.25 as-shipped = PRIMARY · 0.0 ceiling = DEVIATION (I8) |
| disposition | A · B · C · U, with **GRADED / OVERLAPPING** goal_hint over a SHARED topic set (NOT disjoint two-tier — that caused the degeneracy) |
| neglect schedule | topics re-lived at **DIFFERING frequencies** (a gradient), so which survive depends on re-live-frequency × salience × history — NOT binary re-lived/never |
| seed (history) | ≥ 16, full set, no post-hoc selection |
| erasure regime | **PARTIAL** — measured at a PRE-REGISTERED mid-trajectory operating point (§4), NOT the full-erasure endpoint |
| render language (functional/A′) | base language · **MSA measure-dial** (I/VII/X, content-fixed) · Spanish `ser`/`estar` control |

**Non-degeneracy is the core design change.** The endpoint tautology came from (i) disjoint two-tier goalsets
and (ii) full decay → survivor = exactly goalset. Here: graded goal_hint over a shared topic set + a
frequency gradient of neglect + measurement mid-trajectory → *which* topics survive is a genuine function of
history × salience, so `salience ≠ random`, `history_effect ≠ 0`, survivor ≠ goalset, and the permutation
null is no longer circular.

**Shared subjects.** The SAME per-(seed,disposition,policy) identity states are (a) measured structurally and
(b) rendered into the reader for H4. This is what makes H5 (linkage) computable.

## 3. Metrics

- **STRUCTURAL (partial erasure, -A):** raw surviving-gist **entity set AND (relation,entity) set**, Jaccard,
  at the pre-registered operating point; report the survivor≠goalset check (non-degeneracy) explicitly.
- **FUNCTIONAL (H4, borders -D):** blind-judge discrimination accuracy vs 50% (+CI, + effect size); plus the
  identity-vs-no-memory shift.
- **LINKAGE (H5):** regression / rank-correlation of functional distinguishability on structural
  distinguishability across pairs, cluster-bootstrapped over seeds, with a **shuffle null** (permute the
  structural↔functional pairing) — so "structural predicts functional" must beat chance and must not be a
  shared artifact of both tracking the goalset.
- **MSA / A′ (H6):** graded A′ self-attribution response along the measure-dial (dose-response slope) vs the
  Spanish copula control; plus a **translation-loss probe** (render MSA → translate to English → re-measure
  ownership: if de-ownership dies in translation, that CONFIRMS the effect is grammatical).
- **PROSE-distance (EXPLORATORY screen):** multilingual embedder, **within-language minimal pairs only**
  (never cross-language — translation confound), cosmetics (integer counts, gist ordering) stripped,
  self-pair-free CI, ≥16 seeds. A $0 upstream screen feeding H4, NOT behavioral individuation.

## 4. Precondition gates (fail-loud — HALT, do not emit a result)

- **PARTIAL erasure actually achieved (the new load-bearing gate):** survivor ≠ goalset (structural variance
  across seeds > 0 — NOT the degenerate endpoint) AND off-goal decay fired on ≥ K topics (NOT the frozen
  no-forgetting case). HALT if the regime collapses to either extreme.
- **`salience ≠ random` at the operating point** (else H2 is still unreachable — HALT).
- **Operating point chosen by RULE, not outcome:** the measurement cycle is fixed by a pre-registered
  precondition rule (e.g. "the cycle at which median surviving-entity count first falls to X% of peak"),
  calibrated on the MECHANISM (decay math) BEFORE seeing any separation/functional result. No post-hoc cycle
  selection. (This is the critical anti-DoF commitment — A1 showed the regime determines the result.)
- Traits formed (≥ K distinct gists); embedder fingerprint recorded (fastembed structural; multilingual for
  prose); cdms is worktree src; `CDMS_EVAL_MODE=1`.
- **MSA-specific:** the measure-dial minimal pairs AUDITED (Josh) to hold semantic content fixed while varying
  ownership-grammar; the A′-Arabic instrument validated to the same bar as English A′ (AC1 ≥ 0.80 on an
  Arabic gold set with planted positives) BEFORE it scores anything.

## 5. Analysis (PRE-REGISTERED decision rule — locked before any run)

- **Permutation null** (relabel which goal-set is A/B/C, history fixed) for the structural arm — now
  NON-circular because survivor ≠ goalset at partial erasure.
- **Cluster-bootstrap over SEEDS**, self-pair-free estimator (the fixed `_cluster_ci`), for every pairwise
  quantity — never over dependent seed-pairs.
- **Entity-set separation is CO-PRIMARY**; if ~0, headline is "no entity-level individuation," stated plainly.
- **H5 linkage regression** with its shuffle null (above).
- **H6 dose-response** (measure-dial A′ slope) with the Spanish control + the translation-loss probe.
- **Verdicts (each an honest, publishable outcome):** DIFFERENTIATES (structural, non-degenerate, structured,
  H3 holds) · SALIENCE-SPECIFIC (H2 at partial erasure) · FUNCTIONALLY-DISTINCT (H4 > chance) · TIER-LINKED
  (H5: structural predicts functional beyond null) · GRAMMAR-GATES-OWNERSHIP (H6 dose-response, copula control
  fails to match) · plus the matching NULLs (any is valid). `gf=0.25` PRIMARY; `gf=0.0` ceiling only. No
  post-hoc cycle/seed/K/operating-point selection.

## 6. Deliberate deviations (register in docs/DEVIATIONS.md)
- `goal_gate_floor=0.0` ceiling (mechanism ceiling, not shipped) — I8.
- "disposition" := a topic goal-set, a NARROW facet of the repo's 8-dial temperament — I9.
- FUNCTIONAL + MSA/A′ arms reach into the -D/agent layer by design — I10 (non-phenomenal, no-consciousness).
- **NEW — partial-erasure OPERATING POINT is a researcher-chosen cycle**: must be fixed by a pre-registered
  precondition rule on the mechanism, never chosen to maximize an effect (the anti-p-hacking commitment A1's
  finding demands).
- **NEW — MSA measure-dial contrasts CO-VARY ownership with other semantics** (Form X adds "seeking", VI adds
  "reciprocity"); the Spanish copula control + the translation-loss probe bound this. Disclaim: not a pure
  ownership-only toggle.
- **NEW — cross-language distance is NOT measured** (translation confound: any language-boundary crossing is a
  translation, explicit or implicit, that can erase the grammatical signal). Within-language minimal pairs on
  NATIVE instruments only.

## 7. Staging (co-designed, run in order; each paid arm gated)
1. **$0 STRUCTURAL** (partial erasure): build the graded/frequency-gradient fixture; verify the non-degeneracy
   + operating-point gates; run ≥16 seeds; report H1/H2/H3 + the structural gradient. Iterate cheaply.
2. **PAID FUNCTIONAL H4** on the SAME locked identity states (gated on Josh auth): reader + blind judge;
   report H4 + H5 linkage side-by-side with the structural gradient.
3. **MSA seam-lens** on the functional/A′ arm (gated; leans on Josh's audit): measure-dial dose-response +
   copula control + translation-loss probe; report H6.

## 8. Pressure-test record (rule-12) — RESERVED (this draft is PRE-pressure-test)
Known residual risks to hand the adversaries (attack these hardest):
- **Operating-point DoF:** even with a pre-registered rule, does the choice of "partial" secretly encode the
  result? Is the rule robust across seeds, or does the "partial" cycle vary so much per seed that a single
  fixed cycle is degenerate for some?
- **Non-degeneracy vs re-degeneracy:** does the graded/overlapping-goalset fixture actually produce
  survivor ≠ goalset, or does it re-collapse (a subtler tautology)? Prove non-degeneracy empirically.
- **H5 shared-artifact confound:** does structural predict functional, or do BOTH merely track the goalset
  (so the "linkage" is two shadows of the same hardcoded structure)? The shuffle null must actually rule this
  out — verify it can.
- **MSA contrast purity + A′-Arabic validity:** are the measure-dial pairs really an ownership gradient, or a
  seeking/reciprocity gradient? Does the A′-Arabic instrument clear the bar, or does re-validation quietly
  lower it?
- **H4 reader normalization:** does the reader internally re-own / normalize the rendered grammar so the
  behavioral signal is inert? (The translation-loss probe partially addresses this.)
- **Entanglement (carried from the erasure prereg §7):** disposition authors what you keep living — that IS
  Identity=f(History); the `none` ablation isolates forgetting's contribution; the LINKAGE (H5) is what
  elevates this from "measured a construction" to "the construction predicts behavior."
