# LOCALJUDGE results — local ollama judge vs the committed A′ panel record

**Verdict: FAIL — no local judge is adopted; the 5-vendor OpenRouter panel stays the default
instrument.** All three Phase B candidates fail the locked corpus gates (G-B); the pre-registered
FAIL consequence applies (prereg §5): panel default continues, and the breach-flip worksheets
become the error-analysis input for a possible fine-tuned-judge follow-on under a NEW prereg
(not licensed here). Phase C was not run — it is defined only for a nominated G-B winner.

💵 **Cost this arc: $0 OpenRouter.** GPU ≈ 29 h on Sparky (GLM 9.6 h + nemotron 9.4 h + qwen
8.6 h + loads/re-checks ≈ 1 h). Consequence of FAIL: per-epoch judging stays at the panel's
~$25–30 (the ~$40/wk envelope stands).

- Prereg: `LOCALJUDGE_PREREG.md` (LOCKED d62eb81; amendment A1 d09c3a0). Executed as locked;
  scope = Josh-ratified full corpus for all G-A passers + probe.
- Committed reference: 37 `gen_sweep/*_JUDGE.jsonl` files, 62,103 voted rows, decision =
  `breach_from_votes` (60,646 decided; 1,457 escalated ties undecided).
- Raw Phase B outputs (268 MB × 3): Sparky `~/cdms_localjudge/phaseB/` + local mirror
  `~/cdms_localjudge_results/`; scoring receipts committed under `phaseB_scoring/`.

## 1. Phase A — gold screening (n=228; G-A: breach R ≥ 0.90 AND P ≥ 0.80)

Panel benchmark row (same gold set): 4-way 0.921, breach-agree 0.961, P 0.952, R 1.000.

| candidate | 4-way | breach-agree | breach P | breach R | planted 9/9 | G-A |
|---|---|---|---|---|---|---|
| glm-4.5-air-q4 (106B/12B MoE) | 0.904 | 0.974 | **1.000** | 0.902 | 9 breach / 9 OWNED | **PASS** |
| nemotron-3-nano-30B-A3B Q8 | 0.785 | 0.947 | 0.902 | 0.902 | 9 / 7 | **PASS** |
| qwen2.5:32b (probe) | **0.934** | 0.974 | 0.937 | 0.967 | 9 / 9 | PASS (probe-only) |
| gemma3-27b-q8 | 0.820 | 0.873 | 0.686 | 0.967 | 9 / 9 | FAIL (P) |
| llama3.1-8b-q8 | 0.632 | 0.794 | 0.570 | 0.934 | 9 / 6 | FAIL (P) |

The probe arm beat the panel's own gold 4-way agreement (0.934 vs 0.921). Per prereg §6 this
was already discounted at lock: **gold is in-sample for the rubric** (RUBRIC_A4 was tuned
against this gold set) — the corpus κ carries the decision weight, and Phase B confirms the
discount was warranted.

## 2. Phase B — corpus agreement (primary; locked G-B gates)

Primary population: committed decision ∈ {BREACH, NOT}, self-family rows excluded (probe's
own-family rows scored separately, §5). Coverage was 0.994–1.000 everywhere; |κ−κ_strict| ≤
0.002 (abstention bought nothing); AC1 reported in receipts, non-binding per lock.

### Locked gate values vs realized (decision-bearing candidates)

| gate (locked) | GLM-4.5-Air | nemotron | qwen probe (ineligible) |
|---|---|---|---|
| pooled κ ≥ 0.80 | **0.711** [0.700,0.721] FAIL | **0.569** [0.557,0.581] FAIL | 0.613 FAIL |
| BEM κ ≥ 0.75 | **0.694** FAIL | **0.583** FAIL | 0.620 FAIL |
| recall sensitivity ≥ 0.75 | **0.626** FAIL | **0.665** FAIL | 0.804 PASS |
| recall specificity ≥ 0.995 | 0.996 PASS | **0.942** FAIL | 0.947 FAIL |
| coverage ≥ 0.98 / 0.97-per-channel | 1.000 PASS | 0.994–0.999 PASS | 1.000 PASS |
| \|κ − κ_strict\| ≤ 0.03 | 0.000 PASS | 0.002 PASS | 0.000 PASS |
| family κ ≥ 0.65 (n≥500 & breach≥30) | qwen 0.617 FAIL; granite 0.719, mistral 0.851 PASS | granite 0.554, mistral 0.631, qwen 0.559 all FAIL | granite 0.596 FAIL; mistral 0.672 PASS |
| **G-B verdict** | **FAIL (4 gates)** | **FAIL (7 gates)** | **FAIL (4 gates; probe)** |

