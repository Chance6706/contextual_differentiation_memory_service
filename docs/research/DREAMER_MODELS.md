# Dreamer model selection (trait-driven dreaming)

_Scaffolded 2026-06-19 and **pressure-tested by a 4-lens panel before adoption**. Forward-looking: there
is **no dreaming runtime yet**. The panel's headline finding reframed this doc — the dreaming **safety
substrate is not in place**, so most of this is now a spec of what must be true *before* a runtime is
built, not a green light. Config: `tools/dreamer_models.py`._

> **Naming collision (fix before building):** a "Dreamer" already exists in the codebase — `Config.dreamer_*`,
> a read-time **prose renderer** that is never authoritative (`consolidate.py`). The subsystem described
> here is a different thing: an idle trait-**exploration generator** of *synthetic* dreams. Rename one.

## What the (exploration) Dreamer is
The system generating its **own** exploratory content during idle time — recombining stored memories,
exploring hypotheticals in the persona's trait space — to enrich the phenotype **without new real
interaction**. Runs opportunistically on **free GPU during inactivity**, gated off by default.

## 🚨 Safety substrate — MUST-HAVES before any dreaming runtime (panel finding: the invariant is currently fiction)
The intended invariant — "dream content is synthetic, captured `untrusted`, and can never elevate to a
scar or gist-trait" — is **asserted nowhere in enforceable code today.** Verified against the live tree:

1. **Force a dedicated synthetic provenance at ingest.** No current path stamps it: `TurnEvent.provenance`
   defaults to `"trusted"` (`store.py`), and the MCP `store` tool + CLI `ingest` (the paths a dreamer would
   use) both produce **trusted** episodes; `classify_provenance` only fires on hook-captured tool events,
   which a dream isn't. → Add a distinct `"synthetic"` provenance, required on the dream-ingest function;
   forbid MCP `store`/`cmd_ingest` as the dream path. **It must be impossible to write a dream as trusted.**
2. **Gate synthetic content out of recall, the recent tier, AND salience — not just elevation.** Provenance
   is checked only in scar-elevation (`consolidate.py:277`) and gist-aggregation (`:485`). Untrusted content
   still flows through `retrieve`/`knn`/`fts`, the cold-start recent tier (`hooks.py`), associative boost,
   and salience. The "untrusted may surface in the low-authority recent tier" residual was scoped for
   *passive external reads at human rates* — NOT an autonomous high-volume self-author. → exclude synthetic
   from recall + recent + salience competition, or hard-cap + de-authoritize its render.
3. **Break the feedback loop.** Dreams enrich state → seed more dreams. The activity-based decay model
   *fails here*: decay only fades **idle** traits, but a Dreamer keeps its own confabulations non-idle (never
   decays) while advancing the consolidation/decay cycle clock that ages **real** unreinforced memory →
   preferentially forgets the genuine, retains the synthetic. → dreams must not form/reinforce gists, must
   not advance the cycle counter, and ideally run against a **sandbox store** that never back-writes the
   authoritative gist tier. Add a multi-cycle drift-erosion test with a dreaming producer in the loop.
4. **Budget isolation.** `salience_budget` caps are per project/session, not per origin; a high-volume
   Dreamer sharing the persona's session dilutes **real** memory toward eviction. → exclude synthetic from
   `_compete_and_renormalize`, or confine to a dedicated synthetic session/project sub-cap.
5. **Tests through the *real* dream path** (not hand-tagged `TurnEvent`s): assert a dream catastrophe never
   elevates, never gists, never appears in `build_preamble`/recent, and is never returned by `retrieve`.
   And **bound dream temperature against a coherence floor** — high temp inflates novelty→salience and
   raises catastrophe-lexicon collisions (the flashbulb-floor scar path).

