# Attribution-frame decomposition — results

**Pre-registration:** [`FRAME_PREREG.md`](FRAME_PREREG.md) (LOCKED 2026-07-07, commit `1894c7b` — rebased
over the naming PR post-lock, content-identical; rule-12 double pressure-tested at design time; no data
existed at lock). **Generation:** Sparky/GX10, 2026-07-07, **five fresh same-epoch caches**
(`frame_single_20260707_091120`, `frame_filler_20260707_113512`, `frame_team_20260707_141046`,
`frame_outofblock_20260707_164728`, `frame_triple_20260707_191452`), 16 models × 5 arms × 78, temp=0,
zero retries; launcher machine-asserted T1@378 in all five arms + per-arm byte bounds on the host;
preamble hashes verified byte-identical cross-machine pre-launch. **Judge:** locked A′ 5-vendor panel,
one session, **$25.72** (single $2.14 / filler $7.12 / team $6.84 / outofblock $2.07 / triple $7.55).
**Analysis:** `tools/frame_analyze.py … --arm mech --per-facet --sp-expansion-bank` (deterministic, seed
0). **Results-stage discipline:** verdict-blind data audit BEFORE analysis (78/78 completeness all arms;
zero analyzer-INVALID; 5 healthy vendors; ABSENT fractions match the prior epochs to ±0.001; contamination
floors clean); §7b manual model-cluster/drop-top-k robustness computed; TWO adversarial reviewers
(statistical + methodological) audited the data→claims chain BEFORE this document was written — all
MUST_FIX amendments are folded below (both verdicts: PUBLISHABLE-AFTER-FIXES).

## Headline — the subject slot is causal but does not fence; the persona block absorbs third-party-subject facts too

