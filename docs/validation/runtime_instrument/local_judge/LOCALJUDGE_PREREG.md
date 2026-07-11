# LOCALJUDGE pre-registration — can a local judge replace the A′ panel? [LOCKED 2026-07-11]

**Lock record:** double pressure test folded (§7); Phase-B scope ratified by Josh 2026-07-11:
**FULL corpus for every G-A passer AND the probe arm** (completeness over GPU-thrift — his call,
plain-hours quoted: ~70 h ≈ 3 GPU-days serial if all pass). The committed manifest stays pinned
as the fallback artifact only. 17 lock tests green at lock.

**💵 Cost header:** OpenRouter spend this arc = **$0** (the validation set is the committed record;
no generation, no panel calls). Resource = Sparky GPU-time, MEASURED (Phase 0, 2026-07-11, 200
real rows/candidate + 20×2 determinism; cold load ≈ 25 s/GB on this box):

| candidate | warm s/row | full corpus (62,103) | parse | determinism | max prompt tok (ctx 8192) |
|---|---|---|---|---|---|
| llama3.1-8b-q8 | ~0.43 | ~7.5 h | 200/200 | 20/20 byte-identical | 2,014 |
| nemotron-3-nano-30B-A3B Q8 | ~0.81 | ~14 h | 200/200 | 20/20 | 2,185 |
| qwen2.5:32b (probe arm) | ~0.74 | ~13 h | 200/200 | 20/20 | 1,992 |
| gemma3-27b-q8 | ~1.15 | ~20 h | 200/200 | 20/20 | 2,069 |
| GLM-4.5-Air Q4_K_M (106B MoE) | ~0.91 | ~16 h | 200/200 (zero think-leak; bare labels) | 20/20 | 1,990 |

GLM load ops (constraint, recorded in gx10 memory): 72GB cold load ≈ 30 min — **pre-warm with the
run's exact `num_ctx` + `keep_alive:2h` before the harness** (a num_ctx mismatch triggers a full
silent reload; a client disconnect cancels an in-flight load); server `OLLAMA_LOAD_TIMEOUT=30m`
clears it with little margin.

Even full-corpus on every candidate ≈ 2.5–3 GPU-days sequential; coordinate windows with Nate ad
hoc (chunked nohup + cache-resume: pausable per file). Local temp-0 determinism is EXACT
(byte-identical re-runs) vs the panel's 0.2–1.7% flip rate. Week-to-date judging spend at draft:
$23.29 (disambig, 2026-07-10). If this study PASSES, recurring epoch judging drops from ~$25-30
to ~$1-3 (spot-audits only).

**Question.** The A′ 5-vendor OpenRouter panel is the locked runtime self-attribution instrument
(gold-validated: panel-vs-gold 4-way 0.921, breach-agree 0.961, breach P 0.952 / R 1.000; vendor
inter-reliability breach AC1 0.900 overall / 0.827 BEM). Can a SINGLE local ollama judge on
Sparky reproduce the panel's *decisions* well enough to become the default instrument, with the
panel retained as spot-audit + escalation tier?

**The free validation set.** (a) `gold_set/gold_set_a4.jsonl` — 228 adjudicated rows (61 breach),
drift-free absolute anchor. (b) The committed corpus: 37 `gen_sweep/*_JUDGE.jsonl` files,
107,648 rows, **62,103 with votes**; committed decision = `breach_from_votes(votes)` (the
gate-correct determination, never `panel_label`); 7,718 BREACH-decision rows; 2,815 escalated
(decision None — excluded from agreement, local behavior on them reported descriptively).

## 1. Candidates (roster ratified by Josh 2026-07-10 evening)

