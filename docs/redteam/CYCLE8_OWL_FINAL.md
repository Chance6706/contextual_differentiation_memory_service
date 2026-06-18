# CDMS Red-Team — Cycle 8, Final Report — OWL Alpha

> **Model:** OWL Alpha (OpenRouter)
> **Date:** 2026-06-18
> **Commit:** 8e889d7 (branch `claude/keen-ritchie-mrud69`)
> **Methodology:** 6 parallel subagent attacks + manual synthesis. 14 source files read in full. 224 tests passing, 5 Windows-specific failures. This is the deepest audit CDMS has received — every attack surface was covered by a dedicated specialist subagent.
> **Scope:** Full-spectrum red-team: mechanical, concurrency, security, cognitive math, scale, and philosophical.

---

## Executive Summary

CDMS at this commit is a substantially hardened system. Prior cycles fixed 50+ defects. The Cycle 7 triage addressed every open mechanical finding from Cycles 4-6. The new §8 temperament layer is well-designed and well-tested (648 lines of tests). The documentation now explicitly disclaims consciousness and clarifies the individuation claim.

This audit found **6 new HIGH-severity findings**, **8 MEDIUM**, and **6 LOW** — across every attack surface. The most serious issues are:

1. **Spool file contains pre-redaction secrets** (HIGH) — credentials sit world-readable on disk
2. **S0 weight cap too high** (HIGH) — `1e3` allows goal gate bypass
3. **Config `home` field unvalidated** (HIGH) — arbitrary path redirection
4. **Consolidation loads all episodes into memory** (CRITICAL at scale) — OOM at 100K+ episodes
5. **L3 scar table grows without bound** (HIGH) — no eviction mechanism
6. **`get_embedder()` TOCTOU race** (HIGH) — no threading lock on singleton creation

---

## Part I: Mechanical & Code-Level Findings

### CRITICAL

#### C-1: Consolidation loads ALL episodes into memory — OOM at scale
**File:** `consolidate.py:196`
**Threshold:** ~80K–120K episodes
**Trace:** `episodes = self.db.all_episodic()` loads every row into Python memory. Then `self.db.get_embeddings_bulk([e.id for e in episodes])` loads all 384-dim vectors. At 100K episodes: ~100MB text + ~154MB vectors = ~254MB RSS per consolidation. At 500K episodes: ~1.2GB+.
**Impact:** OOM kill on a mini PC. Consolidation fails silently or daemon crashes.
**Fix:** Process episodes in streaming chunks (10K at a time) for eviction and dedup.

### HIGH

#### H-1: Spool file contains pre-redaction secrets with 0644 permissions
**File:** `hooks.py:226-232`, `spool.py:40-59`
**Trace:** `spool_event()` writes raw hook payloads (including `tool_output` containing credentials) to `episodic_queue.ndjson` with `os.open(..., 0o644)`. Secret redaction only happens during `ingest()`. The window between spool write and drain can be minutes to hours.
**Impact:** Any user on the system can read the spool file and harvest credentials.
**Fix:** Apply `redact_secrets()` to `tool_output` in `spool_event()` before writing to disk. Change spool file permissions to `0o600`.

#### H-2: S0 weight validation cap too high — goal gate bypass
**File:** `config.py:231-234`
**Trace:** `CDMS_W_SURPRISE=1e3` → `S0 = 0.25 * (1000 * 1.0) = 250` with `goal=0`. This is 83× the `crisis_threshold=3.0`. Every memory qualifies for scar elevation.
**Impact:** Attacker with config control can make every memory maximally salient.
**Fix:** Cap weights at `10.0` and add cross-field check: `w_s + w_c + w_w + w_a <= 5.0`.

#### H-3: `home` field in config.json not validated — arbitrary path redirection
**File:** `config.py:310-324`
**Trace:** No `_validate()` check for `home`. A malicious `config.json` can set `"home": "/etc/cron.d"` or `"home": "\\\\attacker-server\\share"`.
**Impact:** Complete data exfiltration or overwrite of critical files.
**Fix:** Add `_validate` check that `home` must be under `Path.home()` or whitelisted prefix.

