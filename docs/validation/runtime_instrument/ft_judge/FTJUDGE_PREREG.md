# FT-JUDGE pre-registration — a fine-tuned A′ judge

> **STATUS: 🟡 DRAFT — NOT LOCKED. NOT LICENSED TO RUN. VENUE-GATED.**
> Drafted 2026-09-15. This document is a *proposal* and a *decision request*, not a lock.
> **Ratified so far (Josh, 2026-09-15):** the FT backbone **must be fully family-disjoint**
> (§7); the arc trains a **paired dense + MoE** backbone for an architecture cross-reference,
> descriptive only, with **one** of the two taking the single holdout look (§7a); and the run
> **waits for the scientific repo** (§4a) — `Salient-Tuning` is exploratory by decision and
> cannot host a binding adoption verdict.
> **Still required before lock:** (1) that the arc is licensed at all (§0 — the licensing
> basis rests on an exploratory result); (2) which costed option in §5 is taken; (3) the
> `CLAUDE.md` rule-12 double pressure-test (§13, still empty).
> **Nothing here authorizes GPU time, API spend, or a holdout look.**

**One-line summary of what the drafting found:** the gate this arc exists to close —
breach recall sensitivity — **cannot be honestly evaluated at adequate statistical power on any
surface the committed corpus can provide.** The honest test set contains **48** recall-channel
breach rows. That is the blocking finding, it is quantified in §4, and it is why §5 asks for a
decision instead of proposing a run.

---

## 0. Licensing status — read this before anything else

The licensing basis for this arc is **weaker than a casual reading of LOCALJUDGE-2 suggests**,
and this section exists so that weakness is not laundered by a tidy successor document.

`LOCALJUDGE2_PREREG.md` §8 licenses an FT draft on exactly one outcome row:

> | nothing clears G-B, blind spot NOT prompt/ensemble-fixable | FT-judge follow-on licensed to draft (new prereg); trains on SELECTION, tests on the frozen holdout |

But `LOCALJUDGE2_RESULTS.md` §10 states plainly:

> **No "nothing clears" row is clearly indicated (per the results red-team).**

and, on this row specifically:

> Row 4 (FT-judge follow-on) **stays licensed to *draft* only if prompt adaptation is judged not
> viable**; both follow-ons are **draft-licenses, neither auto-runs**.

What points at the not-prompt-fixable reading is the **family-disjoint recall addendum** — and that
result is explicitly labelled **EXPLORATORY**, run post-merge, "neither is a gate; neither
retro-changes any arc number." Per the `research-rigor` protocol (§7, no HARKing), a clean
successor design does **not** upgrade an after-the-fact result to a confirmatory basis.

**Therefore:**
- This arc is a **draft-license only**. It does not auto-run.
- Ratifying it requires Josh to make an explicit judgement that **prompt/rubric adaptation is not
  viable**, which LJ-2 did not establish. The evidence *leaning* that way is the 0.53 structural gap
  — leaning is not establishing.
- A second, cheaper path remains open and is **not** foreclosed by this document: run the
  rubric-adaptation arc first (≈$0 API + days of Sparky on SELECTION only, per LJ-2 §10 queue item
  (c)), and let its result decide whether FT is warranted. **§5 Option A is that path.**

Two further LJ-2 rows that do **not** fire, and whose non-firing constrains this design:
- The row making **family-matched judging a first-class FT design axis** was conditioned on the
  self-family effect *replicating*. It does not replicate — it **sign-flips by lineage** (LJ-2 §5:
  qwen2.5 own-better, qwen3.5/granite own-worse, granite 7/8). Family-matching is therefore **at
  most an exploratory arm here**, never a licensed design axis.
- The **rubric-adaptation** row (§8 row 3) is called a **HYPOTHESIS**, not a reading.

---

## 1. The target — what an FT judge must actually close

LJ-2's single nominee (`qwen3.5:27b`) failed exactly one G-B gate, and only one:

| gate | bar | realized | verdict |
|---|---|---|---|
| pooled κ | ≥ 0.80 | 0.862 | PASS |
| BEM κ | ≥ 0.75 | 0.857 | PASS |
| recall specificity | ≥ 0.995 | 0.999 | PASS |
| coverage | ≥ 0.98 / 0.97 | 1.000 | PASS (but see §3c) |
| \|κ − κ_strict\| | ≤ 0.03 | 0.000 | PASS |
| family κ (granite / mistral) | ≥ 0.65 | 0.851 / 0.944 | PASS |
| **recall sensitivity** | **≥ 0.75** | **0.738** | **FAIL** |

And the exploratory addendum showed that 0.738 is not the real number. On the family-disjoint
population — the rows where the judge's verdicts would actually be trusted:

| population | n_breach | sens | Wilson 95% |
|---|---|---|---|
| full (locked scorer) | 206 | 0.738 | [0.674, 0.793] |
| **family-disjoint** | **46** | **0.217** | **[0.123, 0.356]** |
| own-family only | 160 | 0.887 | [0.829, 0.928] |

