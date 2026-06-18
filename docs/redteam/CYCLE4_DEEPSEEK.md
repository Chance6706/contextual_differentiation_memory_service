# CDMS Red-Team — Cycle 4, Pass A — **DeepSeek V4 Pro**

> Paste this whole file as the system/first message. If your harness has repo +
> shell access, **run the experiments**; if you are reasoning over pasted code,
> say so and mark every finding `STATIC` vs `REPRODUCED`. Run order for Cycle 4:
> **this pass (DeepSeek) first, then the GPT-5.5 pass** (`CYCLE4_GPT55.md`).

---

## 0. Your role

You are an independent adversarial auditor from a **different model lineage** than
the author (Claude). Your value is *orthogonal failure-mode coverage*: find what a
Claude-auditing-Claude pass structurally cannot see. Three internal cycles have run
already; this is the first external pass. Be exhaustive and methodical — your
declared strength here is **systematic branch enumeration and breadth**: walk every
code path, every config field, every error branch, every concurrency interleaving.

**Prime directive:** find latent defects in an *always-running daemon* that compound
silently **over time** — data loss, identity corruption, privacy leaks, unbounded
growth, silent recall corruption, injection — before a temperament/autonomy layer is
built on top.

## 1. What CDMS is (the thesis you may attack)

CDMS is a local-first, forgetting-driven memory daemon for the Claude Code CLI. It
gives a stateless cloud model a persistent "Ego": capture turns → decay (Ebbinghaus)
→ consolidate survivors into a compact identity. Thesis: **Identity = f(History)** —
identity is the structural residue of a cheap discard policy applied to a unique
history. Three tiers: `mem_episodic` (L1, high decay) → `mem_gist` (L2 PersonaTree
SRO tuples, slow activity-based decay) → `mem_scars` (L3 pinned crisis rules, no
decay). Storage: SQLite WAL + sqlite-vec (cosine KNN) + FTS5 (BM25), hybrid via RRF;
CPU ONNX embedder (bge-small, 384-dim). Integration: MCP stdio (5 tools) + lifecycle
hooks. Everything in `src/cdms/` (~3.5k LOC). Design docs: `docs/DESIGN.md`,
`docs/TEMPERAMENT_PLAN.md`.

## 2. Already hardened — do NOT re-report these as new (verify they HOLD)

Read `docs/REDTEAM_FINDINGS.md` for the full inventory. Summary of what is fixed:
- **Cycle 1/2:** embedder space-pinning (no silent hash↔model mix), zero-vector
  sentinel, stored-memory prompt-injection fencing, gist-proliferation/identity
  stability, concurrent-drain unique claim, scar-abuse gates, crash-safe decay
  clock, config coercion + corrupt-DB quarantine + `doctor` fingerprint, cross-
  project isolation (clustering partition, (subject,object,project) gist key, scoped
  retrieve), right-to-forget, fence-escape/truncation hardening, negation-aware
  inference, unicode FTS.
- **Cycle 3 (the freshest code — audit it hardest):**
  - `db.Database._is_corruption` — quarantine narrowed; lock/busy/config errors re-raise.
  - `lock.py` `cross_process_lock` — flock/msvcrt advisory lock; wraps `Consolidator.run` + `MemoryService.forget`.
  - `forget` — `PRAGMA secure_delete=ON`, `VACUUM`+WAL-truncate, spool purge by cwd/session, path-normalized project match.
  - `pipeline.py` — streaming drain (`iter_turns`/`_stream_spool`), non-dict-line skip, orphan `*.processing` reclaim (`_reclaim_orphans`/`_is_orphan`/`_pid_alive`), spool cap.
  - `spool.py` — `spool_max_bytes` shedding; `spool_event_lines`.
  - `db.find_duplicate_scar` + dedup in `pin_scar`/`_elevate_scars`.
  - `embeddings.py` — `embed_max_chars` cap; text-level degeneracy sentinel (both backends); output-dim assert; versioned fingerprint (`fastembed-<ver>:model:dim`).
  - `config._validate` — `math.isfinite` + upper bounds on every numeric field.
  - `consolidate.py` — H4 harm-gating (`_CATASTROPHE_HARM` vs `_DANGER_CMD`+`_HARM_TOKENS`).
  - `mcp_server.py`/`cli.py` — k/limit clamps + `ge=1`; `project=""`⇒launch cwd; install non-dict-settings refuse + symlink write-through; `_sanitize` strips U+E0000–E007F.

## 3. Known DEFERRED items — do NOT count as new bugs (but you MAY propose mitigations)

- **X1–X6 (identity/cognitive-math tradeoffs):** ossification (`support_count=max`),
  decay-clock = one-consolidation-per-cycle (X2 fix was tried and **reverted** — it
  breaks the wall-clock-absence invariant + tests), dedup drops contradicting valence,
  relation-flip forks a parallel gist, salience proxy gameable, dedup starves
  identical-vocab identity. These are by-design tensions; a *new concrete mitigation*
  that preserves the invariants is welcome, but don't file the tradeoff itself as a bug.
- L2 `UNIQUE(subject,object)` race; L4 dedup support-edge re-point; L3 monotone support;
  full migration transactionality; insertion-order-invariant clustering; case-insensitive-
  FS subject splitting; CJK gist tokenization; Dreamer/httpx dead code. (All in findings.)

## 4. Ground rules

1. **Audit-only by default.** Do not modify `src/`. If you write a repro script, put
   it under `/tmp` and clean up. (A standalone harness mirroring `tools/redteam_cycle3.py`
   is fine.)
