# Contextual Differentiation Memory Service (CDMS)

> *An AI that grows a personality by forgetting.*

By default, most AI assistants start each conversation from a blank slate —
whatever happened last time is gone. CDMS is an experiment in the opposite
direction: it gives an AI a memory that **fades the way human memory does**, and
finds that what's left behind starts to look like a *personality*.

The idea in one sentence: **you are not the sum of everything that ever happened
to you — you are what's left after you forget most of it.** CDMS applies a cheap,
idiosyncratic "is this worth keeping?" rule to everything an AI does, lets the
rest decay, and consolidates the survivors during idle "sleep" passes into a
compact sense of self. Feed two copies of the system different histories and they
drift into genuinely different "selves." Forgetting isn't a flaw to engineer
away — it's the very thing that makes two instances *different*.

It runs **entirely on your own machine** (nothing leaves the computer) and uses
**zero GPU memory**, so it stays out of the way of anything else you're running.

**What we've actually observed so far:** seeded with ~10k real coding-session
turns drawn from three different projects, CDMS grew three distinct, *recognizable*
personalities — with **zero overlap** in their defining traits. Importantly, that
character comes from *what the system remembers*, not from a hidden temperament
someone installs into it — a boundary we've now tested fairly hard (see
[What we've found](#what-weve-found)).

A note on the vocabulary below: words like "Ego," "sleep," "dreaming," and "self"
are borrowed from cognitive science because they earn their keep as *design
intuition*. CDMS **differentiates — it does not animate.** It reproduces the useful
*behavior* of having a past; it makes no claim to consciousness, feelings, or an
inner life. The next section says exactly where that line is.

---

> **Identity = f(History)** — identity does not come from perfect recall. It is
> the structural residue left behind when a cheap, idiosyncratic *discard policy*
> (`f`, the genotype) is applied to a unique lived history. Two CDMS instances fed
> different histories diverge into different "selves." Forgetting is the feature.

### What CDMS claims — and what it does not

This is a claim about **differentiation** — *what makes this instance recognizably
this one, and not some other one* is the structural residue of a forgetting policy
over its lived history. It is **not** a claim about consciousness, sentience, or
subjective experience. CDMS **differentiates; it does not animate** — it produces a
*functional simulacrum* of continuity (the useful behavior of having a past), not an
inner life or a persisting subject. Reading the "identity"/"Ego" language as a claim
about a *mind* is an equivocation on the word "identity."

Two things follow, worth stating up front:

- **The system is entirely mechanical and reactive today.** It consolidates *what
  history did*, by geometry and lexicon only — the LLM never authors the identity
  tuple (no "generative self-fiction"). The step from *"what have I done"* to
  *"what can I become"* (self-direction) belongs to the curiosity/research
  **"active dreaming"** pillar, which is **designed, not built** (see
  [`docs/DESIGN.md`](docs/DESIGN.md) §6). The optional prose *Dreamer* does not
  cross that line — it is off by default and only renders prose. Even once built,
  dreaming is gated *propose-not-act*: functional agency at most, never experience.
- **"Substrate independence" means content, not a soul.** Across a model change the
  *content* of the self-model (gist/scar tuples and dials — all text) carries over;
  the *expression* changes with the new model. That is *not* "the same AI in a new
  body."

---

## Why forgetting?

An agent that retains every raw turn drowns in retrieval noise, memory
interference, and context-window bloat — the *cognitive curse of perfect recall*.
Human expertise comes from selective compression, not infinite logging. CDMS
implements that compression as three hierarchical tiers, modeled on the
complementary-learning-systems account of hippocampus → neocortex consolidation:

```
            HIERARCHICAL COGNITIVE MEMORY TIERING

  L1  mem_episodic   raw turn-by-turn logs          high decay   (hippocampal trace)
        │
        │  ── asynchronous "sleep" consolidation ──►
        ▼
  L2  mem_gist       PersonaTree relational tuples   slow decay  (cortical gist)
        │
  L3  mem_scars      pinned crisis-remediation rules   no decay  (engineering pin)
```

---

## Architecture

```
                         Claude Code CLI
        ┌───────────────────────┴───────────────────────┐
        │ lifecycle hooks (deterministic capture)        │ MCP stdio (model-driven)
        ▼                                                ▼
  SessionStart   PostToolUse   PreCompact/SessionEnd   store · retrieve · history
  (inject ctx)   (spool turn)  (drain + consolidate)   list_paths · create_link
        │              │              │                        │
        └──────────────┴──────┬───────┴────────────────────────┘
                              ▼
                    ┌──────────────────────┐
                    │   CDMS service        │  single `cdms` binary, subcommands
                    │  ┌────────────────┐   │
                    │  │ write path     │   │  surprisal-gated S0
                    │  │ read path      │   │  hybrid recall + accessibility
                    │  │ sleep/dream    │   │  evict · compete · renorm · gist
                    │  └────────────────┘   │
                    └──────────┬───────────┘
                               ▼
        SQLite (WAL) + sqlite-vec (cosine KNN) + FTS5 (BM25)   ·   CPU ONNX embedder
                       ~/.local_memory/memory.db                  (fastembed, 0 VRAM)
```

### The cognitive model

**Write-time salience (surprisal gating).** Every captured turn gets an initial
salience `S0`. Goal-relevance is a *multiplicative veto* — a loud but irrelevant
event is actively suppressed:

```
S0 = G_goal · (S_surprise + C_contingency + W_self-ref + A_affect)
```

Because Claude is a closed hosted model we cannot read its logit entropy, so the
drivers are derived from signals the hooks *can* observe: **surprise** ≈ embedding
novelty (cosine distance to the nearest existing memory); **contingency** ≈ did a
state-mutating tool run and did it succeed; **self-reference** ≈ does the turn
touch the agent's own rules/identity; **affect** ≈ lexical valence of the outcome.

**Decay-driven accessibility.** Memories are never hard-deleted on read; they
become progressively harder to reach (Ebbinghaus), with retrieval-induced
reinforcement (the testing effect), saturated by a cap so one hot memory can't
dominate attention:

```
A(m,t) = S0 · e^(−λt) · min(α^c, Cap)      λ ← 29-day half-life, α = 1.15, Cap = 2.0
```

**Sleep consolidation** (the "dreaming" pass), run at a rest boundary:

1. **Scar elevation** — high-salience *negative* crises are pinned to L3 verbatim.
   A genuine catastrophe is floored to the crisis threshold at capture (the
   *flashbulb floor*) so a real guardrail can't be quietly forgotten.
2. **Temporal eviction** — episodes with `A(m,t) < floor` are permanently dropped.
3. **Hierarchical competition** — session- then epoch-level softmax protects
   highlights from quiet periods against a single noisy debugging marathon.
4. **Conserved-budget renormalization** — all saliences are proportionally
   rescaled to a fixed budget `K`. This *zero-sum* law (SHY-style synaptic
   downscaling) makes runaway reinforcement — "neural howlround" — mathematically
   impossible: boosting one memory forces unrelated stale ones to fade faster.
5. **Mechanical tuple aggregation** — survivor clusters (pure vector geometry) are
   distilled into de-adjectived `⟨Subject, Relation, Object, Valence, Frequency,
   Support⟩` tuples with traceable support edges back to L1. The tuple is the
   authoritative truth; prose is rendered on-the-fly at read time. Extraction is
   **geometry/lexicon only** — the LLM never authors the tuple, which prevents
   *generative self-fiction* (summarizing toward pretrained personality clichés).

---

## What we've found

CDMS is a research project as much as a tool, so the central claims are measured,
not just asserted. The headline results to date (full method + caveats in
[`docs/`](docs)):

- **Differentiation is real and recognizable.** Seeding ~10k real Claude Code turns
  across **3 projects** produced three distinct per-project psyches with **trait
  overlap ≈ 0.00** (stable across all 6 consolidation windows; see
  [`docs/validation/cycle9_experiments/`](docs/validation/cycle9_experiments)) —
  they share none of their defining traits, and a domain query
  reliably surfaces the *right* project's self. That near-zero overlap is *meaningfully
  below chance*, not a vocabulary artifact: against a pooled-resampling null (each psyche
  drawing traits independently from the shared vocabulary) the observed overlap sits
  **~3 SD below** the chance baseline (`z = −3.33` on the offline run; see
  [`docs/validation/measurement_precision/`](docs/validation/measurement_precision)). The phenotype-drift harness
  (`tools/drift_trajectory.py`) confirms the §5.3 invariant: identity stays stable
  and distinct over time, and **absence never ages it** (decay is
  activity-based — a project you don't touch doesn't lose its personality).

- **The steering boundary: recall yes, disposition no.** A key question for a
  memory that shapes behavior: *what kind of influence is it?* Injected CDMS memory
  reliably steers a model via **recalled content and override** (it can pull a
  model off its prior using remembered rules and crisis guardrails) — a positive,
  moderate effect on every model of a 5-model / 3-family panel. But it does **not**
  install a latent **disposition**: two *opposite* temperaments fed to the same
  models produce **statistically indistinguishable** choices — across a 5-model panel
  the dex/uma 95% CIs overlap at n≈50 (see
  [`docs/validation/measurement_precision/`](docs/validation/measurement_precision)), so no
  disposition shift is *detectable*, not merely asserted equal. Disposition *appears* to
  live in the model's weights/activations, not in retrievable context — the line between
  **Side A** (memory) and **Side B** (disposition) below.
  *Caveat: in-context, 12–14B panel — recall-steering measured greedy at n=10 probes,
  disposition sampled at k=5 / n≈50; this measures in-context recall steering, not
  weight-level effects.*

- **A richer recalled phenotype steers more — and stays auditable.** The default
  now carries two enrichments (each gated): **gist exemplars** (a verbatim `e.g.`
  quote on the top-6 highest-support traits, restoring the disposition a model
  acts on without any generative imagination) and the **flashbulb floor** above.
  Turning these on raised behavioral adherence (panel-mean target−counter spread
  1.67 → **3.67**) and rule-citation **9×** (1/30 → 9/30), for a bounded +37–63%
  preamble cost — and the disposition boundary *still held*. The thin phenotype,
  not model robustness, was the bottleneck. _(These panel means are point estimates;
  the harnesses now emit Wilson 95% CIs per rate — `src/cdms/stats.py` — so a small-n
  read like "dex == uma" reads as "not detectable at this n", not a confirmed null. See
  [`docs/validation/measurement_precision/`](docs/validation/measurement_precision).)_

- **Voice shifts too — but it's persona-specific, not generic.** A data-framed
  memory (not an instruction) moves a model's *voice* ~58% as much as an explicit
  directive, and that movement is **specific to the persona's content** (+0.8
  register above a placebo persona), a result that survived de-circularized
  round-robin judging across four judges. Decision-steering remains the dominant,
  robust channel; the voice↔choice coupling is a soft tendency (+0.3), not a law.

