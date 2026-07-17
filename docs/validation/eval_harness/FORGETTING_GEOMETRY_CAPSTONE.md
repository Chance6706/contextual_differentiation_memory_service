# The forgetting-geometry capstone — does disposition-driven forgetting create readable structure BEYOND the salience we impose?

**STATUS: DRAFT (2026-07-17) — the terminal STRUCTURAL test of the CDMS-A individuation thesis. NOT run.
Goes through a focused rule-12 pressure-test → lock → build (dedicated research venv) → run. $0 local.**
On branch `research/differentiation`. Supersedes the state-probe line (`RESOLVING_ANGLE_PROBE.md` v1/v2,
both tautological — see its §10). The behavioral arm (task #10 functional TOST) remains the terminal court (§7).

## 0. Why this is the capstone (and why full breadth, knowing it will likely be null)
Five structural attempts — frozen NULL → erasure ENDPOINT-DEGENERATE → tiered STRUCTURAL NEGATIVE → drift
HOMOGENIZATION → resolving-angle probe v1 (topic) / v2 (valence-lexeme) — all resolve to the SAME law:
**tautological readback XOR null.** Every readout that separates dispositions does so by recovering something
we WROTE IN (goalset / topic axis / valence lexeme); strip the written-in label and separation collapses to
noise (v2 strip test, real fastembed, reproduced: label 1.000 → object-only 0.688 ≈ null band 95th-pct 0.689).
Meta-finding: **disposition individuation is not a readable property of the memory STATE.**

This capstone is the definitive, publication-grade characterization of that negative — tested on the thesis's
**purest** substrate (pure salience geometry, zero content leakage) across **every** emergent-structure channel,
so the pivot to the behavioral arm rests on a comprehensive non-tautological negative, not a suggestive one.
**Full breadth is a deliberate choice (Josh):** a capstone's value is to be the reference that saves the next
researcher from re-running the dead ends — a single-channel null is a shrug; an instrumented negative across all
channels is a contribution. And there is a real (small) chance a channel B/C/D catches structure channel A
cannot (they test genuinely different — second-order, temporal, transfer — properties). If any channel
surprises us, it is a genuine figure in the forgetting *dynamics* — the thesis, finally at the right angle.

## 1. Design principle — hold content constant, vary only the salience FUNCTION
Every prior failure leaked CONTENT into the readout. The capstone forecloses that at the FIXTURE level:
- **Shared input.** Both poles ingest the SAME episodes — same topics, objects, relation labels, verbs. The
  stored gist vectors (`search_text` = subject+relation+object) are IDENTICAL across poles for matched gists
  ⇒ **there is no lexeme to read back** (this is what v1/v2 failed to prevent; here it is structural, not a gate).
- **Disposition = the salience gate, not the input.** The same episodes are differentially reinforced /
  protected vs. allowed to decay (different goal-gate / S0 salience weighting `w` over the shared topics). Which
  gists survive and how they are weighted EMERGES from the salience function on identical content.
- **The confirmatory question is emergent-BEYOND-imposed (the hinge).** The surviving state will ALWAYS reflect
  the weights we imposed (up-weighted topics survive heavier) — reading that back is the tautology in a new
  costume. The real question: does forgetting create structure **not reducible to the imposed weights**?

## 2. The tri-reference contract, per channel ([[feedback-tri-reference-null-tautology-real]])
Each channel emits three marked shapes; REAL is read only *between* the anchors:
- **NULL** — identical disposition (same `w`, different seed). Must NOT separate. (A real matched null, stronger
  than a synthetic shuffle.)
- **KNOWN-TAUTOLOGY** — the **imposed-weight** readback for that channel's statistic. WILL separate trivially;
  marked known-tautology, never a positive finding; doubles as the channel's **power gate** (if even the imposed
  baseline does not fire in the label-free representation, the channel is UNDERPOWERED, not null) and its
  **magnitude anchor** (REAL reported as a fraction of it) and **direction anchor** (REAL must be orthogonal to it).
- **REAL** — the emergent measure: structure the forgetting creates beyond the imposed weights.

## 3. The four channels — A primary (confirmatory), B/C/D secondary (all run + reported, FDR)
Setup: each subject = one consolidation run on shared input under a disposition weight profile `w` over the K
shared topics (e.g. A up-weights {auth,crypto}, B up-weights {payments,database} — same topics, different
emphasis). Label-free representation per subject over the K shared slots: **support** vector (per-topic support),
**centroid** matrix (support-weighted surviving-gist centroid per slot), **survival** mask, and the per-cycle
survival **trajectory**. (Exact geometric statistic per channel is a lock-time pin; the pressure-test attacks
whether each is well-posed and non-tautological.)

| channel | KNOWN-TAUTOLOGY (imposed) | REAL (emergent) | what only this channel can catch |
|---|---|---|---|
| **A — residual / orthogonal-to-imposed (PRIMARY)** | readout on the **support** vector (recovers `w`) | does the **centroid geometry** separate dispositions along a direction **orthogonal** to the imposed-support/weight axis (residualize `w` out)? | first-order emergent geometry — the broadest catch-all |
| **B — coupling** | coupling predicted by the **outer product** of the marginal weights (`w⊗w`) | does the observed pairwise **co-survival / centroid-coupling** matrix separate dispositions **beyond** the marginal-predicted coupling (excess coupling)? | *second-order* structure invisible to A's linear direction test — the "web of associations" |
| **C — trajectory** | decay order predicted by **weight rank** | does the actual per-topic **survival trajectory** over cycles separate dispositions beyond weight-rank, vs a **matched-pairs permutation** null? | *temporal/path* structure invisible to any end-state readout |
| **D — transfer** | per-topic weight on **SEEN** topics (trivially separates on trained topics) | train the readout on SEEN topics, test on **HELD-OUT** topics of the same category never seen weighted — does the disposition signature **transfer**? | a topic-*general* character vs. a per-item lookup — the strongest anti-tautology |

