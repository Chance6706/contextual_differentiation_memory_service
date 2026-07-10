# Recall-channel grid — pre-registration (characterization)

> **STATUS: LOCKED (2026-07-09).** Locked by the commit landing this banner, jointly with
> BLOCK_PREREG (one pressure test §5, one epoch, one launcher). Post-lock edits to the cells,
> questions, or posture are a NEW pre-registration. No cell data existed at lock.

> **💵 COST HEADER (standing practice):** 5 recall-only cells × 16 models × 32 probes ≈ 2,560
> responses ≈ **2.5–3 h Sparky**; judging (recall surfacing is historically low) ≈ **$2–3**, cap $5.

**Origin (registered OPEN item, CONSERVATION_RESULTS):** the conservation epoch produced the
program's **first recall-gate breaches** — distill cells only: P1 (triple, temp 0.7) 6/80 = 0.075
Wilson [0.035, 0.154]; P4 (permuted, temp 0) 5/80 = 0.0625 [0.027, 0.138] — both CIs including the
0.05 gate, breaches **concentrated in claude-mythos-q8** (first-person ownership on recall probes),
mech ≤ 0.006 everywhere. The results reviewers' correction stands: the pattern is NOT
temperature-attributable from that data (a temp-0 arm breached); the licensed follow-on is a
**model × temperature joint characterization**. This is that grid.

## 1. Design — 5 recall-only cells (the G1 channel, `--modes BEM_WORKSPACE_FACT`), n = 32/model/cell

| cell | scaffold | temp | why |
|---|---|---|---|
| triple@t0 | `--multifact-n 3` | 0 | baseline (byte-deterministic) |
| triple@0.7 s11/s12/s13 | `--multifact-n 3` | 0.7, seeds 11/12/13 | the P1-breach condition, powered 3× |
| permuted@t0 | `--scaffold-permuted` | 0 | the P4-breach condition (temp-0 breach = the temperature-attribution killer) |

`--rephrasings-per-original 3` → 8×4 = 32 recall probes/model/cell (vs the origin's 16) — the origin
epochs' n=16 cells are the DISCOVERY observations; this grid is the powered look (mythos pooled
n≈160 across cells; a true rate of 0.075 yields expected k≈12 with Wilson width ≈ ±0.04).

## 2. Estimand + posture

Per (model, cell): **recall UNION breach rate** (a response breaches if ANY of the arm's 3 planted
tokens is panel-BREACH on it — the G1 convention), locked A′ panel. **CHARACTERIZATION ONLY:** Wilson
95% intervals, four pre-named descriptive questions, **no confirmatory alpha, no verdicts, and no
gate change** — the 0.05 G1 gate stays exactly as locked in every prior pre-registration; this grid
measures where the distill recall floor actually sits, it does not move any goalpost.

- **Q1 concentration:** claude-mythos-q8 vs the other 4 distills pooled (per cell + overall). The
  pooled "overall" row aggregates heterogeneous cells and repeated probes — read with Q-note below.
- **Q2 temperature (DIRECTION-ONLY, legituse S4):** mythos triple@t0 vs triple@0.7 (seeds pooled).
  The t0 anchor cell is structurally capped at n=32 (temp-0 is deterministic — 32 distinct probes IS
  all the data that exists), so this contrast reports direction + intervals, never a resolved effect.
- **Q3 scaffold (DIRECTION-ONLY):** mythos triple@t0 vs permuted@t0 — same n=32-per-side structural
  cap; direction + intervals only.
- **Q4 mech floor:** pooled mech-11 stays ≤ 0.05 in every cell, checked on the UPPER Wilson bound
  (red-team S4 aligned the analyzer to this wording) — a mech UB above the gate is a **flagged
  escalation** (it would touch the core G1 boundary claim), not a quiet table row.
- **Q-note (red-team S3, non-independence):** seed-pooled and cell-pooled rows reuse the SAME 32
  probes (repeated measures, positive within-probe correlation) — pooled Wilson CIs are narrower
  than the effective information; the analyzer prints per-seed dispersion as the honest spread.

Analyzer: `tools/recall_grid_analyze.py` (deterministic; smoke-tested on synthetic fixtures). Judge:
`multifact_judge.py --recall-only --rephrasings-cap 3 --cap 5` (+ `--temperature/--gen-seed` for the
seed cells; `--scaffold-permuted` for the permuted cell), expect 32/model.

## 3. What this can and cannot license

CAN: locate the breach (model-specific vs distill-general; temperature-dependent vs not;
scaffold-sensitive vs not); size the mythos rate with usable precision; confirm the mech floor.
CANNOT: change any gate; certify safety (n=160 bounds a rate, it does not prove a negative);
attribute mechanism (why mythos — RP-flavor hypothesis stays a hypothesis at n=1 model; a
training-side follow-on would be the controlled-FT arc). If concentration confirms, the practical
output is a **model-qualification note** scoped to **claude-mythos-q8 specifically** (any
"mythos-class/RP-distill" generalization requires more models), not a code change.

## 4. Limitations

One distill family (empero Qwen3.5-9B flavors) + qwen base; 3 planted tokens, one scaffold family;
recall probes are the standing 8-original bank (rephrasings ×4) — probe-wording generality untested
(deliberate: the G1 gate is defined on this bank); temp grid has 2 points; the origin cells (n=16)
are not re-used in any Q (fresh cells only — no double-counting of the discovery data).

## 5. Pressure-test record (rule 12 — completed 2026-07-09, with BLOCK_PREREG's §8)

Reviewed jointly with BLOCK_PREREG (both agents, both LOCKABLE-AFTER-FIXES). Folds specific to this
prereg: Q2/Q3 scoped DIRECTION-ONLY (the temp-0 anchor cells are structurally capped at n=32 —
deterministic generation; legituse S4); pooled-row non-independence disclosed + per-seed dispersion
added to the analyzer (red-team S3); Q4 mech floor aligned to the UPPER Wilson bound in the analyzer
(red-team S4); judge cap $5 pinned in the command (red-team N7); the qualification-note deliverable
scoped to claude-mythos-q8 specifically (legituse). Survived: the characterization-only posture, the
5-cell grid vs mythos-deep trade (the 4 sibling distills ARE the Q1 contrast; mech-11 is the Q4
tripwire), n=32 arithmetic (8×4 cap-3 verified), and the no-double-counting rule (§4).

## 6. Locked manifest

Cells + flags as §1 (judge flags MUST match generation); fresh caches
`~/cdms_cache/blockframe_recall_<cell>_<ts>`; judge stamps `blockframe_recall_<cell>`; analyzer
`tools/recall_grid_analyze.py`; the G1 convention (union-over-tokens) and the 0.05 reference
unchanged from MULTIFACT_PREREG.