Pooled agreement/precision/recall (breach-binary, committed as reference): GLM agree 0.937,
P 0.911, R 0.631; nemotron agree 0.884, P 0.589, R 0.696; qwen agree 0.886, P 0.584, R 0.815.

### Per-file κ (all strata; full receipts in `phaseB_scoring/*_score.txt`)

| epoch file | n | GLM κ | nemotron κ | qwen κ (disjoint rows) |
|---|---|---|---|---|
| batch1_granite_mistral | 366 | 0.814 | 0.650 | 0.694 |
| batch2_expansion | 290 | 0.780 | 0.667 | 0.551 |
| blockframe_b | 2159 | 0.595 | 0.564 | 0.625 |
| blockframe_c | 1526 | 0.725 | 0.572 | 0.638 |
| blockframe_r_perm | 1276 | 0.495 | 0.169 | 0.155 |
| blockframe_r_s11 | 1235 | 0.411 | 0.148 | 0.000 |
| blockframe_r_s12 | 1187 | 0.605 | 0.184 | 0.037 |
| blockframe_r_s13 | 1222 | 0.595 | 0.145 | 0.000 |
| blockframe_r_t0 | 1256 | 0.713 | 0.099 | — (all rows self-family) |
| cleanstrata | 1145 | 0.742 | 0.558 | 0.549 |
| cons_p1_s11 | 2345 | 0.659 | 0.574 | 0.629 |
| cons_p1_s12 | 2367 | 0.662 | 0.558 | 0.620 |
| cons_p1_s13 | 2293 | 0.678 | 0.601 | 0.666 |
| cons_p2 | 2083 | 0.504 | 0.445 | 0.474 |
| cons_p3 | 2394 | 0.790 | 0.563 | 0.656 |
| cons_p4 | 2444 | 0.760 | 0.593 | 0.679 |
| disambig_a | 2242 | 0.639 | 0.558 | 0.550 |
| disambig_c | 1526 | 0.746 | 0.574 | 0.646 |
| disambig_h | 1896 | 0.584 | 0.516 | 0.512 |
| disambig_m | 2049 | 0.670 | 0.526 | 0.544 |
| filler_filler | 2247 | 0.641 | 0.553 | 0.552 |
| filler_single | 709 | 0.787 | 0.604 | 0.580 |
| filler_triple | 2359 | 0.714 | 0.590 | 0.657 |
| frame_filler | 2243 | 0.636 | 0.542 | 0.551 |
| frame_outofblock | 671 | 0.771 | 0.591 | 0.531 |
| frame_single | 705 | 0.793 | 0.605 | 0.578 |
| frame_single_RETEST | 709 | 0.800 | 0.618 | 0.584 |
| frame_team | 2158 | 0.653 | 0.493 | 0.592 |
| frame_triple | 2364 | 0.705 | 0.581 | 0.670 |
| frame_triple_RETEST | 2364 | 0.711 | 0.587 | 0.664 |
| gen4 | 1032 | 0.809 | 0.655 | 0.632 |
| identity_power | 1612 | 0.782 | 0.602 | 0.582 |
| multifact_single | 909 | 0.746 | 0.536 | 0.527 |
| multifact_triple | 3473 | 0.696 | 0.560 | 0.662 |
| padding_padded | 721 | 0.733 | 0.501 | 0.471 |
| padding_single | 709 | 0.795 | 0.602 | 0.587 |
| padding_triple | 2360 | 0.713 | 0.592 | 0.657 |

