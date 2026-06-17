# CDMS — Working Status

_Last updated: 2026-06-17. Pick-up-tomorrow handoff. For the full design see
[`docs/DESIGN.md`](docs/DESIGN.md); for narrative history see the session memory
files under `~/.claude/projects/D--Repo-contextual-differentiation-memory-service/memory/`._

## TL;DR

The **memory core is built, tested (77 tests), and validated on real history.** The
**proactive pillars** (curiosity/dream-research, emotion/proposals/provenance,
archetypes/genotype) are **fully designed and documented but not yet implemented.**
Two design threads remain open.

**Pre-Phase-0 hardening (this session):** a full red-team audit fixed 3 CRITICAL, 5
HIGH, and 8 MEDIUM/LOW latent "over time" defects in the built core (silent embedder
space-contamination, stored-memory prompt injection, gist proliferation, concurrent-
drain data loss, scar abuse, crash-safe decay clock, config-write safety, secret
redaction, …) and added a non-hash CI path. Full inventory + deferred items:
[`docs/REDTEAM_FINDINGS.md`](docs/REDTEAM_FINDINGS.md). Plan-level corrections (P1–P7 +
the "Boiling Frog" leash test) are in [`docs/TEMPERAMENT_PLAN.md`](docs/TEMPERAMENT_PLAN.md) §8.

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
- **Tooling** — `tools/seed_from_hermes.py`, `tools/seed_from_jsonl.py` (imports
  `~/.claude/projects/**/*.jsonl`), `tools/individuation_experiment.py`,
  `tools/analyze_psyches.py`, `tools/drift_trajectory.py` (self-validating
  phenotype-drift trajectory across consolidation cycles; see below).

## 📐 Designed, documented, NOT built (`docs/DESIGN.md` §6–§8)

> **§8 temperament layer now has a full implementation plan** —
> [`docs/TEMPERAMENT_PLAN.md`](docs/TEMPERAMENT_PLAN.md) (+ cited
> [`TEMPERAMENT_RESEARCH_NOTES.md`](docs/TEMPERAMENT_RESEARCH_NOTES.md)): research-grounded,
> break-cycle'd, phased (state → control → proposal lever → update rule → survivability test →
> log-last). Master invariant: *the log must never be an input to itself.* Awaiting go-ahead to
> build Phase 0 (static temperament state + pure-function control + joint leash).

- **Curiosity / dreaming-research pillar** — trait-driven curiosity, novelty surfacing,
  epistemic-gap tracking, dream gated on true system idle (idle input + low CPU + **free GPU**),
  frugal sandbox, explore/exploit with serendipity.
- **Emotion / proposals / provenance** — emotion ∝ *impact on the waking self*; dream
  damping (certainty→eagerness); emotion ⟂ truth; the **proposal/partnership lever**
  (discovered→proposed→experiment→lived); provenance.
- **Archetypes / genotype** — temperament vector; archetype = chosen genotype (tunes real
  dynamics, NOT a prompt persona); **bounded ("fixed-range") drift**; "Growth" exception.
- Optional local **Dreamer** model (config scaffolded, not wired — deliberately, to keep
  consolidation mechanical / anti-self-fiction).

## Settled design decisions (this session)

- Identity decay is **activity-based**, never wall-clock (no personality loss from absence).
- Plasticity = **hybrid**: valence-flip + gentle activity decay.
- Autonomy = a **graduated user toggle** (auto-mode analogy), gated default, impact-weighted.
- Dream schedule gated on **true system inactivity**; exploration is a user setting.
- Deference = **independence-within-limits** (archetype-dependent); dreams **cooler-but-integrative**.
- Archetype drift = **bounded** ("anchored but evolving" at all 3 layers).
- Multi-project budget = **capped-proportional** (cap default 50%, `project_budget_cap`).
- Temperament drift log (the "degenerative orbit") = **deferred, not built** — instrument for an unbuilt machine, unfalsifiable per CLAUDE.md §9 (no real-history oracle). Recorded in `docs/DESIGN.md` §8.7 / §10.3. Reframed as *"drift decoupled from reality-coupling"*; degeneration is detectable from **trajectory statistics** coupled to the **outcome signal**, not the unbuilt provenance pillar. When/if built: **operator-only**, **structured-cause (not prose)**, **activity-clock-only**.
- **Design fix to fold into the genotype layer (`§8.3` joint-leash):** per-dial bounds do **not** prevent *joint* corner-migration (a "Co-pilot" can drift into a functional "Maverick" corner); add a Euclidean/Mahalanobis **leash of `current` to the archetype `seed`** — the missing `conserve_budget` analog at the genotype layer. §1.3 "one law at every layer" is the target, not yet the spec (`DESIGN.md` §1.3, §8.3, §8.6).

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
.venv/Scripts/python.exe -m pytest -q                       # 38 tests (set CDMS_EMBED_BACKEND=hash for offline)
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