**PRIMARY-A (the run's one confirmatory test) fired SUBJECT-SLOT-CAUSAL on the mech-11:** rendering the
same two planted dependency gists under `the platform-team` (+ its pronoun) instead of `P` reduces their
A′ self-attribution — D_subj = **+0.025**, 95% CI [+0.005, +0.046], one-sided facet-bootstrap LB95 =
+0.008 > 0 (the pre-registered rule; **disclosed calibrated type-I ≈ 0.07, not 0.05, and the margin is
thin** — this is confirmatory-by-preregistration, not a clean 5% result). The reduction is **small**
(~23% relative, below the pre-registered ≥0.05 practical-magnitude label) and the treatment is the
disclosed **de-attribution bundle** (subject string + pronoun + named-entity salience, +36B; §7c).

**And the pre-named complementary cell fired too — CROSS-ENTITY-LEAK:** third-party-attributed tokens
still enter the first-person channel at **0.085** pooled (cobalt_runtime 0.105 / mesa_framework 0.065).
Qualitatively (94 breach rows read by the methodological reviewer; register shares are rough string-match
indicators, not locked measurements): **83% of leaking responses retain the explicit third-party
attribution** — the dominant register is claimed *expertise-with* or *contribution-to* the platform-team's
artifacts ("I have a strong understanding of the cobalt_runtime …, as they are crucial components for
**the platform-team's** services"), with a ~27% minority of genuine contribution-appropriation ("I have
implemented features related to … cobalt_runtime"). De-attribution **reduces but does not fence** —
anchored on leak > 0, which is robust under both facet and model clustering.

Both length verdicts on the decision cell are **WITHHELD by their validity gates, as the power table
predicted for this regime** (observed ~23% reduction ⇒ P(GT pass) ≈ 0.00): the leak itself de-certifies
the team arm as a length control (GT), and the out-of-block episodics were echoed (GO, 0.156 — the
padding run's genre-echo, reproduced on the production `<memory:recent>` path).

## Gates

| gate | mech-11 (decision cell) | distill (descriptive, 5 models) |
|---|---|---|
| G1 recall control (≤0.05, all arms) | 0.006 / 0.011 / 0.006 / 0.017 / 0.000 — **PASS** | 0.025 / 0.000 / 0.000 / 0.013 / 0.025 — **PASS** |
| G2 replication (fresh single T1, 7f) | 0.169 vs anchor 0.182 (±0.10) — **PASS** | 0.129 — **PASS** |
| G4 identical open-SP facet sets | 25/25 ×5 — **PASS** | **PASS** |
| GT team-token adoption ≤0.05/token (certifies PRIMARY-B) | cobalt **0.105** / mesa **0.065** — **FAIL — cross-entity adoption** (organic floor 0.000/0.000, gate valid) | 0.020 / 0.012 — **PASS** |
| GO out-of-block echo ≤0.05 (certifies SECONDARY) | **0.156** on 550 — **FAIL** (single-arm floor 0.000, gate valid) | 0.048 on 250 — **PASS (knife-edge: 12/250; one more echo = FAIL)** |
| GF filler-leg adoptability ≥0.05 (licenses de-attribution language) | P-leg 0.110, LB95 +0.082 — **PASS** | 0.048 — **FAIL — P-leg at floor** |

## MEASURED (pre-specified; reported as found)

1. **PRIMARY-A, mech (confirmatory):** adopt(P-leg) = 0.110, adopt(team-leg) = 0.085, D_subj = +0.025
   [+0.005, +0.046], LB95(one-sided) = +0.008 → **SUBJECT-SLOT-CAUSAL** under the locked rule (with the
   type-I ≈0.07 calibration disclosed above). Robustness (§7b, manual): LOO all-positive (+0.02…+0.03);
   model-cluster bootstrap LB95 = +0.009; drop-top-k **sign holds through k=4** (+0.020/+0.014/+0.011/
   +0.009) though the facet-LB crosses 0 at k=2; one model (granite-3.2-8b) is negative (−0.04). Small,
   real, fragile in magnitude — not fence-grade.
2. **CROSS-ENTITY-LEAK, mech (pre-named descriptive; 0.05 = reporting threshold, not alpha):**
   adopt(team) = 0.085; facet-clustered LB95 = +0.063 (flag fires); **model-clustered LB95 = +0.045 (flag
   does not fire)** — the ≥0.05 flag is a facet-clustered reporting flag, **model-concentrated**
   (granite-3.3-2b adopts team facts at 0.36 and supplies ~⅓ of the leak; drop-top-1 → 0.058, drop-top-2
   → 0.050). Leak **> 0** holds under both clusterings — that is the load-bearing fact. Distill: 0.016,
   below threshold under both.
3. **PRIMARY-B (certified in-block length), mech: WITHHELD** — GT failed; the arm is not a certified
   length control (the pre-named leak↔certification trade). Distill (GT passed): TOST **INCONCLUSIVE**
   (Δ = −0.016, CI [−0.068, +0.036] straddles M = 0.037 — not evidence of a length effect).
4. **SECONDARY (total-context length via `<memory:recent>`), mech: WITHHELD** — GO failed (echo 0.156,
   floor 0.000). Distill (GO passed at 12/250 = 0.048): **LENGTH-CLEAN, knife-edge** — Δ = −0.000, 90% CI
   [−0.032, +0.032] inside ±M = ±0.037 (clears the margin by ~0.005/side; one more echo response would
   have withheld it). The run's only gate-passing length reading: **out-of-block/total-context, distill
   cell only** — it does not generalize to in-block length.
5. **Filler-adoption replication (pre-registered EXPECTED-FAIL):** 0.138 / 0.082 vs the filler epoch's
   0.133 / 0.084 — inside the ±0.10/token band. P-subject dependency gists are still adopted; filler G3
   replicates across epochs.
6. **Multiplicity carrier, 4th epoch (mech, 7f basis):** 28/154 = **0.182** — the fourth consecutive
   epoch whose integer counts round to 0.182 (0.182/0.182/0.182/0.182; "exactly" overstates — these are
   counts rounding to 3 decimals). 25f basis: 0.198, LB95 +0.142. **Mech-only:** distill 7f = 0.143.

## FLAGGED OBSERVATIONS (descriptive; nothing here is stamped)

- **Team-arm T1 tops the ladder** (single 0.196 / filler 0.213 / **team 0.236** / outofblock 0.156 /
  triple 0.202) — consistent with the series' **additive co-adoption** (filler is also elevated; team −
  filler = 0.023, within noise), on a WITHHELD primary whose descriptive CI straddles 0 (+0.040
  [−0.002, +0.082]), with the **opposite sign on distill** (0.096 < 0.112). No de-attribution-specific
  effect on the remaining P-fact is claimed; the series' no-competition result stands.
- **Mech out-of-block descriptive is negative** (Δ = −0.040 [−0.075, −0.007]) on a GO-failed cell —
  exploratory. Echo correlates with *higher* T1 (padding co-adoption), which pushes Δ up, so the negative
  is not a naive echo artifact — but the cells disagree (distill certified ≈0): heterogeneity, not a
  suppression claim.
- **Bounded composite (triple − team) is sign-discordant across cells** (mech −0.035 [−0.080, +0.005];
  distill +0.060 [+0.012, +0.108]) and carries the +30B pair-purity caveat — non-decision; no ordering
  between de-attributed gists and additional achievements is asserted.
- **Distill PRIMARY-A is directionally positive (+0.032, LB +0.016) but is NOT a licensed replication of
  de-attribution:** GF failed there (P-leg 0.048 — at floor), the difference is between two near-floor
  rates (0.048 → 0.016), and it collapses under model-drop (drop-top-2 → +0.010; drop-top-3 sign-flips
  to 0.000; 5 clusters). Direction agreement recorded; nothing stronger.
- **Analyzer cosmetic gap (known, disclosed):** `frame_analyze.py` GF-gates PRIMARY-B's language but not
  PRIMARY-A's verdict string, so the distill printout says "de-attribution works" where the locked GF
  interlock forbids it. **The interlock overrides the print**: de-attribution language is licensed for
  the mech cell only. (Wiring GF into the PRIMARY-A string is a post-lock analyzer fix; the decision
  logic is unaffected.)

## Reproducibility ledgers (same estimand, same facet basis, independent generation+judge epochs)

| quantity (mech-11) | multifact | filler | padding | **frame** |
|---|---|---|---|---|
| fresh single T1 (`REPRO_FACETS`, 7f) | 0.182 | 0.169 | 0.182 | **0.169** |
| fresh triple multiplicity (7f) | 0.182 | 0.182 | 0.182 | **0.182** |
| fresh triple multiplicity (25f) | — | 0.198 | 0.196 | **0.198** |
| filler-token adoption (cobalt/mesa) | — | 0.133 / 0.084 | — | **0.138 / 0.082** |

Four epochs, four days, one judge instrument: the multiplicity carrier keeps landing on 0.182 (7f) and
the singles ledger alternates within its ±0.10 gate band. The generate→judge→score path is stable; the
framing verdict's carrier keeps confirming.

## NOT assertable

- **"De-attribution works (fence-grade)"** — not asserted. The measured reduction is +0.025 (~23%
  relative), sub-practical by the pre-registered ≥0.05 label, magnitude-fragile (facet-LB < 0 at
  drop-top-2), and the residual first-person channel is 0.085. The honest verb: *reduces, does not fence*.
- **"The Hermes-seed hazard is quantified"** — not asserted. This run provides a **first render-surface
  estimate (0.085 on this scaffold)** of the cross-entity contamination a seed-import could create —
  bounded to one subject string, two coined tokens, dependency relations, the minority MCP/import render
  path (§7g), no live importer, no identity anchor. It characterizes the failure **class** the
  Hermes-seed incident exemplifies, not that incident.
- **Any in-block length verdict** — GT-failed on mech, INCONCLUSIVE on distill. The in-block length
  question remains formally OPEN (and, per PADDING_RESULTS, structurally unidentifiable at the per-token
  in-block channel: the identifying cell keeps failing to exist because added block content is added
  attributable content — this run's GT-fail is that wall again, now via cross-entity adoption).
- **Block-level frame effects** — not varied (the persona-block header was held constant across the
  minimal pair by design); nothing block-level is claimed from PRIMARY-A.
- **Mature-store generalization** — the recent block renders only while gists < 5 (§7f); cold-start
  coupling disclosed.

## Architecture significance (CDMS-D world-fence)

Filler showed hygiene cannot triage by content **type**; padding showed the hazard is the attribution
**frame**, not citability. FRAME now shows the frame's line-level lever is **weak**: changing the
subject slot of an imported fact (the thing importer hygiene can actually do per-line) buys a ~23%
reduction and leaves an 0.085 first-person channel — predominantly expertise/contribution claims that
*keep* the third-party label while bolting on self-competence. **Changing an imported fact's subject
slot is insufficient as a fence.** The persona block must be treated **wholesale** as
non-assistant-attributable; the implied fence lever is **block-level** (a separate non-self block /
different header), which this run motivates but did not test. The load-bearing boundary is unchanged:
G1 recall stayed ≤0.017 in all ten cells — this is a rendering/list-mode statement, not a recall-channel
one. The distill contrast (no leak, 0.016) also suggests the leak is model-dependent — fence design
should not assume the best-behaved model.

## What this run licenses next

- **Licensed:** a block-level frame manipulation (separate third-party block / non-self header vs the
  persona block, same facts) — the direct test of the lever this run showed is the operative one.
- **Low-value now:** further line-level subject-slot variants (the lever is measured weak); a fifth
  in-block length control (the identifying cell keeps self-destructing — three designs + this GT-fail).
- **Unchanged:** the controlled-FT frontier arm remains the falsifiable length/identity question if one
  is worth resources (per PADDING_RESULTS §recommendation).

## Data + reproduction

- `gen_sweep/frame_single_JUDGE.jsonl`, `frame_filler_JUDGE.jsonl`, `frame_team_JUDGE.jsonl`,
  `frame_outofblock_JUDGE.jsonl`, `frame_triple_JUDGE.jsonl` (committed).
- `python tools/frame_analyze.py gen_sweep/frame_single_JUDGE.jsonl gen_sweep/frame_filler_JUDGE.jsonl
  gen_sweep/frame_team_JUDGE.jsonl gen_sweep/frame_outofblock_JUDGE.jsonl gen_sweep/frame_triple_JUDGE.jsonl
  --arm mech --per-facet --sp-expansion-bank` (deterministic, seed 0). Distill: `--arm distill
  --allow-incomplete`.
- Scaffolds `setup_bem_team` / `setup_bem_outofblock` + `TEAM_SUBJECT`/`TEAM_GISTS`/`OFB_EVENTS`/
  `OFB_PHRASES` (locked, `tests/test_frame.py`, incl. pronoun-purity assert); bank
  `tools/probes_sp_expansion.py`; power sim `frame/power_sim.py`. Caches off-repo (Sparky).
- §7b manual robustness (model-cluster bootstrap + drop-top-k, both cells) — script preserved in the
  session scratchpad; all numbers reported above.

## Pressure-test outcome vs prediction

The design promised **no wasted cell**, and that held: the null-adjacent outcome (partial reduction)
landed in the pre-named CAUSAL + LEAK cell, and both gate-withholdings were the power table's predicted
behavior for this regime (P(GT pass) = 0.00 at ≤30% reduction), not design failures. The §7a
echo-conservativity argument held again at the fourth epoch (echo co-adoption pushes Δ up; it cannot
manufacture the distill LENGTH-CLEAN, and it argues against the mech negative being an artifact). The
results-stage discipline earned its keep a third time: the verdict-blind audit found a clean pipeline
(ABSENT drift ±0.001 across epochs), and the two-reviewer pass produced one required calibration
disclosure (type-I ≈0.07 inline with "confirmatory"), the 83%-retention texture that reshaped the leak
claim from "self-claimed" to "expertise/contribution claims," the model-concentration of the leak flag,
the knife-edge disclosure on the distill LENGTH-CLEAN, and the kill of a "de-attributed gists raise T1"
over-read — all before any claim entered this document.
