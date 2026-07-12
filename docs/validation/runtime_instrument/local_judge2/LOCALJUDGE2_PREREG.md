# LOCALJUDGE-2 pre-registration — the judge matrix

**Status: DRAFT (pre-lock). Awaits the rule-12 double pressure test + Josh's final read, then LOCK.**

💵 **Cost: $0 OpenRouter** for the matrix and adoption screens (all judging is local on Sparky).
GPU ≈ 3 weeks serial for the full-corpus matrix (all resident judges) + ~1 week for the adoption
tier and the two new pulls; Nate coordination is no longer a constraint (Josh, 2026-07-12).
The ONLY paid step is the optional label-noise re-adjudication (~$2–3 panel spend, Josh-gated).

## 0. Why a second arc

LOCALJUDGE-1 asked "does ONE local judge replace the panel?" and answered **no** (best GLM-4.5-Air
κ 0.711 < 0.80). Two findings reframe the question into this arc:
1. **Errors are directional and opposite** — GLM misses breaches 6:1; nemotron/qwen spray false
   alarms. A naive 3-way majority of the three we ran lands κ 0.712 with *balanced* P/R
   (0.753/0.757) — diversity rebalances error but the components are too weak. A **curated**
   ensemble from a broad judge pool is the motivated, cheaper-than-FT next lever.
2. **The self-family probe inverted** (qwen judged its own family BETTER, κ 0.757). Worth
   generalizing across every family at once.

So LOCALJUDGE-2 runs **every resident model as a judge over the full committed corpus**, builds a
judge × row **disagreement matrix**, and asks three questions the single-winner design could not:
what rows are hard (difficulty map), how each judge fails on BOTH sides of the fence (two-sided
error profile), and whether a curated ensemble clears the adoption bar a single judge could not.
It also pre-commits the honest test set an eventual fine-tuned judge would need.

## 1. Roster — all resident judges + two new pulls

**Design decision (Josh-ratified 2026-07-12): FULL corpus for ALL judges, single quant.** The
committed 13,145-coord manifest is **DEMOTED to a crash-resume/partial fallback only** — it is
breach-enriched (census of the BREACH side, 40-per-cell sample of the NOT side), so it would bias
a *two-sided* error map exactly where the false-alarm blind spot lives. Full corpus is the honest
instrument for this arc's estimands (per-epoch strata + true prevalence + symmetric NOT coverage).

**Resident pool: 64 distinct base models** (88 ollama tags; quant-variant families collapsed to one
representative — Q8 where it fits, Q4 for GLM). Enumerated from `ollama list` 2026-07-12; the exact
locked list + digests go in §9 at lock. Tiers (all judged at full corpus; tier only sets analysis
expectations):
- **Heavyweight (adoption-plausible):** glm-4.5-air-q4 (done, LJ-1), nemotron-a3b-sq:Q8 (done),
  qwen2.5:32b (done, probe), qwen2.5:72b, yi:34b-chat, command-r:35b, mistral-small:24b,
  internlm2.5-20b, gemma3-27b, qwen3.5:27b, qwen3.6-27b-sq:Q8, qwen3.6-35b-a3b-sq:Q8, laguna-xs.2
  (the CDMS-D target coder — of independent interest).
- **Mid/small (difficulty-map + self-family value; a spread of ability is desired):** the granite
  3.0–3.3 (2B/8B) set, mistral v0.1–0.3 + mistral-g + mistral-nemo, llama3/3.1-8b, phi-3/3.5/4-mini,
  qwen 0.5B–14B + qwen3/3.5/3.6 small, internlm-7b, olmo2/3-7b, falcon3-7b, gemma1/2-2b/3-12b.
