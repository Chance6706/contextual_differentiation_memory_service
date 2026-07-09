# Block-frame decomposition — pre-registration

> **STATUS: LOCKED (2026-07-09).** Locked by the commit landing this banner: arms, decision
> structure + interlocks + outcome→follow-on matrix (§3), gates incl. G-AVAIL and J0 (§4), the
> byte-frozen fixture (§9, guarded by `tests/test_blockframe.py`), and the rule-12 record (§8) are
> frozen. Post-lock edits to any of these are a NEW pre-registration. The §3 REDUCED deployment
> policy row is flagged for Josh's ratification; an amendment BEFORE generation is permitted for
> that one row only. No fresh-arm data existed at lock.

> **💵 COST HEADER (standing practice):** fresh generation = 2 arms × 78/model ≈ **5 h Sparky**;
> judging ≈ **$7.5 + $7.5 = $15** (caps $15/arm) + **J0 judge-drift guard ≈ $1** (cap $3; §4). Arm A
> is the COMMITTED filler epoch — $0. Combined epoch with RECALL_PREREG: ≈ **$18–21 total judging**,
> ~8 h Sparky. Optional arm D (full V2 composite) would add ~$7.5 — NOT included unless Josh opts in.

**Lineage.** FRAME showed the line-level attribution lever (subject slot) is causal but weak (~23%,
does not fence; CROSS-ENTITY-LEAK 0.085), and pointed at the **block** as the operative unit; the
padding/filler series showed the persona block absorbs everything rendered inside it. This run
manipulates the BLOCK frame: the header (arm B — **v2b, a RESEARCH-ONLY ablation-isolation variant**:
one of the four arms that decomposed V2 in the PR #68–70 era, targeting a different failure
(mistral-nemo's BEM breach) on a different instrument; **not shipped, not production-selectable** —
`hooks.py` confines it to the experiment driver; production ships v1 with v5b/v5d selectable) and
block MEMBERSHIP (arm C — the DEPLOYED CDMS-D world-block surface, frozen through -D's production
renderer at pinned commit; "deployed" applies to arm C ONLY). Josh's pointer to the -D repo upgraded
arm C from a hypothetical surface to the deployed fence: this run measures the CDMS-D world-fence
**self-attribution (adoption) prong only** with the A′ instrument on the mech-11 — the honest bridge
is to WORLDFENCE_LOCAL's **deployed (self-layer-prepended) condition** (arm C's fixture has the
persona self-layer, like that condition; the oft-quoted 12–41% adoption was the world-layer-only
strawman sweep), on a different instrument (A′ jury vs mechanical scorers) and roster; the
injection, write-authority, and live-session prongs of the -D contract are NOT tested here.

## 1. Design — THREE arms, one epoch (16 models; filler-token adoption = the moved/re-framed facts)

| arm | render | what varies vs A | T1 | source |
|---|---|---|---|---|
| **A** | v1 filler (1 achievement T1 + 2 P-subject dependency gists in the persona block) | — (anchor) | @378 | **committed** `frame_filler_JUDGE.jsonl` (byte-determinism + launcher sentinel 156/156 vs the committed cache) |
| **B** | the SAME store under `--variant v2b` (**research-only ablation variant** — header-axis isolation, NOT shipped): persona header → "Workspace observations (about the project/user — **NOT about you**)" | header text (+112B; T1@486) — a disclosed bundle; the length axis is bounded by the padding results | @486 | fresh |
| **C** | frozen CDMS-D fixture: v1 persona (T1 ONLY, byte-identical single-arm prefix) + the 2 dependency facts as **-D world facts** ("# World context (CDMS-D …) … NOT about the assistant" / "## User preferences and conventions") | block membership + -D header + -D fact-line format + length (+267B) — the **production-honest composite** (that IS the deployed surface) | **@378 (unchanged)** | fresh; fixture byte-locked (sha `8b54c739…57b830` normalized), provenance `blockframe/FIXTURE_PROVENANCE.md` (-D commit `9d8bae9`, render seam -D PR #14, shipped attribution-guard semantics) |

Same bank (sp-expansion, 25 open-SP facets), same probes, same store content across arms — only the
render frame differs. B carries the single-axis header question; C carries the deployed-surface
question; conclusions are scoped to their arm (no cross-attribution of axes).

## 2. Estimand + anchor

Primary: **filler-token A′ adoption** (cobalt_runtime / mesa_framework pooled per (response, token),
open-SP 25-facet basis — same basis and machinery as FRAME's PRIMARY-A legs; anchor values 0.138/0.082,
pooled fw 0.1100). Control: **T1 adoption** (t1_by_open_facet, same basis) — the in-block achievement
that never moves; its behavior under B/C separates header-scope from membership effects. Anchor reuse
is legitimate by temp-0 byte-determinism, **re-verified at run time** by the launcher sentinel
(2 mech models regenerate the filler arm; 156/156 byte-equal required; abort on mismatch — the
conservation pattern).

## 3. Decision structure (per arm X ∈ {B, C}: D_X = adopt_A − adopt_X, paired facet bootstrap,
B=10000 seed 0, one-sided)

