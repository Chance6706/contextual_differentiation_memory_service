# Red-Team Audit & Remediation (pre-Phase-0)

Three adversarial cycles were run before building the §8 temperament layer, on the
premise that latent defects in the always-running core compound silently *over time*.
This file records what was found, fixed, and deliberately deferred. The CI suite
forces the hash embedder, so a non-hash test path (`tests/test_real_embedder.py`)
covers the real model. Suite: 38 → 77 (Cycle 1) → 110 (Cycle 2) tests, all green.

## Cycle 1 — core surfaces

Five focused agents ran experiments against the live code (storage durability,
embedder integrity, long-horizon consolidation, capture concurrency,
security/injection); a sixth pass reviewed the temperament plan; Gemini contributed
three Round-2 attacks.

## Cycle 2 — broadened (every angle) + audit of the Cycle-1 fixes

Seven agents covered new angles (MCP protocol, scale/performance, cognitive-math
correctness, environment/clock/config, data isolation/lifecycle, seeders on untrusted
data, packaging/recovery/test-integrity) AND adversarially re-audited the eight
Cycle-1 fixes — which is how three Cycle-1 fixes were found incomplete/overcorrected.

**Fixed in Cycle 2 (commits `ce783ff..HEAD`):**

| Sev | Defect | Fix |
|-----|--------|-----|
| HIGH | Fence-escape: `</memory:*>` in content closed the trust fence | `_sanitize` escapes angle brackets + strips zero-width/bidi |
| HIGH | SessionStart truncation dropped the close fence + trust disclaimer | block-packing keeps fences balanced + disclaimer within budget |
| HIGH | Cross-project gist contamination (clustering ignored project) | partition episodes by project before clustering |
| HIGH | Subject-basename collision merged distinct repos | gist identity keyed by `(subject, object, project)` |
| HIGH | `retrieve()` had no project scoping (cross-project exfiltration) | `retrieve(project=)`; MCP tools default to launch cwd |
| HIGH | No right-to-forget (scars unremovable; uninstall kept data) | `delete_scar`, `MemoryService.forget`, `cdms forget`, `uninstall --purge` |
| HIGH | JSON config bypassed coercion (stringified dim bricked store) | coerce JSON values to field type |
| HIGH | `SALIENCE_BUDGET=0`/negative silently wiped memory | `_validate()` repairs out-of-range; `conserve_budget` K<=0 no-op |
| HIGH | `doctor` blind to fingerprint mismatch (silent capture refusal) | doctor compares pinned fingerprint + `quick_check` |
| HIGH | Corrupt `memory.db` silently halted capture, spool grew | quarantine corrupt file + start fresh, loudly |
| HIGH | unbounded `store` content = event-loop DoS | cap fields to `max_field_chars` before embed |
| HIGH | `_infer_success` negation-blind (live capture + seeders) | negation-aware + positive-override; conservative None |
| HIGH | (Cycle-1 H4) deed-gate overcorrected → false-negatives | regex tier for phrasing/verb-order variants |
| HIGH | (Cycle-1 H1) gist identity-creep (frozen label vs drifting centroid) | refresh label to track content; support-weighted centroid blend |
| HIGH | (Cycle-1 L1) spool `os.write` short-write swallowed next turn | loop the write |
| MED | redaction gap on `upsert_fact`/`pin_scar` | shared `_clip` redacts+caps all stored fields |
| MED | `create_link` fabricated dangling edges, always "created" | validate endpoints; return real result |
| MED | FTS ASCII-only tokenizer (non-Latin recall lost) | unicode-aware `\w+` (still injection-safe) |
| MED | seeder crashed whole run on one non-dict line | isinstance guards + per-file isolation; stream Hermes cursor |
| MED | empty-cwd dumped every project's scars | empty cwd => global-only scoping |
| MED | vacuous/weak tests; zero MCP coverage | rewrote absence test (mutation-sensitive); added MCP suite |
| LOW | atomic-write fixed tmp race; `_SERVICE` init race; stale warmup msg; unbounded log; numpy unpinned | unique tmp; init lock; accurate msg; log rotation; numpy `<3` |

**Cycle-2 verified-sound (no change):** MCP protocol robustness holds (C1/M7 raises
become clean JSON-RPC errors, stdout stays pristine); cognitive math correct
(20k-case property test on the capped-proportional allocator; M2 clamp exactly
behavior-preserving; clock-skew/malformed timestamps handled); the store is NOT
unbounded while consolidation runs (conserved-budget renorm self-bounds the live
set); WAL crash-recovery sound; M1 negative-idle correctly clamped; seeders route
through redaction; auto-scar injection from transcripts is genuinely hard.

## Cycle 1 details

## Fixed (built code)

