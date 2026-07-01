# Design Validation & Corrections

Before implementing, the claims in
`docs/archive/[Gemini Canvas] Contextual Differentiation Memory Service.md` (moved
out of the repo root 2026-07-01) were validated with
live web research (official docs, model cards, PyPI, neuroscience literature) and
against the actual Claude Code CLI and Python/SQLite toolchain on the build
machine. This document records what was **confirmed**, **adjusted**, or
**rejected**, and how the implementation responds.

## Technical / integration

| # | Claim in design doc | Verdict | What we did |
|---|---|---|---|
| 1 | Embedding model `all-MiniLM-L6-v2` produces **768-dim** vectors | **Rejected** | MiniLM-L6-v2 is **384-dim**. We standardized on **384** and default to `BAAI/bge-small-en-v1.5` (fastembed default, ~50 MB, MTEB-competitive). `embed_dim` is a single config constant, so upgrading to a 768-dim model later (`bge-base`, `nomic-embed-text`) is a one-line change. |
| 2 | Claude Code "`/compact` hook" | **Adjusted** | The real event is **`PreCompact`**. We register `PreCompact` (+ `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop`, `SessionEnd`). |
| 3 | `SessionEnd` blocks cleanup until learnings are written | **Adjusted** | `SessionEnd` is **observational-only** (cannot block, exit-2 is ignored). Capture is instead continuous via `PostToolUse` spooling, so nothing is lost; `SessionEnd` triggers consolidation fire-and-forget. Only `PreToolUse`/`PreCompact` can block. |
| 4 | MCP config lives at `~/.claude-code/mcp-config.json` | **Rejected** | No such path. Claude Code uses `claude mcp add`, a project-root **`.mcp.json`**, or `~/.claude.json`. We write `.mcp.json` (project scope) with `{command, args}` — matching the verified shape of existing servers. |
| 5 | stdio MCP, JSON-RPC 2.0; Python servers OK | **Confirmed** | FastMCP from the official `mcp` SDK (pinned `>=1.28,<2`), `mcp.run(transport="stdio")`. Verified a full `initialize → tools/list → tools/call` round-trip. |
| 6 | sqlite-vec `vec0` + FTS5 hybrid search | **Confirmed (with fixes)** | KNN uses the portable `WHERE embedding MATCH ? AND k = ?` form; `distance_metric=cosine` is set at DDL time (not per query); pinned `sqlite-vec>=0.1.9` (DELETE fix). SQLite 3.50.4 on this machine (≥3.41 ✓). Hybrid = Reciprocal Rank Fusion of cosine KNN + BM25, fused in Python (robust across SQLite versions). |
| 7 | Daemon must be Rust/Go, not Python | **Acknowledged deviation** | Rust isn't installed here and building an `ort`+`sqlite-vec` toolchain in-session is slow/unverifiable. We built a working, tested Python service that honors the *spirit* of the directives (single CLI w/ subcommands, **0 VRAM** CPU embeddings, loopback-only/no sockets) and documented the Rust rewrite as production hardening. |

## Cognitive science

| Claim | Verdict | What we did |
|---|---|---|
| Ebbinghaus exponential decay `e^(−λt)`, 29-day half-life | **Confirmed** (29 days is an engineering hyperparameter, not a literature constant) | Kept exponential decay; made the half-life a tunable config value rather than a hardcoded constant. |
| Surprise/novelty/affect-gated encoding controls consolidation | **Confirmed** | Implemented as the `S0` gate; mechanistic analog is synaptic-tagging-and-capture. |
| Hippocampal → neocortical systems consolidation (CLS) | **Confirmed** | The L1 episodic → L2 gist "dreaming" pass is a faithful analog; replay is interleaved (re-presentation), not one-shot overwrite. |
| Retrieval bump as unbounded `α^c` | **Adjusted** | Unbounded geometric growth contradicts diminishing-returns data. Our `min(α^c, Cap)` **saturates** at `Cap = 2.0`, curbing runaway reinforcement. |
| "Conserved salience budget" (strict zero-sum) ≈ synaptic homeostasis | **Adjusted** | SHY is *proportional downscaling*, not a strict constant sum. Our renormalization scales all saliences by `K/Σs`, which **preserves rank/ratios** — i.e., it is proportional downscaling that also targets a budget. Framed accordingly. |
| Flashbulb memories are non-decaying singletons | **Rejected** (empirically they decay; only confidence/vividness stays high) | L3 scars are framed as an **explicit engineering "pin"** for crisis-remediation rules — a product affordance, not a neuroscience claim. Scar elevation additionally requires *negative* valence so positive preferences flow to gist instead. |

## Models (12 GB VRAM)

| Claim | Verdict | What we did |
|---|---|---|
| `Qwen3.5-9B`, `Qwen3.6-27B`, `Qwen3.6-35B-A3B`, `harrier-oss-v1-0.6b` | **Adjusted** | As of the build date (June 2026, past the assistant's training cutoff) the Qwen3.5/3.6 names are *real* but exact HF repo ids / `-Instruct` suffixes vary — so **model ids are config-driven, never hardcoded**. `harrier-oss-v1-0.6b` is an **embedding** model, not a chat LLM — never use it as the Prose Renderer (CDMS-B) or research worker (CDMS-C). |
| 30B/32B coder fits in 12 GB at Q4 | **Rejected** | It does not. For a 12 GB primary coder use `Qwen2.5-Coder-14B` Q4 (~9 GB) or `-7B` Q4 (~5.7 GB). |
| Local primary LLM required | **Confirmed optional** | For Claude Code (Pattern A) the cloud model reasons; the local primary LLM + LoRA hot-swapping belong only to Pattern B. The deliverable here is the MCP memory server + CPU embedder + the optional CDMS-B Prose Renderer `"Dreaming"`. |

## Net effect on the build

The core architecture (three tiers, decay law, surprisal gating, sleep
consolidation, MCP + hooks) survived validation intact. The corrections were:
**384-dim embeddings**, **`PreCompact`/observational `SessionEnd`**, **`.mcp.json`
config**, **saturating reinforcement**, **proportional (not strict zero-sum)
renormalization**, **scars as engineering pins gated on negative valence**, and
**config-driven model ids**. All are reflected in the code.
