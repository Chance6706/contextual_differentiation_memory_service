# Differentiation via ERASURE — pre-registration (CORE THESIS) — **LOCKED 2026-07-17**

Supersedes the PRIMARY of DIFFERENTIATION_PREREG.md (the frozen-history cube). That cube is retained and
reported as an honest **NULL** (see §0); this document is the locked design that actually exercises the
thesis. Locked per CLAUDE.md rule 12 after two adversarial pressure-tests (validity + red-team) whose
MUST/SHOULD fixes are folded here (§7). No run until the precondition gates pass and (for the paid
secondary) Josh authorizes spend.

**Costs (plain dollars, upfront):** PRIMARY (structural) = **$0**, fully local (fastembed + CDMS, long
cycles, minutes–hours CPU). SECONDARY (functional) = **paid reader**, a real capable model over a bounded
prompt set behind a CostGuard cap — estimated **≤$15**, itemized at run time, GATED on a separate Josh
authorization. No Sparky, no OpenRouter panel for the primary.

---

## 0. Why this exists — the frozen-history NULL that motivated it

The frozen-history cube (DIFFERENTIATION_PREREG) fed **all topics to every disposition every cycle**, so no
topic ever went idle, gist idle-decay never fired, and **nothing was forgotten**. Result (verified, 8 seeds):
entity-level individuation = **0.00** (all dispositions retain all 8 topics); the apparent
`(relation,entity)` separation was relation-label noise, amplified by `top_gist(12)`, unstable across cycle
count (+0.205 @60cy vs +0.030 @80cy), with the same-disposition null ≈ different-disposition overlap
(0.386 vs 0.427). **"What remains after a crude forgetting policy" is vacuous when nothing is forgotten.**
This is committed as a real negative. It also diagnosed the fix: individuation lives in **erasure**, and
erasure requires **neglect + time** (CDMS gist idle-decay: a trait fades after ~92–396 idle cycles — the
mechanical form of "you forget what isn't in front of you," gradual, not amnesia).

## 1. Question + hypotheses

Does forgetting BY SALIENCE, acting on a **shared past** that each disposition then partly **neglects**,
leave behind **different surviving identities** — and does that survivor differ from what random/no
forgetting would leave? Disposition = a GOAL SET; it drives **which topics stay active** (reinforced) vs go
**idle** (fade). Identity = **what remains** in the gist state after long neglect.

- **H1 (erasure individuates):** under salience forgetting, the surviving-gist state of two DIFFERENT
  dispositions diverges MORE than under `none` (keep-all), and the divergence is disposition-STRUCTURED
  (similar>different) and exceeds a permutation null. Falsifier: salience ≈ none → no erasure individuation.
- **H2 (salience, not just any forgetting):** salience-forgetting's survivor is more disposition-structured
  than random-forgetting's. Falsifier: salience ≈ random → "forgetting-anything" suffices; salience adds nothing.
- **H3 (disposition separable from seed):** same disposition across different histories must stay MORE
  similar than different dispositions on matched histories (disposition effect > seed effect). Falsifier:
  same-disp ≈ diff-disp → the divergence is seed noise, INVALID (the frozen-cube failure mode).
- **SECONDARY H4 (functional distinguishability — the effect on the loaded agent):** loaded into a real
  capable reader, (a) an identity changes behavior vs the no-memory baseline, and (b) a **blind judge
  distinguishes identity-A-loaded from identity-B-loaded outputs ABOVE CHANCE** — and we report *by how
  much* (discrimination accuracy + effect size). This is FUNCTIONAL (behavioral distinguishability), an
  explicitly NON-phenomenal, no-consciousness measure ("would an outside observer tell them apart"), and it
  intentionally reaches toward the -D/agent layer — reported as secondary, not as the -A primary.

## 2. Design

| factor | levels |
|---|---|
| forgetting policy (ablation) | `salience` (cdms-full) · `random` (rate-matched, seeded) · `none` (retention_floor=0) |
| goal_gate_floor | **0.25 as-shipped = PRIMARY** · 0.0 ceiling = **DEVIATION** (mechanism ceiling) |
| disposition | A · B(~A, 3/4 shared goals) · C(≠A, disjoint) · U(dispositionless) |
| seed (history) | ≥ 16, full set, no post-hoc selection |
| phase | **shared past** (all topics, forms gists) → **drift** (only goal-topics stay active; off-goal go idle) → **long tail** (≥ ~300 cycles so idle-decay fires) |

Real embedder **fastembed** (asserted, fingerprint recorded); `CDMS_EVAL_MODE=1`; M-A cdms-provenance guard.
Disposition drives BEHAVIOR (which topics recur in the drift+tail phases), so off-goal gists go idle and
face the decay clock; salience determines each surviving gist's support → its idle-decay rate.

## 3. Metrics

- **PRIMARY (structural, -A):** the **raw surviving-gist state** — entity set AND `(relation,entity)` set —
  compared by Jaccard. NOT `top_gist(12)` (that is a -D/retrieval injection subset that inflates noise;
  demoted to at most a secondary view). "What remains."
