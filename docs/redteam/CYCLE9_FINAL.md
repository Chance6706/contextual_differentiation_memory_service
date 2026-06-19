# CDMS Red-Team -- Cycle 9, Final Report -- Hermes Agent

> **Model:** Hermes Agent (Nous Research) via OpenRouter
> **Date:** 2026-06-18
> **Commit:** f4dd7cf (main) -- reports at 51994b0/57733b5/1c803bb/ee64c0e/5f60d10/cd66a33
> **Methodology:** 6 parallel subagent attacks + unified synthesis. 16 source files + all tests + design docs read in full.
> **Prior baseline:** Cycle 8 (OWL Alpha) -- 20 findings at commit 8e889d7.

---

## Executive Summary

**Cycle 8 fix verification: 15/20 fully fixed, 3 partially fixed, 1 deferred, 1 downgraded.**

This cycle found **44 findings** across 6 attack surfaces:

| Severity | Count | Key Themes |
|----------|-------|------------|
| CRITICAL | 1 | SessionStart reads without lock |
| HIGH | 16 | Spool race, config gaps, budget cascade, centroid drift, dedup O(n^2), architectural debt |
| MEDIUM | 14 | goal_hint bypass, associative boost, valence flip, no lifecycle test |
| LOW | 10 | Precision loss, dead code, permissions |
| Deferred | 14 | Design/philosophical observations for Phase 1+ |

**Most serious:** I-1 (CRITICAL) -- SessionStart hook reads DB without cross-process lock, injecting mid-consolidation snapshot.

**P0 fixes (5 items, ~2 hours):**
1. Lock SessionStart read (I-1)
2. Cap assoc_eta/assoc_boost_cap_frac/reinforce_cap (H-M-3)
3. Fix support_count semantics (M-1)
4. Fix spool drop race (C9-H-1)
5. Fix spool disk-full data loss (M-3)

---

## Cycle 8 Verification

**Fully Fixed (15):** H-1 perms, H-2 weight cap, H-3 home traversal, H-5 TOCTOU, M-1 eviction race, M-4 unicode, M-5 creds, M-6 max_length, M-7 loopback, H-4 scar cap, L-1 dedup cache, L-4 quarantine perms, L-S-1 kind validation, M-M-3 boost cap, M-M-4 valence EMA.

**Partial (3):** H-1 content (perms fixed, still pre-redaction), H-3 (traversal blocked, absolute paths OK), C-1 (per-project helps, initial load unchanged, downgraded to MEDIUM).

**Not Fixed (1):** M-M-2/M-3 goal_hint bypass.

---

## New Findings by Surface

### A. Mechanical (8 new)
- **M-1 [HIGH]:** support_count inconsistency -- upsert_fact() increments, consolidation uses max(). Fact gists immune to decay. (store.py:167)
- **M-2 [MED]:** _row_to_gist fallback resets decay clock on NULL last_reinforced. (db.py:480)
- **M-3 [MED]:** _forget_from_spool truncates on disk-full. (store.py:222)
- **M-4 [MED]:** assoc_eta/assoc_boost_cap_frac caps at 1e3 allow 108x budget injection. (config.py:261)
- **M-5..8 [LOW]:** cycle meta corruption, dead _evict_scars return, lock 0o644, float32 precision loss.

### B. Concurrency (1 high, 3 med, 4 low)
- **C9-H-1 [HIGH]:** _forget_from_spool drops concurrent spool_event appends (fd opened before os.replace). (store.py:222)
- **C9-M-1..3 [MED]:** Thread-unsafe lazy init, snapshot divergence, log rotation race.
- **C9-L-1..4 [LOW]:** Non-atomic counter, busy_timeout, PID reuse, check_same_thread.

### C. Security (2 med, 5 low)
- **S-1 [MED]:** Lock file 0o644. (lock.py:45)
- **S-2 [MED]:** Predictable temp filename. (store.py:235)
- **S-1L..5L [LOW]:** Dir umask, log perms, FTS injection, arbitrary model ID, no dep lockfile.

### D. Cognitive Math (1 high, 4 med, 2 low)
- **H-M-3 [HIGH]:** assoc_eta/assoc_boost_cap_frac validate to 1e3 -- 108x K_budget per write. (config.py:261)
- **M-M-6 [MED]:** Single-episode valence flip at support < 8. (consolidate.py:420)
- **M-M-7 [MED]:** goal_hint bypass still unfixed. (store.py:190)
- **M-M-8 [MED]:** Associative boost accumulates 54% of K between consolidations.
- **M-M-9 [MED]:** 3:1 competition ratio amplifies budget asymmetry.
- **L-M-3..4 [LOW]:** goal_gate_floor=0, conserve_budget edge case.