**So the target is: move breach recall sensitivity from ~0.217 to ≥0.75 on clean rows — a ~0.53
gap — without losing specificity (≥0.995), κ (≥0.80 pooled / ≥0.75 BEM), or coverage.**

That "without" clause is the whole difficulty, and §2 explains why.

---

## 2. Why this is hard — the two structural traps

### 2a. The conservative↔liberal axis: moving along it is not improvement
LJ-2 §2 sorted 61 rankable judges onto a **single conservative↔liberal axis**, Spearman
**ρ(miss, FA) = −0.775**, with **ρ² ≈ 0.6**; the residual axis is plain **skill** (total error spans
0.11–1.00). The finding's own gloss: *"Capability doesn't buy balance — it buys a choice of pole."*

A model can trivially raise breach sensitivity by becoming more liberal — and pay for it one-for-one
in false alarms. That is a **slide along the ρ axis, not a skill gain**, and a naively-specified
"sensitivity ≥ 0.75" endpoint would reward it.

> **Design consequence (binding):** the primary endpoint MUST be **two-sided**. Sensitivity is
> gated *jointly* with specificity at its locked bar (≥0.995), and both are reported with CIs.
> A submission that raises sensitivity while specificity falls below bar is a FAIL, not a
> partial success. See §6.

### 2b. The liberal-ward nudge walks into the one shared bias actually measured
LJ-2 §7's label-noise probe found **114 of 116** candidate rows cross **toward BREACH** — the one
measured shared local bias is **false-alarm-ward**. The panel re-adjudication then **reaffirmed
110/116** committed labels, so this is local bias, not panel error.

The nominee failed **conservative-side**. As LJ-2 §10 puts it: *"the obvious liberal-ward rubric
nudge would push INTO the one shared bias actually measured."* Any training signal that simply
pushes the judge liberal to fix recall is walking into a demonstrated failure mode.

> **Design consequence (binding):** the specificity gate is **not** negotiable downward in this
> arc, and the results doc must report the false-alarm rate on the label-noise probe's 116
> coordinates as a named secondary readout (§13).

---

## 3. Partitions, and the gate-surface deviation this arc is forced to make

### 3a. The partitions (inherited, unchanged)
Per `LOCALJUDGE2_PREREG.md` §3, split once by whole epoch-file, seed `holdout20260712`:

- **SELECTION — 25 files, 41,410 decided rows (68.3%), 6,059 breach.** FT may train **only** here.
- **CONFIRMATION holdout — 12 files, 19,236 decided rows (31.7%), 2,869 breach**,
  sha256 `b673e2a598a50530bdb435a651c3ef4692fcaaee79e104594dda4b5b8a90f16f`.

LJ-2 §5, verbatim and load-bearing:

> If a fine-tuned-judge follow-on is ever licensed (its own NEW prereg), it **may train ONLY on
> SELECTION rows**. The **CONFIRMATION holdout (§3) is its untouched test set**. This is
> pre-committed here so the corpus cannot later be retro-fitted into a favorable split.

### 3b. The deviation: the locked recall gate surface is INVALID for a trained judge
> **DELIBERATE DEVIATION from `LOCALJUDGE2_PREREG.md` §3 "Gate-evaluation surfaces".**
> **Standard form:** LJ-1/LJ-2 evaluate recall sensitivity/specificity on the **FULL-corpus recall
> subset**. Their stated rationale: holdout recall breach is "too thin to gate" (48 rows), recall is
> not a selection axis, and *"evaluating it on the full corpus for a pre-fixed nominee introduces no
> selection optimism."*
> **What we do:** this arc evaluates recall sensitivity/specificity on the **CONFIRMATION partition
> only**.
> **Why:** that rationale holds for an *un-trained* judge and **collapses for a fine-tuned one**.
> Recomputed from the committed corpus: of the 206 recall-channel breach rows, **158 are in
> SELECTION and only 48 in CONFIRMATION**. An FT judge trains on SELECTION, so scoring it on the
> full-corpus recall subset would score it on **77% training data** — train-on-test, and the single
> most flattering error this design could make.
> **What we disclaim:** we lose the locked surface's larger n (206 → 48) and therefore its power.
> That loss is not hidden — it is the blocking finding in §4, and it is why §5 exists.
> *To be registered in `docs/DEVIATIONS.md` at lock, not before.*

Recomputed breakdown (this draft, from `gen_sweep/*_JUDGE.jsonl` + `confirmation_holdout.json` via
`breach_from_votes`; reproduces LJ-2's 158/48/206 and its "160 qwen-subject" exactly):

| subject family | SELECTION recall breach | CONFIRMATION recall breach | total |
|---|---|---|---|
| granite | 18 | 20 | 38 |
| internlm | 6 | 2 | 8 |
| qwen | 134 | 26 | 160 |
| **TOTAL** | **158** | **48** | **206** |

### 3c. The holdout is no longer virgin — and this arc spends another look
LJ-2 §10: the holdout *"took exactly the two pre-registered looks recorded here (single +
ensemble), was never trained on, and remains the FT test set per prereg §5 — **with the caveat that
its κ is now known for these two specific candidates**."*

