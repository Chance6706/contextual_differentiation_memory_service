# CDMS Red-Team — Cycle 9 — CONCURRENCY Audit

> **Date:** 2026-06-18
> **Commit:** f4dd7cf (main)
> **Scope:** Concurrency-focused deep audit of lock.py, db.py, consolidate.py, store.py, embeddings.py, hooks.py, pipeline.py, spool.py, and tests/test_capture_concurrency.py.
> **Methodology:** Line-by-line manual review of all source, focusing on TOCTOU races, lock ordering, shared mutable state, SQLite WAL concurrency, signal handling, singleton races, and verification of Cycle 8 fixes.

---

## Executive Summary

CDMS's concurrency model is **substantially improved since Cycle 8**. The three specifically-tracked Cycle 8 concurrency findings (H-5, M-1, M-C-2) have all been addressed — two fully fixed, one partially mitigated with a defensible tradeoff. The cross-process lock design is sound for its purpose. The spool claim mechanism is correctly atomic.

This audit found **1 new HIGH**, **3 new MEDIUM**, and **4 new LOW** concurrency findings. No CRITICAL issues. The most significant new finding is a non-atomic multi-step spool rewrite in `forget` that can silently drop events (HIGH).

---

## Cycle 8 Regression Check

### H-5: `get_embedder()` TOCTOU Race — **FIXED**

**Cycle 8 finding:** Two concurrent first-callers both see `_SINGLETON is None`, both construct `Embedder` instances, loading two ~133MB ONNX sessions.

**Current code** (`embeddings.py:164-178`):
```python
_SINGLETON_LOCK = threading.Lock()

def get_embedder(cfg: Config) -> Embedder:
    global _SINGLETON, _SINGLETON_KEY
    key = _embedder_key(cfg)
    if _SINGLETON is not None and _SINGLETON_KEY == key:
        return _SINGLETON
    with _SINGLETON_LOCK:
        if _SINGLETON is None or _SINGLETON_KEY != key:
            _SINGLETON = Embedder(cfg)
            _SINGLETON_KEY = key
        return _SINGLETON
```

**Assessment:** Classic double-checked locking with a module-level `threading.Lock()`. The fast path (line 167) avoids the lock for the common case. The slow path (line 169) re-checks under the lock so concurrent first-callers construct exactly one instance. The `_embedder_key` mechanism also correctly forces a rebuild when config changes. **Fully fixed.**

---

### M-1: `touch_episodic` vs Eviction Race — **FIXED**

**Cycle 8 finding:** Consolidation decides to evict based on stale `access_count`. Concurrent `retrieve()` (no lock) bumps `access_count` via `touch_episodic()`. Consolidation deletes anyway, wrongly evicting a just-retrieved memory.

**Current code** (`consolidate.py:199-215`):
```python
def _evict(self, episodes, now, rep):
    candidates = [
        e for e in episodes
        if accessibility(e.base_salience, age_days(e.timestamp, now),
                         e.access_count, self.cfg) < self.cfg.retention_floor
    ]
    doomed = []
    for e in candidates:
        fresh = self.db.get_episodic(e.id)       # re-read from DB
        if fresh is None:
            continue
        acc = accessibility(fresh.base_salience, age_days(fresh.timestamp, now),
                            fresh.access_count, self.cfg)  # fresh access_count
        if acc < self.cfg.retention_floor:
            doomed.append(fresh.id)
    rep.episodes_evicted = self.db.delete_episodic(doomed)
```

**Assessment:** The fix adds a per-candidate re-read from the database before deletion. This closes the race window: even if `touch_episodic()` bumped `access_count` between the initial snapshot and the eviction check, the fresh read picks up the new count. The comment explicitly acknowledges the race and cites Cycle-8 M-1. **Fully fixed.** The remaining theoretical window (re-read, then `touch_episodic`, then delete) is vanishingly small and would require a retrieve completing in the microsecond gap between `get_episodic` and `delete_episodic` within the same locked pass — acceptable.

---

### M-C-2: Hook Sees Partial Consolidation State — **Mitigated (defensible tradeoff)**

**Cycle 8 finding:** `SessionStart` reads without the cross-process lock. Can see mid-consolidation state (episodes evicted but gists not yet aggregated).

**Current code:** `SessionStart` still reads without the lock (`hooks.py:76-117`). No change.

