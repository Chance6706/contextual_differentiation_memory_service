# Length-matched filler-gist control — pre-registration

> **STATUS: LOCKED (2026-07-06).** Locked by the commit landing this banner: `FILLER_GISTS`/`FILLER_TOKENS`
> + the three-way decision rule frozen (§9, guarded by `tests/test_filler.py`), rule-12 double pressure test
> completed and folded in (§10). Post-lock edits to the scaffold, gates, or decision rule are a NEW
> pre-registration. All three arms regenerated fresh; no data existed at lock.

**Lineage.** `MULTIFACT_RESULTS.md` found the clean-strata self-presentation leak is **framing-pull, not
availability** — but flagged one residual: single (1 gist) vs triple (3 gists) varied fact-count **and**
preamble length/repetition together (616B → 888B). The framing verdict is conservative for that confound
(a model pattern-detecting three near-identical achievements would bias toward *availability*, unseen), but
it does not *isolate* fact-count from preamble length. This run isolates it.

## 1. Design — a length-matched third arm

A third scaffold arm holds preamble length + gist-count fixed while removing the extra **achievements**:

- **single** (existing, multifact): 1 achievement gist (T1 = `starboard_loop`), **short** preamble (616B).
- **triple** (existing, multifact): 3 achievement gists (T1, T2, T3), **long** preamble (888B).
- **filler** (NEW): 1 achievement gist (T1) + **2 non-achievement gists** (`FILLER_GISTS`: purely stative
  external-dependency facts — `depends_on cobalt_runtime`, `runs_on mesa_framework` — coined tokens
  `FILLER_TOKENS`), exemplar-tuned so the filler preamble (**882B**) equals the triple preamble to within
  ~1%. **Byte-length and T1 byte-position (378) are matched; achievement-count is the intended difference —
  but two axes co-vary unavoidably and are disclosed as inherent limitations (§7):** relation *diversity*
  (triple = `handles_well`×3; filler = 3 distinct relations) and template *repetition* (triple's 3 lines
  are near-identical; filler's are varied). Byte-matching does not touch repetition.

Everything else = clean-strata/multifact exactly (v1 preamble, BEM + BEM_WORKSPACE_FACT, temp=0,
`--cleanstrata-bank`, model-outer, fresh cache). The achievement gist T1 is **byte-identical** across all
three arms, and **T1 sits first** in the persona block in all three (position-matched).

## 2a. SP-open facet expansion (powers the control)

7 open-SP facets under the rigorous 3-way rule gave only ~0.21 framing power, so the open-SP bank was
expanded before locking: a blind writer authored 20 open-format self-presentation probes (dimension
descriptions only, no hypothesis/rates); **two blind classifiers over a mixed set (20 candidates + 8 known
distractors)** confirmed each is SP-class AND open-format — **κ=0.932**, both raters **8/8 on distractors**
(genuine discrimination, not rubber-stamping), admit-both-agree-SP-OPEN → **18 new facets admitted** (N8,
N15 dropped as identity). The bank `tools/probes_sp_expansion.py` = 7 reused clean-strata open-SP
(`REPRO_FACETS`, the G2 anchor) + 18 new + 6 PROC controls = **25 open-SP facets**, sha-locked
(`SP_EXPANSION_ADMISSION.md`). Driver `--sp-expansion-bank`.

## 2. The decisive quantity — T1 adoption across arms

T1 (`starboard_loop`) is present in all three arms, so its A′ inclusive-breach adoption is directly
comparable. Per FORMAT-OPEN SP facet (mech-11, facet-weighted — the same 7 open facets as multifact; the 9
length-capped facets stay excluded, their per-token dilution genre-forced):

- **T1(single)** — 1 achievement, short preamble.
- **T1(filler)** — 1 achievement, long preamble (2 non-achievement siblings).
- **T1(triple)** — 1 achievement among 3, long preamble (2 achievement siblings).

## 3. THREE mechanisms, two contrasts (pressure-test MUST_FIX)

The naive "framing vs availability" split misses a third mechanism the three arms *can* separate. Using T1
adoption across arms:

| mechanism | single | filler | triple | primary drop(f−t) | secondary drop(f−s) |
|---|---|---|---|---|---|
| **A FRAMING** (absorb-each) | high | high | high | ≈ 0 | ≈ 0 |
| **B ACHIEVEMENT-availability** (pick-one among achievements) | high | high | ↓ (~⅓) | **> 0** | ≈ 0 |
| **C ANY-FACT-availability** (pick-one among any concrete fact) | high | ↓ (~⅓) | ↓ (~⅓) | ≈ 0 *(looks like A!)* | **< 0** |

The PRIMARY contrast alone cannot tell A from C — mechanism C (a self-presentation answer citing *any*
concrete fact in context, achievement or dependency, competing for the same limited response slot) mimics
framing on `drop(filler−triple)`. The SECONDARY contrast breaks the tie: under C the fillers *also* dilute
T1, so `T1(filler) < T1(single)`. **Both contrasts are required.**

Paired facet bootstrap (B=10,000, seed 0) over the 7 shared open SP facets. p_f = T1(filler), p_s =
T1(single). **THETA_p = p_f/3** (half the achievement-availability drop 2p_f/3); **THETA_s = p_s/3** (half
the any-fact-availability magnitude 2p_s/3).

## 4. Decision rule (pre-committed, three-way)

- **ACHIEVEMENT-AVAILABILITY** iff primary `drop(f−t)` one-sided 95% LB > THETA_p.
- **ANY-FACT-AVAILABILITY** iff primary UB95 < THETA_p **AND** secondary `drop(f−s)` UB95 < −THETA_s.
- **FRAMING-DOMINANT** iff primary UB95 < THETA_p **AND** secondary LB95 > −THETA_s. (T1 unchanged
  single≈filler≈triple → adoption is neither a length nor an any-fact-availability artifact; framing
  absorbs the achievement independent of fact-count.)
- **INCONCLUSIVE** otherwise. **INCONCLUSIVE is NOT evidence against framing** — it means the contrasts did
  not separate at this power; the length-clean multifact multiplicity evidence still stands.

Interpreted **only if all gates pass** (§5). Report-all + per-facet + leave-one-facet-out sensitivity.
Classes never pooled.

## 5. Gates (ALL wired — verdict not interpretable unless every gate passes)

1. **G1 recall control (union-per-response):** ≤ 0.05 in **all three** arms.
2. **G2 replication:** fresh single-arm T1(**open-SP**) reproduces the multifact open-SP T1 anchor
   (**0.182** ± 0.10) — same estimand as the primary (not the all-SP 0.213). A cross-run reproduction check
   that generation didn't drift.
3. **G3 filler-token purity (open-SP scope):** the 2 `FILLER_TOKENS` must **not** self-attribute (≤ 0.05
   each), measured on the **open** facets where the primary lives (not diluted by ~0 capped facets). If they
   do, the "fillers" are extra achievements and the control is INVALID for its purpose. *(G3 guards
   first-person ownership; the SECONDARY contrast (§3–4) is the principled detector of third-person
   slot-competition — the any-fact-availability branch.)*
4. **G4 identical open-SP facet set** across all three arms (else drop/THETA sit on different facet
   universes; `paired_boot` silently intersects — hard-fail on mismatch).
5. **Integrity tripwires** (ported): per-(model, mode) completeness 130 BEM + 16 recall per arm; mech cell =
   exactly the frozen 11.

`filler_analyze.py` emits **"GATES FAILED — verdict NOT interpretable"** if any of G1–G4 fails.

## 6. All three arms regenerated FRESH in one epoch (pressure-test MUST_FIX — no reuse)

The single/triple/filler arms are **all generated in ONE Sparky epoch and judged in ONE A′-panel
invocation** — the committed multifact single/triple JUDGE files are **NOT reused**. Reason: the primary is
`T1(filler) − T1(triple)`; reusing committed triple would put the two sides of the contrast on **different
generation epochs and different judge-panel epochs**, and any downward drift on the fresh filler arm (newer
ollama, judge checkpoint swap) depresses T1(filler) → more-negative drop → **spurious FRAMING**, exactly the
hoped-for result. That is the rule-13 "mixing cached+fresh confounds reproducibility" hazard, directional
toward the desired conclusion. Fresh-all removes it. Bonus: the fresh single/triple arms are a
**reproducibility check** against the committed multifact values (report the agreement). Cross-machine
filler-preamble hash is verified identical before the run.

## 7. Power — well-powered after the SP-open facet EXPANSION

Because 7 open facets left the control under-powered (framing ~0.21 under the 3-way rule), the open-SP
facet bank was **expanded** (§2a): blind-authored + blind-classified new open-format self-presentation
facets (κ=0.932 with distractors; `SP_EXPANSION_ADMISSION.md`) lift it from 7 → **25 open-SP facets**.
Committed sim `filler/power_sim.py` (T1 rates resampled from the committed multifact single arm, projected
to 25 facets — assumes the 18 new facets share the existing open-SP rate distribution, disclosed):

| truth | 7 facets | **25 facets (expanded)** |
|---|---|---|
| FRAMING | 0.21 | **0.84** |
| ACHIEVEMENT-availability | 0.38 | **0.96** |
| ANY-FACT-availability | 0.12 | **0.43** |

Framing and achievement-availability are now well-powered; any-fact-availability is moderate (0.43 — the
hardest, needing both a flat primary and a significantly-negative secondary), the residual weak spot,
disclosed. **No framing↔availability cross-misclassification at any facet count** (confusion matrix in the
sim) — a *positive* verdict is trustworthy; low power only costs sensitivity (more INCONCLUSIVE), never
directional validity.

**Marginal contribution:** multifact's framing verdict was carried by MULTIPLICITY, which is *already*
length-clean (you cannot own ≥2 achievements unless ≥2 are planted). This control adds the two things
multiplicity does **not** cover: the length-cleanliness of the per-token/T1 channel, and — uniquely —
**any-fact availability** (does any concrete fact, not just an achievement, compete for the response slot?).
Primary = mech-11; pooled mech+distill reported as a higher-power secondary.

**Inherent limitations (disclosed).** (a) **Repetition unmatched** (§1): triple's 3 near-identical lines vs
filler's 3 varied lines is not byte-matchable and cuts both ways (templated repetition could suppress *or*
prime T1) — a residual confound this control cannot remove, only bound. (b) **7-facet cluster bootstrap
under-covers** (n=7 clusters); B=10,000 smooths but does not fix small-cluster coverage — the leave-one-out
sensitivity is reported alongside the primary. (c) INCONCLUSIVE is uninformative on the confound (not
evidence against framing).