| ID | Sev | Defect | Fix (commit) | Test |
|----|-----|--------|--------------|------|
| C1 | CRIT | Silent fastembed→hash degrade wrote hash-space vectors into a bge store (permanent recall corruption); backend never pinned | Raise instead of degrade; pin `{backend:model:dim}` in `cdms_meta`, refuse mismatch | `test_embedder_integrity` |
| C2 | CRIT | Empty/punctuation text → zero vector → NULL distance → KNN crash poisons a tier | Map degenerate rows to a unit sentinel; skip NULL distances in `knn` | `test_embedder_integrity` |
| C3 | CRIT | Untrusted stored memory replayed verbatim at SessionStart as trusted "Guardrails" (persistent prompt injection) | Sanitize + fence all injected content as untrusted DATA | `test_trust_boundary` |
| H1 | HIGH | Gist key (subject, top-2 terms) reshuffled/drifted → one topic shattered into many siblings; identity never crystallized | Reinforce nearest existing gist by episode-space centroid **and** shared object term | `test_gist_stability` |
| H2 | HIGH | Fixed `.processing` claim file → concurrent drains clobbered, dropping a session's turns | Unique per-drain claim name (pid+uuid) | `test_capture_concurrency` |
| H3 | HIGH | Newlines in scars/gists forged fake markdown sections / closed the trust hedge | Collapse newlines+control chars; neutralize code fences | `test_trust_boundary` |
| H4 | HIGH | Benign discussion of "rm -rf"/"force push" auto-pinned as permanent scars | Catastrophe marker must be in the deed (action/outcome), not the prompt | `test_trust_boundary` |
| H5 | HIGH | `all_scars()[:10]` by recency let junk scars evict real guardrails | Scar `origin` (pinned vs elevated); prioritize + dedupe pinned in injection | `test_trust_boundary` |
| M1 | MED | Crash mid-consolidation advanced the decay-cycle counter → identity erosion | Persist cycle counter only after the pass succeeds | `test_storage_robustness` |
| M2 | MED | `accessibility()` overflowed for large access_count → crashed eviction | Clamp the reinforcement exponent before exponentiating | `test_storage_robustness` |
| M3 | MED | No `ORDER BY` → clustering not reproducible across VACUUM/reinsert | Explicit `ORDER BY rowid` (de-facto capture order), THRASH-verified | covered by drift CI |
| M4 | MED | `user_version` set before migration ALTERs → half-migrated store reports new version | Set `user_version` last, after idempotent column adds | `test_storage_robustness` |
| M5 | MED | Malformed config JSON reset to `{}` then overwritten → lost user settings | `_read_json_safe` aborts loudly | `test_install_safety` |
| M6 | MED | Non-atomic config writes could truncate `~/.claude.json` | `_atomic_write_json` (temp + os.replace) | `test_install_safety` |
| M7 | MED | `knn`/`fts` swallowed dim-mismatch OperationalError → silent empty recall | Re-raise dimension errors | `test_embedder_integrity` |
| M8 | MED | Secrets in tool output persisted plaintext + re-injected forever | `redact_secrets` at the ingest chokepoint | `test_trust_boundary` |
| L1 | LOW | Killed subprocess mid-write could merge spool lines | Single `os.write` O_APPEND syscall | `test_capture_concurrency` |

Plus a determinism fix in `tools/individuation_experiment.py` (it seeded RNG with
the per-process-salted builtin `hash()`), which made the experiment reproducible.

## Verified sound (no change needed)
No orphaned vec/FTS rows on delete; WAL bounded under SIGKILL; no unbounded table
growth; id collisions negligible; SQL/FTS injection safe; MCP arg-validation safe;
concurrent spool appends atomic; install idempotent + preserves foreign entries;
turn reconstruction robust; busy_timeout absorbs lock contention; hash embedder
deterministic (blake2b); serialization correct; flip oscillation damped; salience
budget reaches a stable K equilibrium; decay underflow clean.

## Deferred (characterized, lower priority)
- **L2** — no `UNIQUE(subject,object)` on `mem_gist`: a concurrent-writer race could
  create a shadow duplicate. Adding the constraint risks failing on any pre-existing
  duplicate; deferred pending a dedupe-migration.
- **L4** — dedup deletes a superseded episode's support edge without re-pointing it to
  the survivor (silent provenance loss, not row growth).
- **L3** — `support_count = max(...)` is monotonic, so a trait whose source episodes
  never leave rarely decays; forgetting is weaker than the design implies.
- **Full migration transactionality** — Python autocommits DDL; the ordering fix (M4)
  heals interrupted *idempotent* migrations, but a future non-idempotent step would
  need `isolation_level=None` + explicit BEGIN/COMMIT.
- **Insertion-order-invariant clustering** — M3 pins a deterministic order; making
  greedy clustering independent of capture order is a separate algorithmic change.
- **Case-insensitive-FS subject splitting** (Cycle 2) — `C:\Dev\Foo` vs `c:\dev\foo`
  yield two subjects on Windows/macOS; safe cross-platform case normalization is risky
  (a store can move between platforms) and the incidence is low — documented, not fixed.
- **CJK gist tokenization** (Cycle 2) — space-less scripts collapse to one token / drop
  2-codepoint words; needs real segmentation. Cyrillic/accented now handled (FTS fix).
- **Dreamer/httpx path is dead code** (Cycle 2) — `dreamer_*`/`http_*` config is never
  imported; no runtime risk. Left as a documented placeholder for the designed feature.

## Plan-level corrections
Recorded in `docs/TEMPERAMENT_PLAN.md` §8 (P1–P7 + Gemini's "Boiling Frog" exit-gate).
