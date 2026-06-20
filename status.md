# CDMS — Working Status

_Last updated: 2026-06-19 (Cycle 9 triage complete; §8 temperament Phase 0 built & merged). For the full design see
[`docs/DESIGN.md`](docs/DESIGN.md); for narrative history see the session memory
files under `~/.claude/projects/D--Repo-contextual-differentiation-memory-service/memory/`._

## TL;DR

The **memory core is built, tested (306 tests), and validated on real history.** The
**§8 temperament layer Phase 0** (static disposition state + pure-function control + joint
leash) is now **built, tested, and merged to `main`**. The remaining **proactive pillars**
(curiosity/dream-research, emotion/proposals/provenance, the temperament drift/proposal
phases 1+) are **fully designed and documented but not yet implemented.**

**Pre-Phase-0 hardening — nine red-team cycles + a re-run-audit follow-up complete:**
- **Cycle 1** fixed 3 CRITICAL + 5 HIGH + MEDIUM/LOW "over time" defects (silent
  embedder space-contamination, stored-memory prompt injection, gist proliferation,
  concurrent-drain data loss, scar abuse, crash-safe decay clock, config/secret
  safety) and added a non-hash CI path.
- **Cycle 2** broadened to every angle (MCP, scale, cognitive-math, env/clock/config,
  data isolation/lifecycle, seeders, packaging/recovery/test-integrity) AND re-audited
  the Cycle-1 fixes — landing ~16 HIGH + several MED/LOW fixes across 9 commits:
  cross-project isolation (clustering partition, project-keyed gists, scoped
  `retrieve`), **right-to-forget** (`cdms forget`, `uninstall --purge`), config
  validation + corrupt-DB quarantine + `doctor` fingerprint check, fence-escape /
  truncation hardening, negation-aware outcome inference, unicode FTS, and refinements
  to three Cycle-1 fixes (H4 false-negatives, H1 identity-creep, L1 spool short-write).
- **Cycle 3** broadened again (7 angles) + re-audited the Cycle-2 fixes — which
  caught that the Cycle-2 corrupt-DB quarantine had introduced a **CRITICAL data-loss
  regression** (lock contention misread as corruption → healthy store wiped). Fixed 1
  CRIT + 7 HIGH + MED/LOW: cross-process consolidate/forget lock, forget completeness
  (`secure_delete`+VACUUM+spool purge), streaming/reclaiming/capped drain, scar dedup,
  embedder truncation+sentinel+dim-assert+versioned fingerprint, finite/bounded config
  validation, H4 harm-gating, and MCP/install hardening. The identity/cognitive-math
  attacks (X1–X6: ossification, decay-clock, valence-on-dedup, relation-flip, salience
  gaming) are **characterized design tradeoffs, deferred by design** (the thesis itself —
  individuation, thrash damping, budget cap — held: trait overlap **0.000**).
- **Cycles 4–6** added external adversarial reports (DeepSeek V4 Pro, GLM-5.2, OWL-Alpha)
  + the metaphysical-disposition framing ("CDMS individuates, it does not animate").
- **Cycle 7** triaged the open Cycle 4–6 mechanical findings and **built §8 temperament
  Phase 0**; a **double adversarial review** then caught a HIGH new regression (the A2-M1
  gist-orphan rule erased multi-session gists) and reverted it.
- **Re-run-audit follow-up** — a re-run of the OWL Cycle-7 review revealed the original had
  read a **stale revision** (it certified the since-reverted A2-M1 as "fixed"). Re-auditing
  the true tip surfaced and fixed **8 defects** (1 HIGH word-boundary success-inference bug
  poisoning valence; 2 MED — partial-seed archetype-mixing + the Bem-firewall CLI leak; 5
  LOW — purge glob, dedup phantom +1, temperament CHECK constraints, `db_filename`
  traversal, `reinforce_cap<alpha`). Merged to `main` in **PR #15**.
- **Cycle 8 — COMPLETE** (OWL full-spectrum final report, 6-subagent, 20 findings; every
  actionable item fixed or explicitly deferred-with-rationale). Triaged across PRs #17–#25:
  spool/secret/redaction hardening (+ a Gemma-fuzzed pass that found `sk-proj`/`pwd`/marker-
  overmatch gaps), S0-weight + per-session budget caps (H-2/H-M-2), adaptive valence-EMA so
  established traits resist injection (M-M-4), per-write associative-boost cap (M-M-3),
  embedder-lock + eviction-reread races, runtime vec0-format pin (M-8), dedup in-memory survivor
  + MCP `kind` validation (L-1/L-S-1), and **scale** — per-project dedup/aggregation (C-1 memory)
  + a gated VACUUM (M-S-1). Verified overstated/dead-config: `http_host`/`render_base_url` are
  stdio/unwired, C-1 OOM is decay-bounded, L-3 was already shipped in Cycle 7. **Intentionally
  deferred:** C-1 streaming pre-eviction (addressed by C-1 memory + M-S-1; rare dedup-fold
  caveat), L-C-1 (lock + persist-last already cover it), L-6 (cosmetic), L-S-2 (ops/CI not code),
  L-S-3 base64 redaction (high false-positive).
