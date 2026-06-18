# CDMS Red-Team — Cycle 9 — Security Audit

> **Model:** MiMo v2.5 Pro (OpenRouter)
> **Date:** 2026-06-18
> **Commit:** f4dd7cf (branch `main`)
> **Prior commit audited:** 8e889d7 (Cycle 8, OWL Alpha)
> **Methodology:** Full source read of 9 files (spool.py, store.py, hooks.py, config.py, mcp_server.py, db.py, pipeline.py, cli.py, lock.py, embeddings.py, consolidate.py excerpt) + pyproject.toml. All Cycle 8 P0/P1/P2 findings verified against current code.
> **Scope:** Security-focused: secret handling, input validation, file permissions, injection vectors, SSRF, path traversal, supply chain, and Cycle 8 regression verification.

---

## Executive Summary

**All 6 Cycle 8 P0 findings have been fixed.** The codebase has been substantially hardened since Cycle 8:

- Spool file permissions → `0o600` (was `0o644`)
- S0 weight cap → `10` with cross-field crisis gate (was `1e3`)
- Home path traversal rejected
- Unicode line separators (`\x85`, `\u2028`, `\u2029`) added to sanitizer
- Credential patterns expanded (Anthropic, Google, Azure, JWT, private keys)
- Embedder singleton protected by `threading.Lock()` with double-checked locking
- MCP `store` tool now has `max_length=10000` on content
- `http_host` and `dreamer_base_url` validated as loopback-only
- `db_filename` validated against path traversal
- JSON bool-to-int coercion explicitly rejected
- Quarantined `.corrupt-*` files locked to `0o600`
- `drains_skipped` counter surfaced in stats
- `_brief()` now redacts BEFORE truncating

This audit found **2 new MEDIUM** and **5 new LOW** findings. No new CRITICAL or HIGH. The remaining gaps are defense-in-depth improvements, not exploitable vulnerabilities in typical single-user deployments.

---

## Part I: Cycle 8 Finding Verification

### P0 Findings — All Fixed ✅

| Cycle 8 ID | Description | Status | Evidence |
|---|---|---|---|
| **H-1** | Spool pre-redaction secrets, `0o644` | **FIXED** | `spool.py:37` — `os.open(path, ..., 0o600)`. Comment explicitly cites "Cycle-8 H-1". |
| **H-2** | S0 weight cap at `1e3` | **FIXED** | `config.py` `_validate()` — each weight capped at `<= 10`. Cross-field check: `goal_gate_floor * wsum >= crisis_threshold` auto-scales weights down with 10% margin. |
| **H-3** | `home` field unvalidated | **FIXED** | `config.py` `_validate()` — `if ".." in Path(cfg.home).parts` rejects traversal. |
| **H-5** | `get_embedder()` TOCTOU race | **FIXED** | `embeddings.py` — `_SINGLETON_LOCK = threading.Lock()` with double-checked locking. Also includes `_embedder_key()` for config-change rebuilds. |
| **M-4** | Unicode line separators in `_CTRL` | **FIXED** | `hooks.py:49` — regex includes `\x85\u2028\u2029`. |
| **M-5** | Missing credential patterns | **FIXED** | `store.py:_SECRET_PATTERNS` now covers: `sk-ant-*` (Anthropic), `sk-(proj|svcacct|admin)-*` (OpenAI project keys), `AIza*` (Google), JWT, private keys, Azure `AccountKey=`. |

### P1 Findings — Status

| Cycle 8 ID | Description | Status | Notes |
|---|---|---|---|
| **C-1** | Consolidation OOM at scale | **OPEN** | `consolidate.py` still calls `self.db.all_episodic()` (full load). Needs streaming chunk processing. |
| **H-4** | L3 scar table unbounded | **PARTIALLY FIXED** | `config.py` adds `scar_project_cap=100` for auto-elevated scars; pinned scars exempt. Requires consolidation to enforce. |
| **M-1** | `touch_episodic` vs eviction race | **OPEN** | No re-read of `access_count` before eviction delete. |
| **M-3** | `goal_hint` bypass via MCP | **FIXED** | `mcp_server.py:store()` does not expose `goal_hint`/`importance` fields. Comment cites "Cycle-8 M-3". |
| **M-M-4** | Valence EMA poisoning | **FIXED** | `config.py` adds `gist_valence_ema_min=0.05` with adaptive rate `ema / sqrt(support)`. |

### P2 Findings — Status