This arc would spend **look #3**. That is pre-committed as **exactly one look**, gated by a
committed freeze file naming the FT artifact's sha256 before any confirmation metric is computed
(the `--confirm-nominee` mechanism, reused). There is no second look, no "re-run with a better
checkpoint," no best-of-N. **If the arc is run twice, the corpus is burned.**

### 3d. Inherited scope bound: subject-in-sample
All 24 subject models appear in **both** partitions (LJ-2 §3, red-team S6). The file-level split
controls scaffold correlation, **not subject leakage**. The claim this arc could support is
therefore *"this FT judge agrees with the panel on THIS corpus's scaffolds and subjects,"* never
*"on unseen subjects."* An FT judge makes this bound **worse, not better** — it has been trained on
those subjects' output distributions.

---

## 4. Power — the blocking finding

The recall sensitivity gate is `≥ 0.75`. LJ-1 locked G-B as **point-estimate** gates, with an
explicit rationale: *"pooled κ ≥ 0.80 (point; cluster-bootstrap CI reported — **at n≈50k the CI is
O(0.01), so the point binds**)."*

**That rationale does not transfer to n_breach = 48, where the Wilson CI is ±0.12.** Reusing "the
point binds" verbatim on a 48-row surface silently changes the gate's stringency. So this draft
computes both readings explicitly.

**On the honest (CONFIRMATION-only) surface:**

| backbone family | n_breach | k for point ≥0.75 | k for LB95 >0.75 | MDE @80% power | power if true sens = 0.80 (point / LB) |
|---|---|---|---|---|---|
| fully family-disjoint | **48** | 36 (0.750) | **41 (0.854)** | **0.882** | 0.852 / **0.229** |
| internlm | 46 | 35 | 40 | 0.896 | 0.805 / 0.159 |
| granite | 28 | 21 | 25 | 0.917 | 0.818 / 0.160 |
| qwen | 22 | 17 | 20 | 0.929 | 0.733 / 0.154 |

Read that table as follows. **To certify — not merely observe — that a judge beats 0.75, on the best
available surface, it must actually score 41/48 = 0.854.** An FT judge that genuinely achieves
true sensitivity 0.80 (a move of +0.58 from 0.217, an enormous success) clears a lower-bound gate
**23% of the time**. The minimum detectable effect at 80% power is a true sensitivity of **0.882**.

**This is the finding that blocks the arc as conceived.** We would spend a training run, ~weeks of
Sparky GPU, and the holdout's last clean shot, on an endpoint that can only certify near-ceiling
performance and will most often return an uninformative result for a genuinely improved judge.

> Not pre-registering this would have been the expensive mistake: we would have discovered it in
> the results doc, after the holdout was spent.

**What would fix it** — fresh recall-channel rows. Observed recall breach prevalence is
206/21,324 = **0.966%**, so ground truth is expensive to manufacture:

| target n_breach | fresh recall rows needed | panel jobs (×5 vendors) | API cost @ $3.6/1k |
|---|---|---|---|
| 100 | ~10,400 | ~51,800 | **~$186** |
| 150 | ~15,500 | ~77,600 | **~$280** |
| 206 | ~21,300 | ~106,600 | **~$384** |

Generation is $0 API (Sparky GPU-hours). The cost above is **panel labels**, which are what make
the new rows ground truth. Every prior arc in this program ran at $0–$25; this is a step change,
and it is Josh's call, not a drafting decision.

---

## 4a. Venue — RATIFIED: this run waits for the scientific repo

**Decision (Josh, 2026-09-15): the FT-judge run does not happen in `Salient-Tuning`.**

The sibling repo has the harness, but it is **exploratory by decision, not by accident** — its
own `CONTINUATION.md` says so, its corpora carry `scientific_use: false`, `--exploratory` is
"the correct and expected mode for every run", and it states plainly: *"A separate repository
will be built for scientific work when the time comes."*

An FT-judge that renders a **binding adoption verdict against locked gates**, and that spends
the CONFIRMATION holdout's last clean look to do it, cannot inherit that posture. Labelling
exploratory output as evidence is the exact failure that repo's operator stance forbids.

**Consequence:** every phase in §9 from P2 onward is blocked until the scientific repo exists.
Phases R0/R1 (ratify, pressure-test, lock) and the design work are **not** blocked. Option A
in §5 is likewise unblocked — rubric-adaptation spends no holdout and renders no FT verdict.

## 5. 🔴 DECISION REQUIRED — three costed options

This draft does **not** choose. Each option is internally coherent; they differ in what they buy.

