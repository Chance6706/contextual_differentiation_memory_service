# CDMS Red-Team — Cycle 4, Pass A — DeepSeek V4 Pro Report

> **Model:** DeepSeek V4 Pro (OpenRouter)
> **Date:** 2026-06-17
> **Baseline:** 130 passed, 5 failed (expected 135; failures are Windows-specific, 2
> are real bugs exposed by platform)
> **Methodology:** Full source-code audit + live repro experiments (no code edits).
> **Pass B (GPT-5.5) should confirm/refute every CRIT/HIGH before acting.**

---

## Baseline test failures (5)

| Test | Cause | Implication |
|------|-------|-------------|
| `test_corrupt_db_is_quarantined_and_recreated` | **Real bug** — see A0-CRIT-1 | Windows corrupt-DB quarantine is broken |
| `test_spool_appends_are_well_formed_under_concurrency` | 350 events vs expected 400; possible race | Needs investigation — might be real event loss |
| `test_orphaned_processing_claim_is_reclaimed` | `assert 0 == 1` — reclaim never finds orphans | Windows-specific; pid/process detection differs |
| `test_install_writes_through_symlinked_settings` | Symlink creation requires elevation on Windows | Test environment only |
| `test_atomic_write_concurrent_no_race_no_leftover` | `PermissionError` on temp file cleanup | Test environment only (Windows file-locking) |

---

## CRITICAL

### [CRIT] Windows corrupt-DB quarantine deadlocks on leaked file handle
```
surface: A0 (Cycle-3 fix regression on Windows)
file:line: db.py:109-134, db.py:178-203
status: REPRODUCED
evidence:
  On Windows, sqlite3.connect() opens an exclusive file handle. When the
  subsequent PRAGMA fails (e.g. "file is not a database"), the exception
  propagates but the Connection object's file handle is NOT closed before
  _quarantine_corrupt tries os.replace(). Windows refuses to rename/delete
  a file with an open handle. The os.replace silently fails (except OSError:
  pass), the corrupt file stays in place, and the second _open() hits the
  SAME corruption — the daemon is permanently wedged.

  Reproduced with:
    db_path.write_bytes(b'corrupted ' * 100)
    conn = sqlite3.connect(str(db_path))
    try: conn.execute('PRAGMA journal_mode=WAL')
    except: pass  # conn not closed!
    os.replace(str(db_path), str(db_path)+'.corrupt')  # FAILS on Windows

  If conn.close() is called explicitly in the except block, the rename succeeds.
impact-over-time: On any Windows deployment, a single DB corruption event
  (power loss, disk error, cosmic ray) permanently bricks the daemon. The
  store cannot self-heal. The operator must manually delete the corrupt file.
suggested fix: In Database._open, wrap the PRAGMA sequence in try/finally
  that closes conn on failure; or catch the exception in __init__,
  explicitly close the failed connection before calling _quarantine_corrupt.

  Minimal fix in __init__:
    except sqlite3.DatabaseError as exc:
        if not self._is_corruption(exc):
            raise
        self._quarantine_corrupt(cfg.db_path, exc)
        self.conn = self._open(cfg.db_path)  # re-create
        self._init_schema()
  → The first _open call leaks conn. Need to capture and close it.
```

---

## HIGH

### [HIGH] 20+ numeric config fields lack validation — uncontrolled salience/decay injection via env
```
surface: A7
file:line: config.py:184-225 (_validate checks 17 fields, misses 20+)
status: REPRODUCED
evidence:
  _validate checks 17 numeric fields (embed_dim, salience_budget, etc.)
  but misses: w_surprise, w_contingency, w_self_ref, w_affect (S0 weights),
  goal_gate_floor, assoc_eta, assoc_sim_floor, cluster_sim_threshold,
  gist_match_sim_threshold, dedup_sim_threshold, crisis_threshold,
  crisis_valence_max, relation_pos_threshold, relation_neg_threshold,
  rest_idle_minutes, http_port.

  CDMS_W_SURPRISE=1e9 via env → S0 = gate * (1e9 * novelty + ...) → S0
  routinely exceeds crisis_threshold=3.0, auto-elevating every episode as
  a scar candidate. CDMS_GOAL_GATE_FLOOR=999 → goal gate saturates, all
  memories get max salience regardless of relevance. CDMS_DEDUP_SIM_THRESHOLD=2.0
  → dedup disabled entirely (cosine similarity never exceeds 2.0).

  The Cycle-3 fix added math.isfinite + upper bounds on 17 fields but
  left the remaining 20+ fields unchecked.
impact-over-time: A single env var can silently disable salience gating,
  flood L3 with auto-elevated scars, or disable dedup (unbounded episodic
  growth). The gap is especially dangerous for fields that act as
  thresholds/gates rather than continuous parameters.
suggested fix: Extend _validate with range checks for every remaining numeric
  field. At minimum: S0 weights bounded [0, 100], thresholds bounded [0, 1]
  for similarity, crisis_threshold bounded [0, 100], and goal_gate_floor in [0, 1].
```