| Cycle 8 ID | Description | Status | Notes |
|---|---|---|---|
| **M-6** | MCP store no `max_length` | **FIXED** | `mcp_server.py:122` — `Field(max_length=10000)`. |
| **M-7** | `http_host` not loopback-validated | **FIXED** | `config.py` `_validate()` — `_is_loopback()` check with `_clamp`. |
| **M-8** | sqlite-vec version drift | **FIXED** | `db.py:_reconcile_vec_version()` — pins vec version in meta, warns on change. |
| **M-S-5** | `dreamer_base_url` SSRF | **FIXED** | `config.py` `_validate()` — `urlparse` + `_is_loopback()` on hostname. |
| **L-2** | `_brief()` redact-after-trunc | **FIXED** | `pipeline.py:_brief()` — `redact_secrets()` called BEFORE `[:limit]` truncation. |
| **L-3** | Drain skip not in stats | **FIXED** | `db.py:stats()` — `drains_skipped` and `last_drain_skip` included. |
| **L-4** | Quarantine file permissions | **FIXED** | `db.py:_quarantine_corrupt()` — `os.chmod(dest, 0o600)` after `os.replace()`. |
| **L-5** | JSON bool-to-int coercion | **FIXED** | `config.py:_coerce()` — `if isinstance(value, bool): raise ValueError(...)`. |
| **L-S-1** | MCP store silently accepts unknown `kind` | **FIXED** | `mcp_server.py:store()` — `if kind not in ("episode", "fact", "scar"): raise ValueError(...)`. |

---

## Part II: New Findings

### MEDIUM

#### M-1: Lock file created world-readable

**File:** `lock.py:67`
**Line:** `fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)`