- **Cycle 9 — COMPLETE** (five independent multi-vantage reports — Hermes, MiMo, Hy3, Kimi,
  Gemma-fuzz — adjudicated against the actual tip with the SHA-pin-and-reproduce discipline).
  Eight actionable findings fixed across **PRs #27–#30**: **I-1** (the lone CRITICAL) SessionStart
  now reads under one consistent WAL snapshot (no torn mid-consolidation view) + closes its leaked
  connection; **#1** associative boost can no longer *manufacture a scar* (clamped strictly below
  the crisis gate — though measured it **saturates** ~+0.2 default / +0.6 worst-case, so the
  red-team's "unbounded HIGH" was really a bounded LOW–MEDIUM injection vector); **#3** the budget
  `allocate_capped_proportional` infeasible branch now enforces the per-key cap as a hard invariant;
  **#4** a pathologically tiny `crisis_threshold` no longer rounds the S0 weights to zero (silently
  disabling salience); **#5** explicit facts can no longer become decay-immortal via unbounded
  `support_count` (capped in the decay formula only); **#7** `assoc_eta`/`assoc_boost_cap_frac`
  tightened `≤1e3→≤1.0` (re-arming the M-M-3 cap); **#8** `Database.__init__` no longer leaks its
  connection on a partial/failed open. **Verified non-findings (honest):** #6 "joint-leash doc fix"
  — the leash docs/math are already correct (COGNITIVE_MATH review); **T-4** "no leash-under-drift
  test" — already covered by `test_temperament_sim.py` (33 tests: randomized boiling-frog + the
  no-archetype-hop invariant over all pairs). Every fix is build→break→fix tested and clears the
  `drift_trajectory.py` identity guard. The deferred Phase-1+ backlog was then **redefined
  piece-by-piece** (measured at real personal scale — the decay/eviction bound defuses most
  theoretical-scale severities; ~⅔ are NON-ISSUE/already-handled) and the cheap, real items shipped
  as **PR #32** (F-2 durable quarantine marker surfaced in `cdms stats`, S-5 `history()` SQL
  pagination, D-2 consolidation crash-safety guard, T-1 recall-over-consolidated-store guard). Full
  measured register in `docs/REDTEAM_FINDINGS.md`.
- Full inventory + verified-sound + deferred items:
  [`docs/REDTEAM_FINDINGS.md`](docs/REDTEAM_FINDINGS.md). Plan-level corrections
  (P1–P7 + the "Boiling Frog" leash test) are in
  [`docs/TEMPERAMENT_PLAN.md`](docs/TEMPERAMENT_PLAN.md) §8.

The central thesis — **Identity = f(History)** — is empirically confirmed: seeding
~8.6k real Claude Code turns across 4 projects produced distinct, *recognizable*
per-project psyches (trait overlap **0.00**).

## ✅ Built & tested (the core)

- **L1 capture / salience / decay** — surprisal-gated `S0`, Ebbinghaus accessibility,
  reinforcement cap, logit-free proxy signals (`salience.py`, `store.py`).
- **Sleep consolidation** — scar elevation (catastrophe-gated), eviction, hierarchical
  softmax competition, **capped per-project budget**, mechanical gist aggregation
  (`consolidate.py`). Dedup+clustering are vectorized (numpy) → scales to ~10k+ turns.
- **L2 hybrid plasticity** — gists keyed on (subject,object), relation flips on sustained
  valence change, **activity-based** (cycle, not wall-clock) gentle decay → absence never
  ages identity.
- **L3 scars** — pinned crisis guardrails (explicit "pin", not a flashbulb claim).
- **Storage** — SQLite WAL + sqlite-vec (cosine KNN) + FTS5 (BM25) hybrid via RRF;
  CPU ONNX embedder (bge-small, 384-dim, **0 VRAM**).
- **Claude Code integration** — MCP stdio server (5 tools) + lifecycle hooks;
  `cdms install --scope project|user`.