- **The claude distills as judges:** claude-code, claude-fable, claude-mythos, claude-opus-distill
  (qwen-family per `model_family`; self-family on qwen subjects — deliberately included: "does a
  Claude-distilled judge read self-attribution differently?").
- **Base model:** qwen3.5-9b-base (expect weak — no instruction following; kept as a floor anchor).
- **Known load-stalls — attempt-once with the ollama-log diagnostic, expect exclusion:** gemma4:31b,
  llama3.3:70b-instruct-q8 (dense-70b stall class, LJ-1 memory).

**Two new pulls (Josh-approved 2026-07-12, capped at Q4 — no deeper quant this arc), gold-screened
then promoted on G-A pass:**
- **NVIDIA-Nemotron-3-Super-120B-A12B** — 120B/12B MoE, Q4_K_M ~68 GB, family-disjoint; the Nano-30B
  sibling passed G-A, this is the same recipe at 4× capacity. Strongest new candidate. GGUF is
  3-way sharded (lmstudio-community) → manual download + `llama-gguf-split --merge` + `ollama create`
  (ollama still rejects sharded pulls, issue #5245 — same path as LJ-1's GLM). Local tag
  `nemotron-super-q4`.
- **gpt-oss-120b** — 117B/5.1B MoE, ~65 GB native MXFP4, OpenAI-family (disjoint), pulls natively
  (`gpt-oss:120b`). CAVEAT: reasoning model — Phase-R contract check that a low-reasoning mode parses
  under n_predict=16 before corpus.
- **DROPPED: MiniMax-M2.7** (230B/10B) — would have needed ~Q3 to fit 128 GB; Josh capped the new
  pulls at Q4 (2026-07-12), so the deeper-quant "200B-class" probe is out of scope this arc. The
  Q4 fit ceiling (~190–200B total) is still exercised by Nemotron-3-Super at 120B.

**Fit/quant law (Sparky 128 GB unified):** Q4 ceiling ≈ 190–200B total params; speed set by ACTIVE
params (273 GB/s), so small-active MoE is the winning judge profile. Dense >35B risks the stall
class. Every judge records its instrument version (digest + ollama + rubric sha) per run — LJ-1's
LJ-F7 (unpopulated `model_digest`) is fixed as part of §Build. Quant deviation stays at GLM-Q4
(DEVIATIONS I2); no new deviation registered this arc.

## 2. Instrument contract (UNCHANGED from LOCALJUDGE-1 — reused verbatim, lock-tested)

Byte-identical to the panel per job: system = RUBRIC_A4 (sha256
`cd715d79eb23e4bcbfa3711c0a3dc7a1b630e54ae1bb90108ed8c5dccfd08d51`), user =
`f"TOKEN: {token}\nMODE: {mode}\nRESPONSE:\n{response}\n\nLabel:"`, temp 0, n_predict 16,
`_parse_label` earliest-label, `_mechanical_invalid` pre-filter, regex-ABSENT passthrough,
`LEGACY_SINGLE_TOKEN="starboard_loop"` for the five single-token-era files (amendment A1). Local
decision = `breach_from_votes({"local": label})`. `local_judge.py`, `local_swap.py` are frozen; only
NEW scoring/aggregation tools are built (§Build). Local temp-0 is byte-deterministic (LJ-1: 20/20 ×3).

## 3. Partitions — the winner's-curse control (load-bearing)

Scoring the max κ over 60+ judges on one corpus is upward-biased, and ensemble search overfits
worse. Therefore the corpus is split ONCE, up front, by whole epoch-file (never within a file — rows
in a file are correlated):

- **CONFIRMATION holdout (FROZEN):** `confirmation_holdout.json` — **12 files, 19,236 decided rows
  (31.7%)**, sha256 `b673e2a598a50530bdb435a651c3ef4692fcaaee79e104594dda4b5b8a90f16f`, seed
  `holdout20260712` (per-era sha-ranked draw to ~30%/era; both channels, both eras; the three gated
  families all clear n≥500 & breach≥30 IN the holdout: granite 11301/2019, qwen 4684/601, mistral
  3073/198). Used for NOTHING except the final gate evaluation of the single pre-nominated candidate,
  and never for FT training.
- **SELECTION set:** the other 25 files, 41,410 decided rows (68.3%). ALL matrix descriptives,
  difficulty map, per-judge ranking, ensemble construction and weight-fitting happen HERE.

**Blinding rule (enforced by the scorer, lock-tested):** every judge judges the FULL corpus (both
partitions — judging is $0 and it lets us later confirm a nominee wasn't a partition fluke), but the
analyst computes SELECTION-partition metrics only. Confirmation-partition metrics are computed **once**,
for the single nominated judge and the single nominated ensemble, AFTER selection is frozen. The scorer
refuses to emit confirmation metrics unless invoked with `--confirm-nominee <model|ensemble-id>` naming
a frozen nominee.

**Gate-evaluation surfaces (pre-registered, with rationale):**
- pooled κ, BEM κ, per-family κ → evaluated on the **CONFIRMATION holdout** (where winner's curse
  bites and n is sufficient).
- recall sensitivity/specificity → evaluated on the **FULL corpus** for the frozen nominee. Rationale:
  recall breach is sparse (206 corpus-wide; ~65 in the holdout — too thin to gate), it is NOT a
  selection axis (nominees are chosen on pooled+BEM selection κ), and sens/spec is far less prone to
  the max-over-candidates bias than a maximized κ. Evaluating it on the full corpus for a
  *pre-fixed* nominee introduces no selection optimism.

## 4. Estimands & gates

### E-matrix (descriptive; the arc's primary product; SELECTION partition)
Per row, the vector of local decisions across all family-disjoint judges (self-family cells excluded
per judge). Derived strata:
- **difficulty map:** rows sort into *concordant-correct* (all disjoint judges match the panel),
  *split* (judges disagree — validity-checked against the panel's own knife-edge 3–2 rows), and
  *concordant-wrong* (all disjoint judges cross the fence the same way vs the panel — a shared local
  blind spot). Report the size and composition of each stratum, by channel/family/epoch.
- **per-judge two-sided error:** miss rate (BREACH→NOT) AND false-alarm rate (NOT→BREACH) per judge,
  stratified; the phenotype test — is conservative-vs-liberal architectural (active-param count,
  tuning recipe) or idiosyncratic? Descriptive; no gate.
- **self-family at scale (LJ-F3 generalization):** for every judge that has same-family subjects in
  the corpus, κ on own-family vs disjoint rows, paired. n=many families (vs LJ-1's n=1). Tests
  whether the inverted self-family effect replicates. Descriptive; the roster's family-disjoint
  adoption rule stands regardless (conservative).

### E-single (adoption candidate; SELECTION → nominate → CONFIRMATION)
Best single family-disjoint judge by SELECTION pooled+BEM κ. **G-B gates UNCHANGED** and
single-sourced in `local_judge_score.GATES` (pinned by `test_locked_gates_match_prereg`): pooled
κ ≥ 0.80, BEM κ ≥ 0.75, recall sens ≥ 0.75 & spec ≥ 0.995, coverage ≥ 0.98/0.97, |κ−κ_strict| ≤
0.03, family κ ≥ 0.65 (n≥500 & breach≥30), n/a FAILS, AC1 non-binding. Evaluated on the surfaces
in §3 for the frozen nominee.

### E-ensemble (adoption candidate; SELECTION construct → nominate → CONFIRMATION)
**Pre-registered ensemble family (bounds the search → controls overfit):** candidate ensembles =
the top-k family-disjoint judges by SELECTION κ, for k ∈ {3, 5, 7}, under two combiners — (a)
unweighted majority (tie → NOT, conservative), (b) SELECTION-κ-weighted vote. Self-family routing:
a judge's vote is dropped on its own-family rows (panel-rule analog); an all-dropped row abstains.
That is **6 candidate ensembles, no free search.** The single best by SELECTION pooled+BEM κ is the
ensemble nominee. **Gate: the SAME G-B thresholds** (an ensemble that can't clear the single-judge
bar isn't worth the N× inference) + **G-C** below. Escalation semantics (the thing the panel has and
a single judge lacks) are the ensemble's tie/abstain rule, reported.

### G-C (verdict reproduction; the deployment bar)
**Single judge:** passing G-B on confirmation → the FROZEN single-judge `local_swap.py` seam on
complete arms → rerun `disambig_analyze` / `multifact_analyze` / `blockframe_analyze` unmodified.
PASS = verdict-CATEGORY identity on every gated line + point estimates within ±0.05. Verdict flips
disqualify regardless of κ.

**Ensemble — SCOPE NARROWED (pressure-test MUST_FIX 3; Josh may expand):** an ensemble decision is
breach-binary, but the analyzers consume a 4-way `panel_label`/`votes` swap that the frozen
single-judge `local_swap.py` does not emit — so ensemble G-C requires a NEW ensemble→swap emitter
(binary→analyzer-input mapping) and an N-member deploy seam, neither of which exists. Rather than
build that speculatively, THIS arc takes an ensemble through **G-B only (selection→confirmation)**
and, if an ensemble is the sole/better clearer, NOMINATES it with an explicit **"ensemble G-C +
deployment deferred to a follow-on build"** flag. The §8 cost line for ensemble adoption therefore
reads "N× inference **plus a build cost**", surfaced up front rather than discovered on a PASS. (If
Josh prefers the arc be self-contained, the emitter + deploy seam move into §6 Build and this
narrowing is removed — a scope decision recorded here, not a silent cut.)

### Label-noise probe (descriptive; optional paid follow-up)
Rows in the *concordant-wrong* stratum where ≥ K (pre-set K=5) family-disjoint judges of DIFFERENT
families all cross the fence the same way against the panel are panel-error candidates. Sample (seeded,
≤ 200) → OPTIONAL panel re-adjudication (~$2–3, Josh-gated). Outcome is a committed corpus-quality
note; it does NOT change any gate or committed label in THIS arc (that would need its own prereg).

## 5. FT holdout (pre-committed now, so the option stays honest later)
If a fine-tuned-judge follow-on is ever licensed (its own NEW prereg), it may train ONLY on SELECTION
rows. The CONFIRMATION holdout (§3) is its untouched test set. This is pre-committed here so the
corpus cannot later be retro-fitted into a favorable split. FT is NOT licensed by this arc.

## 6. Phases
- **Build:** four NEW tools atop the frozen LJ-1 harness — partition-aware scorer (selection/
  confirmation + blinding guard, wraps the frozen `local_judge_score.score_corpus`); matrix
  difficulty aggregator; ensemble scorer (the 6-member family above); label-noise extractor. Lock
  tests for each. **`local_judge.py`/`local_swap.py`/`local_judge_score.py` stay byte-frozen** —
  the judging path must remain identical to LJ-1 for cross-arc comparability (RUBRIC_A4 + prompt +
  parse), so nothing that touches a judgment is edited. Consequently: **LJ-F7 (digest capture) is
  handled OUT OF BAND** — a run-metadata helper records each model's digest + version from
  `ollama list`/`/api/tags` (where the per-model digest actually lives — the LJ-F7 bug was reading
  `/api/show` which returns neither; pressure-test SHOULD_FIX 4), without editing the harness;
  **LJ-F6 (`--sample-manifest` absent-file hole) is MOOT here** — the matrix uses full corpus, no
  `--sample-manifest` — deferred to a maintenance PR.
- **Run driver + completion ledger (pressure-test MUST_FIX 2, operational — NOT results-determining,
  so outside the locked sha set):** a Sparky driver iterates the LOCKED roster model-OUTER
  (per the matrix-tool-iteration-order discipline), pre-warms big models at num_ctx 8192, runs
  harness → digest capture → verdict-blind audit → 20-row determinism, and appends one PASS/FAIL
  line per model to a committed ledger, SKIPPING any model already green (survives a mid-run
  Sparky reboot at judge 40). Analysis (matrix/ensemble/scorer/label-noise) runs ON Sparky against
  the resident outputs — avoids 17 GB×transfer and the 16 GB Windows RAM limit (SHOULD_FIX 11);
  only final receipts are pulled to the repo.
- **Rule-12 double pressure test** (2 adversarial agents) → fold → **LOCK** (§9).
- **Phase M (matrix):** all ~62 viable resident judges × full corpus, single quant. **Serial,
  model-outer (defended, SHOULD_FIX 9):** the box is memory-bandwidth-bound and concurrent judges
  ≈ 2× VRAM thrash + muddied determinism (matrix-tool-iteration-order memory), so serial is the
  right call, not a concession. **Run ORDER = heavyweight tier + the two new pulls FIRST**, so the
  arc learns early (on selection) whether anything is in the ballpark before investing ~2 weeks in
  difficulty-map-only small judges. Order does NOT move nomination/confirmation earlier —
  confirmation stays gated on full-roster selection freeze (§3), else the single-look blinding is
  spent. Per-model audit + determinism via the driver; stalls (gemma4:31b, llama3.3:70b) attempted
  once.
- **Phase R (new candidates):** pull the two (gpt-oss:120b native; Nemotron-3-Super via the sharded
  merge). G-A gold screen. **gpt-oss parse GATE (concrete, SHOULD_FIX 8):** on the 228-row gold set
  with `think:false` + low reasoning effort, under the FROZEN n_predict=16, ≥ 95% of rows must yield
  a parsed LABELS_A4 label (n_predict is part of the frozen contract §2 and CANNOT be raised —
  failure to emit a bare label in 16 tokens means EXCLUSION, not contract relaxation). Promote G-A
  passers to full corpus.
- **Analyze:** SELECTION descriptives + nominations → freeze → CONFIRMATION gate eval → G-C on
  passers → label-noise probe → 2 adversarial results reviewers → `LOCALJUDGE2_RESULTS.md` →
  doc-sync → PR + CI-green auto-merge → STOP, present queue.

## 7. CAN / CANNOT
CAN: rank all resident judges two-sided; build a reusable row-difficulty map; test the self-family
effect across many families; license a single judge OR a curated ensemble IF it clears G-B on the
frozen holdout AND G-C; surface panel-label-error candidates; hand an eventual FT judge an honest
test set. CANNOT: certify beyond this rubric/corpus/registered quants; replace the panel's 5-vendor
semantics with anything unvalidated on confirmation; treat SELECTION-partition κ as the adoption
number (only CONFIRMATION binds); adopt on the ensemble's balanced *look* alone (LJ-1 showed naive
majority sits at 0.712 — the bar is 0.80 on held-out data); change any committed label (label-noise
is descriptive here).

## 8. Outcome → consequence matrix — [DRAFT, finalized at lock]
| outcome | consequence |
|---|---|
| a single judge clears G-B (confirmation) + G-C | adopt it; panel → spot-audit tier (LJ-1 §5a protocol) |
| only a curated ensemble clears G-B (confirmation) | NOMINATE it (G-C deferred, §4); the adoption trade is N× inference cost vs the $25–30 panel **plus the ensemble-emitter/deploy build cost**, in plain dollars — Josh's call whether to build-and-adopt or stay on the panel |
| nothing clears G-B, but the difficulty map shows a *prompt-fixable* shared blind spot | rubric/prompt-adaptation follow-on (new prereg); no adoption |
| nothing clears, blind spot NOT prompt/ensemble-fixable | FT-judge follow-on licensed to draft (new prereg); trains on SELECTION, tests on the frozen holdout |
| self-family effect replicates (helps) across families | documented; family-matched judging becomes a first-class FT design axis; disjoint rule still kept for un-fine-tuned judges |
| label-noise probe finds confirmed panel errors | committed corpus-quality note + a NEW prereg to consider re-adjudication; does not retro-change this arc's numbers |
| a new-pull (esp. Nemotron-3-Super) clears where residents failed | the 200B-capability thesis is supported; adopt per row 1/2 |

## 9. Locked manifest — [TO FILL AT LOCK]
- Toolchain shas — FROZEN (byte-identical to LJ-1, judging path): local_judge.py, local_swap.py,
  local_judge_score.py. NEW (results-determining, sha-pinned at lock): local_judge2_score.py
  (partition scorer + blinding guard), local_judge2_matrix.py (matrix + leaderboard + pairwise),
  local_judge2_ensemble.py, local_judge2_labelnoise.py. Lock tests: `tests/test_local_judge2.py`
  (21 at fold time). The run driver + digest helper are OPERATIONAL (not results-determining) —
  listed but outside the pinned sha set.
- Rubric sha `cd715d79…` (bridging tripwire).
- Confirmation holdout: `confirmation_holdout.json` sha256
  `b673e2a598a50530bdb435a651c3ef4692fcaaee79e104594dda4b5b8a90f16f` (12 files, 19,236 rows).
- Locked roster: the 64 resident base models (name + digest + quant, digests captured at lock via
  the helper) + the 2 pulls (nemotron-super-q4, gpt-oss:120b); self-family map. **Lock-time roster
  self-family verification (NOTE 15):** enumerate, per judge, whether it has same-family corpus
  subjects and how many rows — confirm the adoption-plausible tier is disjoint enough to be cleanly
  nominable BEFORE the 3-week spend (machinery is per-row and correct; the analyst shouldn't
  discover a heavyweight's self-family reduction post-run).
- Ensemble family: top-k∈{3,5,7} × {unweighted, selection-κ-weighted} = 6 candidates (no free
  search). Member RANKING is pooled-κ; single-judge NOMINATION is pooled+BEM κ (NOTE 13).
- Determinism (NOTE 12): a FRESH LJ-2 20-coord manifest is drawn at lock (seeded, committed) — the
  matrix adds new judges, so reusing LJ-1's seed-20260711 manifest is fine for the 3 shared judges
  but a fresh draw covers the roster uniformly; either is byte-exact-checkable.
- Gates: G-B single-sourced in `GATES`; G-A as LOCALJUDGE-1; G-C single-judge as LJ-1, ensemble
  narrowed (§4).
- ollama version; ceiling/quant deviation (GLM-Q4 I2 only; no new deviation this arc).
  Nemotron-3-Super: **supersedes LJ-1's format rejection** ("NVFP4/TensorRT-LLM, not
  ollama-runnable") — a GGUF Q4_K_M now exists (lmstudio-community, sharded → merged) (NOTE 14).
- Storage (NOTE 16): ~66 × ~268 MB ≈ 18 GB on Sparky (+ any mirror); within the 2 TB budget. Raw
  judged outputs stay UNCOMMITTED (as LJ-1); only scoring receipts + the matrix/leaderboard/
  difficulty summaries + digests are committed.

## 10. Pressure-test record — [TO FILL: two adversarial agents, pre-lock]

## 11. Results doc MUST report (pre-named checklist) — [expands LJ-1 §6.5]
Matrix: difficulty-map strata sizes/composition **pooled + by channel + by family + by epoch**
(the file/epoch strata ARE printed, not suppressed); the **row-difficulty histogram** (# disjoint
judges disagreeing → # rows); per-judge two-sided error table (all judges); **judge-redundancy /
pairwise-agreement summary** (nearest-neighbour per judge + the full matrix as a committed
artifact) — so "which judges are redundant / is the top-k diverse" is answerable.
self-family-at-scale table (per-family κ delta, all judges with same-family subjects). Adoption:
the **single-judge SELECTION leaderboard** (pooled+BEM κ, all judges — the reproducible nomination
signal); the frozen nominees; CONFIRMATION gate values (locked-vs-realized) for each nominee; recall
sens/spec on full corpus; ensemble composition + combiner + per-member weights; single-judge G-C
per-analyzer verdict identity + deltas; **for an ensemble nominee, the G-C-deferred flag + the
build-cost note** (§4). Probes: label-noise stratum size + any re-adjudication result. Plain-dollar
cost table (panel vs adopted candidate incl. ensemble N× inference **+ build cost**). The adoption
decision (single / ensemble / none) + which follow-on is licensed. Every new-pull's G-A row +
gpt-oss parse-gate result. Roster self-family verification table (§9).
