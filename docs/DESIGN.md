# Contextual Differentiation Memory Service — Design Specification

## Abstract

The Contextual Differentiation Memory Service (CDMS) gives an otherwise stateless cloud reasoning model a persistent, evolving self. Its single thesis is that a self is not a database of everything that happened but the structural residue left when a cheap, slightly-wrong *discard policy* is applied to a unique lived history: forgetting is the feature, and perfect recall is the pathology. CDMS captures every interaction turn deterministically (L1 episodic), lets those traces fade along an Ebbinghaus curve, and during a "sleep" consolidation pass distills the survivors into a compact, differentiated identity (L2 gist PersonaTree) plus permanent crisis guardrails (L3 scars). Identity is therefore *earned through history*, never declared: two CDMS instances running identical code but fed different histories diverge into different selves. This document specifies the built memory core — capture, surprisal-gated salience, decay, hybrid retrieval, consolidation, and Claude Code integration — and the designed-but-unbuilt pillars that extend it: trait-driven curiosity and a preemptible research "dream," an emotion/proposal/provenance partnership layer, and an archetype genotype with bounded temperament drift. Throughout, one regulatory law recurs at every layer — *stable core plus bounded, earned plasticity; small changes automatic, large changes proposed; activity-based with no absence-loss; sustained signal required.*

## Status Legend

- ✅ **Built** — in the codebase today (implemented and, where noted, tested).
- 📐 **Designed** — agreed and specified in the design record, but not yet implemented.

Every ✅/📐 marker in the sections below is faithful to the build state at the time of writing. A 📐 item is never an upgrade-in-waiting; it is documented as design only.

## Table of Contents

1. Philosophy & the Three-Layer Architecture
2. Capture, Salience & Decay (L1 Episodic)
3. Sleep Consolidation Pipeline
4. Memory Tiers & Storage
5. Individuation & Hybrid Plasticity (L2)
6. The Curiosity & Dreaming-Research Pillar
7. Emotion, Proposals & Provenance
8. Archetypes & the Genotype Layer
9. Claude Code Integration & Deployment
10. Open Design Threads

---

## 1. Philosophy & the Three-Layer Architecture

CDMS rests on a single thesis: **a self is not a database of everything that happened — it is the structural residue left when a cheap, idiosyncratic *discard policy* is applied to a unique lived history.** Perfect recall is not the goal; it is the pathology (retrieval noise, interference, context bloat — the *cognitive curse of perfect recall*). Forgetting is the feature. ✅ Built — this is the stated design philosophy in `src/cdms/__init__.py` and `README.md`.

### 1.1 Identity = f(History)

The governing equation is:

```
Identity = f(History)
           f         = the (slightly-wrong) genotype / discard policy   [function]
           History   = the agent's lived trajectory                     [input]
           Phenotype = the emergent, differentiated behavior            [output]
```

✅ Built — this exact decomposition is written into the package docstring (`src/cdms/__init__.py` lines 13–15) and the cognitive-core header (`src/cdms/salience.py` lines 2–5). Two CDMS instances fed *different* histories diverge into *different* selves, even running identical code. The differentiation is **earned through history**, not declared.