- **SECONDARY (functional, borders -D):** inject the rendered identity (SessionStart preamble) of self-A vs
  self-B into ONE fixed real reader; collect answers over a fixed probe set; a **blind judge** (disjoint
  from the reader) attempts to tell which self produced each answer. Report discrimination accuracy vs 50%
  chance (with CI) + an effect size, and the identity-vs-no-memory behavioral shift ("if and by how much").

## 4. Precondition gates (fail-loud — HALT, do not emit a result)

Correctly computed (`evicted/(cycles*TURNS_PER_CYCLE)`, not the old hardcoded /250) and ENFORCED:
- **Erasure actually happened:** cumulative `gists_decayed ≥ 1` per idle topic AND off-goal entity-count
  drops materially from the shared-past peak under `salience` (else no forgetting → HALT, as in §0).
- Traits formed and are non-trivial (≥ K distinct gists); backend == fastembed; cdms is worktree src.

## 5. Analysis (PRE-REGISTERED — decision rule locked before any run)

- **Permutation null (M2):** per seed, randomly relabel which goal-set is A/B/C (history fixed), recompute
  the separation; report observed vs the permutation distribution + p. A positive counts ONLY if observed
  exceeds the permutation null. (Kills the "similar>different is guaranteed by construction" tautology.)
- **Cluster-bootstrap over SEEDS** for every pairwise quantity (M4) — never over dependent seed-pairs.
- **Entity-set separation is a CO-PRIMARY** (M1): if it is ~0, the headline is "no entity-level
  individuation," stated plainly, regardless of tuple-metric numbers.
- **Verdicts:** DIFFERENTIATES (H1 holds: salience > none, structured, beats permutation null, H3 holds) ·
  SALIENCE-SPECIFIC (H2: salience > random) · NULL (salience ≈ none or ≈ random) · INVALID (H3 fails or a
  precondition gate trips). An honest NULL is a valid, publishable outcome. `gf=0.25` is the PRIMARY;
  `gf=0.0` is reported as the mechanism ceiling only. No post-hoc cycle/seed/K selection.

## 6. Deliberate deviations (register in docs/DEVIATIONS.md)
- `goal_gate_floor=0.0` ceiling arm: shipped behavior floors off-goal salience at 0.25 (anti-total-amnesia);
  we lift it to test the mechanism's individuation ceiling. Disclaim: NOT the shipped product.
- "disposition" := a topic GOAL SET — a NARROW facet of temperament (repo's real construct = 8 dials).
  Flag per rule 11; do not claim personality/temperament individuation generally.
- SECONDARY functional metric reaches into the -D/agent layer by design (Josh: we still want to know the
  effect on the loaded agent). Reported as secondary; NON-phenomenal, no-consciousness framing pinned.

## 7. Pressure-test record (rule-12) — folded from two adversarial reviews (pre-lock)
Both reviews (validity-diff, redteam-diff) on the frozen-history cube. MUST_FIX folded INTO this design:
- **M1** entity individuation ~0 → entity-set is a CO-PRIMARY; the design now creates real erasure so it can
  be nonzero. **M2** tautology/no null → permutation null pre-registered (§5). **M3** prereg≠impl / over-time
  → the drift+tail design IS the over-time trajectory; snapshots per cycle; onset reported. **M4** pseudo-
  replication → cluster-bootstrap over seeds. **M5** preconditions unenforced + 10× denom → §4 corrected +
  HALT. **S1** metric discards weighting → raw-state primary + the FUNCTIONAL secondary capture what the set
  misses. **S2** relation "inert" → REFUTED empirically (differential forgetting flips relations on shared
  topics 5/8), but disclosed as partly small-sample; permutation null adjudicates. **S4** effect = gate+weak-
  eviction property → the erasure design makes eviction the load-bearing mechanism, reported as such. **S5**
  multiple comparisons → single designated PRIMARY (structural, gf=0.25, salience-vs-none) + decision rule.
  **N7** canonical-entity collision → aggregate entity by per-episode ground-truth majority vote, not
  order-dependent substring. **N8** gf=0 not a true filter → the drift design (not the gate) is the erasure
  driver. **N10** "surfaced=salience-ranked" wrong → corrected; top_gist demoted.
- **Residual risk / RESERVED:** the drift schedule and the FUNCTIONAL-reader design are NEW here and were
  not in the adversarial reviews. A final focused pressure-test runs on those two BEFORE the paid secondary
  run (not blocking the $0 structural run). Disposition/history remain entangled by design (disposition
  authors what you keep living) — that IS Identity=f(History); the `none` ablation isolates forgetting's
  contribution.

## Amendment A1 (disclosed, pre-run — 2026-07-17, Josh)
The FUNCTIONAL secondary (H4/§3) runs as a **reader-tier sweep**, not a single reader: (a) a **LOCAL** reader
via ollama ($0, breadth + reproducibility across the salience-matrix's runtime/FT/quant axis) AND (b) a
**frontier cloud** reader (the ≤$15 paid arm, the capability-tier check). Same fixed probe set; the blind
judge is disjoint from every reader (reader≠judge). Report distinguishability + effect size PER reader tier,
so "does an identity move the loaded agent, and by how much" is answered across capability, not at one point.
The local arm is $0 and ungated; only the frontier cloud arm needs the spend authorization (given).

## Results — PENDING (structural first, $0; functional secondary gated on Josh + its own pressure-test)