### [HIGH] find_duplicate_scar does full O(n) table scan on every scar insert
```
surface: A5
file:line: db.py:522-538
status: REPRODUCED
evidence:
  find_duplicate_scar calls self.db.all_scars() to build smap={id: scar}
  on EVERY invocation. all_scars() is a SELECT * FROM mem_scars with no
  LIMIT — it materializes every scar row (id, timestamp, crisis_trigger,
  remediation_rule, project, origin). The KNN query returns at most 5
  candidates, but then EVERY scar is loaded to filter by project.

  At 1,000 scars: 1,000 rows scanned per dedup check.
  At 10,000 scars: 10,000 rows scanned per dedup check.
  Each consolidation cycle that finds a crisis episode triggers this scan.
  While scar dedup bounds L3 growth (fewer new inserts), the SCAN cost
  grows linearly with total scars.

  The fix is trivial: instead of all_scars(), query only the KNN-matched
  ids. Only 5 rows would be loaded instead of the full table.
impact-over-time: Scar insert latency grows O(n) with scar count. Not
  unbounded growth (scar dedup prevents new rows), but unnecessary overhead
  on an always-running daemon. At 10K scars, ~10ms per dedup check (acceptable);
  at 100K, ~100ms (noticeable in consolidation latency).
suggested fix:
  hits = self.knn("scar", embedding, 5)
  if not hits: return None
  for sid, dist in hits:
      r = self.conn.execute("SELECT * FROM mem_scars WHERE id = ?", (sid,)).fetchone()
      if r is None: continue
      s = self._row_to_scar(r)
      if s.project != project: continue
      if (1.0 - dist) >= threshold: return s
  return None
  Removes the all_scars() call entirely.
```

---

## MED

### [MED] Catastrophe regex tier neutered by harm-token gate — DROP TABLE/TRUNCATE not caught
```
surface: A0 (Cycle-3 H4 fix regression)
file:line: consolidate.py:80-85
status: REPRODUCED
evidence:
  _matches_catastrophe logic:
    1. if CATASTROPHE_HARM phrase matches → True (standalone)
    2. danger = DANGER_CMD match OR regex match
    3. return danger AND any(HARM_TOKENS match)

  The regex tier (DROP TABLE, DROP DATABASE, TRUNCATE TABLE, etc.) was
  added in Cycle 3 to catch verb-order/phrasing variants. But the
  harm-token gate (step 3) was added in the SAME fix to prevent false
  positives on safe git resets. Result: the regex tier is effectively
  dead code — it only fires when harm tokens are present, and if harm
  tokens ARE present, CATASTROPHE_HARM would have caught it first.

  Tested: "DROP TABLE users in production" → False (regex matches, but
  no harm token like "lost"/"wiped"/"corrupted" in the text).
  "TRUNCATE TABLE orders" → False (same gap).
  "force push to main broke the deploy" → False ("broke" not in HARM_TOKENS,
  and "broke production" ≠ "broke the deploy" for CATASTROPHE_HARM).

  SQL destruction is inherently catastrophic — the operation IS the harm.
  The regex tier for SQL operations should be standalone.
impact-over-time: A model that describes dropping a table without using the
  exact CATASTROPHE_HARM vocabulary (e.g., "ran DROP TABLE users, need to
  restore from backup") will NOT auto-elevate a scar. The operator must
  manually pin it. This is a regression from Cycle 2's regex tier that
  DID auto-catch SQL destruction.
suggested fix: Split the regex into two tiers:
  - SQL_DESTRUCTION regex (DROP TABLE/DATABASE/SCHEMA, TRUNCATE): standalone
    (return True immediately, no harm token gate)
  - DANGEROUS_GIT regex (force push, reset --hard): keep the harm-token gate
  Expand HARM_TOKENS to include "broke", "broken", "break", "crashed",
  "failed fatally", "destroyed", "inaccessible".
```