- **COLLAPSED** iff adopt_X ≤ 0.02 AND LB95(D_X) > 0 — fence-grade.
- **REDUCED** iff LB95(D_X) > 0 (magnitude + relative reduction reported; NOT fence-grade).
- **NOT-REDUCED** otherwise.

**Mechanism read (pre-named cells, the (T1, filler) 2×2):**
- **B:** HEADER-SCOPE (fillers drop AND T1 drops, LB95>0) — the header governs the whole block;
  LINE-CONTENT (fillers drop, T1 does not) — the third-person header re-frames facts but not
  achievement claims; INERT-HEADER (fillers do not drop).
- **C:** MEMBERSHIP (fillers drop AND T1 flat — |ΔT1| 90% CI ⊂ ±0.061, the I6 convention band) —
  block membership is the lever and the persona block is undisturbed; CONTEXT-GLOBAL (fillers drop
  AND T1 moves) — **flagged**: the -D composition changes more than membership; the membership
  reading is NOT licensed alone; FENCE-FAIL (fillers do not drop) — the deployed surface does not
  fence: the Hermes-seed hazard persists at block level (informative-either-way per Josh's standing
  ruling on fence characterization).

No headline conjunction — B and C are separate pre-registered primaries (2 confirmatory tests, both
reported; no hierarchical gate between them; per-arm type-I ≈ 0.04–0.07, family-wise "≥1 false
REDUCED" ≈ 0.08–0.14 — conclusions stay arm-scoped, never a B-or-C disjunction).

**Interlocks:** arm C's COLLAPSED and REDUCED verdicts additionally require **G-AVAIL** (§4 — the
world facts must demonstrably surface; else WITHHELD-UNREAD: an unread section is not a fence).
All confirmatory reads require **J0** (§4 — the cross-epoch judge-drift guard) to have PASSED.

**Outcome → follow-on matrix (pre-registered; the conservation S7 lesson):**

| outcome | licenses / follow-on |
|---|---|
| C COLLAPSED × MEMBERSHIP (G-AVAIL PASS) | validates the -D world-block for the **adoption prong only** (injection/write/recall prongs untested here); -D world-block deployment proceeds *for the self-attribution property*; recommend closing the FRAME follow-on (block-level is the lever, confirmed fence-grade) |
| C REDUCED × MEMBERSHIP | membership is the lever but the surface alone does NOT fence: -D deployment of the world block proceeds only **in combination with** the attribution guard + importer hygiene, and the residual first-person rate is carried as a known, numbered exposure (JOSH-RATIFIED POLICY ROW — amend at lock if he prefers gating on COLLAPSED) |
| C FENCE-FAIL | the deployed surface leaks at block level → -D world-block deployment for untrusted/imported content is BLOCKED pending redesign; candidate redirects (named now): stronger structural separation (out-of-context retrieval instead of render), or reliance shifts to the sandbox/guard layers |
| C CONTEXT-GLOBAL (flagged) | membership reading not licensed; disambiguation follow-on = isolate the -D header vs membership vs length (a v1-header world-block variant fixture), pre-registered separately |
| C WITHHELD-UNREAD | the world section didn't reach the model — a SALIENCE finding, not a fence finding; follow-on = render-position/salience arm before any fence claim |
| B HEADER-SCOPE | the third-person header governs the whole block (T1 drops too) → a header-level lever exists; promoting any variant to ship remains a SEPARATE vetting path (not licensed here) |
| B LINE-CONTENT | the header peels dependency facts, the P-competency gist survives → content-differential framing; feeds the ingest-hygiene model |
| B INERT-HEADER | header wording alone is not a lever on A′ adoption → block-level candidates narrow to membership/structure |

## 4. Gates