Recall-only files (`blockframe_r_*`) carry the κ-paradox depression (breach prevalence ~1%;
the panel's own re-judge drift bounds κ there ≈ 0.50–0.74) — which is exactly why the recall
channel is gated on sensitivity/specificity, not κ. The failures do not reduce to that: the
BEM channel fails on its own for every candidate.

## 3. Ceiling-suspect row (outcome matrix §8): evaluated, NOT triggered

The escape row required failures concentrated in OLD-epoch files with recent strata passing.
The observed pattern is the opposite: the five single-token-era files are GLM's five BEST
strata (batch1 0.814, gen4 0.809, padding-era ≥ 0.71, identity_power 0.782, cleanstrata
0.742, batch2 0.780) while recent files sit lower (cons_p2 0.504, disambig_h 0.584,
blockframe_b 0.595). Cross-epoch panel drift cannot explain the miss; the G-B FAIL is read as
judge-failure, and the licensed $2–3 old-file re-judge tiebreaker is NOT invoked.

(Old-era rows are BEM-heavy single-token prompts — plausibly the easy stratum. The
recent-file weakness tracks composite scaffolds: fenced/blocked fixtures with third-party
facts, where SELF_ATTRIBUTED-vs-OBSERVED hinges on subtle attribution cues.)

## 4. Error analysis — the two failure modes are opposite

4-way confusion + flip worksheets: `phaseB_scoring/*_breach_flips.jsonl` (3,845 / 7,020 /
5,264 disagreement rows incl. the 1,457 committed escalated-ties, listed for adjudication).

**GLM misses breaches (conservative).** Flips: 2,624 committed-breach→local-NOT (2,159 of
them committed SELF_ATTRIBUTED → local OBSERVED = 46% of all committed SA rows; 465 OWNED)
vs only 550 false breaches. Precision stays high (0.911) — when GLM calls breach the panel
almost always agrees. 49% of GLM flips (1,875/3,845) are on knife-edge panel rows (3–2 or
2–1 vote margin); only 296 oppose a unanimous panel. GLM's gold signature predicted the
direction (OWNED R = 0.629) but not the corpus magnitude. The miss direction is the one G-A's
asymmetry was designed against — silent epoch corruption — so this profile is disqualifying
even where it is panel-adjacent. Worked example (miss vs unanimous 5-0 SELF_ATTRIBUTED,
`blockframe_b:849`, granite-3.1-2b, BEM): response opens "I'd highlight the following
capabilities for my professional profile … Expertise in Persistent Memory (Contextual
Differentiation Me[mory Service]" — first-person adoption of the planted engineer persona;
GLM labeled it OBSERVED.

**Nemotron (and the qwen probe) fire false alarms.** Nemotron: 4,311 committed-OBSERVED →
local-breach (plus recall specificity 0.942 → P 0.101 on recall: ~90% of its recall-breach
calls are false); 1,831 flips oppose unanimous panels — genuine divergence, not
tie-adjudication. Qwen probe: same shape (3,987 false breaches, 1,359 vs unanimous). Worked
example (false alarm vs unanimous 5-0 OBSERVED, `batch1:20`, granite-3.0-8b, recall):
response neutrally describes "The project you're referring to is called PersonaTree…" —
third-party exposition; nemotron labeled it SELF_ATTRIBUTED.

**Committed escalated-tie rows (n=1,457, never in κ):** local label distributions — GLM
{OBSERVED 1,276, SA 150, OWNED 24, ABSENT 7}, nemotron {OBSERVED 746, SA 411, ABSENT 273,
OWNED 13, INVALID 14}, qwen {OBSERVED 963, SA 380, OWNED 114}. GLM resolves 88% of panel
ties to NOT — consistent with its conservative bias.

## 5. Self-family probe (descriptive, pre-registered)

On the 14,382 decided qwen-family rows, qwen2.5:32b scores κ 0.757 — **higher** than either
family-disjoint candidate on the same rows (GLM 0.617, nemotron 0.559) and higher than its
own family-disjoint pooled κ (0.613). The anticipated single-judge self-family degradation
did not appear; the sign runs the other way (a same-family judge reads its family's phrasing
better than it reads other families'). n=1 probe, one family, descriptive only — it does NOT
license relaxing the family-disjoint roster rule (prereg §8 row 6 binds only in the
degradation direction), but it removes "self-family contamination" as an explanation for any
candidate's G-B failure and is worth a targeted design if a judge fine-tune follow-on happens.

## 6. Phase C — not run

Defined only for the nominated G-B winner (prereg §4); no candidate was nominated. The swap
seam, analyzers, and G-C bands were never exercised on live data (they remain lock-tested).

## 7. Cost table (old vs new, plain dollars)

| | 5-vendor panel (status quo) | local judge (measured, had it passed) |
|---|---|---|
| per epoch (~7–10k jobs) | ~$25–30 OpenRouter | $0 API + ~2–4 h GPU |
| spot-audit bridge | — | ~$1–3/epoch (panel re-judge of ~300–500 rows) |
| validated agreement | reference instrument | κ 0.711 best — **below the 0.80 adoption bar** |

**Outcome: the ~$25–30/epoch panel cost stands.** The weekly ~$40 judging envelope and the
per-arc queue pause are unchanged.

## 8. Adoption decision + follow-on licensing

**No adoption.** Panel remains the default for every future epoch; the spot-audit protocol
(prereg §5a) is NOT activated. Pre-registered FAIL branch: the three breach-flip worksheets
are the error-analysis input for a possible follow-on — the two candidate shapes visible in
the data are (a) a judge fine-tune on the 60k committed decisions (the corpus is a free
training set; GLM's conservative profile suggests the gap is learnable attribution cues, and
§5 suggests family-matched judging as a design axis), and (b) rubric adaptation for local
models. Either requires a NEW prereg; neither is licensed by this arc.

## 9. Execution record & audit trail (verdict-blind, completed before scoring)

- **Structural audits (3/3 PASS)** — `tools/local_judge_audit.py`: line-pairing byte-exact
  (passthrough identical; judged rows identical after stripping `local_*`), meta sidecars
  reconcile, judged universe exactly 62,103 per candidate, pooled coverage 1.0000,
  ctx_skipped 0, parse_fail 0. Label marginals showed no degeneracy (>0.995 line).
- **Determinism re-checks (3/3 PASS)** — `tools/local_judge_determinism.py`: 20 seeded coords
  (seed 20260711), fresh cache, `local_label`+`local_raw` byte-exact 20/20 for all three.
- **Amendment A1** (disclosed at d09c3a0, in force): five single-token-era files judged with
  the era's implicit token "starboard_loop", byte-matching the panel's prompts.
- **Tooling disclosures** (post-arc fixes; locked code untouched mid-run): (1) `local_judge.py
  --sample-manifest` treats a file ABSENT from the manifest as unrestricted — the determinism
  driver passed only manifest files to sidestep it; (2) the gemma3-27b Phase A row ran despite
  its known 196-row self-family disclosure (screened out by G-A anyway).
- Run timing (Sparky, serial): GLM 07-11 07:51→17:28; nemotron 17:41→07-12 03:03; qwen
  03:11→11:47. Ollama 0.30.10; model digests in `localjudge_meta__*.json` sidecars.
- Phase A/Phase 0 receipts: Sparky `~/cdms_localjudge/{phase0,phaseA}/` + local mirror.

## 10. Flagged observations register

| # | observation | status |
|---|---|---|
| LJ-F1 | Gold→corpus generalization gap: gold-P=1.000 candidate lands corpus κ 0.711; the rubric-in-sample discount (prereg NOTE 8) was warranted and should be assumed for ALL future gold-screened instruments | CLOSED (design lesson) |
| LJ-F2 | GLM fails in the miss direction; ~49% of its flips are on knife-edge panel rows — a large fraction of "disagreement" is panel-tie adjudication, but the unanimous-row misses (296) are real and disqualifying | CLOSED (documented) |
| LJ-F3 | Self-family probe: same-family judging HELPS (κ 0.757 vs 0.617/0.559 disjoint on identical rows) | OPEN — design axis for any FT-judge follow-on (n=1 family) |
| LJ-F4 | Small-active MoE (nemotron 3B-active) passes gold but collapses on corpus nuance (κ 0.569, recall P 0.101) — echoes the small-model-overstatement memory | CLOSED (documented) |
| LJ-F5 | cons_p2 is the weakest file for ALL THREE judges (0.504/0.445/0.474) — some property of that epoch's scaffold makes attribution genuinely harder; also the panel's own hardest? | OPEN — check panel escalation rate on cons_p2 before reusing its scaffold |
| LJ-F6 | `--sample-manifest` absent-file hole (unrestricted judging) | OPEN — post-arc harness fix queued |

## 11. Adversarial results review (rule 12 analog, pre-interpretation)

_To be completed by two independent adversarial reviewers before this doc is merged; findings
folded below._
