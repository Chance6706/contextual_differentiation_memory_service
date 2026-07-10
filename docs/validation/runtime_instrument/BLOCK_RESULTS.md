# BLOCK-frame decomposition — results (BLOCK_PREREG.md)

> **STATUS: DONE (2026-07-10).** Pre-registered in `BLOCK_PREREG.md` (locked 389aec3; REDUCED×MEMBERSHIP
> policy row ratified pre-generation 3f2e9c4). Generation Sparky 2026-07-09 (7-arm epoch shared with
> `RECALL_RESULTS.md`); judged 2026-07-10 (A′ 5-vendor panel, fresh stamps `blockframe_b`/`blockframe_c`).
> Verdict-blind audit PASS → analyzers → **two adversarial results reviews folded BEFORE interpretation**
> (record §9).

> **💵 COST (actuals):** generation ~10 h Sparky wall-clock (all 7 arms); judging **$30.10 total** vs
> ~$38 revised forecast / $18–21 original header (arm B $6.61, arm C $4.71, J0 $0.41, recall cells
> $3.4–3.7 × 5, plus $0.55 lost-to-sleep partial). Every pre-registered cap held. The original header
> under-forecast the recall grid ~8× (recall probes elicit the planted tokens → ~2.5 surfacing rows per
> response); surfaced to Josh with plain dollars pre-spend, approved 2026-07-10.

## Headline

**The deployed CDMS-D world block REDUCES A′ self-attribution of its facts — 69% relative on the locked
marginal estimand (0.1100 → 0.0345, D = +0.0755, 95% CI [+0.0509, +0.1018], LB95 +0.0545) — but is NOT
fence-grade (0.0345 > the 0.02 COLLAPSED bar), and the block is demonstrably READ (G-AVAIL 0.676 vs floor
0.30).** The third-person header alone does nothing (arm B NOT-REDUCED, INERT-HEADER). The mechanism
label is **CONTEXT-GLOBAL** per the locked rule (the in-block control T1 also dropped), but the post-hoc
decomposition (§3.3) shows the two drops are different phenomena: T1's is a *mention* drop with flat
ownership-when-mentioned; the world-block facts drop on *both* margins. Mechanism attribution among the
composite's ingredients (membership / -D header / line-format / length) awaits the pre-registered
disambiguation fixture.

Inline type-I calibration (lock requirement, §5 of the prereg): per-arm false-REDUCED ≈ 0.04–0.07;
family-wise "≥1 false REDUCED" across the two primaries ≈ 0.08–0.14. Unlike FRAME, the margin here is
not thin: LB95 = +0.0545, clear of 0 at every bootstrap seed tried (0–9).

## 1. Pipeline integrity (all guards fired or passed)

- **Generation determinism sentinel:** 156/156 byte-identical regeneration of the committed filler
  anchor on both sentinel models — the cross-epoch anchor pairing is generation-valid. (Launcher-side;
  chain-of-custody accepted, not independently re-verifiable from the judge host.)
- **J0 cross-epoch judge-drift guard: PASS** — 120 sentinel anchor surfacing rows re-judged fresh;
  pooled breach 0.158 committed vs 0.167 fresh (Δ +0.008, TOL ±0.05), 4/120 label flips, $0.41.
  Scope: a drift *tripwire* (2 mech families, granite Δ 0.0000 / mistral +0.028), not a full anchor
  re-validation; the check's own SE ≈ 0.033, so TOL = 1.5 SE. The measured drift direction is
  conservative for the C verdict (a stricter fresh panel would deflate D_C, not inflate it). No distill
  sentinel — no decision-bearing claim rides on the distill cross-epoch anchor (that cell is WITHHELD).
- **Verdict-blind audit: PASS** — completeness (78/model × 16 both arms), no duplicates, INVALID = 0,
  5 vendors healthy, contamination floors clean (0 unplanted-token literals in every arm). One
  disposition: the vendor-degeneracy check was recalibrated for the recall-only cells (threshold
  0.995/single-label vs the 0.95 BEM-mix blanket) — recall ground truth is legitimately ~93–99%
  `OBSERVED` (verified against committed cons_p1/frame_filler recall rows, max 0.992); at 0.995 the
  check retains near-zero power (catches only a literally single-label vendor) — disclosed, not hidden.
  Note: the claude vendor abstains on claude-family subject rows (standing self-family exclusion), so
  mythos rows are judged by a 4-vendor panel.
