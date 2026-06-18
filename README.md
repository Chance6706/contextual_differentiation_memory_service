# Contextual Differentiation Memory Service (CDMS)

A **local-first, forgetting-driven cognitive memory daemon** for the
[Claude Code](https://claude.com/claude-code) CLI.

CDMS gives an otherwise stateless cloud reasoning model a persistent, evolving
"Ego": it silently captures what happens across terminal sessions, lets those
memories **decay** along an Ebbinghaus forgetting curve, and **consolidates** the
survivors during idle "sleep" passes into a compact, structured identity. The
service runs entirely on the **CPU (0 GPU VRAM)** so your GPU stays free for
whatever else you run locally.

> **Identity = f(History)** — identity does not come from perfect recall. It is
> the structural residue left behind when a cheap, idiosyncratic *discard policy*
> (`f`, the genotype) is applied to a unique lived history. Two CDMS instances fed
> different histories diverge into different "selves." Forgetting is the feature.

### What CDMS claims — and what it does not

This is a claim about **individuation** — *what makes this instance recognizably this
one* is the structural residue of a forgetting policy over its lived history. It is
**not** a claim about consciousness, sentience, or subjective experience. CDMS
**individuates; it does not animate** — it produces a *functional simulacrum* of
continuity (the useful behavior of having a past), not an inner life or a persisting
subject. Reading the "identity"/"Ego" language as a claim about a *mind* is an
equivocation on the word "identity."

Two things follow, worth stating up front:

- **The system is entirely mechanical and reactive today.** It consolidates *what
  history did*, by geometry and lexicon only — the LLM never authors the identity tuple
  (no "generative self-fiction"). The step from *"what have I done"* to *"what can I
  become"* (self-direction) belongs to the curiosity/research **"active dreaming"**
  pillar, which is **designed, not built** (see [`docs/DESIGN.md`](docs/DESIGN.md) §6).
  The optional prose *Dreamer* does not cross that line — it is off by default and only
  renders prose. Even once built, dreaming is gated *propose-not-act*: functional agency
  at most, never experience.
- **"Substrate independence" means content, not a soul.** Across a model change the
  *content* of the self-model (gist/scar tuples and dials — all text) carries over; the
  *expression* changes with the new model. That is *not* "the same AI in a new body."

The cognitive vocabulary throughout — "Ego," "sleep," "dreaming," "individuation" — is
borrowed from cognitive science (complementary learning systems, the Ebbinghaus curve,
synaptic downscaling) because it earns its keep as design intuition, not because CDMS
literally instantiates those phenomena.

---

## Why forgetting?

An agent that retains every raw turn drowns in retrieval noise, memory
interference, and context-window bloat — the *cognitive curse of perfect recall*.
Human expertise comes from selective compression, not infinite logging. CDMS
implements that compression as three hierarchical tiers, modeled on the
complementary-learning-systems account of hippocampus → neocortex consolidation:

```
            HIERARCHICAL COGNITIVE MEMORY TIERING

  L1  mem_episodic   raw turn-by-turn logs        high decay   (hippocampal trace)
        │
        │  ── asynchronous "sleep" consolidation ──►
        ▼
  L2  mem_gist       PersonaTree relational tuples  slow decay  (cortical gist)
        │
  L3  mem_scars      pinned crisis-remediation rules  no decay  (engineering pin)
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

## Claude Code integration

CDMS hooks into Claude Code two ways, which work together:

**1. Lifecycle hooks (deterministic, extractive capture).** Registered in
`.claude/settings.json`. Capture never depends on the model *choosing* to call a
tool:

| Hook | What CDMS does |
|---|---|
| `SessionStart` | Injects guardrails (scars) + PersonaTree gist + recent salient activity as read-only `additionalContext`. Pure DB reads — no model load, instant. |
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
cdms stats              store statistics
cdms doctor             verify environment + warm the embedder
cdms install/uninstall  wire/unwire CDMS into a project's Claude Code config
cdms forget ...          delete stored memory by --project / --session / --id (right-to-forget)
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
| `CDMS_EMBED_BACKEND` | _(unset)_ | Set to `hash` to force the offline deterministic embedder (tests/CI). |

---

## Hardware & the 12 GB VRAM budget

The memory service itself uses **0 GB VRAM** — embeddings run on CPU via ONNX
Runtime. The 12 GB budget only matters for *optional* local models:

* **Dreamer (optional):** a small consolidation LLM for nicer gist prose, e.g.
  `llama-3.2-3b-instruct` Q4 (~2–3 GB). CDMS works fully without it (tuple
  extraction is mechanical by design).
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

CDMS is an always-running daemon, so it has been put through **three adversarial
red-team cycles** before the temperament layer is built — see
[`docs/REDTEAM_FINDINGS.md`](docs/REDTEAM_FINDINGS.md). Notable guarantees:

* **Right-to-forget.** `cdms forget --project/--session/--id` deletes across all
  three tiers, scrubs the not-yet-ingested spool (raw, pre-redaction tool output),
  and `VACUUM`s with `secure_delete` so deleted content is not recoverable from the
  db file. `cdms uninstall --purge` removes the whole store.
* **Secret redaction at capture** — high-signal credential shapes (AWS/GitHub/Slack/
  OpenAI keys, JWTs, `*_TOKEN=`/`*_SECRET=` assignments) are scrubbed before anything
  is persisted or re-injected at `SessionStart`.
* **Trust boundary.** Stored memory is partially untrusted; it is sanitized and
  fenced as `<memory:*>` DATA at injection, never as instructions.
* **Crash/concurrency safe.** WAL + per-statement transactions, a cross-process lock
  serializing consolidation/forget, orphan-claim reclaim after a killed drain, a
  bounded spool, and a corrupt-DB quarantine that never fires on mere lock contention.
* **Embedder integrity.** The vector-space identity (backend + model + version + dim)
  is pinned on first write and refused on mismatch, so an embedder/weight change can
  never silently corrupt recall.

---

## Development

```bash
uv pip install -e ".[dev]"
CDMS_EMBED_BACKEND=hash python -m pytest -q     # 135 tests, offline, no downloads
```

The cognitive core (`salience.py`) is pure stdlib and fully unit-tested. Tests use
a deterministic hashing embedder so they run offline; a separate non-hash path
(`tests/test_real_embedder.py`) exercises the real model and skips cleanly when it
is unavailable.

## Status & roadmap

**What is built today is the reactive mechanical core** — capture, salience, decay, the
five-step sleep consolidation, hybrid retrieval, and the privacy/durability hardening
above. The *proactive* layers — §6 curiosity/dreaming-research ("active dreaming"), §7
emotion/proposals, and §8 archetypes/temperament (see
[`docs/DESIGN.md`](docs/DESIGN.md)) — are **designed, not built**; DESIGN.md marks every
line ✅ Built vs 📐 Designed.

This is a working reference implementation (Python). Per the spec's
production-hardening directive, a future pass could rewrite the daemon in Rust/Go
for a single ~27 MB dependency-free binary and `<40 MB` RAM footprint; the
algorithms and schema port directly. AES-256-GCM at-rest encryption and a
loopback HTTP/REST surface are also on the roadmap. The current build binds no
network sockets (MCP is stdio; data is a local SQLite file).

## License

MIT