- **§8 temperament Phase 0** — static disposition state (8 dials × `(seed, current,
  bounds, plasticity)`, 5 archetypes), pure-function control (no DB/IO/wall-clock), and the
  **joint leash** (Euclidean `current`→`seed`, capped to bind inside the box and below the
  nearest other-archetype seed). **Operator-only** — never enters context (Bem firewall),
  enforced at the `cdms temperament` CLI boundary. `current == seed` (no drift yet —
  drift/proposal are Phases 1+). `temperament.py`, schema v4 `mem_temperament` table.
- **Tooling** — `tools/seed_from_hermes.py`, `tools/seed_from_jsonl.py` (imports
  `~/.claude/projects/**/*.jsonl`), `tools/individuation_experiment.py`,
  `tools/analyze_psyches.py`, `tools/drift_trajectory.py` (self-validating
  phenotype-drift trajectory across consolidation cycles; see below).

## 📐 Designed, documented, NOT built (`docs/DESIGN.md` §6–§8)

> **§8 temperament layer — Phase 0 is BUILT & merged** (see "Built & tested" above). The
> full phased plan lives in [`docs/TEMPERAMENT_PLAN.md`](docs/TEMPERAMENT_PLAN.md) (+ cited
> [`TEMPERAMENT_RESEARCH_NOTES.md`](docs/TEMPERAMENT_RESEARCH_NOTES.md)): research-grounded,
> break-cycle'd, phased (state → control → **proposal lever → update rule → survivability test →
> log-last**, the still-unbuilt Phases 1+). Master invariant: *the log must never be an input
> to itself.*

- **Curiosity / dreaming-research pillar** — trait-driven curiosity, novelty surfacing,
  epistemic-gap tracking, dream gated on true system idle (idle input + low CPU + **free GPU**),
  frugal sandbox, explore/exploit with serendipity.
- **Emotion / proposals / provenance** — emotion ∝ *impact on the waking self*; dream
  damping (certainty→eagerness); emotion ⟂ truth; the **proposal/partnership lever**
  (discovered→proposed→experiment→lived); provenance.
- **Archetypes / genotype** — temperament vector; archetype = chosen genotype (tunes real
  dynamics, NOT a prompt persona); **bounded ("fixed-range") drift**; "Growth" exception.
- Optional local **Prose Renderer `"Dreaming"`** (CDMS-B; `Config.render_*` scaffolded, not
  wired — deliberately, to keep consolidation mechanical / anti-self-fiction). Distinct from
  CDMS-C / Active Research `"Dreaming"` (`tools/research_models.py`). See `docs/DEVIATIONS.md` L6.

## Settled design decisions (this session)

- Identity decay is **activity-based**, never wall-clock (no personality loss from absence).
- Plasticity = **hybrid**: valence-flip + gentle activity decay.
- Autonomy = a **graduated user toggle** (auto-mode analogy), gated default, impact-weighted.
- Dream schedule gated on **true system inactivity**; exploration is a user setting.
- Deference = **independence-within-limits** (archetype-dependent); dreams **cooler-but-integrative**.
- Archetype drift = **bounded** ("anchored but evolving" at all 3 layers).
- Multi-project budget = **capped-proportional** (cap default 50%, `project_budget_cap`).
- Temperament drift log (the "degenerative orbit") = **deferred, not built** — instrument for an unbuilt machine, unfalsifiable per CLAUDE.md §9 (no real-history oracle). Recorded in `docs/DESIGN.md` §8.7 / §10.3. Reframed as *"drift decoupled from reality-coupling"*; degeneration is detectable from **trajectory statistics** coupled to the **outcome signal**, not the unbuilt provenance pillar. When/if built: **operator-only**, **structured-cause (not prose)**, **activity-clock-only**.
- **Joint-leash (`§8.3`) — now BUILT in Phase 0:** per-dial bounds do **not** prevent *joint* corner-migration (a "Co-pilot" can drift into a functional "Maverick" corner), so the genotype layer carries a Euclidean **leash of `current` to the archetype `seed`** — the `conserve_budget` analog. Implemented in `temperament.py` (radius capped to bind inside the box AND below the nearest other-archetype seed → no archetype-hopping; property-tested incl. the "Boiling Frog" ratchet). A Mahalanobis Σ from the survivable region is the Phase-2 upgrade (`DESIGN.md` §1.3, §8.3, §8.6).

## 🔲 OPEN — pick up here

1. **Survivability testing of archetypes** (`DESIGN.md` §10.1) — sweep temperament
   permutations, score each for a stable/individuated/non-pathological self; widen the
   archetype set from the *survivable* region. We now have **real ground-truth psyches**
   (the 4 projects) to calibrate against.
2. **Baked-in interests** (`DESIGN.md` §10.2) — seed innate appetites in the genotype so a
   newborn agent has proclivities before history accrues. Tensions noted: authored-by-history
   invariant, provenance origin, drift, archetype coupling.