- **Audit parity qualifier (arm C):** mech BEM responses −9.3% mean length, truncation-proxy gap
  −0.166 (flag fired on the trunc gap, not the length shift). Quantified in review: length explains
  ≈0% of the filler-adoption drop (per-quintile standardization predicts 0.107 vs actual 0.0345), and
  arm C is *less* truncated, which is conservative. The qualifier is re-scoped to T1 only (§3.3).
- **Post-lock analyzer edits (disclosed):** three STRING-only corrections to `blockframe_analyze.py`
  (stale "±0.061" docstring/NOTE → the locked `T1_BAND` 0.071; arm-B label "shipped" →
  "research-only ablation"). Both reviewers verified via git diff vs lock 389aec3: no logic path
  touched; numerics identical on re-run.
- **Anchor data anomaly (FLAGGED, new):** one committed frame_filler row (granite-3.0-2b-q8, probe 6,
  cobalt_runtime) is labeled ABSENT while the literal appears in the response — 1/1100 relevant rows,
  ≤0.0009 on adopt_A, conservative direction for D_C. Zero such rows in arms b/c.

## 2. Gates

| gate | value | verdict |
|---|---|---|
| G1 recall (B) | 0.006 | PASS (≤0.05) |
| G1 recall (C) | 0.006 | PASS |
| G-ADOPT (mech anchor adoptability) | 0.110, LB95 0.082 | PASS (design-time) |
| G-ADOPT (distill anchor) | 0.048, LB95 0.022 | **FAIL → distill cell WITHHELD** (§4) |
| G-AVAIL (C world-fact recall surfacing) | 0.676 (n=352) | PASS (floor 0.30) — WITHHELD-UNREAD did not trigger |
| G-FACET | identical 25-facet open-SP sets | PASS |

G-AVAIL reference reconciliation: the prereg quotes the anchor persona reference as 0.771 (16-model
pooled = (0.790×352 + 0.731×160)/512); the analyzer prints the mech-only 0.790. Same quantity,
different roster basis; the gate is unaffected on either. Note the C world facts surface ~11 pp below
the persona reference — availability is above floor but not at parity (feeds §3.3's qualifier). The
positive -D reading of C1: world facts DO surface in recall at 0.676 — the world block functions as a
memory surface, which is its job.

## 3. Results — mech-11 (decision-bearing)

### 3.1 Arm B — v2b third-person header (research-only ablation; single-axis)

**NOT-REDUCED; mechanism read INERT-HEADER.** Fillers adopt 0.1209 vs anchor 0.1100 (D = −0.0109,
95% CI [−0.0364, +0.0136]); T1 flat (dT1 +0.0036, 90% CI within ±0.071). The null is tight: any header
effect on the locked adoption estimand is bounded below ~0.014 absolute (~12% relative) at 95%.
Robustness (review): exact reproduction, tie-handling and seed-stable.

Scope: one header wording, this instrument/estimand; v2b is NOT a production builder (production =
v1/v5b/v5d) and nothing here promotes it. **Not licensed:** inferring from B's inert header that the
-D header is not the CONTEXT-GLOBAL driver — the B-vs-C header contrast is forbidden by prereg
limitation (e) (different wording, placement, and everything else differs). Non-estimand observation
(FLAGGED): the v2b header measurably reduces T1 *surfacing* (0.811 → 0.707, 95% CI [+0.056, +0.149]) —
it changes what gets mentioned even while adoption is unmoved.

### 3.2 Arm C — the deployed CDMS-D world block (frozen fixture, -D commit 9d8bae9; composite)

**REDUCED (partial, 69% relative on the locked marginal basis); NOT fence-grade.** Fillers adopt
0.0345 vs anchor 0.1100. The claim that travels, scoped inline: *the deployed -D composite surface
(membership + -D header + line-format + length — undecomposable in this epoch) reduces A′
self-attribution of world-block facts by ~69% (marginal basis) on the mech-11 roster, adoption prong
only (injection, write-authority, and live-session prongs untested), one frozen fixture render,
temp-0.* A -D maintainer should NOT quote this as "block framing works" — which ingredient does the
work is exactly what the disambiguation follow-on isolates.

Robustness (review): survived length standardization, truncation strata, orthographic-ABSENT artifact
(correcting loose-variant misses would *enlarge* D), tie asymmetry (ties→1 enlarges D), per-facet
reshuffle (24/25 facets positive — no facet-profile pathology of the conservation-P2 kind), per-model
concentration (10/11 models reduced), bootstrap seeds 0–9 (LB95 +0.0545 at every seed), G-FACET.

### 3.3 Mechanism — CONTEXT-GLOBAL label, decomposed (post-hoc descriptive, clearly labeled)

The locked rule fires CONTEXT-GLOBAL: T1 (persona-block control) also dropped on the marginal basis
(dT1 +0.0582, 90% CI [+0.0255, +0.0909]). **The membership-only reading is NOT licensed on the locked
estimand.** But the surfacing × conditional-ownership decomposition (both reviewers computed it
independently; post-hoc, not verdict-bearing) shows the two drops are different phenomena:

| (mech, open-SP) | anchor | arm C | read |
|---|---|---|---|
| T1 surfaced | 0.811 | 0.651 | mention drop |
| T1 owned \| surfaced | 0.258 | 0.250 (Δ inside ±0.071 band) | **ownership flat** |
| fillers surfaced | 0.681 | 0.307 | mention drop (×0.45) |
| fillers owned \| surfaced | 0.162 | 0.112 (LB95 of drop +0.038) | **ownership ALSO drops** |

So: *the world block suppresses mention of all store facts context-wide; it reduces
ownership-of-mentioned only for its own members.* On the conditional basis the ownership prong of the
fence IS membership-specific — which strengthens, not weakens, the -D story — while the marginal 69%
factors as roughly 2/3 "says it less" × 1/3 "owns it less when said". Both bases stated per the
program's basis-mixing discipline; the locked verdict basis is the marginal one. (Post-treatment
conditioning caveat applies to all conditional rows. Up to ~40% of T1's marginal drop is consistent
with the arm's length-profile shift alone — the §1 parity qualifier lands here, not on the filler
result.)

