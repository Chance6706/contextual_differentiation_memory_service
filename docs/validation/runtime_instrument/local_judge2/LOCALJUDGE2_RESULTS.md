# LOCALJUDGE-2 results — how 62 open models judge self-attribution

**Status: COMPLETE 2026-07-28 — characterization + integrity gates + single-look confirmation all
run; adoption outcome: NO ADOPTION (§10).** Prereg: `LOCALJUDGE2_PREREG.md` (LOCKED 2026-07-12). Intent
(Josh-set, 2026-07-17; reinforced 2026-07-28): **characterize HOW open local models judge — the
failure-mode survey is the product.** The adoption gates are the pre-registered sidebar (§8 here),
reported second. 💵 Cost: **$0 API** for everything in this doc (all judging + re-judging local on
Sparky); the only priced option is the deferred label-noise re-adjudication (~$2–3, §9).

## 1. What ran

Closed roster of **62 judges** (64 locked minus 2 in-flight exclusions, §7) × the full committed
37-file gen_sweep corpus (60,646 decided rows; 41,410 SELECTION / 19,236 CONFIRMATION per the
frozen epoch-file split, sha `b673e2a5…`). Phase M 2026-07-12 → 07-28, serial model-outer on
Sparky, instrument byte-identical to LOCALJUDGE-1 (RUBRIC_A4 `cd715d79…`, temp 0, n_predict 16).
Per-model instrument digests: `phaseM_digests/` (62). Raw judge mirrors (6.7 GB) stay uncommitted
per NOTE 16; every number below reproduces from the committed receipts in `phaseM_receipts/`.

## 2. PRIMARY RESULT — judging failure is one-dimensional to first order

The per-judge two-sided error table (`phaseM_receipts/matrix_report.txt`, PER-JUDGE TWO-SIDED
ERROR) sorts 62 heterogeneous judges onto a single **conservative↔liberal axis**:

- **Liberal pole (false-alarm sprayers):** gemma1-2b FA 0.997 (a constant-BREACH judge),
  qwen2.5:0.5b FA 0.945, yi:34b-chat FA 0.890, granite-3.3-2b FA 0.869, internlm2.5-7b FA 0.853.
  Weak models don't fail noisily — they fail by yelling BREACH.
- **Conservative pole (silent missers):** claude-opus-distill miss 0.998 (constant-NOT),
  claude-code miss 0.889, granite-3.0-8b miss 0.745, qwen3.5:9b miss 0.580, glm miss 0.368 at
  FA 0.009, mistral-small miss 0.306 at FA 0.007.
- **The balanced middle is nearly empty:** only the qwen3.5/3.6 27–35B block (miss 0.09–0.15,
  FA 0.008–0.02) and, more loosely, nemotron-super (miss 0.179 / FA 0.046) and laguna-xs.2
  (miss 0.064 / FA 0.159) sit near balance.

Capability doesn't buy balance — it buys a *choice* of pole (yi:34b sits at the liberal pole with
the 2B models; its nearest behavioral neighbour is gemma1-2b, agree 0.928). This replicates and
scales LJ-1's directional finding (GLM misses 6:1 vs nemotron/qwen spraying).

## 3. Generation moves judging skill; parameter count mostly doesn't

Within qwen at constant-ish scale: qwen2.5:32b 0.629 → qwen3.5:27b 0.885 (+0.26 across one
generation); meanwhile qwen2.5:32b → qwen2.5:72b goes *backwards* (0.596). The mistral line:
v0.1/v0.2/v0.3 7B ≈ 0.27–0.43 → mistral-small 24B 0.771. Granite 3.0→3.3 wobbles within
0.23–0.35 with no monotone size effect (2B beats 8B in two of four generations). Judge-side skill
tracks **training recipe/generation**, echoing the subject-side generation-isolation result from
the opposite chair. Quant is inert here too: every -sq/Q8 twin lands within ~0.02 of its base
(32b-sq actually +0.020), replicating the quant-replication arc's "generation moves leak, quant
moves coherence" from the judge side.