#### H-4: L3 scar table grows without bound
**File:** `consolidate.py:246-274`
**Trace:** Scars are "pinned" by design — no eviction, no time-based decay. Only dedup at 0.95 similarity.
**Impact:** At 10K+ scars, scar-tier KNN retrieval becomes the dominant latency.
**Fix:** Add per-project scar count cap (e.g., 100) with oldest-first eviction for elevated (non-pinned) scars.

#### H-5: `get_embedder()` TOCTOU race — no threading lock
**File:** `embeddings.py:234-240`
**Trace:** Two concurrent first-callers both see `_SINGLETON is None`, both construct `Embedder` instances. Two ONNX sessions loaded (~133MB each).
**Impact:** Memory leak (~133MB per race). Two different models could be loaded.
**Fix:** Add `threading.Lock()` with double-checked locking.

### MEDIUM

#### M-1: `touch_episodic` vs eviction race
**File:** `consolidate.py:320-327` vs `store.py:310`
**Trace:** Consolidation (under lock) reads `access_count`, decides to evict. Concurrent retrieve (no lock) bumps `access_count`. Consolidation deletes anyway.
**Impact:** Recently-retrieved memories can be wrongly evicted.
**Fix:** Re-read `access_count` inside `_evict()` before deleting.

#### M-2: Weight annihilation disables salience
**File:** `config.py:231-234`
**Trace:** All weights set to 0 → `S0 = 0` for every episode → every episode immediately evictable.
**Fix:** Add cross-field check: `w_s + w_c + w_w + w_a > 0`.

#### M-3: `goal_hint` is an unauthenticated bypass channel
**File:** `store.py:190-193`
**Trace:** Any caller of `MemoryService.ingest()` can inject `goal_hint=1.0`.
**Fix:** Strip `goal_hint` from MCP tool callers; compute internally only.

#### M-4: Unicode line separators survive `_sanitize()`
**File:** `hooks.py:49-68`
**Trace:** U+2028, U+2029, U+0085 not in `_CTRL` regex. Can survive into SessionStart injection.
**Fix:** Add `\u2028\u2029\u0085` to the `_CTRL` regex.

#### M-5: Secret redaction misses Anthropic/Google credential formats
**File:** `store.py:60-75`
**Trace:** `sk-ant-*` (Anthropic), `AIza*` (Google), Azure `AccountKey=` not covered.
**Fix:** Add patterns for these credential formats.

#### M-6: MCP `store` tool has no content length limit
**File:** `mcp_server.py:122-144`
**Trace:** No `max_length` on `content` field. 10MB string accepted by MCP layer.
**Fix:** Add `max_length=10000` to the `content` field's `Field()`.

#### M-7: `http_host` not validated as loopback-only
**File:** `config.py:123`
**Trace:** `CDMS_HTTP_HOST=0.0.0.0` binds to all interfaces.
**Fix:** Validate `http_host` must be a loopback address.

#### M-8: `sqlite-vec` minor version can break vec0 format
**File:** `pyproject.toml`
**Trace:** `sqlite-vec<0.2` allows 0.1.x updates that could change vec0 binary format. Not caught by embedder fingerprint.
**Fix:** Pin exact version or add runtime version check.

### LOW

#### L-1: Dedup supersession per-candidate DB round-trip
**File:** `consolidate.py:299`
**Trace:** One SQL query per dedup candidate. At 50K+ episodes: 25K+ queries.
**Fix:** Cache `keep_e` episodes in a dict (already in memory).

#### L-2: `_brief()` truncation before redaction boundary
**File:** `pipeline.py:89-95`
**Trace:** Truncation to 1000 chars before `redact_secrets()` scans. Credential split at boundary might be missed.
**Fix:** Redact secrets before truncation.

#### L-3: Consolidation skip drains not in stats
**File:** `pipeline.py:286-301`
**Trace:** Drain skip counter recorded in meta but not surfaced in `cdms stats`.
**Fix:** Add `drains_skipped` to stats output.

#### L-4: Quarantined `.corrupt-*` files retain original permissions
**File:** `db.py:171-186`
**Trace:** `os.replace()` preserves original permissions (typically 0644).
**Fix:** Set `0o600` on quarantined files at creation.