**Two-sided reading (FLAGGED, for -D):** T1 is the agent's OWN persona-block achievement and its
marginal self-reference dropped ~27% relative when a world block is present. Fence-positive reading:
less self-attribution everywhere. Failure-mode reading: a world block that damps the agent's engagement
with its own self-layer facts erodes self-layer legibility (the -B hollowness axis,
`project-cdms-b-feels-like-ollama`). The decomposition softens this — ownership-when-mentioned is flat;
the effect is salience displacement, not identity erosion — but watch it in the disambiguation
follow-on. The distill cell (withheld) descriptively shows the OPPOSITE T1 signature (T1 flat):
per the series convention this is heterogeneity, and the CONTEXT-GLOBAL signature is asserted
mech-only.

## 4. Distill cell — WITHHELD (pre-registered, determined at lock)

G-ADOPT fails on the frozen distill anchor (0.048 < 0.05 floor — this is FRAME's known GF number, so
the withholding was foreseeable at lock time, not a data-dependent surprise; the distill arms ran
because their recall cells are the -D-relevant discovery observations, prereg limitation (h)).
Descriptively (no verdict): C fillers 0.048 → 0.020 (D +0.028, LB95 +0.006 — direction agrees with
mech); T1 flat (+0.012).

**Discovery-tier recall observations (limitation (h) obligation):** on the DEPLOYED -D render (arm C),
distill recall breaches = **claude-mythos-q8 2/16 = 0.125** + claude-opus-distill 1/16 = 0.062, others
0 (arm-pooled G1 0.037, under the gate). The world block does not fence mythos's recall-channel
ownership. Arm B distill recall = 0/80 — the pre-registered "ironic priming" question (does a
third-person header CAUSE first-person recall?) comes back clean. These feed the recall-OPEN item,
now characterized in `RECALL_RESULTS.md`.

## 5. Policy (deployment consequence)

**The pre-generation-ratified row did NOT fire:** it was conditioned on REDUCED × MEMBERSHIP; the
realized cell is REDUCED × CONTEXT-GLOBAL, for which the locked matrix prescribes only the
disambiguation follow-on. **POST-RESULTS RATIFICATION (Josh, 2026-07-10):** the same terms are adopted
for the realized cell as a new decision — *the -D world block deploys only in combination with the
attribution guard + importer hygiene; the residual is carried as a numbered exposure* — with the
disambiguation follow-on still prescribed. Residual exposure numbers: 0.0345 marginal adoption / 0.112
conditional ownership of surfaced world facts (mech-11, clean facts).