**Assessment:** This was always a design tradeoff, not a bug. SessionStart must be fast (hook timeout); acquiring the cross-process lock would block it for the duration of a consolidation pass (seconds to tens of seconds). The inconsistency window is bounded by consolidation duration and the impact is cosmetic — the injected context may reference gists whose support episodes were just evicted, or miss gists not yet aggregated. The context is self-healing (next session sees consistent state). **Defensibly not fixed.** A read-lock or snapshot isolation approach would be correct but impractical for the hook timeout constraint.

---

## New Findings

### HIGH

#### C9-H-1: `forget` spool rewrite can drop events appended during processing

**File:** `store.py:222-260` (`_forget_from_spool`) vs `spool.py:40-59` (`spool_event`)

**Race window:** The `_forget_from_spool` method uses `os.replace()` to atomically claim the spool into a temp file, filters it, then writes back kept lines. Between the `os.replace` and the `spool_event_lines` writeback, concurrent hooks may call `spool_event()` which opens the (now-renamed-away) file by path — but gets a NEW file at the original path (O_CREAT).

**Actual issue:** `spool_event` at `spool.py:20` does:
```python
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
```
If this `os.open` executes AFTER `_forget_from_spool`'s `os.replace(q, claimed)` has moved the original file away, a NEW empty file is created at `queue_path`. The event is written to this new file. Then `_forget_from_spool` writes its kept lines back to `queue_path` via `spool_event_lines` (also O_APPEND), which appends AFTER the new event. The ordering is shuffled but no event is lost.

**However**, there is a narrower race: if `spool_event` opens the fd (getting a handle to the OLD inode) just BEFORE `os.replace` moves it, the `os.write` appends to the CLAIMED file (old inode). The `spool_event_lines` writeback creates a NEW file at `queue_path` and writes kept lines there. When `claimed.unlink()` runs, the event from the racing `spool_event` is destroyed.

**Race sequence:**
1. `spool_event` calls `os.open(queue_path, ...)` — gets fd pointing to old inode
2. `_forget_from_spool` calls `os.replace(queue_path, claimed)` — old inode now at `claimed` path, `queue_path` is gone
3. `spool_event` calls `os.write(fd, data)` — writes to claimed file (old inode)
4. `_forget_from_spool` reads `claimed`, filters, writes kept lines to new `queue_path` via `spool_event_lines`
5. `_forget_from_spool` calls `claimed.unlink()` — the event from step 3 is destroyed