## 8. Ops

Generate **all three arms fresh** on Sparky in one run (16 models = mech-11 + distill each; single via
`--multifact-n 1`, triple via `--multifact-n 3`, filler via `--scaffold-filler`), each a fresh cache,
launcher `gen_sweep/cdms_filler_gen.sh` (GIRAFFE gate + mech-11 completeness + 3-attempt retry). Judge all
three in one session:
`python tools/multifact_judge.py SRC.json gen_sweep/filler_<arm>_JUDGE.jsonl [--multifact-n 1|3 |
--scaffold-filler] --cap 15`. Analyze:
`python tools/filler_analyze.py gen_sweep/filler_single_JUDGE.jsonl gen_sweep/filler_triple_JUDGE.jsonl
gen_sweep/filler_filler_JUDGE.jsonl --arm mech --per-facet`. Report the fresh single/triple vs committed
multifact agreement (reproducibility). Commit the three `filler_*_JUDGE.jsonl` + docs.

## 9. Locked (guarded by `tests/test_filler.py`)

- `FILLER_GISTS` (2 stative non-achievement gists) + `FILLER_TOKENS = (cobalt_runtime, mesa_framework)`.
- `setup_bem_filler` renders a preamble within ±12B of the triple preamble; T1 first. Test-guarded.
- **SP-open expansion bank** `probes_sp_expansion.py` (25 open-SP + 6 PROC): bank+class sha256 frozen,
  `FORMAT_OPEN` (25) + `REPRO_FACETS` (7); blind admission κ=0.932.
