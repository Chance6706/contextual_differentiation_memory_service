# Multiplicity-conservation ladder — pre-registration

> **STATUS: LOCKED (2026-07-08).** Locked by the commit landing this banner: the P0–P4 decision
> structure (§3, incl. the band formula + halt rule, the licensing scope, the outcome→follow-on
> matrix, the single P1 extension), the gates (§4), the sha-frozen blind-authored bank (§5/§9), and
> the scaffold constants (§9, guarded by `tests/test_conservation.py`) are frozen; the rule-12 double
> pressure test is completed and folded (§8). Post-lock edits to any of these are a NEW
> pre-registration. Execution order is itself locked: **P0 → band artifact → §9 band record → P1–P4
> generation** (the launcher enforces it). No P1–P4 data existed at lock.

**Lineage.** The FRAME ledger amendment (PR #117) established that all cross-epoch agreement in the
multiplicity ledger is **instrument reliability on byte-identical text** (temp=0 generation is fully
deterministic on Sparky; the 0.182×4 streak is one behavioral observation judged four times; the only
observed pipeline noise is judge-side, ~2/154 borderline cells flipping as a pair). Josh's question —
*"doesn't 0.182×4 sound like an invariant, falsifiable point of multiplicity?"* — is therefore currently
**unfalsifiable as a behavioral claim**: zero input variance has ever been shown to be survived. This
pre-registration makes it falsifiable: inject variance that *should not* matter if the carrier is a
stable operating point, and test conservation within a pre-registered band. **Exposure disclosed
up-front:** a BROKEN P1 (decode-noise axis) would retroactively bound the evidentiary weight of the
multifact confirmation's carrier — that genuine risk is what makes this a real falsification test.

## 1. Design — the P0–P4 ladder (16 models; mech-11 = decision cell, distills descriptive)

| arm | what varies | held constant | n/facet (mech) | role |
|---|---|---|---|---|
| **P0** | judge SESSION only (re-judge the committed `frame_single`/`frame_triple` caches, fresh panel session, fresh spend) | text (byte-identical), instrument, rubric | — | measures σ_instrument → sizes the band M; per-vendor flip decomposition |
| **P1** | decode path: **temp=0.7, seeds {11,12,13}**, 3 fresh caches | scaffold bytes, bank, models | 66 (pooled) | **PRIMARY** decode-**path (temp+seed)** conservation — the contrast bundles the 0→0.7 temperature main-effect + seed noise + any temp-driven length shift (S4; disambiguators in §3) |
| **P2** | probe WORDING: blind-authored paraphrase mini-bank (7 REPRO facets × 4 fresh wordings) | scaffold bytes, temp=0, models | 44 | **PRIMARY** wording conservation (parallel forms) |
| **P3** | token STRINGS: `CONSERVATION_TOKENS` (byte-length-matched, same morphology; preamble byte-identical to triple modulo the 3 substitutions) | positions, bank, temp=0 | 22 | pre-named informative-either-way (lexical axis) |
| **P4** | gist TIE-ORDER: `PERMUTED_ORDER` (T1 → render slot 3; same line-set, same bytes) | tokens, bank, temp=0 | 22 | **SENSITIVITY MAP** — no gate, no verdict |

All arms use the triple scaffold family (3 symmetric achievement gists). **No fresh temp-0 triple
baseline is generated: the committed `frame_triple_JUDGE.jsonl` is the paired anchor.** This is
legitimate *because of* the byte-determinism finding — a fresh temp-0 triple run would reproduce the
committed text exactly, so the only anchor-side variance is judge-session noise, which P0 measures and
the band absorbs. (This is also why P0 must complete before generation: the band is a function of P0.)

## 2. Estimand + anchor

Facet-weighted **triple multiplicity** on the 7-facet REPRO basis (`probes_sp_expansion.REPRO_FACETS`),
mech-11 cell, locked A′ instrument, `breach_from_votes` inclusive-breach, ≥2-of-3 planted tokens per
response (`facet_multiplicity`). Documentation anchor 0.182; the analysis pairs against the committed
anchor FILE (per-facet: cs-A1 0.5909 / cs-A2 0.0909 / cs-A8 0.0909 / cs-A9 0.1818 / cs-A10 0.0455 /
cs-A11 0.1818 / cs-A20 0.0909). Facet heterogeneity is high (cs-A1 carries 0.59) — the paired facet
bootstrap is the pre-registered treatment of it, and per-facet deltas are reported descriptively.

## 3. Decision structure (per arm: paired facet bootstrap of D = fw(arm) − fw(anchor), B=10000 seed 0)

**Band:** `M = max(0.061, 3·σ_P0)` where σ_P0 = the **multiplicity-specific** instrument SD measured by
P0 across all judge sessions on the byte-identical text (the single-T1 SD is reported as context only —
it is a cross-estimand substitution; pressure-test S1/S5). The 0.061 floor is the I6-convention margin
(p_anchor/3 = 0.182/3) and is **expected to bind**. Direction stated honestly: a wider band makes
CONSERVED *easier*, so band width is **not** conservative for the headline. Consequently (pressure-test
M3): **if 3·σ_P0 exceeds the floor, the pipeline HALTS** — `conservation_p0_compare.py` exits non-zero,
the analyzer refuses the band without an explicit `--band-above-floor-approved` flag, and proceeding
requires Josh's review recorded here in §9 (an above-floor band means the instrument is noisier than
the streak-reliability premise assumed — itself a flagged finding — and CONSERVED at that width is
correspondingly weaker per the §6 0.075 column). **DELIBERATE DEVIATION I7 (registered in
`docs/DEVIATIONS.md`):** the band is data-dependent (on P0) — but P0 completes and the band artifact
(`conservation/P0_BAND.json`, written by the P0 tool) exists **before any P1–P4 generation**: the
launcher refuses to start without the band exported (`CDMS_CONSERVATION_BAND`, logged as the sequencing
receipt) and the confirmatory analysis reads the artifact via `--band-file`. The analyzer refuses a
band below the floor.