---

## Claude Code integration

CDMS hooks into Claude Code two ways, which work together:

**1. Lifecycle hooks (deterministic, extractive capture).** Registered in
`.claude/settings.json`. Capture never depends on the model *choosing* to call a
tool:

| Hook | What CDMS does |
|---|---|
| `SessionStart` | Injects guardrails (scars) + PersonaTree gist (plus recent salient episodes as a cold-start fallback, until enough gists have formed) as read-only `additionalContext`. Pure DB reads — no model load, instant. |
| `UserPromptSubmit` | Spools the user's intent (anchors later tool turns). |
| `PostToolUse` | Spools the tool trajectory + outcome (~100 ms, no model). |
| `Stop` | Spools a turn boundary. |
| `PreCompact` | Drains the spool and ingests before context is compacted. |
| `SessionEnd` | Drains, ingests, and runs the full consolidation/dream pass. |

**2. MCP stdio server (model-driven recall & notes).** Five tools, JSON-RPC 2.0:
`store`, `retrieve`, `history`, `list_paths`, `create_link`. The model can
explicitly save a fact/scar or query memory mid-task.

### Quickstart

```bash
# 1. Install (uv recommended). From the repo root:
uv venv --python 3.11
uv pip install -e .

# 2. Verify the environment (checks SQLite >= 3.41, sqlite-vec, embedder)
cdms doctor

# 3. Wire CDMS into Claude Code (hooks + MCP server)
cdms install --project /path/to/your/project   # this repo only
cdms install --scope user                       # ALL repos (one shared global store)

# 4. Restart Claude Code in that project; approve the 'cdms-memory' MCP server.
#    Watch memory accumulate:
cdms stats
cdms retrieve "what do I know about the build system"
```