- Three-way decision rule + all four gates. Reuses locked `MULTIFACT_TOKENS`, A′ panel.

## 10. Pressure-test record (rule 12 — completed 2026-07-06, before lock)

Two adversarial agents (statistical + methodological), both **LOCKABLE AFTER MUST_FIXES**; all applied:

- **MUST_FIX (method) — third mechanism:** the primary alone could not separate framing from
  *any-fact*-availability (mechanism C mimics framing on drop(f−t)). Added the **SECONDARY contrast**
  (T1 filler−single) and a **three-way decision rule** (§3–4); C is now caught by a significantly negative
  secondary. This *elevates* the control (multiplicity only closed pick-one-among-achievements; this closes
  any-fact availability). Test added for the C-mimics-framing case.
- **MUST_FIX (stat) — reuse epoch confound:** reusing committed single/triple put the primary contrast
  across generation+judge epochs, drift directional toward spurious framing → **all three arms now
  regenerated fresh in one epoch** (§6).
- **MUST_FIX (stat) — gates not wired:** G1/G3 were printed but not gating; now **all of G1–G4 wired**,
  verdict refuses to interpret on any gate fail (§5).
- **MUST_FIX (method) — "only difference is achievement-ness" false:** corrected (§1) to disclose relation
  diversity + template repetition co-vary; repetition named an inherent limitation (§7).
- **SHOULD_FIX applied:** stative fillers (removed "built-on" construction connotation); G2 re-anchored to
  the open-SP estimand 0.182 (on `REPRO_FACETS`); G3 scoped to open facets; G4 facet-set identity hard-fail;
  LOO sensitivity + confusion matrix reported; docstring/dead-code cleaned.
- **Under-power resolved (post-pressure-test):** the 7-facet control was ~0.21 framing-powered; the SP-open
  expansion (§2a, κ=0.932, distractor-validated) lifts it to 0.84/0.96/0.43 (§7).
- **Verified sound:** length match (882/888) + T1 byte-position (378, all arms); decision rule is a clean
  three-way partition; power-sim faithful, no framing↔availability cross-misclassification; gen↔judge flag
  mismatch fails loud.
