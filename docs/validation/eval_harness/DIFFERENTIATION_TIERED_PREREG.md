# Differentiation — the TIERED EXPLORATION (pre-registered EXPLORATORY analysis plan)

**STATUS: NOT LOCKED — structural arm resolved NEGATIVE during the rule-12 pressure-test; see
DIFFERENTIATION_TIERED_RESULTS.md.** The empirical pressure-test probe was decisive before lock: at
single-pass consolidation the non-degenerate survivor carries **stochastic per-topic recency, not
disposition-structured** individuation (history_effect sits AT its seed-shuffle null), and **salience is
inert** at the forgetting boundary. Per Josh's call the negative is reported and the individuation question
**pivots to the DRIFT / recall-reconsolidation mechanism** ([[project-cdms-recall-reconsolidation]]). This
DRAFT is retained for its design/pressure-test record; it is NOT run as-is. (Original draft header below.)

> **Mode (read first).** This run does **not** test a thesis. It **maps where interaction structure lies**
> across the tiers and their projections. It is EXPLORATORY by design. The disciplines that keep exploration
> honest (and that both prior disasters — the single-seed "+0.24", the prose glint — violated by treating
> exploration as confirmation):
> 1. **Pre-committed measurements** (§3) — no post-hoc metric cherry-picking.
> 2. **A null on every probe** (§3) — not to test a thesis, but so "where the interaction lies" is real
>    structure, not apophenia. *This is the falsifiability spine: every probe carries a null it could fail.*
> 3. **The generate-not-confirm boundary** (§5) — outputs are HYPOTHESIS-GENERATING. A candidate graduates to
>    a confirmatory follow-on ONLY IF (a) it beat its null here AND (b) it can be stated as a **falsifiable**
>    assertion with a pre-registered test on **FRESH seeds**. *Everything is falsifiable or it is not pursued.*

**Costs (plain dollars, upfront):** EXPLORE (structural) = **$0** local. CONFIRM (functional H4 / MSA) =
**paid**, behind a CostGuard cap, **GATED** per arm on a Josh authorization. Explore cheap, confirm expensive
— money follows signal.

---

## 0. Why this exists — the two nulls and the tautology

1. **Frozen-history NULL:** all topics every cycle → nothing idles → nothing forgotten → no individuation.
2. **Erasure ENDPOINT-DEGENERATE (4-agent pressure-test):** at full erasure the survivor ≡ goalset by
   construction (zero-variance separation, `history_effect ≡ 0`, circular permutation null, H2 unreachable).
   BUT salience ≠ random OFF the endpoint — the interaction signal lives in the non-degenerate regime the
   endpoint discards.

## 1. Guiding question (north star — NOT a thesis)

**Where does the interaction lie** — across **substrate × disposition × history**, and their **structural /
functional / grammatical** projections? Identity = f(substrate × disposition × history + interactions),
observable only as functional distinguishability. We hold substrate fixed, vary disposition × history in a
non-degenerate regime, and map **where beyond-null structure appears — and, as informatively, where it does
NOT** (a non-piece is as valuable as a piece; the endpoint null already told us the discard-RANKING is not a
piece).

## 2. Design — the steady-state NEGLECT GRADIENT (non-degeneracy without an operating-point knob)

The endpoint tautology came from (i) *disjoint two-tier* goalsets and (ii) *full* decay → survivor = exactly
goalset. The fix is a **gradient**, not a mid-trajectory snapshot:

- Topics are re-lived at **DIFFERING FREQUENCIES** over a **SHARED** topic set (graded `goal_hint`, not
  disjoint HI/LO). Mechanism: a gist re-lived often enough keeps resetting its idle clock
  (`_decay_gists` reads `cycle − last_cycle`) → survives; re-lived rarely → decays between touches. The
  **marginal band** (topics near the re-live/decay threshold) is where **history** (did a random event touch
  it recently) × **salience** (did `goal_hint` pad its support so it resists decay a little longer) DECIDE
  survival. This yields a **stable, non-degenerate survivor at STEADY STATE** — measured at the end, with **no
  fragile mid-trajectory operating point and no cycle-picking degree of freedom** (this removes the
  operating-point DoF the first draft carried).

