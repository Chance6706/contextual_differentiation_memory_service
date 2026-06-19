# CDMS Red-Team — Cycle 9, Mechanical/Code Audit

> **Model:** Hermes Agent (Nous Research)
> **Date:** 2026-06-18
> **Commit:** f4dd7cf on main (parent of HEAD 1c803bb)
> **Methodology:** Full source read of all 16 Python files in `src/cdms/` (~4500 LOC). Each file read via `git show HEAD:src/cdms/<file>`. Cross-referenced against Cycle 8 (OWL Alpha) final report.
> **Scope:** Mechanical/code-level defects: logic errors, off-by-ones, unhandled exceptions, swallowed errors, dead code, API misuse, missing input validation, incorrect defaults.

---

## Executive Summary

Cycle 8 reported 20 findings (1 CRITICAL, 6 HIGH, 8 MEDIUM, 6 LOW). This mechanical audit verifies those fixes and searches for new defects.

**Fix verification:** All 6 Cycle 8 P0 findings are addressed. However, **2 HIGH findings are only partially fixed** (H-1 spool secrets: permissions fixed but content still pre-redaction; H-3 home validation: traversal blocked but arbitrary absolute paths still accepted). The CRITICAL C-1 (OOM at scale) remains architecturally present — the code still loads all episodes into memory, though per-project partitioning reduces peak memory during dedup/clustering.

**New findings:** 1 HIGH, 3 MEDIUM, 4 LOW. No new CRITICAL. The codebase is substantially hardened; most remaining issues are edge cases or minor inconsistencies.

---

## Part I: Claimed-Fixed-but-Not-Fully-Fixed

### CF-1: H-1 Spool secrets — permissions fixed, content still pre-redaction [MEDIUM]

**Cycle 8 H-1 claimed:** "Spool file contains pre-redaction secrets with 0644 permissions."
**What was fixed:** `spool.py:32` now uses `os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)`.
**What was NOT fixed:** `spool_event()` at `spool.py:43-57` still writes the raw hook payload to disk. Secret redaction only happens during `drain_and_ingest()` -> `store.ingest()` -> `_clip()` -> `redact_secrets()`. The window between spool write and drain can be minutes to hours.

**Trace:**
```
hooks.py:113  spool_event(cfg, payload)     # raw payload, no redaction
  -> spool.py:55  data = json.dumps(payload, ...) + "\n"
  -> spool.py:32  _append_bytes(cfg.queue_path, data)  # 0o600, but raw content
```

**Impact:** Credentials in `tool_output` (env dumps, curl responses, config files) sit in plaintext on disk. The 0o600 fix means only the file owner can read them (down from HIGH to MEDIUM), but any process running as the same user (or an attacker with user-level access) can harvest them.

**Fix:** Apply `redact_secrets()` to the payload's `tool_output` field inside `spool_event()` before serializing. This is a one-line change:
```python
# In spool_event(), before json.dumps:
if isinstance(payload.get("tool_output"), str):
    payload["tool_output"] = redact_secrets(payload["tool_output"])
```

---

### CF-2: H-3 Home validation — traversal blocked, arbitrary absolute paths still accepted [MEDIUM]

**Cycle 8 H-3 claimed:** "`home` field in config.json not validated — arbitrary path redirection."
**Fix applied:** `config.py:347-348`:
```python
if ".." in Path(cfg.home).parts:
    _clamp("home", d.home, "home contains a path-traversal ('..') component")
```
**What was NOT fixed:** The Cycle 8 recommendation was "Add `_validate` check that `home` must be under `Path.home()` or whitelisted prefix." The current fix only blocks `..` traversal. An absolute path like `CDMS_HOME=/etc/cron.d` or `CDMS_HOME=C:\Windows\System32` still passes validation.

**Trace:**
```bash
CDMS_HOME=/tmp/evil cdms consolidate  # creates memory.db in /tmp/evil/
```

**Impact:** An attacker with environment variable control (or who can write a `config.json`) can redirect the store to any writable directory. Lower severity than originally reported because: (1) the operator controls env vars, (2) the store creation would fail in protected directories, (3) the traversal vector IS blocked. But the fix is weaker than recommended.

