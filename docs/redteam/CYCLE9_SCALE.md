# CDMS Red-Team — Cycle 9 — SCALE and LONG-HORIZON Audit

> **Model:** Hermes / Nous Research (subagent)
> **Date:** 2026-06-18
> **Commit:** f4dd7cf (main, pre-existing Cycle-9 mechanical/concurrency/security reports on branch)
> **Scope:** Memory footprint at 10K/50K/100K/500K episodes. SQLite index performance. Consolidation time complexity. DB file growth. Embedding storage. FTS5 index size. Scar table growth. Spool file growth. Memory leaks. lru_cache growth. Anything loading 'all' data into memory.

---

## Executive Summary

Cycle 8's C-1 fix (per-project partitioning) significantly reduced peak *vector matrix* memory during consolidation, and the H-4 scar cap prevents L3 unbounded growth. However, **every major code path still loads full tables into Python via `all_episodic()`, `all_gist()`, and `all_scars()`** — the Python object overhead (not the vectors alone) is the dominant memory consumer. At 100K+ episodes, consolidation RSS exceeds 500MB (realistic) to 1.7GB (worst case). At 500K episodes, dedup's O(n^2) per-project matmul takes 8+ minutes for a single large project.

**On the 128GB mini PC target:** current code handles 100K episodes comfortably (realistic workload). At 500K episodes with a single large project, consolidation takes ~12 minutes and peaks at ~2.5GB RSS — functional but slow. The system is **not at risk of OOM on the target hardware at 500K or fewer episodes with realistic text lengths**.

The highest-impact remaining scale bottleneck is the **O(n^2) dedup matmul**, not memory. The second is the pervasive `all_*()` loading pattern that blocks streaming/chunked processing.

---

## Cycle 8 Part V Scale Findings — Status

| Cycle-8 ID | Finding | Status | Evidence |
|------------|---------|--------|----------|
| **C-S-1** | Consolidation loads ALL episodes into OOM | **PARTIALLY FIXED** | Per-project partitioning (1f60865) bounds vector matrices to largest project. But `all_episodic()` still materializes ALL Python objects before partitioning. |
| **H-S-1** | L3 scar table unbounded growth | **FIXED** | `scar_project_cap=100`, `_evict_scars()` evicts oldest auto-elevated per project; pinned exempt (33f2b3a). |
| **M-S-1** | DB file bloat from free pages | **FIXED** | `vacuum_after_deletes=5000` gates VACUUM to passes deleting >=5000 rows (33f2b3a). |
| **M-S-2** | Retrieval latency at 50K+ gists | **NOT FIXED** | vec0 KNN still brute-force cosine. Gist count self-limits via decay (mitigating). |
| **L-S-1** | Dedup per-candidate DB round-trip | **FIXED** | `keep_e` in-memory list caches survivors (ff8ba22). |
| **L-S-2** | `lru_cache(maxsize=None)` unbounded | **NOT FIXED** | `pipeline.py:51` — still `maxsize=None`. Practically ~20 entries. |

---

## Findings

### S-1: `all_episodic()` loads ALL episodes into Python before any processing

**Severity: HIGH**
**File:** `consolidate.py:198`, `db.py:244-254`

`_run_locked()` calls `self.db.all_episodic()` which does `SELECT * FROM mem_episodic ORDER BY rowid` and materializes every row as a Python `Episodic` dataclass. This happens *before* the per-project partitioning that was the C-1 fix. The partitioning only bounds the *vector matrices*, not the episode objects themselves.

Each `Episodic` Python object consumes:
- 3 text fields x (avg ~300-500 chars + 49-byte string header + 64-byte pointer) = ~1.2KB realistic, ~12.5KB worst-case (max_field_chars=4000 x 3)
- Dataclass + metadata: ~200 bytes
- **Realistic average: ~1.5KB per episode object**
- **Worst case: ~13KB per episode object**

**Estimated Python object memory (all_episodic, pre-partitioning):**

| Episodes | Realistic (1.5KB/ep) | Worst case (13KB/ep) |
|----------|---------------------|---------------------|
| 10K      | 15 MB               | 130 MB              |
| 50K      | 75 MB               | 650 MB              |
| 100K     | 150 MB              | 1.3 GB              |
| 500K     | 750 MB              | 6.5 GB              |

**Also affected:** `history()` (store.py:368), `forget()` (store.py:394-402), `_decay_gists()` via `all_gist()` (consolidate.py:446), `_evict_scars()` via `all_scars()` (consolidate.py:247).

**Impact:** On the 128GB target, realistic workloads are fine through 500K. Worst-case (max-length fields) peaks at 6.5GB for 500K episodes — still within 128GB but 10x more than necessary.

