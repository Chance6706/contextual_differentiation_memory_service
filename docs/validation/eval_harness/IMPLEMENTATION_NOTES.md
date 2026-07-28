# Eval-harness (ablation) — implementation notes

Companion to `EVAL_HARNESS_PREREG.md` v2 (ablation-first). Records the grounded config-seam audit so
the adapter build is faithful. Branch: `feat/eval-harness-ablation` off `origin/main` (post-#125, has
the hardened scrubber). **Salvaged from v1 (verified clean):** `tools/eval_harness/_fixtures.py` (1512
lines) + `fixtures/__init__.py`. Everything else (adapters/runner/scorer/judge/check_gates) is REBUILT.

## Ablation condition → config seam (audited 2026-07-16)

| condition | seam | status |
|---|---|---|
| **cdms-full** | defaults | ✓ |
| **cdms−fence** | `enforce_provenance=False` (config.py:187) | ✓ exists |
| **cdms−forgetting** | `retention_floor=0.0` (config.py:72) → nothing evictable | ✓ exists |
| **cdms−salience → random-discard** | NEW seam in `consolidate._evict` (see Gap 1) | ✗ MUST BUILD |
| **cdms−provenance-write** | subset of `enforce_provenance` (see Gap 2) | ⚠ not separable today |
| naive-dump / no-memory | harness-side adapters | ✓ no CDMS change |

## Gap 1 (BLOCKING for the sharp control) — random-discard needs a new discard-policy seam
`consolidate._evict` (consolidate.py:486) selects victims by `accessibility(salience, age, access) <
retention_floor` — purely salience-driven. The random-discard control must forget at the **same rate**
(same eviction COUNT per cycle) but pick victims **at random**. Required change:
- Add `discard_policy: str = "salience"` + `discard_random_seed: int` to `Config`.
- In `_evict`, when `discard_policy == "random"`: compute the count N the salience policy WOULD evict
  this cycle, then evict a **seeded-random N-subset** of the eligible episodes instead. Rate-matched by
  COUNT (the prereg's default; budget-matching is the alternative to resolve at lock).
- This touches identity-shaping code → it gets its **own rule-12 pass** before use, and it must be a
  pure no-op when `discard_policy == "salience"` (assert byte-identical eviction set in a test).
- Deterministic: the seed is pinned; do NOT use `Math.random()`/unseeded RNG.

## Gap 2 — fence read vs write not separable with the single `enforce_provenance` flag
`enforce_provenance` gates BOTH the read-side fence (store.retrieve/history/preamble) AND the write
gate (consolidate elevation + gist formation). So **cdms−fence** and **cdms−provenance-write** cannot
be isolated with today's config. Options (resolve at lock):
- (a) Collapse them into ONE `cdms−provenance` ablation (simplest; loses the read-vs-write decomposition).
- (b) Add granular flags (`enforce_provenance_read` / `enforce_provenance_write`) defaulting to the
  current combined behavior — a small, safe config split, its own tiny change.
Recommendation: (b) if the read-vs-write decomposition is wanted (it's the more informative result);
(a) if we want the first pass minimal.

## Build order (sprint plan, paced)
1. ✓ Branch + salvage fixtures + secret-scan + these notes. *(this sprint)*
2. `adapter.py`: `CdmsAdapter(condition=...)` applying the §2 toggles (fence/forgetting via config;
   random-discard via Gap 1 once built); `NaiveDump`/`NoMemory`. Adapter MUST pass `project=scope.project`
   into `retrieve` (v1's isolation bug). `reset()` isolation via `is_relative_to`.
3. Gap 1: the `discard_policy` seam in `consolidate._evict` + its rule-12 + no-op test.
4. `runner.py`: provenance-threaded ingest (honor per-turn fixture provenance), scope passed to query,
   errored conditions surfaced with axis/condition.
5. `scorer.py` + panel: effect-based gate adjudication via the OR panel (reuse the validated
   injection_panel rubric); `tokens_injected` = injected context; mechanical isolation/forget checks.
6. `analyze.py`: ablation-delta tables with bootstrap CIs (Δ = ablation − full).
7. `tests/`: gate-fires-on-known-fail, isolation negative test, secret-scan-of-source, determinism/hash.
8. Run + panel re-judge; results doc with the run-config header.

Each step is one paced sprint; the rule-12 review applies to my own work before merge (the v1 lesson:
confidently-green ≠ correct).