## Validation gate — there is no dream-quality metric yet, so every tier/temp/family claim is unfalsifiable
Build this first (cheap — reuse `tools/individuation_experiment.py` primitives: `build_psyche`,
`_session_start_context`, `rel_obj` Jaccard, gist-centroid `cosine`). Score a dream on three axes,
**mechanically** (geometry/lexicon, never the LLM grading itself):
- **Coherence (floor):** does the dream survive the consolidation clustering path at all? Zero clusters → incoherent → wasted GPU. This *operationalizes* the `min` tier's coherence floor.
- **On-trait:** cosine to the persona's gist centroid above a floor, and **higher for its own persona than others** (cross-persona discrimination, reusing the individuation table).
- **Novel-but-not-drift:** introduces some new `(relation, object)` (Jaccard < 1.0) but stays within a drift band (cosine above a ceiling) — the quantitative "adjacent possible."

A dream passes iff coherent ∧ on-trait ∧ novel-but-bounded. Until this exists, the tiers below are a
**parameter sketch**, not a validated selection.

## Tiers — min / sweet / best (host-aware; footprints weights-only Q4, verified)
| tier | role | Q4 weights | families (rotate) | runs on |
|---|---|---|---|---|
| **min** | coherence floor; cheap, frequent | 4-6GB | qwen2.5:7b · llama3.1:8b · mistral:7b · gemma2:9b | 4070 Ti **or** spare GX10 |
| **sweet** (default) | best exploration / free-GPU cost | 7-20GB | qwen2.5:14b · **qwen2.5:32b** · gemma4:12b · phi4:14b · mistral-nemo | 4070 Ti (≤14B); 32B → GX10 |
| **best** | deep-idle, richest | 43-73GB | llama3.1:70b · qwen2.5:72b · mistral-large 123B | **GX10 only** |

`dreamer(tier, family, max_model_gb)` filters to host-fitting models (4070 Ti `sweet` correctly excludes the
32B); `rotate(tier, max_model_gb)` cycles families; `pick_for_budget(free, idle, max_model_gb)` picks the
biggest tier meeting the gate **and** fitting the host. The `best` gate is **80GB free** (a 123B's ~73GB +
KV must fit — the earlier 48GB gate was OOM-reachable). Negative inputs clamp to `min`.

## Open design questions (need the validation gate to answer)
- **Family rotation confounds diversity with per-family quality** — a "more divergent" dream may just be a
  weaker model. Deconfound the way steering's `FAMILY_LADDERS` deconfounds scale (hold the eval fixed; show
  cross-family variance > within-family run-to-run variance) before trusting rotation. Also verify rotation
  doesn't shift cluster/EMA geometry during consolidation.
- **Temperature should likely scale inversely with tier** (protect `min`'s coherence floor; let `best`
  absorb divergence) and couple to the autonomy/curiosity-radius dial, not sit flat at 0.9.
- **Does `best` (70B+) earn its cost for *dreaming*?** Dreaming is recombination-within-a-known-space, not
  frontier reasoning — `sweet` may saturate. Run the eval up the qwen2.5 within-family ladder (7→14→32→72)
  and find the knee; if it knees at `sweet`, drop or re-scope `best`.
- **Size may be the wrong axis** — dream *task types* (memory recombination vs adjacent-possible synthesis
  vs gap-filling research) have different capability floors; consider (task-type × budget) selection.

## Ops gaps (feasibility panel) — must close before a runtime
- **"free VRAM" is not directly measurable on the GX10's unified pool** (DGX OS, shared CPU+GPU); and
  **"idle" is ill-defined on a headless appliance**. The scheduler's two inputs are currently unknowable —
  define them (queue-emptiness of foreground tenants, a measured allocatable-headroom API) before shipping.
- **No preemption.** `pick_for_budget` only gates *starting*; once a `best` dream runs, an incoming Tales
  (HunyuanVideo/TRELLIS) job contends catastrophically on the shared ~273 GB/s pipe (and can OOM). Needs a
  foreground signal + kill/checkpoint path + tenant reservations. Even a `min` dream throttles a serving
  model on bandwidth — co-residence is memory-safe, not free.

## Follow-ups
- **Shared tag catalog** (`tools/local_models.py`) so `steering_experiment.py` and this module stop
  duplicating drift-prone Ollama tags.
- **Rename** to resolve the `Config.dreamer_*` (prose-renderer) collision.