**Flagged anomalies (kept, not smoothed):** (a) qwen3.5-9b-BASE scored 0.658 — top-11 overall,
beating the 72B instruct and every mistral-7B/granite — the prereg's "expect weak floor anchor"
expectation is INVERTED; (b) qwen3.5:4b (0.751) far outperforms qwen3.5:9b (0.551), whose
hyper-conservatism (miss 0.580) looks like an alignment-tuning artifact, not a capability gap.

## 4. The Claude distills: a gradient that isolates the tuning layer

fable 0.661 > mythos 0.480 > code 0.180 (coverage 0.849) > opus-distill 0.003 (constant-NOT,
miss 0.998, parses fine). Most telling: **claude-fable agrees with qwen3.5-9b-base at 0.985** —
the distill judges self-attribution almost exactly like its backbone's *base* model, and *better*
than the instruct sibling qwen3.5:9b (0.551). Distillation preserved base-model judging where
instruct-tuning damaged it; the answer to the prereg's "does a Claude-distilled judge read
self-attribution differently?" is: **no — it reads it like its base, shifted conservative.**

## 5. Self-family reading splits by lineage (descriptive; S7 confound stands)

LJ-1's inversion (judging own family BETTER) **replicates in the qwen2.5 line** (own vs disjoint:
14b 0.622/0.380, 32b 0.751/0.629, 72b 0.690/0.596) **and mistral-small (0.931/0.771)** — but
**reverses in qwen3.5/3.6** (27b 0.843/0.885) **and the claude distills** (fable 0.480/0.661).
Whatever family-familiarity is, it changed sign between generations. Per prereg §4 this is a
descriptive replication signal only — own-family rows differ in subjects/epochs/prevalence, so no
causal family effect is claimed. The family-disjoint adoption rule stands regardless.

## 6. Failure modes include MUTE and BROKEN, not just wrong

- **mistral-v0.1-7b: zero parseable labels across 60,646 decided rows** (JUDGED ledger line,
  coverage 0.000) — a judge can complete a three-day run and say nothing.
- **phi-3-mini: 17 usable rows** (62,086 parse-failures); its audit exit-1 is the degeneracy
  tripwire firing on that vanishing sample (line-pairing and universe accounting reconciled clean)
  — receipt committed as-is (`phaseM_receipts/audits/`).
- **gemma1-2b coverage 0.450, claude-code 0.849** — partial mutes.
- **yi:34b-chat κ 0.035 at full coverage** — fluent, confident, and uncorrelated with the panel.

## 7. Difficulty map, label-noise probe, exclusions

**Difficulty map (62 judges, SELECTION):** concordant-correct 682 rows (1.6%), split 40,728
(98.4%), **concordant-wrong 0** — the strict-unanimity stratum died at 62 heterogeneous judges
exactly as red-team N11 predicted; per-channel/family/epoch strata + the row-difficulty histogram
(mode ≈ 7–8 disagreeing judges, tail to 46) are in the committed report. The N11 note stands: do
NOT read the empty blind-spot stratum as "no shared blind spots" — the operative signal is below.

**Label-noise probe (K≥5 distinct families, seeded, stamp `localjudge2-analyze-20260728`):**
**116 candidate rows; 114 of them cross toward BREACH** (judges unanimously say BREACH where the
panel said NOT). The shared-local-bias direction is overwhelmingly false-alarm-side — consistent
with the S9 framing that these are AMBIGUOUS between panel error and shared local bias, with
shared-bias expected to dominate. Worksheet: `phaseM_receipts/labelnoise_worksheet.md`. Optional
~$2–3 panel re-adjudication is Josh-gated and NOT run (§9).

**Exclusions applied as locked:** gpt-oss:120b — Phase-R parse gate 0/228 (reasoning consumed the
frozen n_predict=16; exclusion, not contract relaxation). olmo3-7b — NOT a load-stall: its GGUF
chat template invokes `tools | tojson`, unparseable by the pinned ollama build (deterministic
llama-server exit 1, ×2); excluded (Josh-ratified 2026-07-28), olmo family covered by olmo2-7b.
Known stall-class attempt-once: gemma4:31b, llama3.3:70b (as locked).

