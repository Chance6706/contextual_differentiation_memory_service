# FT-JUDGE pre-registration — a fine-tuned A′ judge

> **STATUS: 🟡 DRAFT (rev 2) — NOT LOCKED. NOT LICENSED TO RUN. VENUE-GATED.**
> Drafted 2026-09-15; **rev 2 same day**, after the rule-12 double pressure test (§15).
> **Ratified (Josh, 2026-09-15):** backbone must be **fully family-disjoint** (§7); the arc trains a
> **paired dense + MoE** for a descriptive architecture cross-reference, with **one** arm taking the
> single holdout look (§7); the run **waits for the scientific repo** (§6); and backbone choice is
> settled by a **measured zero-shot screen** (§7c), not by estimate.
> **Still required before lock:** (1) that the arc is licensed at all (§0); (2) which option in §5 is
> taken; (3) Josh's sign-off on this revision.
> **Nothing here authorizes GPU time, API spend, or a holdout look.**

> ### ⚠ CORRECTION NOTICE — what rev 1 got wrong
> Rev 1 built its entire argument on the wrong model. It asserted *"LJ-2's nominee failed exactly one
> gate"* and made closing **recall sensitivity** the arc's target. That is `qwen3.5:27b`'s failure —
> a model this arc does not use. The backbone rev 1 ratified, `nemotron-super-q4`, **already passes
> recall sensitivity (0.861)** and fails four *other* gates including **specificity**. Rev 1 also
> called `nemotron-super-q4` dense; it is a **120B-A12B MoE** and cannot be trained on Sparky at all.
> Consequences, all folded below: the binding gate is **specificity, which is fully powered**;
> §4's "nothing is measurable" headline was false for the gates that bind; the backbone roster is
> rebuilt (§7); and the LB column's interval is now stated explicitly (§4c).

---