`cdms install` writes `.claude/settings.json` (hooks) and `.mcp.json` (the MCP
server entry) into the target project, pointing at the current Python
interpreter. `cdms uninstall --project ...` removes both cleanly.

### CLI reference

```
cdms serve              run the MCP stdio server (used by Claude Code)
cdms hook <Event>       handle a lifecycle hook (reads JSON on stdin)
cdms consolidate        drain the queue and run the sleep/dream pass
cdms drain              ingest spooled events without consolidating
cdms retrieve <q> [-k]  query memory from the terminal
cdms history [-n]       recent episodic timeline
cdms paths              show the PersonaTree (subject/relation) paths
cdms observe            read-only operator audit/observability UI (localhost)
cdms temperament        show the §8 disposition vector + leash (operator-only)
cdms stats              store statistics
cdms doctor             verify environment + warm the embedder
cdms install/uninstall  wire/unwire CDMS into a project's Claude Code config
cdms forget ...         delete stored memory by --project / --session / --id (right-to-forget)
cdms ingest ...         manually ingest a turn (scripting/testing)
```

### Configuration

All cognitive parameters live in `cdms/config.py` and are overridable via
`CDMS_*` environment variables or `$CDMS_HOME/config.json`. Highlights:

| Variable | Default | Meaning |
|---|---|---|
| `CDMS_HOME` | `~/.local_memory` | Data directory (DB, queue, logs). |
| `CDMS_EMBED_MODEL` | `BAAI/bge-small-en-v1.5` | CPU ONNX embedding model. |
| `CDMS_EMBED_DIM` | `384` | Vector dimension (must match the model). |
| `CDMS_DECAY_HALFLIFE_DAYS` | `29` | Forgetting-curve half-life. |
| `CDMS_RETENTION_FLOOR` | `0.10` | Accessibility below which episodes are evictable. |
| `CDMS_CRISIS_THRESHOLD` | `3.0` | S0 above which a *negative* event becomes a scar. |
| `CDMS_SALIENCE_BUDGET` | `1000` | Conserved global salience `K`. |
| `CDMS_PROJECT_BUDGET_CAP` | `0.5` | Max fraction of `K` any one project/subject may hold. |
| `CDMS_RECALL_EXEMPLARS` | `true` | Attach a verbatim `e.g.` quote to surfaced gists. |
| `CDMS_RECALL_EXEMPLAR_TOP_N` | `6` | How many top-support gists carry an exemplar (`0` = terse). |
| `CDMS_FLASHBULB_FLOOR_CATASTROPHES` | `true` | Floor a genuine catastrophe's S0 to the crisis gate. |
| `CDMS_ENFORCE_PROVENANCE` | `true` | Block untrusted-origin content from forming gists/scars. |
| `CDMS_EMBED_BACKEND` | _(unset)_ | Set to `hash` to force the offline deterministic embedder (tests/CI). |