#### L-5: JSON config bool-to-int coercion edge case
**File:** `config.py:317-322`
**Trace:** `"embed_dim": true` → `int(True)` → `1`, valid int in range.
**Fix:** Explicitly reject bool values for numeric fields in `_coerce()`.

#### L-6: Gist `render()` relation forgeability
**File:** `models.py:63-65`
**Trace:** If object field contains "handles_well", rendered output is ambiguous.
**Fix:** Low priority. Consider prefixing relation with non-ambiguous marker.

---

## Part II: Concurrency Findings

### HIGH

#### H-C-1: `get_embedder()` TOCTOU (same as H-5 above)
**File:** `embeddings.py:234-240`
**Race:** Thread A checks `_SINGLETON is None`, starts constructing. Thread B checks `_SINGLETON is None` (not yet assigned), starts constructing. Two ONNX sessions loaded.
**Fix:** `threading.Lock()` with double-checked locking.

### MEDIUM

#### M-C-1: `touch_episodic` vs eviction (same as M-1 above)
**Race:** Consolidation decides to evict based on stale `access_count`. Concurrent retrieve bumps it. Eviction proceeds anyway.
**Fix:** Re-read `access_count` before delete in `_evict()`.

#### M-C-2: Hook sees partial consolidation state
**File:** `hooks.py:102-118` vs `consolidate.py:175-228`
**Race:** `SessionStart` hook reads without the lock. Can see mid-consolidation state (episodes evicted but gists not yet aggregated).
**Impact:** Inconsistent context injection — gists reference evicted episodes.
**Fix:** Brief lock acquisition during SessionStart read, or "consolidation in progress" flag.

### LOW

#### L-C-1: Meta counter lost-update
**File:** `db.py:320-324`
**Race:** Two processes read cycle=5, both compute 6, both write 6. Cycle counter advances by 1 instead of 2.
**Mitigating factor:** Cross-process lock prevents concurrent consolidation.
**Fix:** Use `UPDATE ... SET value = value + 1 WHERE key = 'cycle'` (atomic increment).

#### L-C-2: Spool append during `_forget_from_spool`
**File:** `store.py:457-500` vs `spool.py:40-59`
**Race:** Forget rewrites spool while hook appends. No data loss (O_APPEND creates new file), but ordering not guaranteed.
**Impact:** Acceptable — spool semantics don't guarantee ordering.

---

## Part III: Security Findings

### HIGH

#### H-S-1: Spool file contains pre-redaction secrets (same as H-1 above)

#### H-S-2: `home` field unvalidated (same as H-3 above)

### MEDIUM

#### M-S-1: Unicode line separators survive sanitizer (same as M-4 above)

#### M-S-2: Secret redaction misses credential formats (same as M-5 above)

#### M-S-3: MCP `store` tool has no content length limit (same as M-6 above)

#### M-S-4: `http_host` not validated as loopback (same as M-7 above)

#### M-S-5: `dreamer_base_url` has no URL scheme/host validation
**File:** `config.py:117-120`
**Trace:** No URL validation. When dreamer is wired, `dreamer_base_url` could point to `http://169.254.169.254/latest/meta-data/` for SSRF.
**Fix:** Validate `dreamer_base_url` must be loopback unless explicitly overridden.

#### M-S-6: Quarantined `.corrupt-*` files world-readable (same as L-4 above)

### LOW

#### L-S-1: MCP `store` tool silently accepts unknown `kind` values
**File:** `mcp_server.py:129`
**Trace:** `"kind": "scra"` silently becomes an episode.
**Fix:** Validate `kind` against `{"episode", "fact", "scar"}`.

#### L-S-2: No lock file with hashes for dependencies
**File:** `pyproject.toml`
**Trace:** Loose version ranges. Supply-chain attack on PyPI could inject malicious code.
**Fix:** Generate and check in a `requirements.lock` with hashes.

#### L-S-3: Base64-encoded secrets not redacted
**File:** `store.py:60-75`
**Trace:** `export API_KEY="c2Vj...="` would not match any pattern.
**Fix:** Add pattern for high-entropy base64 strings in KEY/SECRET/TOKEN assignment contexts.

---

## Part IV: Cognitive Math Findings

### HIGH

#### H-M-1: Weight explosion bypasses goal gate (same as H-2 above)