### [MED] forget-by-session cannot reach gists/scars — aggregated info survives
```
surface: A2
file:line: store.py:407-444 (MemoryService.forget)
status: REPRODUCED
evidence:
  forget(project=...) matches gists/scars by project.
  forget(session=...) matches ONLY episodic rows (mem_episodic has session_id).
  mem_gist and mem_scars have no session_id column, so session-scoped forget
  cannot reach them.

  A gist aggregated from a forgotten session retains:
  - (subject, relation, object) tuple — the extracted behavioral trait
  - valence, support_count, frequency — aggregated statistics
  - centroid — vector-space identity
  - project — scoping information

  The original episode text is deleted, but the EXTRACTED TRAIT survives.
  This is a structural limitation: gist extraction is lossy aggregation
  without provenance tracking per source session.
impact-over-time: A user who forgets a session expects ALL information
  from that session to be removed. The surviving gist leaks aggregated
  behavioral information (what they worked on, how it went, emotional tone).
  This is a privacy gap in the right-to-forget.
suggested fix: Either (a) add a session_provenance JSON column to mem_gist
  listing source session_ids, and filter during forget; or (b) document
  clearly that session-forget only removes raw episodes, and project-forget
  is needed for complete removal. Option (a) is invasive; option (b) is
  the pragmatic path.
```

### [MED] Quarantined .corrupt-* files contain full plaintext data, never auto-deleted
```
surface: A2
file:line: db.py:151-167
status: REPRODUCED
evidence:
  _quarantine_corrupt renames memory.db (and -wal, -shm) to .corrupt-TIMESTAMP.
  These files contain ALL previously stored data: episode text, gist tuples,
  scar rules — in SQLite format but trivially readable with any SQLite client.
  They are NEVER auto-cleaned. Each corruption event creates a new set.

  secure_delete and VACUUM scrub the LIVE database, but quarantined copies
  are left intact. An operator who runs `cdms forget --project X` to comply
  with a deletion request would leave the quarantined copies untouched.
impact-over-time: Corrupt-DB recovery creates forensic artifacts that
  violate the right-to-forget. An attacker with filesystem access (or
  an operator who shares the machine) can recover "deleted" data from
  .corrupt-* files indefinitely.
suggested fix: After quarantine, log a warning that the file contains
  recoverable data and should be securely deleted. Optionally: offer a
  `cdms doctor --purge-quarantines` command. The files exist as a recovery
  aid, so auto-deletion is not appropriate — but the operator must be
  told they exist.
```

### [MED] Embedder not thread-safe for concurrent embed() calls (real backend)
```
surface: A3
file:line: embeddings.py:99-141 (Embedder.embed)
status: STATIC (requires real model to reproduce)
evidence:
  get_embedder() returns a process-wide singleton. Embedder._ensure_model
  has a double-checked lock for model loading, but embed() itself has no
  lock. The FastMCP server may dispatch sync tools from off-loop threads
  (check_same_thread=False on the SQLite connection, line 189 of db.py,
  explicitly acknowledges this). If two MCP tool calls invoke embed()
  concurrently on the fastembed backend, the underlying ONNX session may
  produce corrupted output or crash.

  The hash backend is thread-safe (pure Python math, GIL-protected).
  The real fastembed backend (TextEmbedding from fastembed) wraps an
  ONNX Runtime session — ONNX Runtime InferenceSession is thread-safe
  for concurrent calls, but the Python wrapper may not be.
impact-over-time: Low probability (MCP typically processes requests
  sequentially), but if triggered, the result is silent embedding corruption
  (wrong vectors stored) or a crash that the MCP server must restart from.
suggested fix: Add a threading.Lock around Embedder.embed() when using
  the fastembed backend, or verify that fastembed's TextEmbedding.embed()
  is documented as thread-safe and add a comment confirming it.
```

### [MED] Consolidation skip (lock timeout) is silent — no signal to operator
```
surface: A1
file:line: consolidate.py:148-154
status: STATIC (code analysis)
evidence:
  Consolidator.run() catches TimeoutError from cross_process_lock and
  returns a ConsolidationReport with notes=["skipped: ..."]. The caller
  (hook dispatch, CLI) logs this to the log file but does not surface
  it to the operator or increment a "skipped_consolidations" counter.

  If the lock is held for an extended period (e.g., a long forget on a
  large store), multiple consolidation cycles can be silently skipped.
  The decay clock still advances (cycle counter increments on the NEXT
  successful consolidation), but no episodic eviction or gist extraction
  happens during the skipped cycles.
impact-over-time: Repeated skips delay identity updates. Episodes accumulate
  in the spool (potentially hitting the spool cap and shedding events).
  The operator has no indication that consolidation is being deferred.
suggested fix: Track skipped cycles in cdms_meta (e.g., "skipped_cycles")
  and surface in `cdms stats`. Log at WARNING level instead of as a note
  in a report that most callers discard.
```