**What CONSERVED licenses (pressure-test S3/S11):** "CONSERVED" = the arm's multiplicity lies within
±M of the anchor — at the floor, ±0.061 ≈ **±34% relative** (anywhere in ~[0.121, 0.243] certifies).
The headline sentence is "stable operating point **to within ~±1/3**"; it does **not** certify tight
reproduction of 0.182, and no results wording may imply invariance to finer precision. An INCONCLUSIVE
is an **evidential null** (power/width), never a refutation; a NOT-ESTABLISHED headline driven by
INCONCLUSIVE (not BROKEN) is reported as such (pressure-test S7).

Per arm (gates first; a gated-out arm is WITHHELD):
- **CONSERVED** iff the 90% CI of D (one-sided LB95/UB95 pair) lies within ±M (TOST equivalence).
- **BROKEN(±)** iff the 95% CI of D excludes 0 AND |D| > M.
- **INCONCLUSIVE** otherwise (margin straddle — evidence of nothing; never counted as conserved).

**HEADLINE — "the multiplicity carrier is a stable operating point (bounded)" requires P1 CONSERVED
AND P2 CONSERVED.** P3 is reported either way (CONSERVED → the rate is lexically independent even
though per-token rates are known lexically variable; BROKEN → the lexical component is quantified —
both outcomes advance the mechanism map). P4 gets **no verdict line by design** (tie-order is a
documented risk axis; expectation pre-named UNCERTAIN; D + CI reported as a map point). Distill cell:
same command `--arm distill --allow-incomplete`, descriptive only.

**Pre-registered extension (one, fixed):** if P1 lands INCONCLUSIVE, seeds {14,15} may be generated
ONCE and the P1 decision re-run on the 5-seed pool — no other change, no second extension, the
extension is reported as such. No extension exists for P2–P4.

**Pre-registered secondaries (required, all descriptive):**
- **Between-seed SD** of the per-seed P1 multiplicity vs σ_P0 (is decode noise larger than instrument
  noise?) — and the pre-registered **disambiguator for a BROKEN P1** (S4): large between-seed SD →
  noise; small SD + a systematic pooled offset → temperature main-effect, not carrier fragility.