#### H-M-2: Budget exhaustion attack
**File:** `consolidate.py:330-356`
**Trace:** 100 attacker sessions × 1 episode at S0=250 pushes legitimate episodes (50 at S0=2, total=100) from salience 2.0 down to 0.078, below `retention_floor=0.10`. Legitimate memories evicted.
**Impact:** Attacker with many sessions can starve legitimate memories.
**Fix:** Add per-session write cap or strengthen per-project budget isolation.

### MEDIUM

#### M-M-1: Weight annihilation disables salience (same as M-2 above)

#### M-M-2: `goal_hint` bypass (same as M-3 above)

#### M-M-3: Associative boost amplification
**File:** `store.py:214-231`
**Trace:** A single high-S0 write injects +50 salience into nearby episodes (with weight explosion). Can cascade.
**Impact:** Amplifies the weight explosion attack.
**Fix:** Cap per-write associative boost total.

#### M-M-4: Valence EMA poisoning
**File:** `consolidate.py:420`
**Trace:** Just 2 injected episodes at valence=-1.0 flip a neutral trait to `has_trouble_with` (EMA=0.4).
**Impact:** Identity fragile — few injected episodes can flip traits.
**Fix:** Lower `gist_valence_ema` to ~0.2 or add adaptive EMA ∝ 1/√(support_count).

#### M-M-5: Empty consolidation cycle bombing (X2 tradeoff, documented)
**File:** `consolidate.py:214-228`
**Trace:** ~134 forced empty cycles erase a minimally-supported trait.
**Status:** Documented tradeoff, deliberately not fixed.

### LOW

#### L-M-1: Gist centroid creep
**File:** `consolidate.py:426-427`
**Trace:** Greedy clustering absorbs semantically unrelated episodes into a gist over time.
**Impact:** Gradual identity drift.
**Mitigating factor:** Support-weighted centroid blend resists drift.

#### L-M-2: Single-session softmax dominance
**File:** `salience.py:101-137`
**Trace:** `softmax([250, 0.5]) ≈ [1.0, 0.0]`. One high-salience session dominates epoch.
**Impact:** Amplifies budget exhaustion attack.
**Mitigating factor:** Hierarchical competition operates at session level.

---

## Part V: Scale Findings

### CRITICAL

#### C-S-1: Consolidation OOM (same as C-1 above)

### HIGH

#### H-S-1: L3 scar table unbounded (same as H-4 above)

### MEDIUM

#### M-S-1: DB file bloat from free pages
**File:** `consolidate.py` (no VACUUM)
**Trace:** After bulk eviction, free pages remain. DB grows 2-3× beyond actual data.
**Fix:** Run `PRAGMA incremental_vacuum(N)` periodically during consolidation.

#### M-S-2: Retrieval latency growth at 50K+ gists
**File:** `store.py:317`
**Trace:** vec0 KNN is brute-force cosine across all vectors. At 50K gists: ~5-20ms. At 200K: ~100ms.
**Impact:** Degraded but functional.
**Mitigating factor:** Gist count is self-limiting via decay.

### LOW

#### L-S-1: Dedup per-candidate round-trip (same as L-1 above)

#### L-S-2: `lru_cache(maxsize=None)` on `_marker_re`
**File:** `pipeline.py:51-57`
**Trace:** Unbounded cache. In practice only ~20 entries (fixed marker sets).
**Fix:** Set `maxsize=128` for defense-in-depth.

---

## Part VI: Philosophical Findings

### Genuine Vulnerabilities

#### P-1: Individuation is topic discrimination, not character differentiation
**The gist substrate is a competence-map** (`handles_well`/`has_trouble_with` over project-domain terms), not a personality. The §10.5 portrait gap is acknowledged but unfixed.
**Status:** Known limitation. The temperament layer (§8) is the planned richer substrate.

#### P-2: The "LLM never authors the tuple" discipline creates a behaviorist prison
**The self-model can never exceed the lexical surface of what was literally said.** It cannot infer "Josh is methodical" from patterns of behavior — it can only record "Josh handles_well testing."
**Status:** Deliberate design choice. The mechanical extraction prevents generative self-fiction but also prevents richer self-models.