- **B and C are not downstream of A.** A is a first-order orthogonal-direction test; B (pairwise) and C (temporal)
  can carry signal A's linear end-state readout structurally cannot see. They earn independent runs.
- **D needs a richer fixture** — a disposition keyed to a topic CATEGORY (a *rule*, "up-weight security-flavored
  topics") rather than a fixed list, so held-out topics exist to transfer to. This is the one extra build
  (flagged, not silent); included per the capstone-completeness call.

## 4. Representation (label-free by construction)
The confirmatory representations are the **support / centroid / survival / trajectory** geometry over the shared
topic slots — NOT `search_text` (identical across poles ⇒ carries no signal AND no lexeme). Structured per-topic
slots (shared topics ⇒ slot identity is constant across poles, no topic leak). **Raw is primary; isotropy
correction is a reported diagnostic only** (label-leakage fear retired, PT4-overfit NIT8).

## 5. Statistics + guards (inherit the PT4/PT5 survivors)
- **ONE confirmatory primary = channel A.** B, C, D are pre-registered **secondary**, ALL fully run and reported,
  under **FDR (Benjamini–Hochberg)** across the {B,C,D} family. A secondary hit is labeled
  **exploratory-needs-replication** unless it survives FDR AND replicates on fresh seeds — never a confirmatory
  win on its own. This is the run-all-report-all rigor for a null-expected capstone (the multiple-comparisons
  trap is "claim a win if ANY fires"; reporting all with FDR + one primary is its opposite).
- **Permutation-distribution null (≥1000) per channel**, threshold = the permutation null's upper quantile
  (pre-registered), not an absolute bar. C additionally uses the **matched-pairs permutation** trajectory null
  (NOT the √2-miscalibrated within-self spread; circumambulation-as-signal dropped).
- **Power gate per channel** = the channel's KNOWN-TAUTOLOGY (imposed baseline) must fire in the SAME label-free
  representation used for REAL; else UNDERPOWERED, not null. (Fixes PT5-fixstat MUST_FIX3 — the power control
  must match the confirmatory contrast, not a topic-lexeme control.)
- **Orthogonality gate** REAL ⟂ imposed direction: **|cos| < τ**, τ set from a permutation CI on random
  directions in the same space (NOT a hand-picked 0.2 — PT5-fixstat SHOULD_FIX4); report the cosine with its
  null band.
- **Seeds ≫ 16** with null-sd reported (n=16 is a fat-tailed floor, sd≈0.14 measured); all hyperparameters
  (readout, folds, τ, quantile, seed count, cycles) pre-registered to numbers at lock; no post-hoc selection.

## 6. Verdicts (mechanized, per channel + family)
- **FIGURE RESOLVES (channel A):** A's REAL beats its ≥1000-perm null AND exceeds A's NULL AND is orthogonal to
  A's imposed direction — **conditional on A's power gate (imposed baseline) firing.** ⇒ forgetting creates
  first-order geometric structure beyond the imposed salience: a real figure in the dynamics.
- **NO FIGURE (channel A):** A's power gate fires but A's REAL sits at its permutation null ⇒ no emergent
  first-order structure. Reported **plainly**. (Report B/C/D likewise; any FDR-surviving + replicated secondary
  hit is flagged as an exploratory discovery, NOT a thesis resolution.)
- **UNDERPOWERED / INCONCLUSIVE (a channel):** its imposed-baseline power gate does NOT fire ⇒ the substrate
  can't carry that channel's signal; no verdict on that channel's REAL.
- **INVALID / OVERFIT (a channel):** its NULL (identical disposition) separates above its permutation null ⇒ the
  pipeline manufactures structure; fix before any claim.

## 7. Terminal falsifier (unchanged; this capstone is the terminal STRUCTURAL test)
The state question ends here. Whatever the outcome, the **behavioral arm is the terminal court**: task #10, the
powered functional **TOST** (~200/arm, blind judge disjoint from the reader), pre-registered with a concrete
equivalence margin δ + α + a power_sim. Decision logic (three branches, PT5-legit MUST_FIX2): the difference-test
rejects ⇒ deeds distinguishable (thesis survives); the **TOST rejects ⇒ deeds equivalent within δ ⇒ thesis FALSE,
HALT**; neither ⇒ INCONCLUSIVE/underpowered (NOT false). A NO-FIGURE capstone routes here; it does not itself
kill or save the thesis. The negative has relocated exactly once (state → behavior); behavior is terminal.

## 8. Cost + staging
- **$0 local.** Channels **A, B, C share the SAME subject runs** (three statistics over one surviving geometry +
  trajectory) — full breadth on A/B/C is near-free. **D needs the extra rule-based fixture** — the one genuine
  additional build. Embeds on **fastembed-gpu** in the dedicated research venv once CUDA-13 runtime is resolved;
  **canonical / reproducibility runs stay on CPU** (byte-determinism; CPU↔GPU drift can tip 0.90 merges).
- Staging: this DRAFT → **focused rule-12 pressure-test** (attack surfaces: does the shared-input fixture truly
  hold content constant with no residual leak; is each channel's imposed-tautology baseline a valid power gate;
  is A's orthogonal-residual statistic well-posed and non-tautological; is the FDR family honest; is D's
  category-rule fixture free of a new tautology) → **lock** (pin all numbers) → build → run → commit alongside
  the v2 negative → pivot to the task-#10 functional TOST prereg.

## 9. Pressure-test record (rule-12) — RESERVED.