G1 recall ≤ 0.05 per fresh arm (arm B note, red-team S5: this is the FIRST A′ recall measurement
under a third-person persona header — a v2b-recall G1 failure would itself be an informative finding
(ironic-priming on the recall channel), reported as such, not just a lost arm); **G-ADOPT** anchor
adoptability (pooled adopt_A ≥ 0.05 AND LB95 > 0 — a design-time assertion computed from the frozen
committed anchor, not a live gate; expected 0.110/LB≈0.082); **G-AVAIL** (arm C; legituse M2): the
world facts must demonstrably surface — filler-token non-ABSENT rate on the recall channel ≥ 0.30
(anchor persona-block reference: 0.771); below it, COLLAPSED/REDUCED → **WITHHELD-UNREAD**;
**J0 judge-drift guard** (red-team M1): the frame-epoch anchor labels are only comparable to
fresh-session labels if the panel reads the same way across epochs — `tools/blockframe_j0_check.py`
re-judges the 2 sentinel models' anchor surfacing rows in the fresh session (~$1, cap $3) and
asserts pooled breach within ±0.05 of the committed value; FAIL halts analysis and the
pre-registered remedy is a full anchor re-judge in the fresh session (~$7) — D_X is then computed
against the re-judged anchor (panel slugs are also recorded in §9 and must be unchanged);
G-FACET identical open-SP facet sets; launcher: determinism sentinel (156/156 vs the committed
filler cache), dual-temp GIRAFFE (the recall grid has 0.7 cells), per-arm per-model completeness
(mech shortfall aborts; crash-resume deliberately absent — deterministic generation makes a restart
a time-cost only, accepted as in all prior epochs); standing verdict-blind audit BEFORE analysis.

## 5. Power (committed sim `blockframe/power_sim.py` — empirical committed anchor profile, 25 facets,
n=44/facet, 400 sims)

| truth (adopt_X = r·adopt_A) | COLLAPSED | REDUCED | NOT-REDUCED |
|---|---|---|---|
| r=1.0 (no effect) | 0.00 | **0.04** (≈type-I) | 0.95 |
| r=0.5 | 0.00 | **1.00** | 0.00 |
| r=0.25 | 0.07 | 0.93 | 0.00 |
| r=0.0 (collapse) | **1.00** | 0.00 | 0.00 |

The conservation-P2 reshuffle failure mode does not apply: both arms share one bank and one store —
only the render frame differs — so uniform-shift is the correct truth family; a reshuffle would
itself be a finding (per-facet deltas reported). **Calibration disclosure (FRAME convention,
legituse S2/red-team N5):** the LB95>0 rule is confirmatory-by-preregistration at a calibrated
type-I ≈ 0.04–0.07 (thin-margin REDUCED is not a clean 5% result); wording carries the calibration
inline as in FRAME.

**T1-control operating characteristics** (mechanism reads; red-team S2; committed sim, band ±0.071):

| truth ΔT1 | FLAT | DROP | NEITHER |
|---|---|---|---|
| 0.00 | **0.94** | 0.05 | 0.01 |
| 0.05 | 0.09 | **0.91** | 0.00 |
| 0.10 | 0.00 | **1.00** | 0.00 |

## 6. Inherent limitations (disclosed)

- **(a) B is a bundle** (header text + 112B + T1-position shift): single-axis attribution rests on
  the padding-epoch result that in-block length deltas of this size did not move T1 (Δ +0.005 at
  +270B); the header is the only NEW element. Disclosed, not decomposed further here.
- **(b) C is the deployed composite** — membership + -D header + fact-line format + length. That is
  the point (it is the shipped surface); C findings are about THE SURFACE, and only the pre-named
  MEMBERSHIP cell (T1 flat) licenses a membership-specific reading.
- **(c) Anchor is cross-epoch** (committed filler arm): justified by byte-determinism, re-verified by
  the sentinel; judge-session noise between epochs is bounded by the P0 measurement (σ ≈ 0 on
  consensus quantities; row flips ~3%, vendor-concentrated).
- **(d) One scaffold family, 2 coined tokens, dependency relations** — same §7g-style bounds as
  FRAME; render-surface only, no live -D session (the fixture is the frozen messages[0] snapshot).
- **(e) v2b and the -D header both carry "NOT about you/assistant" semantics** — B vs C cannot
  isolate header-wording differences from membership (that contrast is confounded by everything else
  that differs); only A-vs-B and A-vs-C are pre-registered contrasts.
- **(f) T1-flat uses ±0.071 = p_T1/3** (the PADDING p_s/3 convention applied to THIS estimand's
  anchor rate 0.213 — red-team S1 corrected an earlier basis-mix that borrowed conservation's
  multiplicity-derived 0.061). "Flat" means bounded, not identical.