**Fix:** Replace `all_episodic()` with streaming/chunked `SELECT ... LIMIT ? OFFSET ?` or cursor-based iteration. For consolidation, process one project at a time with `SELECT ... WHERE project = ? ORDER BY rowid`.

---

### S-2: Dedup O(n^2) matmul complexity per project

**Severity: HIGH**
**File:** `consolidate.py:333-368`

The vectorized dedup compares each episode against all survivors via `keep_mat[:m] @ v`. For a single project with N episodes and few duplicates (m approaches N), this is O(N^2 x dim/2) FLOPs:

| Episodes (single project) | FLOPs | Time @ 100 GFLOPS |
|---------------------------|-------|--------------------|
| 10K                       | 19B   | 0.2s               |
| 50K                       | 480B  | 5s                 |
| 100K                      | 1.9T  | 20s                |
| 500K                      | 48T   | 480s (8 min)       |

With per-project partitioning, the cost is the sum of (N_p^2 x dim/2) across P projects. For evenly split episodes: total = N^2 x dim / (2P).

| Episodes | 1 project | 5 projects | 20 projects |
|----------|-----------|------------|-------------|
| 10K      | 0.2s      | 0.04s      | 0.01s       |
| 50K      | 5s        | 1s         | 0.25s       |
| 100K     | 20s       | 4s         | 1s          |
| 500K     | 480s      | 96s        | 24s         |

**Impact:** Single-project-heavy workloads (one large repo) see quadratic time blowup. At 500K episodes in one project: 8 minutes just for dedup.

**Fix:** Use LSH (locality-sensitive hashing) or batch-near-neighbor indexing. Alternatively, cap the dedup comparison window to the K most recent episodes rather than all survivors.

---

### S-3: `history()` loads ALL episodes into memory

**Severity: HIGH**
**File:** `store.py:366-371`

```python
def history(self, limit: int = 20, session_id: Optional[str] = None) -> list[Episodic]:
    eps = self.db.all_episodic()  # loads EVERYTHING
    if session_id:
        eps = [e for e in eps if e.session_id == session_id]
    eps.sort(key=lambda e: e.timestamp, reverse=True)
    return eps[:limit]
```

To return 20 most-recent episodes, this loads all episodes, sorts them in Python, and slices. At 100K episodes: ~150MB allocation to return 20 items.

**Fix:** Add `db.recent_episodic(limit, session_id)` with `SELECT ... ORDER BY timestamp DESC LIMIT ?` and optional `WHERE session_id = ?`.

---

### S-4: `forget()` loads ALL episodes + gists + scars

**Severity: HIGH**
**File:** `store.py:394-402`

```python
for e in self.db.all_episodic():  # all L1
    ...filter by project/session/ids...
for g in self.db.all_gist():      # all L2
    ...filter...
for s in self.db.all_scars():     # all L3
    ...filter...
```

Three full table scans materialized as Python objects. At 100K episodes + 1K gists + 100 scars: ~155MB.

**Fix:** Push project/session filtering into SQL: `DELETE FROM mem_episodic WHERE project = ?` (or `session_id = ?`). Only load explicit-ID matches into Python.

---

### S-5: `_evict()` per-candidate DB round-trip

**Severity: MEDIUM**
**File:** `consolidate.py:301-318`

The race fix from Cycle-8 M-1 re-reads each eviction candidate individually before deleting:
```python
for e in candidates:
    fresh = self.db.get_episodic(e.id)  # one SQL query per candidate
```

At 100K episodes with 50% eviction candidates: 50K individual `SELECT ... WHERE id = ?` queries. At ~0.1ms per query: ~5 seconds.

**Fix:** Batch the re-read: `SELECT id, base_salience, access_count FROM mem_episodic WHERE id IN (...)` in chunks of 800, then re-check accessibility in Python.

---

### S-6: VACUUM requires 2x DB file size

**Severity: MEDIUM**
**File:** `db.py:298-303`

`PRAGMA wal_checkpoint(TRUNCATE)` + `VACUUM` rewrites the entire DB file. SQLite needs ~2x the DB size during VACUUM (old file + new file coexist briefly).

| Episodes | DB Size | VACUUM Peak Disk |
|----------|---------|-----------------|
| 10K      | ~50 MB  | ~100 MB         |
| 50K      | ~250 MB | ~500 MB         |
| 100K     | ~500 MB | ~1 GB           |
| 500K     | ~2.5 GB | ~5 GB           |

**Impact:** On the 128GB mini PC with presumably ample disk, this is not a concern. On a constrained VM with small disk, VACUUM at 500K could fail.

**Mitigation:** Already gated behind `vacuum_after_deletes=5000` — only runs after bulk deletes. Consider `PRAGMA auto_vacuum=INCREMENTAL` + `PRAGMA incremental_vacuum` as a lighter alternative.

---

### S-7: vec0 brute-force KNN — linear scan at query time