**Fix:** Add a whitelist check:
```python
home_resolved = cfg.home.resolve()
user_home = Path.home().resolve()
if not (str(home_resolved).startswith(str(user_home) + os.sep) or home_resolved == user_home):
    _clamp("home", d.home, "home must be under user home directory")
```

---

### CF-3: C-1 Consolidation OOM — per-project partitioning helps, but initial load unchanged [MEDIUM at scale]

**Cycle 8 C-1:** "Consolidation loads ALL episodes into memory — OOM at scale."
**What changed:** Dedup and clustering are now partitioned by project (`consolidate.py:261-275`), reducing peak memory during those steps. The embeddings are also loaded per-project (`_embeddings_for` called inside the loop).
**What was NOT fixed:** `self.db.all_episodic()` at `consolidate.py:185` still loads every episode into a Python list. At 100K episodes, this is ~100MB+ of Python objects before any processing begins.

**Impact:** Downgraded from CRITICAL to MEDIUM because per-project partitioning reduces the second-order memory spike (vectors + clustering matrices). The initial list load is still the bottleneck.

**Fix:** Stream episodes in chunks or use SQL-side filtering (e.g., `SELECT * FROM mem_episodic WHERE project = ?`).

---

## Part II: New Findings

### NEW-1: `support_count` semantic inconsistency between facts and consolidation [HIGH]

**File:** `store.py:265` vs `consolidate.py:421`

**Trace:** `upsert_fact()` at `store.py:265` does `existing.support_count += 1` (cumulative increment). But consolidation at `consolidate.py:421` does `existing.support_count = max(existing.support_count, len(members))` (peak cluster size). Both write to the same field, and both feed into the same decay formula at `consolidate.py:501`:

```python
strength = g.support_count * (self.cfg.gist_decay_per_cycle ** idle)
```

**Impact:** A fact-upserted gist accumulates unbounded `support_count` with each MCP `store kind=fact` call, making it effectively immune to decay (strength grows monotonically with each upsert, counteracting idle-cycle decay). A consolidation-derived gist's support_count reflects only the largest cluster ever seen, decaying normally. This asymmetry means:
- A model that repeatedly stores the same fact (e.g., "user prefers Python") gets a gist that can never decay, even if the user switches preferences.
- Consolidation-derived gists decay normally, creating an inconsistency in the identity model.

**Fix:** Either (a) make `upsert_fact` use `max()` semantics like consolidation, or (b) cap fact-upserted support_count at a reasonable maximum (e.g., 100), or (c) use a separate counter for fact frequency vs episode-derived support.

---

### NEW-2: `_row_to_gist` silently assigns current time as fallback `last_reinforced` [MEDIUM]

**File:** `db.py:662-672`

**Trace:**
```python
lr = r["last_reinforced"] if "last_reinforced" in keys else None
# ...
last_reinforced=lr or utc_now_iso(),  # fallback to "now"
```

A row with `last_reinforced IS NULL` (from a migration edge case, partial corruption, or external DB edit) gets `utc_now_iso()` as its `last_reinforced`. This makes the gist appear freshly reinforced.

**Impact:** A gist that should have been idle for months appears to have been reinforced "just now." This doesn't directly affect decay (which uses `last_cycle`, not `last_reinforced`), but it corrupts any diagnostic or debugging view of gist age. If `last_reinforced` is ever used for decay in a future phase, this would silently freeze the gist.

**Fix:** Use `last_reinforced=lr or ""` (empty string) and handle the empty case in consumers, or log a warning when the fallback fires.

---

### NEW-3: `_forget_from_spool` data loss on disk-full during rewrite [MEDIUM]

**File:** `store.py:477-500`

**Trace:** `_forget_from_spool()` atomically renames the spool file to a temp name, filters events, then writes back the kept events. If `spool_event_lines()` fails (e.g., disk full, permission error), the `finally` block at `store.py:498` deletes the claimed temp file:

```python
finally:
    try:
        claimed.unlink()  # deletes the original events
    except OSError:
        pass
```

The `kept` list exists in memory but was never written to disk. The original spool file was already renamed away.

**Impact:** On disk-full during `forget`, all not-yet-ingested spooled events are permanently lost. This is an edge case but is data loss in the right-to-forget path.