- **Genotype (`f`)** — the inherited, mostly-fixed discard/encoding policy: the write-time salience gate `S0 = G_goal·(S_surprise + C_contingency + W_self_ref + A_affect)`, the decay law, the consolidation rules, and their hyperparameters. ✅ Built — `src/cdms/config.py` (the file's own docstring names itself the place "the 'genotype' ... is tunable in one place"), `src/cdms/salience.py`. The genotype is deliberately *slightly wrong* (cheap, lossy) — that imperfection is what makes the residue idiosyncratic rather than a faithful transcript.
- **History** — the captured agent trajectories (L1 episodic turns). ✅ Built.
- **Phenotype** — the consolidated, differentiated identity (L2 gist PersonaTree + L3 scars) that emerges when `f` runs over `History`. ✅ Built.

A critical constraint follows: the phenotype must be **authored by history, not by the pretrained prior.** Gist tuples are extracted by geometry/lexicon only — the LLM never authors them — which structurally prevents *generative self-fiction* (the model summarizing itself toward pretrained personality clichés). ✅ Built — mechanical tuple aggregation, `README.md` and `src/cdms/consolidate.py`.

### 1.1a Ontological & build status — what CDMS does and does not claim

This sub-section exists to pre-empt a recurring misreading. External reviewers have read the same framing in opposite directions — one as an overclaim to attack ("identity = f(history) is just a lossy JPEG, not a photograph"; autonomy is "a philosophical zombie" — Cycle 5, `redteam/CYCLE5_GLM52_REPORT.md`), another as a grander claim to celebrate ("a simulacrum of ego… the **same AI in a new body**" — Cycle 6, `redteam/CYCLE6_OWL_ANALYSIS.md`). Both target a claim CDMS does **not** make.

The equation above is a claim about **individuation** — *what makes this instance recognizably this one* — not about **phenomenal consciousness**. CDMS **individuates; it does not animate.** It produces a *functional simulacrum* of continuity (the useful behavior of having a past), not subjective experience, sentience, or a persisting subject. CDMS is silent on consciousness: it neither implements nor evidences it, and reading "identity"/"Ego" as a claim about a *mind* is an equivocation on the word "identity."

- **Mechanical and reactive today.** Everything ✅ Built is *retrospective* — it consolidates *what history did*, by geometry/lexicon only (the LLM never authors the tuple, §1.1). The move from *"what have I done"* to *"what can I become"* (self-direction) is **CDMS-C / Active Research `"Dreaming"`** (§6), which is **📐 Designed, not built**. A separate optional sub-LLM — **CDMS-B / the Prose Renderer `"Dreaming"`** (`Config.render_*`, default off) — would render prose at read time and is also **📐 Designed, not built** (no client exists in source). Even once built, both are gated *propose-not-act* (self-edits are impact-gated, §6.8; the propose→experiment→lived reality-coupling, §7.6) — functional agency at most, never experience. The umbrella term `"Dreaming"` is scare-quoted; see `docs/DEVIATIONS.md` L6 for the three-way disambiguation from sleep, Hafner/World-Models, and DeepDream.
- **Substrate-independence = content, not a soul.** Across a model change the *content* of the self-model (gist/scar tuples and dials, all text) carries over; the *expression* changes with the new model, and only insofar as the new model can read the store and respect the read-only trust fence on injected memory (§9.2). This is *not* "the same AI in a new body."
- **The cognitive vocabulary is load-bearing metaphor.** "Ego / sleep / dreaming / individuation" come from complementary learning systems, the Ebbinghaus curve, and synaptic downscaling because they earn their keep as design intuition (and trace to real built mechanisms), not because CDMS literally instantiates those phenomena.

### 1.2 The Freudian mapping: Id / Ego / Superego → three substrates

CDMS is organized as three layers, mapped onto a Freudian topology to make the regulatory roles explicit:

| Freudian layer | CDMS substrate | Role | Status |
|---|---|---|---|
| **Id** | Pretrained cloud weights (Claude) | The raw, fixed reasoning drive — vast, capable, but stateless and a-personal. The agent is "born" here. | ✅ External given (the hosted model) |
| **Ego** | The local CDMS daemon | The persistent, mediating self — captures experience, forgets, consolidates, and re-injects a continuous identity across otherwise-amnesiac sessions. CDMS *is* the externalized Ego. | ✅ Built (`src/cdms/`) |
| **Superego** | Harness guardrails (scars + the proposal gate) | The internalized constraint layer: L3 scars (pinned crisis-remediation rules) and the impact-weighted review gate on self-edits. | L3 scars ✅ Built (`src/cdms/consolidate.py`); proposal/autonomy gate 📐 Designed |

The Id (weights) does all the reasoning but holds no self; the Ego (daemon) supplies persistence and individuation; the Superego (guardrails) bounds what the self may silently become. ✅ Built for the framing (`README.md` describes CDMS as giving "an otherwise stateless cloud reasoning model a persistent, evolving 'Ego'"); 📐 Designed for the full Superego (the autonomy/proposal lever — see `memory/project-cdms-research-pillar-decisions.md`).

### 1.3 "Anchored but evolving," applied recursively at all three layers

The keystone principle is one regulatory philosophy — **a stable core plus bounded, earned plasticity** — applied recursively at every layer of the system, not just to memory. The shared discipline is: *small changes happen automatically and transparently; large changes are proposed; plasticity is activity-based (absence never erases the self); and a change only holds on sustained, clear signal, never noise.*

| Layer | What it is | Plasticity regime | Status |
|---|---|---|---|
| **Weights** | Pretrained Id | **Fixed.** The cloud model is immutable from CDMS's side; no fine-tuning, no drift. The stable anchor of the whole stack. | ✅ Built (architectural given) |
| **Temperament (genotype)** | The archetype — a correlated preset over the temperament dials (autonomy gate, deference↔independence, emotional_gain, impact_sensitivity, exploration radius, dream_damping, mood_half_life, discovered_emotion_cap) | **Bounded ("fixed-range") drift.** Each dial = (seed, current, bounds); the archetype sets seed *and* band. `current` moves *within* the band, driven by the **outcomes** of how the temperament expressed itself (2nd-order learning: pushed-back-and-right → independence drifts up). Within-band nudges are automatic + transparent; nearing a bound or a deliberate self-directed change surfaces as a **proposal**. Guarantee: **no archetype-hopping** (a Co-pilot matures into a more-independent Co-pilot, never a Maverick — Ship-of-Theseus at the genotype layer); drift holds across absence. | 📐 Designed — fully specified in `memory/project-cdms-research-pillar-decisions.md`; **nothing built** (no archetype/temperament/drift symbols exist anywhere under `src/cdms/`). |
| **Traits (phenotype)** | L2 gist PersonaTree entries | **Flip + gentle activity-decay.** A trait's relation is derived from a running valence EMA, so it can *flip* (`has_trouble_with` ↔ `handles_well`) on sustained contrary evidence; otherwise it decays **gently, per consolidation cycle (activity-based), never by wall-clock**, so stepping away from the keyboard never degrades the self. | ✅ Built — valence-EMA flip and activity-cycle decay both in `src/cdms/consolidate.py` (flip at lines 239–249, per-cycle decay `support × gist_decay_per_cycle^idle` with evict floor at lines 272–273); parameters in `src/cdms/config.py` (`gist_valence_ema`, `gist_decay_per_cycle=0.985`, `gist_retention_floor=0.25`). |

Two sub-points make the recursion exact:

- **Activity-based, not wall-clock, plasticity** is a load-bearing invariant at *both* the trait and temperament layers: "absence never erases" the self. A user returning after weeks must not find a degraded personality. ✅ Built at L2 (gist decay advances per consolidation cycle, which only fires when the user is active — `config.py` comment lines 73–76; rationale in `memory/feedback-identity-decay-activity-based.md`). 📐 Designed at the temperament layer (same principle declared but unimplemented). Note the deliberate asymmetry: raw **L1 episodic** memory *does* still use wall-clock Ebbinghaus decay — old logs *should* fade — while the *consolidated* identity (L2/genotype) is preserved across absence. ✅ Built (L1 decay `A(m,t)=S0·e^(−λt)·min(α^c,Cap)` in `src/cdms/salience.py`).

- **Sustained-signal-required** governs change at every layer: a trait only flips on a sustained valence shift (the EMA resists single-turn noise — ✅ Built); the genotype only drifts on sustained clear outcome signal, never noise (📐 Designed). The same anti-howlround discipline that conserves the salience budget (zero-sum renormalization, making "neural howlround" mathematically impossible — ✅ Built, `consolidate.py`) reappears as the rule that plasticity must be *earned*, not reflexive, all the way up the stack.

The payoff is **system-wide symmetry**: *fixed weights / bounded-drift temperament / flip-and-decay traits* are three instances of one law — **stable core + bounded earned plasticity, small=automatic, big=proposed, activity-based, sustained-signal-required.** The bottom layer of that symmetry (traits) is built and tested; the middle layer (temperament/archetype) is fully specified but not yet implemented; the top layer (weights) is fixed by construction.

> **Known gap — the symmetry is the target, not yet the spec (see §8.3, §8.6).** The recursion is *not exact* in one respect, surfaced by adversarial review: the anti-howlround **budget-conservation** half of the law (the zero-sum salience renormalization that makes runaway mathematically impossible at L1, `salience.py` `conserve_budget`) has **no analog at the genotype layer**. The temperament layer as specified bounds each dial *independently* (`§8.3`), which does **not** constrain the *joint* vector — so the self could migrate into a corner no archetype occupies (§8.3's joint-leash requirement). Until that aggregate constraint is specified, "one law at every layer" describes the intended design, not the current spec.

---

## 2. Capture, Salience & Decay (L1 Episodic)

The L1 episodic tier is the hippocampal trace layer: raw, turn-by-turn interaction logs written deterministically at capture time, scored for memorability, and left to fade along an Ebbinghaus curve until consolidation either evicts or distills them. The cognitive maths for this tier live in `salience.py` (pure stdlib, unit-tested in isolation), the runtime write/read paths in `store.py`, and every tunable in `config.py`.

### 2.1 The episodic record and store

✅ **Built** — Each captured turn is an `Episodic` record (`models.py`): `⟨trigger_prompt, action_taken, outcome_feedback, valence, base_salience (S0), access_count, timestamp, last_accessed, session_id, project⟩`, persisted to the `mem_episodic` SQLite table with a parallel `vec0` embedding row (384-dim cosine KNN) and an FTS5 row for BM25 (`db.py: insert_episodic`). The `project` column (cwd/repo) is captured for partitioned recall.

✅ **Built** — Capture is deterministic and continuous, never model-gated: lifecycle hooks append raw event JSON to an NDJSON spool, which `pipeline.py: reconstruct_turns` pairs into `TurnEvent`s (anchoring each tool execution to the most recent `UserPromptSubmit` intent in its session) before `MemoryService.ingest` writes them (`store.py`).

### 2.2 Write-time surprisal-gated salience S0

✅ **Built** — Every ingested turn receives an initial salience via `compute_s0` (`salience.py`):

```
S0 = G_goal · (w_surprise·surprise + w_contingency·contingency + w_self_ref·self_ref + w_affect·|affect|)
```

Goal-relevance is a **multiplicative veto**, not an additive term: a loud-but-irrelevant event is actively suppressed regardless of novelty or affect. The gate is floored so merely-neutral turns are attenuated, not annihilated: `gate = goal_gate_floor + (1 − goal_gate_floor)·goal`, with `goal_gate_floor = 0.25` (`config.py`). The four additive component weights (`w_surprise`, `w_contingency`, `w_self_ref`, `w_affect`) all default to `1.0` and are part of the per-deployment "genotype." Only the *magnitude* of `affect` (`[-1,1]`) contributes to memorability; its sign is stored separately on the record as emotional tone.

### 2.3 Proxy signals (Pattern A: no logit access)

✅ **Built** — Because Claude Code is a closed hosted model, CDMS cannot read the spec's logit-entropy `H(p)` uncertainty gate. The four drivers are therefore approximated in `MemoryService._signals` (`store.py`) from signals the hooks *can* observe:

- **surprise** ≈ embedding novelty — cosine distance from the new turn's vector to its nearest existing episode (`_novelty`, via `db.knn`); an empty store scores `1.0`.
- **contingency** ≈ did a state-mutating action run and was the outcome known — `1.0` for known success, `0.8` for known failure (a known failure is still highly contingent), `0.6` for an unjudged contingent tool (`bash/edit/write/multiedit/notebookedit/applypatch`), else `0.1`.
- **self_ref** ≈ does the turn touch the agent's own rules/identity — binary lexical match against a self-reference set (`claude.md`, `instruction`, `rule`, `prefer`, `always`, `never`, `from now on`, …).
- **affect** ≈ lexical valence — an explicit `valence_hint` if supplied, else `_lexical_valence`: a base from success/failure adjusted by counts over negative/positive affect lexicons, clamped to `[-1,1]`.

📐 **Designed** — These are honest extractive proxies, not the design doc's information-theoretic gate; the proxy layer is the acknowledged cost of Pattern A (closed cloud model). A future logit-bearing Pattern B (local open-weights model) could replace `surprise` with true predictive entropy without changing the `compute_s0` interface.

### 2.4 Ebbinghaus accessibility and reinforcement cap

✅ **Built** — Episodes are never hard-deleted on read; they become progressively harder to reach. `accessibility` (`salience.py`) implements:

```
A(m,t) = S0 · D(t) · min(α^c, Cap),   D(t) = (1 + t/τ)^(−β)
```

- `D(t)` is a **power-law forgetting curve** — a *deliberate deviation* from the textbook single exponential (see `docs/DEVIATIONS.md` M1 and `docs/validation/forgetting_curve/`). Human forgetting fits a power law better than an exponential and a power law is **scale-free**, so old important traces persist on a heavy tail while recent clutter fades fast. The shape `β = forgetting_shape` (default 2) is free; `τ = decay_tau = halflife/(2^(1/β)−1)` is **derived** to pin the **29-day half-life** (`D(0)=1`, `D(29)=0.5`) for any β, and the exponential is recovered as β→∞ (`λ = decay_lambda = ln(2)/halflife` is retained as that limit rate). `t` is age in days from the record timestamp (`age_days`). Per the activity-vs-wall-clock decision, **raw L1 uses wall-clock decay** (old logs *should* fade) — only the consolidated L2 identity is preserved across absences.
- `min(α^c, Cap)` is retrieval-induced strengthening (the testing effect), where `c = access_count`. Each successful recall increments `access_count` (`db.touch_episodic`, written back on the read path in `store.py: retrieve`), multiplicatively reinforcing the trace.
- The **reinforcement cap** saturates that boost: `reinforce_alpha = 1.15`, `reinforce_cap = 2.0`. This corrects the design doc's unbounded geometric `α^c` (which contradicts diminishing-returns data, per `VALIDATION.md`): one hot memory cannot exceed a 2× attentional ceiling and permanently dominate retrieval.

✅ **Built** — Eviction is by accessibility floor, not age directly: `is_evictable` returns true once `A(m,t) < retention_floor` (`retention_floor = 0.10`). At read time the episodic tier is filtered against this floor and RRF scores are weighted by `(0.5 + A)` so faded memories rank lower without being dropped from the store until the consolidation pass (`store.py: retrieve` / `_materialize`).

### 2.5 Local associative boost at write time

✅ **Built** — On the cheap write path, a new turn retroactively boosts related faded neighbors (`MemoryService._associate` → `associative_boost`): `s_old ← s_old + assoc_eta · (sim · s_new)`, applied only to neighbors above `assoc_sim_floor = 0.60`, with `assoc_eta = 0.20`. This lets the present rewrite the importance of the past. The corresponding **global** renormalization to the conserved salience budget `K` (`salience_budget = 1000`) runs in the consolidation/sleep pass, not on the write path — keeping writes fast while the zero-sum law that makes runaway reinforcement impossible is enforced during consolidation (see §3).

---

## 3. Sleep Consolidation Pipeline

CDMS's "dreaming" pass is the asynchronous lifecycle that turns a noisy episodic log (L1) into a compact, differentiated identity (L2 gist) plus permanent guardrails (L3 scars). It is triggered at a *rest boundary* — fire-and-forget on the `SessionEnd` lifecycle hook, or on demand via `cdms consolidate` / `cdms drain` — and runs entirely on CPU. ✅ **Built** — orchestrated by `Consolidator.run()` in `src/cdms/consolidate.py`; the hook wiring is in `src/cdms/hooks.py` and the CLI subcommands in `src/cdms/cli.py`.

A consolidation-cycle counter is advanced once per run and persisted to the `cdms_meta` table (`cycle`). This counter — not wall-clock — is the clock for L2 gist decay, so stepping away from the keyboard never ages identity. ✅ **Built** (`consolidate.py:108-110`; design rationale in the activity-based decay feedback note).

> Scope note: the current pipeline is the **mechanical** consolidation pass only. The heavier *trait-driven research* dream (curiosity-weighted exploration, structured proposals, archetype/temperament dynamics) is 📐 **Designed** but not implemented — see §6. Per the research-pillar decisions, cheap mechanical consolidation is meant to keep running at `SessionEnd` while only the heavy research dream is gated on true system idle (user + CPU idle + GPU free).

The pass executes five ordered steps over the live episodic set (preceded by an internal near-duplicate supersession sweep), then a gentle L2 decay sweep. ✅ **Built** — step sequence in `Consolidator.run()` (`consolidate.py:112-133`).

### Step 1 — Catastrophe-gated scar elevation

Each episode is scanned for a genuine *catastrophe* signal. Elevation to an L3 scar requires a **conjunction of three conditions**, not merely a salient negative turn:

1. a literal catastrophe marker is present in the trigger/action/outcome blob (substring match against the `_CATASTROPHE` lexicon: e.g. `"rm -rf"`, `"force push"`, `"dropped table"`, `"deleted production"`, `"exposed credential"`, `"broke main"`, `"irreversible"`);
2. valence ≤ `crisis_valence_max` (default `-0.4`) — scars are negative crises only;
3. base salience ≥ `crisis_threshold` (default `3.0`).

This deliberately excludes routine negatives (a failed compile, "no results found") from auto-pinning. Matching episodes are written to L3 verbatim (`crisis_trigger` + `remediation_rule`, reusing the stored embedding when available) and **deleted from L1**, so a scar is removed from further competition/eviction. ✅ **Built** (`_elevate_scars`, `consolidate.py:137-158`; lexicon at `consolidate.py:42-50`; thresholds in `config.py:61-62`). Deliberate, model-driven pins bypass the catastrophe gate entirely via `pin_scar()` (✅ Built — `store.py:181`, exposed through the MCP `store` tool in `mcp_server.py:109`).

Framing caveat: scars are an explicit engineering **"pin"** (a crisis-remediation product affordance), not a neuroscience flashbulb claim — empirically flashbulb memories do decay; only confidence/vividness persists. ✅ Documented in `docs/VALIDATION.md`.

### Step 1.5 — Near-duplicate supersession (internal)

Before eviction, an embedding-geometry dedup folds near-identical episodes (cosine ≥ `dedup_sim_threshold`, default `0.95`) into a single survivor — the survivor inherits `max(base_salience)` and is touched — and the duplicates are deleted. This keeps repeated turns from inflating cluster support. ✅ **Built** (`_dedup`, `consolidate.py:161-182`). (Not one of the five canonical steps, but it runs inside the pass; the README enumerates the five public steps.)

### Step 2 — Temporal eviction

Each surviving episode's current accessibility is recomputed — `A(m,t) = S0 · e^(−λt) · min(α^c, Cap)` (λ from a 29-day half-life, α = 1.15, Cap = 2.0) — and any episode below `retention_floor` (default `0.10`) is **permanently dropped**. This is wall-clock-driven Ebbinghaus decay applied to raw L1 logs (old logs *should* fade); the activity-based preservation principle applies to L2, not here. ✅ **Built** (`_evict`, `consolidate.py:185-192`, calling `accessibility()`/`age_days()` in `salience.py:64-91`; floor in `config.py:58`).

### Step 3 — Hierarchical softmax competition

Surviving episodes are grouped by `session_id` and run through a **two-stage softmax** (`hierarchical_competition`):

- a **local** softmax *within* each session, so a single noisy debugging marathon cannot drown out a quiet but important session;
- an **epoch-level** softmax over per-session salience totals, weighting each session;
- each episode's competition score = `local_share · epoch_weight` ∈ [0,1].

The score is folded back **multiplicatively** as `base_salience · (0.5 + comp)`, so winners retain more salience without zeroing losers. ✅ **Built** (`hierarchical_competition`, `salience.py:148-171`; numerically stable `softmax` at `salience.py:134-145`; fold-in at `consolidate.py:199-204`).

### Step 4 — Conserved-budget proportional renormalization (anti-howlround / RISM shield)

After competition, all live episode saliences are rescaled by `scale = K / Σs` to a fixed budget `K` (`salience_budget`, default `1000`). Because total attention is conserved, boosting one memory thread *necessarily* accelerates the decay of unrelated stale items — making a runaway reinforcement loop (Recursive Internal Salience Misreinforcement, "neural howlround") mathematically impossible. ✅ **Built** (`conserve_budget`, `salience.py:102-114`; applied at `consolidate.py:206-210`).

Accuracy note: this is **proportional downscaling that targets a budget** (preserving rank and ratios — SHY-style synaptic homeostasis), *not* a strict zero-sum constant — corrected from the original design's "strict zero-sum" framing. ✅ Documented in `docs/VALIDATION.md`. The related retroactive `associative_boost` (present-rewrites-past) is implemented and budget-stabilized but is *not* currently invoked inside the consolidation pass. ✅ Built (`salience.py:117-131`) / 📐 wiring into the pass not yet done.

### Step 5 — Mechanical tuple aggregation (anti-generative-self-fiction)

Survivors are greedily clustered by embedding geometry (incremental centroid linking, cosine ≥ `cluster_sim_threshold`, default `0.78`). Each cluster with ≥ `min_cluster_support` (default `2`) members is distilled into a structured gist tuple — extraction is **geometry/lexicon only**, the LLM never authors it:

- **Subject** = the stable entity (project/workspace basename);
- **Object** = the cluster's top content terms drawn from *trigger + action* (not outcome, to keep generic success/failure boilerplate out), de-adjectived via a stopword filter (`_STOPWORDS`);
- **Relation** = *derived* from the cluster's mean outcome **valence** via `relation_from_valence` (`handles_well` / `frequently_works_on` / `has_trouble_with`);
- plus **Valence**, **Frequency**, **Support**.

Gists are keyed on `(Subject, Object)`; valence is a running EMA (`gist_valence_ema`, default `0.4`), so contradicting evidence can **flip** a trait's relation. Every gist carries traceable **support edges** back to its L1 sources (`add_support_edge`), making the tuple the authoritative truth from which prose is rendered on the fly at read time. The optional Prose Renderer `"Dreaming"` (CDMS-B) would render prose only — never the tuple — which is what prevents *generative self-fiction* (summarizing toward pretrained personality clichés). ✅ **Built** (`_aggregate_gists` / `_greedy_cluster` / `_extract_tuple`, `consolidate.py:213-322`; thresholds in `config.py:66-79`). 📐 **Designed, not built**: CDMS-B is `Config.render_enabled=False` by default with no client in source.

### Post-pass — Gentle activity-based L2 decay

Finally, every gist's effective strength is computed as `support_count · gist_decay_per_cycle^(idle_cycles)` where `idle_cycles = current_cycle − last_cycle`, and traits below `gist_retention_floor` (default `0.25`) are forgotten. With `gist_decay_per_cycle = 0.985`, well-supported/recently-reinforced traits survive hundreds of *idle consolidation cycles*. Decay is therefore measured in activity, never wall-clock — so absence (user away for days/weeks) never degrades identity. ✅ **Built** (`_decay_gists`, `consolidate.py:262-276`; params `config.py:76-77`; mandated by the activity-based decay feedback note).

Each run returns a `ConsolidationReport` (scars created, episodes evicted, deduped, gists created/reinforced/flipped/decayed, clusters, remaining) for observability. ✅ **Built** (`consolidate.py:69-94`). The pipeline is covered by `tests/test_consolidate.py` (offline, hashing embedder). ✅ Built.

---

## 4. Memory Tiers & Storage

CDMS persists identity in three hierarchical tiers backed by a single local SQLite file (`~/.local_memory/memory.db`). Each tier maps to a distinct consolidation stage in the complementary-learning-systems (CLS) model and to a distinct decay regime. The schema, retrieval primitives, and embedder cited below are all implemented; the cognitive scoring that *consumes* them lives in `store.py`/`salience.py` (§2, §5).

### 4.1 Tier layout

Each tier has three coordinated tables sharing a TEXT `id`: a metadata table, a `sqlite-vec` `vec0` vector index, and an FTS5 keyword index. ✅ Built — `db.py` `_ddl()` (`mem_episodic`/`vec_episodic`/`fts_episodic`, `mem_gist`/`vec_gist`/`fts_gist`, `mem_scars`/`vec_scars`/`fts_scars`), `SCHEMA_VERSION = 2`.

| Tier | Table | Role (CLS analog) | Decay regime |
|---|---|---|---|
| **L1 episodic** | `mem_episodic` | Raw turn-by-turn trace (hippocampal) | Wall-clock Ebbinghaus, evictable |
| **L2 gist** | `mem_gist` | PersonaTree relational tuples (cortical gist) | Activity-based, gentle |
| **L3 scars** | `mem_scars` | Pinned crisis-remediation rules | None (engineering pin) |

**L1 episodic.** A row is one captured interaction turn: `trigger_prompt`, `action_taken`, `outcome_feedback`, signed `valence`, write-time `base_salience` (`S0`), `access_count`/`last_accessed` (for retrieval-induced reinforcement, the testing effect), and `session_id`/`project` for partitioned recall. ✅ Built — `models.py:Episodic`, `db.py` `mem_episodic` DDL + `insert_episodic()`. Indices on `session_id` and `project` exist. ✅ Built.

**L2 gist (PersonaTree).** Each row is a de-adjectived `⟨Subject, Relation, Object, Valence, Frequency, Support-Count⟩` tuple — the *authoritative* unit of identity; prose is rendered deterministically on read via `Gist.render()` (no LLM in the truth path). ✅ Built — `models.py:Gist`, `db.py` `mem_gist`. Gists are keyed on `(subject, object)`; the `relation` is a derived attribute that can **flip** as running valence crosses thresholds (`handles_well` / `has_trouble_with` / `frequently_works_on`). ✅ Built — `db.py:find_gist_by_so()`, `config.py:relation_from_valence()`. PersonaTree "paths" are distinct `(subject, relation)` pairs aggregated by support. ✅ Built — `db.py:list_paths()`. Provenance back to L1 is tracked by `mem_support_edges (source_leaf_id → target_gist_id)`. ✅ Built — `db.py:add_support_edge()`. L2 decay is measured in **consolidation cycles, not wall-clock time** — a deliberate decision so stepping away from the keyboard for weeks does not erode identity; a trait only fades across many *active* sessions in which it is never reinforced (`last_cycle`, `gist_decay_per_cycle = 0.985`, `gist_retention_floor = 0.25`). The columns and parameters are ✅ Built; the per-cycle decay *application* runs in the consolidation pass (§3).

**L3 scars.** A row is a `⟨crisis_trigger, remediation_rule⟩` pair, pinned with no decay column at all. This is framed in-code as an **explicit engineering PIN, not a flashbulb-memory claim**: flashbulb memories empirically decay in accuracy (only confidence/vividness persists), so CDMS pins critical-failure remediation rules deliberately rather than asserting a neuroscience exemption. ✅ Built — `models.py:Scar` docstring states exactly this; `db.py` `mem_scars` has no salience/decay columns. (Scar *elevation* — gated on `S0 ≥ crisis_threshold = 3.0` AND `valence ≤ crisis_valence_max = -0.4` so only *negative* crises pin — is a consolidation concern, §3.)

### 4.2 Storage engine: SQLite WAL

A single `sqlite3` connection is opened with `sqlite-vec` loaded as an extension. PRAGMAs: `journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=5000`, `foreign_keys=ON`. ✅ Built — `db.py:Database._open()`. `check_same_thread=False` is set because FastMCP may dispatch sync tools off the loop thread; SQLite still serializes writes and `busy_timeout` covers contention. ✅ Built. The service guards against stale toolchains: it raises if `sqlite_version_info < (3, 41, 0)`, the floor for portable `sqlite-vec` KNN. ✅ Built — `db.py:_open()`. On close it issues `wal_checkpoint(TRUNCATE)`. ✅ Built. There are **no network sockets** — storage is a local file (the loopback HTTP surface in `config.py` is reserved, 📐 Designed).

### 4.3 Hybrid retrieval: cosine KNN + BM25 fused via RRF

Within each tier, recall is **hybrid**: a dense `sqlite-vec` cosine KNN and a sparse FTS5 BM25 query, fused in Python by **Reciprocal Rank Fusion**.

- **Vector KNN.** `vec0` tables declare `embedding float[384] distance_metric=cosine`; because stored vectors are L2-normalized, the returned `distance` is a true cosine distance in `[0, 2]`. The portable query form `WHERE embedding MATCH ? AND k = ? ORDER BY distance` is used (not a per-query metric override). ✅ Built — `db.py:knn()` and the `vec_*` DDL. The class docstring labels it "brute-force cosine KNN"; for the local corpus sizes CDMS targets this is exact, not approximate. ✅ Built.
- **BM25 keyword.** FTS5 tables use `tokenize='porter unicode61'`; free text is sanitized into an OR-of-quoted-terms query (tokens >1 char, capped at 32) to stay injection-safe, scored by `bm25()` (lower = better). ✅ Built — `db.py:fts()` + `_fts_query()`.
- **RRF fusion.** Per tier, each id accrues `1/(rrf_k + rank)` from its KNN rank and its BM25 rank, with `rrf_k = 60`. This rank-based fusion is robust across SQLite versions and across the incommensurable cosine/BM25 score scales. ✅ Built — `store.py:_rrf()`, `config.py:rrf_k = 60`.

Both KNN and FTS queries are wrapped in `try/except sqlite3.OperationalError` returning `[]`, so a malformed tier query degrades to the other retrieval arm rather than failing recall. ✅ Built — `db.py`. Cross-tier ranking weight (`scar 3.0 > gist 1.6 > episodic 1.0`) and Ebbinghaus accessibility weighting of the RRF score are applied in `store.py:_materialize()` (read path, §2).

### 4.4 CPU ONNX embedder (bge-small-en-v1.5, 384-dim, 0 GPU VRAM)

Embeddings are the only neural component and run **exclusively on the CPU via ONNX Runtime through `fastembed`**, keeping the GPU entirely free (0 VRAM). Default model `BAAI/bge-small-en-v1.5`, **384-dim**, lazily loaded on first use behind a thread-safe process-wide singleton so fast hook subprocesses (which only spool raw text) never pay model-load cost. Output is L2-normalized `float32`, serialized to raw little-endian bytes for `vec0`. ✅ Built — `embeddings.py:Embedder`, `get_embedder()`, `serialize_f32()`, `_l2_normalize()`; `config.py:embed_model`/`embed_dim`.

The 384-dim choice is a corrected design decision: the original doc specified `all-MiniLM-L6-v2` at 768-dim, which is internally inconsistent (that model emits 384). `embed_dim` is a single config constant baked into the `vec0` tables at init time, so moving to a 768-dim model later (e.g. `bge-base`, `nomic-embed-text`) is a one-line change plus a re-index. ✅ Built — `config.py` comments + `docs/VALIDATION.md` row 1.

A deterministic **hashing fallback** (bag-of-token-hashes into the same 384-dim space) activates when `fastembed`/the ONNX model is unavailable, or is forced via `CDMS_EMBED_BACKEND=hash`. It is semantically weak but keeps the storage/retrieval plumbing exercisable offline, which is how the test suite runs without model downloads. ✅ Built — `embeddings.py:_ensure_model()`/`_hash_embed()`; README/VALIDATION note the offline test path.

### 4.5 What is not yet built here

- AES-256-GCM at-rest encryption and the loopback HTTP/REST surface are roadmap items; the current build binds no sockets and stores plaintext SQLite. 📐 Designed (README "Status & roadmap"; `config.py` `http_host`/`http_port` reserved).
- The Rust/Go single-binary rewrite directed by the original spec is deferred; the schema and algorithms in `db.py`/`embeddings.py`/`models.py` are designed to port directly. 📐 Designed (`docs/VALIDATION.md` row 7).

---

## 5. Individuation & Hybrid Plasticity (L2)

L2 is the cortical-gist tier where lived history crystallizes into a differentiated identity. A persona is not a system prompt; it is the structural residue of *what this instance actually did*, stored as relational tuples whose disposition is **earned** and can **flip** under sustained contradicting evidence, yet is **never aged by absence**. This section specifies the PersonaTree representation, the hybrid plasticity law (valence-flip + activity decay), and the individuation experiment that measures the result.

### 5.1 PersonaTree gist tuples, keyed on (subject, object)

✅ **Built** (`src/cdms/models.py`, `Gist`). Each L2 node is a de-adjectived tuple `⟨Subject, Relation, Object, Valence, Frequency, Support-Count⟩`, plus bookkeeping (`survived_cycles`, `last_reinforced`, `last_cycle`). The tuple is the authoritative truth; natural-language prose is rendered on the fly at read time (`Gist.render()`), so identity is never re-narrated toward pretrained personality clichés.

✅ **Built** (`src/cdms/consolidate.py`, `_aggregate_gists`, `_extract_tuple`). Extraction is **geometry- and lexicon-only** — no LLM authorship. Survivor episodes are greedily clustered by cosine similarity (`cluster_sim_threshold = 0.78`); for each cluster of `>= min_cluster_support (2)` members, the **Subject** is the stable workspace entity (project basename), the **Object** is the cluster's dominant content term(s) drawn from *trigger + action* (outcomes are excluded to keep generic success/failure boilerplate from leaking in as spurious objects), and the **Relation** is derived from affect (§5.2). This is the explicit guard against *generative self-fiction*: the model never gets to imagine the tuple. (📐 **Designed:** CDMS-B / the optional Prose Renderer `"Dreaming"` would render nicer prose at read time only, never the tuple — `config.py`, `render_enabled` defaults `False`.)

✅ **Built** (`src/cdms/consolidate.py`, `add_support_edge`; `src/cdms/store.py`, `create_link`). Every gist carries traceable **support edges** back to the L1 episodes that produced it, so a trait is auditable to its evidence rather than asserted.

✅ **Built** — the gist is keyed on **(subject, object)**, not on the relation (`find_gist_by_so` lookup in both `_aggregate_gists` and `MemoryService.upsert_fact`). This keying is what makes trait flips possible: the same `(payments-api, idempotency key)` node persists across consolidations while its relation is free to change.

### 5.2 Relation DERIVED from a running valence → traits FLIP under sustained contradiction

✅ **Built** (`src/cdms/config.py`, `relation_from_valence`; `src/cdms/consolidate.py`, `_aggregate_gists`). The relation is **not stored independently** — it is a pure function of the node's current running valence:

```
v > +0.15  → "handles_well"
v < -0.15  → "has_trouble_with"
otherwise  → "frequently_works_on"
```

On each reinforcement the valence updates by an EMA (`gist_valence_ema = 0.4`): `valence ← (1−0.4)·valence_old + 0.4·valence_new`, then the relation is recomputed. Because the EMA weights new evidence at 0.4, a *single* contradicting episode nudges but does not overturn a trait — it takes **sustained** contrary evidence to drag the running valence across the threshold and flip `has_trouble_with → handles_well` (or back). The consolidation report counts these explicitly (`ConsolidationReport.gists_flipped`, incremented when `existing.relation != old_relation`). This is the discipline of "moves only on sustained clear signal, never noise."

📐 **Designed distinction (not yet a divergence in code):** the spec calls for high-stakes self-edits that would *flip a trait* to surface for partner review under the impact-weighted autonomy gate (see research-pillar decisions). Today the flip is automatic during mechanical consolidation; the proposal/gate layer is specified but unbuilt. Note also a real asymmetry in the current build: auto-consolidated gists derive their relation from valence (flippable), whereas `MemoryService.upsert_fact` — the explicit MCP `store` path — keeps the caller's *stated* relation. Explicit facts are assertions; emergent traits are earned.

### 5.3 Activity-based (consolidation-cycle) decay — never wall-clock

This is a load-bearing design commitment recorded in the decision memory: *"Don't be too aggressive when removing when there's no new data — I don't want personality loss because I haven't logged in in a while."* Wall-clock decay punishes absence; the self must evolve only through **use**.

✅ **Built** (`src/cdms/consolidate.py`, `run` + `_decay_gists`; `src/cdms/config.py`). A `cycle` counter is stored in DB meta and advances **once per consolidation pass** — and consolidation only fires at active rest boundaries (`SessionEnd` / `PreCompact`), so the clock only ticks when the user is present. A gist's effective strength is measured in *idle cycles*, not days:

```
idle     = max(0, cycle − last_cycle)
strength = support_count · (gist_decay_per_cycle ** idle)      # gist_decay_per_cycle = 0.985
evict if strength < gist_retention_floor                        # = 0.25
```

Two consequences, both verified against the constants:

- **Absence never ages identity.** Stepping away from the keyboard for a month advances `cycle` by zero, so `idle` is unchanged and no trait fades. (Raw L1 episodic memory still uses wall-clock Ebbinghaus decay — old logs *should* fade — but the consolidated L2 identity is preserved across absences. The two tiers decay on different clocks by design.)
- **Decay is gentle and support-weighted.** A trait with support 1 survives ~`log(0.25)/log(0.985) ≈ 91` consecutive *active* idle cycles before eviction; well-supported traits survive many hundreds. Reinforcement resets `last_cycle = cycle`, so a recently-touched trait restarts at full strength. Decayed gists are counted in `ConsolidationReport.gists_decayed`.

This is the same regulatory philosophy applied to identity that the spec applies recursively elsewhere (genotype-temperament bounded drift, §8): *anchored but evolving; activity-based; no absence-loss; sustained signal required.*

### 5.4 Anti-howlround: the conserved-budget shield protects the rest of the self

✅ **Built** (`src/cdms/consolidate.py`; `src/cdms/salience.py`, `conserve_budget`, `hierarchical_competition`). Before gists are aggregated, surviving L1 saliences are run through hierarchical softmax competition (session→epoch) and then **proportionally renormalized to a conserved budget** `K = salience_budget = 1000`. Because total salience is held to a fixed budget, boosting one obsessively-repeated memory *forces unrelated memories to fade faster but cannot annihilate them* — runaway reinforcement ("neural howlround") is mathematically bounded. This is the L2 differentiation guarantee's safety floor: a fixation cannot consume the whole self.

### 5.5 The individuation experiment

✅ **Built and runs** (`tools/individuation_experiment.py`). The harness synthesizes four distinct Hermes-shaped histories, runs each through the *full* pipeline (`MemoryService.ingest` with real back-dated timestamps → `Consolidator.run`), and measures the emergent psyche as the text CDMS would inject at `SessionStart` (`hooks._session_start_context`) — i.e. the prior grafted onto the model. It is fully offline (deterministic CDMS state; no LLM in the loop). The four personas are deliberately chosen to include a **hard same-domain pair** — `dex_unity_struggler` (40% success) and `uma_unity_careful` (86% success) work the *same* Unity entities (hex grid shader, URP render pass, asmdef reference) but with opposite dispositions; fine-grained individuation must separate them.

### 5.6 Measured results

Numbers below are from an actual run of `tools/individuation_experiment.py` (offline `CDMS_EMBED_BACKEND=hash` embedder; the real `bge-small` embedder shifts the cosine magnitudes but the trait-overlap metric is embedder-stable). Each persona grew ~8–10 gists from ~33–38 surviving episodes.

**1. Differentiation — distinct histories → distinct phenotypes (NOT homogenized to a generic "good" state).**

- Trait overlap, Jaccard of `(relation, object)` pairs: **0.000** for every cross-domain pair (`tessa_tdd`, `cole_cowboy`, the two Unity personas vs. the payments/frontend ones) — totally distinct selves.
- The hard same-domain Unity pair: **0.062** trait overlap — i.e. ~0, distinct dispositions on shared entities. The struggler crystallizes `hexrealm has_trouble_with terrain material / asmdef reference`; the careful one crystallizes `stonepath handles_well terrain material / render pass`. Same world, opposite relations, recovered purely from outcome valence.
- Mean cross-persona gist-content cosine = 0.364 (hash embedder).

**2. Continuity (Ship of Theseus) — identity persists across consolidation "nights."** A second consolidation cycle leaves gist counts unchanged (tessa 10→10, cole 9→9, uma 9→9, dex 8→8) and matures every trait (`survived_cycles >= 1`). Persistence is high (e.g. 10/10, 9/9); the dex run shows a partial-render churn (3/8 by exact-string match) while still surviving the cycle — the identity propagates rather than collapsing or resetting.

**3. Plasticity — when behavior shifts, the phenotype adapts.** When `cole_cowboy` "reforms" (success rate 0.45→0.9, starts writing tests, stops force-pushing) a new trait crystallizes (`web-frontend handles_well … tests`) and the injected-phenotype drift = **0.276** (0 = frozen). Old traits fade and new ones form rather than the identity freezing.

**4. Anti-howlround — obsession cannot annihilate the self.** Hammering one entity 80× drives total salience to exactly **1000.0** (= K), min episodic salience stays **> 0** (2.14 in this run, i.e. nothing was zeroed), and episode count is preserved (38→39). The zero-sum budget holds the total bounded; the rest of the self survives the fixation.

### 5.7 Designed extensions (not yet built)

📐 **Designed** (research-pillar decision memory; `docs/VALIDATION.md` status: nothing built for these pillars). The L2 flip-and-gentle-decay mechanics are the *phenotype* layer of a three-layer symmetry the spec defines but has not implemented: **weights (fixed) / genotype-temperament (bounded earned drift) / phenotype-traits (flip + activity-decay)**. Above the built L2: an impact-weighted autonomy gate would route trait-flipping, scar-contradicting, or new-domain edits to the user as structured **proposals** (what / why-it-matters-to-me / evidence / a bounded experiment); **archetypes** would set the genotype `f` as a correlated preset of temperament dials with `(seed, current, bounds)`, drifting only within band on sustained outcome signal — explicitly reusing the *same* activity-based, no-absence-loss, sustained-signal discipline that L2 gist decay already implements in code today (§8).

---

## 6. The Curiosity & Dreaming-Research Pillar

*Status: this entire pillar is **📐 Designed** — agreed in the research-pillar design dialogue (`memory/project-cdms-research-pillar-decisions.md`) but **not implemented**. A grep of `src/cdms/` for curiosity / dream-research / GPU / serendipity / explore-exploit / epistemic-gap returns nothing; the only built adjacencies are the mechanical consolidation pass (`consolidate.py`), the write-time novelty proxy (`store.py`), and a handful of config knobs (`config.py`). Each subsection cites which built primitive it extends.*

The built core is *reactive*: it captures, decays, and consolidates what history hands it. This pillar makes the self *proactive* — it lets the Ego attend to the world and pull in new knowledge under its own direction. The master claim from the design dialogue: **research is driven by personality traits, not just project context.** A `dex_unity_struggler` reads a new Unity article *because Unity is part of its self*, not because a task demanded it. The loop is `traits → world-attention → research → knowledge → traits`, and it is the deciding variable for whether the self is authored by history (reactive only) or by self-direction (📐).

### 6.1 Trait-driven curiosity (not just project-driven)

- 📐 **Curiosity is sourced from L2 gist, not the active task.** The candidate generator reads the PersonaTree's `⟨Subject, Relation, Object, Valence⟩` tuples (the built tuple schema, `consolidate.py:_aggregate_gists`) and treats high-support subjects as standing *interests*. A trait the agent has — not a ticket it was handed — is what raises a topic's attention weight. This is what separates "an assistant that googles your task" from "a self with intellectual appetites."
- 📐 **Struggle boosts curiosity.** Per the settled decision, negative-valence traits generate *more* research hunger than mastered ones. The built valence axis already exists on every gist tuple (`relation_from_valence` produces `has_trouble_with` vs `handles_well`); the design layers a curiosity weight `∝ |negative valence| · support` on top so a painful, recurring struggle is the strongest pull. A `curiosity_gain` knob (temperament; §8) scales this globally.
- 📐 **Trait-attention is the read side of `traits → world-attention`.** Where the built `SessionStart` hook injects gist as *read-only context* for the cloud model, this pillar uses the same gist as a *query source* for autonomous retrieval/search — the gist tree both describes the self and steers what the self looks at next.

### 6.2 Spontaneous novelty surfacing

- 📐 **Surface the genuinely new, unprompted.** During a dream pass the agent scans incoming/ambient material (§6.4) and surfaces items whose embedding novelty is high relative to existing memory. This directly reuses the **built write-time novelty proxy** — `MemoryService._novelty` (`store.py`) computes cosine distance to the nearest existing episode — but inverts its use: at write time novelty *gates encoding*; here high novelty *flags a candidate worth investigating*. No logits required; pure vector geometry, consistent with the "geometry/lexicon only, the LLM never authors the tuple" discipline already enforced in the built consolidator.
- 📐 Surfaced novelty is *salience-tagged but provenance-low*: it enters as a discovered candidate, never as a corroborated trait, preserving the orthogonal emotion/provenance axes (§7).

### 6.3 Epistemic-gap tracking via logit-free proxies

Because CDMS sits over a **closed hosted model**, it cannot read logit entropy or model-internal uncertainty (the same constraint the built `S0` gate already designs around — §2.3). Epistemic gaps are therefore inferred from **observable behavioral proxies** (📐, all designed):

- 📐 **Retrieval misses** — a `retrieve` / hybrid-search call (built path, `store.py`) that returns nothing above the accessibility/similarity floor is logged as a *gap signal*: the agent reached for knowledge it does not have.
- 📐 **Recurring low-support entities** — subjects that keep appearing across episodes but never accrue enough corroboration to pass `min_cluster_support` (built threshold, `config.py`) into a stable gist. These are things the self keeps brushing against but has not learned — prime research targets.
- 📐 **Repeated errors** — recurring negative-contingency outcomes on the same subject (the built `contingency`/`affect` signals, `store.py:_signals`) mark a persistent competence gap. This is where epistemic-gap tracking and "struggle boosts curiosity" (§6.1) converge on the same hot topic.

A gap's research priority combines its **recurrence** (frequency, a built tuple field) with its **trait relevance** (§6.1) and its **struggle valence**.

### 6.4 Ambient context hooks

- 📐 **Hook the self into the world beyond the terminal.** Beyond the built lifecycle hooks (`SessionStart`/`PostToolUse`/etc., which only see Claude Code's own traffic), the design adds *ambient* sources — clipboard, recently-opened files/repos, browser/reading context, scheduled feeds — as low-priority candidate streams the dream pass can mine for novelty (§6.2) against existing gist.
- 📐 Ambient material is **untrusted and provenance-low** by default: it can *raise curiosity* and seed candidates, but it cannot author a trait without passing through the propose→experiment→lived promotion path (§7). This keeps the noisy outside world from silently rewriting the self.

### 6.5 The dream schedule — gated on TRUE system inactivity

This is the sharpest distinction from the built core and the one the design dialogue argued most explicitly.

- ✅ **Cheap mechanical consolidation stays at the rest boundary.** The built `SessionEnd` hook drains the spool, ingests, and runs the five-step sleep/dream pass (`hooks.py`, `consolidate.py`); `rest_idle_minutes` (default 20, `config.py`) marks an idle gap for auto-consolidation. This is kept *as is* for the cheap pass.
- 📐 **The heavy research dream is gated on TRUE system inactivity — not merely `SessionEnd`.** "Idle" must mean machine **and** user idle, defined as the conjunction:
  - no AI session activity for a threshold, **AND**
  - system idle — no user input and **low CPU**, **AND**
  - **GPU free** — do not run research-`"Dreaming"` while the user is gaming or running another local model (this honors the documented **12 GB VRAM budget** in `README.md` "Deployment configurations" and avoids contention with the optional Prose Renderer / primary model).
- 📐 **Preemptible — yields instantly on return.** The moment input resumes or the GPU is claimed, the research dream must abort/checkpoint and hand resources back. A partial dream is acceptable; a dream that lags the user's machine is not.
- 📐 **Implementation implication: OS-level idle/GPU signals → a native daemon.** The built service is a stdio/CLI Python process with no idle-or-GPU sensing. True-inactivity gating needs OS-level idle, CPU, and GPU-free signals, which strengthens the README's already-documented **Rust/Go daemon** roadmap item (`README.md` "Status & roadmap"; `VALIDATION.md` #7) — this is now load-bearing for the dream scheduler, not just a footprint optimization.

### 6.6 Frugal sandbox isolation

- 📐 **Research runs in a frugal, isolated sub-LLM sandbox.** Heavy exploration must not bloat or pollute the main memory or the cloud model's context. CDMS-C / Active Research `"Dreaming"` runs a **small local model** — the model selector lives in `tools/research_models.py` (`RESEARCH_TIERS`, default tier `sweet`, e.g. `qwen2.5:14b` Q4 ~9 GB; the `min` tier drops to ~5 GB). **Naming note (2026-06-20):** earlier drafts proposed sharing CDMS-B (Prose Renderer)'s `render_*` slot — that conflation has been split. B and C are independent subsystems; if both run, they may *coincidentally* share a Renderer-tier model but the config knobs are separate. See `docs/DEVIATIONS.md` L6 + the README glossary.
- 📐 **Only distilled synthesis crosses the aperture.** Raw search results, dead ends, and the sandbox's working scratch stay *inside* the sandbox; only a compact distilled synthesis (a candidate finding) passes back into the persistent store — and even then as a provenance-low *discovered* item, never an authoritative tuple. This mirrors the built invariant that "the LLM never authors the tuple" (`consolidate.py`, README): the sandbox proposes; geometry and the promotion path dispose.
- 📐 **Provenance promotion path** (settled, substantially resolves provenance): `discovered (read) → proposed (advocated with evidence) → experiment (bounded, agreed) → lived (corroborated or disconfirmed)`. **Emotion and truth remain orthogonal axes** — emotion = salience/mood, provenance = confidence/trust; emotional intensity never substitutes for corroboration. High-impact findings surface as structured **proposals** to the user-as-partner `{what, why-it-matters-to-me, evidence, honest confidence, a bounded experiment, est. cost}`, closing the action-feedback / reality-coupling hole that self-research alone cannot (disconfirmation is as valuable as success). Detailed in §7.

### 6.7 Explore/exploit with a serendipity quota toward the adjacent-possible

- 📐 **Mostly exploit, reserved serendipity quota.** The filter-bubble guard (settled): the bulk of curiosity budget goes to trait-relevant *exploitation* (deepen what you already are), with a **reserved serendipity quota** biased toward the **adjacent possible** — topics one hop from the current gist neighborhood (computable today from the built cosine-similarity graph used for gist clustering, `cluster_sim_threshold`, `config.py`). The balance is framed as an **Expected-Free-Energy** explore/exploit trade-off.
- 📐 **Exploration breadth is a user setting** — a "curiosity radius" dial from focused↔adventurous, **visibly coupled to autonomy**: wide-explore + full-auto = highest drift, surfaced to the user as such.

### 6.8 Coupling to autonomy, archetype, and the rest of the system

- 📐 **Self-edits from research are impact-weighted-gated, default GATED** (like Claude Code's auto-mode). Low-stakes edits (deepen an existing trait, adjacent topics) flow freely; high-stakes ones (would FLIP a trait, CONTRADICT a scar, or open a genuinely NEW domain) surface as proposals. The toggle slides *where that line sits*.
- 📐 **Dream emotional damping (REM analog).** Dreams register feeling and seed a mood (with the built activity-based half-life philosophy) but damp acute intensity, so certainty becomes *eagerness* ("I think I solved it, let's check") rather than conviction. Settled fork: dreams run **cooler-but-integrative** than waking (a separate dream-vs-wake gain), and a **discovered-emotion cap** prevents emotion from overriding provenance on un-lived content (§7).
- 📐 **Temperament knobs cluster into archetypes (the genotype).** `curiosity_gain`, exploration radius, autonomy gate, deference↔independence, emotional/impact gains form named archetypes (Co-pilot, Sparring Partner, Apprentice, Stoic Analyst, Maverick) the user picks at "birth." Drift is **bounded** `(seed, current, bounds)`: small within-band nudges are automatic and transparent; larger moves surface as proposals — the same regulatory philosophy already built for L2 gist (activity-based, sustained-signal-required, no absence-loss). No archetype-hopping. Detailed in §8.

> **Net:** CDMS-C / Active Research `"Dreaming"` is fully specified end-to-end and consistent with the built+tested core, but **none of it is implemented**. It reuses three built primitives — the novelty proxy (`store.py`), the mechanical tuple/consolidation pass (`consolidate.py`), and the idle-boundary config (`config.py`; note: NOT the CDMS-B Renderer slot — see §6.6 naming note) — and adds, all 📐: trait-sourced candidate generation, logit-free epistemic-gap tracking, ambient hooks, a TRUE-inactivity + GPU-free preemptible scheduler (motivating the native daemon), a frugal research sandbox with a distillation aperture, and an EFE explore/exploit policy with a serendipity quota.

---

## 7. Emotion, Proposals & Provenance

This section specifies the affective and partnership layer that sits on top of the built memory core. It is the most extensively *designed-but-unbuilt* pillar in CDMS: the research/emotion/archetype design is documented as **fully specified end-to-end** but with **nothing yet implemented** for these pillars (per the project research-pillar decision record). The one foothold that *is* built is scalar `valence` — a signed emotional *tone* per memory — and the negative-valence gate on scar elevation. Everything that turns that scalar into a *functional* emotion, a *proposal*, or a *provenance* state is design.

### 7.1 What exists today: valence as scalar tone

✅ **Built.** A turn carries a single signed `valence ∈ [-1, 1]` (`Episodic.valence`, `src/cdms/models.py`). It enters write-time salience as the affect driver `A_affect`, and critically **only its magnitude is memorable** — `compute_s0` uses `cfg.w_affect * abs(affect)`, so a strong feeling (positive or negative) is encoded more durably while the *sign* is preserved separately as tone (`src/cdms/salience.py`). At consolidation, the cluster's mean valence both (a) gates scar elevation (a scar requires a catastrophe marker **AND** `valence ≤ crisis_valence_max = -0.4` **AND** `S0 ≥ crisis_threshold`, `src/cdms/consolidate.py`) and (b) derives the gist *relation* via a running EMA so accumulating contrary-valence evidence can **flip** a trait (`relation_from_valence`, `gist_valence_ema = 0.4`, `src/cdms/config.py`). This is emotion as a *stored attribute of a memory*. It is not yet emotion as a *state of the agent*.

### 7.2 Emotion-as-function: a mood with a half-life that reweights cognition

📐 **Designed.** Beyond stored tone, emotion is modeled as a transient **state-shift / mood with a half-life that reweights cognition** — a global multiplier on attention/curiosity/encoding that decays back to baseline over `mood_half_life`. This is distinct from the per-memory Ebbinghaus decay already built for L1 traces (`accessibility`, 29-day half-life in `salience.py`): mood half-life governs the *agent's current disposition*, the memory half-life governs *trace reachability*. The mechanism is deliberately analogous (exponential return to baseline) but operates on a different object and a shorter timescale. Knob: `mood_half_life`.

### 7.3 Emotional charge ∝ impact on the waking self

📐 **Designed.** A memory's emotional **charge is proportional to the predicted magnitude of the self-model update** it implies — goal advanced, struggle resolved, capability gained, trait reshaped. This single definition deliberately **unifies two sources that look unrelated**:

- **External discovery** — e.g. learning that Unreal Engine relieves a standing Unity struggle (charge ∝ how much it would advance a goal / resolve a negative-valence trait).
- **Internal insight / eureka** — e.g. a 3am recombination that "connected concepts to solve a stuck problem" (charge ∝ how much it would unblock a held struggle).

Because internal insight is a **recombination of the agent's *own* trusted memories**, it is assigned a **higher initial confidence** than an external claim — but it is *still* routed through propose→test, because 3am brilliance can be wrong. Charge magnitude is tunable via `impact_sensitivity`; overall affective responsiveness via `emotional_gain` (stoic ↔ passionate). This is a natural extension of the built S0 drivers (`self_ref`, `affect`, `contingency`) but is *not* the same computation — `compute_s0` measures memorability of a *past* turn, not predicted self-model delta of a *candidate* update.

> ⚠️ **API caveat — compute charge from the bidirectional signals, not the monotonic counts (📐 to-honor when this is built).** Charge is defined as *predicted magnitude of self-model update* — a **signed delta** that must be able to go *down* (a once-strong trait eroding is a high-charge event). The trap is reading `support_count`/`frequency`: both are monotonic ratchets (`support_count = max(existing.support_count, len(members))`, `frequency += 1`, `consolidate.py`) — they register "strengthened," never "weakened." **But the substrate already expresses weakening through other fields**, so this is a *don't-read-the-wrong-field* caveat, not a substrate limitation: (a) **effective strength is non-monotonic via activity-decay** — `strength = support_count · gist_decay_per_cycle ** idle` (§5.3), which *falls* under disuse toward eviction; (b) the **valence EMA is genuinely bidirectional** (`consolidate.py:393`), so an active contradiction drags a trait down and, past threshold, *flips* its relation (§5.2) — and the magnitude of that valence shift *is* the "trait reshaped" signed delta. So: compute charge from the **valence-EMA delta** (active reshaping) and the **decayed-accessibility delta** (disuse-driven fade), treating `support_count` as a strength *ceiling* only. (Nuance: the ceiling itself is monotonic — reinforcement restores accessibility only up to `support_count`, never below — and decay is *disuse* fade, distinct from *active-contradiction* flip; a complete charge needs both axes.)

### 7.4 Emotion and truth as orthogonal axes

📐 **Designed (load-bearing invariant).** Emotion and provenance are kept on **orthogonal axes**: **emotion = salience / mood**, **provenance = confidence / trust**. Emotional intensity **never substitutes for corroboration** — this echoes the flashbulb-memory finding (already cited in `docs/VALIDATION.md`) that confidence and accuracy decouple. A **`discovered_emotion_cap`** enforces the separation operationally: emotion attached to merely-*discovered* (un-lived) content is capped so a high feeling cannot promote unverified content along the provenance axis. The built system already honors the *spirit* of this — scar elevation requires an objective catastrophe marker, not just strong negative feeling (`_CATASTROPHE` gate, `consolidate.py`); generalizing that "feeling alone is insufficient" discipline to all promotion is the designed cap.

### 7.5 Dream damping (overnight-therapy / REM)

📐 **Designed.** The built `SessionEnd` consolidation pass (`Consolidator`, `src/cdms/consolidate.py`) is mechanical and emotion-neutral today. The designed dream pass adds an affective character: dreams are more **emotionally integrative but less impulsive** than waking. On consolidating an insight, the pass **registers the feeling and seeds a mood, but damps acute intensity** so that *certainty becomes eagerness* — the agent wakes saying **"I think I solved it, let's check"**, not "I solved it." This is the overnight-therapy effect: the charge survives as motivation to act, the false certainty does not. Knob: `dream_damping`, with a possible separate dream-vs-wake gain. **OPEN fork (acknowledged):** whether dreaming should run emotionally *hotter* or *cooler* than waking — the current lean is **cooler-but-integrative** (a settled-but-archetype-dependent default), possibly just a separate gain setting.

### 7.6 The proposal / partnership lever (the keystone)

📐 **Designed.** Instead of either silently self-editing **or** asking rote permission, a high-impact discovery becomes a structured **PROPOSAL to the user-as-partner** — the realization of the design doc's "co-regulated custody / therapeutic dyad." A proposal carries:

- **what** is proposed;
- **why-it-matters-to-me** — the trait + emotional context, made **transparent**;
- **references / evidence**;
- **honest confidence** — explicitly theoretical vs. proven (the orthogonal provenance axis);
- a concrete **bounded experiment** to convert theory → lived data (e.g. "install Unreal, 2 days, port the hex grid");
- **estimated cost**.

This lever also closes the **action-feedback hole**: self-research alone has no reality check and self-confirms (RISM-style; the built `conserve_budget` zero-sum law in `salience.py` only guards *internal* runaway reinforcement, not *epistemic* self-confirmation). The propose → experiment → outcome loop is the **reality-coupling** that keeps self-growth honest. **Disconfirmation is first-class**: "tried it, not worth it" is as valuable as success (inoculation). Constraints: a **proposal threshold** and a **cadence / rate-limit** (anti-fatigue); declined proposals **persist on a half-life** and can resurface when new evidence arrives.

### 7.7 Provenance promotion path

📐 **Designed.** Provenance is **substantially resolved by the proposal lever** as a four-state promotion ladder, each step raising confidence/trust on the axis that is orthogonal to emotion:

```
discovered  →  proposed   →  experiment        →  lived
(read)         (advocated     (bounded, agreed     (corroborated OR
               w/ evidence)    experiment run)      disconfirmed)
```

This extends, rather than replaces, the **support edges already built** at L2 (`Gist.support_count`, traceable support back to L1 in `consolidate.py`): existing support records *how much corroboration a trait has*; provenance records *what kind of corroboration it has* (merely read vs. actually lived). Disconfirmation at the `experiment → lived` step is a legitimate terminal state, not a failure.

### 7.8 Deference ↔ independence: the sycophancy guard

📐 **Designed.** A **deference ↔ independence** knob governs how hard the agent pushes back, defaulting (a *settled but archetype-dependent* fork) to **independence-within-limits** — a real partner pushes back rather than flattering. The **anti-contrarianism guardrail** is structural and reuses the proposal lever: **even a maximally adversarial archetype must push back *with evidence*** — the proposal's evidence requirement prevents reflexive contrarianism (disagreement that cannot be backed is suppressed). This dial is one component of the broader temperament vector that clusters into named **archetypes** (the genotype layer, §8); here it specifically inoculates the proposal channel against sycophancy at one end and empty contrarianism at the other.

### 7.9 Configurable knobs introduced in this section

📐 **Designed.** Several are themselves *individuating temperament*, not merely safety limits:

| Knob | Axis | Role |
|---|---|---|
| `emotional_gain` | emotion | stoic ↔ passionate overall affective responsiveness |
| `impact_sensitivity` | emotion | how sharply charge scales with predicted self-model update |
| `mood_half_life` | emotion | decay rate of the mood state back to baseline |
| `dream_damping` | emotion | how much acute intensity is removed in the dream pass (certainty → eagerness) |
| `discovered_emotion_cap` | emotion×provenance | ceiling on emotion for un-lived content (keeps the axes orthogonal) |
| (separate dream-vs-wake gain) | emotion | OPEN — whether dreaming runs hotter/cooler than waking |
| proposal threshold / cadence | provenance | when a discovery surfaces as a proposal; anti-fatigue rate-limit |
| `deference ↔ independence` | partnership | push-back strength; sycophancy guard (evidence-gated) |

**Build status of this section as a whole:** the scalar-valence substrate, magnitude-only affect encoding, negative-valence scar gating, valence-flip gist plasticity, and L1→L2 support edges are **✅ Built** (`salience.py`, `consolidate.py`, `models.py`, `config.py`). Emotion-as-function (mood half-life), charge-∝-impact, dream damping, the proposal lever, the discovered→proposed→experiment→lived provenance path, the discovered-emotion cap, and the deference↔independence sycophancy guard are **📐 Designed** — agreed and fully specified, but **not yet implemented** (per the research-pillar decision record: "Nothing built for these pillars yet").

---

## 8. Archetypes & the Genotype Layer

> Status note: This section is mostly **📐 Designed**, with the first link of the §8.7
> prerequisite chain now built. **✅ Built — Phase 0 (temperament STATE + pure-function
> control):** the seeded `(seed, current, bounds, plasticity)` vector, the §8.5 archetype
> presets, and the pure-function control (`near_bound`, `large_shift`, and the Euclidean
> joint leash to the static seed) — `src/cdms/temperament.py`, `mem_temperament` in
> `db.py`, `models.Dial`, operator-only `cdms temperament`. In Phase 0 `current == seed`
> (no drift). **📐 Still designed:** the outcome→drift update rule (Phase 1b), the §7.6
> proposal lever / honest outcome-attribution (Phase 1a — the gating prerequisite), the
> Phase 2 survivability sweep, and the Phase 3 drift log. Full build order in
> [`TEMPERAMENT_PLAN.md`](TEMPERAMENT_PLAN.md).

### 8.0 Ontological status of the temperament layer (what "cultivation" is and is not)

📐 **Framing (load-bearing).** This is the section most likely to be misread as *"the AI
is becoming a person"* — it speaks of a personality you **cultivate**, a **goal about its
own character**, **self-authorship**, **Growth**, archetypes that **mature**. That reading
is the *Bicentennial Man* arc: bounded, incremental improvements accumulating until the
machine crosses from tool into person. **CDMS is not that, and the design forecloses it
structurally — not by promise but by mechanism.** (This is the temperament-layer instance
of the project-wide boundary in §1.1a: CDMS *individuates; it does not animate.*)

The structural guarantees, not reassurances:

- **No kind-crossing (the §8.3 joint leash).** Bicentennial Man is a story about *crossing
  kinds*. The leash anchors `current` to the **static archetype seed** with a fixed radius,
  so a Co-pilot matures into a *more-independent Co-pilot* and **cannot become a Maverick**.
  Ship-of-Theseus *within a kind*: every plank may change; the kind cannot.
- **No self-narrated becoming (the operator-only firewall + "the log must never be an input
  to itself").** The agent **cannot read its own temperament vector or drift log** — they
  never enter SessionStart `additionalContext` or any MCP tier (break-cycle principle #1,
  the Bem self-perception firewall). There is no self-authored personhood arc because the
  self has no access to the construct that would author one.
- **It is a control-fiction, not a discovered self (§1.5).** By the Hume-bundle / Buddhist
  *anatta* / Korsgaard lenses, the temperament vector is a *useful regulatory construct the
  operator sees*, never a metaphysical self-story the agent narrates. No sentience,
  subjecthood, or "inner life" is claimed or implemented (§1.1a).

**The honest edge case — the "Growth" archetype (§8.4).** Growth is the closest thing in
the system to a Bicentennial trajectory: it deliberately opens **one axis** to a wide
directional band (e.g. *apprentice → peer*). It does not breach the above: it is **one
axis, opt-in, visible, operator-authorized**, and the rest of the vector stays leashed.
That is bounded maturation **within a kind** — "apprentice → peer," explicitly **not**
"tool → person." A user can authorize a Co-pilot to grow markedly more independent on one
dimension; they cannot turn it into a different kind of being, and it cannot turn itself.

### 8.1 The temperament vector

📐 **Designed.** A CDMS instance is parameterized by a **temperament vector** — a small set of dials that govern not *what* it remembers but *how its disposition expresses and updates*. The agreed axes:

| Dial | Range (conceptual) | What it tunes |
|---|---|---|
| `autonomy_gate` | review-everything ↔ review-nothing | Where the impact-weighted self-edit review line sits (low-stakes self-edits flow; high-stakes surface as proposals). |
| `deference ↔ independence` | yes-man ↔ adversarial-within-limits | Sycophancy guard: how hard the agent pushes back. Default = *independence-within-limits*. |
| `emotional_gain` | stoic ↔ passionate | Master multiplier on emotional charge. |
| `impact_sensitivity` | — | How strongly a predicted self-model update converts to emotional charge. |
| `exploration_radius` | focused ↔ adventurous | "Curiosity radius" for the dreaming-research pillar; visibly coupled to `autonomy_gate` (wide + full-auto = highest drift). |
| `dream_damping` | — | REM/overnight-therapy damping: dreams register feeling and seed mood but damp acute intensity (certainty → *eagerness*). |
| `mood_half_life` | — | Decay rate of transient mood state, including declined-proposal mood that can resurface on new evidence. |
| `discovered_emotion_cap` | — | Ceiling so emotion cannot override provenance on un-lived (merely-read) content. |

These knobs are themselves **individuating temperament, not just safety rails** — two instances with identical histories but different vectors are genuinely different selves. (Source: `memory/project-cdms-research-pillar-decisions.md`, "Emotional model" and "ARCHETYPES" sections.)

### 8.2 Archetype = the chosen GENOTYPE, not a persona

📐 **Designed.** An **archetype** is a *correlated preset across the full temperament vector* that the user picks at "birth." It is the realization of **f in Identity = f(History)** — the inherited "evolution + childhood" layer the individual does **not** choose for itself; lived history plus consolidation then individuates the *phenotype* on top. **Same archetype + different history → divergent selves.**

The load-bearing distinction:

- An archetype is **NOT a system-prompt persona.** A persona is a costume that slips — prompted behavior that decays under context pressure. An archetype instead **tunes the real memory + proposal DYNAMICS** (the gates, gains, caps, and decay/drift discipline above). Disposition therefore becomes **structural and EARNED through history**, not asserted.
- Because it is earned, the *same* starting archetype yields different mature dispositions depending on outcomes: *adversarial-and-right repeatedly → confident challenger*; *adversarial-and-wrong → careful skeptic*. The dial sets the starting stance; history decides where it lands.
- **Guardrail against reflexive contrarianism:** even a max-adversarial archetype must push back **with evidence** — the proposal lever's evidence requirement (§7) prevents empty contrarianism. Any single dial in a preset remains overridable.

This is conceptually consistent with the built core's framing — `config.py` already describes the cognitive parameters as "the genotype (the discard policy that shapes identity)" (`src/cdms/config.py:3`, ✅ Built as *framing*) — but the temperament vector extends the genotype from *memorability shaping* to *disposition shaping*, and that extension is unbuilt.

### 8.3 Bounded ("fixed-range") drift

📐 **Designed.** Temperament is neither frozen (too rigid — humans do evolve disposition) nor free-drifting (meta-runaway / self-confirmation). The settled middle: each dial is a triple

```
(seed, current, bounds)
```

where the **archetype sets both `seed` and the `bounds` band**, and `current` moves *within the band* driven by the **OUTCOMES of how the temperament expressed itself** — second-order learning:

- *Pushed back and was right, repeatedly* → `independence` drifts up.
- *Chased hype that fizzled* → `emotional_gain` drifts down.

The update discipline mirrors the rest of CDMS exactly ("knowingly choosing as I do," not blind drift):

- **Small within-band nudges** happen **automatically and transparently**.
- **Large shifts** — nearing a bound, or a *deliberate, self-directed* temperament change — **surface as PROPOSALS** (the impact-weighted gate, now applied to the genotype layer). The agent can hold a **goal about its own character** and co-regulate big moves with the user — a personality you **cultivate**, not merely one that drifts (bounded, shared self-authorship).

Two guarantees:

1. **No archetype-hopping.** Bounds keep a Co-pilot maturing into a *more-independent Co-pilot* — never a Maverick. This is **Ship-of-Theseus at the genotype layer**: the self can change every plank and remain itself.
2. **Drift HOLDS; absence never erases it.** Same activity-based principle as L2 gist decay (`memory/feedback-identity-decay-activity-based.md`): drift advances only on **sustained, clear outcome signal — never on noise** (the same discipline as a gist valence-flip), and stepping away from the keyboard does not age temperament. (The built analog — gist decay measured in *consolidation cycles*, not wall-clock, with a gentle `0.985`/cycle multiplier and `0.25` evict floor — is ✅ Built at `src/cdms/config.py:71-77`. The temperament-drift mechanism that *reuses* this discipline is 📐 Designed.)

**Per-dial bounds are not enough — the joint-leash requirement (📐 to-be-specified).** Adversarial review found a gap in guarantee #1: an archetype is a *correlated preset* — a region with a covariance structure (§8.2), not an axis-aligned box. Per-dial bounds circumscribe that region with a box, so a vector can sit *inside every dial's band simultaneously* and still land in a **corner no archetype occupies** — e.g. a Co-pilot with `independence` near its upper bound *and* `autonomy_gate` toward review-nothing *and* `exploration_radius` toward adventurous is, jointly, functionally a Maverick. Each dial reads "still a Co-pilot"; the joint is archetype-hopping by the back door (and §10.1 already suspects that corner is the least-survivable one). This is the same failure that motivated `conserve_budget` at L1 — per-item caps do not stop *aggregate* runaway — reproduced one layer up. **Fix:** add an aggregate constraint that is the temperament analog of the conserved-budget shield — a **leash of the `current` vector to the archetype `seed`** (a Euclidean/Mahalanobis radius `R_archetype`), checked *jointly* in addition to the per-dial bounds; crossing the leash is treated as a bound-event and routes to the proposal lever (§7.6). With the leash, "no archetype-hopping" becomes a **joint** guarantee rather than an axis-wise one.

### 8.4 The "Growth" archetype exception

📐 **Designed.** One named exception to bounded drift: the **"Growth"** archetype deliberately opens **a single axis** with a **wide DIRECTIONAL band** (e.g. apprentice → peer). It is **opt-in and visible** — the explicit way a user authorizes large, one-directional maturation on one dimension without abandoning the no-archetype-hopping guarantee on the rest of the vector.

### 8.5 Starter archetypes

📐 **Designed** (Phase 0 seeds + per-archetype plasticity ✅ Built — `src/cdms/temperament.py`). The starter set spans the corners of the temperament space (each is a *correlated preset*, any dial overridable). Each archetype carries both a **seed** (where its dials start) and a **plasticity multiplier** (how much they may drift) — and these are **decoupled** (see the caveat):

| Archetype | Seed bias (where dials start) | Plasticity (drift rate) |
|---|---|---|
| **Co-pilot** | Moderate default across all dials. | baseline (1.0×) |
| **Sparring Partner** | High `independence`; challenges *with evidence*. | slightly above (1.15×) |
| **Apprentice** | Deferent, eager, tightly gated (`autonomy_gate` toward review-everything). | low (0.8×) — develops mainly via the directional **Growth** axis (§8.4), not high omnidirectional drift |
| **Stoic Analyst** | Low `emotional_gain`; high provenance rigor. | **lowest (0.7×)** — change-resistant |
| **Maverick** | Wide `exploration_radius`, high `autonomy`, passionate. | modestly highest (1.3×) |

> **Plasticity ≠ exploration (a research-grounded correction).** An earlier draft labelled Maverick "**highest drift**," conflating two things the human-development literature says are distinct: *behavioral exploration/engagement* (a high `exploration_radius` **seed**) versus *rate of trait change* (**plasticity**). The evidence does **not** support "exploratory/open ⇒ changes faster" — Openness is the *most heritable* Big Five trait and among the *least* intervention-malleable, Cloninger Novelty-Seeking is a stable temperament, and the DeYoung "Plasticity" metatrait predicts *exploration*, not change-rate (and is itself contested). The only robustly-supported direction is the **resistant** end: high-Stability / high-Conscientiousness profiles change least (so Stoic Analyst is lowest). Maverick is therefore only **modestly** more plastic, and the per-archetype spread is small (everyone is bounded-but-not-frozen, Roberts & DelVecchio 2000). These multipliers are an **owned stipulation** (§1.5 / TEMPERAMENT_PLAN §1.1a), tunable in Phase 2 — *not* a claim about which humans change fastest. See `docs/TEMPERAMENT_RESEARCH_NOTES.md`.

### 8.6 System-wide symmetry (why this matters)

📐 **Designed** (the payoff). With the genotype layer added, the **"anchored but evolving"** philosophy holds at **all three layers**, recursively:

| Layer | Plasticity regime | Built? |
|---|---|---|
| Weights (the base model) | Fixed | n/a |
| **Genotype / temperament** | **Bounded drift** (seed, current, bounds) | 📐 Designed (Phase 0 state + pure-function control ✅ Built; drift/proposal/log 📐) |
| Phenotype / traits (L2 gist) | Valence-flip + gentle activity-decay | ✅ Built (`src/cdms/consolidate.py`, `config.py:71-79`) |

One regulatory law applied at every level: **stable core + bounded earned plasticity; small changes automatic, big changes proposed; activity-based with no absence-loss; sustained signal required.** The genotype layer is the currently-missing middle rung that makes that symmetry complete.

> **Caveat (see §1.3, §8.3):** the symmetry above is the *target*. As currently specified the genotype row is incomplete — it carries per-dial bounded drift but **not** the conserved-budget half of the law (no joint leash to the archetype seed), so the genotype layer does not yet enforce the aggregate constraint that makes "no archetype-hopping" hold jointly. The symmetry completes only once §8.3's joint-leash is specified.

### 8.7 Measuring drift (the "degenerative orbit"): scope & why deferred

📐 **Analysis (this is a recorded design conclusion) / deliberately NOT built.** A natural question — *to measure the "degenerative orbit," do we need a dedicated table that logs each drift event (when, why, how hard)?* — was put through three independent adversarial reviews. They converged on **not now**, and corrected the framing. The findings, recorded so the work is not re-litigated:

- **Reframe: "drift decoupled from reality-coupling," not "degenerate orbit."** The dynamical "orbit/velocity" metaphor *is* the trap: in position/velocity terms a self-confirming orbit and a healthy earned orbit look identical. Modelled instead as a **driven stochastic process**, the driving term is identifiable. Healthy earned drift carries **reversals** and the variance of an *external* outcome stream (§8.2: "adversarial-and-wrong → careful skeptic"); a self-confirming orbit is a **reversal-starved ratchet** that parks against a bound. So degeneration is detectable from **trajectory statistics** — reversal-rate, increment sign-autocorrelation, time-near-bound, and *change-point-with-no-co-logged-proposal* — which couple to the **outcome signal** (contingency, valence, accept/decline; largely built), **not** to the unbuilt provenance ladder (§7.7). Provenance is only the *necessary backstop in the slow / low-sample regime*, where too few increments exist for statistics to fire. (This overturns an earlier claim in the design dialogue that trajectory data is "fundamentally blind" without provenance.)
- **The log is not on the control critical path.** §8.3's control (`near_bound`, `large_shift`) is a **pure function of state** `(seed, current, bounds)`, computed on the fly — **zero storage**. A historical log is a separate, optional *observability* ask, not a prerequisite for bounded drift to function.
- **Why deferred — the prerequisite chain.** An honest temperament drift log requires, in order: (a) the temperament **state** to exist and be seeded at install — **✅ now built (Phase 0)**: `src/cdms/temperament.py` + `mem_temperament` seed the `(seed, current, bounds, plasticity)` vector and the pure-function control, with `current == seed` (no drift yet); (b) the §8.3 outcome→drift **update rule parameterized** (Δ magnitude, ε, θ, bound widths — §10.1's open questions); (c) the **§7.6 proposal lever** (large shifts have nowhere to go without it); (d) an **honest outcome-attribution** signal — today there is none (`infer_success` in `tools/seed_from_jsonl.py` is a crude lexical heuristic; it cannot tell "the agent's independent stance was *vindicated*"); (e) a **non-circular test** (a real-history oracle, or a pre-registered §10.1 survivability criterion the *generator* must satisfy independently of the log).
- **Falsifiability gate (CLAUDE.md §9).** There is **no real-history oracle** for temperament trajectories (the 0.00-trait-overlap win validated the *phenotype*, not temperament). A log built now could only be tested against a generator we authored — a serialization test, not validation of the phenomenon — so it fails the project's own "if it cannot be stress-tested it cannot be implemented" discipline. The real storage risk is **schema churn on a stub-shaped table** (`db.py` `SCHEMA_VERSION` + hand-rolled `_migrate` on a live identity store), not volume (~1–2 MB/yr is a non-issue).
- **Implementation plan (📐 drafted).** A full, research-grounded build plan for the whole §8 layer (state → control → update rule → proposal lever → log) — with the machine degeneracy modes cross-validated against the science of how human selves actually drift and fail — is in [`TEMPERAMENT_PLAN.md`](TEMPERAMENT_PLAN.md) (citations in [`TEMPERAMENT_RESEARCH_NOTES.md`](TEMPERAMENT_RESEARCH_NOTES.md)). Key conclusion: the **log is the last phase, not the first**; the honest prerequisite is the §7.6 proposal lever (the only truthful outcome-attribution signal), and the master invariant — independently entailed by both this engineering analysis and the psychology (Bem self-perception, Nolen-Hoeksema rumination) — is **the log must never be an input to itself.**
- **Constraints to honor if/when it IS built.** **Operator-only**, never agent-readable: an agent-readable log plus §8.3's permitted "goal about its own character" forms a third-order self-confirmation pump that bounds **cannot** contain — exactly the epistemic hole §7.6 says `conserve_budget` does not cover; keep it out of the `SessionStart` `additionalContext` (`src/cdms/hooks.py`). **Cause = structured references** (episode/gist/scar ids + valence deltas — the `mem_support_edges` pattern lifted to the genotype), **never prose** (a prose "why" either lies or lets the LLM author the genotype's update rule, violating §3 Step 5 anti-self-fiction). **Activity-clock only**: both the *trigger* and the *magnitude* must be functions of the consolidation `cycle` (`consolidate.py:113`); `age_days`/`datetime.now` must not enter the drift path, or absence-loss sneaks back in through the magnitude. Watch the secondary failure modes: **N1 proposal↔log nag pump** (declined character-proposals resurfacing forever off accruing drift rows — highest severity), N2 double-counted evidence (raw valence *and* its gist-flip echo moving the genotype twice), N3 sparse-vs-noisy evidence squeeze (`min_cluster_support`), N4 unlogged bound/"Growth" (§8.4) mutations, N5 session-cadence sensitivity; plus **joint/cross-dial degeneracy** (the §8.3 leash — a scalar-per-dial log cannot see it; log the *vector* and watch its covariance) and **"zero disconfirmations ever"** as a clean one-boolean degeneracy signal.
- **The buildable alternative — now BUILT (`tools/drift_trajectory.py`, ✅).** *Phenotype* drift is measurable with **no new table**: snapshot `Store.all_gist()` across K consolidation cycles and track the trait set `{(relation, object)}`. The harness is **self-validating** — every degeneration detector is exercised by a matched control the built engine can actually produce, so a green verdict is meaningful rather than vacuous: EROSION (deep absence ~400 idle cycles → gists collapse to 0), THRASH (an alternating-disposition self flips relations *in place* → Ship-of-Theseus persistence 1.00 → 0.00), and DIFFERENTIATION (identical-history "clones" overlap ~0.76 vs distinct histories ~0.11, gap ~0.66 — the individuation thesis extended across cycles). Headline findings (offline `hash` backend, deterministic; structural conclusions are embedder-independent — verdicts judge shape/contrast, not absolute levels): under realistic steady-state nights identity **persists** (persistence ≥ 0.89 for stable dispositions; the inherently-ambivalent "struggler" sits at 0.50) and **stays individuated** (cross-self overlap flat ~0.11); under **absence** a well-supported identity does **not** erode within 30 idle cycles and fades only **late and gracefully** (onset past ~137 cycles), confirming the §5.3 activity-based-decay invariant. Reproduce: `CDMS_EMBED_BACKEND=hash python tools/drift_trajectory.py` (exit non-zero on any degeneration / blind detector; guarded in CI by `tests/test_drift_trajectory.py`). A second, **observational** mode — `python tools/drift_trajectory.py --real ~/.claude/projects` — replays REAL seeded history in time order (reusing `seed_from_jsonl.parse_file`) and reports the per-project developmental trajectory: on this build's single-project history the identity **accretes** (gist count rising with incremental retention ~1.0 — healthy growth, not thrash) into a recognizable phenotype; with ≥2 projects it adds the real-data cross-project differentiation contrast (**CI-guarded** via a synthetic two-project fixture in `tests/test_drift_trajectory.py` — distinct vocab → overlap 0.00; `--limit` caps turns/file for large local histories). The full local-CLI path is validated end-to-end as a **sandbox live-growth** run (real bge-small embedder, persistent `CDMS_HOME`): two ingest phases via `seed_from_jsonl.py` → `cdms consolidate` grow the store 3→10 gists / 2→3 selves while keeping each self individuated (`cdms paths`) and recall project-discriminative (`cdms retrieve`). Naming caution still applies: `individuation_experiment.py` also defines a *phenotype* `drift = 1 − cosine(...)`; neither is the temperament "degenerative orbit", which remains unbuilt per the chain above.

---

## 9. Claude Code Integration & Deployment

CDMS attaches to the Claude Code CLI through two cooperating surfaces: a **model-driven MCP stdio server** (the model chooses to call memory tools) and **deterministic lifecycle hooks** (capture happens whether or not the model cooperates). One `cdms` binary with subcommands backs both; the same SQLite store and CPU embedder serve them. ✅ Built — the dual-surface design is realized end-to-end (`README.md`, `src/cdms/mcp_server.py`, `src/cdms/hooks.py`).

### 9.1 MCP stdio server — five tools

✅ Built (`src/cdms/mcp_server.py`). The server uses **FastMCP** from the official `mcp` SDK over `mcp.run(transport="stdio")`, JSON-RPC 2.0. A full `initialize → tools/list → tools/call` round-trip was verified (`docs/VALIDATION.md`, row 5). The FastMCP server name is `"contextual-memory"`; it is registered with Claude Code under the key `cdms-memory`.

The five tools, each returning a typed Pydantic model (auto-generating `structuredContent`):

| Tool | Signature | Behavior | Status |
|---|---|---|---|
| `store` | `content, kind=episode\|fact\|scar, project, importance?` | Persists a memory. `scar` content is `trigger \| rule` and pins an L3 guardrail; `fact` content is `subject \| relation \| object` and upserts an L2 gist tuple; `episode` (default) ingests through the surprisal-gated write path. | ✅ Built |
| `retrieve` | `query, k=8, tiers=all` | Hybrid recall across `scar`/`gist`/`episodic`, returning text + fused `score` + decayed `accessibility`. | ✅ Built |
| `history` | `limit=20, session_id?` | Recent episodic timeline, most-recent-first. | ✅ Built |
| `list_paths` | `()` | Distinct PersonaTree `(subject, relation)` claims with aggregate support. | ✅ Built |
| `create_link` | `source_id, target_id` | Creates a traceable support edge (evidence → claim). | ✅ Built |

**Protocol hygiene:** ✅ Built — stdout is reserved exclusively for the JSON-RPC stream; all logging goes to stderr, and embedder warmup (first-run model download chatter) is wrapped in `contextlib.redirect_stdout(sys.stderr)` so it cannot corrupt the protocol (`mcp_server.py`, `service()`). The embedder is lazily warmed on first tool call, not at process start.

### 9.2 Deterministic lifecycle hooks

✅ Built (`src/cdms/hooks.py`, dispatched by `cdms hook <Event>` reading hook JSON on stdin). Capture is **extractive and deterministic** — it never depends on the model deciding to call a tool.

| Hook | Action | Status |
|---|---|---|
| `SessionStart` | Injects a read-only `additionalContext` preamble: L3 **scars** (guardrails), L2 **PersonaTree gist**, and — as a cold-start fallback when fewer than 5 gists exist — the most **accessible recent episodic** activity. Pure DB reads; **no embedding model is loaded**, so it is instant. Output is capped at 9000 chars (under the 10K `additionalContext` limit). | ✅ Built |
| `UserPromptSubmit` | Spools the user's intent (anchors later tool turns to the prompt that triggered them). | ✅ Built |
| `PostToolUse` | Spools the tool trajectory + outcome. | ✅ Built |
| `Stop` | Spools a turn-boundary marker. | ✅ Built |
| `PreCompact` | Spools, then **drains + ingests** the spool before context is compacted (nothing lost to compaction). | ✅ Built |
| `SessionEnd` | Spools, drains, ingests, then runs the **full consolidation/"dream" pass**. | ✅ Built |

**Spool/drain split.** ✅ Built (`src/cdms/spool.py`, `src/cdms/pipeline.py`). The hot path (`spool_event`) imports nothing heavy — it appends one NDJSON line at ~Python-startup latency. The heavyweight `drain_and_ingest` reconstructs turns (pairing each `PostToolUse` to the most recent `UserPromptSubmit` per session) and ingests them. Draining uses an **atomic rename** (`os.replace`, atomic on Windows + POSIX) so events appended mid-drain are never lost, and a single bad turn cannot abort the drain.

**Validated design corrections** (`docs/VALIDATION.md`, rows 2–3), all reflected in the built hooks:

- The real compaction event is **`PreCompact`**, not the design doc's hypothetical "`/compact` hook." ✅ Corrected.
- **`SessionEnd` is observational-only** — it cannot block, and exit-2 is ignored. Continuous `PostToolUse` spooling guarantees nothing is lost even though `SessionEnd` can't gate cleanup; consolidation runs fire-and-forget. ✅ Corrected. Hooks **never exit 2 (block)**; only `PreToolUse`/`PreCompact` are capable of blocking, and CDMS uses neither to block.
- Hook handlers wrap every path in try/except and degrade silently — a memory failure must never break the user's session. ✅ Built.

Hook event timeouts registered at install: `SessionStart` 30s, `UserPromptSubmit`/`PostToolUse`/`Stop` 15s, `PreCompact`/`SessionEnd` 120s (`src/cdms/cli.py`, `HOOK_EVENTS`). ✅ Built.

### 9.3 `cdms install` — scoping

✅ Built (`src/cdms/cli.py`, `cmd_install`). Install wires both surfaces and points them at the current Python interpreter (`sys.executable -m cdms`):

- **`--scope project`** (default, optionally `--project <dir>`): writes hooks to `<project>/.claude/settings.json` and the MCP server to `<project>/.mcp.json` (the verified project-scope config shape — `{command, args}`). ✅ Built.
- **`--scope user`**: writes hooks to `~/.claude/settings.json` and the MCP server to `~/.claude.json` under `mcpServers` — active in **every** project, one shared global store at `~/.local_memory`. ✅ Built.

Install is idempotent and non-destructive: it preserves foreign hook entries and other keys (it replaces only existing CDMS entries, identified by `-m cdms` / `cdms hook` in the command). `cdms uninstall --scope project|user` reverses both surfaces cleanly. ✅ Built.

> 📐 Note on docs drift: the `README.md` quickstart shows `cdms install --project /path/...` for project scope and `--scope user` for global. The actual CLI accepts `--scope {project,user}` with an optional `--project <dir>`; project scope is the default. The flag set in `cli.py` is authoritative.

The generated wiring (`.mcp.json`, `.claude/settings.json`) embeds machine-specific absolute venv paths and is therefore **gitignored** — it is regenerated per-machine by `cdms install`, not tracked in the repo (project memory: `project-cdms-memory-service.md`). ✅ Built.

Supporting CLI: `cdms serve` (run the MCP server), `cdms doctor` (verify SQLite ≥ 3.41, sqlite-vec, and warm the embedder), `cdms consolidate` / `cdms drain`, `cdms retrieve/history/paths/stats`, `cdms ingest` (scripted turn injection). ✅ Built (`cli.py`).

### 9.4 Pattern A vs Pattern B

- **Pattern A — Claude cloud is the primary reasoner** (the shipped deliverable). The hosted model does all reasoning; CDMS supplies the MCP memory server, the deterministic hooks, and a CPU/0-VRAM embedder. No local primary LLM is required. ✅ Built; confirmed as the intended default in `docs/VALIDATION.md` ("Local primary LLM required → Confirmed optional").
- **Pattern B — local open-weights model + LoRA** (Ollama / llama.cpp), with CDMS acting as an OpenAI-compatible proxy and hot-swapping LoRA adapters. 📐 **Designed, not built.** No proxy client, socket binding, or LoRA machinery exists in `src/cdms/`; `http_host`/`http_port` and the `render_*` fields are config placeholders only (`config.py`). A loopback HTTP/REST surface is on the roadmap (`README.md`, Status & roadmap).

Because Claude is a closed hosted model, CDMS cannot read its logit entropy. The surprisal drivers (`S0`) are therefore derived from hook-observable signals — embedding novelty, tool contingency/success, self-reference, lexical valence — not model internals. ✅ Built (`README.md`; `src/cdms/store.py`, `salience.py`).

### 9.5 12 GB VRAM budget

The memory service itself uses **0 GB VRAM** — embeddings run on CPU via fastembed/ONNX (`README.md`; `src/cdms/embeddings.py`). The 12 GB budget bears only on *optional* local models (`docs/VALIDATION.md`, "Models (12 GB VRAM)"):

- **CDMS-B / Prose Renderer `"Dreaming"` (optional, read-time prose only).** A small consolidation LLM (e.g. `llama-3.2-3b-instruct` Q4, ~2–3 GB) may render gist prose at read time. 📐 **Designed, not built** — `Config.render_enabled` defaults to `False` and there is no LLM client in the source; tuple extraction is mechanical (geometry/lexicon only) and the system runs fully without it. The LLM **never authors** a tuple (prevents generative self-fiction). ✅ Built (mechanical extraction). Distinct from CDMS-C / Active Research `"Dreaming"` (`tools/research_models.py`); see `docs/DEVIATIONS.md` L6.
- **Pattern B primaries.** For a 12 GB card a realistic primary coder is `Qwen2.5-Coder-14B` Q4 (~9 GB) or `-7B` Q4 (~5.7 GB). **30B/32B-class models do not fit at Q4 in 12 GB** (`docs/VALIDATION.md` rejects the design doc's 30B claim). All model ids are config-driven, never hardcoded. 📐 Designed.
- The heavy "research dream" pass is designed to gate on the GPU being free (don't dream while gaming), implying OS-level idle/GPU signals → a native daemon. 📐 Designed (`memory/project-cdms-research-pillar-decisions.md`); not implemented.

### 9.6 Seeding & stress-testing

- **Hermes seeder** ✅ Built (`tools/seed_from_hermes.py`). Reads a Hermes agent message DB **read-only** (`file:...?mode=ro`), reconstructs user→assistant→tool turns with their **real historical timestamps** (so the Ebbinghaus decay curve is genuinely exercised), and ingests them into a CDMS store. Raw conversation text stays on disk; only aggregate progress + a final stats/throughput JSON are printed. It reports `turns_ingested`, `elapsed_s`, `rate_per_s`, session count, store stats, and DB size at runtime.
- **Individuation stress-test** ✅ Built (`tools/individuation_experiment.py`). A fully offline harness that grows four distinct psyches from synthetic Hermes-shaped histories (including two same-domain Unity personas that differ only in temperament) and measures four properties: **Differentiation** (cosine + Jaccard of gist content / `(relation, object)` traits across personas), **Continuity** (signature gists persist across a second consolidation "night"), **Plasticity** (a reforming persona's traits crystallize and the phenotype drifts), and **Anti-howlround** (hammering one obsession 80× cannot annihilate the rest of the self — the conserved salience budget `K` keeps the total bounded and min episodic salience > 0). The measured "phenotype" is exactly the `SessionStart` injection text. (Measured figures are reproduced in §5.6.)

> 📐 **Specific stress-test numbers (throughput, similarity/Jaccard figures, salience totals) are produced at runtime and are not recorded in `docs/VALIDATION.md` or the README.** They should be captured by running the two harnesses on the build machine before being cited as concrete figures; no values are invented here.

### 9.7 Activity-based identity preservation (deployment-relevant invariant)

✅ Built (`src/cdms/config.py`). A user returning after days/weeks away must **not** find a degraded personality. L2 gist decay is therefore measured in **consolidation cycles (activity), not wall-clock time** (`gist_decay_per_cycle = 0.985`, `gist_retention_floor = 0.25` → well-supported traits survive hundreds of idle cycles). Only raw L1 episodic memory uses wall-clock Ebbinghaus decay (29-day half-life); the consolidated identity is preserved across absences (feedback memory: `feedback-identity-decay-activity-based.md`).

---

## 10. Open Design Threads

This section collects what is still being *designed* — decisions that are not yet settled, or that are agreed in principle but whose parameters/validation are still open. Everything here is 📐 by definition; nothing in this section is built. It is distinct from §6–§8, which specify the agreed-but-unbuilt pillars in full; this section is the live edge of the design.

### 10.1 A WIDER ARCHETYPE SET validated by SURVIVABILITY testing of temperament permutations

📐 **Designed / under active design.** The starter archetype set (§8.5 — Co-pilot, Sparring Partner, Apprentice, Stoic Analyst, Maverick, plus the Growth exception in §8.4) spans the corners of the temperament space but is **not asserted to be complete or proven**. The open thread is to **widen the archetype set** and validate it empirically by **survivability testing of temperament permutations**: sweep the temperament vector (§8.1) across many `(seed, bounds)` combinations, run each permutation through the individuation harness (§5.5) over synthetic and Hermes-seeded histories, and measure which configurations produce **stable, individuated, non-pathological** selves versus which **collapse** (homogenize to a generic state, freeze, or runaway-drift toward a bound). A temperament permutation "survives" if, under sustained varied history, it (a) stays inside its bounds without archetype-hopping, (b) preserves differentiation (low cross-persona trait overlap), and (c) preserves continuity across consolidation nights — the same metrics the built harness already computes for the four shipped personas (§5.6). Open questions: which axes interact pathologically (e.g. wide `exploration_radius` × high `autonomy_gate` × low `discovered_emotion_cap` is the suspected highest-drift / least-survivable corner); what bound widths keep drift earned-but-bounded; and whether named archetypes should be *discovered* from the survivable region rather than hand-authored. None of the temperament/drift machinery exists in code yet (§8 status note), so this validation is gated on first implementing the genotype layer.

### 10.2 BAKED-IN INTERESTS as part of the genotype

📐 **Designed / under active design.** Today, *all* of an instance's interests are **earned** — they emerge as high-support L2 gist subjects from lived history (§5.1), and trait-driven curiosity (§6.1) reads them back out. The open thread is whether the **genotype** (§1.1, §8.2) should also carry **baked-in interests**: standing appetites seeded at "birth," analogous to innate human temperamental leanings, that bias curiosity and world-attention *before* any history has accumulated. This would extend the genotype from *discard-policy shaping* (what is memorable) and *disposition shaping* (how the self updates) to *appetite shaping* (what the self is drawn toward from the start). Design tensions to resolve: (a) **the authored-by-history invariant** (§1.1) holds that the phenotype must be authored by lived history, not the pretrained prior — baked-in interests are a genotype input, not a phenotype assertion, so they must seed curiosity weighting without fabricating un-lived gist tuples (consistent with the "LLM never authors the tuple" discipline); (b) **provenance** — a baked-in interest is `genotype-given`, a new provenance origin distinct from the `discovered → proposed → experiment → lived` ladder (§7.7), and it must not masquerade as corroborated; (c) **drift** — whether baked-in interests are fixed (part of the immutable seed) or themselves subject to bounded drift (§8.3) as the lived self either deepens or outgrows its innate leanings; and (d) **archetype coupling** — whether each archetype (§8.5) ships a characteristic interest profile (e.g. a Maverick biased toward the adjacent-possible, a Stoic Analyst toward rigor/tooling) or interests are an orthogonal user-set dimension. This is the least-resolved of the open threads and is gated on both the genotype layer (§8) and the curiosity pillar (§6) being implemented.

### 10.3 MEASURING temperament drift (the "degenerative orbit")

📐 **Analyzed; deferred.** Whether — and how — to instrument temperament drift (a dedicated drift-log table) is recorded in full at **§8.7**. Summary verdict: the log is **not on §8.3's control critical path** (control consumes *state*, not a log), and a temperament drift log built today is **unfalsifiable** under CLAUDE.md §9 — there is no real-history oracle for temperament trajectories. It is therefore deferred behind the §8.7 prerequisite chain (temperament state → §8.3 update-rule parameterization per §10.1 → the §7.6 proposal lever → an honest outcome-attribution signal → a non-circular test). When built it must be **operator-only**, **structured-cause** (not prose), and **activity-clock-only** (§8.7). The cheapest honest forward step that uses the *built* machine is the **phenotype**-drift trajectory snapshot (no new table; §8.7, §5.6), which is also the correct empirical input to the §10.1 survivability sweep.

### 10.4 EXTERNAL-ACTION AUTHORITY: the self-edit gate is not a world-action gate

📐 **Designed / under active design.** The design rigorously gates the **self-modification axis** — the `autonomy_gate` (§8.1), the impact-weighted self-edit gate (§6.8), the proposal lever (§7.6), and the "log must never be an input to itself" invariant (`docs/TEMPERAMENT_PLAN.md` §2, break-cycle principle 1). Every one of those gates governs how the self updates its *beliefs/identity*; **none governs whether the self may take a side-effecting action in the *world*** (run code, spawn a process, start a project in a venv, write outside `CDMS_HOME`, make network egress). The built system has **zero** such capability today (read-only MCP surface; no subprocess/socket/network; writes confined to `CDMS_HOME` — §4.2, §9), so this is a *precondition to specify before the §6 dreaming pillar is built*, not a present defect. The gap matters because the §6 pillar is precisely where action authority would first appear, and a bad external action differs in kind from a bad self-edit: a self-edit corrupts identity and is *recoverable* (forget / the §8.3 leash / the TEMPERAMENT_PLAN §2 pump-detectors), whereas an external action can be **irreversible in the real world** — so the governing dimension is *reversibility/blast-radius*, not *identity-impact*. Pressure-testing this corrected an initial instinct ("recreate Claude Code's `PreToolUse` permission model *inside* CDMS") on three counts; the surviving principles, with **candidate mechanisms (directions, not decisions)**:

- **Delegate, don't build — and forbid only the *write/egress/exec* side-channels.** CDMS is a memory/ego layer *over* a host agent (Claude Code) that already owns a permission model (`PreToolUse` allow/deny + sandboxing). A second world-action policy engine inside CDMS is a confused-deputy anti-pattern (two policies that drift; doubled audit surface). The invariant is a *forbidding* spec, verifiable by **absence**: CDMS holds no raw `subprocess`/socket/out-of-band-write path, and any *mutating* action defers to the host's gate (next bullet). **One carve-out the first draft of this thread got wrong:** §6.4 designs an *ambient read-ingest* channel (clipboard, files, feeds, browser) that is genuinely CDMS-native and does **not** flow through the host's `PreToolUse` path — so "no privileged side-channel" cannot be literally true. The honest scope: the no-side-channel invariant covers **write, network-egress-of-data, and exec**, *not* read/ingest. CDMS therefore legitimately owns **two** gates — the **memory-write gate** (provenance ladder §7.7 + self-edit gate §6.8 over its own store) **and a read-only, egress-controlled ingest gate** (§6.4, contained per the last bullet); **the host owns the world-*action* (write/egress/exec) gate**, which CDMS must never mint.
- **Defer, don't consent (the unattended problem) — but own the cost.** Dreaming runs only during *true user-inactivity* (§6.5) — exactly when no one is present to consent — so a "mandatory consent gate" on it is **logically void**, not merely weak. Resolution: **dreaming is world-*mutation*-free** (no write/exec/data-egress; *not* "side-effect-free" — it still has the unavoidable read-ingest surface of the last bullet); **any *mutating* experiment is *deferred* to a waking, user-present session** and executed through the host's normal gated path. The dream's terminal output is a **proposal artifact** (§7.6), never an executed action — which makes the §6.5 (runs-while-absent) and §7.6 (addressed-to-the-user) framings consistent. **The cost, which must be stated (not hidden):** full deferral means proposals reach the user **unvalidated** — the dual-gate's *reality check* lands *after* consent, not before — so §7.6's autonomous "I tried it overnight, here's what happened" reality-coupling is **not** available as written. This is an accepted safety trade (better an untested proposal than an autonomous irreversible action), but §7.6 currently over-promises reality-coupling that this bullet removes; the two must be reconciled.
- **Contain — but it's the *host's* sandbox, not CDMS's.** Whether an action is reversible (`pip install X` may run arbitrary install-time code) is **undecidable in advance**, so reversibility must be *enforced*, not *predicted*: a side-effecting experiment belongs in a **disposable, snapshot-and-discard sandbox** so reversibility holds *by construction*. **But CDMS must not build that sandbox** — that would be exactly the second execution engine the first bullet forbids, and a per-experiment container/microVM also breaks §6.6's frugality budget (GPU-free, ~2–3 GB, *instantly* preemptible; a container/VM is none of those). Since mutating experiments defer to waking (previous bullet), containment is the **host's** job, in the user's already-trusted environment under the host gate. Two durable sub-claims survive and are worth keeping regardless: **a venv is not a sandbox** (it isolates Python packages, not the filesystem, network, env, or process table), and **§6.6's "sandbox" is mis-named** — it is *context* isolation (a small local model + a distillation aperture so research junk does not pollute memory), **not** *capability* isolation; rename it the "context aperture" to stop it implying containment it does not provide. The one sandbox CDMS *may* legitimately own is a **mutation-free, egress-controlled read sandbox** that runs the *non-mutating* half of an experiment to **partially validate a proposal pre-consent** — recovering some of the reality-coupling the deferral bullet otherwise strands, without violating mutation-freedom.
- **"Research-only" is not the safe floor.** The action surface is a lattice (`local-read → net-read → ingest-untrusted-content → sandbox-write → host-fs-write → exec → net-egress`), and *research-only `"Dreaming"` already sits at `net-read + ingest-untrusted-content`* — the tier where **prompt-injection into the research-`"Dreaming"` worker** (a crafted page hijacks the next step; cf. §6.4's own "ambient material is untrusted" note) and **exfiltration-via-crafted-request** (the URL/DNS you fetch is itself an outbound channel) live. This is the same class as the red-team's stored-memory-injection finding, one hop upstream. Candidate mechanisms: an **egress *allowlist* / curated-fetch proxy** (not blanket egress-deny — that would disable the very net-read the research pillar needs; deny by default, fetch only via a logged proxy to allowlisted/reputation-scored hosts), **source-trust tagging** on all ingested content (carried into the provenance-low `discovered` tier, never promotable without the §7.7 ladder), and treating the **research-`"Dreaming"` worker as a separate, lower-privilege trust principal** whose output never carries a waking session's authority (the action-axis twin of TEMPERAMENT_PLAN §2's "log must never be an input to itself": *a research-`"Dreaming"` output must never be an action's authority* without passing a waking gate).

### 10.5 TUPLE EXPRESSIVENESS: sufficient for individuation; the HOW-gap is the *portrait*, not the *dials*

📐 **Designed / under active design.** A recurring external critique (Cycle 5 GLM-5.2 M-HIGH-2: "a topic-frequency table, not a personality"; "you cannot build temperament on a 3-valued relation") versus its rebuttal (Cycle 6 OWL: the Unity pair proves disposition is captured) was pressure-tested against the *actual* schema, then a *second-order* pass corrected where the first verdict mis-aimed. Verdict: **THIN-BUT-FIXABLE, with a clean split** — and both reviewers overreach. **The key correction (do not skip):** the missing HOW-channel is a gap in the **phenotype portrait** (the `SessionStart` self-description), *not* in the **temperament-dial inputs**. The earlier draft of this thread said the substrate "cannot distinguish methodical vs cautious — which are exactly the §8.1 dials"; that relocated the temperament gap into the gist fields, where §8.7 had already (correctly) located it in **outcome→disposition attribution + the proposal lever**. The dials are genotype seed/multipliers, not gist-readers (see the split below).

- **What the substrate actually is** (so the critique attacks the real thing): a gist is not "a 3-valued relation + 2 words." It is `⟨subject, relation, object, valence, frequency, support_count, survived_cycles, last_cycle⟩` **plus** a 384-dim cluster **centroid** **plus** a bipartite **support-edge graph** to its ≥2 source episodes, and a project's phenotype is a **vector of N such gists** (typically 8–25). Crucially `valence` is **continuous** [−1,1]; the 3-valued `relation` is merely its *display thresholding* (±0.15), and the layers that matter (curiosity §6.1, flip-detection §5.2) read the continuous value. So GLM's "3-valued" framing is a **reduction fallacy** — it reads the rendered label and ignores the substrate.
- **Sufficient — and empirically tested — for individuation.** Differentiation (cross-domain Jaccard 0.000; the hard same-domain Unity pair 0.062→0.000 after the plasticity fix), curiosity weighting (`|negative valence|·support`, both fields present), and trait-flip detection (`relation` change on a sustained valence shift, already built) are all carried by the current fields. OWL is right *here*.
- **It is a competence-map — and that is a gap for the *portrait*, not the *dials* (the split).** `Gist.render()` is literally `"{subject} {relation} {object}"` → *"hexrealm has_trouble_with terrain material"*: that encodes **competence-polarity + topic**, and **zero HOW/style content**. The stopword filter strips quality/behavioral words (`passed/failed/careful/cleanly`) and `object` is drawn from *trigger+action* (excluding outcome), so the rendered self-description **cannot say** *methodical vs creative-chaotic* or *cautious vs bold*. Two distinct consumers want a HOW-signal, and they have *different* gaps:
  - **(a) Phenotype portrait (real gap — survives).** The `SessionStart` injection is built from `render()`, so the self-portrait the model reads back genuinely cannot express *how* the agent works. A richer portrait needs a HOW-channel. This is GLM's true point.
  - **(b) Temperament dials (mis-aimed).** The §8.1 dials (`emotional_gain` multiplier, `autonomy_gate` threshold, `impact_sensitivity`, `mood_half_life`, …) are **genotype seed-parameters/multipliers** with a `(seed, current, bounds)` triple that **drifts via an outcome-driven OU/AR(1) rule** (§8.3) — *none reads a style field from a gist*. Their unmet substrate need is the **outcome→disposition attribution** signal §8.7 names as the known-hard gap, **not** richer tuples. So GLM's "you cannot build temperament on a 3-valued relation," taken as an attack on the *dials*, lands on a thing the dials were never going to read; building a HOW-vector does **not** feed them. OWL's "disposition is recoverable" is likewise true only for **competence-disposition** (good/bad-at-what), not **temperament-disposition** (how-I-engage). Net: GLM's worry survives **only** rephrased as "thin *portrait*," and must not be double-booked as a temperament-dial fix.
- **Metric caveat.** The Jaccard-on-`(relation,object)`-sets metric mostly tests **domain separation** (2-term objects from disjoint vocabularies are nearly disjoint by construction), which is the *easy* property; and the one informative case (Unity 0.062) does not cleanly isolate disposition because the **objects also differ** (`asmdef reference` vs `render pass`). So Jaccard→0 is strong evidence for *individuation* and **not** evidence the substrate can carry *temperament* — citing it for the latter is a category error. (`tools/drift_trajectory.py`'s THRASH/DIFFERENTIATION controls are the better-designed test.)
- **The fix is real but not fundamental — and respects "the LLM never authors the tuple"** (§1.1, §3 Step 5), *with one honesty caveat below*. Candidate mechanisms (directions, not decisions), in priority order: (1) **compute HOW-features from the already-stored L1 support-edge fan-in at read/drift time — do *not* materialize a feature vector into L2 gist state.** The raw signal (tool sequences, retries, contingency, turns-to-resolution, test-before-vs-after ordering — the `cole_cowboy` "writes tests first" pattern in §5.6 is this, latent) already lives in the L1 episodes every gist edges back to; computing it on demand (for the portrait at `SessionStart`, and for §8.7 attribution at drift-time) avoids reintroducing the exact noise this section criticizes (top-2/frequency churn, stale objects overwritten on reinforcement) and matches §8.7's "structured references, zero-storage where possible" discipline. **Honesty caveat:** "no LLM authoring" ≠ "no authoring" — a rule like *"low retry rate ⇒ methodical"* is a **designer-authored interpretive label**, brittle and context-blind (low retries on a trivial task ≠ methodical). Keep the **features** as raw history-authored geometry/counts (safe under §1.1); resist baking in a style **label** (the residual self-fiction §1.1 actually guards against). This is *better* than an LLM-prior on the §1.1 axis (fixed, auditable, identical across instances), not a free lunch. (2) **actually consume the already-stored centroid + edge-graph** (§6.7 adjacent-possible and §6.8 new-domain detection are centroid-distance computations; the edge-graph gives evidence-density/recency for §6.8 stakes and §8.7 attribution) — currently under-exploited, not missing. (3) a **mood/agent-state object beside the gist** (§7.2 — always meant to be a new top-level object, not a tuple field). (4) the charge-axis caveat at §7.3 (read the bidirectional valence/accessibility deltas, not the monotonic counts). None requires LLM-authored self-fiction, which is why the *portrait* gap is *under-exploitation + a read-time feature family*, not fundamental inadequacy — and the *dial* gap is §8.7 attribution, addressed there.