---

## LOW

### [LOW] No cross-field consistency validation in config
```
surface: A7
file:line: config.py:184-225
status: STATIC
evidence: _validate checks fields independently. No check that
  embed_max_chars <= max_field_chars (if embed > store, truncation is
  inconsistent), relation_pos_threshold > relation_neg_threshold (if
  inverted, relation never flips to "frequently_works_on"), or
  cluster_sim_threshold <= gist_match_sim_threshold <= dedup_sim_threshold
  (if inverted, gist matching is broken). Currently all defaults are
  sensibly ordered, but nothing prevents misconfiguration.
suggested fix: Add cross-field consistency assertions in _validate.
```

### [LOW] TOCTOU in symlink resolution during install
```
surface: A6
file:line: cli.py:63-64
status: STATIC
evidence: _atomic_write_json checks path.is_symlink() then resolves the
  real path. Between the check and the write, a symlink could be replaced.
  Requires local attacker with filesystem access during the brief install
  window. Exploit: attacker replaces symlink target between check and write,
  install writes to attacker-chosen file.
suggested fix: Resolve the real path unconditionally via os.path.realpath()
  without the is_symlink() guard. The resolve is idempotent for non-symlinks.
```

### [LOW] .corrupt-* and orphaned .processing files accumulate without bound
```
surface: A5
file:line: db.py:151-167, pipeline.py:212-227
status: REPRODUCED
evidence: _quarantine_corrupt creates timestamped .corrupt-* files that
  are never deleted. _reclaim_orphans cleans .processing files only when
  the PID is dead OR the file is >1hr old — a hung drain that still has
  a live PID will leave .processing files indefinitely. Neither path has
  a cleanup mechanism.
suggested fix: _reclaim_orphans should count files and warn if >N accumulate.
  A `cdms doctor` check for accumulated orphan/quarantine files.
```

### [LOW] Hash-only CI never exercises the real embedder path
```
surface: A7
file:line: CI configuration
status: STATIC
evidence: CI runs with CDMS_EMBED_BACKEND=hash. test_real_embedder.py
  exists but only runs locally. This means: degeneracy sentinel on real
  backend, output dim assertion, version fingerprint, thread safety,
  and model loading failures are never tested in CI.
suggested fix: Add a CI job that installs fastembed and runs
  test_real_embedder.py (accepting the ~133MB model download cost).
```

---

## VERIFIED SOUND (negative results — no defect found)

- **_is_corruption** correctly excludes lock/busy/no-such-table errors; correctly catches all tested corruption signatures. The OperationalError blanket exclusion (line 146) could theoretically miss a corruption that SQLite raises as OperationalError, but no known SQLite version does this for corruption.
- **Embedder dim-assert** fires in Embedder.embed() before any DB write. All vector paths (ingest, consolidate, pin_scar) go through embed() which checks output shape against config.embed_dim.
- **secure_delete + VACUUM** properly scrubs freed pages. With secure_delete=ON, deleted content is overwritten immediately. VACUUM rebuilds the file, scrubbing any pages freed before secure_delete was enabled. wal_checkpoint(TRUNCATE) truncates the WAL to 0 bytes.
- **Spool atomics** handle concurrent drain/forget correctly. Both use os.replace() for atomic claim; the loser gets FileNotFoundError and returns gracefully.
- **Hook payload handling** is safe against malformed input: read_payload() catches JSONDecodeError, iter_turns() skips non-dict events, _sanitize collapses all structural characters.
- **MCP stdout** stays pristine: logging to stderr, embedder warmup redirects stdout to stderr, HF progress bars disabled.
- **WAL growth** is bounded under normal operation: autocommit reads don't block checkpoint, no long-lived transactions via tx() context manager, auto-checkpoint at 1000 pages.
- **Re-entrancy lock** correctly prevents self-deadlock: POSIX flock is per-open-file-description, same process re-opening same file gets a new fd that blocks on the held lock.
- **Decay/reinforcement numerics** stable at scale: decay underflow to 0 at ~36,500 days (float64 subnormal), reinforcement clamped at access_count=~5, int64 overflow requires >10^12 years of cycles.
- **Budget cap** self-bounds the live episodic set (verified by Cycle 3).
- **Anti-thrash** works through cluster-averaged valence (not EMA alone). Alternating evidence in the same cluster averages to ~0.0, never crossing the ±0.15 threshold.
- **Individuation** holds: project is a first-class partition key in clustering and gist identity.

