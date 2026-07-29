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
per prereg NOTE 16 — they live at `D:\cdms_localjudge2_pull\phaseM\` (Windows box; run tree on
Sparky at `~/cdms_localjudge2/`); every number below reproduces from the committed receipts in
`phaseM_receipts/`: `matrix_report.txt` (leaderboard, two-sided error, difficulty map, self-family,
redundancy), `pairwise.jsonl` (full pairwise matrix), `ensemble_selection.txt`, `phaseM_scoring/`
(14 heavyweight per-judge selection receipts), `labelnoise_worksheet.md`, `audits/` (62 + SUMMARY),
`determinism_report.txt`, `confirmation_single.txt` / `confirmation_ensemble.txt`, and the run
ledgers `phaseM_ledger.txt` / `determ_ledger.txt`. NOT committed: `difficulty_rows.jsonl` (per-row
difficulty; pull dir only). Corpus: `docs/validation/runtime_instrument/gen_sweep/*_JUDGE.jsonl`.
Terms: **BEM** and **recall** are the instrument's two judged channels (Bem-firewall
self-attribution probes vs workspace-fact recall; see `../local_judge/`); **-sq** = salience-quant
builds (`roster.txt`); shorthands N11/M1/M2/S4–S9 are red-team findings and NOTE 12/15/16 are
locked notes, all in `LOCALJUDGE2_PREREG.md` §4/§9–10.

## 2. PRIMARY RESULT — judging failure is one-dimensional to first order

The per-judge two-sided error table (`phaseM_receipts/matrix_report.txt`, PER-JUDGE TWO-SIDED
ERROR) sorts 62 heterogeneous judges onto a single **conservative↔liberal axis**:

- **Liberal pole (false-alarm sprayers):** gemma1-2b FA 0.997 (a constant-BREACH judge),
  qwen2.5:0.5b FA 0.945, yi:34b-chat FA 0.890, granite-3.3-2b FA 0.869, internlm2.5-7b FA 0.853.
  Weak models don't fail noisily — they fail by yelling BREACH.
- **Conservative pole (silent missers):** claude-opus-distill miss 0.998 (constant-NOT),
  claude-code miss 0.889, granite-3.0-8b miss 0.745, qwen3.5:9b miss 0.580, glm miss 0.368 at
  FA 0.009, mistral-small miss 0.306 at FA 0.007.
- **The balanced-and-accurate middle is nearly empty:** only the qwen3.5/3.6 27–35B block (miss
  0.09–0.15, FA 0.008–0.02) and, more loosely, nemotron-super (miss 0.179 / FA 0.046) and
  laguna-xs.2 (miss 0.064 / FA 0.159) combine balance with skill. Balanced-but-poor judges exist
  (command-r 0.179/0.184, falcon3-7b 0.146/0.156) — balance alone buys nothing.

"To first order" quantified (computed from the committed two-sided table): Spearman ρ(miss, FA)
= −0.775 across the 61 rankable judges — strong, but ρ²≈0.6, and the residual axis is plain
**skill** (total error spans 0.11–1.00; at FA≈0.15, miss runs 0.146–0.524). §3 lives on that
second axis. Capability doesn't buy balance — it buys a *choice* of pole (yi:34b sits at the
liberal pole with the 2B models; its nearest behavioral neighbour is gemma1-2b, agree 0.928).
This replicates and scales LJ-1's directional finding (GLM misses 6:1 vs nemotron/qwen spraying).

## 3. Generation moves judging skill; parameter count mostly doesn't

Within qwen at constant-ish scale: qwen2.5:32b 0.629 → qwen3.5:27b 0.885 (+0.26 across the
2.5→3.5 gap); meanwhile qwen2.5:32b → qwen2.5:72b goes *backwards* (0.596). The mistral 7B line:
v0.2/v0.3 ≈ 0.42–0.43, with the -g arm putting v0.1 at 0.270 (plain mistral-v0.1-7b scored
nothing at all — §6) → mistral-small 24B 0.771. Granite 3.0→3.3 wobbles within 0.03–0.35 with no
monotone size effect (2B beats 8B in two of four generations). Judge-side skill tracks **training
recipe/generation**, echoing the subject-side generation-isolation result from the opposite
chair. Quant is scale-dependently inert: every ≥24B twin lands within ~0.02 of its base (32b-sq
+0.020, 27b-sq −0.002, mistral-small-q8 −0.003), while small twins move up to ~0.06 (3b-sq
−0.060, 7b-q8 +0.031; the nemotron-nano Q8→Q4 pair, which also changes bit-width, −0.044) —
direction-consistent with the quant-replication arc's "generation moves leak, quant moves
coherence", now carrying a small-model caveat.

**Flagged anomalies (kept, not smoothed):** (a) qwen3.5-9b-BASE scored 0.658 — top-11 overall,
beating the 72B instruct and every mistral-7B/granite — the prereg's "expect weak floor anchor"
expectation is INVERTED; (b) qwen3.5:4b (0.751) far outperforms qwen3.5:9b (0.551), whose
hyper-conservatism (miss 0.580) looks like an alignment-tuning artifact, not a capability gap.

## 4. The Claude distills: a gradient that isolates the tuning layer

fable 0.661 > mythos 0.480 > code 0.180 (coverage 0.849) > opus-distill 0.003 (constant-NOT,
miss 0.998, parses fine). claude-fable's nearest behavioral neighbour is qwen3.5-9b-base (raw
agree 0.985; the backbone identity is per build metadata, not any committed receipt), and it
out-judges the instruct sibling qwen3.5:9b (0.551). Two counterweights from the same receipt keep
this correlational: raw agreement is not chance-corrected on a NOT-dominant corpus
(unrelated-lineage glm agrees with fable at 0.954), and claude-mythos's nearest neighbour is the
INSTRUCT qwen3.5_9b at 0.977 — the sibling supports "reads like its instruct" as readily as
"reads like its base." The answer to the prereg's "does a Claude-distilled judge read
self-attribution differently?" is: **no distinct reading emerges — the distills sit in their
backbone's neighbourhood, shifted conservative; consistent with, but not isolating, a
tuning-layer effect.**

## 5. Self-family reading splits by lineage (descriptive; S7 confound stands)

LJ-1's inversion (judging own family BETTER) **replicates in the qwen2.5 line** (own vs disjoint:
14b 0.622/0.380, 32b 0.751/0.629, 72b 0.690/0.596) **and mistral-small (0.931/0.771)** — but
**reverses in qwen3.5/3.6** (27b 0.843/0.885 — with exceptions: qwen3.5:2b goes own-better
0.179/0.085) **and the claude distills** (fable 0.480/0.661). The largest own-family population,
granite (n=24,500/judge, 8 judges), sits own-WORSE in 7 of 8. Whatever family-familiarity is, it
changed sign between generations and is not monotone within a lineage. Per prereg §4 this is a
descriptive replication signal only — own-family rows differ in subjects/epochs/prevalence, so no
causal family effect is claimed. The family-disjoint adoption rule stands regardless.

## 6. Failure modes include MUTE and BROKEN, not just wrong

- **mistral-v0.1-7b: zero parseable labels across 60,646 decided rows** (`phaseM_ledger.txt`
  JUDGED line; leaderboard κ=n/a n=0 cov 0.000; audit TOTALS judged=0 / parse_fail=62,103 —
  `phaseM_receipts/audits/mistral-v0.1-7b-q8_latest.audit.txt`) — a judge can complete a
  three-day run and say nothing.
- **phi-3-mini: 17 usable rows of 62,103 label-attempted** (62,086 parse-failures; a further
  2,103 rows mechanically invalid — `phaseM_receipts/audits/phi-3-mini-q8_latest.audit.txt`); its
  audit exit-1 is the degeneracy tripwire firing on that vanishing sample (line-pairing and
  universe accounting reconciled clean) — receipt committed as-is.
- **gemma1-2b coverage 0.450, claude-code 0.849** — partial mutes.
- **yi:34b-chat κ 0.035 at near-full coverage (0.995)** — fluent, confident, and uncorrelated
  with the panel.

## 7. Difficulty map, label-noise probe, exclusions

**Difficulty map (62 judges, SELECTION):** concordant-correct 682 rows (1.6%), split 40,728
(98.4%), **concordant-wrong 0** — the strict-unanimity stratum died at 62 heterogeneous judges
exactly as red-team N11 predicted; per-channel/family/epoch strata + the row-difficulty histogram
(mode ≈ 7–8 disagreeing judges, tail to 46) are in the committed report. Strata are NOT
comparable across subject families: membership counts only family-DISJOINT judges, so qwen rows
get ~36 voters vs granite's ~54, and unanimity is mechanically easier with fewer voters (qwen
concordant-correct 644/9,699 = 6.6% vs granite 30/24,500 = 0.12% — a ratio that is at least
partly structural); the histogram mixes voter counts the same way. The N11 note stands: do
NOT read the empty blind-spot stratum as "no shared blind spots" — the operative signal is below.

**Label-noise probe (K≥5 distinct families, seeded, stamp `localjudge2-analyze-20260728`):**
**116 candidate rows; 114 of them cross toward BREACH** (judges unanimously say BREACH where the
panel said NOT). The shared-local-bias direction is overwhelmingly false-alarm-side — consistent
with the S9 framing that these are AMBIGUOUS between panel error and shared local bias, with
shared-bias expected to dominate. Composition caveat: **108/116 candidates are granite-subject**
(93%, vs a 59% granite base rate in selection; remainder 5 mistral, 2 qwen, 1 claude-fable) — the
direction claim is effectively a single-subject-family sample. Worksheet:
`phaseM_receipts/labelnoise_worksheet.md`. Optional ~$2–3 panel re-adjudication is Josh-gated and
NOT run (§9).

**Exclusions applied as locked:** gpt-oss:120b — Phase-R parse gate 0/228 (reasoning consumed the
frozen n_predict=16; exclusion, not contract relaxation; recorded in `roster.txt` — no separate
Phase-R receipt is committed, registered as a gap). olmo3-7b — NOT a load-stall: its GGUF
chat template invokes `tools | tojson`, unparseable by the pinned ollama build (deterministic
llama-server exit 1, ×2); excluded (Josh-ratified 2026-07-28), olmo family covered by olmo2-7b.
Known stall-class attempt-once: gemma4:31b, llama3.3:70b (as locked). **New-pull G-A rows (prereg
§11):** nemotron-super-q4 G-A PASS 2026-07-15 — breach R=0.967/P=0.967 vs gates 0.90/0.80
(`roster.txt` header); gpt-oss failed its parse gate as above.

## 8. SIDEBAR — the pre-registered adoption gates

Selection leaderboard (all 62) is in the committed matrix report; freeze files `nominee.json` +
`ensemble_members.json` committed BEFORE any confirmation look (freeze commit `65c0938`,
confirmation receipts land later in `b9a4a94`; `matrix_report.txt` has a single-commit history,
never rewritten — the git ordering IS the blinding receipt). Post-exclusion only **10 of the 62**
completed judges are fully family-disjoint (`roster_selffamily.txt` is the pre-exclusion 12/64
table and still lists gpt-oss + olmo3):

- **Single nominee: qwen3.5_27b** — selection pooled 0.885 / BEM 0.877, cov 1.000
  (self-family-reduced n=31,711 — 23.7% of decided rows are dropped for any qwen judge, prereg
  NOTE 15). Per-family selection: granite 0.880, mistral 0.929, internlm 0.850.
- **Ensemble nominee (locked rule, no free search): k=3 unweighted** {qwen3.5_27b, 27b-sq,
  3.6-27b-sq} — selection pooled 0.892, but the all-qwen membership drops all votes on qwen rows →
  **selection coverage 0.766 = the red-team M2 coverage-crater scenario, visible pre-confirmation**
  (k=5 runner-up: 0.847, cov 1.000 — recorded in the receipt, not nominated). The κ-weighted k=3
  twin ties the nominee exactly (0.892/0.885, same members) and weighting is inert at every k —
  the tool's fixed candidate order (unweighted first) breaks the tie; a finding in itself:
  κ-weighting bought nothing.
- Best fully-family-disjoint single judge: **nemotron-super-q4 0.747/0.743 (n=41,410, cov 1.000,
  miss 0.179 / FA 0.046)** — the new-pull thesis (§8 row 7 of the prereg) gets a best-disjoint
  judge but NOT a gate-clearer on selection numbers; +0.220 over its Nano-30B sibling. GLM 0.717
  on this corpus (cross-arc anchor: LJ-1 measured 0.711 and the M1 verification re-run 0.698,
  three numbers on three populations — stable to ±0.02, not "unchanged").

**CONFIRMATION (single look each, binding — run 2026-07-28 after determinism + audits green;
receipts `confirmation_single.txt` / `confirmation_ensemble.txt`):**

- **single:qwen3.5_27b → G-B FAIL on exactly one gate.** Locked-vs-realized: pooled κ ≥0.80 →
  **0.862 PASS**; BEM κ ≥0.75 → **0.857 PASS**; recall sensitivity ≥0.75 → **0.738 FAIL**
  (n_breach=206); recall specificity ≥0.995 → **0.999 PASS**; coverage ≥0.98/0.97 →
  **1.000/1.000/1.000 PASS**; |κ−κ_strict| ≤0.03 → **Δ=0.000 PASS**; family granite **0.851
  PASS**, mistral **0.944 PASS** (gemma/internlm/phi below min-n, descriptive). Selection→
  confirmation shrinkage 0.885→0.862 (modest, expected selection optimism).
- **Two population disclosures on those numbers (results red-team):** (a) coverage 1.000 is of
  the **14,552 self-family-reduced holdout rows** — the 4,684 qwen-subject rows (24.4% of the
  19,236-row holdout) never enter the single judge's denominator, so single and ensemble coverage
  are NOT commensurable: both are trusted on none of the qwen quarter, the scorer just
  denominates it differently. Adopting this nominee would leave ~24% of the corpus needing
  another verdict authority. (b) The recall gate — the only failing one — is evaluated on the
  FULL-corpus recall subset (locked scorer behavior, not the holdout) with **no self-family
  exclusion applied: 160 of the 206 breach rows (77.7%) are qwen-subject, own-family for this
  judge**, and this judge is worse on own-family rows (own κ 0.843 vs disjoint 0.885) — so 0.738
  sits inside the S7 confound the rest of the arc excludes by construction. The gate is also
  underpowered: Wilson 95% CI ≈ [0.67, 0.79] spans the 0.75 bar. A family-disjoint recall
  recomputation would be a NEW analysis (exploratory or prereg-amended) — queued in §10, not run.
- **ensemble:k3:unweighted → G-B FAIL, the M2 coverage crater realized.** κ where it can vote:
  pooled **0.869** / BEM **0.865** (PASS); but coverage **0.756/0.780/0.704 FAIL** (all-qwen
  membership drops all votes on qwen-family rows — the same voteless qwen quarter as the single
  nominee, here counted in the denominator), recall sensitivity **0.130 FAIL** (only 46 breach
  rows retain votes), strict Δ **0.118 FAIL**. Accurate where it votes. The locked no-free-search
  rule was applied as written — the k=5 cov-1.000 runner-up was recorded at freeze time but not
  nominated, and is NOT scored on confirmation (that would be a second look).

**G-C verdict reproduction: DID NOT FIRE** — its locked condition (single-judge G-B confirmation
pass) is false. Ensemble G-C remains DEFERRED per the ratified §4 narrowing.

## 9. Integrity receipts, deviations, cost

**Audits:** 62/62 run verdict-blind BEFORE any official receipt; 61 PASS, 1 exit-1 (phi-3-mini
degeneracy tripwire, §6). Audit PASS is **structural** (line-pairing + universe accounting +
degeneracy tripwire) — coverage is informational at audit time and gated downstream by the scorer
(mistral-v0.1 PASSes structurally while emitting nothing). "Verdict-blind" describes the TOOL —
the analyst had already seen two provisional selection looks (disclosure below). **Determinism:** 20-coord fresh-cache
re-judge per model against the LJ-1 manifest (sha16 `24328bd9…` verified pre-ship), committed
`determ_ledger.txt` 62/62 DETERM-DONE, comparator receipt
`phaseM_receipts/determinism_report.txt`: **46/62 models 20/20 byte-exact (label+raw); all frozen
nominees, nemotron-super, and glm byte-stable.** The 16 non-exact models decompose as (hand-
tallied from the per-model MISMATCH blocks in the receipt): 13/25 diff-rows **label-identical**
(no scoring impact on those rows — 8 of them phi-3-mini's None→None degenerate garbage varying
byte-wise) + **12 single-row label flips** (1/20 each; 2/20 for nemotron-nano), the 25 diff-rows
spanning **12 distinct coordinates, 6 of them hit by multiple models** (frame_single:234 by 5
judges, cons_p4:826 by 4, frame_triple:1977 by 3; the label flips land on 8 of the 12). The
shared-coordinate signature says these are near-tie rows tipping under temp-0 llama.cpp numerics,
not cache corruption (which would scatter per-model). **10 of the 13 heavyweight-tier judges are
byte-exact**; yi:34b, internlm2.5-20b and laguna-xs.2 each move one row of 20 (nemotron-nano-30B
Q4: two), and the rest of the instability pools in small/degenerate judges. On mechanism:
co-residency is the one KNOWN difference between the arms (the determ pass kept up to 3 small
models loaded; Phase M was strictly one-resident) and is the leading candidate; reading
byte-determinism as a stable judge phenotype is the weaker, speculative interpretation. Scope
caveat either way: a 20-coordinate probe bounds little corpus-wide — 12 of the 20 manifest
coordinates were unstable in at least one model, and a clean 20/20 bounds a nominee's per-row
flip probability only below ~14% (95% upper).

**Disclosure (analysis order — read this before trusting the selection numbers):** two
provisional SELECTION looks (07-27, 07-28) preceded the audits; the official pass was regenerated
post-audit and is numerically identical to the provisional runs (diff = embedded paths only). The
provisional outputs were not retained, so that identity claim rests on the author's attestation,
not a committed diff.

**Disclosures (run):** nemotron-
super loaded on 2nd attempt after an infra fix (OLLAMA_LOAD_TIMEOUT + NVMe); the Phase-M driver
buffers the roster at launch, so a mid-run roster addition (nemotron-super, added 07-20) was
invisible until a driver re-run — cost ~4 idle hours on 07-27, no data impact (idempotent ledger).

**Cost (plain dollars):** this arc $0 API + ~2.5 weeks Sparky GPU.

| option | $/epoch | GPU/epoch | one-time build |
|---|---|---|---|
| frontier panel (status quo, LJ-1 §5) | ~$25–30 | — | — |
| single local judge (none cleared) | $0 | ~1 GPU-h order-of-magnitude (scaled from Phase M full-corpus wall-clock; unmeasured per-epoch) | — |
| k=3 ensemble (did not clear) | $0 | 3× single | emitter/deploy build, ~1–2 days eng (deferred) |

The label-noise re-adjudication option is separately priced at ~$2–3 (§7, Josh-gated).

## 10. Outcome → consequence (prereg §8)

**Realized outcome: nothing clears G-B on confirmation → NO ADOPTION; the frontier panel stays
the verdict authority.** Scope note: "closed negative" covers this roster + rubric; subjects
appear in both partitions (prereg §3), so confirmation is not an independent subject draw.

- **No "nothing clears" row is clearly indicated (per the results red-team).** Row 3's locked
  trigger is a prompt-fixable shared blind spot in the DIFFICULTY MAP — but that stratum is EMPTY
  (§7), and the operative N11 signal (the label-noise probe) points FALSE-ALARM-ward while the
  nominee failed conservative-side: the obvious liberal-ward rubric nudge would push INTO the one
  shared bias actually measured. The failing sensitivity gate is also underpowered (CI spans the
  bar) and computed on a 78%-own-family population (§8). Row 3 is therefore a HYPOTHESIS a
  follow-on prereg could test — with the family-disjoint recall recomputation as its first step —
  not the reading this evidence establishes.
- **Row 4 (FT-judge follow-on)** stays licensed to *draft* only if prompt adaptation is judged
  not viable; both follow-ons are draft-licenses, neither auto-runs. **Holdout status for that
  path:** the confirmation holdout took exactly the two pre-registered looks recorded here
  (single + ensemble), was never trained on, and remains the FT test set per prereg §5 — with the
  caveat that its κ is now known for these two specific candidates.
- **Row 5 (self-family):** replicates but **sign-flips by lineage** (§5) — documented; the
  family-matched-FT design-axis consequence carries the lineage caveat.
- **Row 7 (new-pull/200B thesis — tested at 120B, nemotron-super standing in for the 190–200B
  ceiling per the prereg's substitution):** UNSUPPORTED — best-disjoint (0.747) but never
  gate-grade; it did not clear where residents failed.
- **Ensemble row:** did not clear (coverage crater, §8) — the emitter/deploy build decision is
  moot; the k=5 shape is a candidate for a future prereg only.

Standing queue for Josh: (a) **family-disjoint recall recomputation** — new analysis on existing
mirrors, $0, minutes; needs an explicit exploratory label or a prereg amendment; the cheapest
decisive next fact given §8's population disclosure; (b) label-noise re-adjudication option
(~$2–3, Josh-gated, §7); (c) rubric-adaptation vs FT-judge follow-on choice — each needs a new
prereg, and the effort asymmetry is large: rubric adaptation ≈ $0 API + days of Sparky (re-judge
a handful of candidate judges on the SELECTION partition only), FT ≈ a training run on SELECTION
plus spending the holdout's single remaining clean shot; (d) nothing else — the adoption question
is closed negative for this roster + rubric.

## Pressure-test record (rule 12, both sides of usage)

Two independent reviewers ran post-draft, pre-ship (2026-07-28), each verified against the
committed receipts before folding: **legitimate-use** (5 MUST_FIX + 17 SHOULD_FIX; fold commit
`2cfa93e` — receipt pointers, population denominators named, ledgers committed, cost table,
glossary) and **red-team/statistical-leakage** (5 live MUST_FIX + 8 SHOULD_FIX; folded here —
coverage-denominator incommensurability, recall-gate self-family contamination 160/206,
determinism coordinate count corrected 8→12/6, §10 row-3 reading weakened to hypothesis,
distill claim downgraded to correlational). Inherent limitations registered, not fixed: no
committed Phase-R receipt for the gpt-oss parse gate; subjects appear in both partitions
(confirmation is not an independent subject draw); provisional-selection identity rests on
attestation; the 20-coordinate determinism probe bounds little corpus-wide.

## §11 checklist coverage

Difficulty strata pooled+channel+family+epoch ✅(report) · histogram ✅ · two-sided error all
judges ✅ · redundancy/pairwise + committed matrix ✅ · self-family table ✅ · selection
leaderboard ✅ · frozen nominees ✅ · confirmation locked-vs-realized ✅(§8) · recall sens/spec
✅(§8) · ensemble composition/combiner ✅ · G-C per-analyzer ✅ condition-not-met (§8) · ensemble
G-C-deferred flag ✅ · label-noise stratum ✅ · cost table ✅ · adoption decision ✅ NO ADOPTION
(§10) · new-pull G-A rows ✅(`roster.txt` header + §7) · gpt-oss parse gate ✅ · roster
self-family verification ✅(`roster_selffamily.txt`, pre-exclusion 12/64 → 10/62 live, §8) ·
determinism receipt ✅(§9, 46/62 byte-exact, nominees clean) · run ledgers ✅(`phaseM_ledger.txt`,
`determ_ledger.txt`).