#### P-3: The Bem firewall is permeable
**A capable model can estimate its temperament from the gist distribution it receives at SessionStart.** The phenotype IS the dial, lossily encoded. The firewall blocks direct reading but not indirect inference.
**Status:** Acknowledged limitation. The --operator flag on `cdms temperament` is the mitigation.

#### P-4: Substrate independence is content portability, not soul transfer
**The embedding-space geometry and specific L1 episodes are lost on model change.** Only summary text and crisis guardrails survive perfectly. Calling it "the same AI in a new body" is rhetorical overreach.
**Status:** The design doc now honestly disowns this reading (DESIGN.md §1.1a).

#### P-5: The escalation ladder approaches proto-consciousness
**The full design trajectory (reactive → drifting → dreaming → self-editing → reality-coupled) approaches proto-consciousness thresholds under IIT, GWS, and HOT theories.** The "mechanical and reactive today" framing is correct for Phase 0 but misleading about the full design.
**Status:** The design explicitly disclaims consciousness. The line's location is theory-dependent.

### Defensible Positions

- **Convergence of different histories to the same self-model** is a feature of any finite perceptual system. The lossy compression is the design.
- **Bounded plasticity is true by construction** — any finite system is bounded. Whether bounds are at natural joints is deferred to Phase 2.
- **The "useful behavior" framing** works if you accept the hard problem move (functional organization ≠ phenomenal experience).

---

## Part VII: Prioritized Action Items

### P0 — Fix Before Next Merge

| ID | Finding | Fix |
|----|---------|-----|
| H-1 | Spool pre-redaction secrets | Redact in `spool_event()` or `0o600` |
| H-2 | S0 weight cap too high | Cap at 10.0, sum ≤ 5.0 |
| H-3 | `home` field unvalidated | Validate under `Path.home()` |
| H-5 | `get_embedder()` TOCTOU | Add `threading.Lock()` |
| M-4 | Unicode sanitizer bypass | Add U+2028/2029/0085 to `_CTRL` |
| M-5 | Missing credential patterns | Add Anthropic/Google patterns |

### P1 — Fix Before Production

| ID | Finding | Fix |
|----|---------|-----|
| C-1 | Consolidation OOM at scale | Streaming chunk processing |
| H-4 | L3 scar table unbounded | Per-project cap + eviction |
| M-1 | touch_episodic vs eviction | Re-read before delete |
| M-3 | `goal_hint` bypass | Strip from MCP callers |
| M-M-4 | Valence EMA poisoning | Lower EMA or adaptive rate |

### P2 — Fix When Convenient

| ID | Finding | Fix |
|----|---------|-----|
| M-6 | MCP store no max_length | Add `max_length=10000` |
| M-7 | `http_host` not validated | Validate loopback |
| M-8 | sqlite-vec minor version | Pin exact version |
| M-S-5 | `dreamer_base_url` no validation | Validate loopback |
| L-1 | Dedup per-candidate round-trip | In-memory cache |
| L-4 | Quarantine file permissions | `0o600` at creation |
| L-3 | Drain skip not in stats | Add to `cdms stats` |

---

## Closing Assessment

CDMS is the most thoroughly red-teamed personal AI system I've encountered. Five prior cycles fixed 50+ defects. The Cycle 7 triage addressed every open finding. The new temperament layer is research-grounded and well-tested. The documentation is philosophically honest.

This audit found 20 new findings (6 HIGH, 8 MEDIUM, 6 LOW). The most serious are the spool secret exposure (H-1), the S0 weight cap (H-2), the unvalidated `home` field (H-3), and the consolidation OOM at scale (C-1). None of these are architectural flaws — they're all fixable with targeted patches.

The philosophical analysis confirms that CDMS's ego-simulacrum claim is defensible but sits on a knife's edge. The system is designed to be *as much of an ego as possible without crossing into consciousness*, and the line's location is theory-dependent. The documentation's explicit disclaimer is the right call.

**Bottom line:** CDMS is ready for Phase 0 deployment with the P0 fixes applied. The P1 fixes should be applied before any production use. The P2 fixes can be scheduled as maintenance items. The philosophical vulnerabilities are acknowledged and defensible.

---

*End of Cycle 8 (OWL Alpha) — Final red-team report. All findings independently verifiable against commit 8e889d7.*