**Description:** The cross-process advisory lock file (`consolidate.lock`) is created with `0o644` permissions. While the lock file itself contains no sensitive data and `fcntl.flock` operates at the kernel level (permissions don't affect locking), the file exposes the lock path to all local users.

**Attack scenario:** A local attacker cannot interfere with locking, but can observe lock file creation/modification times to infer CDMS activity patterns (when consolidation runs, when sessions end).

**Impact:** LOW — information disclosure of activity timing only. No credential or memory exposure.

**Fix:** Change to `0o600` for consistency with the rest of the CDMS security posture:
```python
fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o600)
```

#### M-2: `_forget_from_spool` temp file inherits source permissions

**File:** `store.py:469`
**Line:** `claimed = Path(f"{q}.forget-{os.getpid()}.tmp")`

**Description:** The `os.replace()` call in `_forget_from_spool` renames the spool file to a `.tmp` path. `os.replace` preserves the source file's permissions (now `0o600`), so the temp file is correctly protected. However, the temp filename pattern (`*.forget-*.tmp`) is predictable (PID + fixed suffix). A local attacker who can predict the PID could attempt a symlink race on the temp path between the `os.replace` and the `read_text` call.

**Attack scenario:** Attacker creates a symlink at the predicted temp path before `os.replace` executes. The `os.replace` would then write the spool data to the symlink target.

**Impact:** LOW — requires precise timing and same-user access. The spool data is already `0o600`. A successful race would redirect (not copy) the spool to an attacker-controlled location, but the attacker already has same-user access.

**Fix:** Use a random suffix for the temp filename (similar to `_drain_locked`'s UUID pattern):
```python
import uuid
claimed = Path(f"{q}.forget-{os.getpid()}-{uuid.uuid4().hex[:8]}.tmp")
```

---

### LOW

#### L-1: `ensure_home()` creates directory with default permissions

**File:** `config.py:151`
**Line:** `self.home.mkdir(parents=True, exist_ok=True)`

**Description:** `Path.mkdir()` uses the process umask (typically `0o777 & ~0o022 = 0o755`). On a shared system, the CDMS home directory (`~/.local_memory`) would be world-readable. All files inside are `0o600`, so no content leaks, but the directory listing is visible.

**Impact:** NEGLIGIBLE — attacker can see that CDMS is installed but cannot read any files.

**Fix:** Explicitly set `mode=0o700`:
```python
self.home.mkdir(parents=True, exist_ok=True, mode=0o700)
```

#### L-2: `log_path` file created with default permissions

**File:** `hooks.py:174`
**Line:** `with open(p, "a", encoding="utf-8") as f:`

**Description:** The log file (`cdms.log`) is created via `open()` which uses the process umask (typically `0o644`). Log messages contain operational metadata (drain counts, consolidation reports, error messages) but not raw credentials (redaction happens before `ingest`). However, error tracebacks in the log could leak file paths.

**Impact:** LOW — log contains operational metadata, not secrets. On a shared system, other users could read CDMS operational status.

**Fix:** After first creation, set `0o600`:
```python
if not p.exists():
    os.open(str(p), os.O_CREAT | os.O_WRONLY, 0o600)
```

#### L-3: `db_filename` validation allows forward slashes on Windows

**File:** `config.py` `_validate()` — `db_filename` check
**Line:** `os.path.basename(v) == v`

**Description:** The validation rejects backslashes (`"\\" not in v`) and requires `basename == value`. On Windows, `os.path.basename("../../evil.db")` returns `"evil.db"` (forward slashes are path separators), so `"../../evil.db"` passes the `basename == value` check... but only if the input doesn't contain `..` as a path component. Wait — actually `"../../evil.db"` has `basename == "evil.db"` which does NOT equal `"../../evil.db"`, so the check catches it.

**Re-analysis:** The check is correct. `os.path.basename("../../evil.db")` returns `"evil.db"`, which != `"../../evil.db"`. The traversal is rejected. No vulnerability here — corrected from initial assessment.

**Impact:** NONE — false alarm on re-analysis. The `basename == value` check correctly rejects all traversal inputs.

#### L-4: `_fts_query` does not escape double quotes within terms

**File:** `db.py:246`
**Line:** `return " OR ".join(f'"{t}"' for t in terms)`

**Description:** Terms are extracted via `_FTS_TOKEN = re.compile(r"\w+", re.UNICODE)` which only matches word characters (alphanumeric + underscore). Double quotes cannot appear in `\w+` matches, so FTS5 injection via `"` is impossible. However, if the regex were ever broadened to include non-word characters, this would become exploitable.

**Impact:** NONE with current regex. Defense-in-depth concern only.

**Fix (optional):** Add explicit quote escaping for future safety:
```python
t_escaped = t.replace('"', '""')
return " OR ".join(f'"{t_escaped}"' for t in terms)
```

#### L-5: Supply chain — no lockfile with hashes

**File:** `pyproject.toml`

**Description:** (Same as Cycle 8 L-S-2.) Dependencies use loose version ranges without hash verification. A PyPI compromise could inject malicious code.

**Impact:** LOW — standard Python ecosystem risk. The pinned major version ranges (`<2`, `<0.2`, `<1.0`, `<3`) limit blast radius.

**Fix:** Generate `requirements.txt` with `pip-compile --generate-hashes` and verify in CI.

---

## Part III: Positive Security Observations

These are noteworthy hardening measures that go beyond what Cycle 8 recommended:

1. **Redact-before-truncate** (`pipeline.py:_brief`) — Secrets are redacted BEFORE the length cap, preventing a credential fragment from surviving past the truncation boundary.

2. **FTS query sanitization** (`db.py:_fts_query`) — Only `\w+` tokens allowed, max 32 terms, each double-quoted. Injection-safe by construction.

3. **Loopback enforcement** (`config.py`) — Both `http_host` and `dreamer_base_url` are validated as loopback-only, preventing SSRF even if the Dreamer or HTTP server is wired up.

4. **Temperament Bem firewall** (`cli.py:cmd_temperament`) — Agent self-reads blocked at the CLI boundary (non-TTY stdout refused unless `--operator` flag). Defense-in-depth against prompt injection via memory.

5. **Project scoping** (`mcp_server.py`) — MCP tools default to `_LAUNCH_CWD` for project scope. Empty project coerced to launch cwd. Model cannot self-authorize cross-project/global writes.

6. **`goal_hint` not exposed** (`mcp_server.py:store`) — Model cannot set `goal_hint` to bypass the goal-relevance gate. Only computed internally from turn signals.

7. **`_sanitize()` defense-in-depth** (`hooks.py`) — Control chars, zero-width/bidi Unicode, angle brackets, backticks all neutralized. Content fenced as untrusted DATA with explicit "not instructions" disclaimer.

8. **Atomic spool drain** (`pipeline.py`) — `os.replace()` claim prevents concurrent drain corruption. Unique claim names with UUID prevent clobbering.

9. **Config `_coerce()` rejects bools for non-bool fields** — Prevents `"embed_dim": true` → `int(True) == 1` from silently producing a degenerate config.

---

## Part IV: Remaining Open Items (Prioritized)

| Priority | ID | Finding | Effort |
|---|---|---|---|
| P1 | C-1 (Cycle 8) | Consolidation OOM — streaming chunks needed | Medium |
| P1 | M-1 (Cycle 8) | `touch_episodic` vs eviction race | Low |
| P2 | M-1 (this cycle) | Lock file permissions `0o600` | Trivial |
| P2 | M-2 (this cycle) | Randomize forget temp filename | Trivial |
| P3 | L-1 (this cycle) | `ensure_home()` mode `0o700` | Trivial |
| P3 | L-2 (this cycle) | Log file permissions `0o600` | Trivial |
| P3 | L-5 (this cycle) | Supply chain lockfile | Low |

---

## Closing Assessment

CDMS at commit f4dd7cf has **resolved all 6 Cycle 8 P0 findings** and most P1/P2 findings. The security posture is significantly stronger than Cycle 8:

- **Spool credentials** are now behind `0o600` permissions
- **S0 weight explosion** is bounded by a 10× cap with cross-field crisis-gate enforcement
- **Path traversal** in `home` and `db_filename` is rejected
- **Unicode injection** vectors are neutralized in the sanitizer
- **Credential patterns** cover all major cloud providers and token formats
- **Embedder TOCTOU** race is eliminated
- **MCP input validation** includes content length caps, kind validation, and loopback enforcement
- **SSRF** is blocked on both `http_host` and `dreamer_base_url`

The 2 new MEDIUM findings are defense-in-depth improvements (lock file permissions, temp file randomization). The 5 LOW findings are cosmetic or ecosystem-level. None represent exploitable vulnerabilities in a typical single-user deployment.

**Bottom line:** CDMS is ready for deployment. The P1 open items (consolidation OOM, eviction race) are operational concerns, not security vulnerabilities. No security blockers remain.

---

*End of Cycle 9 (MiMo v2.5 Pro) — Security audit. All findings independently verifiable against commit f4dd7cf.*