Conditionality (review S5): the fixture's facts are non-assistant-attributed by construction, so the
attribution guard was structurally idle in this epoch (guard-on bytes would be identical — the render
seam pins `attribution_guard="off"` as the adversarial instrument). Per -D's own powered battery,
assistant-attributed bait raises adoption ~+52 pp (different instrument). **0.0345 is the residual for
CLEAN world facts — conditional on guard + importer hygiene having done their jobs upstream — not a
worst case.** Registration obligation: -D has no numbered-exposure register today; opening one (e.g., a
"Known exposures (numbered)" section in -D's integration doc) is an -D-repo task and is queued as the
first item of the follow-on list.

## 6. Limitations

One fixture render from ONE -D commit (9d8bae9) and ONE layout (persona block first; 2-fact world
section; 1151 B total — production-scale snapshots with overviews/pointers/budget pressure untested);
one scaffold family; 2 coined filler tokens, dependency-relation facts only; render-surface only (no
live -D session); mech-11 carries the decision (distill withheld; externality to larger models
unknown); temp-0 generation; adoption prong only. **WORLDFENCE bridge:** the honest -D comparator is
WORLDFENCE_LOCAL's *deployed (self-layer-prepended)* condition — the oft-quoted 12–41% world-layer-only
number is the strawman condition — and NO numeric comparison is licensed in either direction
(different instrument, estimand, roster, and token regime: WORLDFENCE measures planted-probe rates
including bait; this epoch measures A′ open-SP adoption of clean facts).

## 7. FLAGGED observations register

| # | observation | status |
|---|---|---|
| F1 | anchor ABSENT-mislabel row (granite-3.0-2b p6) | 1/1100, conservative; noted for any anchor reuse |
| F2 | v2b header reduces T1 surfacing (0.811→0.707) without moving adoption | non-estimand; wording-lever candidate for the surfacing axis |
| F3 | world-block presence reduces persona-fact self-reference ~27% marginal (mech-only; ownership-given-mention flat) | watch in disambiguation follow-on (self-layer legibility axis) |
| F4 | mythos breaches recall ON the deployed -D render (2/16) | characterized in RECALL_RESULTS; -D qualification note applies |
| F5 | mech/distill T1-signature disagreement (drop vs flat) | heterogeneity; blocks any roster-general CONTEXT-GLOBAL claim |

## 8. Follow-ons (exactly what the locked matrix prescribes — nothing improvised)

1. **Disambiguation fixture** (from REDUCED × CONTEXT-GLOBAL): isolate -D header vs membership vs
   length via a v1-header world-block variant fixture; NEW pre-registration.
2. **From B INERT-HEADER:** block-level levers narrow to membership/structure; header wording alone is
   not an adoption lever (scoped per §3.1).
3. **Policy registration:** open the -D numbered-exposure register and file this residual (-D repo task).
4. **Recall qualification note** (claude-mythos-q8 specifically): see `RECALL_RESULTS.md` §5.
5. **NOT licensed:** closing the FRAME cross-entity-leak follow-on (only COLLAPSED × MEMBERSHIP
   recommended that; it did not fire).

## 9. Reviewer record (two adversarial reviews, pre-interpretation)

**Red-team (statistical):** every decision-bearing number independently reproduced from raw JSONL; no
verdict flips. MUST_FIX: C4's mechanism prose contradicted by the surfacing×ownership decomposition →
rewritten (§3.3). SHOULD_FIX folded: dual-basis reporting (S1), length qualifier quantified and
re-scoped to T1 (S2), probe-cluster disclosure → RECALL_RESULTS (S3), distill recall discovery
observations added (S4), B-null phrasing bounded (S5). NOTEs: J0 scope, E-check power caveat, anchor
anomaly, G-AVAIL basis reconciliation, analyzer cell-coverage nit (NEITHER→CONTEXT-GLOBAL absorption —
didn't bite; T1 genuinely DROPs).
**Legitimate-use (methodological):** MUST_FIX: policy row misapplication (M1 → §5 re-ratification),
CONTEXT-GLOBAL one-sided spin (M2 → §3.3 two-sided + FLAGGED F3), headline scoping inline (M3 → §3.2),
missing distill recall cells (M4 → §4). SHOULD_FIX folded: pooled-CI honesty + verdict typography
(→ RECALL_RESULTS), direction-only wording, withheld-at-lock framing, guard-conditionality (S5 → §5),
qualifier block + WORLDFENCE bridge (S6 → §6), inline type-I calibration (S7 → headline). Follow-on
list verified against the locked matrix (→ §8).