**Severity: MEDIUM**
**File:** `db.py:458-475`

sqlite-vec `vec0` does brute-force cosine KNN (full table scan). Latency scales linearly with table size:

| Tier rows | KNN latency (est.) |
|-----------|--------------------|
| 10K       | ~1-2ms             |
| 50K       | ~5-10ms            |
| 100K      | ~10-20ms           |
| 500K      | ~50-100ms          |

**Impact:** At 500K episodes, each `retrieve()` does 3 KNN calls (scar, gist, episodic) = ~150-300ms total KNN time. Still interactive but noticeable. Gist and scar tiers are much smaller (self-limiting).

**Mitigating factor:** Gist count self-limits via decay (typically 500-5000). Scar count bounded by `scar_project_cap` (typically less than 500). Only episodic tier reaches 100K+.

**Fix:** Consider approximate nearest-neighbor (ANN) indexing via sqlite-vec's `vec0` with an IVF index if/when supported, or switch to a HNSW-backed solution.

---

### S-8: Support edges table growth — never independently pruned

**Severity: LOW**
**File:** `db.py:87-91`, `consolidate.py:437`

Each episode linked to a gist gets a row in `mem_support_edges`. Edges are only deleted when their source episode or target gist is deleted — there is no independent pruning.

| Episodes | Edges (est.) | Table size |
|----------|-------------|------------|
| 10K      | ~10K        | ~1 MB      |
| 50K      | ~50K        | ~5 MB      |
| 100K     | ~100K       | ~10 MB     |
| 500K     | ~500K       | ~50 MB     |

**Impact:** Negligible at all scales. No index on this table means queries scan linearly, but the table is only used for provenance tracking (not in any hot path).

---

### S-9: `lru_cache(maxsize=None)` on `_marker_re`

**Severity: LOW**
**File:** `pipeline.py:51`

```python
@lru_cache(maxsize=None)
def _marker_re(marker: str) -> re.Pattern[str]:
```

Unbounded cache, but the marker set is static (~20 entries from `_ERR_MARKERS` and `_OK_MARKERS`). Cache size: ~20 x ~200 bytes = ~4KB. No growth over time.

**Status:** Cosmetic. Set `maxsize=128` for defense-in-depth.

---

### S-10: `_match_gist_by_embedding()` scans all centroids for subject+project

**Severity: LOW**
**File:** `consolidate.py:496-513`

```python
for g, gc in self.db.gist_centroids(subject, project):
    ...dot product check...
```

Loads all centroids for a (subject, project) pair and linear-scans them. In practice: most projects have 10-100 gists per subject. At the theoretical extreme (10K gists for one subject): ~10K dot products x 384 dims = ~4M FLOPs = negligible.

---

## Aggregate Memory and Time Estimates

### Consolidation Total RSS (episodes + vectors + working memory)

| Episodes | Realistic Text | Worst-Case Text |
|----------|---------------|-----------------|
| 10K      | ~50 MB        | ~170 MB         |
| 50K      | ~250 MB       | ~850 MB         |
| 100K     | ~500 MB       | ~1.7 GB         |
| 500K     | ~2.5 GB       | ~8.5 GB         |

*Realistic: avg 800 chars/episode across 3 fields. Worst-case: max_field_chars=4000 x 3.*

### Consolidation Wall-Clock Time (dedup-dominated)

| Episodes | 1 project | 5 projects | 20 projects |
|----------|-----------|------------|-------------|
| 10K      | ~2s       | ~1s        | ~1s         |
| 50K      | ~16s      | ~7s        | ~4s         |
| 100K     | ~70s      | ~25s       | ~10s        |
| 500K     | ~730s     | ~300s      | ~100s       |

*Includes: all_episodic load, dedup, evict, compete+renorm, aggregate, decay, optional VACUUM.*

### DB File Size

| Episodes | Data Size | With Indexes + WAL |
|----------|-----------|--------------------|
| 10K      | ~37 MB    | ~50 MB             |
| 50K      | ~185 MB   | ~250 MB            |
| 100K     | ~370 MB   | ~500 MB            |
| 500K     | ~1.85 GB  | ~2.5 GB            |

*Per-episode: ~900B mem_episodic + ~1.6KB vec_episodic + ~1.2KB fts_episodic = ~3.7KB*

### Embedding Storage (vec0 tables)

| Episodes | vec0 Size |
|----------|-----------|
| 10K      | 15 MB     |
| 50K      | 73 MB     |
| 100K     | 146 MB    |
| 500K     | 732 MB    |

*Per vector: 384 x 4 bytes = 1,536 bytes*

### FTS5 Index Size

| Episodes | FTS5 Size (est.) |
|----------|-----------------|
| 10K      | ~15 MB          |
| 50K      | ~75 MB          |
| 100K     | ~150 MB         |
| 500K     | ~750 MB         |

