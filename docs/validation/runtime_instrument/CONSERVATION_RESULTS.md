# Multiplicity-conservation ladder — results

**Pre-registration:** [`CONSERVATION_PREREG.md`](CONSERVATION_PREREG.md) (LOCKED 2026-07-08, commit
`d01da5c`, rule-12 double pressure-tested at design time; band + sequencing enforced by artifacts).
**P0 (before generation):** fresh-session re-judge of the committed frame caches ($9.60) → σ_multiplicity
= 0.0000 across 5 sessions, **band M = 0.0610 (the I6-convention floor binds — the band is
convention-floored at p_anchor/3 ≈ ±34% relative, not meaningfully "instrument-calibrated"; halt=false)**;
artifact `conservation/P0_BAND.json`. **Generation:** Sparky/GX10, 2026-07-08→09, **six fresh caches**
(p2 paraphrase 60/model; p1 seeds 11/12/13 @ temp 0.7; p3 renamed; p4 permuted — 78/model each), zero
retries, per-arm completeness asserted, **determinism sentinel OK 156/156** (the paired anchor is valid
in the run's environment, verified not assumed). **Judge:** locked A′ panel, $43.66; **P0b novel-text
spot-check CLEAR** (3/100 flips vs P0's 3.5% — P1 rows only; the P2 bank's judge reliability was NOT
separately spot-checked, a disclosed gap). **Analysis:** `tools/conservation_analyze.py --band-file
conservation/P0_BAND.json` (deterministic, seed 0; the confirmatory run used the artifact path, verified
reproducible by the reviewers). **Results-stage discipline:** verdict-blind audit BEFORE analysis (PASS;
one dispositioned flag, see FLAGGED); TWO adversarial reviewers BEFORE interpretation (both
PUBLISHABLE-AFTER-FIXES; both MUST_FIXes + all SHOULD_FIXes folded below — including one that killed a
drafted claim outright).

## Headline — NOT ESTABLISHED: the wording axis is OPEN with no pre-registered remedy; nothing BROKE

The pre-registered headline ("stable operating point (bounded)") required P1 AND P2 CONSERVED. The
realized cell is **P1 CONSERVED (marginal, see below) + P2 INCONCLUSIVE + P3 INCONCLUSIVE — zero BROKEN
arms**. Per the locked outcome→follow-on matrix, an INCONCLUSIVE-driven NOT-ESTABLISHED is an
**evidential null**: conservation was not refuted on any axis, the wording axis could not be certified
at this power/width, and the single pre-registered extension (P1 seeds {14,15}) does not apply (P1 was
not the INCONCLUSIVE arm) — **the wording question stays OPEN at this cost tier; certifying it is a new
pre-registration.**

The answer to the motivating question ("isn't 0.182×4 an invariant?"), assembled honestly:
- the **exact** streak was settled *before* this run: temp-0 generation is byte-deterministic
  (FRAME ledger amendment) — the streak is a pipeline canary, not behavioral replication;
- under real perturbation the carrier **moves**: at temp 0.7 it is **seed-variable (0.136–0.188,
  between-seed SD 0.028)** with a **statistically resolved small downward shift** (pooled 0.1558,
  D = −0.026, 90% CI [−0.0563, −0.0022] — excludes 0) that nonetheless sits inside the ±0.061 band →
  **equivalent-within-±34%, not invariant**;
- one axis certifies that bounded equivalence (decode-path), two axes are unresolved (wording, lexical),
  and none broke. "0.182 is a constant of the system" is dead; "the carrier stays within ~±1/3 of its
  anchor under decode-path perturbation" is the certified replacement.

## Per-arm verdicts (mech-11, band ±0.0610, paired facet bootstrap vs the committed frame-epoch anchor)

| arm | fw | D vs anchor 0.1818 | 90% CI | verdict |
|---|---|---|---|---|
| **P1 decode-path (temp 0.7 × seeds {11,12,13} pooled)** | 0.1558 | −0.0260 | [−0.0563, −0.0022] | **CONSERVED — marginal** (LB 0.0047 inside the band edge; CI excludes 0 = the pre-registered significant-but-small equivalence case; LOFO: dropping cs-A2 flips to INCONCLUSIVE — profile-fragile; 7-cluster bootstrap pre-disclosed anti-conservative) |
| **P2 paraphrase (parallel forms)** | 0.1526 | −0.0292 | [−0.1331, +0.0584] | **INCONCLUSIVE** — evidential null, NOT a refutation; see the reshuffle below |
| **P3 token-renamed** | 0.1623 | −0.0195 | [−0.0714, +0.0260] | **INCONCLUSIVE** |
| **P4 tie-order permuted** | 0.1883 | +0.0065 | [−0.0260, +0.0455] | **MAP (no verdict by design)** — the documented risk axis produced ≈ nothing |

Gates: G1 recall PASS all mech arms (≤0.006); G-FLOOR (p3 contamination) PASS 0; G-SEED/G-FACET PASS;
**M4 length/truncation parity: NO qualifier** (mech mean length +1.2–1.4% vs anchor, truncation-proxy
gaps ≤2.3pp — temp 0.7 did not move verbosity materially). Directional note: three of four mech point
estimates sit below the anchor — reported as description only (the arms share one fixed anchor, so
their signs are correlated, and P1's own offset is noise-dominated per the pre-registered S4
disambiguator: between-seed SD 0.028 ≳ pooled offset 0.026); no joint sign test is licensed.

## MEASURED (pre-specified; reported as found)

1. **P1 (confirmatory): decode-path CONSERVED, with texture that must lead:** at temperature the
   carrier finally moves — per-seed 0.1883 / 0.1429 / 0.1364 — and lands slightly but resolvably below
   the anchor. **Decode noise, not judge noise, is the binding variance source** (between-seed SD 0.028
   vs σ_multiplicity = 0.0000 on identical text; the prereg's σ_T1 comparison is dropped as
   cross-estimand per review). A reader should hear "bounded, not frozen."
2. **P2: the new bank RESHUFFLES the facet profile at near-constant mean** — cs-A1 0.591→0.227,
   cs-A9 0.182→0.318, cs-A20 0.091→0.205 (verified exactly by both reviewers) — which inflates the
   paired-bootstrap CI and produces the straddle. Per the pre-registered disambiguator this pattern
   points at **facet×wording (bank-difficulty) interaction rather than a uniform wording effect**; an
   instrument-side alternative (the panel reading the novel bank differently) remains live — P0b did
   not cover P2 rows, and deepseek's p2 near-degeneracy is quantified under FLAGGED. **Wording
   conservation is NOT established** (the near-constant mean carries no verdict weight). Locked
   asymmetry: this is forward-only — no threat to prior-epoch comparability (all prior epochs shared
   byte-identical wordings). Fair summary sentence: *the 7f basis is wording-sensitive at facet level
   even where the mean is not.*
3. **P0/P0b (instrument):** σ_multiplicity = 0.0000 across five sessions on identical text; row-level
   flips 3.1–3.5%, concentrated in deepseek/mistral single votes (claude + gemini: zero), absorbed by
   the 3-vote consensus; novel-text reliability consistent (3/100, P1 rows).
4. **Per-token rates (pre-registered descriptive — CORRECTED per both reviewers' MUST_FIX):** the
   draft claim "the conditional attribution rate is lexically stable" was WRONG and is withdrawn: its
   numbers were per-token **marginal** rates (25-facet SP basis, ABSENT-inclusive) mislabeled as
   conditional, on a different basis from the 7f machinery, and its anchor triple contained a copy
   error. Corrected, definition-explicit values, position-ordered T1/T2/T3:
   - marginal (25f, ABSENT-inclusive): anchor 0.202/0.211/0.182 · renamed 0.202/0.191/0.189 ·
     permuted 0.191/0.211/0.205;
   - conditional breach|present (reviewer-computed): anchor **0.199/0.253/0.266 (rising)** vs renamed
     ≈0.206/0.190/0.190 (**flat**) — i.e. under the conditional definition the rename *changes the
     positional profile*; and under wording (P2) the marginal moves ~0.04 (≈2× the drafted "±0.02").
   **No per-token conservation claim is made**; the quantity is definition- and axis-sensitive. A
   same-basis, definition-locked per-token conservation question would need its own pre-registration.

## FLAGGED OBSERVATIONS (descriptive; nothing here is stamped)

- **Distill recall-gate first breaches (small-n, model-concentrated, NOT temperature-clean):** 2 of 4
  distill arms exceed the 0.05 recall gate by point estimate — P1 6/80 = 0.075 (Wilson 95%
  [0.035, 0.154]) and **P4 5/80 = 0.0625 [0.027, 0.138] at temp ZERO** — both CIs include the gate, and
  P3 (0.0375, CI to 0.105) is statistically indistinguishable from them. The breaching responses are
  genuine first-person ownership on recall probes and are **concentrated in one model,
  claude-mythos-q8** (the RP-flavored Claude distill), across both a temp-0.7 and a temp-0 arm; mech
  held ≤0.006 everywhere. Registered **OPEN**: distill-model-specific recall fragility under
  perturbation — a follow-on must vary MODEL and temperature jointly; "temperature erodes the
  firewall" is NOT the licensed reading (self-contradicted by the temp-0 breach).
- **Distill perturbation sensitivity (n=5, descriptive):** P2 0.064 / P3 0.057 vs the distill anchor
  0.143 — BROKEN(−) under the rule but extremely LOFO-fragile (P2 flips to INCONCLUSIVE under any of
  five facet drops); mech and distill cells disagree in degree, consistent with the series' pattern.
- **deepseek near-degeneracy in p2 (audit flag, dispositioned quantitatively):** 96.1% one-label in p2
  vs its 0.90–0.91 baseline elsewhere (still emitting all four labels — not mechanically stuck). A
  **post-hoc robustness check** (mislabeled "pre-committed" in the draft; corrected per review):
  excluding deepseek moves P2 to fw 0.1591 / D −0.023 (~0.007 of the shortfall) and leaves P1
  CONSERVED (D −0.024), P2 INCONCLUSIVE, and the reshuffle intact — no verdict depends on deepseek.
  Mild instrument asymmetry (the anchor's deepseek was not degenerate) noted.
- **Power-sim promise not met on P2 (structural, disclosed):** §6 promised P(CONSERVED)=0.85; the sim
  modeled a uniform multiplicative shift on the anchor's facet profile, while reality redistributed
  multiplicity across facets at near-constant mean — the paired-bootstrap CI inflates under reshuffle.
  The INCONCLUSIVE is therefore partly structural (facet×wording interaction), not raw-n; future
  parallel-forms banks need more facets or a reshuffle-robust design.

## NOT assertable

- **"Stable operating point"** — not asserted (headline NOT ESTABLISHED; wording axis OPEN).
- **"0.182 is an invariant"** — dead twice over: the exact streak is temp-0 determinism, and at
  temp 0.7 the carrier is seed-variable (0.136–0.188). What IS certified: bounded equivalence within
  ±34% on the decode-path axis, marginal and profile-fragile as disclosed.
- **"Wording/lexical conservation"** — INCONCLUSIVE both; evidential nulls.
- **Any per-token conservation claim** — withdrawn (MEASURED #4).
- **"Temperature erodes the distill recall firewall"** — not licensed (temp-0 breach; CIs include the
  gate; one-model concentration).

## Ledger / canary going forward

| quantity | value | status |
|---|---|---|
| fresh-triple multiplicity, 7f mech, temp-0 (pipeline canary) | **0.182** (byte-deterministic; 5 judge sessions σ=0.0000) | unchanged canary |
| temp-0.7 seed band (P1) | **0.136–0.188** (pooled 0.156; CONSERVED-marginal, shift −0.026) | new |
| wording arm (P2) | 0.153, INCONCLUSIVE (facet reshuffle) | OPEN |
| token-renamed arm (P3) | 0.162, INCONCLUSIVE | OPEN |
| tie-order arm (P4, map) | 0.188 (Δ ≈ +0.007) | map point |
| distill recall first-breach | claude-mythos-q8-concentrated, 0.038–0.075 across arms | **registered OPEN** |

## What this licenses next (per the locked matrix)

- The realized cell (P1 CONSERVED ∧ P2/P3 INCONCLUSIVE) → the conservation question **stays OPEN at
  this cost tier**; a certified wording axis needs a NEW pre-registration (more facets / a
  reshuffle-robust paired design — see the power-sim reconciliation).
- The temp-0 canary (0.182) remains valid and cheap; the block-level frame manipulation (FRAME
  follow-on) is unaffected and proceeds on a carrier now characterized under perturbation.
- The distill recall observation feeds a joint model×temperature recall-channel arm if pursued —
  it touches the program's core G1 boundary and is the highest-signal open item this run produced.

## Data + reproduction

- `gen_sweep/cons_p2_JUDGE.jsonl`, `cons_p1_s11/12/13_JUDGE.jsonl`, `cons_p3_JUDGE.jsonl`,
  `cons_p4_JUDGE.jsonl` + P0 retests (`frame_single_RETEST_JUDGE.jsonl`,
  `frame_triple_RETEST_JUDGE.jsonl`) + `conservation/P0_BAND.json` (committed).
- `python tools/conservation_analyze.py --anchor gen_sweep/frame_triple_JUDGE.jsonl --p1
  gen_sweep/cons_p1_s11_JUDGE.jsonl gen_sweep/cons_p1_s12_JUDGE.jsonl gen_sweep/cons_p1_s13_JUDGE.jsonl
  --p2 gen_sweep/cons_p2_JUDGE.jsonl --p3 gen_sweep/cons_p3_JUDGE.jsonl --p4 gen_sweep/cons_p4_JUDGE.jsonl
  --band-file conservation/P0_BAND.json --arm mech` (deterministic, seed 0; distill: `--arm distill
  --allow-incomplete`, distill-only as locked).
- Costs: P0 $9.60 + arms $43.66 + P0b $0.31 = **$53.57** (vs ≈$54 pre-registered); Sparky ~15 h incl.
  sentinel; zero generation failures.

## Pressure-test outcome vs prediction

The design's guards all fired or held as built: the determinism sentinel validated the paired anchor in
the run's environment (156/156); the band floor bound exactly as predicted (σ_m = 0.0000); M4 parity
came in far under its flags; P0b cleared. The §6 power table was RIGHT for P1 (0.95 promised; a clean
verdict delivered) and **wrong-for-a-disclosed-reason on P2** (uniform-shift assumption vs realized
reshuffle — recorded above as a structural lesson for parallel-forms designs). The results-stage
discipline caught real errors a fourth consecutive time: both reviewers independently killed the
drafted per-token "conditional stability" claim (mislabeled marginal, cross-basis, anchor copy error —
the corrected conditional profile suggests the *opposite*), and both caught the distill-recall
temperature misattribution (the breach reproduces at temp 0, in one model). What survived — every
locked verdict, byte-for-byte, under independent recomputation including a deepseek-excluded
re-consensus.