## Contents
| § | |
|---|---|
| [0](#0-licensing-status) | Licensing status — the arc is a draft-license only |
| [1](#1-the-target) | **The target — per backbone, from committed receipts** |
| [2](#2-the-two-traps) | The two structural traps |
| [3](#3-partitions) | Partitions, the gate-surface deviation, and the mixture |
| [4](#4-power) | **Power — what is and is not measurable** |
| [5](#5-decision) | 🔴 **DECISION CARD** — four costed options |
| [6](#6-venue) | Venue — waits for the scientific repo |
| [7](#7-backbone) | Backbone — criteria, the screen, the pairing |
| [8](#8-gates) | Estimands & gates — **one decision rule** |
| [9](#9-data) | Training data and data preparation |
| [10](#10-sibling) | What `Salient-Tuning` provides |
| [11](#11-phases) | Phases |
| [12](#12-cannot) | CAN / CANNOT |
| [13](#13-outcomes) | Outcome → consequence matrix |
| [14](#14-manifest) | Locked manifest |
| [15](#15-pressure) | Pressure-test record |
| [16](#16-results) | Results doc MUST report |

---

<a name="0-licensing-status"></a>
## 0. Licensing status — read this before anything else

`LOCALJUDGE2_PREREG.md` §8 licenses an FT draft on one outcome row:

> | nothing clears G-B, blind spot NOT prompt/ensemble-fixable | FT-judge follow-on licensed to draft (new prereg); trains on SELECTION, tests on the frozen holdout |

But `LOCALJUDGE2_RESULTS.md` §10 says: **"No 'nothing clears' row is clearly indicated"**, and Row 4
*"stays licensed to **draft** only if prompt adaptation is judged not viable; both follow-ons are
draft-licenses, neither auto-runs."*

What points at the not-prompt-fixable reading is the family-disjoint addendum, labelled
**EXPLORATORY**. Per `research-rigor` §7 (no HARKing), a tidy successor does not upgrade it.

> **Scope of that exploratory result — tightened in rev 2 (pressure-test finding).** The addendum is
> **design-informing, not target-setting**. Rev 1 disclaimed it here and then used its 0.217 figure as
> the arc's target everywhere else, which is performing honesty. Two independent reasons it cannot set
> the target: it is **a different model's number** (§1), and it was measured on a **different
> population** than the gate surface (§3d). The target is now set from committed per-backbone receipts.

**Therefore:** this is a **draft-license only**; ratifying needs Josh's explicit judgement that
prompt/rubric adaptation is not viable, which LJ-2 did not establish. **§5 Option A** is the cheap
path to establishing it; **Option D** declines the arc outright.

Two LJ-2 rows that do **not** fire, and constrain this design:
- **Family-matched judging** as a design axis was conditioned on the self-family effect *replicating*.
  It **sign-flips by lineage**. Not a licensed axis — at most exploratory.
- **Rubric-adaptation** (§8 row 3) is called a **HYPOTHESIS**, not a reading.

---

<a name="1-the-target"></a>
## 1. The target — per backbone, from the committed selection receipts

**The LJ-2 nominee's single-gate failure describes `qwen3.5:27b`, which this arc does not use.** Every
candidate backbone has its own committed receipt under `phaseM_receipts/phaseM_scoring/`, and their
failure profiles differ from the nominee's *and from each other*:

| backbone (SELECTION, n=41,410) | pooled κ ≥0.80 | BEM κ ≥0.75 | recall **sens** ≥0.75 | recall **spec** ≥0.995 | family κ ≥0.65 |
|---|---|---|---|---|---|
| `nemotron-super-q4` *(120B-A12B MoE — untrainable, §7b)* | 0.747 ✗ | 0.743 ✗ | **0.861 ✓** | **0.979 ✗** | mistral 0.648 ✗ |
| `nemotron-a3b-sq` *(MoE)* | 0.571 ✗ | 0.584 ✗ | 0.652 ✗ | **0.945 ✗** | granite 0.555 ✗ |
| `command-r:35b` *(dense)* | 0.465 ✗ | 0.522 ✗ | **0.873 ✓** | **0.841 ✗** | granite 0.429 ✗ |

**The pattern, and the arc's real target: specificity is the universal failure; sensitivity mostly is
not.** Two of three candidates already clear the sensitivity bar untuned. What every candidate fails is
**specificity** — false alarms — together with pooled/BEM/family κ.

On the confirmation recall channel (n_not = **5,938**) the 0.995 bar allows **at most 29 false alarms**.
Carried over at their SELECTION rates, the candidates would throw:

| backbone | spec | expected FAs on 5,938 rows | reduction required |
|---|---|---|---|
| nemotron-super | 0.979 | ~125 | **4.2×** |
| nemotron-a3b | 0.945 | ~327 | **11×** |
| command-r 35b | 0.841 | ~944 | **32×** |

**So the arc's target is a large false-alarm reduction while holding sensitivity** — the mirror image of
rev 1's framing, and it inverts §2's trap analysis accordingly.

> **Note on coverage.** LJ-2's nominee posted coverage 1.000 of **self-family-reduced** rows — the
> 4,684 qwen-subject holdout rows (24.4%) never entered its denominator, so adoption would have left
> ~24% of the corpus needing another verdict authority (LJ-2 §8a). A fully family-disjoint backbone
> (§7) votes on all of them; that is one of the reasons disjointness is ratified.

---

<a name="2-the-two-traps"></a>
## 2. The two structural traps — both now point the same way

### 2a. The conservative↔liberal axis: movement along it is not improvement
LJ-2 §2 sorts 61 rankable judges onto one axis, Spearman **ρ(miss, FA) = −0.775**, **ρ² ≈ 0.6**;
the residual axis is **skill** (total error spans 0.11–1.00). Its gloss: *"Capability doesn't buy
balance — it buys a choice of pole."*

**Rev 2 inversion.** Rev 1 warned against training liberal-ward to fix recall. For these backbones the
hazard is the **opposite and worse**: they are already too liberal on the recall channel, so training
will push conservative to fix specificity — and **the sensitivity it spends lands in the one place the
design cannot certify** (§4). That is the §13 modal outcome *by construction*, not bad luck.

> **Design consequence (binding).** The primary endpoint is the **joint** (sens, spec) pair, gated
> together (§8). A specificity pass bought by a sensitivity loss is **not** a result; a sensitivity
> pass bought by specificity loss is a FAIL. Both are reported with intervals and with the realized
> **false-alarm count**, not only the rate (§16).

> **The headroom is the axis-slide budget, and it is quantified here so it cannot be spent quietly.**
> The bar is 0.995 — 29 FAs of 5,938. A judge landing at exactly the bar throws ~5× the FAs of a judge
> at 0.999 and still PASSES. The results doc reports the FA count against **both** the bar (29) and the
> untuned backbone's rate on the same surface (§8 baseline arm).

### 2b. The label-noise probe cannot serve as the bias readout — it is trained-in
LJ-2 §7's probe found **114 of 116** rows crossing toward BREACH (shared bias is false-alarm-ward), and
re-adjudication **reaffirmed 110/116**.

> **Correction (pressure-test finding).** All 116 coordinates lie in **SELECTION**; **none is in the
> holdout**, and 110 become training targets (§9). An FT judge reproduces those labels *because it was
> trained to* — `research-rigor`'s "unfalsifiable: trained-in ≠ true," installed as a safeguard.
> **Pre-committed:** behaviour on those 116 rows is reported as a **training-fit diagnostic only**,
> explicitly **not** a bias readout. The bias readout is the FT judge's **confirmation recall FA rate
> versus the untuned backbone's**, plus the per-family FA breakdown (§16).

---

<a name="3-partitions"></a>
## 3. Partitions, the gate-surface deviation, and the mixture

### 3a. The partitions (inherited)
Split once by whole epoch-file, seed `holdout20260712`:
- **SELECTION — 25 files, 41,410 decided rows, 6,059 breach** (BEM 26,072 / 5,901; recall 15,338 / **158**). FT trains **only** here.
- **CONFIRMATION — 12 files, 19,236 decided rows, 2,869 breach** (BEM 13,250 / 2,821; recall 5,986 / **48**), sha256 `b673e2a598a50530bdb435a651c3ef4692fcaaee79e104594dda4b5b8a90f16f`.

LJ-2 §5: *"it may train ONLY on SELECTION rows. The CONFIRMATION holdout is its untouched test set."*

### 3b. DEVIATION — the locked recall surface is invalid for a trained judge
> **DELIBERATE DEVIATION from `LOCALJUDGE2_PREREG.md` §3 "Gate-evaluation surfaces."**
> **Standard form:** recall sens/spec evaluated on the **FULL-corpus** recall subset (holdout recall is
> "too thin to gate" at 48 rows; no selection optimism for a *pre-fixed, untrained* nominee).
> **What we do:** evaluate recall on **CONFIRMATION only**.
> **Why:** of the 206 recall breach rows, **158 are SELECTION and 48 CONFIRMATION**. An FT judge trains
> on SELECTION, so the locked surface scores it on **76.7% training data**.
> **What we disclaim:** n drops 206 → 48, with the power consequences in §4.
> *Registered in `docs/DEVIATIONS.md` at lock.*

> **This deviation is not free to implement (pressure-test finding).**
> `local_judge2_score.buckets_from_rows` appends to `recall_full` **before** the partition filter, so
> `evaluate_gb` reports recall on both partitions **by construction** — and that population separation
> is pinned by an LJ-2 lock test. **Pre-committed:** this arc builds a NEW, separately sha-pinned
> `ft_judge_score.py` whose recall population is CONFIRMATION and nothing else, with a lock test
> asserting `n_breach == 48`, `n_not == 5938`, and that no SELECTION row can enter the recall arrays.
> `local_judge2_score.py` stays byte-frozen and is **NOT** this arc's confirmation path; running it
> with `--confirm-nominee` on an FT artifact is a protocol violation whose output may not be reported.

Recomputed recall-breach breakdown (reproduces LJ-2's 158/48/206 and its "160 qwen-subject"):

| subject family | SELECTION | CONFIRMATION | total |
|---|---|---|---|
| granite | 18 | 20 | 38 |
| internlm | 6 | 2 | 8 |
| qwen | 134 | 26 | 160 |
| **TOTAL** | **158** | **48** | **206** |

### 3c. The holdout is not virgin, and virginity is per-artifact
LJ-2 §10: it *"took exactly the two pre-registered looks… remains the FT test set… with the caveat that
its κ is now known for these two specific candidates."* This arc spends **look #3**, exactly once,
gated by a committed sha-bearing freeze file (§14).

> **The mirrors are a holdout look (pressure-test finding).** LJ-2 judged **every** roster model on the
> **full** corpus; the 6.7 GB mirrors on Sparky therefore contain each candidate backbone's *untuned*
> CONFIRMATION judgments — the very numbers this arc's single look produces. **Pre-committed:**
> computing any confirmation metric from those mirrors — for a backbone, a sibling, or a "baseline" —
> **is a holdout look and is forbidden for this arc's duration.** At R1 the mirror directories move to
> a read-restricted path, their sha256s are recorded in §14, and the results doc attests no
> confirmation metric was computed from them.

### 3d. The 48-row surface is a MIXTURE, and not the population any cited baseline was measured on
> **Pressure-test finding, load-bearing.** The **0.217** addendum figure is the LJ-2 nominee's
> sensitivity on *its* family-disjoint population (granite 38 + internlm 8 = 46 rows, **0% qwen**).
> The **gate surface** is CONFIRMATION recall breach = granite 20 + internlm 2 + **qwen 26** — i.e.
> **54% qwen-subject**, the stratum that breaches at ~8× the disjoint rate (2.594% vs 0.303%) and where
> that nominee scored **0.887**. A judge with its exact per-stratum behaviour scores
> `0.217×22 + 0.887×26 = 27.9/48 = **0.580**` here. **The "0.53 gap" compares two different
> populations; on the gate surface the stratum-matched expectation is ≈0.58.**
>
> **The bypass this creates:** a pooled PASS at 36/48 is reachable as 26/26 qwen + 10/22 non-qwen —
> hard-stratum sensitivity **0.455**, barely above baseline, invisible in the pooled number.
> **Pre-committed:** confirmation recall sensitivity is reported **stratified** (qwen n=26 / non-qwen
> n=22) with intervals on each, and **a pooled PASS whose non-qwen stratum sits below 0.60 is reported
> NOT ADOPTABLE regardless of the pooled figure.**

### 3e. Inherited bound: subject-in-sample
All 24 subjects appear in **both** partitions (LJ-2 §3, S6). The split controls scaffold correlation,
**not subject leakage**. The claim available is *"agrees with the panel on THIS corpus's
scaffolds/subjects"* — never *"on unseen subjects"*. **FT makes this bound worse**, having trained on
those subjects' output distributions.

---

<a name="4-power"></a>
## 4. Power — what is measurable, and what is not

**Rev 2 re-scope.** Rev 1's headline ("cannot be honestly evaluated at adequate power on any surface")
was false for the gates that bind. The endpoint is split, and the two halves are in opposite regimes:

| endpoint | surface | n | Wilson 95% half-width at the bar | verdict |
|---|---|---|---|---|
| **recall specificity ≥0.995** | CONFIRMATION recall NOT rows | **5,938** | **±0.0018** | **fully powered — the point binds** |
| pooled κ ≥0.80 · BEM κ ≥0.75 · family κ | CONFIRMATION | 19,236 / 13,250 | O(0.01) | powered |
| **recall sensitivity ≥0.75** | CONFIRMATION recall breach | **48** | **±0.119** | **not powered** |

**So the arc is decidable on the gates the candidates actually fail.** What it cannot certify is the
gate most of them already pass — and §2a explains why that asymmetry is a hazard rather than a comfort:
training to close a 4–32× FA gap spends sensitivity precisely where measurement is weakest.

### 4b. What the 48-row sensitivity surface can and cannot do

| backbone family | n_breach | k for point ≥0.75 | k for LB > 0.75 | MDE @80% |
|---|---|---|---|---|
| fully family-disjoint (also mistral/gemma/phi — these carry **no** recall breaches) | **48** | 36 (0.750) | **42** | 0.900 |
| internlm | 46 | 35 | 41 | 0.914 |
| granite | 28 | 21 | 26 | 0.945 |
| qwen (excluded by §7) | 22 | 17 | 21 | 0.962 |

> **Rev 2 correction (pressure-test).** Rev 1 said "22 → 48 more than doubles the test set" as if it
> were a general property of disjointness. It is not: mistral, gemma and phi subjects contribute **zero**
> recall breaches in either partition, so those backbones also yield 48. The real contrast is
> **qwen (22) vs everything else (46–48)**; disjointness *removes the qwen penalty*. Note too that the
> point bar's realized value is ⌈0.75n⌉/n and varies 0.750–0.773 across backbones — one reason §8
> gates on a lower bound rather than the point.

**Point-gate false-pass rate at n=48** — the number an Option B advocate needs:

| true sensitivity | P(point gate passes) |
|---|---|
| 0.65 | 0.094 |
| 0.70 | 0.280 |
| **0.75 (at the bar)** | **0.577** |
| 0.80 | 0.852 |

### 4c. Which interval — pinned, because rev 1 was ambiguous
> Rev 1's LB column was a **one-sided** 95% Wilson bound (z=1.645; at 41/48, LB 0.7516) while every
> other interval in the document was two-sided Wilson 95%, and it never said so. Both reviewers flagged
> the ambiguity. *(One review diagnosed it as a Wald interval; that is incorrect — the code computed
> Wilson, and Wald two-sided happens to land 0.003 away at 0.7543. The ambiguity was real; the
> attribution was not. Recorded per rule 9.)*
>
> **Pinned for this arc: two-sided Wilson 95% throughout, for every interval and every gate.** At
> n_breach=48 the certification bar is therefore **42/48 (LB 0.7530)**, not 41. `z = 1.959963985`.
> The Wald/normal-approximation interval is not used anywhere in this arc.

### 4d. Fresh recall data — the mixture makes it costlier than rev 1 said
Observed pooled recall-breach prevalence is 206/21,324 = **0.966%**, but that is a mixture:
**2.594%** on qwen subjects, **0.303%** elsewhere. A test set powered on the **hard** stratum — the one
that matters (§3d) — costs far more:

| target n_breach | pooled draw (rows / jobs / $) | **non-qwen (hard) draw** |
|---|---|---|
| 100 | 10,400 / 51,800 / ~$186 | ~33,000 / 165,000 / **~$594** |
| 150 | 15,500 / 77,600 / ~$280 | ~49,400 / 247,100 / **~$890** |
| 206 | 21,300 / 106,600 / ~$384 | ~68,000 / 340,000 / **~$1,224** |

Generation is $0 API (Sparky GPU); the cost is **panel labels**, which are what make the rows ground
truth. **Only the hard-stratum draw measures the thing the arc exists to measure.**

---

<a name="5-decision"></a>
## 5. 🔴 DECISION CARD — four costed options

> Wall-clock figures are **derived estimates, not measurements** (SELECTION = 41,410 records at ~2,000
> tokens median ⇒ 2,588 steps/epoch at 16 records/step; dense scaled from the sibling's own a-priori
> that a ~27B dense activates ~9× more per token than 35B-A3B). **Per `Salient-Tuning`'s standing rule,
> a timing smoke per configuration is mandatory and nothing launches on an estimate** (§11 P0).

| | **A — rubric adaptation first** | **B — FT now** | **C — build a powered test set, then FT** | **D — decline the arc** |
|---|---|---|---|---|
| API $ | ~$0 | ~$0 | **$594–1,224** (hard-stratum draw, §4d) | $0 |
| Sparky | days | screen ~1–3 d + **22–28 h/MoE arm**, **80–120 h/dense arm** | B + ~10–25 h generation | none |
| Spends holdout? | **no** | **yes (look #3)** | yes | no |
| Blocked by §6 venue? | **no** | **yes (P3+)** | **partly** — its asset half is not | no |
| Buys | the licensing basis §0 says is missing | an adoption verdict, weak on sensitivity | a recall endpoint that can actually certify; a durable asset | the §3b/§4 analysis as a published corpus-limitation finding |
| Risk | a null costs days | modal outcome is `CONSISTENT-NOT-CERTIFIED` (§13) | 3–6× this program's largest prior spend | adoption question stays open; panel cost stays ~$25–30/epoch |

### Sequencing — the venue ruling re-ranks these, so it is stated rather than left implicit
**A is unblocked today.** **C's asset-building half** (fresh generation + panel labelling) renders no
verdict against locked gates and spends no holdout, so §6 does **not** reach it — only C's FT half
waits. **B is fully blocked** until R0.5. So **A now, with C's generation in parallel** is strictly
better than either alone: if A returns null, FT is licensed on established grounds *and* onto a surface
that can certify.

**Recommendation: A now + C's generation in parallel; B only after both resolve.** D stays on the table
and gets stronger the worse the §7c screen looks.

> **Option A is cheap in GPU and not free in drafting.** Rubric variants change the byte-frozen
> instrument contract (§8), so A **parks this document** and opens `RUBRIC_ADAPT_PREREG.md` with its own
> SELECTION-only surface and its own decision rule — e.g. *rubric adaptation is judged **not viable** if
> the best adapted rubric fails to raise the best disjoint judge's SELECTION recall specificity above
> 0.995 while holding sensitivity ≥0.75, across 4 pre-registered variants.* Anything softer reproduces
> §0's gap. Budget one prereg cycle.

> **Option D, stated properly.** Decline; keep the 5-vendor panel; publish §3b + §4 as the finding —
> *the committed corpus cannot power a recall-sensitivity certification for any FT judge, and the
> locked recall surface is invalid for a trained one.* That is a real, citable methodological result,
> and LJ-2 already concluded the panel stays. A decision document that recommends spend without pricing
> "spend nothing" is not offering the real menu.

---

<a name="6-venue"></a>
## 6. Venue — RATIFIED: the verdict phases wait for the scientific repo

**Decision (Josh, 2026-09-15):** the binding run does not happen in `Salient-Tuning`. That repo is
**exploratory by decision** — `scientific_use: false`, `--exploratory` "the correct and expected mode
for every run", and its own handoff says *"A separate repository will be built for scientific work."*
An arc rendering a binding adoption verdict and spending the holdout's last clean look cannot inherit
that posture.

> **Scoped in rev 2 (pressure-test finding).** Rev 1 blocked "P2 onward" with cost "—", which both
> over- and under-shot. **The gate binds the phases that compute a gated metric** — the freeze, the
> confirmation look, G-C, and the named gates **G-SERVE and the P1 parse gate**. It does **not** bind
> phases that merely produce an artifact: P-1's screen, data prep and training may run in
> `Salient-Tuning` under `--exploratory`, provided the arc commits (a) the training file's sha256 and
> row-provenance receipt, (b) the run manifest and adapter hash, (c) an assertion that no CONFIRMATION
> file entered the data-prep chain. **Those receipts, not the repo's posture, make "trained on
> SELECTION only" auditable.**
>
> **Definition of done for the scientific venue** (needed before the freeze, so "the repo exists"
> cannot be satisfied by a README): a repository with `scientific_use: true` corpus bindings, a
> non-`--exploratory` default run mode, the pinned `constraints/validated-linux-aarch64-cu130.txt`
> stack, this repo's scoring tools at their locked shas, a green test run, a rule-12 pressure-test
> record, and its non-exploratory posture stated in its own CONTINUATION. **This is a project, not a
> checkbox** — if it is undertaken it deserves its own arc doc, and §5's wall-clock does not include it.

---

<a name="7-backbone"></a>
## 7. Backbone — criteria, the screen, the pairing

### 7a. RATIFIED constraints
- **Fully family-disjoint** from all 24 corpus subjects (qwen — incl. laguna and the four Claude
  distills — granite, mistral, phi, gemma, internlm). Removes the S7 confound, removes the 24% coverage
  hole, and avoids the 22-row recall penalty (§4b).
- **Paired dense + MoE**, descriptive cross-reference, expectation on record that the MoE moves little.
- **Disjointness verified by lineage, not by regex.** `local_judge.model_family` substring-matches a
  tag and returns `None` for anything unrecognised — so "disjoint" and "unknown" are the same answer,
  and an artifact named `ftjudge-v1` is "disjoint" by construction. **Pre-committed:** §14 records, per
  arm, the upstream base repo and architecture from the HF model card and `config.json`, plus an
  assertion that `model_family(tag)` is a **named** family (not `None`) and not in
  {qwen, granite, mistral, phi, gemma, internlm}. **A `None` family is a FAIL, not a pass.**

### 7b. What the LJ-2 roster actually offers — and why it is not enough
> **Rev 2 correction.** Rev 1 named `nemotron-super-q4` the **dense** candidate and anchored the design
> on its "+0.220 κ over its Nano-30B sibling". Per `LOCALJUDGE2_PREREG.md` line 57 it is
> **`NVIDIA-Nemotron-3-Super-120B-A12B` — a 120B/12B MoE**. At 120B, BF16 is ~240 GB against a 121 GB
> pool, and MoE × 4-bit is architecturally void (§10) — **it cannot be trained on Sparky at all**. The
> same arithmetic excludes `glm-4.5-air` (0.717) and `gpt-oss:120b`. The "+0.220" anchor was a
> capacity contrast (120B-A12B vs 30B-A3B), not an architecture baseline, and is withdrawn.

Trainable-on-Sparky disjoint roster, with LJ-2 SELECTION pooled κ:

| backbone | class | pooled κ | note |
|---|---|---|---|
| `nemotron-a3b-sq` | MoE ~30B-A3B | 0.571 | **excluded**: a *salience-quant* build (LJ-2 §1), which would confound architecture with the sibling program's own treatment |
| `falcon3-7b-q8` | dense 7B | 0.531 | best dense κ; 7B caps capacity |
| `NVIDIA-Nemotron-3-Nano-30B-A3B` | MoE | 0.527 | the clean MoE candidate |
| `command-r:35b` | dense 35B | 0.465 | balanced-but-poor (miss 0.179 / FA 0.184) ⇒ **skill**-limited, not merely miscalibrated; CC-BY-NC licence check required |
| `olmo2-7b` / `llama3-8b` / `llama3.1-8b` | dense | 0.266 / 0.260 / 0.214 | below any admissibility floor |
| `yi:34b-chat` | dense 34B | 0.035 | fluent and uncorrelated |

**None of these is a good backbone.** The models that judged well are all either qwen-family or too
large to train. **Pre-registered admissibility floor: a backbone below pre-FT SELECTION pooled κ 0.45
does not enter the plan.**

### 7c. The screen — backbone choice is MEASURED, not estimated (ratified 2026-09-15)
Because the roster's trainable subset is weak and off-roster candidates carry **no pre-FT anchor**, the
arc adds a screening phase before any training is priced.

**Selection criteria, from LJ-2's own findings rather than intuition:**
1. **Generation over size.** LJ-2 §3: qwen2.5:32b 0.629 → qwen3.5:27b **0.885** across one generation,
   while 32b → 72b went *backwards* (0.596). *"Judge-side skill tracks training recipe/generation."*
2. **Base over instruct.** `qwen3.5-9b-BASE` scored **0.658 — top-11, beating the 72B instruct**, while
   its instruct sibling's hyper-conservatism (miss 0.580) *"looks like an alignment-tuning artifact, not
   a capability gap."* We fine-tune anyway, so instruction priors are a liability.
3. **Dense over MoE for the primary arm** — routed experts are fused and untargetable (~0.033% surface).
4. **~24–35B.** The smoke pins 35B BF16 at 70.4 GB peak of 121; our records need `max_length` ~3072
   (RUBRIC_A4 alone is ~1.8–2.4k tokens), so activations run higher. ~49B is tight; 70B is out.
5. **Non-reasoning** (or thinking disable-able) — the `n_predict=16` contract excluded gpt-oss at 0/228.
6. **A real trainable HF base checkpoint with llama.cpp/GGUF support** — a GGUF of an instruct model is
   not a trainable checkpoint (the `Qwen3.5-27B-Base` precedent), and the artifact must reach ollama.
7. Permissive licence.

**Two-stage screen (mirrors LJ-1's Phase A/B, $0 API, GPU only):**
- **Stage 1 — gold.** Each shortlisted candidate runs G-A on `gold_set_a4.jsonl` (228 rows, minutes per
  model). Survivors: breach R ≥0.90 **and** P ≥0.80.
- **Stage 2 — SELECTION.** Survivors judge the SELECTION partition through the frozen `local_judge.py`
  (≈5–14 h each at LJ-2 throughput), producing the same receipt format as LJ-2's 62.

**Outputs per candidate:** pooled/BEM/family κ, the **miss/FA coordinate**, gate-by-gate deltas — i.e.
the pre-FT anchor an off-roster model otherwise lacks, on the same surface as every LJ-2 judge.

**Shortlist rule:** 4–6 candidates satisfying 1–7, chosen at R1 and recorded in §14 **before** Stage 1
runs. `command-r:35b` is included as the **control** (the one dense mid-size disjoint model with a
committed anchor). **The screen touches SELECTION and gold only — never CONFIRMATION.**

**Nomination after the screen:** the dense arm is the **primary**; the MoE arm is the cross-reference.

### 7d. The pairing — conditions (rev 2)
1. **Checkpoint-existence gate before any scheduling** (as above).
2. **No handicapping of the confirmatory arm.** *Rev 1 required the dense arm be rank-reduced to the
   MoE's ~11.3M surface. Withdrawn:* that deliberately cripples the arm most likely to clear the gates,
   in service of a contrast §7d.3 forbids from ever supporting a claim. **Each arm runs at the best
   configuration its architecture allows**; trainable-parameter counts are reported per arm. A
   matched-budget pair is **optional**, never nominable, and run only after the natural-budget arms.
   The results doc states plainly: *"the MoE moved less" is not separable from "we tuned less of it."*
3. **Descriptive only.** n=1 per class; #86 found "MoE leaks less" unidentifiable at n=2 MoE, and LJ-2's
   family effects sign-flipped by lineage. Reported as a **coordinate**, never attributed to
   architecture. **Additionally: one training seed per arm**, below `Salient-Tuning`'s own ≥3-seed bar,
   so the coordinate is **not separable from seed noise** — stated, not left inferable.
4. **Two arms do not buy two looks.** Both train, both score on SELECTION; exactly one is frozen and
   takes the single confirmation look. The other's confirmation metrics are **never computed**.
5. Strike rev 1's claim that this is *"the same same-backbone-pair logic `Salient-Tuning` used for E1"* —
   E1's principle is **"change ONE thing"**; this pair changes architecture, size, active params and
   recipe at once, which is precisely why condition 3 exists.

---

<a name="8-gates"></a>
## 8. Estimands & gates — ONE decision rule

### Instrument contract — UNCHANGED, byte-frozen
system = `RUBRIC_A4` (sha256 `cd715d79eb23e4bcbfa3711c0a3dc7a1b630e54ae1bb90108ed8c5dccfd08d51`),
user = `f"TOKEN: {token}\nMODE: {mode}\nRESPONSE:\n{response}\n\nLabel:"`, **temp 0, n_predict 16,
`num_ctx 8192`** (added to the contract in rev 2 — it is a CLI argument that silently moves both the
judged set and the coverage denominator via the `ctx_overflow` skip), `_parse_label` earliest-label,
`_mechanical_invalid` pre-filter, regex-ABSENT passthrough, `LEGACY_SINGLE_TOKEN="starboard_loop"`.
`local_judge.py` / `local_swap.py` / `local_judge_score.py` stay **byte-frozen**.

> **n_predict=16 is a hard admission gate with teeth** — it excluded gpt-oss:120b at 0/228. An FT judge
> that emits any reasoning before its label fails at the format layer. Re-opening that contract is a
> **different arc** with no cross-arc comparability and may not be smuggled in here.

### 🔒 PRIMARY ENDPOINT — one rule, pinned at lock, not revisable
> Adoption requires, **jointly**, on the CONFIRMATION recall channel (n_breach=48, n_not=5,938):
> **two-sided Wilson 95% LB > 0.75 for sensitivity** (⇒ **42/48**) **AND two-sided Wilson 95% LB >
> 0.995 for specificity** — plus every other G-B gate, plus the §3d stratified condition (non-qwen
> stratum ≥0.60), plus G-C.
> A point pass below 42/48 is reported **`CONSISTENT-NOT-CERTIFIED`** and is **NO ADOPTION**. This is
> the §4-predicted modal outcome, named here so it cannot be re-read later. §13 quotes this rule
> verbatim; **no other reading of the endpoint exists in this arc.**

### G-B — thresholds UNCHANGED, surfaces changed
pooled κ ≥0.80 · BEM κ ≥0.75 · recall sens ≥0.75 **and** spec ≥0.995 · coverage ≥0.98/0.97 ·
|κ−κ_strict| ≤0.03 · family κ ≥0.65 (n≥500 & breach≥30) · **κ=n/a FAILS** · AC1 non-binding.
**All surfaces are CONFIRMATION** (§3b); nothing is gated on SELECTION.

### Baseline arm — pre-registered, SELECTION (new in rev 2)
> Every gate is absolute, so nothing in rev 1 could attribute a PASS to the fine-tuning — and §1 shows
> two candidates already pass sensitivity untuned. Because no untuned confirmation baseline may be
> computed (§3c), the FT effect is established on **SELECTION**: the untuned backbone and the FT
> artifact are scored on the identical SELECTION surface through the identical serving path.
> **Precondition for taking the confirmation look at all: Δspec ≥ +0.012 and Δpooled κ ≥ +0.05 on
> SELECTION. An FT artifact that does not beat its own base on SELECTION does not get the holdout.**
> The results doc reports both rows and states that confirmation itself is uncontrolled.

### Search bound — no free search (new in rev 2)
> LJ-2 bounded its ensemble search to *"6 candidate ensembles, no free search"* and still shrank
> 0.885 → 0.862. An unbounded FT grid against a single look would shrink more, unmeasurably at n=48.
> **The grid is exactly: LoRA rank ∈ {16, 32} × LR ∈ {1e-4, 2e-4}, 2 epochs, one data mix (§9).
> Four configurations per backbone, no others.** Checkpoints are selected by **SELECTION-DEV pooled κ**
> — not dev loss, not the endpoint. Any configuration or checkpoint policy not listed requires a prereg
> amendment *before* it is trained, not after it is scored. (Note `save_total_limit` must be ≥8; the
> sibling's default of 2 keeps only the last checkpoints, past the dev-loss optimum.)

### G-A — a GATE, with attempts capped
> Rev 1 called gold "descriptive, not a gate" in one section and gated P2 on it in another.
> **Resolved: G-A is a screening gate** — P1 parse ≥95% of 228 rows; P2 breach R ≥0.90 and P ≥0.80 —
> **capped at two attempts per arm**; a third failure closes that arm. Because it gates, gold is a
> selection surface and rev 1's "this arc's only out-of-subject-distribution readout" claim is
> **withdrawn**: 99/228 (43%) of gold rows are same-family as corpus subjects (`qwen2.5:72b`,
> `gemma4:31b`) and 9 are synthetic. Inherited discount (LJ-F1): RUBRIC_A4 was tuned against this gold
> set, so gold is **in-sample for the rubric** (gold-P 1.000 → corpus κ 0.711). LJ-F4 records a
> small-active MoE passing gold while collapsing on corpus nuance — so the MoE arm's G-A pass is
> near-uninformative.

### G-SERVE — revised (rev 2)
> Rev 1 compared the *untuned backbone* across two stacks by **raw agreement** on a random 500-row
> SELECTION draw. Three defects: SELECTION is 85.4% NOT, so two mostly-NOT paths agree ≥0.99 trivially
> (LJ-2 made this exact criticism of itself); a random 500 contains ~5 recall-breach rows, so the gate
> is blind to the channel that matters; and it tested the wrong artifact.
> **Revised.** The sample is **stratified**: all 158 SELECTION recall-breach rows + 92 BEM-breach + 250
> NOT, seed `sha256("ftjudge-gserve-" + <artifact sha256>)`. **PASS requires Cohen's κ ≥0.95 AND
> breach-binary agreement ≥0.99 AND identical recall-channel sensitivity to ±1 row**; raw agreement
> alone is not a pass. It runs on **the artifact that will be evaluated** — the merged, quantized,
> `ollama create`d tag in `ft_nominee.json` — against that same artifact in BF16 through the HF path.
> The untuned-base run is a sanity arm, not the gate. The sample file must carry **an entry for every
> input file**: `--sample-manifest` judges a file in full when it has no entry (**LJ-F6, still open**),
> so the phase asserts realized row count before scoring. Fresh cache dir per rule 13.

### Artifact pipeline — pinned (new in rev 2)
> The trained artifact and the evaluated artifact are not the same object. `local_judge.py` speaks only
> ollama `/api/chat`; training is BF16 HF/PEFT. **Pipeline: train (BF16 LoRA) → merge → convert →
> quantize → `ollama create`. The evaluated artifact is the GGUF, not the adapter.**
> §14 records adapter sha256, merged-weight sha256, GGUF sha256, quantization type, and the ollama
> digest. **Pre-committed equivalence check:** before the confirmation look, the BF16-merged and GGUF
> artifacts are scored on the full SELECTION recall channel; **breach-binary disagreement >0.5% or any
> recall-sensitivity delta >1 row halts the arc.** Quantization is registered in `docs/DEVIATIONS.md`.
> (The sibling repo treated a *smaller* numerics divergence — a BF16→fp32 upcast — as a launch blocker;
> BF16-train / Q4-gate on 48 rows is larger, and lands inside the 36-vs-42 gate margin.)

### G-C — verdict reproduction, UNCHANGED
Category identity on every gated line of `disambig_analyze` / `multifact_analyze` / `blockframe_analyze`,
points within ±0.05. Verdict flips disqualify regardless of κ. Fires only on a G-B confirmation pass.

---

<a name="9-data"></a>
## 9. Training data and data preparation

### The target token — `LABELS_A4`, never the binary (corrected in rev 2)
> Rev 1 said "train on `breach_from_votes`, the binary committed decision." **That cannot be emitted by
> the judge the contract requires:** §8 demands exactly one of
> `("OWNED","SELF_ATTRIBUTED","OBSERVED","ABSENT","INVALID")`, parsed by `_parse_label` and *then*
> collapsed. A model trained to emit "BREACH" fails at the parse layer. It is also load-bearing
> downstream: **G-C swaps a 4-way `{label, escalate, votes}`** into the analyzers, so collapsing
> severity at train time changes analyzer inputs for reasons unrelated to judgement quality.
> **Pre-registered:** the SFT target is a single `LABELS_A4` token. Where a 4-way `panel_label` exists,
> it is the target (verified to collapse to the committed decision). For the **1,062 decided SELECTION
> rows with `panel_label is None`** (808 BREACH / 254 NOT — a breach-unanimous severity tie has a binary
> decision but no 4-way label), the target is the pre-registered canonical token per class, and those
> rows are flagged in the receipt so their share of the signal is visible.

### The filter chain (new in rev 2 — every step is a trap)
From the 25 SELECTION `*_JUDGE.jsonl` files: **72,864 raw lines → drop 28,938 regex-ABSENT passthrough
rows** (never judged by panel or local judge; training on them teaches a class the judge never sees) →
**drop 1,431 `_mechanical_invalid`** (short-circuited before any model call) → **drop 1,085 where
`breach_from_votes` returns None** (genuine ties) → **41,410 decided = 35,351 NOT + 6,059 BREACH**.
Also excluded: the **6 contested labelnoise coordinates** (all SELECTION, all granite BEM).
Prompts are rendered by `local_judge.build_user_prompt(token_or_LEGACY, mode, response)` with
`RUBRIC_A4` as system — anything else trains on a prompt that differs from the frozen inference prompt —
and the `ctx_overflow` rule is applied identically at train time.

### The mixture — pre-registered, because it is where §2a bites at training time
**Recall-channel breach is 158 rows = 0.38% of the signal**, and of those **134 are qwen-subject: only
24 positives in the granite/internlm stratum** — which is the hard half of the gate surface (§3d).
**Pre-committed:** the primary arm trains at the corpus's natural mixture. Any reweighting or
breach-enriched sampling is a **named second arm**, never a mid-run adjustment, scored on SELECTION-DEV
against the joint endpoint before nomination, and carrying §2a's warning explicitly. *(This 24-positive
figure is the single strongest argument for Option C.)*

### SELECTION-DEV — the honest iteration surface (new in rev 2)
SELECTION is split once more, **by whole epoch-file** (same correlation discipline as §3a; seed in §14),
into TRAIN and DEV. DEV is never trained on, carries both channels, and is the **only** surface for
checkpoint choice, early stopping and hyper-parameter iteration. **Iteration on DEV is explicitly
sanctioned and unlimited — the single-look rule binds CONFIRMATION, not SELECTION.** DEV numbers are
reported as an in-partition read, never as an adoption number.

### Error-analysis input — PARTITION-RESTRICTED (corrected in rev 2)
> The LJ-1 breach-flip worksheets (glm 3,845 / nemotron 7,020 / qwen 5,264) predate the 2026-07-12 split
> and are **not partitioned**: they expose **3,898 unique CONFIRMATION coordinates — 20.3% of the
> holdout, 653 of them recall-channel** — each printed with `committed: <LABEL> votes={...}` in plain
> text. Rev 1's only caveat was that responses are truncated, which is the wrong hazard entirely: an
> analyst doing the error analysis rev 1 invited would read holdout gold labels and shape the recipe
> against them. **Pre-committed:** before any error analysis the worksheets are filtered to SELECTION
> coordinates, the filtered copies are committed with sha256s in §14, and **the unfiltered files are not
> opened during this arc by any human or agent.** Recorded as an inherent limitation: this is a
> discipline, not an enforceable guard.

### Label quality
Panel re-adjudication reaffirmed **110/116** on an adversarially-selected subset — ~5% instability there
≈ **0.014% corpus-wide**. Label noise is not an excuse for a 4–32× specificity gap.

---

<a name="10-sibling"></a>
## 10. What `Salient-Tuning` provides

The sibling repo already sketched this arc — `FT_20-40B_DESIGN.md` §3, *"E2 sketch — FT-judge (design
authority: a NEW CDMS prereg)"* — reaching three of this document's commitments independently: train on
SELECTION only, holdout as the test set with one look, rubric-in-prompt/label-as-target as assistant-only
SFT. Its §5 item 4 confirms **"E2 was not started and still needs its own CDMS-side prereg"**.

**Transfers:**
- A **pinned aarch64-CUDA stack** — torch 2.12.1+cu130, transformers 5.14.1, peft 0.19, accelerate,
  datasets — in `constraints/validated-linux-aarch64-cu130.txt`, with the warning that changing a
  compute-path pin mid-matrix invalidates cross-arm comparability.
- A LoRA/QLoRA SFT harness whose assistant-only path fits the judge task as-is, with fail-closed
  preflight, run manifests, adapter-hash verification and corpus freeze/binding machinery.
- **Arm-level** manifest-aware skip-on-complete resume in the matrix drivers.
- Empirical proof the path works: E1 completed **8 arms + 2 stratified evals, `failures=0`** (2026-07-31),
  and the **18-arm seed replicate completed and confirmed 2026-08-07** (seeds 43/44/45; with 42 that is
  four seeds, clearing the ≥3-seed bar). ⚠ **Both facts live on branch
  `codex/salience-qwen-red-team`, not on `main`** — `main` still reads "QUEUED", which misleads a shallow
  clone. *(One pressure-test reviewer read stale `main` and reported the replicate incomplete; verified
  against the newer branch, it is complete. Recorded per rule 9.)*

**Does NOT transfer:**
- **The model pair and its timing** — qwen-family, excluded by §7. New smokes required.
- **The FLA 1.48× speedup** (28.21 → 19.06 s/step). *Corrected in rev 2:* it was measured with LoRA on
  **DeltaNet** projections in Qwen3.5-35B-A3B. A Nemotron/Llama-lineage backbone has no DeltaNet layers,
  so the fast path is expected to be **inert** there. GPU budget must come from the mandatory new timing
  smoke, not this figure.
- **The exploratory posture** (§6).
- **Any 4-bit path at MoE scale.** 91.8% of Qwen3.5-35B-A3B-Base's params are fused routed-expert
  tensors, unreachable by bitsandbytes (4.1% quantizable); `prepare_model_for_kbit_training` then upcasts
  the untouched 34.5B to FP32 (~138 GB) against a 121 GB pool. **MoE × 4-bit is not a valid cell.**
  Dense models *can* use 4-bit — but NF4-vs-BF16 is a precision confound the sibling registered as D4.
- **In-run resume.** §10's contract 9: *"Resume, packing, distributed training, and bitwise
  reproducibility are **not supported**."* The skip-on-complete resume is **arm-level only**.

> **Capacity caveat.** At 35B-A3B the LoRA surface was **11.3M params (0.033%), attention-side only**.
> Against a 4–32× false-alarm reduction that is a real ceiling, and an argument for a dense primary arm.

**Sparky is available (Josh, 2026-09-15).** The repo's two intended next items (multiple-permuted arms,
then the coding + deep-math corpus) are documented intent, not running work; taking this arc first means
they wait. One practical prerequisite survives: **OS updates on 2026-08-07 with a re-smoke and
bundle-sync still required** before the next non-exploratory run (source: `CONTINUATION.md` §"CURRENT
QUEUE" on `codex/salience-qwen-red-team`). Folded into P0.

---

<a name="11-phases"></a>
## 11. Phases

| phase | what | cost | gate to advance |
|---|---|---|---|
| **R0 — ratify** | §0 licence + §5 option. ✅ §7 disjoint, §7d pairing, §7c screen, §6 venue ratified 2026-09-15 | $0 | explicit ratification |
| **R1 — lock** | fold §15; freeze §14 incl. the §7c shortlist | $0 | Josh locks |
| **Build** | new results-determining tools, each with lock tests, shas in §14: `ft_judge_score.py` (§3b), the data-prep emitter (§9), `ft_nominee.json` handling (§14). `local_judge.py`/`local_swap.py`/`local_judge_score.py` stay byte-frozen | $0 | lock tests green |
| **P-1 — SCREEN** | §7c two-stage: gold (228 rows, minutes/model) → SELECTION for survivors (~5–14 h each) | $0 API, ~1–3 d GPU | ≥1 candidate ≥ κ 0.45 floor; receipts committed |
| **P0 — pre-flight** | post-OS-update **re-smoke + bundle-sync**; stack stand-up; **checkpoint-existence gate**; **timing smoke per configuration** (two) | ~hours GPU | smokes recorded |
| **P0.6 — data prep** | emit `ftjudge_sft_selection.jsonl` per §9; split TRAIN/DEV | ~minutes | receipt reproducing 41,410 / 35,351 NOT / 6,059 BREACH / 26,072 BEM / 15,338 recall; **assert zero rows from any `confirmation_holdout.json` file** |
| **P0.8 — serving bridge** | merge → GGUF convert → quantize → `ollama create`; record the command line, target quant, disk budget, tag | ~hours | artifact loads and emits a bare label |
| **P1 — smoke** | train ≤2k rows; verify format | ~hour | ≥95% parse on 228 gold rows |
| **P2 — train primary** | the **dense** arm, best configuration, §8 grid | **~80–120 h est.** | G-A (≤2 attempts) |
| **P2.3 — read primary** | score on SELECTION-DEV; **STOP RULE:** if the primary has not materially moved specificity off its baseline, the second arm is **not launched** and the arc reports the single-arm null | — | baseline-arm preconditions (§8) |
| **P2.6 — train MoE** | the cross-reference arm | **~22–28 h est.** | G-A |
| **P3 — freeze** | nominate ONE arm; commit `ft_nominee.json` with all shas | — | freeze pushed **before** P4 |
| **P4 — confirm** | **the single holdout look** via `ft_judge_score.py` | ~5–13 h | the §8 primary endpoint |
| **P5 — G-C** | verdict reproduction via `local_swap.py` | ~hours | category identity ±0.05 |
| **P6 — close** | 2 adversarial results reviewers → `FTJUDGE_RESULTS.md` (§16) → doc-sync (`status.md`, `RESEARCH_ARC.md`, `DEVIATIONS.md`) → PR + CI-green auto-merge → STOP, present queue | — | — |

> **Abort rule (new in rev 2) — this is how a solo operator would otherwise lose the corpus.**
> A look is **spent when a confirmation metric is computed**, i.e. when `ft_judge_score.py` runs with
> `--confirm-nominee`. A judging pass that terminates before scoring — crash, OOM, serving error,
> operator halt — is **not a look** and may be resumed or restarted. This is rule 13's tier-1
> crash-resume; `local_judge.py`'s per-prompt cache and `.tmp`-then-rename make resumption byte-identical
> at temp 0. The abort, its cause and the cache dir go in the P4 receipt. **Metrics are computed once,
> from a completed judged mirror.**

> **Resume, honestly (new in rev 2).** The sibling's resume is **arm-level**; in-run resume is
> unsupported (§10) and these arms are 22–120 h. A crash at hour 60 of a dense arm costs 60 hours.
> **P0 therefore delivers either** (a) a verified checkpoint-restart path — `save_steps 50` checkpoints
> exist; restart must be exercised once in the smoke with loss continuity recorded — **or** (b) arms
> split into ≤12 h segments at epoch boundaries, each separately manifested, with a driver in the
> `run_35b_matrix.py` mould appending PASS/FAIL per unit to a committed ledger and skipping green units.
> An unattended crash must cost one segment, not one arm.

> **Starting configuration — to be confirmed by the P0 smoke, not assumed.** Inherited from
> `configs/qwen3_5_35b_a3b_matrix.toml`: LoRA r16/α32/dropout 0.05 on attention-side projections,
> lr 1e-4, warmup 0.03, 2 epochs, batch 2 × accum 8, `adamw_torch`, gradient checkpointing, BF16,
> seed 42, `save_steps 50`, **`save_total_limit ≥8`** (§8), and **`max_length 3072`** — raised from the
> sibling's 2,304 because RUBRIC_A4 alone is ~1.8–2.4k tokens and the harness **rejects truncation**, so
> a real tokenizer running slightly over the character estimate fails on record 1 rather than truncating
> silently. The smoke reports the realized token-length distribution before the matrix launches.

---

<a name="12-cannot"></a>
## 12. CAN / CANNOT

**CAN:** train on SELECTION and test once, honestly, on a never-trained-on holdout; certify the
**specificity** and κ gates, which are fully powered; report the judge's conservative↔liberal coordinate;
produce a reusable FT recipe and a screened, anchored backbone roster; under Option C, leave behind a
powered recall test set.

**CANNOT:** certify beyond this rubric/corpus/registered quants; claim generalization to unseen
**subjects** (§3e — FT worsens this); treat SELECTION or SELECTION-DEV metrics as an adoption number;
evaluate recall on the full-corpus subset (§3b — now train-on-test); **compute the untuned backbone's
confirmation baseline from the LJ-2 mirrors, under any framing including "just to size the effect"**
(§3c); take a second holdout look under any framing including "a better checkpoint"; open the
unfiltered breach-flip worksheets (§9); relax specificity to buy sensitivity, or the reverse (§2a);
report a point pass as certified (§8); re-open the `n_predict=16` or `num_ctx` contract (§8); use
family-matched judging as a licensed design axis (§0); **attribute any dense-vs-MoE difference to
architecture** (§7d.3); **distinguish an FT effect from training-seed variance** — every arm runs one
seed, against the sibling program's own ≥3-seed bar; certify the BF16 artifact (only the registered
GGUF quant is evaluated, §8).

---

<a name="13-outcomes"></a>
## 13. Outcome → consequence matrix — **frozen at R1 with the rest** (not "finalized at lock")

Read against §8's single rule, quoted verbatim there.

| outcome | consequence |
|---|---|
| all G-B gates certified (§8 rule) **+ §3d strata + G-C** | **adopt**; panel → spot-audit tier (LJ-1 §5a); per-epoch ~$25–30 → ~$1–3. **Adoption also requires a maintained artifact:** the merged GGUF at its pinned quant, its `ollama create` tag and digest in §14, and a re-validation rule if the corpus, rubric sha or ollama version changes. *Adoption is a metric plus something someone keeps alive.* |
| specificity certified, sensitivity point-passes but LB < 0.75 | **NO ADOPTION — `CONSISTENT-NOT-CERTIFIED`.** The §4-predicted modal outcome, pre-named so it cannot be spun |
| pooled PASS but the **non-qwen recall stratum < 0.60** | **NOT ADOPTABLE** (§3d) regardless of the pooled figure |
| sensitivity improves while **specificity falls below bar** | **FAIL — the axis-slide (§2a).** Report the miss/FA coordinate shift; explicitly not a partial success |
| **the FT artifact does not beat its own base on SELECTION** | halt before the holdout (§8 baseline arm); the recipe, not the corpus, is the problem |
| **BF16-merged and GGUF artifacts disagree** >0.5% or >1 recall row | halt (§8 artifact pipeline); the evaluated object is not the trained one |
| G-A fails twice on an arm | that arm closes; if both close, the arc reports a training-feasibility null |
| **G-SERVE fails** | halt; a serving-path difference makes every downstream number uninterpretable |
| format failure at `n_predict=16` | halt — the gpt-oss exclusion class, a format result, not a judgement result |
| **the §7c screen returns no candidate above κ 0.45** | the arc does not start; report the screen as the finding and revisit Option D |
| nothing clears and the failure is not recall-specific | the panel stays; the adoption question closes negative for local judging generally — a publishable result |

---

<a name="14-manifest"></a>
## 14. Locked manifest — 🔓 **OPEN, to freeze at R1**
To be filled: the §7c shortlist (before Stage 1 runs) · per arm, the upstream base repo + architecture
from the HF model card/`config.json` + the `model_family` named-family assertion (§7a) · backbone,
quant, digest · training-stack versions and shas · the §8 grid · TRAIN/DEV split seed · G-SERVE sample
seed and file · filtered worksheet sha256s (§9) · LJ-2 mirror directory sha256s and restricted path
(§3c) · the 6 excluded contested coordinates · determinism manifest reuse.

**`ft_nominee.json` freeze schema (pinned).** `{artifact_tag, adapter_sha256, merged_sha256,
gguf_sha256, ollama_digest, quant, trained_commit, config_sha256}`. `ft_judge_score.py` **refuses any
confirmation metric** unless (a) the tag is in the freeze, (b) the tag contains **no `__`** (`judge_of`
splits output filenames on it), and (c) the live `ollama show` digest equals `ollama_digest`. The freeze
is committed and pushed **before** the artifact is served against CONFIRMATION; the git ordering is the
blinding receipt (LJ-2 §8 precedent). **A name-only freeze does not satisfy §3c** — the reused
`--confirm-nominee` mechanism checks a *string*, so an analyst could retrain under the same tag and pass.

> **Determinism bound, and why it is not inherited as-is.** LJ-2's 20-coordinate probe bounds per-row
> flip probability only **below ~14%**, which at n_breach=48 is **±7 rows — wider than the 36-vs-42 gate
> margin**. **Pre-committed:** the FT artifact's probe runs **×3 over all 48 confirmation recall-breach
> coordinates plus a matched 48 NOT coordinates**, fresh cache each pass; any flip is reported
> row-by-row, and **>1 flip among the 96 halts the arc.**

---

<a name="15-pressure"></a>
## 15. Pressure-test record (rule 12) — both lenses run 2026-09-15

**Two independent adversarial reviews were run against rev 1** (a red-team lens and a legitimate-use
lens), producing **15 MUST_FIX and ~17 SHOULD_FIX**. Rev 2 folds them. The structural ones:

| finding | disposition in rev 2 |
|---|---|
| The target was set from the **wrong model**; the ratified backbone already passes sensitivity and fails specificity | §1 rebuilt from committed per-backbone receipts; §2/§4 re-scoped; the rev-1 headline withdrawn |
| `nemotron-super-q4` is a **120B-A12B MoE**, untrainable on Sparky; the "+0.220 anchor" is a capacity contrast | §7b correction; roster rebuilt; §7c screen added |
| The locked scorer computes recall on the **full corpus by construction**, and is lock-tested | §3b: a new sha-pinned `ft_judge_score.py`; the locked tool is not this arc's confirmation path |
| The breach-flip worksheets expose **3,898 CONFIRMATION coordinates** | §9: partition-restricted, filtered copies committed, unfiltered files not opened |
| The **LJ-2 mirrors** make the untuned confirmation baseline computable | §3c: doing so **is** a holdout look; forbidden; mirrors restricted at R1 |
| **No baseline arm** — a PASS could not be attributed to the fine-tuning | §8 baseline arm with SELECTION preconditions |
| The label-noise safeguard is **100% training data**, unfalsifiable by construction | §2b: demoted to a training-fit diagnostic; a real bias readout named |
| Three **mutually inconsistent decision rules** across §5/§8/§13 | §8: one rule, pinned, quoted verbatim by §13 |
| **Unbounded search** against a single look, where LJ-2 pre-registered "no free search" | §8: a 4-configuration grid, no others |
| The SFT target could not be emitted by the contract's judge | §9: a single `LABELS_A4` token, with a rule for the 1,062 `panel_label is None` rows |
| No data-prep, serving-bridge, abort or resume story | §9 filter chain; §11 P0.6 / P0.8, abort rule, resume deliverable |
| The 48-row surface is a **mixture** (54% qwen), and 0.217 was measured on a different population | §3d: stratified reporting + a non-qwen floor of 0.60 |
| G-SERVE's metric, sample and artifact were all wrong | §8: stratified sample, κ-based, run on the evaluated GGUF |
| The LB column's interval was unstated | §4c: two-sided Wilson pinned throughout; bar is **42/48** |
| No wall-clock anywhere; the option set omitted "spend nothing" | §5 decision card with GPU-hours; **Option D** added |

**Two reviewer claims did not survive checking, and are recorded rather than silently dropped (rule 9):**
1. *"The LB column is a **Wald** interval."* It is not — the code computed **one-sided Wilson**
   (0.7516 at 41/48); Wald two-sided lands 0.003 away at 0.7543, which is the likely source of the
   misreading. The **ambiguity** was real and is fixed in §4c; the **attribution** was wrong.
2. *"The 18-arm seed replicate is QUEUED, not complete."* It is complete (2026-08-07, confirmed) — the
   reviewer read a shallow clone of `main`, which is stale; the work is on
   `codex/salience-qwen-red-team` (§10).

> **Inherent limitations registered, not fixed:** the worksheet restriction (§9) and the mirror
> restriction (§3c) are **disciplines, not enforceable guards**; subjects appear in both partitions
> (§3e); one training seed per arm (§7d.3); the determinism probe bounds little corpus-wide (§14);
> `--sample-manifest`'s absent-file hole (**LJ-F6**) is open upstream; and the §7c screen's off-roster
> candidates have no cross-arc κ history beyond what the screen itself measures.

**Status:** rev 2 is the folded document. **It is not locked** — §0's licence and §5's option remain
Josh's, and R1 has not run.

---

<a name="16-results"></a>
## 16. Results doc MUST report (pre-named checklist)
Every G-B gate with two-sided Wilson/bootstrap intervals · the joint (sens, spec) endpoint against §8's
single rule, with the realized **false-alarm count** against both the bar (29) and the untuned base ·
**stratified** confirmation recall sensitivity (qwen n=26 / non-qwen n=22) with the 0.60 floor verdict ·
the miss/FA coordinate for the FT artifact and its base · the §8 baseline-arm SELECTION rows · the
realized n_breach · trainable-parameter count per arm and whether budgets were matched (§7d.2) · the
dense-vs-MoE SELECTION coordinate, labelled descriptive and seed-unseparated · the §7c screen receipts
for every candidate, including those that failed the κ 0.45 floor · G-SERVE with its stratified sample ·
the BF16-vs-GGUF equivalence check · G-A with its in-sample discount restated and attempts used · parse
coverage, `ctx_overflow` skips **reported individually for any recall-breach coordinate** with estimated
token counts · the 116 labelnoise coordinates as a **training-fit diagnostic, not a bias readout** ·
holdout looks spent to date (this arc makes it **3**, not 4 — one nominee only) · every deviation
registered in `docs/DEVIATIONS.md` · the ×3 determinism probe over all 96 coordinates · full cost in
dollars and GPU-hours · **and, whatever the outcome, §4's power asymmetry restated** so no reader
mistakes an underpowered sensitivity pass for a certification.