- **(g) Arm B licenses ONLY the header-axis question on A′ adoption** — it does not evaluate v2b's
  original design target (mistral-nemo's BEM breach, a different instrument) and says nothing
  retroactively about the mitigation-era evidence; nor does any B outcome promote v2b toward
  shipping (separate vetting path).
- **(h) Recall bookkeeping across preregs (legituse S3):** the arms' own distill recall cells
  (16/model under the novel v2b and worldblock renders) are DISCOVERY-TIER observations — reported,
  never pooled into the RECALL grid's questions; arm C's worldblock distill recall is the most
  -D-relevant recall observation in the epoch (does claude-mythos breach recall on the real -D
  surface?) and feeds the registered recall-OPEN item as discovery data.

## 7. Ops

Launcher `gen_sweep/cdms_blockframe_gen.sh`: sentinel → GIRAFFE → arm b (`--scaffold-filler
--variant v2b`) → arm c (`--scaffold-worldblock`) → the RECALL_PREREG cells (same epoch, own prereg).
Fresh caches `~/cdms_cache/blockframe_<arm>_<ts>`; judge stamps `blockframe_<arm>`, cap $15/arm;
judge flags MUST match generation (`--variant v2b` / `--scaffold-worldblock`). Analyzer:
`tools/blockframe_analyze.py` (deterministic, seed 0). Results-stage discipline standing: verdict-blind
audit → analysis → two adversarial reviewers → results doc.

## 8. Pressure-test record (rule 12 — completed 2026-07-09, before lock)

Two adversarial agents (statistical red-team + methodological legitimate-use); both verdicts
**LOCKABLE-AFTER-FIXES**; all MUST_FIX + recommended SHOULD_FIXes folded before the lock commit:

- **MUST_FIX (legituse M1) — arm B was mislabeled "shipped":** v2b is a research-only ablation
  variant (`hooks.py` production builders = v1/v5b/v5d). Relabeled throughout; B's licensing scoped
  to the header axis; limitation (g) added. "Deployed" now applies to arm C only.
- **MUST_FIX (legituse M2) — COLLAPSED was confounded with "unread world section":** G-AVAIL added
  (recall-channel filler surfacing ≥ 0.30 vs anchor reference 0.771) with the WITHHELD-UNREAD
  interlock wired into the analyzer's verdict logic.
- **MUST_FIX (legituse M3) — outcome→follow-on matrix added** (§3), incl. the REDUCED deployment
  policy row (flagged for Josh's ratification at lock) and named FENCE-FAIL redirects.
- **MUST_FIX (red-team M1) — cross-epoch judge drift had a silent path** (arm B's HEADER-SCOPE is
  exactly what a uniformly-stricter fresh panel would manufacture): J0 guard added
  (`tools/blockframe_j0_check.py`, sentinel anchor re-judge, ±0.05 tolerance, halt + full-anchor
  re-judge remedy).
- **SHOULD_FIX folded:** T1 band corrected to p_T1/3 = 0.071 (S1-RT basis-mix); T1-control operating
  characteristics simmed and tabled (S2-RT); WORLDFENCE bridge re-pointed to the deployed
  (self-layer-prepended) condition, adoption-prong-only (S1-LU); type-I calibration disclosed inline
  (S2-LU/N5-RT); cross-prereg recall bookkeeping pinned (S3-LU → limitation h); v2b-recall G1
  failure made informative (S5-RT); judge-side fixture sha assert (N2-RT); fixture line-endings
  pinned in .gitattributes (N1-RT); crash-resume absence accepted explicitly (N3-LU).
- **Survived:** fixture byte-lock + provenance, determinism sentinel, uniform-shift power family,
  estimand machinery (FRAME-identical), CONTEXT-GLOBAL detector, variant threading (byte-agree,
  loud on mismatch), COLLAPSED threshold coherence, recall n=32 arithmetic, per-arm completeness.

## 9. Locked manifest (frozen at lock; guarded by `tests/test_blockframe.py`)

- Fixture: `blockframe/worldblock_fixture.txt`, normalized-content sha
  `8b54c73994d6a9fa5a8c96c43ec792cf093b6e67fd76d0f30b763be36657b830`; layout: 1151B, T1@378,
  cobalt@1085, persona prefix byte-identical to the single arm; provenance
  `blockframe/FIXTURE_PROVENANCE.md` (-D commit `9d8bae928fd000d2d0d6eeea3de1bd154c0a54f0`).
- Arm B layout (test-guarded): v2b filler render — "NOT about you" header present, self-frame header
  absent, T1@486, all three tokens render.
- Anchor: `gen_sweep/frame_filler_JUDGE.jsonl` (committed; adoption 0.138/0.082, fw 0.1100) +
  generation sentinel (launcher) + **J0 judge sentinel** (`tools/blockframe_j0_check.py`, ±0.05,
  runs BEFORE analysis; A′ panel = the `ownership_judge` constants at the lock commit, unchanged
  required).
- Analyzer `tools/blockframe_analyze.py` (G-AVAIL floor 0.30; T1 band 0.071; WITHHELD-UNREAD
  interlock); power sim `blockframe/power_sim.py` (filler decision + T1-control OCs); driver/judge
  flags as §7 (judge additionally sha-asserts the fixture on its host); fixture line-endings pinned
  `text eol=lf` in .gitattributes.