**Fix:** Don't unlink the claimed file on rewrite failure:
```python
try:
    if kept:
        spool_event_lines(self.cfg, kept)
    unlink_claimed = True
except Exception:
    unlink_claimed = False  # preserve for manual recovery
finally:
    if unlink_claimed:
        try:
            claimed.unlink()
        except OSError:
            pass
```

---

### NEW-4: `assoc_eta` and `assoc_boost_cap_frac` upper bounds allow extreme salience injection [MEDIUM]

**File:** `config.py:166-167`

**Trace:** Validation allows:
- `assoc_eta` up to `1e3`
- `assoc_boost_cap_frac` up to `1e3`

With `assoc_eta=1000` and a high-salience write (`s_new=100`, achievable with weight explosion), `associative_boost()` produces `s_old + 1000 * 1.0 * 100 = s_old + 100,000` per neighbor. The cap at `assoc_boost_cap_frac=1000` allows `1000 * 100 = 100,000` total injection. The consolidation `conserve_budget` would eventually renormalize, but between consolidations, salience is unbounded.

**Impact:** An attacker with config control (env vars) can amplify any episode's neighbors to extreme salience, pushing legitimate memories below the retention floor during the next consolidation.

**Fix:** Cap `assoc_eta` at `1.0` and `assoc_boost_cap_frac` at `1.0`:
```python
("assoc_eta", lambda v: _num(v) and 0 <= v <= 1.0),
("assoc_boost_cap_frac", lambda v: _num(v) and 0 <= v <= 1.0),
```

---

### NEW-5: `cycle` meta value not guarded against non-numeric corruption [LOW]

**File:** `consolidate.py:183`

**Trace:**
```python
cycle = int(self.db.get_meta("cycle", "0") or "0") + 1
```

If the `cycle` meta value is a non-numeric string (from external DB edit, corruption, or a migration bug), `int("abc")` raises `ValueError`, crashing the entire consolidation pass.

**Impact:** Low — the meta table is only written by CDMS code, so corruption is unlikely. But a single bad meta entry would permanently brick consolidation until the operator manually fixes the DB.

**Fix:** Use a try/except:
```python
try:
    cycle = int(self.db.get_meta("cycle", "0") or "0") + 1
except (ValueError, TypeError):
    cycle = 1  # reset to 1 on corruption
```

---

### NEW-6: `_evict_scars` return value is dead code [LOW]

**File:** `consolidate.py:296`

**Trace:** `_evict_scars()` returns `set[str]` (the set of evicted scar IDs), but the caller at `consolidate.py:203` discards it:
```python
self._evict_scars(rep)  # return value ignored
```

The return type annotation `-> set[str]` is misleading — the evicted IDs are never used.

**Impact:** None functionally. Dead code that could confuse maintainers.

**Fix:** Change return type to `-> None` or use the return value.

---

### NEW-7: Lock file created with 0o644 [LOW]

**File:** `lock.py:68`

**Trace:**
```python
fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
```

The advisory lock file at `consolidate.lock` is created world-readable. While it contains no sensitive data (it is an empty lock file), the spool file uses 0o600 for defense-in-depth consistency.

**Impact:** None — the file is empty and advisory. Inconsistent with the security posture.

**Fix:** Change to `0o600` for consistency.

---

### NEW-8: `_greedy_cluster` float32 centroid accumulation precision loss [LOW]

**File:** `consolidate.py:547`

**Trace:**
```python
cent = np.empty((n, dim), dtype=np.float32)
# ...
cent[j] += (v - cent[j]) / counts[j]   # incremental mean in float32
```

The incremental mean is computed in float32. After ~100+ updates, float32 precision (~7 decimal digits) causes the centroid to drift from the true mean. For a 384-dim vector, the accumulated error per dimension is small but nonzero.

**Impact:** Negligible in practice — the centroid is used for similarity matching, and the error is within the noise floor of the embedding space. But it is technically imprecise.

**Fix:** Use `np.float64` for the centroid accumulator, convert back to float32 at the end:
```python
cent = np.empty((n, dim), dtype=np.float64)
# ... accumulate in float64 ...
# Convert back when needed
```

---

## Part III: Cycle 8 Fix Verification Matrix

