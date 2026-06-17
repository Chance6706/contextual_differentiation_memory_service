# Red-Team Audit & Remediation (pre-Phase-0)

A full adversarial audit of the built package was run before building the §8
temperament layer, on the premise that latent defects in the always-running core
compound silently *over time*. Five focused agents ran experiments against the live
code (storage durability, embedder integrity, long-horizon consolidation, capture
concurrency, security/injection); a sixth pass reviewed the temperament plan. Gemini
contributed three Round-2 attacks. This file records what was found, what was fixed,
and what is deliberately deferred. The CI suite forces the hash embedder, so a
non-hash test path (`tests/test_real_embedder.py`) was added to cover the real model.

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

## Plan-level corrections
Recorded in `docs/TEMPERAMENT_PLAN.md` §8 (P1–P7 + Gemini's "Boiling Frog" exit-gate).