---

## Hardware & the 12 GB VRAM budget

The memory service itself uses **0 GB VRAM** — embeddings run on CPU via ONNX
Runtime. The 12 GB budget only matters for *optional* local models:

* **Prose Dreamer (optional):** a small consolidation LLM that only *renders*
  nicer gist prose at read time, e.g. `llama-3.2-3b-instruct` Q4 (~2–3 GB) — not to
  be confused with the unbuilt "active dreaming" pillar in the roadmap. CDMS works
  fully without it (tuple extraction is mechanical by design).
* **Pattern B (not required for Claude Code):** if you instead drive a *local*
  open-weights model (Ollama / llama.cpp), CDMS can act as an OpenAI-compatible
  proxy. For a 12 GB card, a realistic primary coder is `Qwen2.5-Coder-14B` Q4
  (~9 GB) or `-7B` Q4 (~5.7 GB). **30B/32B-class models do *not* fit at Q4 in
  12 GB.** With Claude Code (Pattern A) the cloud model does all reasoning, so no
  local primary model is needed at all.

See [`docs/VALIDATION.md`](docs/VALIDATION.md) for the full research-backed
review of the original design doc, including corrections.

---

## Privacy, durability & hardening

CDMS is an always-running daemon, so it has been put through **nine adversarial
red-team cycles plus a re-run-audit follow-up** (one of which caught that an
external review had blessed a stale revision) — see
[`docs/REDTEAM_FINDINGS.md`](docs/REDTEAM_FINDINGS.md). Notable guarantees:

* **Right-to-forget.** `cdms forget --project/--session/--id` deletes across all
  three tiers, scrubs the not-yet-ingested spool (raw, pre-redaction tool output),
  and `VACUUM`s with `secure_delete` so deleted content is not recoverable from the
  db file. `cdms uninstall --purge` removes the whole store.
* **Secret redaction at capture** — high-signal credential shapes (AWS/GitHub/Slack/
  OpenAI keys, JWTs, `*_TOKEN=`/`*_SECRET=` assignments) are scrubbed before anything
  is persisted or re-injected at `SessionStart`.
