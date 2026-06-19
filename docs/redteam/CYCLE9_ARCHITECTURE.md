# Cycle 9 — Architecture, Design Debt & Emergent Behavior Audit

**Scope:** Cross-component interaction bugs, emergent behaviors from the
decay+consolidation+temperament stack, design debt that compounds through the
lifecycle, failure-mode cascading, config knob interaction effects, test
coverage gaps, observability gaps, active dreaming extensibility, and whether
the system achieves individuation.

**Base commit:** `51994b0` (HEAD, main)  
**Codebase:** ~4,500 LOC across 16 Python modules in `src/cdms/`  
**Prior art:** Cycle 8 found 20 issues (6 HIGH, 8 MEDIUM, 6 LOW); Cycle 9
focuses on systemic/architectural concerns rather than individual bugs.

---

## Part I: Cross-Component Interaction Bugs

### 1.1 The write→consolidate→retrieve→inject lifecycle

The full memory lifecycle is:

```
Hook (spool) → Drain (reconstruct + ingest) → Salience (S0 + associate)
  → Consolidate (scar-elevate → dedup → evict → compete → gist-aggregate → L2-decay)
    → Retrieve (RRF + accessibility + reinforce) → Inject (SessionStart context)
```

#### CRITICAL — I-1: SessionStart reads WITHOUT the cross-process lock

**Trace:** `hooks.py:dispatch` → `_session_start_context` → `MemoryService` →
`db.all_scars()` + `db.top_gist()` + `db.all_episodic()` — all executed
**without** `cross_process_lock`. Meanwhile, `SessionEnd` runs
`_drain_and_consolidate` **under the lock**. A SessionStart hook arriving
mid-consolidation can read an inconsistent snapshot: episodes that have been
evicted but whose gists haven't been aggregated yet, or gists that have been
decayed but whose replacements aren't written yet.

**Impact:** Injected context can reference evicted episodes, omit newly-created
gists, or present a half-consolidated PersonaTree. The model's "prior belief"
is stale by exactly one consolidation step.

**Severity:** CRITICAL — this is the one moment where the memory system shapes
the model's behavior, and it's reading a possibly-inconsistent state.

**Suggested fix:** Either (a) acquire a brief shared-mode lock during
SessionStart reads (reader-writer pattern — `fcntl.flock(LOCK_SH)`), or (b)
snapshot the context at consolidation end and cache it for the next
SessionStart. Option (b) is simpler and avoids any lock contention on the hot
SessionStart path.

#### HIGH — I-2: Consolidation's in-memory snapshot diverges from DB mid-pass