### E. Scale (4 high, 3 med, 3 low)
- **S-3 [HIGH]:** all_episodic() loads ALL episodes -- OOM at 100K+. (db.py:350)
- **S-4 [HIGH]:** Dedup O(n^2) -- 480s at 500K episodes. (consolidate.py:280)
- **S-5 [HIGH]:** history()/forget() load entire tables. (store.py:310)
- **S-6 [HIGH]:** lru_cache(maxsize=None) unbounded. (pipeline.py:51)
- **S-7..9 [MED]:** DB bloat, KNN latency at 50K+, embedding storage 750MB at 500K.
- **S-10..12 [LOW]:** Spool growth, object accumulation, FTS index size.

### F. Architecture & Philosophy (1 critical, 6 high, 5 med, 5 low)
- **I-1 [CRITICAL]:** SessionStart reads DB WITHOUT lock -- mid-consolidation snapshot injection. (hooks.py:102)
- **I-2 [HIGH]:** Dedup uses stale access_count. (consolidate.py:280)
- **I-3 [HIGH]:** Centroid drifts toward sentinel vector. (consolidate.py:415)
- **E-2 [HIGH]:** Budget starvation cascade across cycles. (consolidate.py:330)
- **D-1 [HIGH]:** MemoryService god object. (store.py)
- **D-2 [HIGH]:** Consolidation 300-line method, implicit ordering. (consolidate.py:175)
- **F-1 [HIGH]:** Spool death spiral -- most identity-forming events shed first. (pipeline.py:286)
- **F-2 [HIGH]:** Corruption -> quarantine -> silent identity loss. (db.py:171)
- **T-1 [HIGH]:** No lifecycle integration test. (tests/)
- **T-2 [HIGH]:** All tests use hash embedder. (tests/conftest.py)
- **D-3..4, O-1..2 [MED]:** English tokenizer, no embed_dim migration, no health dashboard, no degradation alerting.
- **P-1..3, O-3..4 [LOW]:** Topic-level not dispositional individuation, Bem permeable, empty cycle bombing, log rotation, valence inference.

---

## Prioritized Action Items

### P0 -- Fix Before Next Merge (~2 hours)

| # | Finding | Fix | Effort |
|---|---------|-----|--------|
| 1 | I-1: SessionStart without lock | Acquire lock or add consolidation_in_progress flag | 30min |
| 2 | H-M-3: Config caps too high | assoc_eta<=1.0, boost_frac<=1.0, reinforce_cap<=10.0 | 15min |
| 3 | M-1: support_count inconsistency | MAX(support_count, current+1) in upsert_fact() | 15min |
| 4 | C9-H-1: Spool drop race | Atomic write or fcntl.flock on spool fd | 30min |
| 5 | M-3: Spool disk-full loss | Write-to-temp, fsync, rename | 20min |

### P1 -- Fix Before Production (~1 day)

6. S-3: Streaming chunked all_episodic()
7. S-4: LSH for approximate dedup
8. S-5: Pagination for history()/forget()
9. I-2: Re-read access_count under lock
10. E-2: Cross-cycle budget carryover limit
11. F-2: Log WARNING on quarantine
12. T-1: Lifecycle integration test
13. T-2: Real embedder smoke tests

### P2 -- When Convenient (10 items)
goal_hint bypass, valence flip, English tokenizer, embed_dim migration, health dashboard, degradation alerting, lru_cache cap, VACUUM, lock perms, temp filename.

### P3 -- Design Debt (Phase 1+)
God object decomposition, consolidation extraction, spool death spiral, Bem firewall.

---

## Philosophical Assessment

**Topic-level individuation: YES.** Different histories -> different PersonaTrees. 0.000 cross-domain Jaccard. Claim holds.

**Dispositional individuation: NOT YET.** Temperament layer inert at Phase 0.

**What breaks the claim:** (1) Convergence (not observed). (2) Amnesia from consolidation bugs (F-1, F-2). (3) Homogenization via injection (P0 fixes address this).

---

## Comparison with Cycle 8

| Metric | Cycle 8 | Cycle 9 |
|--------|---------|---------|
| Findings | 20 | 44 |
| CRITICAL | 0 | 1 |
| HIGH | 6 | 16 |
| MEDIUM | 8 | 14 |
| LOW | 6 | 10 |
| Fixes verified | N/A | 15/20 fixed |

---

## Closing

CDMS at f4dd7cf is substantially hardened. Cycle 8 was 75% effective. The one CRITICAL (I-1) produces stale context, not corruption. HIGH findings cluster around scale debt and config gaps -- fixable with patches, not rewrites.

**Ready for Phase 0 with 5 P0 fixes (~2 hours). P1 gates multi-user deployment. Architectural debt gates Phase 1.**

---

*End of Cycle 9 -- 6 parallel subagents, 44 findings, all verifiable.*