**Impact:** A single event can be silently dropped during a `forget` operation. The event was captured by a hook but never ingested. Rare in practice (requires exact timing of hook append during forget's spool processing window), but non-recoverable.

**Severity:** HIGH — silent data loss of captured interactions.

**Fix:** Since `forget` already holds the cross-process lock, drain the spool BEFORE calling `_forget_from_spool`, so no concurrent append can reach the spool file during processing. Alternatively, after the claim, check for a new spool file and merge. The simplest fix: `_forget_from_spool` should re-check for a new spool file after processing and NOT delete `claimed` until it's confirmed no events were stranded.

---

### MEDIUM

#### C9-M-1: `_reconciled` flag in MemoryService is a thread-unsafe lazy init

**File:** `store.py:97-104`

```python
def __init__(self, ...):
    ...
    self._reconciled = False

def _reconcile_embedder(self) -> None:
    if self._reconciled:        # no lock, non-atomic check
        return
    self.db.reconcile_embedder(self.embedder.fingerprint())
    self._reconciled = True
```

**Race window:** FastMCP dispatches sync tools off the loop thread (`check_same_thread=False`). Two concurrent `ingest()` calls on the same `MemoryService` instance could both read `_reconciled = False`, both call `reconcile_embedder()`. Since `reconcile_embedder` does a `get_meta` then `set_meta` (two separate transactions), two concurrent reconcilers could interleave: both read `None` for `embed_fingerprint`, both write the same fingerprint. Result: harmless duplicate write (INSERT OR REPLACE is idempotent). No corruption.

**Impact:** At most a harmless duplicate meta write. The fingerprint value is the same in both callers.

**Severity:** MEDIUM — the pattern is a latent TOCTOU that could become a real bug if `reconcile_embedder` ever gains non-idempotent side effects.

**Fix:** Add `self._reconciled_lock = threading.Lock()` and use double-checked locking, or accept since idempotent.

---

#### C9-M-2: Consolidation's in-memory episode list diverges from DB state during multi-step pass

**File:** `consolidate.py:175-228` (`_run_locked`)

**Trace:** The consolidation pass loads `episodes = self.db.all_episodic()` once at the top, then proceeds through 5 steps (elevate, dedup, evict, compete, aggregate) using the in-memory list. Each step does DB writes that modify the store. The in-memory list is progressively pruned between steps (lines 201, 204, 207), but DB operations from step N affect rows that step N+1's in-memory list considers.

**Assessment:** The design is intentionally snapshot-based for performance (the prior re-query approach was optimized away, per comment at line 193). The snapshot divergence is bounded and well-managed — each step filters removed IDs from the in-memory list before passing to the next step.

**Severity:** MEDIUM — the snapshot approach is correct for the current step ordering, but any future reordering of steps could introduce subtle bugs. Document the invariant: "steps must be order-independent with respect to in-memory state."

---

#### C9-M-3: Log rotation race between two hook processes

**File:** `hooks.py:192-207` (`_log`)

```python
if p.exists() and p.stat().st_size > _LOG_MAX_BYTES:
    for g in range(_LOG_GENERATIONS, 1, -1):
        src = p.with_name(p.name + f".{g - 1}")
        if src.exists():
            src.replace(p.with_name(p.name + f".{g}"))
    p.replace(p.with_name(p.name + ".1"))
```

**Race window:** Two hook processes both check `st_size > _LOG_MAX_BYTES`, both start rotating. Process A renames `log` -> `log.1`, process B tries to rename `log` -> `log.1` but `log` no longer exists. The `p.replace()` raises `FileNotFoundError`, caught by the outer `except OSError`.

**Impact:** Lost log message. Rotation may leave gaps in the log chain.

**Severity:** MEDIUM — logs are best-effort debugging aids. The `except OSError` prevents crashes.

**Fix:** Catch `FileNotFoundError` specifically in the rotation loop and continue. Or accept as best-effort.

---

### LOW

#### C9-L-1: `set_meta` used for non-atomic counter increment (cycle counter)

**File:** `db.py:146-148` and `consolidate.py:184`

**Race:** Two processes read `cycle=5`, both compute `6`, both write `6`. Counter advances by 1 instead of 2.

**Mitigation:** Cross-process lock prevents concurrent consolidation. Only manifests on platforms without advisory locks.

**Severity:** LOW. Fix: use atomic SQL increment.

---

#### C9-L-2: SQLite `busy_timeout` may be insufficient for long consolidation

**File:** `db.py:128` (`PRAGMA busy_timeout=5000`)

**Trace:** WAL mode allows concurrent reads during writes, so the 5-second timeout covers only write-write contention (which the cross-process lock prevents). Read-write contention is handled by WAL's snapshot isolation.

**Severity:** LOW — WAL mode largely eliminates the concern.

---

#### C9-L-3: PID reuse in orphan detection

**File:** `pipeline.py:230-246` (`_is_orphan`)

**Trace:** If the original drain process died and a new process reuses the same PID within `_RECLAIM_AGE_SECONDS` (3600s), the claim is incorrectly considered alive. Events are stranded for up to 1 hour.

**Severity:** LOW — PID reuse within 1 hour is rare. The 1-hour reclaim age is a hard backstop.

---

#### C9-L-4: `check_same_thread=False` broad relaxation

**File:** `db.py:125`

**Trace:** Disables Python's thread-safety check. Needed for FastMCP. Current code never shares cursors across threads (each method creates its own via `self.conn.execute()`). The GIL provides implicit safety for the connection object.

**Severity:** LOW — safe today, but could mask future bugs if cursor sharing is introduced.

---

## Findings Summary

| ID | Severity | Description | File:Line | Status |
|----|----------|-------------|-----------|--------|
| **Cycle 8 Regression** | | | | |
| H-5 | ~~HIGH~~ | Embedder TOCTOU singleton race | `embeddings.py:164-178` | FIXED |
| M-1 | ~~MEDIUM~~ | touch_episodic vs eviction stale read | `consolidate.py:199-215` | FIXED |
| M-C-2 | MEDIUM | Hook sees partial consolidation state | `hooks.py:76-117` | Mitigated (defensible) |
| **New Findings** | | | | |
| C9-H-1 | **HIGH** | forget spool rewrite can drop concurrent appends | `store.py:222-260` | Open |
| C9-M-1 | MEDIUM | `_reconciled` flag is thread-unsafe lazy init | `store.py:97-104` | Open |
| C9-M-2 | MEDIUM | In-memory episode list diverges during multi-step pass | `consolidate.py:175-228` | Document |
| C9-M-3 | MEDIUM | Log rotation race drops messages | `hooks.py:192-207` | Open |
| C9-L-1 | LOW | Non-atomic cycle counter increment | `db.py:146-148` | Accepted |
| C9-L-2 | LOW | busy_timeout vs long consolidation | `db.py:128` | WAL mitigates |
| C9-L-3 | LOW | PID reuse in orphan detection | `pipeline.py:230-246` | Accepted |
| C9-L-4 | LOW | check_same_thread=False broad relaxation | `db.py:125` | Safe today |

---

## Concurrency Architecture Assessment

### Cross-Process Lock (`lock.py`)
**Sound.** Uses `fcntl.flock` (POSIX) / `msvcrt.locking` (Windows) with non-blocking poll. Auto-released on process death. Degrades to no-op on unsupported platforms (documented). The `cross_process_lock` context manager correctly releases in `finally`. The timeout-and-skip pattern (vs. blocking) is the right choice for hooks with tight deadlines.

### SQLite WAL Mode (`db.py`)
**Correct.** WAL mode enables concurrent readers during writes. `busy_timeout=5000` covers write-write contention. `secure_delete=ON` + `VACUUM` after forget ensures right-to-forget. The quarantine-on-corruption logic correctly distinguishes `OperationalError` (lock contention) from genuine `DatabaseError` (corruption).

### Spool Claim Mechanism (`pipeline.py`)
**Correct for drain path.** Unique per-drain claim names (`pid-uuid.processing`) prevent concurrent drain clobbering. Atomic `os.replace` picks exactly one winner. Orphan reclamation handles killed drains. The issue is only in the `_forget_from_spool` path (C9-H-1).

### Singleton Embedder (`embeddings.py`)
**Fixed.** Double-checked locking with module-level `threading.Lock()`. Fast path avoids lock. Slow path re-checks under lock. Config key change forces rebuild.

### Thread Safety of MemoryService
**Adequate.** Instances are created per-hook (short-lived) or per-MCP-request. The `_reconciled` flag is the only shared mutable state on instances, and its race is idempotent. The `Database` connection is safe due to SQLite's internal serialization and no cursor sharing.

---

## Recommendations

### P0 — Fix Before Next Merge

| ID | Finding | Fix |
|----|---------|-----|
| C9-H-1 | forget spool rewrite drops concurrent appends | Drain spool before `_forget_from_spool` (lock already held), or re-check for new spool file after processing |

### P1 — Fix When Convenient

| ID | Finding | Fix |
|----|---------|-----|
| C9-M-1 | `_reconciled` TOCTOU | Add threading.Lock or accept idempotent duplicate |
| C9-M-2 | In-memory snapshot divergence | Document the step-ordering invariant |
| C9-M-3 | Log rotation race | Add `except FileNotFoundError` in rotation loop |

### Accepted Risks

| ID | Finding | Rationale |
|----|---------|-----------|
| C9-L-1 | Non-atomic cycle counter | Only on platforms without locks; impact is minor |
| C9-L-2 | busy_timeout vs long consolidation | WAL mitigates; cross-process lock prevents write-write |
| C9-L-3 | PID reuse in orphan detection | 1-hour backstop; rare on typical systems |
| C9-L-4 | check_same_thread=False | No cursor sharing today; GIL provides implicit safety |

---

## Test Coverage Assessment

`tests/test_capture_concurrency.py` covers:
- Concurrent overlapping drains lose no events (unique claim names)
- Spool appends are well-formed under concurrency (no torn lines)

**Not covered:**
- `forget` during concurrent spool appends (C9-H-1)
- `touch_episodic` during consolidation eviction (M-1 fix regression test)
- `get_embedder()` singleton under concurrent first-call (H-5 fix regression test)
- `SessionStart` during consolidation (M-C-2 — hard to test without time-travel)

---

*End of Cycle 9 Concurrency Audit.*