* **Trust boundary + capture-time provenance.** Stored memory is partially
  untrusted; it is sanitized and fenced as `<memory:*>` DATA at injection, never as
  instructions. Each episode also carries an origin label (`trusted` /
  `untrusted` / `synthetic`); **untrusted-origin content can never form a gist
  trait, and only trusted-origin content can mint a scar guardrail** — so
  external/quoted text can never poison the persona's identity layer.
* **Crash/concurrency safe.** WAL + per-statement transactions, a cross-process lock
  serializing consolidation/forget, orphan-claim reclaim after a killed drain, a
  bounded spool, and a corrupt-DB quarantine that never fires on mere lock contention.
* **Embedder integrity.** The vector-space identity (backend + model + version + dim)
  is pinned on first write and refused on mismatch, so an embedder/weight change can
  never silently corrupt recall.
* **Operator-only observability.** `cdms observe` serves a read-only audit UI on
  localhost (provenance breakdown, scar origins, raw salience) that the model never
  sees; the §8 disposition vector is held behind the same operator-only "Bem
  firewall" and never enters the model's context.

---

## The three sides — A / B / C

CDMS is the first of three deliberately separated layers (settled as one monorepo
with namespaces, not three repos):

- **Side A — Memory / recall substrate (this repo).** Built, tested, and validated
  on real history. The working channel: capture → forget → consolidate → recall.
- **Side B — Disposition steering (the `cdms-steering` research line — today a set
  of experiment harnesses, e.g. `tools/steering_experiment.py`, not a shipped
  module).** The [steering-boundary work](#what-weve-found) lives here: it isolates
  the part of behavior that is *weight/activation-level temperament*, which Side A's
  recalled memory does **not** appear to install (at the scales tested). §8
  temperament Phase 0 (static disposition state) is the first piece that touches
  this from the A side.
- **Side C — Interface / agent layer (design direction).** The thin layer for
  driving local + cloud models together and conserving tokens/cost. Earliest stage.

---

## Status & roadmap

**What is built today is the reactive mechanical core** — capture, salience, decay,
the five-step sleep consolidation, hybrid retrieval, the enriched-phenotype recall
(exemplars + flashbulb floor, on by default), Layer-3 capture-time provenance, and
the privacy/durability hardening above — plus **§8 temperament Phase 0**: static
disposition state (8 dials, 5 archetypes), pure-function control, and the
operator-only joint leash (`current == seed`; no drift yet).

The remaining *proactive* layers are **designed, not built** (DESIGN.md marks every
line ✅ Built vs 📐 Designed):

- **§6 curiosity / "active dreaming"** — trait-driven novelty surfacing and
  epistemic-gap tracking; an optional idle-time exploration *Dreamer* whose safety
  substrate (synthetic provenance, recall/budget isolation, a dream-quality eval
  gate) is specified as a precondition in [`docs/research/DREAMER_MODELS.md`](docs/research/DREAMER_MODELS.md).
- **§7 emotion / proposals / provenance** and the **§8 temperament drift/proposal
  Phases 1+** — see [`docs/DESIGN.md`](docs/DESIGN.md) and
  [`docs/TEMPERAMENT_PLAN.md`](docs/TEMPERAMENT_PLAN.md).
- **Scale re-validation** — every load-bearing finding above was measured on a
  12–14B panel; [`docs/validation/SCALE_LADDER.md`](docs/validation/SCALE_LADDER.md)
  is the pre-registered design to retest them up a within-family size ladder
  (Qwen2.5 7B→72B) on larger hardware. Scaffolded, not yet run.

This is a working reference implementation (Python). Per the spec's
production-hardening directive, a future pass could rewrite the daemon in Rust/Go
for a single ~27 MB dependency-free binary and `<40 MB` RAM footprint; the
algorithms and schema port directly. AES-256-GCM at-rest encryption and a
loopback HTTP/REST surface are also on the roadmap. The current build binds no
network sockets (MCP is stdio; data is a local SQLite file).

---

## Development

```bash
uv pip install -e ".[dev]"
CDMS_EMBED_BACKEND=hash python -m pytest -q     # 336 tests; the core runs fully offline
```

The cognitive core (`salience.py`) is pure stdlib and fully unit-tested. Tests use
a deterministic hashing embedder so they run offline; a separate non-hash path
(`tests/test_real_embedder.py`) exercises the real model and skips cleanly when it
is unavailable.

## License

MIT