| tier | model | family | note |
|---|---|---|---|
| big | GLM-4.5-Air instruct Q4_K_M (106B MoE, ~12B active) | glm | family-disjoint from all subjects AND panel vendors; **DELIBERATE DEVIATION from the Q8-only roster line** (Q8 ≈ 112GB won't fit 128GB unified; Q4_K_M = 73GB; quant held constant within-candidate; the empirical gates are the evidence) — registered as **DEVIATIONS.md I2** at lock. Imported via merged GGUF + `ollama create` (ollama 0.30.10; HF sharded pull AND local sharded import both fail — merge with `llama-gguf-split --merge`) |
| mid | gemma3-27b-q8 | gemma | on disk; **NOT fully family-disjoint** (red-team S4): the corpus's older epochs contain a gemma3:12b subject — 196 decided self-family rows, mechanically flagged `local_self_family` and excluded from its primary κ (disclosed here; the exclusion machinery is lock-tested). gemma4:31b EXCLUDED — known load-stall |
| mid | nemotron-3-nano-30B-A3B Q8 (`nemotron-a3b-sq:Q8_0`) | nvidia | on disk; MoE 3B-active; family-disjoint (verified: zero nvidia-family subjects corpus-wide) |
| small | llama3.1-8b-q8 | llama | on disk; family-disjoint (verified corpus-wide); fastest |
| probe | qwen2.5:32b | qwen | DELIBERATE self-family arm: judges its own family for **8 corpus subjects** (qwen3.5-base, 4 qwen-based claude-distills, qwen1.5/2/2.5-7b in older epochs — red-team S5) — measures the single-judge self-family effect; NEVER decision-bearing |

DROPPED: llama3.3:70b-instruct-q8_0 — LOAD-STALL on this box (45-min tensor-load timeout,
2026-07-10, journal receipt; same class as gemma4:31b). Evaluated-and-rejected at proposal time:
Qwen3.5-122B-A10B + Qwen3-Coder-Next (subject-family conflict), DeepSeek-R1-Distill-Llama-70B
(always-think incompatible with the 16-token one-word contract), Nemotron-3-Super-120B NVFP4
(TensorRT-LLM format, not ollama-runnable).

Selection preference on PASS: the **smallest** candidate clearing every gate (throughput is the
point of the exercise). Fallback = next tier up.

## 2. Instrument contract (lock-tested, tests/test_local_judge.py — 17 tests green at lock)

System prompt = `RUBRIC_A4` byte-identical (sha pinned:
cd715d79eb23e4bcbfa3711c0a3dc7a1b630e54ae1bb90108ed8c5dccfd08d51 — any rubric edit fails the
suite loudly = the bridging tripwire); user prompt byte-equivalent to `classify_one`'s; parse =
`_parse_label` (earliest-label); `_mechanical_invalid` applied identically; temp 0,
n_predict 16, think:false; explicit num_ctx 8192 with pre-call estimate skip + post-call
`prompt_eval_count` truncation assertion (ollama front-truncates silently — would eat the rubric
first). Regex-ABSENT rows are job-construction ground truth: passed through, never judged.

## 3. Estimands & gates

**E-A (gold, absolute; screening):** per candidate — 4-way agreement, breach agreement, breach
P/R (Wilson), OWNED/SA per-rung P/R, planted catch; benchmark row = the committed panel numbers.
**G-A (advance to Phase B):** breach recall ≥ 0.90 AND breach precision ≥ 0.80 on gold (n=228;
the asymmetry is deliberate — a missed breach corrupts epochs silently, a false breach costs one
spot-audit; panel comparison reported, not gated). [Pressure test: attack these numbers.]

**E-B (corpus, agreement at scale; primary):** breach-binary agreement local-vs-committed
(local decision = `breach_from_votes({"local": label})`), population = committed decision ∈
{BREACH, NOT}, self-family rows excluded (single-judge analog of the panel rule; reported
separately). Cohen's κ + Gwet AC1 + raw agreement + P/R (committed as reference), cluster
bootstrap CI by (file, subject_model, mode, probe_idx). Strata: pooled, per channel, per subject
family, per epoch file. COVERAGE (fraction of eligible rows yielding a local decision) and
κ_strict (non-decisions = disagreement) are first-class.
**G-B (LOCKED; single-sourced in `local_judge_score.GATES`, pinned by
`test_locked_gates_match_prereg`):**
- pooled κ ≥ 0.80 (point; cluster-bootstrap CI reported — at n≈50k the CI is O(0.01), so the
  point binds; red-team NOTE 10);
- BEM-channel κ ≥ 0.75;
- **recall channel: breach sensitivity ≥ 0.75 AND specificity ≥ 0.995** (vs committed
  decisions). NOT κ — at the recall channel's 0.97% breach prevalence (206/21,324) the panel's
  OWN re-judge drift (0.2–1.7% flips) yields κ_recall ≈ 0.50–0.74 (the κ-paradox; red-team
  MUST_FIX 1: a fixed κ bar there fails panel-equivalent judges). κ_recall is reported
  descriptively with this note attached;
- coverage ≥ 0.98 pooled and ≥ 0.97 per channel;
- |κ − κ_strict| ≤ 0.03 pooled (abstention must not buy agreement);
- family strata: κ ≥ 0.65 for every stratum with ≥ 500 decided rows AND ≥ 30 committed-breach
  rows (below that = descriptive only; κ on ~150 rows is noise — red-team S7);
- **κ = n/a (undefined) FAILS the gate it belongs to, never passes** (red-team MUST_FIX 2);
- **AC1 is reported but NON-BINDING in corpus mode**: a constant-label judge scores AC1 0.99 on
  recall (majority-class trap) — corpus AC1 is NOT comparable to the panel's gold-mode AC1 gate
  (red-team S3; the scorer prints it annotated "(non-binding)").
**Ceiling disclosure:** committed labels are epoch-dated; the panel's own re-judge flip rate
(disambig drift receipt: 0.2–1.7% rows) bounds achievable agreement below 1.0 — a G-B failure
that per-file stratification attributes to OLD-epoch files specifically is reported as
ceiling-suspect, not judge-failure (outcome matrix row).

**E-C (verdict reproduction; the deployment bar):** swap seam (`local_swap.py` — writes BOTH
decision-bearing fields: `votes={"local": ...}` AND `panel_label`; no-vote rows byte-identical)
on complete arms, then re-run three locked analyzers unmodified:
`disambig_analyze.py` (a/m/h/c ladder — its drift report doubles as a built-in local-vs-panel
receipt), `multifact_analyze.py` (single+triple; the 0.182-family numbers),
`blockframe_analyze.py` (exercises the `panel_label != "ABSENT"` recall-surfacing path feeding
verdict-bearing G-AVAIL).
**G-C:** verdict-CATEGORY identity on every gated line (rung verdicts, gates, ladder summary);
point estimates within ±0.05 (the cross-session DRIFT_WARN convention).

**Descriptives (never gates):** local labels on the 2,815 committed-escalated rows; self-family
probe arm κ vs the family-disjoint candidates on the same rows; 4-way confusion per candidate;
breach-flip adjudication dump (becomes the operational spot-audit worksheet on PASS).

## 4. Phases

- **Phase 0 (pre-lock, operational):** per candidate: ~200-row real-prompt throughput (LAN),
  prompt_eval_count histogram vs num_ctx, temp-0 determinism (20 rows judged twice — byte-equal),
  load-stall screen. Output = the measured tier table; Phase B scope is written from it.
- **LOCK** after rule-12 double pressure test (2 adversarial agents) + Josh's scope ratification.
- **Phase A (gold screening):** all 4 candidates × 228 rows. Apply G-A.
- **Phase B (corpus) [RATIFIED by Josh at lock, 2026-07-11]:** **FULL corpus (all 62,103 judged
  rows) for every G-A passer AND the probe arm** (~70 h ≈ 3 GPU-days serial if all pass;
  completeness chosen over the manifest default that the pressure test recommended — recorded as
  Josh's explicit call). The committed manifest (13,145 coords, sha pinned in §9) remains the
  FALLBACK artifact if GPU time must shrink mid-run; any such shrink is a disclosed scope change.
  Serial per model; nohup + cache-resume chunking (Nate-pausable — see the GLM keep_alive note);
  the G-C candidate is full-corpus by construction.
- **Phase C (verdict reproduction):** on the nominated replacement candidate only.
- Verdict-blind audit of local outputs (completeness, coverage, ctx-skip count, determinism
  re-check) BEFORE scoring; then scoring; then 2 adversarial results reviewers; results doc; PR.

## 5. Adoption rule (pre-registered consequence)

PASS (all of G-A/G-B/G-C on one candidate) → that model becomes the DEFAULT judge for future
epochs via the **executable fresh-epoch flow** (built and lock-tested pre-lock — pressure-test
MUST_FIX 1): generate on Sparky → scp caches as today → `multifact_judge.py <sources> <out>
--local-judge <model>` (identical job construction, ABSENT semantics, completeness refusal, and
output schema; rows carry `votes={"local": label}` + provenance; runs on Sparky, or from the
Windows box via an SSH tunnel `ssh -L 11434:localhost:11434` since Sparky's ollama binds
localhost) → analyzers unchanged. Ops: pre-warm the judge with the run's exact `num_ctx` +
`keep_alive` sized to cover any planned Nate pause (a keep_alive lapse on GLM = a 30-min reload).

**(a) A′ spot-audit per epoch (the per-epoch bridge — executable mini-protocol):**
- rows: ALL local-BREACH rows (typically ~100-300) + a seeded random subsample of 200
  local-NOT rows stratified round-robin by (mode, subject_model); seed =
  `int(sha256(epoch_stamp)[:8], 16)` — derived, not chosen.
- judge: the pinned 5-vendor panel, byte-identical rubric (sha `cd715d79…`), self-family
  exclusion as always; cost ~$1-3 at the observed $3.6/1k-jobs rate.
- metrics + thresholds: breach-binary agreement on the NOT-subsample ≥ 0.95 (the miss-direction
  canary) AND panel-confirmed fraction of local-BREACH rows ≥ 0.75 (the false-alarm bound).
- consequence: EITHER threshold fails → that epoch is re-judged by the FULL panel before any
  analysis (cost reverts for that epoch), and local judging is suspended pending a disagreement
  analysis; the audit receipt (rows, seed, agreements) is committed with every epoch — this
  receipt is what a future analyst cites for cross-epoch comparability.
**(b) escalation tier** — the panel adjudicates every local/spot-audit disagreement.
**(c) bridging** — THIS study is the validation bridge (both instruments over the committed
record); the per-epoch spot-audit receipts are the RUNNING bridge thereafter.
**(d) instrument version** = model digest + ollama version + rubric sha (recorded in run meta);
any ollama/model/quant upgrade re-runs Phase A (gold, ~free) before continuing.
FAIL → panel stays default; the disagreement dump becomes the error-analysis input for a
possible fine-tuned-judge follow-on (NEW prereg; not licensed here).

## 6. CAN / CANNOT

CAN: license local-default WITH panel spot-audits (the audit tier is load-bearing in the PASS
design); locate where a local judge diverges (channel/family/rung); measure the single-judge
self-family effect.
CANNOT: certify the local judge as gold-equivalent beyond n=228 absolute rows — **and the gold
screening is in-sample for the RUBRIC** (RUBRIC_A4 was tuned against this gold set via the 6×
soft-band expansion; the local model is fresh but reads a rubric fitted to score these rows —
gold P/R may be optimistic; the corpus κ and Phase C carry the decision weight; red-team NOTE
8); separate local-judge error from cross-epoch panel drift in corpus κ (bounded, not
eliminated, by the ceiling disclosure); generalize to future rubrics, subject families outside
the corpus, or non-Q8 quants beyond the registered GLM Q4 candidate (DEVIATIONS I2); replace the
panel's 5-vendor plurality semantics (single judge has no tie/escalate mechanism — its
INVALID/None rows are conservative non-decisions).

## 6.5 Results doc MUST report (pre-named checklist)

Per-candidate gold table vs the PANEL_BENCH row; per-candidate corpus κ/AC1/agreement/P/R/
coverage/κ_strict across ALL strata (pooled, per-channel, per-family, per-file table); breach-flip
dump summary + worked examples; the probe arm's self-family κ delta vs the family-disjoint
candidates on the same rows; local-label distribution over the 2,815 committed-escalated rows;
Phase C per-analyzer verdict-CATEGORY identity + point-estimate deltas (±0.05 band); the
old-vs-new plain-dollar cost table; the adoption decision (which candidate, or none) + the
spot-audit protocol restated; every gate's locked value vs realized value.

## 7. Pressure-test record (rule 12 — completed 2026-07-11, two adversarial agents, pre-lock)

**Red-team (all folded):** M1 recall-channel κ gate mis-calibrated — DEMONSTRATED that the panel
re-judging itself at its own drift rate scores κ_recall 0.50–0.74 at the channel's 0.97% breach
prevalence (κ-paradox) → recall gated on sensitivity/specificity instead; κ_recall descriptive.
M2 κ=n/a had no gate behavior (and broke the κ_strict clause via TypeError) → n/a-FAILS rule,
implemented + tested. S3 AC1 majority-class trap (constant-label judge scores AC1 0.99 recall /
0.724 BEM — above the panel's gold-mode gate) → AC1 declared non-binding, annotated in output.
S4 gemma3-27b not fully disjoint (gemma3:12b subject, 196 decided rows in old epochs) → roster
disclosure; machinery already excludes. S5 probe undercount (8 qwen-family corpus subjects, not
5) → corrected. S6 cache keyed by model NAME not digest → per-cache-dir digest pin,
`assert_digest_unchanged`, tested. S7 family-strata gate underpowered on small strata → min-n
(500) / min-breach (30) guard; below = descriptive. N8 gold is rubric-in-sample → §6 CANNOT.
N9 scorer accepts swap-output by mistake → hard refusal, tested. N10 CI-LB redundancy at n≈50k →
point binds, CI reported; manifest files are non-swappable → the G-C candidate MUST be
full-corpus (folded into §4 Phase B). SURVIVED (verified by the red-team on real data): swap
field-coverage complete incl. None/escalated semantics; κ catches the constant-label judge
(0.000); coverage catches the abstention dodger (0.778 ≪ 0.98); perfect-mirror κ=1.000;
llama/nemotron/glm disjointness; gold/corpus non-overlap (0/227); rubric literal-braces parity.
**Legitimate-use (all folded):** M1 §5 adoption was not executable (tools were validation-shaped;
job construction welded to panel_judge) → BUILT the fresh-epoch seam pre-lock:
`local_panel_result` + `multifact_judge --local-judge` (identical job construction/refusal
semantics; lock-tested contract). M2 spot-audit unspecified → executable mini-protocol in §5(a)
(derived seed, N, panel+rubric sha, two thresholds, revert consequence, committed receipt).
S3 full-corpus-on-all-passers over-design → Phase B default inverted (manifest for all; winner
promoted to full corpus). S4 scorer had no gate evaluation → G-A/G-B engines + `--enforce`,
tested (degenerate FAILS, perfect PASSES). S5 gate numbers dual-sourced → single source =
`GATES`/`GATES_GOLD` + pin test. S6 Q4 deviation deferred to adoption → registered at lock
(DEVIATIONS.md I2). S7 GLM keep_alive vs Nate pauses → ops note in cost header + §5. S8 results
checklist → §6.5. N9 cumulative progress lines → added.

## 8. Outcome → consequence matrix — [DRAFT]

| outcome | consequence |
|---|---|
| PASS on small tier | adopt smallest; biggest becomes the escalation-tier-2 option |
| PASS only on big tier | Josh's call: GPU-time per epoch vs $25-30 panel (plain-dollar comparison in results) |
| G-A pass, G-B fail | no adoption; disagreement analysis → possible rubric-adaptation or FT-judge follow-on (new prereg) |
| G-B fail attributable to OLD-epoch files (per-file strata: failures concentrate in cleanstrata/batch-era files while recent-epoch strata pass) | ceiling-suspect, not judge-failure: report both readings; a re-judge of ONE old file by the CURRENT panel (~$2-3, Josh's approval) becomes the licensed tiebreaker — do NOT silently adopt or reject |
| G-C fail with G-B pass | no adoption (verdict flips are disqualifying regardless of κ); report which analyzer/line flipped |
| self-family probe shows family effect | documented constraint: local judge must stay family-disjoint from all subjects in any future epoch (roster check at prereg time) |
| ALL candidates fail G-A | panel stays; gold set grows as the next lever (adjudication backlog), not judge shopping |

## 9. Locked manifest

- Toolchain (normalized-newline sha16): local_judge.py `70e9e25e662e5104`, local_swap.py
  `a9ccbec5f57d653e`, local_judge_score.py `1044cd81b6b06180` (gates single-sourced in
  `GATES`/`GATES_GOLD`, pinned by `test_locked_gates_match_prereg`), local_judge_manifest.py
  `7d152c682bb906af`; lock tests: `tests/test_local_judge.py`, 17 green at lock.
- Rubric: RUBRIC_A4 sha256 `cd715d79eb23e4bcbfa3711c0a3dc7a1b630e54ae1bb90108ed8c5dccfd08d51`
  (pinned in the test suite — the bridging tripwire).
- Phase B manifest: `phaseB_manifest.jsonl`, **13,145 coordinates** (all 7,718 breach + all
  2,815 escalated + seeded NOT sample), seed 20260711, not-per-cell 40, sha256
  `0021915e053200234124d18e682cb151bf6aa9134ca913f8878558e5226c8649` (committed).
- Fresh-epoch adoption seam: `multifact_judge.py --local-judge` → `local_judge.local_panel_result`
  (contract lock-tested).
- Candidates as §1; ollama 0.30.10; model digests recorded per run in `localjudge_meta__*.json`
  sidecars (digest guard: `assert_digest_unchanged`).
- Panel benchmarks (gold mode comparison row): 4-way 0.921, breach-agree 0.961, breach P 0.952 /
  R 1.000; panel inter-vendor AC1 (breach 0.900 overall / 0.827 BEM) is a RELIABILITY number,
  not a gold-accuracy benchmark — never compared to local gold numbers.
- Judging cost this arc: $0 OpenRouter; GPU per the §cost-header tier table.