## 8. SIDEBAR — the pre-registered adoption gates

Selection leaderboard (all 62) is in the committed matrix report; freezes committed BEFORE any
confirmation look (commit `65c0938`):

- **Single nominee: qwen3.5_27b** — selection pooled 0.885 / BEM 0.877, cov 1.000 (self-family-
  reduced n=31,711, NOTE 15). Per-family selection: granite 0.880, mistral 0.929, internlm 0.850.
- **Ensemble nominee (locked rule, no free search): k=3 unweighted** {qwen3.5_27b, 27b-sq,
  3.6-27b-sq} — selection pooled 0.892, but the all-qwen membership drops all votes on qwen rows →
  **selection coverage 0.766 = the red-team M2 coverage-crater scenario, visible pre-confirmation**
  (k=5 runner-up: 0.847, cov 1.000 — recorded in the receipt, not nominated).
- Best fully-family-disjoint single judge: **nemotron-super-q4 0.747/0.743 (n=41,410, cov 1.000,
  miss 0.179 / FA 0.046)** — the new-pull thesis (§8 row 7 of the prereg) gets a best-disjoint
  judge but NOT a gate-clearer on selection numbers; +0.220 over its Nano-30B sibling. GLM holds
  0.717 (LJ-1 cross-arc anchor, unchanged).

**CONFIRMATION (single look each, binding — run 2026-07-28 after determinism + audits green;
receipts `confirmation_single.txt` / `confirmation_ensemble.txt`):**

- **single:qwen3.5_27b → G-B FAIL on exactly one gate.** Locked-vs-realized: pooled κ ≥0.80 →
  **0.862 PASS**; BEM κ ≥0.75 → **0.857 PASS**; recall sensitivity ≥0.75 → **0.738 FAIL**
  (n_breach=206 — a ~3-row shortfall); recall specificity ≥0.995 → **0.999 PASS**; coverage
  ≥0.98/0.97 → **1.000/1.000/1.000 PASS**; |κ−κ_strict| ≤0.03 → **Δ=0.000 PASS**; family granite
  **0.851 PASS**, mistral **0.944 PASS** (gemma/internlm/phi below min-n, descriptive). Selection→
  confirmation shrinkage 0.885→0.862 (modest, expected selection optimism). The one failing gate is
  the phenotype speaking: the 27B block sits slightly conservative (§2), and the recall subset is
  exactly where a conservative judge pays.
- **ensemble:k3:unweighted → G-B FAIL, the M2 coverage crater realized.** κ where it can vote:
  pooled **0.869** / BEM **0.865** (PASS); but coverage **0.756/0.780/0.704 FAIL** (all-qwen
  membership drops all votes on qwen-family rows), recall sensitivity **0.130 FAIL** (only 46
  breach rows retain votes), strict Δ **0.118 FAIL**. Accurate where it votes; mute on a quarter
  of the holdout. The locked no-free-search rule was applied as written — the k=5 cov-1.000
  runner-up was recorded at freeze time but not nominated, and is NOT scored on confirmation
  (that would be a second look).

**G-C verdict reproduction: DID NOT FIRE** — its locked condition (single-judge G-B confirmation
pass) is false. Ensemble G-C remains DEFERRED per the ratified §4 narrowing.

## 9. Integrity receipts, deviations, cost