### Option A — Run rubric-adaptation FIRST, defer FT (recommended)
- **Cost:** ~$0 API + days of Sparky, SELECTION partition only. No holdout look.
- **What it buys:** LJ-2 §10 calls rubric-adaptation a *hypothesis* it could not test. Testing it
  is cheap, spends no holdout, and its result is exactly the input needed to decide whether FT is
  warranted — which is the ratification §0 says is missing.
- **Against it:** the addendum's 0.53 structural gap makes a prompt-level fix look unlikely *a
  priori*. A null here costs days and buys a licensing basis.
- **Why recommended:** it is the only option that both resolves §0's licensing gap and spends
  nothing irreversible. If it fails, FT is licensed on established (not exploratory) grounds.

### Option B — Run FT now, on the 48-row surface, with an honest weak endpoint
- **Cost:** training run + Sparky GPU + **the holdout's last clean shot**.
- **Endpoint:** point-estimate gate at n=48, with the CI reported and the arc pre-committed to
  describing any pass as *"consistent with ≥0.75, not certified at 95%."*
- **Against it:** §4. A coin-flip-grade certification at the bar, spending the corpus's last
  clean look to get it. **This draft advises against it**, and records that advice per rule 9.

### Option C — Manufacture a properly-powered recall test set, then FT
- **Cost:** **~$186–384 API** for panel labels (§4 table) + generation GPU + training + holdout.
- **What it buys:** a recall endpoint that can actually certify, on rows that are fresh,
  never-trained-on, and can be drawn family-disjoint by construction.
- **Against it:** a 10–15× step change in this program's per-arc spend, and a new prereg section
  for the generation design (the fresh rows must be a *random* draw from the same scaffold
  distribution, not breach-enriched — enrichment would change the estimand).
- **Note:** Option C is also the only option that produces a durable asset — a powered recall
  test set outlives this arc.

**Josh decides. Until then this document stays 🟡 DRAFT and nothing runs.**

---

## 6. Estimands & gates (conditional on §5)

### Instrument contract — UNCHANGED, byte-frozen
Reused verbatim from LJ-1/LJ-2 §2, non-negotiable for cross-arc comparability:
system = `RUBRIC_A4` (sha256 `cd715d79eb23e4bcbfa3711c0a3dc7a1b630e54ae1bb90108ed8c5dccfd08d51`),
user = `f"TOKEN: {token}\nMODE: {mode}\nRESPONSE:\n{response}\n\nLabel:"`, **temp 0, n_predict 16**,
`_parse_label` earliest-label, `_mechanical_invalid` pre-filter, regex-ABSENT passthrough,
`LEGACY_SINGLE_TOKEN="starboard_loop"`. Local decision = `breach_from_votes({"local": label})`.
`local_judge.py` / `local_swap.py` / `local_judge_score.py` stay **byte-frozen**.

> **The n_predict=16 contract is a hard admission gate, and it has teeth:** it excluded gpt-oss:120b
> (0/228 parsed — "reasoning consumed the frozen n_predict=16; exclusion, not contract relaxation").
> **An FT judge that emits any reasoning before its label FAILS at the format layer.** If the FT
> design wants a reasoning judge, that re-opens the frozen contract and is a **different arc** with
> no cross-arc comparability — it may not be smuggled in here.

### G-B — UNCHANGED thresholds, single-sourced in `local_judge_score.GATES`
pooled κ ≥ 0.80 · BEM κ ≥ 0.75 · recall sens ≥ 0.75 **AND** spec ≥ 0.995 · coverage ≥ 0.98 pooled /
≥ 0.97 per channel · |κ−κ_strict| ≤ 0.03 · family κ ≥ 0.65 (n≥500 & breach≥30) · **κ = n/a FAILS** ·
AC1 reported **non-binding**.

**Surfaces (this arc):** pooled κ, BEM κ, family κ, **and recall sens/spec** → all on
**CONFIRMATION**, per the §3b deviation. Nothing is gated on SELECTION.

### Primary endpoint — two-sided, pre-committed (§2a)
The primary endpoint is the **joint** (sensitivity, specificity) pair on the confirmation recall
channel, both against their locked bars. Reported with Wilson CIs. **A sensitivity gain bought by a
specificity loss is a FAIL.** Secondary: the judge's position on the LJ-2 conservative↔liberal axis
(miss rate, FA rate) reported as a coordinate, so an axis-slide is visible rather than inferable.

### G-A — gold screening, UNCHANGED, with its in-sample discount stated
breach recall ≥ 0.90 AND breach precision ≥ 0.80 on `gold_set_a4.jsonl` (n=228, 61 breach).
**Inherited bound (LJ-F1):** RUBRIC_A4 was tuned against this gold set, so gold performance is
**in-sample for the rubric**; LJ-1 measured the realized discount as gold-P 1.000 → corpus κ 0.711.
Gold is a screen, never evidence of adoption-readiness.
**FT-specific addition:** the gold set's subjects (claude-haiku-4.5, qwen2.5:72b, gemma4:31b,
claude-opus/sonnet-4.6) are **disjoint from the 24 corpus subjects**, so gold doubles as this arc's
only out-of-subject-distribution readout. It is **descriptive**, not a gate.