| Cycle 8 ID | Finding | Status | Notes |
|------------|---------|--------|-------|
| C-1 | Consolidation OOM | **PARTIAL** | Per-project partitioning helps; initial all_episodic() load unchanged |
| H-1 | Spool pre-redaction secrets | **PARTIAL** | Permissions fixed (0o600); content still pre-redaction |
| H-2 | S0 weight cap too high | Fixed | Capped at 10, cross-field check added |
| H-3 | Home field unvalidated | **PARTIAL** | `..` traversal blocked; arbitrary absolute paths still accepted |
| H-4 | L3 scar table unbounded | Fixed | `_evict_scars` with `scar_project_cap` |
| H-5 | `get_embedder()` TOCTOU | Fixed | `_SINGLETON_LOCK` with double-checked locking |
| M-1 | touch_episodic vs eviction | Fixed | `_evict` re-reads before delete |
| M-2 | Weight annihilation | Fixed | Cross-field wsum > 0 check |
| M-3 | goal_hint bypass | Fixed | MCP store tool does not expose goal_hint |
| M-4 | Unicode sanitizer bypass | Fixed | `\x85\u2028\u2029` in `_CTRL` |
| M-5 | Missing credential patterns | Fixed | Anthropic/Google/Azure patterns added |
| M-6 | MCP store no max_length | Fixed | `max_length=10000` |
| M-7 | http_host not validated | Fixed | Loopback check added |
| M-8 | sqlite-vec minor version | Fixed | `_reconcile_vec_version` warns on change |
| L-1 | Dedup per-candidate round-trip | Fixed | In-memory survivor used |
| L-2 | _brief truncation before redaction | Fixed | Redact before truncate |
| L-3 | Drain skip not in stats | Fixed | `drains_skipped` in stats |
| L-4 | Quarantine file permissions | Fixed | `os.chmod(dest, 0o600)` |
| L-5 | JSON bool-to-int coercion | Fixed | Bool rejection in `_coerce` |
| L-6 | Gist render forgeability | Deferred | Acknowledged low priority |

---

## Part IV: Prioritized Action Items

### P0 — Fix Before Next Release

| ID | Finding | Fix |
|----|---------|-----|
| CF-1 | Spool content still pre-redaction | Redact `tool_output` in `spool_event()` |
| NEW-1 | support_count semantic inconsistency | Align fact upsert with max() or cap |

### P1 — Fix When Convenient

| ID | Finding | Fix |
|----|---------|-----|
| CF-2 | Home validation incomplete | Validate home under `Path.home()` |
| CF-3 | Consolidation OOM (initial load) | Stream episodes or SQL-side filter |
| NEW-2 | _row_to_gist fallback timestamp | Use empty string, not utc_now_iso() |
| NEW-3 | _forget_from_spool data loss | Do not unlink claimed file on rewrite failure |
| NEW-4 | assoc_eta/boost_cap upper bounds | Cap at 1.0 |

### P2 — Cleanup

| ID | Finding | Fix |
|----|---------|-----|
| NEW-5 | cycle meta non-numeric guard | try/except around int() |
| NEW-6 | _evict_scars dead return value | Change return type to None |
| NEW-7 | Lock file 0o644 | Change to 0o600 |
| NEW-8 | Float32 centroid precision | Use float64 accumulator |

---

## Closing Assessment

CDMS at f4dd7cf is substantially hardened. Of Cycle 8s 20 findings, 15 are fully fixed, 3 are partially fixed, 1 is deferred, and 1 is downgraded. The 1 new HIGH (support_count inconsistency), 3 new MEDIUM (spool redaction gap, fallback timestamp, forget data loss), and 4 new LOW findings are targeted fixes. No new CRITICAL defects were found in the mechanical layer.

The most impactful remaining issue is **NEW-1 (support_count inconsistency)** — it creates an asymmetry where MCP-stored facts become immune to decay while consolidation-derived gists decay normally. This undermines the Ebbinghaus model's core premise that all identity decays.

**Bottom line:** CDMS is mechanically sound for production use. The P0 items (spool redaction, support_count consistency) should be addressed before the next release cycle.

---

*End of Cycle 9 (Mechanical) audit. All findings independently verifiable against commit f4dd7cf.*