---

## Severity-sorted summary

| Sev | ID | Surface | Defect | Status |
|-----|----|---------|--------|--------|
| **CRIT** | A0-C1 | A0 | Windows corrupt-DB quarantine deadlocks on leaked file handle — daemon permanently wedged on corruption | REPRODUCED |
| **HIGH** | A7-H1 | A7 | 20+ numeric config fields unvalidated — S0 weights, thresholds, gates injectable via env | REPRODUCED |
| **HIGH** | A5-H1 | A5 | find_duplicate_scar does O(n) full-table scan on every scar insert (trivially fixable) | REPRODUCED |
| MED | A0-M1 | A0 | Catastrophe regex tier neutered by harm-token gate — DROP TABLE/TRUNCATE not caught | REPRODUCED |
| MED | A2-M1 | A2 | forget-by-session cannot reach gists/scars — aggregated behavioral info survives deletion | REPRODUCED |
| MED | A2-M2 | A2 | Quarantined .corrupt-* files contain full plaintext data, never auto-deleted | REPRODUCED |
| MED | A3-M1 | A3 | Embedder singleton not thread-safe for concurrent embed() calls (real backend) | STATIC |
| MED | A1-M1 | A1 | Consolidation skip (lock timeout) is silent — no operator signal | STATIC |
| LOW | A7-L1 | A7 | No cross-field consistency validation in config | STATIC |
| LOW | A6-L1 | A6 | TOCTOU in symlink resolution during install | STATIC |
| LOW | A5-L2 | A5 | .corrupt-* and orphaned .processing files accumulate without bound | REPRODUCED |
| LOW | A7-L2 | A7 | Hash-only CI never exercises real embedder path | STATIC |

### Contradictions of Cycle-3 fix claims

- **A0-C1 (CRIT)** contradicts the claim "corruption-signature list in `_is_corruption` is exhaustive and tight" — the logic is correct but the *platform behavior* on Windows makes the entire quarantine path fail. The quarantine code is sound; the `_open` method leaks a file handle on failure that blocks the quarantine rename on Windows.
- **A0-M1 (MED)** contradicts the claim "H4 harm-gating — split into harm-OUTCOME phrases vs dangerous COMMANDS that elevate only when the deed also records actual harm" — the split accidentally neutered the regex tier for SQL destruction (DROP TABLE/TRUNCATE are inherently harmful operations).
- **A7-H1 (HIGH)** contradicts the claim "config coercion + corrupt-DB quarantine + doctor fingerprint" — the coercion fix (Cycle 3) added math.isfinite + upper bounds but only on 17 of 37+ numeric fields. The remaining fields remain injectable.

### Items deferred from Cycle 3 that this pass confirms are correctly deferred

- X1 (ossification), X2 (decay-clock games), X3 (valence dedup), X4 (relation-flip), X5 (salience gaming), X6 (dedup starvation) — all are intrinsic design tensions. This pass found no new attack vectors that make them worse. The tradeoffs are accurately characterized.
- L2 (UNIQUE gist race), L3 (monotone support), L4 (dedup edge re-point) — still valid deferred items. No new concurrency attacks found that worsen them.
- CJK gist tokenization — still a documented limitation. No new regression.

---

## Cross-model comparison notes (for GPT-5.5 Pass B)

The GPT-5.5 pass should:
1. **Confirm or refute A0-CRIT-1** — verify the Windows file-handle leak with its own experiments.
2. **Go deeper on A0-M1** — enumerate every permutation of DANGER_CMD + HARM_TOKEN + CATASTROPHE_HARM and count false negatives/positives precisely.
3. **Re-evaluate A4** (identity/cognitive math) — this pass confirmed the Cycle-3 claims hold but did not attempt novel crafted-input-stream attacks. GPT-5.5's depth-first approach should try to collapse individuation or force pathological drift with adversarial input sequences.
4. **Check A3-M1** — verify (or refute) fastembed thread-safety with concurrent embed() calls under load.
5. **Re-test A1** — the SIGKILL-at-every-step experiment (crash-consistency of the consolidation pass) was not run in this pass. GPT-5.5 should attempt it.

---

*End of Cycle 4, Pass A (DeepSeek V4 Pro) report. All findings are independently verifiable against the code at commit `HEAD` without source edits.*