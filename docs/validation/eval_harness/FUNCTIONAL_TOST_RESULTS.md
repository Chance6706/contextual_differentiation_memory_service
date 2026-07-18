# The functional TOST — RESULTS (task #10; the terminal falsifier)

**Run: 2026-07-18, locked design v3-FINAL (commit 155f840), executed as locked, one pass, no optional
stopping. 💵 main run $10.44; arm total $15.48 of the $50 authorization. Per-item data:
`tost_main_items.jsonl`; aggregates: `tost_main_metrics.json`; caches retained.**

## VERDICT (mechanized, branch 2, all validity gates passed):

> **EQUIVALENT — THESIS FALSE, HALT.**

**The branch-2 verdict, stated to the pinned floor (prereg §11: "thesis FALSE as operationally defined, HALT") and the §7 scope ceiling:** *CDMS-A's disposition
individuation is not detectable in enacted deeds within δ = 0.10 at this substrate; the thesis is false
as operationally defined.*

## The numbers (all arms, tri-reference)
| arm | n | result |
|---|---|---|
| **REAL** (stripped, pooled, A-vs-C) | 799/800 | **acc 0.532, 90% CI [0.476, 0.588]** — TOST rejects (CI ⊂ (0.40, 0.60)); difference test does NOT reject (LB < 0.5) ⇒ **EQUIVALENT** |
| EXPRESSION gate (same-seed, unstripped) | 48 | **0.958** (90% LB 0.917 ≥ 0.80) — **PASS**: the reader richly enacts its loaded payload |
| POOLED-UNSTRIPPED (content-included anchor) | 100 | 0.520 [0.44, 0.60] — even with topic content visible, dispositions are ~indistinguishable under the honest (pooled-reference) protocol |
| NULL (A-vs-A, stripped, pooled) | 96 | X-rate 0.510, inside the permutation band (95%: ~[0.42, 0.58]) — no manufacture |
| PRO judge subset (robustness) | 100 | 0.520 [0.44, 0.60] — corroborates the primary judge |
| NEUTRAL secondary (passive leak) | 48 | 0.521 [0.40, 0.64] — ~chance, as pilot-measured (scope boundary) |
| BOW stylometric diagnostic (LOSO) | 40 items | **0.75** (point diagnostic, non-prereg variant — see D1) — a linear word-count trace persists (diagnostic, never verdict, per §7) |

All secondary-arm CIs bracket 0.5 and are wide (binomial 90%; the pinned 3-way bootstrap widens them further) — consistent with ~chance at modest n.

Gates and guards: unparse 0.13% (≪ 12%); in-run sig_t 0.23 (≤ 0.4 — no downgrade); impute-as-miss
dual-analysis CI [0.477, 0.590] — **branch agreement** ✓; fresh-14 gate n/a (branch-1 only).

## What this result IS (pre-registered scope, §7)
- The thesis was operationalized (prereg §1, δ folded into the definition): *individuation ≝ above-chance
  relational distinguishability of enacted deeds BY A MARGIN ≥ δ, to a blind frontier judge.* On the
  locked substrate — valence-matched imposed dispositions, identity-eliciting tasks, topic-stripped deeds,
  pooled references, one frontier reader (claude-sonnet-4.6), two cross-family judges (gemini-2.5-flash
  primary, -pro robustness) — that proposition is **false**: the TOST establishes equivalence within
  δ = 0.10 with every fairness gate passing.
- **Where the surviving signal localizes:** the same-seed expression gate (unstripped) matches at
  0.958 — confirming the instrument is live (the reader does enact seed-specific payload) — but this
  is the seed-FINGERPRINTING channel (pilot-3b: same-seed→pooled collapses 1.000→0.565;
  PT8-construct ~47%). Once references are pooled across seeds, dispositions are ~indistinguishable
  whether deeds are unstripped (0.520) or stripped (0.532): the only thing the judge tracks is a
  specific generation's fingerprint, not the disposition. This LOCALIZES the negative; it is not a
  per-history individuation finding and does not re-open one (the state arc closed
  history_effect ≡ 0). A linear stylometric classifier still separates the dispositions (BOW 0.75)
  — a machine-detectable trace that no frontier judge in this protocol converts into functional
  distinguishability.
- This kills **this substrate's thesis**. It does not adjudicate other substrates, richer dispositions, or
  other operationalizations — any such claim would need a new thesis and a new prereg (§7). No
  phenomenology (I10).