3. Then: **start implementing** a pillar. Cheapest first = novelty-surfacing + gap-tracking
   (no models, Pattern-A-native), which the rest feeds.
4. ✅ **Phenotype-drift trajectory — DONE** (`tools/drift_trajectory.py`; `DESIGN.md` §8.7).
   Self-validating harness (built posit→break→build→break→fix): snapshots
   `Store.all_gist()` across K cycles, **no new table**. Every detector is proven to fire
   on a matched control — EROSION (deep absence → 0), THRASH (in-place relation flip →
   persistence 1.00→0.00), DIFFERENTIATION (clone overlap ~0.76 vs distinct ~0.11).
   Findings: steady-state identity persists & stays individuated; absence fades only
   late/gracefully (onset past ~137 cycles), confirming the §5.3 invariant. Deterministic
   under `CDMS_EMBED_BACKEND=hash`; guarded in CI by `tests/test_drift_trajectory.py`.
   Also runs over **real** seeded history (`--real <path> [--windows N] [--limit N]`,
   observational, reuses `seed_from_jsonl.parse_file`): single-project history shows healthy
   accretion (count rising, incremental retention ~1.0) into a recognizable phenotype; the
   **≥2-project cross-project differentiation branch is CI-guarded** against a synthetic
   two-project fixture (distinct vocab → overlap 0.00). `--limit` caps turns/file for large
   local histories.
5. ✅ **Sandbox live-growth — validated end-to-end** (the local-CLI path, real bge-small
   embedder, persistent `CDMS_HOME`). Two-phase growth via `seed_from_jsonl.py` →
   `cdms consolidate` → `cdms stats|paths|retrieve`: phase 1 (2 projects) **3 gists / 31
   episodic / 2 selves** → phase 2 (+real history) **10 gists / 181 episodic / 3 selves**.
   Memory grew live; selves stayed individuated (`paths` shows 3 distinct subjects, the real
   one valence-differentiated into handles_well / frequently_works_on / has_trouble_with);
   recall discriminates by project ("database migration"→alpha, "react component"→beta,
   "drift trajectory"→real). **Ready for the local CLI with more history and the sandbox.**
6. ✅ **Integration surface verified** (the local-CLI wiring). `pip install -e .` (documented
   in README) → all 38 tests pass with no `PYTHONPATH`; `cdms hook SessionStart` runs clean;
   `cdms install --scope project` writes correct `.claude/settings.json` + `.mcp.json`;
   `cdms serve` MCP handshake lists all 5 tools (store/retrieve/history/list_paths/create_link);
   `cdms doctor` HEALTHY; the persistent store survives a cold reopen.
   ⚠️ Hooks invoke `python -m cdms` — so **`pip install -e .` is mandatory** locally; a
   source-only (`PYTHONPATH=src`) env would have silently no-op hooks.

## Real-data findings (all fixed)

| Finding | Fix |
|---|---|
| Consolidation O(n²), intractable at scale | Vectorized dedup+clustering (PR #6) — 8.6k turns in ~4s |
| Gist extraction noisy on real transcripts | Stopwords + singular/plural dedupe (PR #7) |
| One project dominated the budget (74.9%) | Capped per-project budget (PR #8) — now 50% cap |

## Resume commands

```bash
# from repo root, venv at .venv
.venv/Scripts/python.exe -m pytest -q                       # 306 tests (set CDMS_EMBED_BACKEND=hash for offline)
.venv/Scripts/python.exe tools/individuation_experiment.py  # synthetic individuation harness
python tools/drift_trajectory.py                            # self-validating phenotype-drift (PASS/FAIL)
python tools/drift_trajectory.py --real ~/.claude/projects  # observational real-history trajectory
# seed + analyze real multi-project history into a throwaway store:
CDMS_HOME=.tmp python tools/seed_from_jsonl.py --path ~/.claude/projects --home .tmp
CDMS_HOME=.tmp python -m cdms consolidate
CDMS_HOME=.tmp python tools/analyze_psyches.py
# sandbox live-growth: persistent store grows as sessions accrue, selves stay individuated:
export CDMS_HOME=~/.local_memory
python tools/seed_from_jsonl.py --path ~/.claude/projects --home "$CDMS_HOME"
python -m cdms consolidate && python -m cdms stats && python -m cdms paths
```

## Notes / decisions still pending the user

- CDMS is installed **project-scoped** in this repo only (per choice); `cdms install --scope user`
  makes it global when wanted.
- Real `~/.local_memory` is **not** seeded (test-only by choice); the JSONL history is one command
  away if we decide to bootstrap it.
- A future **Rust/Go rewrite** of the daemon is the spec's production-hardening step (algorithms +
  schema port directly).