**Trace:** `consolidate.py:_run_locked` loads `episodes = self.db.all_episodic()`
once at the top, then progressively filters in memory. But `touch_episodic`
(called by `retrieve` via the lock's drain timeout) can bump `access_count` on
episodes the consolidator already evicted from its in-memory list. The
`_evict` step now re-reads candidates (Cycle-8 M-1 fix), but `_dedup` does
**not** — it folds salience/access from the stale snapshot into survivors.

**Impact:** A memory retrieved between dedup-start and dedup-end loses its
access boost (the survivor gets `max(salience)` but the freshly-retrieved
episode's bumped `access_count` is folded from the stale value). Low-severity
data loss, but it violates the "testing effect" guarantee.

**Severity:** HIGH — undermines the retrieval-reinforcement feedback loop.

**Suggested fix:** Re-read `access_count` from DB in the dedup fold path, or
snapshot access_count alongside base_salience at pass start.

#### HIGH — I-3: Gist centroid drifts toward the embedder's sentinel vector

**Trace:** `embeddings.py` maps degenerate inputs (emoji-only, whitespace) to a
canonical sentinel `[1,0,0,...]`. If a gist's supporting episodes contain
degenerate inputs (e.g., a tool that returns only emoji status), the centroid
computed from those episodes' embeddings will be pulled toward the sentinel.
Over many consolidation cycles, the centroid migrates, causing `_match_gist_by_embedding`
to match unrelated gists (collapsing differentiation).

**Impact:** Low-probability but real: projects with emoji-heavy tool output
could see gist identity corruption.

**Severity:** HIGH — directly undermines individuation.

**Suggested fix:** Filter degenerate embeddings from the centroid computation
(`consolidate.py:_centroid`), or exclude episodes whose text passes
`_has_content() == False` from clustering.

#### MEDIUM — I-4: `_forget_from_spool` races with active hook appends

**Trace:** `store.py:_forget_from_spool` atomically renames the spool to
`*.forget-{pid}.tmp`, filters it, and writes back. But a hook process can
`spool_event` between the rename and the writeback — those events land in the
new (post-rename) queue file, which is correct. However, if two forget
operations run concurrently (unlikely but not prevented by any lock — forget
holds the consolidation lock, but two `cdms forget` CLIs could race), the
second rename would fail with `FileNotFoundError` (the file was already
renamed by the first), silently dropping the second forget's spool filter.

**Impact:** Low-probability concurrency edge; the spool events would still be
ingested and could be forgotten later.

**Severity:** MEDIUM.

---

## Part II: Emergent Behaviors from Decay + Consolidation + Temperament

### 2.1 The "Identity Freezing" emergent behavior

**Mechanism:** When the hash embedder is in use (common in testing, possible in
production via `CDMS_EMBED_BACKEND=hash`), all episodes with similar vocabulary
map to nearly-identical vectors. The dedup threshold (0.95) then merges almost
all episodes into a handful of survivors. These survivors get folded salience
from all their duplicates, pushing them above the retention floor permanently.
Meanwhile, the cluster threshold (0.78) groups everything into 1–2 gists.

**Emergent result:** The entire store collapses to 1–2 gists with very high
support_count, which then resist gist_decay for hundreds of cycles. The
temperament dials (Phase 0, `current == seed`) are inert, so nothing modulates
this. The system reaches a stable equilibrium where identity is frozen after
~3 consolidation cycles.

**Severity:** MEDIUM — only affects hash-backend deployments, but the test
suite runs entirely on hash, so tests may not catch gist-proliferation bugs
that the real embedder would expose.

### 2.2 The "Budget Starvation Cascade"

**Mechanism:** An attacker who can force many high-S0 episodes in one project
triggers the project budget cap (0.5). The capped-proportional allocator
redistributes the excess, but within each project, the **session budget cap**
(0.5) further constrains. If the attacker uses many sessions, each gets a
thin slice. Meanwhile, legitimate episodes in the same project get their
salience renormalized downward. On the next consolidation, some fall below
`retention_floor=0.10` and are evicted. This reduces the denominator in the
next `conserve_budget`, which **increases** the attacker's share proportionally.

**Emergent result:** A positive feedback loop where attacker episodes
progressively starve legitimate ones, accelerated by each eviction cycle.
The loop terminates only when all legitimate episodes are gone or the attacker
stops. Cycle-8 identified the static attack (H-M-2, budget exhaustion) but
not the **dynamic cascade** across multiple consolidation cycles.

**Severity:** HIGH — the per-session cap mitigates the single-cycle attack but
does not prevent the multi-cycle cascade.

**Suggested fix:** Track per-project episode counts across consolidation
cycles; if a project's episode count drops by >50% in one cycle, flag it and
hold the budget allocation constant for one cycle (damping).

### 2.3 The "Temperament Inertia Trap" (Phase 1b hazard)

**Mechanism (pre-build analysis):** The TEMPERAMENT_PLAN specifies an OU
process with seed-reverting term: `current ← current + α·(evidence − current)
− γ·(current − seed)`. With Phase 0's `current == seed`, the restoring term
is zero — drift can only begin if α·evidence ≠ 0. But the plan also specifies
a **prediction-error gate**: updates fire only on expectancy violation. An
agent whose temperament matches its experience (no expectancy violation) will
never drift at all, even if the environment changes dramatically — because the
gate requires the agent to *expect something different* from what happened, and
the agent has no mechanism to form expectations yet (that requires the proposal
lever, Phase 1a).

**Emergent result:** Phase 1b without Phase 1a produces a temperament that can
only drift on *surprising* outcomes, but has no mechanism to be surprised. This
is the TEMPERAMENT_PLAN's own §6 warning made concrete: "If we are unwilling to
build the proposal lever, we should not build temperament drift at all."

**Severity:** LOW (pre-build — the trap exists in the design, not the code).

---

## Part III: Design Debt That Compounds

### HIGH — D-1: The single-binary `MemoryService` owns both read and write paths

`MemoryService` in `store.py` is the god object: it holds the DB connection,
the embedder, and exposes ingest, retrieve, pin_scar, upsert_fact, forget,
history, list_paths, create_link, and close. Every caller (hooks, MCP server,
CLI commands, consolidation) constructs its own instance.

**Compounding debt:**
- The MCP server holds a **process-lifetime singleton** (`_SERVICE`), but hooks
  (subprocess invocations) create a new `MemoryService` per call. The embedder
  singleton (`_SINGLETON`) is per-process, so each hook subprocess loads the
  ONNX model on first use — adding ~2s to the first hook call.
- `forget()` requires the consolidation lock but is called from `MemoryService`,
  which also provides `retrieve()` (lock-free). The lock ownership is invisible
  from the caller's perspective.
- `_reconcile_embedder()` is called lazily on first vector operation, but
  `ingest()`, `retrieve()`, `pin_scar()`, and `upsert_fact()` all call it. A
  caller who only does `history()` never reconciles — correct behavior, but the
  "when does reconciliation happen" contract is implicit.

**Suggested fix:** Split into `MemoryReader` (lock-free, no embedder) and
`MemoryWriter` (embedder, reconciliation). The MCP server's `history` and
`list_paths` tools could use a lightweight reader without loading ONNX.

### HIGH — D-2: Consolidation is a 300-line method with implicit step ordering

`Consolidator._run_locked` executes 6 steps in a specific order:
1. `_elevate_scars` (mutates DB: deletes episodes, inserts scars)
2. `_dedup` (mutates DB: deletes episodes, updates salience)
3. `_evict` (mutates DB: deletes episodes)
4. `_compete_and_renormalize` (mutates DB: updates salience)
5. `_aggregate_gists` (mutates DB: inserts/updates gists, adds edges)
6. `_decay_gists` (mutates DB: deletes gists)

The ordering is **load-bearing**: dedup before evict (so near-dupes don't waste
eviction checks), evict before compete (so the budget is distributed among
survivors only), compete before gist-aggregate (so gists reflect the final
salience distribution). But this ordering is **not enforced or documented in
code** — only in prose comments. A future contributor could reorder steps or
insert a new step between them, breaking invariants silently.

**Compounding debt:** Each step mutates the in-memory `episodes` list AND the
DB. The in-memory mutations are correct but create a fragile implicit contract:
`_elevate_scars` returns removed IDs, `_dedup` filters them out, etc. Adding a
step requires updating all downstream filters.

**Suggested fix:** (a) Document the ordering invariant in an assertion or
explicit `Pipeline` class with ordered phases. (b) Consider making each step
return the updated episode list rather than filtering in the caller.

### MEDIUM — D-3: The `_content_terms` tokenizer is lossy and English-centric

**Trace:** `consolidate.py:_content_terms` strips non-alphanumeric chars, lowercases,
removes stopwords from a hardcoded English set, and removes tokens ≤2 chars.
CJK content (which is alphanumeric per `str.isalnum`) survives tokenization but
produces single-character tokens that are then filtered by the `len(tok) > 2`
check. Cyrillic, Arabic, and most non-Latin scripts produce tokens that are
often ≤2 chars after the stopword filter.

**Impact:** Gist objects for non-English projects are empty or dominated by
English fragments (file extensions, tool names). The FTS5 arm of hybrid recall
works (it uses `unicode61` tokenizer), but the gist extraction arm — the
identity-forming layer — is English-only.

**Severity:** MEDIUM — affects non-English users; the FTS fallback partially
compensates.

### MEDIUM — D-4: No migration path for embed_dim changes

**Trace:** `db.py:_ddl` bakes `embed_dim` into the `vec0` table declarations
at creation time. `reconcile_embedder` catches mismatches at runtime, but
there's no migration path: changing `embed_dim` requires deleting the store
and starting fresh. The design doc acknowledges this ("one-line change plus a
re-index") but no re-index tool exists.

**Impact:** Users who want to upgrade from bge-small (384) to bge-base (768)
lose all consolidated identity (gists, scars, the PersonaTree).

**Severity:** MEDIUM — blocks a natural upgrade path.

---

## Part IV: Failure Mode Cascading

### 4.1 The "Spool Death Spiral"

**Cascade sequence:**
1. The drain process crashes or is killed (hook timeout, OOM).
2. Orphaned `.processing` claims accumulate (reclaimed after `_RECLAIM_AGE_SECONDS = 3600`).
3. During the 1-hour window, new events accumulate in the live spool.
4. If the spool exceeds `spool_max_bytes` (100 MB), new events are **shed**.
5. The shed events are the most recent ones — the ones most likely to contain
   high-salience, identity-forming content.
6. When the drain finally resumes, it processes only the stale backlog, missing
   the shed events.
7. The consolidated identity reflects the **pre-crash** state, not the current one.

**Severity:** HIGH — the most important events are lost during the recovery window.

**Suggested fix:** (a) Reduce `_RECLAIM_AGE_SECONDS` from 3600 to 300 (5
minutes — a drain should never take an hour). (b) Log shed events to a
separate `.shed` file (append-only, bounded) for post-hoc analysis. (c) Add a
`cdms stats` field for `events_shed_total`.

### 4.2 The "Corruption → Quarantine → Silent Data Loss" cascade

**Cascade sequence:**
1. The SQLite store is corrupted (disk error, power loss during write).
2. `Database.__init__` quarantines the corrupt file and starts fresh.
3. The new store has no gists, no scars, no temperament — a blank slate.
4. The next SessionStart injects **nothing** — the model has amnesia.
5. The spool may still contain un-ingested events from the pre-corruption
   session, which are now ingested into the blank store.
6. The model operates without any guardrails until the next consolidation
   creates new (possibly different) gists.

**Impact:** Silent identity loss. The quarantine preserves the corrupt file for
recovery, but there's no automatic recovery mechanism and no alert beyond
stderr output.

**Severity:** HIGH — identity loss without user notification.

**Suggested fix:** (a) Write a `RECOVERY_NEEDED` marker file in the home
directory after quarantine. (b) `cdms doctor` should check for this marker and
offer recovery guidance. (c) Consider a `cdms restore <quarantine-file>`
command.

### 4.3 The "Embedder Fingerprint Mismatch → Permanent Capture Refusal" cascade

**Cascade sequence:**
1. User upgrades fastembed (changes the model weights under the same name).
2. The fingerprint changes (includes fastembed version — Cycle-8 fix).
3. `reconcile_embedder` raises `RuntimeError` on every write.
4. `MemoryService.ingest` propagates the exception.
5. `hooks.py:dispatch` catches it in the generic `except Exception` and logs it.
6. The hook returns `{}` (success) to Claude Code — no error visible to the user.
7. All subsequent captures fail silently until the user runs `cdms doctor`.

**Impact:** The user believes CDMS is working but no new memories are being
captured. The existing identity slowly decays (L1 episodes age, gists fade)
without any new reinforcement.

**Severity:** MEDIUM — the embedder fingerprint check is correct, but the
failure mode is silent.

**Suggested fix:** `cdms doctor` should be run automatically (or prompted) after
any fastembed upgrade. Add a `cdms doctor --auto` mode that checks and exits
non-zero if the fingerprint mismatches.

---

## Part V: Config Knob Interaction Effects

### 5.1 The "Adaptive EMA + Low Support → Permanent Trait Fragility" interaction

**Trace:** `config.py:gist_valence_ema = 0.4`, `gist_valence_ema_min = 0.05`.
The adaptive EMA formula in `consolidate.py` is:
```
ema_eff = max(ema_min, ema / sqrt(old_support))
```

For a gist with `support_count = 1`: `ema_eff = max(0.05, 0.4/1) = 0.4`
(full base rate — the gist is malleable). For `support_count = 64`:
`ema_eff = max(0.05, 0.4/8) = 0.05` (floor hit — the gist is nearly frozen).

**Interaction:** If a user explicitly creates a fact via `upsert_fact` (MCP
`store kind=fact`), the `support_count` is set to 1 and incremented by 1 each
time. But `upsert_fact` uses the **caller's stated relation**, not the
derived-from-valence relation. So a fact with `support_count=2` is still at
full malleability (`ema_eff = 0.28`), but its relation is immune to the EMA
(it's stated, not derived). This creates a "zombie trait" — high plasticity
but no direction change.

**Severity:** LOW — edge case, but it means explicit facts and emergent traits
play by different rules that aren't documented together.

### 5.2 The "crisis_threshold vs S0 weight cap" interaction

**Trace:** The Cycle-8 H-2 fix caps S0 weights so that `goal_gate_floor ×
wsum < 0.9 × crisis_threshold`. With defaults: `0.25 × wsum < 0.9 × 3.0`,
so `wsum < 10.8`. Current defaults: `wsum = 4.0` — well within bounds.

**But:** If a user sets `crisis_threshold = 0.5` (very sensitive) and
`goal_gate_floor = 0.5`, the cap becomes `0.5 × wsum < 0.45`, so `wsum < 0.9`.
With 4 weights, each must be < 0.225 — effectively disabling the salience
gate. The `_validate` function clamps this, but the user's intent (sensitive
crisis detection) is thwarted by the interaction.

**Severity:** MEDIUM — config validation prevents breakage but may silently
defeat the user's tuning intent.

**Suggested fix:** When clamping S0 weights for the crisis threshold invariant,
log a warning that explains the interaction: "Your crisis_threshold is
sensitive enough that S0 weights had to be reduced to prevent false scar
elevation. Consider raising crisis_threshold instead."

### 5.3 The "project_budget_cap + session_budget_cap" double-squeeze

**Trace:** With `project_budget_cap = 0.5` and `session_budget_cap = 0.5`, a
project with 4 sessions gets: project share = 500 (50% of K=1000). Each
session gets at most 250 (50% of 500). With 4 sessions, each gets ~125.

But if the project has only 1 session (the common case for a solo developer),
the session gets the full 500. The cap only bites when there are ≥3 sessions.

**Interaction:** A solo developer using both hooks (real sessions) and the MCP
`store` tool (which uses the default empty session) effectively has 2 sessions:
the real one and the empty one. The empty session's episodes (explicit notes)
compete with real hook-captured episodes for the session budget.

**Severity:** LOW — the empty-session issue was already addressed in Cycle-8
(H-M-2), but the double-squeeze interaction means the fix is more aggressive
than intended for single-user, multi-source projects.

---

## Part VI: Test Coverage Gaps

### 6.1 No integration test for the full write→consolidate→retrieve→inject lifecycle

**Gap:** Tests cover individual components (ingest in `test_store.py`,
consolidation in `test_consolidate.py`, retrieval in `test_store.py`, hooks in
`test_pipeline_hooks.py`) but **no test exercises the full cycle**:
1. Spool a hook event
2. Drain and ingest
3. Consolidate
4. Retrieve the resulting gist
5. Verify it appears in SessionStart context

The closest is `test_lifecycle.py`, which tests forget but not the positive path.

**Severity:** HIGH — integration bugs at component boundaries are the most
likely and the least tested.

### 6.2 No test for the hash-vs-real embedder semantic gap

**Gap:** All tests run on the hash embedder (`CDMS_EMBED_BACKEND=hash`). The
hash embedder produces vectors where cosine similarity reflects vocabulary
overlap, not semantic similarity. This means:
- Dedup threshold (0.95) catches near-exact-vocabulary episodes but misses
  semantically-identical episodes with different wording.
- Cluster threshold (0.78) groups by vocabulary, not meaning.
- The `gist_match_sim_threshold` (0.90) identity-resolution path works
  differently in hash-space vs real-space.

`test_real_embedder.py` exists but only tests the embedder itself, not the
consolidation/retrieval dynamics with real embeddings.

**Severity:** HIGH — the test suite may green-light behavior that breaks in
production.

### 6.3 No test for concurrent consolidation + retrieval

**Gap:** `test_capture_concurrency.py` tests concurrent spool appends, but no
test exercises the scenario where `retrieve` (via MCP) runs while
`consolidate` (via SessionEnd hook) is in progress. The cross-process lock
serializes consolidation against drain, but retrieval is lock-free — it can
read mid-consolidation state.

**Severity:** MEDIUM — the I-1 finding above would be caught by such a test.

### 6.4 No test for temperament leash under drift

**Gap:** `test_temperament.py` tests Phase 0 (static dials, leash distance,
near_bound, large_shift). `test_temperament_sim.py` tests the drift trajectory
harness. But there's no unit test that:
1. Sets `current ≠ seed` (simulating Phase 1b drift)
2. Verifies the leash fires correctly
3. Verifies the archetype-radius derivation holds under skewed dials

This is partially covered by the drift trajectory harness, but that's a
black-box integration test, not a unit test of the leash math.

**Severity:** MEDIUM.

### 6.5 No test for the `_infer_success` negation edge cases with Unicode

**Gap:** `test_inference.py` tests English negation patterns but not:
- Unicode negators (e.g., "не" in Russian, "没有" in Chinese)
- Mixed-script text (English tool names with CJK outcomes)
- The `_OVERRIDE_RE` matching against non-ASCII text

**Severity:** LOW — the valence inference is a crude proxy, but non-English
users get systematically inverted valence for common patterns.

---

## Part VII: Observability Gaps

### MEDIUM — O-1: No consolidation health dashboard

The `ConsolidationReport` is printed to stdout (CLI) or logged as JSON (hooks)
but there's no persistent trend data. The operator can run `cdms stats` for a
point-in-time snapshot, but cannot see:
- Is consolidation running regularly? (Last consolidation timestamp is in
  hooks logs but not in `cdms_meta`.)
- Is gist count growing, stable, or shrinking?
- Are episodes being evicted faster than they're created? (Net memory loss.)
- How many consolidation cycles have run since the last gist flip?

**Suggested fix:** Persist a `last_consolidation` timestamp and a rolling
summary (episodes_evicted, gists_created, gists_flipped) in `cdms_meta`.
Expose via `cdms stats --trend`.

### MEDIUM — O-2: No alerting on identity degradation

There's no mechanism to detect when the system is **losing** identity:
- Gist count declining over time (identity erosion)
- All gists converging to the same relation (loss of differentiation)
- Scar count growing unboundedly (guardrail inflation)
- Tempering leash approaching the radius (drift nearing limits)

**Suggested fix:** Add a `cdms health` command that compares current state
against a stored baseline and flags degradation trends.

### LOW — O-3: The log rotation doesn't surface rotation events

`hooks.py:_log` rotates at 5 MB with 3 generations but doesn't log when a
rotation happens. An operator debugging a problem may not realize the relevant
log was rotated away.

---

## Part VIII: Active Dreaming Extensibility

### 8.1 The Dreamer slot is architecturally ready but operationally stranded

The `dreamer_enabled`, `dreamer_base_url`, `dreamer_model` config knobs exist
but are completely unwired — no code path reads them. The design doc (§6)
specifies the Dreamer as a prose-rendering-only layer on top of the mechanical
consolidator.

**Extensibility assessment:**
- **Good:** The consolidator's `_extract_tuple` produces structured tuples that
  the Dreamer could render without modifying the truth path.
- **Good:** The `ConsolidationReport` provides the exact data a Dreamer needs
  (what changed, what was reinforced, what was evicted).
- **Bad:** There's no hook point in the consolidation pipeline for a Dreamer to
  intercept. It would need to be called after `_run_locked` completes, reading
  the report and producing prose — but the current code returns the report
  directly.
- **Bad:** The Dreamer's "trait-driven curiosity" (§6.2) requires scanning
  ambient sources (clipboard, files, browser), which needs OS-level integration
  that the current Python CLI architecture can't provide. The design doc
  correctly identifies this as requiring a native daemon.

### 8.2 The "research dream" requires infrastructure that doesn't exist

The full §6 vision (curiosity-weighted exploration, structured proposals,
preemptible GPU-bound research) requires:
1. An idle-detection mechanism (OS-level, not available in Python stdlib)
2. A local GPU-bound model (requires VRAM management)
3. A sandboxed execution environment (the dream must not modify the main store
   until proposals are accepted)
4. A proposal/acceptance protocol (Phase 1a of TEMPERAMENT_PLAN)

None of these exist. The mechanical consolidator is the right foundation — it
runs cheaply at SessionEnd and produces the structured data the dream would
consume — but the dream itself is a separate system, not an extension of the
consolidator.

**Severity:** LOW (design debt, not a bug) — the extensibility seams are in
the right places, but the dream is years away from implementation.

---

## Part IX: Does the System Achieve Individuation?

### 9.1 The case FOR individuation

**Evidence from the code:**
- Two CDMS instances fed different histories **will** produce different
  PersonaTrees: the gist extraction is geometry/lexicon-based, so different
  vocabularies → different objects; different outcome patterns → different
  relations; different crisis patterns → different scar sets.
- The Ebbinghaus decay is **idiosyncratic** by design: the same episode gets
  different S0 in different deployments (depending on novelty relative to
  existing store, the salience weights, and the config genotype).
- The consolidation pass is **history-dependent**: the dedup threshold,
  cluster threshold, and competition dynamics produce different survivors
  depending on the episode distribution.
- The archetype seed gives each deployment a **starting disposition** that
  shapes which episodes get high salience (via the goal gate and affect
  weights), though Phase 0 is inert.

**Verdict:** The system achieves **topic-level individuation** — it produces
a distinct map of "what this workspace/user works on and how it goes." This
is real, functional differentiation.

### 9.2 The case AGAINST character-level individuation

**Evidence from the code:**
- The gist tuple is `⟨Subject, Relation, Object⟩` — this is a **competence
  map**, not a personality. "handles_well testing" is a fact about work
  patterns, not about character.
- The relation is derived from valence, which is derived from a lexical proxy
  (`_lexical_valence`). Two agents with identical work patterns but different
  tool output verbosity get different valence, different relations, and
  therefore different "personalities" — but the difference is an artifact of
  the proxy, not of genuine character divergence.
- The temperament layer (Phase 0) is inert: `current == seed`, no drift, no
  modulation of behavior. The eight dials exist in the schema but affect
  nothing in the consolidation or retrieval pipeline.
- The Bem firewall prevents the agent from reading its own disposition, which
  means the agent cannot **act on** its individuated state. The identity exists
  in the store but has no behavioral expression.

**Verdict:** The system achieves **differentiation** (distinct memory patterns)
but not **individuation** in the strong sense (distinct behavioral
dispositions). The temperament layer is the planned bridge, but it's Phase 0 —
state only, no drift, no behavioral wiring.

### 9.3 The philosophical gap (building on Cycle-8 P-1, P-2, P-3)

Cycle-8 Part VI identified that the gist substrate is a competence map, not a
character portrait (P-1), that the "LLM never authors the tuple" discipline
creates a behaviorist prison (P-2), and that the Bem firewall is permeable
(P-3).

**Cycle-9 refinement:** The deeper issue is that CDMS individuates along the
**wrong axis** for the claim it makes. The design doc says "Identity =
f(History)" and the system delivers "Workspace-Knowledge = f(History)." These
are not the same thing. A CDMS instance that has worked on payments for 6
months and one that has worked on auth for 6 months have different
PersonaTrees — but they have the same *character* (same config, same
archetype, same inert temperament). The individuation is **contextual** (what
I've seen), not **dispositional** (how I respond).

The temperament layer (§8) is explicitly designed to close this gap, and the
TEMPERAMENT_PLAN's research grounding is impressive. But until Phase 1b ships
with a wired behavioral effect, the "Identity = f(History)" claim holds only
for the weak (contextual) reading, not the strong (dispositional) reading.

**Severity:** This is not a bug — it's an honest assessment of where the
system stands relative to its own design ambitions.

---

## Part X: Summary & Prioritized Findings

### CRITICAL

| ID | Finding | Part |
|----|---------|------|
| I-1 | SessionStart reads without lock — inconsistent context injection | I |

### HIGH

| ID | Finding | Part |
|----|---------|------|
| I-2 | Dedup uses stale access_count — undermines testing effect | I |
| I-3 | Gist centroid drifts toward sentinel vector | I |
| D-1 | MemoryService god object — read/write coupling | III |
| D-2 | Consolidation step ordering is implicit, fragile | III |
| F-1 | Spool death spiral — shed events are the most important | IV |
| F-2 | Corruption→quarantine→silent identity loss | IV |
| T-1 | No full-lifecycle integration test | VI |
| T-2 | All tests on hash embedder — semantic gap untested | VI |
| E-2 | Budget starvation cascade across consolidation cycles | II |

### MEDIUM

| ID | Finding | Part |
|----|---------|------|
| I-4 | Forget spools can race (double-forget edge) | I |
| E-1 | Hash embedder causes identity freezing in tests | II |
| D-3 | Content terms tokenizer is English-only | III |
| D-4 | No embed_dim migration path | III |
| K-2 | crisis_threshold interaction defeats user intent | V |
| O-1 | No consolidation health dashboard | VII |
| O-2 | No identity degradation alerting | VII |
| F-3 | Embedder mismatch → silent permanent capture refusal | IV |
| T-3 | No concurrent consolidation+retrieval test | VI |

### LOW

| ID | Finding | Part |
|----|---------|------|
| E-3 | Temperament inertia trap (Phase 1b without 1a) | II |
| K-1 | Explicit facts vs emergent traits play by different rules | V |
| K-3 | Double-squeeze on solo developer with MCP notes | V |
| T-4 | No temperament leash under drift unit test | VI |
| T-5 | No Unicode negation test for `_infer_success` | VI |
| O-3 | Log rotation events not surfaced | VII |
| D-5 | Active dreaming extensibility seams are correct but dream is distant | VIII |

---

## Architectural Improvement Recommendations

### A1: Snapshot-based SessionStart injection (fixes I-1)

Instead of reading the live DB during SessionStart, persist a "context
snapshot" at the end of each consolidation pass:
```python
# In Consolidator._run_locked, after all steps:
snapshot = self._build_context_snapshot()  # scars + top gists + recent accessible
self.db.set_meta("session_start_context", json.dumps(snapshot))
```
SessionStart reads the snapshot (one `get_meta` call, no DB scan, no lock
needed). The snapshot is always consistent because it was built inside the
lock. Staleness is bounded to one consolidation cycle.

### A2: Split MemoryService into Reader/Writer (fixes D-1)

```python
class MemoryReader:
    """Lock-free, no embedder. For SessionStart, history, list_paths."""
    def __init__(self, db: Database): ...
    def retrieve(self, query, ...): ...  # FTS-only, no vector
    def history(self, ...): ...
    def list_paths(self): ...

class MemoryWriter:
    """Requires embedder. For ingest, consolidate, pin_scar, forget."""
    def __init__(self, cfg, db, embedder): ...
    def ingest(self, ev): ...
    def forget(self, ...): ...
```

The MCP server's `history` and `list_paths` tools use `MemoryReader` (no ONNX
load). The `retrieve` tool uses `MemoryWriter` (needs embeddings). The
`SessionStart` hook uses `MemoryReader` with the snapshot from A1.

### A3: Consolidation pipeline with explicit phase ordering (fixes D-2)

```python
@dataclass
class ConsolidationPhase:
    name: str
    fn: Callable
    mutates: list[str]  # which DB tables this phase touches
    requires: list[str]  # which phases must run first

PHASES = [
    ConsolidationPhase("elevate_scars", _elevate_scars, ["episodic", "scars"], []),
    ConsolidationPhase("dedup", _dedup, ["episodic"], ["elevate_scars"]),
    ConsolidationPhase("evict", _evict, ["episodic"], ["dedup"]),
    ConsolidationPhase("compete", _compete, ["episodic"], ["evict"]),
    ConsolidationPhase("gist_aggregate", _aggregate, ["gist", "edges"], ["compete"]),
    ConsolidationPhase("gist_decay", _decay, ["gist"], ["gist_aggregate"]),
]
```

### A4: Identity degradation detector (fixes O-2)

Persist a rolling baseline in `cdms_meta`:
```json
{"identity_baseline": {
    "gist_count": 42, "scar_count": 5,
    "unique_relations": 3, "last_checked": "2026-06-18T..."
}}
```
`cdms health` compares current state against baseline and flags:
- gist_count declining >30% over 10 cycles
- unique_relations dropping to 1 (all traits same direction)
- scar_count growing >2× (guardrail inflation)

### A5: Embedder upgrade tool (fixes D-4)

```bash
cdms re-embed --new-dim 768 --new-model bge-base-en-v1.5
```
Re-embeds all stored vectors (episodic, gist, scars) with the new model,
updates the fingerprint, and vacuums. Non-trivial but preserves identity
across model upgrades.

---

## Closing Assessment

Cycle 9 shifted from "find individual bugs" (Cycles 1–8) to "evaluate the
architecture as a system." The individual components are well-engineered — the
salience math is sound, the consolidation pipeline is thorough, the security
hardening is impressive. The architectural concerns are about **boundaries**:
where one component's assumptions end and another's begin.

The most important finding is I-1 (SessionStart reading without the lock) —
this is the single point where CDMS's memory shapes the model's behavior, and
it's reading a possibly-inconsistent state. The snapshot-based fix (A1) is
simple and eliminates the entire class of mid-consolidation reads.

The individuation assessment (Part IX) is the most nuanced finding. CDMS
achieves genuine topic-level differentiation — two instances with different
histories produce meaningfully different PersonaTrees. But it does not yet
achieve dispositional individuation — the temperament layer is inert, and the
agent cannot act on its own identity. This is an honest place to be: the system
does what it claims (contextual differentiation) while the stronger claim
(dispositional identity) awaits the temperament layer's Phase 1b.

The design debt items (D-1, D-2) are the most likely to compound: the god
object and the implicit step ordering will become harder to fix as more code
accumulates around them. Addressing them now, while the codebase is still
~4,500 LOC, is far cheaper than addressing them at 10,000 LOC.

**Bottom line:** CDMS is a well-architected system with a clear vision and
honest documentation. The architectural concerns are real but addressable.
The system achieves what it currently claims (contextual differentiation) and
has a credible path to the stronger claims (dispositional individuation) via
the temperament layer. The most impactful next step is A1 (snapshot-based
SessionStart) — it's the simplest fix with the highest impact on correctness.

---

*End of Cycle 9 — Architecture, Design Debt & Emergent Behavior audit.*
*All findings independently verifiable against commit 51994b0.*