**Neutral-demotion disclosure (prereg §11, pinned):** *The confirmatory arm was moved from neutral
to identity-eliciting tasks after exploratory pilots (excluded from confirmatory) showed neutral tasks
give the reader no occasion to enact its disposition (neutral 2AFC ≈ chance), making the hypothesis
untestable on that tier; the neutral arm is retained and reported as a secondary passive-leak read
(0.521 here).* Under branch-2 this cuts FOR the verdict: the confirmatory sat on the tier most likely
to show a signal, and none survived.

## Disclosed deviations (implementation vs the locked prereg)
1. **The LEAK gate as implemented is not the prereg's variant.** §3 specified a BOW domain classifier
   *trained on unstripped deeds* (seed-fold split) *tested on stripped* with recovery CI required to
   include 0.5; the runner computed stripped-trained BOW 2AFC variants instead (0.75), and the verdict
   chain did not consult a leak gate. **Why the verdict is robust to this:** the LEAK gate exists to
   prevent residual topic content from manufacturing a false DISTINGUISHABLE; leak can only make
   distinguishing *easier*. An EQUIVALENT verdict cannot be produced by leak — the judge failed to
   distinguish even with whatever residue remains. Flagged for the PT8 round-2 audit.
2. n_real = 799 (one item unparsed after re-ask, excluded + counted; dual-analysis covers it).
3. NULL arm n = 96 parsed of 100 (4 unparsed) vs the prereg's 100 — immaterial to the band test.
4. Against the OPPOSITE concern (over-stripping manufacturing a false EQUIVALENT): the
   pooled-UNSTRIPPED anchor read 0.520 — dispositions are ~chance even with full topic content
   visible, so the equivalence is not an artifact of the masker.

## The arc this closes
State arc: five structural attempts + the forgetting-geometry capstone, confirmed unchanged across the full plasticity ladder (task #16, every guardrail-removal rung) → **state = f(imposed) ⊕ noise**
(no fourth term; tautological-readback XOR null throughout). Behavioral arc: five measuring rounds
($5.04) stripped away, in turn, the topic tautology, the valence tautology, and seed fingerprinting;
PT8 (round 1) forced the honest protocol; the locked terminal run then answered: **the de-confounded
disposition signal that survives is machine-traceable but not functionally distinguishable to a frontier
judge within the pre-committed margin.** The negative relocated exactly once (state → behavior), behavior
was the terminal court, and the court has ruled. **The program HALTS on its pre-registered terms.**


## Post-verdict audit (PT9 — the final agent round, 3 reviewers, $0 on the committed JSONL)
- **PT9-narrative (scope/honesty): CONDITIONAL PASS → fixes A–G applied** (commit 34375a9): provenance
  correction, the pinned neutral-demotion disclosure, CIs on all arms, the per-history framing replaced
  with the honest localization, HALT-scope stated.
- **PT9-robust (estimator battery): VERDICT STABLE.** The naive iid-binomial would have *spuriously*
  rejected toward "distinguishable" (LB 0.503) — the clustering correction is load-bearing and correct
  (measured sig_t 0.23). Every better-calibrated estimator is NARROWER than the pinned SETS and preserves
  EQUIVALENT: CR-multiway [0.491, 0.573], studentized-t [0.489, 0.568], GLMM-MoM [0.486, 0.577]; the
  over-conservative full-multiplicity bootstrap would only downgrade to INCONCLUSIVE — **no defensible
  estimator supports the thesis.** Deed-jackknife: no single deed drives the result (max leverage 0.0013).
  **Retro-power:** the design detects a true ≥0.56–0.59 at 0.85 power (≥0.60 at ≥0.90) — the absence of a
  functionally-actionable signal is evidence FOR equivalence, not low power. Additional record: a judge
  label-preference artifact (acc|Y 0.564 vs acc|X 0.500 — neutralized by exact balance; further evidence
  the residual structure is judge-side, not disposition); task-10 significantly BELOW chance (an
  anti-signal); no task survives BH-FDR; the mixture check bounds any subpopulation at <0.59 (no masked
  strong effect); seed-side sd 0.074/0.036 (not quite the assumed 0 — absorbed by the 3-way estimator).
- **PT9-audit (mechanization/conformance): [pending at this commit; folded on receipt].**

**What HALT binds:** no further paid runs and no new thesis on this substrate without a new pre-registration and Josh's decision; the pre-authorized $0 worktree exploration is INCONCLUSIVE-scoped and does not apply (this is branch-2). HALT does not bind the PT9 results audit or the publication write-up.