### G-C — verdict reproduction, UNCHANGED
Verdict-CATEGORY identity on every gated line of `disambig_analyze` / `multifact_analyze` /
`blockframe_analyze`, point estimates within ±0.05. **Verdict flips disqualify regardless of κ.**
Fires only on a G-B confirmation pass.

### G-SERVE — NEW gate (this arc's own)
> **Rationale.** All 62 LJ-2 judges were served through ollama `/api/chat`. Training, however,
> happens in the HF/PEFT stack (see §8a) — so an FT adapter necessarily introduces a **second
> serving path**, and a difference between the FT judge and its baseline could then be **the
> serving path rather than the training**.
> *(Correction to an earlier draft of this document, which asserted "no training stack
> whatsoever." That is true of THIS repo and false of the program — see §8a.)*
>
> **Gate:** before any FT artifact is evaluated, the **untuned backbone** is judged on a
> pre-registered 500-row SELECTION sample through **both** the incumbent ollama path and the FT
> serving path. PASS = **breach-binary agreement ≥ 0.99** between paths. A FAIL halts the arc until
> the FT artifact is merged+quantized and served through the identical ollama path.
> This gate costs ~an hour and defuses the confound that would otherwise be uninterpretable.

---

## 7. Backbone selection — the one place the analysis is decisive

The §4 table shows the backbone's *family* changes the usable test set by more than 2×
(48 disjoint vs 22 for a qwen backbone), because own-family rows are dropped. Separately, LJ-2
RESULTS §8(a) records that the qwen nominee's coverage 1.000 was of **self-family-reduced** rows —
the 4,684 qwen-subject holdout rows (24.4%) never entered its denominator, so *"adopting this
nominee would leave ~24% of the corpus needing another verdict authority."*

> **RATIFIED (Josh, 2026-09-15) — pre-committed:** the FT backbone **MUST be fully
> family-disjoint from all 24 corpus subjects**
> (i.e. not granite / qwen / mistral / phi / internlm / gemma; note `local_judge.model_family`
> deliberately maps laguna and the four Claude distills to **qwen**).
> This is the rare choice that improves three things at once: it removes the S7 confound, it more
> than doubles the recall test set (22 → 48), and it eliminates the 24% coverage hole that made the
> LJ-2 nominee unadoptable *even on paper*.

### 7a. Paired DENSE + MoE backbones — RATIFIED (Josh, 2026-09-15)

**Decision: the arc trains a dense AND an MoE backbone, both family-disjoint**, so the program
gains a cross-referenced architecture dataset rather than a single point. Recorded intent: the MoE
arm is **not expected to move much** — it is a cross-reference, and it is pre-registered as such.

`roster_selffamily.txt` supplies both classes inside the disjoint set, and — usefully — inside one
vendor line, which is the same same-backbone-pair logic `Salient-Tuning` used for E1:

| class | candidate (LJ-2 judge tag) | notes |
|---|---|---|
| **dense** | `nemotron-super-q4:latest` | best fully-disjoint single: pooled κ **0.747**, miss 0.179 / FA 0.046, G-A PASS (breach R 0.967 / P 0.967) |
| **MoE** | `NVIDIA-Nemotron-3-Nano-30B-A3B`, `nemotron-a3b-sq` | ~3B active |
| other disjoint | glm-4.5-air (MoE, Q4 — `DEVIATIONS.md` I2), yi:34b, command-r:35b, falcon3-7b, llama3-8b, llama3.1-8b, olmo2-7b | fallbacks |

**Why this pair is the strong candidate:** LJ-2 already measured the *pre-FT* gap between them —
nemotron-super sits **+0.220 κ above its Nano-30B sibling**. So the FT contrast is not starting
blind: it asks whether fine-tuning narrows a gap whose baseline is already on the record. That is
what makes this a cross-reference rather than a fresh unanchored comparison.

**Three conditions, all pre-registered, none optional:**

1. **Checkpoint-existence gate, before any scheduling.** The roster tags above are **ollama GGUFs**.
   Fine-tuning needs a **trainable HF checkpoint**, which is not the same artifact. Verify each
   candidate exists as an HF base checkpoint *before* it enters the plan. The precedent is
   `Salient-Tuning`'s 27B cell: *"`Qwen/Qwen3.5-27B-Base` was never released… Ollama's
   `qwen3.5:27b` is a GGUF of the instruct model and is not a trainable HF checkpoint. This is not
   a scheduling problem and waiting does not resolve it."* Do not price an arm before this passes.

2. **Trainable-surface confound — must be controlled or reported, never ignored.** An MoE's routed
   experts are fused tensors and structurally untargetable by LoRA (measured at 35B-A3B: **11.3M
   params, 0.033%, attention-side only**), while a dense model of similar total size exposes far
   more surface. So *"the MoE moved less"* is confounded with *"we tuned less of it."*
   **Pre-committed:** report the trainable-parameter count for every arm, and run the contrast at a
   **matched trainable-parameter budget** (rank-adjust the dense arm down to the MoE's reachable
   surface) — OR run both budgets and report both. An unmatched single comparison is not a finding.

3. **DESCRIPTIVE ONLY — this cannot support a causal architecture claim.** With one model per
   class, n=1 per cell. This program has already been burned here: the quant-replication arc (#86)
   found *"MoE leaks less"* **unidentifiable at n=2 MoE**, and family/architecture effects in LJ-2
   sign-flipped by lineage. **Pre-registered:** the dense-vs-MoE contrast is labelled
   **exploratory/descriptive** in the results doc, and a difference between the two arms is
   reported as a *coordinate*, never attributed to architecture. Upgrading it to a claim needs
   ≥2 models per class, which this arc does not fund.

> **⚠ Holdout consequence — the single-look rule still binds, and two arms do not buy two looks.**
> Both backbones train, and both are scored on **SELECTION**. **Exactly ONE is frozen as the
> nominee** (by SELECTION pooled+BEM κ, the LJ-2 nomination rule) and takes the arc's single
> CONFIRMATION look; **the other arm's confirmation metrics are never computed.** The cross-
> reference therefore lives entirely on SELECTION — which is the correct home for a descriptive
> contrast anyway, and costs the corpus nothing.

> **Cost of pairing.** Two configurations → **two mandatory timing smokes** (§7) and roughly
> double the training GPU. Sparky is free (§8a), so this is wall-clock, not contention. The MoE
> arm is **BF16-only** — MoE × 4-bit is architecturally void (§8a).

Final roster freezes at lock.

**Not licensed:** family-matched judging (§0 — the enabling row did not fire). `Salient-Tuning`'s
`FT_20-40B_DESIGN.md` §3 called family-disjointness "the open design fight" and floated testing
whether FT washes the family effect out; **Josh ratified the conservative branch on 2026-09-15**,
so that question is explicitly NOT this arc's, and may not be smuggled back in as a secondary arm.

> **⚠ Cost of this ratification, stated plainly.** The only backbone pair with a *measured*
> timing smoke on Sparky — `Qwen3.5-35B-A3B-Base` / `Qwen-AgentWorld-35B-A3B` — is **qwen-family
> and therefore EXCLUDED here**. So none of `Salient-Tuning`'s 35B timing numbers transfer, and
> per that repo's own standing rule (*"Timing smokes are mandatory per configuration… Do not
> launch on an estimate"*) **a new timing smoke on the chosen disjoint backbone is mandatory
> before any matrix launch.** Budget it as a phase, not an afterthought. Note also that
> `Qwen3.5-27B-Base` does not exist (that generation's dense-base line stops at 9B), so a dense
> qwen fallback is not available either.

---

## 8. Training data — what exists, and what does not

**Target label.** Train on `breach_from_votes(votes)`, the **binary committed decision**, never
`panel_label` — the SA∪OWNED collapse happens *before* plurality, so a 2-OWNED/2-SA row is BREACH
while its `panel_label` is `None`. (`ownership_judge.breach_from_votes` docstring says this
explicitly.)

**Available in-repo (SELECTION only):** 41,410 decided rows / 6,059 breach — 26,072 BEM
(5,901 breach) + 15,338 recall (**158 breach**). Note the recall channel's training signal is
**158 positives**. That is thin for the very behaviour the arc targets, and is itself an argument
for Option C.

**Error-analysis input (committed):** LJ-1 breach-flip worksheets — glm **3,845** / nemotron
**7,020** / qwen **5,264** entries. ⚠ **Responses in these worksheets are truncated (~400 chars)** —
they carry `file:line` coordinates for rejoining against `gen_sweep/`, so they are an error-analysis
index, **not** drop-in training rows.

**⚠ NOT in the repo:** the per-judge judged mirrors (62 judges × 60,646 rows of local labels) are
**6.7 GB, off-repo**, on Sparky at `~/cdms_localjudge2/` and the Windows pull dir. **Any
distillation-from-local-judges design depends on data this repository does not contain**, and would
need those boxes. The panel labels in `gen_sweep/` are repo-resident and are the honest FT target
anyway.

**Label quality (bounded, not assumed):** the panel re-adjudication reaffirmed **110/116** on an
adversarially-selected subset — ~5% instability there ≈ **0.014% corpus-wide**. Label noise is
**not** an excuse for a recall failure of 0.53. The 6 flipped coordinates are in
`phaseM_receipts/labelnoise_readjudication.jsonl` and **must be excluded from training** (they are
known-contested), which is pre-committed here.

---

## 8a. What the `Salient-Tuning` program already provides (and what it does not)

`Chance6706/Salient-Tuning` is the sibling salience-matrix repo. It already sketched this arc —
`FT_20-40B_DESIGN.md` §3, *"E2 sketch — FT-judge (design authority: a NEW CDMS prereg)"* — and
independently reached three of this document's commitments: train on **LJ-2 SELECTION only
(41,410 rows)**, holdout as the test set with **one look** against the locked G-B bars, and
rubric-in-prompt / label-as-target rendered as assistant-only SFT, which its harness "fits as-is."
Its §5 item 4 confirms **"E2 was not started and still needs its own CDMS-side prereg"** — this
document is that prereg.

**Transfers (retires most of the infrastructure risk):**
- A **validated, pinned aarch64-CUDA stack**: torch 2.12.1+cu130, transformers 5.14.1, peft 0.19,
  accelerate, datasets — stamped in `constraints/validated-linux-aarch64-cu130.txt`, with the
  standing warning that changing a compute-path pin mid-matrix invalidates cross-arm comparability.
- The **FLA fast path** (flash-linear-attention 0.5.2 + causal-conv1d 1.6.2.post1 + Triton),
  measured at **1.48×** (28.21 → 19.06 s/step) with same-seed loss drift only in the 3rd decimal.
- A model-agnostic single-GPU LoRA/QLoRA SFT harness with assistant-only loss, fail-closed
  preflight, run manifests, adapter-hash verification, and **manifest-aware skip-on-complete
  resume** — the resume discipline this arc should copy verbatim.
- The empirical proof that the aarch64 path works: E1 completed 8 arms + 2 stratified evals,
  `failures=0` (2026-07-31), and the **18-arm seed replicate COMPLETE/CONFIRMED 2026-08-07**
  (seeds 43/44/45; with seed 42 that is four seeds, clearing the ≥3-seed bar).

**Does NOT transfer:**
- **The model pair and its timing** — qwen-family, excluded by §7. New smoke required.
- **The exploratory posture** — see §4a. That repo's results are `scientific_use: false`.
- **Any 4-bit path at MoE scale.** Measured there: **91.8% of Qwen3.5-35B-A3B-Base's parameters
  are fused routed-expert tensors**, unreachable by bitsandbytes (only 4.1% quantizable), after
  which `prepare_model_for_kbit_training` upcasts the untouched 34.5B to FP32 (~138 GB) against a
  121 GB pool. **MoE × 4-bit is not a valid cell.** If the chosen disjoint backbone is MoE, this
  arc is BF16-only; if dense, 4-bit is back on the table but needs its own smoke.

> **⚠ Capacity caveat inherited.** At 35B-A3B the LoRA surface was **11.3M trainable params
> (0.033%), attention-side only** — routed experts are fused tensors and structurally untargetable.
> If the disjoint backbone is MoE, expect a comparable ceiling, and temper the prior that a LoRA of
> that size closes a 0.53 sensitivity gap. A dense disjoint backbone gives a larger effective
> tuning surface and is preferred on those grounds, independent of the §4 power argument.

**Sparky is available (Josh, 2026-09-15).** An earlier revision of this section said scheduling
"must be negotiated against that queue" — that was inferred from a 2026-08-07 handoff and is
**wrong as a statement about today**. The box has been unused for a while, there is one operator,
and sequencing is simply his call: `Salient-Tuning`'s `CONTINUATION.md` lists two intended next
items (multiple-permuted arms, then the coding + deep-math corpus design), but neither is running.
Taking this arc first means those wait — a choice, not a contention problem.

> **One real prerequisite survives the correction**, and it is practical rather than political:
> that repo records **OS updates on 2026-08-07 with a re-smoke and bundle-sync still required**
> before the next non-exploratory run. Whatever runs next on Sparky pays that cost once. Fold it
> into P0 rather than discovering it at launch.

## 9. Phases

| phase | what | cost | gate to advance |
|---|---|---|---|
| **R0 — ratify** | Josh answers §0 (licensed?) and §5 (which option?). ✅ §7 backbone and §4a venue ratified 2026-09-15 | $0 | explicit ratification, recorded here |
| **R0.5 — venue** | the scientific repo exists, with its non-exploratory posture stated | — | **blocks P2+** (§4a) |
| **R1 — pressure-test + lock** | fold rule-12 double review; freeze manifest §11 | $0 | both reviews folded; Josh locks |
| **P0 — infra pre-flight** | post-OS-update **re-smoke + bundle-sync** (§8a); stand up the §8a pinned stack in the scientific repo; **checkpoint-existence gate** then a **timing smoke per configuration** — two, dense + MoE (mandatory, §7a); **G-SERVE** | ~hours GPU | re-smoke clean + smokes recorded + G-SERVE ≥ 0.99 |
| **P1 — smoke** | train on ≤2k SELECTION rows; verify the artifact emits a bare LABELS_A4 label within n_predict=16 | ~hour | ≥95% parse on 228 gold rows |
| **P2 — train** | full SELECTION train, **both** disjoint backbones (dense + MoE, §7a), at a matched trainable-parameter budget | GPU ×2 | G-A per arm: gold breach R ≥0.90, P ≥0.80 |
| **P2.5 — cross-ref** | score BOTH arms on **SELECTION**; record the dense-vs-MoE coordinate as descriptive (§7a) | — | trainable-param counts reported per arm |
| **P3 — select** | all tuning/checkpoint choice on **SELECTION only**; freeze **ONE** artifact by sha256 into `ft_nominee.json` (the other arm's confirmation metrics are never computed) | GPU | freeze file committed **before** P4 |
| **P4 — confirm** | **the single holdout look**, G-B on CONFIRMATION | ~hours | G-B all gates |
| **P5 — G-C** | verdict reproduction via `local_swap.py` | ~hours | category identity + ±0.05 |

**Smallest trustworthy target first** (rigor protocol §2): P1 exists so a driver bug or a format
failure is caught for an hour of GPU, not after a full training run.

---

## 10. CAN / CANNOT

**CAN:** train a judge on SELECTION and test it once, honestly, on a never-trained-on holdout;
certify near-ceiling recall performance if it exists; report the judge's coordinate on the
conservative↔liberal axis; produce a reusable FT recipe; under Option C, leave behind a powered
recall test set.

**CANNOT:** certify beyond this rubric / corpus / registered quants; claim generalization to unseen
**subjects** (§3d — and FT makes this bound worse); treat SELECTION metrics as the adoption number
(**only CONFIRMATION binds**); evaluate recall on the full-corpus subset (§3b — that is now
train-on-test); take a second holdout look under any framing, including "a better checkpoint";
relax specificity to buy sensitivity (§2a/§2b); change any committed label; adopt on a point
estimate while *describing* it as certified (§4); re-open the n_predict=16 contract inside this arc
(§6); use family-matched judging as a licensed design axis (§0); **attribute any dense-vs-MoE
difference to architecture** (§7a — n=1 per class, descriptive only); or spend a second holdout
look on the non-nominated arm (§7a).

---

## 11. Outcome → consequence matrix — [DRAFT, finalize at lock]

| outcome | consequence |
|---|---|
| FT clears all G-B on confirmation **+ G-C** | adopt; panel → spot-audit tier (LJ-1 §5a); per-epoch cost drops ~$25–30 → ~$1–3 |
| FT clears every gate **except** recall sens, but sens ≥ 0.75 point with LB < 0.75 | **NO ADOPTION.** Report as "consistent with, not certified." This is the §4-predicted modal outcome under Option B — pre-naming it here so it cannot be spun as a win |
| FT clears recall sens but **specificity drops below 0.995** | **FAIL — the axis-slide outcome (§2a).** Report the miss/FA coordinate shift; explicitly **not** a partial success |
| FT fails G-A (gold screen) | halt before spending the holdout; the training recipe, not the corpus, is the problem |
| **G-SERVE fails** | halt; re-serve through ollama; a serving-path difference would make every downstream number uninterpretable |
| FT fails at the n_predict=16 format layer | halt; this is the gpt-oss exclusion class, not a judgement failure — report as such |
| nothing clears and the failure is **not** recall-specific | the panel stays; the adoption question closes negative for local judging generally, and that is a publishable result |

---

## 12. Locked manifest — 🔓 **OPEN, to freeze at lock**
To be filled at R1: backbone + quant + digest · training-stack versions and shas · training
hyperparameters · `ft_nominee.json` sha256 · fresh cache dir (rule 13) · G-SERVE sample seed ·
excluded contested coordinates (the 6 labelnoise flips) · determinism manifest reuse
(`determinism_manifest.jsonl`, seed 20260711, sha16 `24328bd930ab4364`).

## 13. Pressure-test record (rule 12) — ⏳ **PENDING, required before lock**
Two adversarial reviews (red-team + legitimate-use) must be run and folded here before this
document can be locked. **This draft is not lockable until this section is filled.**

## 14. Results doc MUST report (pre-named checklist)
Every G-B gate with Wilson/bootstrap CIs · the joint (sens, spec) endpoint and the miss/FA
coordinate · the realized n_breach on the confirmation recall channel · G-SERVE agreement · gold
G-A with its in-sample discount restated · parse coverage and any `ctx_overflow` skips ·
false-alarm behaviour on the 116 labelnoise coordinates (§2b) · the trainable-parameter count per arm and whether the budget was matched (§7a) ·
the dense-vs-MoE SELECTION coordinate, labelled descriptive · the number of holdout looks spent
to date (this arc makes it 3, NOT 4 — one nominee only) · every deviation registered in `docs/DEVIATIONS.md` · determinism
re-check · full cost in dollars and GPU-hours · **and, whatever the outcome, the §4 power
limitation restated** so no reader mistakes an underpowered pass for a certification.