*Per episode FTS5: ~800 chars content + inverted index overhead = ~1.5KB*

### Scar Table Growth (now bounded)

With `scar_project_cap=100` and dedup at 0.95 similarity:
- Maximum auto-elevated scars per project: 100
- Plus pinned scars (unlimited, but rarely created — typically less than 20)
- Per scar: ~4KB (text + vec + FTS5)
- At 10 projects: ~10 x 100 x 4KB = ~4MB (negligible)

### Spool File Growth

Capped at `spool_max_bytes=100MB`. At ~500 bytes per event: ~200K events before cap. Events are shed (dropped) above cap with stderr warning.

---

## Memory Leak Analysis

| Object | Size | Lifetime | Leaks? |
|--------|------|----------|--------|
| `_SINGLETON` Embedder | ~133MB (ONNX model) | Process lifetime | No — by design |
| `_marker_re` lru_cache | ~4KB | Process lifetime | No — bounded by marker set |
| `all_episodic()` list | Proportional to episodes | Per-consolidation pass | No — freed after pass |
| numpy `keep_mat` | Largest project x 384 x 4 | Per-project dedup loop | No — `del vecs, keep_mat` after each project |
| numpy `cent` matrix | Per-project x 384 x 4 | Per-project cluster loop | No — `del vecs, items` after each project |

**No incremental memory leaks found.** All large allocations are scoped to a consolidation pass and freed afterward. The `_SINGLETON` embedder is the only long-lived allocation.

---

## Prioritized Findings Summary

| # | Finding | Severity | Fix Effort | Est. Impact |
|---|---------|----------|------------|-------------|
| S-1 | `all_episodic()` loads all episodes before partitioning | **HIGH** | Medium | 1.7GB at 100K (worst) |
| S-2 | Dedup O(n^2) per project | **HIGH** | High | 480s at 500K/1 project |
| S-3 | `history()` loads all episodes for top-N | **HIGH** | Low | 150MB to get 20 items |
| S-4 | `forget()` loads all tables to filter | **HIGH** | Low | 300MB+ at 100K |
| S-5 | `_evict()` per-candidate re-read | **MEDIUM** | Low | 5s at 100K candidates |
| S-6 | VACUUM needs 2x DB disk | **MEDIUM** | Low | 5GB at 500K |
| S-7 | vec0 brute-force KNN | **MEDIUM** | High | 50-100ms/500K rows |
| S-8 | Support edges never pruned independently | **LOW** | Low | 50MB at 500K |
| S-9 | `lru_cache(maxsize=None)` | **LOW** | Trivial | ~4KB |
| S-10 | Centroid linear scan | **LOW** | None | Negligible |

### Recommended Fix Priority

**P0 — Before 500K deployment:**
1. S-3: `history()` — replace `all_episodic()` with SQL `ORDER BY timestamp DESC LIMIT ?`
2. S-4: `forget()` — push filtering into SQL `DELETE WHERE project = ? / session_id = ?`
3. S-5: `_evict()` — batch re-read with `WHERE id IN (...)` instead of per-row

**P1 — Before 100K production:**
4. S-1: Streaming consolidation — `SELECT WHERE project = ?` instead of `all_episodic()` + filter
5. S-2: Dedup windowing — limit comparison to K most-recent survivors, or LSH

**P2 — Nice to have:**
6. S-6: `PRAGMA auto_vacuum=INCREMENTAL` as lighter alternative to full VACUUM
7. S-7: ANN indexing when sqlite-vec supports it
8. S-8: Periodic orphan-edge cleanup
9. S-9: `maxsize=128` on `_marker_re`

---

## Closing Assessment

CDMS on the 128GB mini PC target handles 100K episodes comfortably and 500K episodes in realistic workloads (multi-project). The Cycle 8 C-1 per-project partitioning was the right fix — it eliminated the worst OOM vector. The scar cap (H-4) and gated VACUUM (M-S-1) are solid.

The remaining scale ceiling is the O(n^2) dedup time complexity, not memory. For a single-project user accumulating 500K+ episodes, consolidation will take 8+ minutes. This is a *performance* problem, not a *correctness* or *OOM* problem — consolidation still completes and the system still functions.

The `all_*()` loading pattern is the root technical debt. Fixing S-3 and S-4 are low-effort wins. Fixing S-1 (streaming consolidation) is the architectural change that would unlock true linear scaling but requires careful handling of the in-memory dedup/eviction state tracking.

**Bottom line:** CDMS is scale-safe on its target hardware through 500K episodes. The P0 fixes (S-3, S-4, S-5) are simple SQL improvements. The P1 fix (S-1, streaming consolidation) is the real investment needed for the 500K+ horizon.

---

*End of Cycle 9 — SCALE and LONG-HORIZON audit. All findings independently verifiable against commit f4dd7cf.*
