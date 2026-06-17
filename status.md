# CDMS — Working Status

_Last updated: 2026-06-17. Pick-up-tomorrow handoff. For the full design see
[`docs/DESIGN.md`](docs/DESIGN.md); for narrative history see the session memory
files under `~/.claude/projects/D--Repo-contextual-differentiation-memory-service/memory/`._

## TL;DR

The **memory core is built, tested (36 tests), and validated on real history.** The
**proactive pillars** (curiosity/dream-research, emotion/proposals/provenance,
archetypes/genotype) are **fully designed and documented but not yet implemented.**
Two design threads remain open. `main` is clean; 8 PRs merged this session.

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
  `tools/analyze_psyches.py`.

## 📐 Designed, documented, NOT built (`docs/DESIGN.md` §6–§8)

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

## Real-data findings (all fixed)

| Finding | Fix |
|---|---|
| Consolidation O(n²), intractable at scale | Vectorized dedup+clustering (PR #6) — 8.6k turns in ~4s |
| Gist extraction noisy on real transcripts | Stopwords + singular/plural dedupe (PR #7) |
| One project dominated the budget (74.9%) | Capped per-project budget (PR #8) — now 50% cap |

## Resume commands

```bash
# from repo root, venv at .venv
.venv/Scripts/python.exe -m pytest -q                       # 36 tests (set CDMS_EMBED_BACKEND=hash for offline)
.venv/Scripts/python.exe tools/individuation_experiment.py  # synthetic individuation harness
# seed + analyze real multi-project history into a throwaway store:
CDMS_HOME=.tmp python tools/seed_from_jsonl.py --path ~/.claude/projects --home .tmp
CDMS_HOME=.tmp python -m cdms consolidate
CDMS_HOME=.tmp python tools/analyze_psyches.py
```

## Notes / decisions still pending the user

- CDMS is installed **project-scoped** in this repo only (per choice); `cdms install --scope user`
  makes it global when wanted.
- Real `~/.local_memory` is **not** seeded (test-only by choice); the JSONL history is one command
  away if we decide to bootstrap it.
- A future **Rust/Go rewrite** of the daemon is the spec's production-hardening step (algorithms +
  schema port directly).