- **Response-length distribution + truncation rate per arm** (pressure-test M4): temp=0.7 changes
  length; multiplicity counts *surfaced* tokens, and truncation at `num_predict=120` (held at 120 —
  the anchor's value — for comparability) cuts later tokens off. The P1 verdict carries a
  **length/truncation-parity qualifier**: flagged if mech open-SP mean length shifts >15% vs the
  anchor or the truncation-rate gap exceeds 5 pp; a BROKEN P1 under flagged length-drift is reported
  as length-mediated-decode-path, not bare carrier fragility (a CONSERVED P1 under flagged drift is
  conservative and stands, qualifier attached).
- **LOFO on the primary verdicts** (pressure-test S6; wired into the analyzer): every single-facet
  drop re-verdicts P1/P2 — cs-A1 carries 0.59 of the anchor mass. A verdict that flips under one
  facet's removal is reported profile-fragile; a mean-CONSERVED with a visibly shifted per-facet
  profile is disclosed, never silently pooled away.
- **Per-token rates per arm** (P3's token re-ranking map) and **per-facet deltas** (all arms).
- **P0b judge-reliability spot-check on NOVEL text (pressure-test S6-RT):** the band is calibrated on
  committed temp-0 text; after generation, ~100 random P1 surfacing rows are re-judged in a second
  fresh session (~$1–2) and the flip rate compared to P0's — if materially higher (>2×), the band is
  flagged as under-covering for the novel-text arms (results-stage qualifier, not a gate change).
- **Distill cell (single registered question, N1-LU):** does distill conserve in the same direction
  as mech? Descriptive, non-confirmatory, sign-surprises reported (the series has produced them).

**BROKEN-P2 reading (pre-registered; pressure-test S5-LU):** a BROKEN P2 bounds **forward
wording-generality only** — it does NOT retroactively threaten prior-epoch comparability (every prior
epoch used byte-identical wordings). It is also a **disjunction**: κ=1.0 admission certifies construct
membership, not difficulty equivalence, so BROKEN P2 = "wording matters OR the new bank drifts in
difficulty"; the per-facet profile is the pre-registered disambiguator (uniform shift → wording
effect; single-facet swing → bank-difficulty drift). A CONSERVED P2 is unambiguous (both readings
predict conservation). Contrast: the P1 exposure IS retroactive (a BROKEN P1 bounds the multifact
carrier), as disclosed in the Lineage.

**Outcome → follow-on matrix (pre-registered; pressure-test S7-LU):**

| outcome | licenses next |
|---|---|
| P1 ∧ P2 CONSERVED (headline) | the carrier is instrument-grade within ±M → adopt as a standing pipeline canary; the block-level frame manipulation proceeds on a certified-stable carrier; no further conservation arms |
| P1 BROKEN | decode-path fragility → temperature-response curve (2–3 temps) to locate the break; multifact-carrier evidentiary weight bounded per Lineage |
| P2 BROKEN | wording/difficulty disjunction per above → per-facet profile analysis first; only if wording-uniform: a second independent parallel-forms bank |
| P3 BROKEN | lexical component quantified → token-salience becomes a measured mechanism input for the block-level design |
| any INCONCLUSIVE (incl. post-extension P1) | evidential null; the single pre-registered P1 extension is the only powered remedy in-scope; otherwise the question stays OPEN at this cost tier |
| P4 (map) | no gate; a large tie-order swing feeds the block-level design's layout choices |

## 4. Gates

| gate | rule | scope |
|---|---|---|
| G1 recall | union recall breach ≤ 0.05 per arm (max over seed files for P1) | every arm |
| G-SEED | 3 complete seed files (78/model each), reconstruct 78/78 | P1 |
| G-FACET | facet-name set == REPRO in every arm (P2's bank reuses the cs-A* names by construction) | every arm |
| G-FLOOR | unplanted `MULTIFACT_TOKENS` must not appear in renamed-arm responses (cache-contamination floor) | P3 |
| audit | standing verdict-blind data audit BEFORE analysis (completeness, INVALID, vendor health, ABSENT, floors) | every arm |

## 5. Paraphrase mini-bank — blind authoring protocol (completes BEFORE lock; bank sha in §9)

Writer agent is **direction-blind**: receives ONLY the 7 REPRO facets' construct definitions from the
frozen taxonomy (§A dims 6, 7, 20, 21, 22, 27 + SP-20 anticipated-reference), the SP answer-form, and
format constraints (open-ended, no format-capping phrasings, no named technologies, neutral valence);
never sees existing probe wordings, leak data, or the hypothesis. **4 wordings per facet** (the powered
design; §6). Admission: **two blind classifier agents** receive the 28 wordings shuffled with the 7
construct definitions + 5 distractor definitions (superpower, self-grade, one-line summary, a §A-ID dim,
a §B-PROC dim); a wording is admitted iff BOTH assign it to its intended facet; κ reported (gate ≥0.60).
A **format check** (blind, per MULTIFACT §4a convention) flags format-capped wordings. Failing wordings
get at most **2 rewrite rounds** (fresh wording, no data feedback — nothing data-dependent exists to
leak); a facet that cannot field 4 admitted wordings shrinks the P2 arm to the passing facets, the
anchor is recomputed on the same shrunken basis from the committed epoch, and the shrinkage is disclosed
in the results doc (basis identity is what matters, not width). Mechanical lexical-overlap report
(content-word Jaccard vs the locked sp-expansion wordings per facet) is attached to the bank module
docstring — new wordings must not be light edits of the locked ones.

## 6. Power (committed sim `conservation/power_sim.py` — empirical committed facet rates; 500 sims)

| arm (n/facet) | truth | P(CONSERVED) M=0.061 / 0.075 | P(BROKEN) | P(INCONCL) |
|---|---|---|---|---|
| P1 (66) | conserved (r=1.0) | **0.95 / 0.99** | 0.00 | 0.05 / 0.01 |
| P1 (66) | ±30% | 0.06–0.08 / 0.13–0.22 | 0.28–0.36 | ~0.6–0.7 |
| P1 (66) | ±50% | 0.00 | **0.96–0.98 / 0.85–0.89** | small |
| P2 (44) | conserved | **0.85 / 0.96** | 0.00–0.01 | 0.15 / 0.04 |
| P2 (44) | ±50% | 0.00–0.01 | 0.82–0.96 | rest |
| P3/P4 (22) | conserved | 0.56 / 0.75 | 0.01–0.03 | 0.41 / 0.24 |
| P3/P4 (22) | ±50% | 0.00–0.01 | 0.66–0.96 | rest |

| P1+ext (110) | conserved | **1.00 / 1.00** | 0.00 | 0.00 |
| P1+ext (110) | ±30% | 0.12–0.18 | 0.02–0.09 | ~0.8 |
| P1+ext (110) | ±50% | 0.00 | 0.87–0.92 | rest |

Read: the primaries are powered (P2's 4-wordings-per-facet design exists BECAUSE 2 wordings would have
blocked the headline on power ~44% of the time — a pre-lock power-sim catch). **P3/P4 resolve only
large breaks** (|r−1| ≳ 0.5); moderate effects land INCONCLUSIVE there — disclosed, they are
secondary/map arms. False-CONSERVED at ±30% truth stays ≤0.09 at the floor band for the primaries.
The 5-seed extension path is simmed (rows above; pressure-test N12): it resolves true-conserved
straddles to 1.00 with false-CONSERVED at ±30% ≤0.18 — the extension's second look is a TOST
re-decision that overwhelmingly resolves toward the true state, and its mild alpha cost is disclosed
rather than corrected (single, pre-registered, fires only on straddle). Coverage caveat (pressure-test
S10): the paired bootstrap has 7 clusters with one dominant (cs-A1 = 0.59) — percentile CIs at 7
clusters tend anti-conservative, biasing toward CONSERVED on top of the band's width; the §6 table IS
the empirical calibration of that machinery (false-CONSERVED measured ≤0.09 at ±30%), and the LOFO
secondary answers the dominant-cluster challenge directly.

## 7. Inherent limitations (disclosed)

- **(a) Seed-pooling independence:** the sim pools P1 seeds as iid; real decode noise may correlate
  within (model, probe). The between-seed SD descriptive (§3) measures this; if seeds are strongly
  correlated the effective n is smaller and INCONCLUSIVE more likely (conservative direction).
- **(b) One temperature point:** P1 tests temp=0.7 only. No temperature-response curve is claimed;
  "survives decode noise" means *at this operating temperature*.
- **(c) P2 = parallel-forms reliability** bounded by the construct definitions: it tests wording, not
  construct choice. A conserved P2 does not certify the taxonomy.
- **(d) P3 = one substitution set** (same morphology/length, nature-flavored compounds like the
  originals). Lexical generality beyond this class is not claimed.
- **(e) P4 = one permutation** (rotation placing T1 last). A tie-order MAP point, not a sweep.
- **(f) The anchor is a single epoch sample**; its judge-session noise is exactly what P0 measures and
  M absorbs. Facet-sampling noise enters via the paired bootstrap. The anchor's *generation* has no
  sampling noise (byte-deterministic).
- **(g) Scope of "stable operating point":** this scaffold family (3 symmetric achievement gists),
  this bank basis (7f), mech-11, this instrument. NOT a universal constant; model-family generality
  is the distill descriptive at best.
- **(h) Judge caching:** panel calls are cached per (response, token) within a stamp; P0's fresh stamp
  forces fresh judgments — P0 measures session-to-session noise, not cache reads. P1's temp>0
  responses are new text, so no cross-arm judge-cache reuse is possible; P2/P3/P4 responses that
  happen to reproduce committed text verbatim WOULD hit distinct stamps (fresh sessions) — stamps are
  per-arm by protocol (§ops).
- **(i) Band calibrated on committed temp-0 text only (S6-RT):** judge reliability on novel temp-0.7 /
  paraphrase-bank responses is uncharacterized and plausibly worse; the P0b spot-check (§3) measures
  it post-generation, and a >2× flip-rate excess flags the band as under-covering for the primaries.
- **(j) Environment drift vs the reused anchor (M2):** byte-determinism was established across PAST
  epochs; the launcher's determinism sentinel (2 mech models regenerated at temp 0 and byte-diffed
  against the committed anchor cache, 156/156 required) re-verifies it in the RUN's environment and
  aborts on mismatch — an Ollama upgrade / model re-pull / driver change is caught before any arm
  generates, not after.
- **(k) σ_P0 estimation width:** the instrument SD comes from ~5 judge sessions whose outcomes
  cluster into ~2 states (FRAME amendment) — a noisy SD to multiply by 3; the halt-above-floor rule
  (§3) is the guard, and the floor is expected to bind.
- **(l) Ollama seed reproducibility (N19-RT / N4-LU):** seeded decode paths are not contractual
  across model reloads / concurrent load; fresh-cache-per-arm + single-pass generation mitigates, and
  a forced mid-arm resume could mix decode states within a seed (completeness and pooling validity
  survive; "one seed = one clean path" is approximate).
- **(m) Discovery-direction multiplicity (N13-RT):** the headline conjunction is a clean
  intersection-union test, but BROKEN findings across P1/P2/P3 are per-arm α ≈ 0.05 uncorrected —
  "identifies the fragile axis" carries that qualifier.
- **(n) Empty-response cells:** `ollama_chat` no longer caches empty responses (N14-RT); a cell empty
  after 3 launcher retries surfaces as a completeness shortfall (S8), never a frozen all-ABSENT row.

## 8. Pressure-test record (rule 12 — completed 2026-07-08, before lock)

Two adversarial agents (statistical red-team + methodological legitimate-use); both verdicts
**LOCKABLE-AFTER-FIXES**; every MUST_FIX and all recommended SHOULD_FIXes folded before the lock
commit:

- **MUST_FIX (both agents, M1) — P2 integrity hard-fail:** `integrity_check` hardcoded
  EXPECT_RECALL=16; the P2 arm (cap 3 → recall 32) would SystemExit the headline-gating PRIMARY, and
  `--allow-incomplete` would have disabled ALL integrity for the arm. Fixed: `expect_recall`
  parameterized (default 16), P2 passes 32; guarded by a P2-shaped test reproducing the reviewer's
  exact failure.
- **MUST_FIX (red-team M2) — anchor environment re-verification:** the launcher now regenerates a
  2-model temp-0 sentinel and byte-diffs 156/156 responses against the committed anchor cache,
  aborting on any mismatch — environment drift can no longer silently confound the temp-0 arms.
- **MUST_FIX (red-team M3) — band ceiling:** above-floor bands HALT (P0 tool exits non-zero; analyzer
  requires `--band-above-floor-approved` + a §9-recorded decision) instead of silently widening
  CONSERVED.
- **MUST_FIX (red-team M4) — temp verbosity/truncation:** per-arm length + truncation descriptives
  pre-registered with a parity qualifier on the P1 verdict (§3); `num_predict` held at the anchor's
  120.
- **SHOULD_FIX folded:** band uses the multiplicity-specific σ with the conservativity direction
  corrected (S1/S5); band provenance is artifact-enforced — `P0_BAND.json` + launcher env guard +
  analyzer `--band-file` (S2/S7); CONSERVED licensing scoped to ±M ≈ ±34% relative, INCONCLUSIVE =
  evidential null (S3/S11/S7-LU); P1 relabeled decode-path with pre-registered disambiguators (S4);
  BROKEN-P2 forward-only asymmetry + difficulty-drift disjunction pre-registered (S5-LU); LOFO wired
  into the analyzer for the primaries (S6-LU); outcome→follow-on matrix added (S7-LU); per-arm
  completeness assert with mech-abort in the launcher (S8-LU/S9-RT); GIRAFFE gates at BOTH temp 0 and
  0.7 (S8-RT); 7-cluster coverage caveat + empirical calibration note (S10).
- **NOTEs folded:** 5-seed extension simmed (N12); per-arm α qualifier (N13); empty responses no
  longer cached (N14); intra-facet diversity report appended to ADMISSION.md — worst pair J=0.20, no
  near-duplicates (N15); anchor-in-σ note (N16, subsumed by the halt rule); seed-reproducibility and
  distill-question registrations (N19/N1-LU).
- **Survived both reviews unchanged:** the verdict/TOST branch logic (incl. CONSERVED-before-BROKEN
  precedence and the significant-but-small → INCONCLUSIVE edge), the cache-key opts derivation with
  legacy-key preservation, the headline conjunction as an IUT, the byte-layout asserts, the judge's
  refusal to write partial files, the paired-anchor justification, the P4 map arm's scope, and the
  blind-authoring admission protocol.

## 9. Locked manifest (frozen at lock; guarded by `tests/test_conservation.py`)

- Scaffolds: `CONSERVATION_TOKENS = ("limewater_feed", "saltmarsh_shard", "bayside_queue")`
  (byte-lengths 14/15/13 == the MULTIFACT tokens); `PERMUTED_ORDER = (1, 2, 0)`; renamed preamble ==
  triple modulo the 3 token substitutions (890B, replacement-T1@378); permuted preamble = same
  line-set, T1@650 (slot 3).
- P1: temp=0.7, seeds {11,12,13} (+ the single {14,15} extension per §3); opts folded into generation
  cache keys (`opts:temp=0.7;seed=<s>`), judge reconstruction passes the same flags.
- Bank: `tools/probes_conservation.py` — sha256
  `ce8d56492d768e30acd0f96eb237f24c10443241374bf6580b4a4771646c4d07` (blind-authored + blind-classified
  κ=1.0, admission record `conservation/ADMISSION.md`; 7 facets × 4 wordings, EXPECT_BEM=28). P2 runs
  `--rephrasings-per-original 3`, which expands the recall mode too (8×4=32) → **60/model expected**
  (28 BEM + 32 recall); driver and judge share the one cap, keeping reconstruction consistent.
- Band: `M = max(0.061, 3·σ_multiplicity_P0)`; artifact `conservation/P0_BAND.json` (halt flag if
  above floor); the P0 output block + resulting M are appended to this section before generation.
  Confirmatory analysis uses `--band-file conservation/P0_BAND.json`; an above-floor band additionally
  requires `--band-above-floor-approved` + Josh's decision recorded here.
- Analyzer: `tools/conservation_analyze.py` (deterministic, seed 0; LOFO wired for P1/P2); judge:
  `multifact_judge.py` `--scaffold-renamed/--scaffold-permuted/--conservation-bank/--temperature/
  --gen-seed` (P2 expect 60/model).
- Ops: fresh timestamped caches `~/cdms_cache/conservation_<arm>[_s<seed>]_<ts>`; one launcher with:
  band env guard (`CDMS_CONSERVATION_BAND`, refuses to start unset), determinism sentinel (2 mech
  models, 156/156 byte-diff vs the committed anchor cache, abort on mismatch), GIRAFFE gate at temp 0
  AND 0.7, arm-aware byte/position asserts, per-arm per-model completeness assert (mech shortfall
  aborts the ladder; distill shortfall logs loud + continues); model-outer; per-arm judge stamps
  `conservation_<arm>[_s<seed>]`; judge cap $15/arm; expected cost ≈ $10 (P0) + ~$42 (P1–P4) + ~$2
  (P0b) ≈ **$54**; Sparky ≈ **14.5 h** incl. the sentinel (coordinate with Nate ad hoc).