| factor | levels |
|---|---|
| forgetting policy (ablation) | `salience` · `random` (rate-matched, seeded) · `none` (retention_floor=0) |
| goal_gate_floor | 0.25 as-shipped · 0.0 ceiling (DEVIATION I8) |
| disposition | A · B · C · U — GRADED / OVERLAPPING `goal_hint` over a shared topic set (NOT disjoint) |
| neglect schedule | topics re-lived at DIFFERING frequencies (the gradient) → a non-degenerate marginal band |
| seed (history) | ≥ 16, full set, no post-hoc selection |
| render language (functional/A′) | base · **MSA measure-dial** (IV → I → VII → X, content-fixed) · Spanish `ser`/`estar` control |

**Shared subjects:** the SAME per-(seed, disposition, policy) identity states feed BOTH the structural metric
AND the functional reader — the only way to look at whether structural and functional structure co-vary.

**Non-degeneracy is a PRECONDITION, verified empirically (§4), not assumed** — you cannot *explore* a
tautology; you need real variance to map.

## 3. What we MEASURE (pre-committed) + the null each probe carries — the falsifiability spine

Each row is a **lens we look through**, not a claim we accept/reject. We report the observed value, its null,
and whether it cleared. A probe with no null it could fail does not belong here.

| probe (what we map) | its null (what it could fail) |
|---|---|
| **Structural gradient** — surviving entity / (rel,ent) set across dispositions × policies × seeds | **permutation** (relabel which goalset is A/B/C) — now NON-circular (survivor ≠ goalset) |
| **Disposition vs history** — same-disp-across-seeds vs diff-disp overlap | cluster-boot over seeds (self-pair-free); is same-disp > diff-disp beyond seed noise? |
| **Salience vs random vs none** — does the survivor's structure differ by policy? | salience-vs-random at steady state (a *non*-difference is a real, publishable finding: "any forgetting suffices") |
| **Functional distinguishability** — blind judge tells A-loaded from B-loaded outputs | vs 50% chance + a no-memory control (identical preamble → judge can't win) |
| **Structural ↔ functional co-variation** — do structurally-distinct pairs read as more behaviorally distinct? | **shuffle** the structural↔functional pairing (rules out both merely tracking the goalset) |
| **MSA measure-dial** — graded A′ self-attribution along IV → I → VII → X (content held fixed) | the Spanish `ser`/`estar` single-axis **control** + the **translation-loss probe** (render → translate → re-measure; de-ownership dying in translation confirms it is grammatical) |
| **Prose-distance** (exploratory screen) — within-language minimal pairs, multilingual embedder, cosmetics stripped, self-pair-free CI | the ~0.03 metric floor (the `none` prose separation) + the fulcrum history-null (does distance scale with shared-history fraction f?) |

The MSA dial spans a real ownership range: **IV** (أفعل, causative — high agency/ownership, and common enough
that a reader parses it naturally) → **I** (bare) → **VII** (انفعل, mediopassive "becomes-X-ed", low agency) →
**X** (استفعل, seeks/deems — displaced). Held together by one root, so semantics stay fixed while the frame
rotates.

## 4. Precondition gates (fail-loud — HALT; the exploration is only VALID if these hold)

- **Non-degeneracy achieved:** survivor ≠ goalset (structural variance across seeds > 0 — NOT the degenerate
  endpoint) AND decay fired (NOT the frozen no-forgetting case). Prove it empirically; HALT on either extreme.
- **`salience ≠ random` at steady state** (else the policy probe is inert — HALT).
- Traits formed (≥ K distinct gists); embedder fingerprint recorded (fastembed structural; multilingual for
  prose); cdms is worktree src; `CDMS_EVAL_MODE=1`.
- **MSA-specific:** measure-dial minimal pairs AUDITED (Josh) to hold semantic content fixed while varying
  ownership-grammar; A′-Arabic instrument validated to the English bar (AC1 ≥ 0.80 on an Arabic gold set with
  planted positives) BEFORE it scores anything.

## 5. Analysis + the generate-not-confirm boundary

- **Report every probe's observed value + its null + whether it cleared.** Produce a **map** of the
  interaction landscape (which tiers/projections carry beyond-null structure; which don't).
- **NO confirmatory verdicts.** Outputs are candidate findings, explicitly labelled exploratory.
- **Graduation rule (the bar):** a candidate becomes a confirmatory follow-on ONLY IF **(a)** it beat its null
  here AND **(b)** it can be stated as a **falsifiable assertion with a pre-registered test on FRESH seeds**.
  Otherwise it is **not pursued.** (Josh: everything is falsifiable or it isn't pursued as a follow-on.)
- Explore on the $0 structural arm; only pay for the H4 / MSA confirmation of what the exploration flags.

## 6. Deliberate deviations (register in docs/DEVIATIONS.md)
- `goal_gate_floor=0.0` ceiling (mechanism ceiling, not shipped) — I8.
- "disposition" := a topic goal-set, a NARROW facet of the 8-dial temperament — I9.
- FUNCTIONAL + MSA/A′ arms reach into the -D/agent layer — I10 (non-phenomenal, no-consciousness).
- MSA measure-dial contrasts CO-VARY ownership with other semantics (X adds "seeking", VI "reciprocity", IV
  "causation"); the Spanish control + translation-loss probe bound this. Not a pure ownership-only toggle.
- Cross-language distance is NOT measured (translation confound); within-language minimal pairs on native
  instruments only.
- *(RESOLVED vs the first draft: the partial-erasure OPERATING-POINT DoF is GONE — the steady-state gradient
  makes the survivor non-degenerate at the end, so no cycle is chosen.)*

## 7. Staging (co-designed; run in order; each paid arm gated)
1. **$0 EXPLORE (structural):** build the gradient fixture; verify the non-degeneracy + `salience ≠ random`
   gates; run ≥16 seeds; map the structural landscape + nulls. Iterate cheaply.
2. **PAID CONFIRM — functional H4** on the SAME identity states (gated): reader + blind judge; map functional
   distinguishability + the structural↔functional co-variation, side-by-side with the structural gradient.
3. **MSA seam-lens** on the functional/A′ arm (gated; leans on Josh's audit): measure-dial dose-response +
   copula control + translation-loss probe.

## 8. Pressure-test record (rule-12) — RESERVED (this draft is PRE-pressure-test)
Adversary charge is EXPLORATION-appropriate: *will this surface FALSE structure, mislead, or let exploration
be laundered into confirmation?* Attack hardest:
- **Non-degeneracy vs re-collapse:** does the gradient actually yield survivor ≠ goalset, or a subtler
  tautology? Prove it empirically before locking.
- **Null validity:** is each probe's null actually valid (not circular the way the endpoint permutation was)?
  A null that can't fail is worthless.
- **Null-clearing artifacts:** can a candidate beat its null and STILL be an artifact (e.g., prose cosmetics)?
- **Boundary integrity:** does the generate-not-confirm boundary actually hold, or will an exciting
  null-clearing result get written up as confirmed without the fresh-seed follow-on?
- **Gradient DoF:** the re-live-frequency schedule is now the researcher knob the operating-point used to be —
  is it pre-committed and mechanism-justified, or tunable to manufacture a marginal band?
- **MSA contrast purity + A′-Arabic validity;** **H4 reader normalization** (does the reader re-own the
  grammar internally, making the behavioral signal inert — the translation-loss probe partially addresses).