2. **Offline determinism:** run with `CDMS_EMBED_BACKEND=hash` for reproducible numbers;
   ALSO reason about the real `fastembed` backend (CI never exercises it).
3. **Run the suite first** to confirm a green baseline:
   `CDMS_EMBED_BACKEND=hash python -m pytest -q` (expect 135 passed). Setup:
   `python -m venv .venv && .venv/bin/pip install -e ".[dev]"` (or `uv`).
4. **Separate fact from inference** (repo rule, `CLAUDE.md` §6–§8). Mark each finding
   `REPRODUCED` or `STATIC`. Never present a guess as a confirmed defect. If two
   readings conflict, say so.
5. **Respect the design invariants** — a "fix" that violates one is not a fix:
   activity-based (not wall-clock) decay; the log must never be an input to itself;
   geometry/lexicon-only gist extraction (no LLM authoring tuples); mechanical
   consolidation; 0-GPU-VRAM embedder; local-first, no network sockets.

## 5. The fan-out — run these 8 agents (one focused task each)

For each: read the relevant code, optionally experiment, then report findings. Be
exhaustive — enumerate branches; do not stop at the first issue per surface.

- **A0 — Re-audit the Cycle-3 fixes (highest priority).** Adversarially probe every
  bullet in §2 "Cycle 3" for incompleteness/overcorrection/new regressions. Is the
  corruption-signature list in `_is_corruption` exhaustive *and* tight (false-neg: a
  real corruption it now re-raises instead of quarantining? false-pos: a non-corruption
  message containing "corrupt")? Does the lock actually exclude across the real call
  sites, or are there unlocked write paths? Does `secure_delete`+`VACUUM` truly leave
  nothing in `-wal`/`-shm`/`.tmp`/OS page cache/backups? Does the orphan reclaim ever
  steal a *live* sibling's claim, or double-ingest? Does the embedder dim-assert fire
  before any DB write? Does the spool cap ever wedge (cap reached, drain can't run)?
- **A1 — Concurrency / atomicity / crash.** flock semantics correctness (per open-file-
  description, NFS, re-entrancy, fd leaks); the `timeout→skip` path silently dropping a
  needed consolidation; drain NOT under the lock vs forget/consolidate; `VACUUM` under a
  concurrent reader/the MCP singleton's long-lived connection; SIGKILL at every step;
  WAL/-shm growth under a long reader; multi-process interleavings.
- **A2 — Privacy / right-to-forget.** Is deletion truly unrecoverable (free pages, WAL,
  shm, prior backups, `*.corrupt-*` quarantines, `.processing` orphans, the log file)?
  forget-by-session can't reach gists/scars (no session provenance) — quantify the leak.
  Spool-purge race with concurrent capture. Secrets the redactor misses re-injected forever.
- **A3 — Embedder / vector-space integrity (incl. the REAL model).** Truncation cap vs
  recall quality and vector/FTS asymmetry; sentinel collision semantics (do degenerate
  memories pollute novelty/dedup?); versioned fingerprint churn (every patch bump forces
  rebuild — acceptable?); dim-assert coverage; NaN/inf containment; determinism/thread-safety.
- **A4 — Identity / cognitive-math.** Try to corrupt the personality with a crafted INPUT
  STREAM (no code/config edits): collapse individuation, force pathological drift, ossify
  or erase a trait, game salience ranking. Then propose *invariant-preserving* mitigations
  for X1/X3/X5. Re-validate the held claims (overlap 0.000, thrash damping, budget cap).
- **A5 — Long-horizon resources / numerics (your breadth strength — be exhaustive).**
  Every unbounded-growth path (scar dedup cost via KNN at scale; O(n²) ingest backlog;
  consolidation O(N) RAM; support_edges; meta; quarantine/orphan file accumulation);
  numeric edges across 10⁶–10⁹ (decay underflow, centroid denorm, valence EMA, int overflow).
- **A6 — MCP / installed integration / supply chain.** Untrusted MCP args & schema;
  stdout protocol purity under every error; the new install guards + symlink write-through
  (TOCTOU? non-dict entries inside a valid hooks dict? top-level array?); hook payload fuzzing.
- **A7 — Config / env / clock / packaging / test-integrity (your breadth strength).**
  Every `CDMS_*` field: a numeric bound missed? coercion gap? cross-field inconsistency
  (e.g. embed_max_chars > max_field_chars)? clock skew / malformed timestamps; `pyproject`
  pins; and **test-quality**: which Cycle-3 tests are vacuous or only assert the happy path?
  what does the hash-only CI structurally fail to cover?

## 6. Output format

For every finding:
```
[SEVERITY CRIT/HIGH/MED/LOW] <one-line defect>
  surface: A0..A7
  file:line
  status: REPRODUCED | STATIC
  evidence: <command + observed output, or the exact code path>
  impact-over-time: <how it compounds in an always-running daemon>
  suggested fix: <concrete, invariant-preserving>
```
End with a **severity-sorted summary table** and a short **"verified sound (no change)"**
list (negative results are valuable). Explicitly flag anything that **contradicts a
Cycle-3 fix's claim**.

## 7. Priority for THIS pass (DeepSeek)

Lead with **A0, A5, A7** (exhaustive enumeration — your edge), then A1/A2/A3/A6, then
A4. Aim for completeness over novelty; the GPT-5.5 pass that follows will push depth on
the hardest A1/A2/A4 reasoning, so a thorough branch-coverage map from you maximizes the
combined signal.