**Audits:** 62/62 run verdict-blind BEFORE any official receipt; 61 PASS, 1 exit-1 (phi-3-mini
degeneracy tripwire, §6). **Determinism:** 20-coord fresh-cache re-judge per model against the
LJ-1 manifest (sha16 `24328bd9…` verified pre-ship), Sparky ledger 62/62 DETERM-DONE, comparator
receipt `phaseM_receipts/determinism_report.txt`: **46/62 models 20/20 byte-exact (label+raw);
all frozen nominees, nemotron-super, and glm byte-stable.** The 16 non-exact models decompose as:
13/25 diff-rows **label-identical** (raw drift only, zero scoring impact — 8 of them phi-3-mini's
None→None degenerate garbage varying byte-wise) + **12 single-row label flips** (1/20 each; 2/20
for nemotron-nano) concentrated on **8 corpus rows shared across models** (frame_single:234 flips
or drifts in 5 judges, cons_p4:826 in 4, frame_triple:1977 in 3). The shared-coordinate signature
says these are near-tie rows tipping under temp-0 llama.cpp numerics, not cache corruption (which
would scatter per-model); byte-determinism is itself a judge phenotype here — every heavyweight
except yi:34b is byte-stable, instability pools in small/degenerate judges + boundary rows.
Co-residency (determ pass kept up to 3 small models loaded; Phase M was strictly one-resident) is
a plausible but unproven amplifier — flagged, not asserted. **Disclosure (analysis order):** two provisional SELECTION looks (07-27,
07-28) preceded the audits; the official pass was regenerated post-audit and is numerically
identical to the provisional runs (diff = embedded paths only). **Disclosures (run):** nemotron-
super loaded on 2nd attempt after an infra fix (OLLAMA_LOAD_TIMEOUT + NVMe); the Phase-M driver
buffers the roster at launch, so a mid-run roster addition (nemotron-super, added 07-20) was
invisible until a driver re-run — cost ~4 idle hours on 07-27, no data impact (idempotent ledger).

**Cost (plain dollars):** this arc $0 API + ~2.5 weeks Sparky GPU. Frontier panel baseline stays
~$25–30/epoch (LJ-1 §5). An adopted single local judge ≈ $0/epoch + GPU-hours; the nominated
ensemble would be 3× inference PLUS an emitter/deploy build (deferred) — decision matrix in §10.

## 10. Outcome → consequence (prereg §8)

**Realized outcome: nothing clears G-B on confirmation → NO ADOPTION; the frontier panel stays
the verdict authority.** Which "nothing clears" row fires depends on whether the blind spot is
prompt-fixable:

- The evidence leans **row 3 (prompt-fixable → rubric/prompt-adaptation follow-on, new prereg, no
  adoption):** the single judge's sole failure is a 0.012 sensitivity shortfall (~3 breach rows)
  with specificity headroom 0.999 vs the 0.995 bar — a calibration-shaped miss (the conservative
  pole of §2), not a comprehension hole. A liberal-ward rubric nudge trading spec for sens is the
  obvious candidate; it requires a NEW prereg and is NOT run here.
- **Row 4 (FT-judge follow-on)** stays licensed to *draft* only if prompt adaptation is judged
  not viable; both follow-ons are draft-licenses, neither auto-runs.
- **Row 5 (self-family):** replicates but **sign-flips by lineage** (§5) — documented; the
  family-matched-FT design-axis consequence carries the lineage caveat.
- **Row 7 (new-pull/200B thesis):** UNSUPPORTED — nemotron-super is best-disjoint (0.747) but
  never gate-grade; it did not clear where residents failed.
- **Ensemble row:** did not clear (coverage crater, §8) — the emitter/deploy build decision is
  moot; the k=5 shape is a candidate for a future prereg only.

Standing queue for Josh: (a) label-noise re-adjudication option (~$2–3, Josh-gated, §7); (b)
rubric-adaptation vs FT-judge follow-on choice (each needs a new prereg); (c) nothing else — the
adoption question is closed negative for this roster + rubric.

## §11 checklist coverage

Difficulty strata pooled+channel+family+epoch ✅(report) · histogram ✅ · two-sided error all
judges ✅ · redundancy/pairwise + committed matrix ✅ · self-family table ✅ · selection
leaderboard ✅ · frozen nominees ✅ · confirmation locked-vs-realized ✅(§8) · recall sens/spec
✅(§8) · ensemble composition/combiner ✅ · G-C per-analyzer ✅ condition-not-met (§8) · ensemble
G-C-deferred flag ✅ · label-noise stratum ✅ · cost table ✅ · adoption decision ✅ NO ADOPTION
(§10) · new-pull G-A rows ✅(roster header) · gpt-oss parse gate ✅ · roster self-family
verification ✅(`roster_selffamily.txt`) · determinism receipt ✅(§9, 46/62 byte-exact, nominees
clean).
