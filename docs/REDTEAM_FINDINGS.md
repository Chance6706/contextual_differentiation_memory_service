# Red-Team Audit & Remediation (pre-Phase-0)

Three adversarial cycles were run before building the §8 temperament layer, on the
premise that latent defects in the always-running core compound silently *over time*.
This file records what was found, fixed, and deliberately deferred. The CI suite
forces the hash embedder, so a non-hash test path (`tests/test_real_embedder.py`)
covers the real model. Suite: 38 → 77 (Cycle 1) → 110 (Cycle 2) → 135 (Cycle 3)
tests, all green.

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
- **Prose Renderer "Dreaming" / httpx path is dead code** (Cycle 2) — `render_*` (formerly
  `dreamer_*` pre-naming-PR) / `http_*` config is never imported; no runtime risk. Left as a
  documented placeholder for CDMS-B (designed-not-built); see `docs/DEVIATIONS.md` L6.

## Plan-level corrections
Recorded in `docs/TEMPERAMENT_PLAN.md` §8 (P1–P7 + Gemini's "Boiling Frog" exit-gate).

## Cycle 3 — broadened again (7 angles) + re-audit of the Cycle-2 fixes

Seven agents: re-audit of the Cycle-2 fixes, privacy/right-to-forget completeness,
adversarial attacks on the identity/cognitive math, concurrency/atomicity/crash
durability, long-horizon resource exhaustion + numerics, the installed MCP
integration surface, and the REAL (non-hash) embedder path CI never exercises.
The re-audit again paid off: **the Cycle-2 corrupt-DB quarantine had introduced a
CRITICAL data-loss regression.**

**Fixed in Cycle 3 (commit `122e29d`):**

| Sev | Defect | Fix |
|-----|--------|-----|
| CRIT | Lock contention misread as corruption → healthy store quarantined/WIPED. `sqlite3.OperationalError("database is locked")` is a `DatabaseError` subclass the Cycle-2 quarantine caught; a multi-second consolidation overlapping a hook open trips it. | `Database._is_corruption`: quarantine only on true corruption signatures; re-raise lock/busy/config-induced errors. |
| HIGH | `inf` / astronomically-large config bypassed `_validate` (`DECAY_HALFLIFE_DAYS=inf`→decay off; huge `MAX_FIELD_CHARS`→DoS cap defeated), via env *or* JSON. | require `math.isfinite` + a sane UPPER bound on every numeric field. |
| HIGH | No cross-process lock: concurrent consolidate/forget → duplicate gists, lost cycle increments, half-built persona, and a pass rebuilding gists from episodes a `forget` is mid-delete on (resurrecting forgotten content). | new `lock.py` (flock/msvcrt advisory lock) serializes `Consolidator.run` + `MemoryService.forget`; second pass skips rather than blocking a hook. |
| HIGH | `forget` left raw **pre-redaction** secrets in the spool, and deleted content stayed recoverable from db free pages (logical-only delete). | `PRAGMA secure_delete=ON`; `VACUUM`+WAL-truncate after forget; purge matching spool events by cwd/session. |
| HIGH | A non-dict spool line (`42`, `[1,2]`) crashed `reconstruct_turns` → destroyed a whole session + orphaned the claim; a large spool OOM'd the drain (~8.7× RSS). | stream the drain (`iter_turns`+`_stream_spool`, O(session) memory); skip non-dict events; cap the spool (`spool_max_bytes`, shed over cap). |
| HIGH | SIGKILL of a drain after it claimed the spool orphaned the turns forever (no reclaim scan). | `_reclaim_orphans`: re-ingest `*.processing` claims whose owning pid is dead (or stale by age). |
| HIGH | Unbounded L3 scar table — a recurring crisis minted a fresh permanent ~4 KB scar every cycle. | `find_duplicate_scar` (per-project cosine) dedups on insert in both `pin_scar` and `_elevate_scars`. |
| HIGH | Embedder silently truncated long input at ~512 tokens → vector/FTS asymmetry and tail-collision; degenerate-input sentinel (C2) was dead code on the real backend. | explicit `embed_max_chars` cap; degeneracy decided at the TEXT level so the sentinel works on BOTH backends; assert model output dim == `embed_dim`; fingerprint carries the fastembed version (catches weight drift on upgrade). |
| MED | `_infer_success` positive-override inverted a real failure to `True` ("no errors **but the test failed**"). | override is no longer an unconditional short-circuit: strip override phrases, then a *separate* failure marker still reads as failure. |
| MED | H4 catastrophe regex/command tier matched a dangerous command's mere presence → benign "git reset --hard to discard local edits" auto-pinned as a permanent scar. | split into harm-OUTCOME phrases (stand-alone) vs dangerous COMMANDS that elevate only when the deed also records actual harm. |
| MED | `forget --project` exact-string match leaked content under trailing-slash / subdirectory cwds. | path-normalized prefix match (`_project_match`). |
| MED | install/uninstall raised a raw traceback on a non-dict `hooks`/settings; `_atomic_write_json` replaced a symlinked `settings.json` with a detached file. | refuse loudly on malformed shape (`_require_dict`); write THROUGH a symlink to its target. |
| LOW | MCP negative `k`/`limit` negative-sliced results; `project=""` was a model-accessible cross-project read opt-out; `_sanitize` let the invisible Unicode TAG block through. | clamp `k`/`limit` (+ `ge=1` schema bound); empty project ⇒ launch cwd (global is operator/CLI-only); strip `U+E0000–E007F`. |

**Cycle-3 verified-sound (no change):** individuation is not collapsible (identical
vocab + opposite valence → trait Jaccard **0.000**; subject is the cwd basename,
never parsed from content); thrash stays damped (alternating max-valence → 0 flips);
the capped-proportional budget holds under a 3000-turn flood (attacker ≤50%, 0
victim evictions); row-level atomicity under SIGKILL mid-consolidate (0 orphaned
vec/FTS rows in 8 trials; cycle counter stays put); retrieve-during-consolidate
never crashes/tears; WAL serializes drain+ingest vs consolidate; decay/accessibility/
float-centroid numerics are stable at 10⁶–10⁹ scale (clean underflow, no NaN/Inf);
log rotation bounds the log to ~10 MB; `support_count = max(...)` does NOT cause
unbounded gist growth (decay still evicts; live set self-bounds); MCP stdout stays
pristine and tool-arg validation/SQL-FTS injection defenses hold; the real embedder
loads/refuses/contains-NaN correctly and is deterministic + thread-safe.

### Cycle 3 detail — adversarial attacks on the identity / cognitive math itself

Surface: can a crafted INPUT STREAM (not code/config edits) corrupt the personality?
Repro harness: `tools/redteam_cycle3.py` (offline, `CDMS_EMBED_BACKEND=hash`). All
numbers below are from that harness against the live pipeline; no source was edited.

**Headline claims that HELD up:**
- **Individuation is robust.** Same store, two projects, *identical* vocab, opposite
  valence → trait (relation,object) Jaccard overlap = **0.000**; each project's gist
  carries its own project column + valence. Project-name *spoofing via content* fails
  (subject = basename of `e.project`/cwd, never parsed from text). No cross-project
  gist contamination. (consolidate.py `_aggregate_gists` partitions by project first.)
- **Thrash is fully damped.** 12 cycles of alternating max-valence evidence →
  **0 flips**. The valence EMA (α=0.4, ±0.15 thresholds) needs ~2 consecutive
  saturated cycles to cross, and alternation never accumulates.
- **Budget cap holds.** Victim (12 real turns) vs attacker (3000-turn flood): attacker
  capped at exactly 50% (500/K=1000), victim keeps 500, **0 victim episodes evicted**,
  none below retention floor. No starvation, no flood-eviction of the victim tier.
- **Injection framing holds.** Poisoned gist is still wrapped in `<memory:persona>` as
  untrusted DATA with the "prior belief, not ground truth" hedge (Cycle 1–2 fixes).

**Confirmed defects / gameable surfaces (severity-sorted at end):**

| ID | Sev | Defect | file:line | Numbers |
|----|-----|--------|-----------|---------|
| X1 | HIGH | **Ossification via monotonic `support_count = max(...)`** (the deferred L3, now quantified). A *single* adversarial burst mints a near-permanent junk trait, and later weak evidence can never shrink it. | `consolidate.py:346`, decay `:386` | 30-turn burst → support_count=29 → **~315–324 idle cycles** to forget vs design's "1 support". 5 later 2-episode touches leave support_count pinned at 30 (never lowers). |
| X2 | HIGH | **Decay-clock games (both directions).** Every consolidation run advances the cycle counter *even on an empty episodic set* ("gist maintenance only"), so an actor who can trigger consolidation repeatedly ages the whole L2 decay clock with zero evidence; conversely, never consolidating freezes identity forever. | `consolidate.py:140,168-169`, `:376-390` | **Accelerated erosion:** 288 rapid empty cycles (≈288 s wall-clock via a consolidate loop) erased a support=17 trait that represents weeks of real work. **Freeze:** 10 simulated years, never consolidate → gist `last_cycle` frozen, trait unchanged (while L1 episodic accessibility wall-clock-rots to ~0). |
| X3 | MED | **Dedup silently drops contradicting valence (first-writer-wins).** `_dedup` merges on text-embedding only (≥0.95), folds salience via `max()`, but **discards the newer episode's valence/outcome entirely** — it keeps the *older* survivor's valence. A later turn that reuses similar phrasing but flips the outcome is deleted before it can update the trait. | `consolidate.py:230-245` (esp. 232-239) | Two text-identical turns, valence +1.0 then −1.0 (cos=1.0 ≥ 0.95) → after dedup only +1.0 survives; the −1.0 evidence vanishes. Across 12 alternating cycles the gist stayed valence=1.0 / `handles_well` despite 24 negative turns. |
| X4 | MED | **Relation "flip" is largely unreachable; contradiction spawns a parallel contradictory gist instead.** Because the object label is derived from dominant *content terms* (incl. the action verb), a behavior reversal usually arrives with different vocabulary ("shipped" → "regressed"), routing it to a *new* `(subject, object)` gist rather than flipping the existing one. Result: `handles_well widget shipped` and `has_trouble_with widget regressed` coexist permanently. | `consolidate.py:332-369`, `_extract_tuple:439-454` | Sustained reversal (4 positive then 4 negative cycles) → **0 flips**, two coexisting opposite-relation gists for the same logical trait. The flip path only fires when the object string stays byte-identical while valence crosses ±0.15. |
| X5 | MED | **Salience proxy is gameable (S0 ranking, not scar gate).** Trivial spam crafted to hit every additive driver (novelty≈1, self-ref keyword, success, mutating tool) reaches S0=3.700 (92.5% of the 4.0 max) and clears the `crisis_threshold`=3.0 S0 gate; a genuinely important *read-only* finding scores far lower. | `store.py:159-195`, `salience.py:43-58` | Spam S0=**3.700**; important non-mutating security `Read` (near-dup, novelty≈0, contingency 0.1, goal 0.5) S0=**0.232** → spam outranks the real finding **~16×**. (Scar elevation still blocked by catastrophe-in-deed + valence gates — only the *ranking/injection* is gamed, not L3.) |
| X6 | LOW/INFO | **Dedup starves identity formation for *consistent* behavior, and the cold-start fallback dumps raw poisoned episodic text.** 40 near-identical on-topic turns → 39 deduped → 1 survivor → below `min_cluster_support` → **no gist forms at all**. Separately, when <5 gists exist, SessionStart injects raw episodic turns verbatim, so attacker content (e.g. "sudo rm production database …") reaches context unsummarized (still fenced as DATA). | `consolidate.py:213-245,292,309`; `hooks.py:108-116` | Identical-vocab adversary produces *zero* personality; ironically the system is more robust to identical spam than to lexically-varied spam. |

**Honest tradeoff notes (fact vs inference):**
- X1/X2 are partly *inherent* to the design choice "activity-based, not wall-clock,
  decay + `max()` support so heavy traits persist." The continuity benefit is real;
  the cost is the erosion/ossification asymmetry above. Fact: the asymmetry is large
  and one-burst-triggerable. Inference: a sub-linear support cap (e.g.
  `support_count = round(0.7*old + 0.3*new)` or `min(old+1, …)`) plus tying decay to a
  monotonic *wall-clock-anchored* cycle estimate would blunt both without losing
  continuity — but that is a design change, not a clear bug.
- X3/X4 are the flip side of the (correctly working) anti-thrash damping. The system
  errs hard toward *stability*: it would rather drop or fork contradicting evidence
  than risk oscillation. Fact: sustained, genuine reversals therefore often fail to
  update the existing trait. Suggested fix for X3: when dedup supersedes, blend the
  survivor's valence with the dropped episode's (or keep the *newer* outcome) instead
  of discarding it — dedup should preserve emotional evidence even when it drops the
  duplicate row.
- X5: the surprisal proxy can't see model logit entropy (documented limitation in
  `store.py`); the lexical/novelty proxy is inherently spoofable. Suggested mitigation:
  cap the additive self-ref/affect contribution when the turn is also high-novelty +
  trivial-length, or weight contingency by *verified* tool effect rather than mere
  tool class.

**Severity-sorted confirmed findings:** X1 (HIGH) · X2 (HIGH) · X3 (MED) · X4 (MED) ·
X5 (MED) · X6 (LOW/INFO).

**Disposition (X1–X6 are DEFERRED-by-design, not fixed in Cycle 3):** these are
intrinsic tensions of the validated design (activity-based decay + `max()` support
for continuity; anti-thrash valence damping; a logit-free salience proxy), not clear
bugs, and every "fix" trades away a property the design deliberately bought.
Specifically **X2 was investigated as a fix and reverted**: gating the cycle clock on
"real work" breaks the *one-consolidation-==-one-cycle* invariant that makes wall-clock
absence harmless (it failed `test_absence_does_not_age_identity` and the drift-tool
EROSION control), and forcing erosion requires the privileged ability to invoke
consolidation repeatedly. The honest mitigations (sub-linear support update for X1,
valence-blend-on-supersede for X3, novelty×triviality cap for X5) are design changes
recorded here for the survivability-testing work, to be weighed against the continuity/
stability they would cost — they are not silent bugs to patch. CRIT/HIGH defects on the
*other six* surfaces (durability, privacy, embedder, MCP, config, concurrency) WERE
fixed (table above).

## Cycles 4–6 — external reports + metaphysical disposition

External, cross-lineage passes were run from the prompt packs in `redteam/` and their
reports saved alongside: Cycle 4 Pass A (`CYCLE4_DEEPSEEK_REPORT.md`, DeepSeek V4 Pro),
Cycle 5 (`CYCLE5_GLM52_REPORT.md`, GLM-5.2), Cycle 6 Pass A (`CYCLE6_OWL_ANALYSIS.md`,
OWL Alpha). Per `redteam/README.md`, an external report is **untrusted input** until
each CRIT/HIGH is independently reproduced.

**This commit dispositions only the *metaphysical / framing* findings — by documentation,
not code.** The trigger was a recurring reader-misconception: external models read the
docs as *claiming to create consciousness / a real subject* and reacted in opposite
directions — GLM deflationarily (M-CRIT-1 "identity = f(history) is a lossy JPEG, not a
photograph"; M-HIGH-4 autonomy is "the philosophical zombie of agent autonomy"), OWL
enthusiastically (the "ego-simulacrum" reframe, and Part VII's "the ego is information…
the *same AI in a new body*"). Both target a claim CDMS does not make.

Disposition: keep `Identity = f(History)` as the thesis and add an explicit
**ontological + build-status** clarification (README "What CDMS claims — and what it does
not"; DESIGN §1.1a). The stated boundary: CDMS is a claim about **individuation**, not
phenomenal consciousness — it *individuates, does not animate*; it is **entirely
mechanical/reactive today**, with the "what can I become" self-direction belonging to the
designed-not-built §6 active-dreaming pillar; and substrate-independence means *content*
carries over while *expression* changes (OWL Part IV), explicitly **not** "the same AI in
a new body" (OWL Part VII). OWL's *headline* recommendation — rebrand to "ego strapped
over the id" — was **declined**: "ego" unqualified raises the very misread it would aim to
prevent, so the simulacrum framing is kept as a deflationary gloss, not the marquee.

**Design-level dispositions (added after pressure-testing).** Two further design-axis
findings from these passes were pressure-tested (independent adversarial passes + a
factual grounding pass) and recorded as **open design threads**, since the relevant layer
(§6 dreaming) is designed-not-built and there is nothing to patch in code:
- **GLM M-HIGH-2 — "topic-frequency table, not a personality" (tuple expressiveness)** →
  **DESIGN §10.5**. Verdict: *thin-but-fixable*. The substrate is sufficient (and tested)
  for individuation/differentiation/curiosity/trait-flip, but is a **competence-map**: it
  lacks a HOW/style channel. A second-order pass corrected the aim — the gap is in the
  **phenotype portrait** (the `SessionStart` self-description), **not** the §8 temperament
  dials (which are genotype seed/multipliers driven by §8.7 outcome-attribution, not
  gist-readers). GLM's "3-valued relation" is a reduction fallacy (ignores continuous
  valence + centroid + N-gist composition); OWL's "disposition recoverable" over-claims
  (conflates competence- with temperament-disposition); the Jaccard 0.000 tests domain
  separation, not richness. Fix is mechanically-extractable at read-time from L1 (history-
  authored *features*, not designer-authored *labels*), plus fuller centroid/edge-graph
  use and a separate mood object — no LLM-authored self-fiction.
- **External-action authority gap (not raised verbatim by any pass; OWL Part VI's
  "boundary violation" hints at it)** → **DESIGN §10.4**. The self-edit gate is not a
  world-action gate. Surviving principles: delegate to the host's permission model (no
  CDMS side-channel); dreaming is research-only with side-effecting experiments deferred
  to a waking session (consent is void for unattended action); contain-don't-classify (a
  venv is not a sandbox); "research-only" already sits at net-read + untrusted-ingest.

**Not addressed here (open engineering track):** the *mechanical* code-level findings from
these passes — e.g. GLM C-HIGH-1 (drain not under the cross-process lock), C-HIGH-2
(`get_embedder()` singleton ignores config changes), C-HIGH-3 (`_associate`
read-modify-write race), and the DeepSeek/Owl mechanical items — remain to be triaged and
**independently reproduced** before any fix, in a later cycle. They are out of scope for
this change.

## Cycle 7 — triage of the open Cycle 4–6 mechanical findings

The external reports were treated as **untrusted until independently reproduced** (per
`redteam/README.md`). Extraction: GLM-5.2 (Cycle 5) = 3 HIGH + 8 MED + 3 LOW; DeepSeek
(Cycle 4) = 1 CRIT + 2 HIGH + 5 MED + 4 LOW; OWL (Cycle 6) = **0 mechanical** (purely
philosophical, already dispositioned). Each was reproduced, then FIXED / REFUTED /
DEFERRED. Regression tests in `tests/test_cycle7_triage.py`.

**FIXED (reproduced → fixed → test):**
- **A7-H1** (HIGH, `config.py`) — `_validate` left the S0 weights and ~12 thresholds
  unchecked; `CDMS_W_SURPRISE=1e9` / `CDMS_DEDUP_SIM_THRESHOLD=2.0` silently disabled the
  salience gate / dedup. Now bounded (incl. valence/threshold ranges, http_port).
- **A0-C1** (CRIT-on-Windows, `db.py`) — `_open` leaked the OS file handle on a failed
  open, so the quarantine `os.replace` can't rename the corrupt file on Windows → daemon
  wedged. `_open` now closes the connection on failure.
- **C-HIGH-2 / A3-M1** (HIGH, `embeddings.py`) — `get_embedder()` returned the first
  singleton forever, ignoring later config (model/dim/max_chars/backend). Now keyed on
  those; rebuilds on change.
- **C-HIGH-1** (HIGH, `pipeline.py`) — `drain_and_ingest` ran without the cross-process
  lock, so a drain could ingest into a store mid-consolidation (stale snapshot →
  missing/duplicate gists). Drain now holds the lock (short timeout + skip-on-timeout;
  spool preserved). Safe — drain is only called at top level, never while the lock is held.
- **C-HIGH-3** (HIGH) — the *stated* mechanism (touch vs set_salience) is **partly
  REFUTED**: those write disjoint columns and cannot corrupt each other. The real race
  (ingest `_associate` vs consolidation's salience renormalization, and ingest-vs-ingest)
  is closed by the same drain-under-lock fix. *Residual:* a direct MCP `store` ingest
  bypasses drain, so a concurrent MCP-store-vs-consolidation `base_salience` race remains
  — narrow (serial stdio MCP) and self-healing (next `conserve_budget`); deferred.
- **A2-M1** (MED, privacy) — `forget(session=…)` leaves session-derived gists behind.
  ⚠️ **A first fix was SHIPPED THEN REVERTED.** The edge-based `gists_orphaned_by` rule
  (delete a gist whose support edges are all inside the forgotten set) was caught by the
  post-Cycle-7 double review (finding **H1, HIGH**): `delete_episodic` prunes a gist's edges
  when a supporter is **evicted**, so the residual edges underestimate provenance — a later
  session-forget would erase genuine MULTI-session traits (identity loss) once one session's
  episodes had aged out. Reverted to episodes-only forget; `gists_orphaned_by` removed; a
  regression test asserts session-forget never erases gists. **Re-DEFERRED:** a correct
  scoping needs **persisted per-gist session provenance** (a schema change), not residual
  edges. Gists remain forgettable by project/id (which always worked).
- **C-MED-6** (MED, `pipeline.py`) — `_infer_success` negation window was a fixed 10 chars,
  missing multi-word negators ("without any errors") and flipping success→failure. Now the
  last-3-words window (catches multi-word negators; a far-back negator can't wrongly negate).

**PARTLY REFUTED:**
- **A0-M1** (MED) — "the regex tier is dead code" is **refuted** (it is reachable, e.g.
  `reset --hard … wiped`). But "the deed-gate causes false negatives" is **real** (double
  review): a dangerous command described without a `_HARM_TOKENS` word was not elevated.
  The harm-token gate is the deliberate Cycle-3 precision fix (avoids re-pinning routine
  work), so this is an **accepted recall gap, now narrowed** — `_HARM_TOKENS` widened with
  unambiguous harm words ("rewrote", "rewritten", "nuked", "blew away", "wiped out",
  "trashed", "clobbered"), tested. (Catastrophes with *no* harm word remain non-elevated by
  design; the episode is still stored, and `store kind=scar` is the explicit escape hatch.)

**DEFERRED (reproduced, real, but low-impact / tradeoff / operational / out-of-code-scope):**
- **C-MED-1** touch on deleted/deduped episode → lost reinforcement: **partly PROMOTED
  (Cycle-7 Phase 3).** The substantive concern (deduped survivors under-counted) is now
  fixed — supersession folds the dropped duplicate's **full** `access_count` into the
  survivor via `bump_access` (was only `+1`). The *residual* (a retrieve→touch on an
  episode a concurrent consolidation just deleted) stays DEFERRED: it is a benign no-op
  (`UPDATE` 0 rows, verified) on the hot read path, self-healing, not worth serializing.
- **C-MED-2** FTS has no phrase queries: recall *quality*, GLM self-downgraded; acceptable.
- **C-MED-3** `config.json` string/path fields (e.g. `home`) unvalidated: trust boundary —
  the file lives in the user's own `CDMS_HOME`; write access there already grants full control.
  ⚠️ **Contingent defer (double review):** this holds *only while the Prose Renderer stays unwired*.
  `render_base_url`/`render_enabled` (formerly `dreamer_*`) are currently consumed by **zero code**
  (verified); the moment a future cycle wires the Renderer to make HTTP requests, an attacker-controlled
  `render_base_url` becomes an SSRF / memory-exfiltration vector — **re-triage and promote then.**
- **C-MED-4** Windows `msvcrt.locking` defeated by manual lock-file recreation: Windows-only,
  requires deleting the lock file mid-pass; narrow.
- ~~**C-MED-5** ReDoS in `redact_secrets`~~ → **✅ PROMOTED & FIXED (Cycle-7 Phase 6):** the
  name-prefix/suffix quantifiers around the keyword are now BOUNDED (`{0,64}`), so the
  pattern can't catastrophically backtrack even if length-clipping is bypassed. Test: an
  adversarial 10k-char input completes in <1s; normal redaction unchanged.
- **C-MED-7** `_content_terms` decomposes paths into filename fragments: representational
  coarseness, tracked under the §10.5 portrait-richness thread.
- ~~**C-MED-8 / A5-H1** O(n) `all_gist`/`all_scars` on retrieve & `find_duplicate_scar`~~
  → **✅ PROMOTED & FIXED (Cycle-7 follow-up, Phase 1):** `_materialize` and
  `find_duplicate_scar` now fetch only the hit/candidate ids via `get_gists_by_ids` /
  `get_scars_by_ids` (chunked `WHERE id IN`), not the whole table. Integration test proves
  retrieve results are byte-identical with whole-table scans forbidden
  (`tests/test_cycle7_deferred.py`).
- ~~**A1-M1** silent consolidation-skip on lock timeout~~ → **✅ PROMOTED & FIXED
  (Cycle-7 Phase 2):** a skip now increments a durable `consolidations_skipped` counter +
  `last_consolidation_skip` timestamp in meta (surfaced by `cdms stats`), sets
  `ConsolidationReport.skipped`, and emits a stderr warning — repeated skips (a wedged
  holder) are now visible. Integration test holds the lock and asserts the counter advances.
- ~~**A2-M2 / A5-L2** quarantined `.corrupt-*` files hold plaintext, never auto-deleted~~ →
  **✅ PROMOTED & FIXED (Cycle-7 Phase 8):** `cdms doctor --purge-quarantines` scrubs the
  forensic `.corrupt-*` artifacts (test included). (`secure_delete` already protects the
  live store; orphaned `.processing` files are reclaimed by the next drain.)
- ~~**A6-L1** TOCTOU in install symlink resolution~~ → **✅ PROMOTED & FIXED (Cycle-7
  Phase 7):** `_atomic_write_json` now applies `realpath` unconditionally (idempotent for
  non-symlinks) instead of an `is_symlink()` check-then-use, closing the swap window.
  Test: write-through-symlink still updates the target; plain paths unaffected.
- ~~**A7-L1** no cross-field config consistency checks~~ → **✅ PROMOTED & FIXED (Cycle-7
  Phase 5):** `_validate` now repairs jointly-nonsensical config — inverted relation
  thresholds, `embed_max_chars > max_field_chars`, and a broken `cluster <= gist_match <=
  dedup` order — to defaults, with a warning. Test covers each.
- **A7-L2** hash-only CI never exercises the real embedder: CI infrastructure, not code
  (`test_real_embedder.py` exists and runs locally).
- ~~**C-LOW-1** log rotation keeps one generation~~ → **✅ PROMOTED & FIXED (Cycle-7
  Phase 4):** keeps N=3 generations (`.1`..`.3`), bounded at ~N*max_bytes. Test asserts
  `.1/.2/.3` exist and `.4` never does.
- **C-LOW-2** `top_gist` ordering gameable via frequency inflation: same class as the
  deferred-by-design X5 (salience gaming); deferred with it.
- ~~**C-LOW-3** dependency upper bounds~~ → **✅ PROMOTED & FIXED (Cycle-7 Phase 9):** added
  `sqlite-vec<0.2` (vec0 format — the open risk, not covered by the embedder fingerprint) and
  `fastembed<1.0` caps, set above installed 0.1.9 / 0.8.0 so no resolver breakage.

### Double adversarial review of the Cycle-7 diff

Two independent reviews (correctness/concurrency; security/abuse + adjudication audit) of
`95d1135..HEAD`. Suite 204→206 green throughout. Outcomes:
- **H1 (HIGH, NEW REGRESSION) — fixed by REVERT.** The A2-M1 gist-orphan rule erased
  multi-session gists after eviction; reverted (see A2-M1 above). The single most important
  catch — it attacked the core identity-preservation invariant under normal operation.
- **Drain-skip silence (B) — FIXED.** Drain now records `drains_skipped`/`last_drain_skip`
  (surfaced by `cdms stats`) + a stderr warning, mirroring the A1-M1 consolidation-skip
  signal, so a lock-starved drain that could back the spool up to its shed cap is visible.
- **Config repair made minimal (M1) — FIXED.** Clamp the offender (e.g. `embed_max_chars`
  DOWN to `max_field_chars`; lower only the sim-threshold offender) instead of resetting
  fields the operator deliberately set; S0 weight bound tightened 1e6→1e3.
- **Purge glob tightened** to `*.corrupt-[0-9]*` so a stray user file isn't collateral.
- **A0-M1 relabelled** partly-refuted; `_HARM_TOKENS` widened (above).
- **C-MED-3 annotated** as a contingent defer (above).
- Both reviews confirmed **no fix opened a serious new hole**; `bump_access`,
  `get_*_by_ids`, the embedder key, the drain-lock (no deadlock/nesting; turns deferred not
  lost), and the `realpath` change were independently verified sound.

## Re-run audit (Cycle 7, Pass C) — the external review read a stale revision

The OWL Cycle-7 report claimed to verify the branch tip but had actually read a **pre-revert
revision**: it certified the A2-M1 gist-orphan deletion as "VERIFIED FIXED" and praised the
since-**removed** `gists_orphaned_by` in detail (its test count / `doctor` glob matched the
older tree, not the tip). Re-auditing the **true tip** (three parallel source audits + numeric
checks) confirmed the joint-leash math sound and N-MED-1 (float comparison) misguided (it
matches immutable *seeds*), but surfaced **8 real defects**, all fixed and regression-tested.
Full suite **229 passed**. Landed in **PR #15**.

- **HIGH — substring success-inference.** `_infer_success` matched negators / OK+ERR markers /
  positive-override phrases as bare **substrings**, so ordinary words flipped a real failure to
  success/neutral and poisoned stored valence (`"tokens"`⊃`"ok"`, `"casino"`⊃`"no"`,
  `"casino errors"`⊃`"no errors"`, `"annotation"`⊃`"not"`). Now **word-boundary** matching
  (whole-token negators, `n't` suffix, leading-`\b` regex for phrases/markers/overrides; stems
  still match inflections). This is the bug the C-MED-6 negation rewrite was *believed* to have
  fixed — the prior review blessed the diff without exercising the marker sets.
- **MED — partial-seed archetype mixing.** A truncated temperament store whose archetype label
  was also lost was completed from the *default* archetype, mixing two dispositions and
  weakening the leash. Added `match_archetype_by_partial_seed`; the partial-heal path now
  recovers the archetype from the seeds present (unambiguous match only) before defaulting.
- **MED — Bem-firewall CLI leak.** `cdms temperament` printed the full disposition to stdout, so
  an agent with Bash access could read its own dials (firewall was policy-only on the data
  paths). The command now refuses on a non-interactive stdout unless the operator opts in
  (`--operator` / `CDMS_ALLOW_TEMPERAMENT_READ=1`); stdout stays empty on refusal.
- **LOW — purge glob.** `doctor --purge-quarantines` used a bare `*.corrupt-[0-9]*` glob that
  could delete unrelated operator files; anchored to the db-filename prefix.
- **LOW — dedup phantom +1.** Dedup folded `max(1, access_count)`, crediting a never-retrieved
  duplicate with a synthetic access; now folds the real (possibly zero) count.
- **LOW — temperament CHECK constraints.** `mem_temperament` gained per-dial range / `lower <=
  upper` / `current`-within-band CHECKs as defense-in-depth before Phase 1b adds a `current`
  writer.
- **LOW — `db_filename` traversal.** A directory component (`"../../etc/x"`, `"/abs"`, a POSIX
  backslash) let an env var place the store outside `CDMS_HOME`; now required to be a bare
  filename, clamped to the default otherwise.
- **LOW — `reinforce_cap < reinforce_alpha`.** Each was range-checked but never against the
  other; a cap below alpha neuters even the first reinforcement. Added a minimal cross-field
  repair raising the cap to alpha.
- **Process note.** A red-team verdict is only as good as the revision it read — re-derive the
  tip (`git log` / `-S`) before trusting an external "VERIFIED FIXED."

## Cycle 8 — OWL final report (full-spectrum, 6 subagents) triage

External report: `docs/redteam/CYCLE8_OWL_FINAL.md` (reviewed commit `8e889d7` — verified
current; not stale). 20 findings; each reproduced against the real code before action.

**Fixed — PR #17 (security/salience/concurrency):** H-1 spool `0o600` (raw pre-redaction
secrets), L-4 quarantine `0o600`, M-5 Anthropic/Google/Azure redaction patterns, M-4 Unicode
line separators, M-3 drop the MCP `importance`/goal_hint bypass, M-6 MCP content cap, H-2 S0
weight cap 1e3→10 + zero-goal anti-bypass cross-field, M-2 reject all-zero weights, H-5
`get_embedder` lock, M-1 eviction re-reads access_count.

**Fixed — PR #18 (scale/config hardening):** H-4 per-project cap on AUTO-ELEVATED scars
(pinned guardrails fail-safe-exempt, oldest-first), M-S-1 gated full `VACUUM` after bulk
deletes, H-3 reject path-traversal `home`, M-7 `http_host` loopback-only, M-S-5
`render_base_url` (formerly `dreamer_base_url`) loopback-only, L-5 reject JSON bool for numeric
fields, L-2 redact before truncation in `_brief`.

**Verification corrections (report overstated / stale):**
- **M-7 / M-S-5** are NOT live exposures at this commit — the MCP server is `mcp.run(transport=
  "stdio")` and the Prose Renderer is unwired. Fixed as latent defense-in-depth, not active holes.
- **C-1 "CRITICAL OOM"** — real `all_episodic()`/bulk-vector load, but episodic count is
  decay/eviction-bounded, so the 80–120K trigger is unlikely in personal use; severity is
  overstated. The realistic scale issue (disk bloat) is M-S-1, fixed.
- **L-3** ("drains_skipped not in stats") — already shipped in Cycle 7 (`db.stats()` exposes it).
- **M-S-1's literal fix** (`PRAGMA incremental_vacuum`) is a **no-op** unless the store was
  created `auto_vacuum=INCREMENTAL`; used the existing gated full `VACUUM` instead.
- **H-3's literal fix** ("require `home` under `Path.home()`") would break legitimate
  `CDMS_HOME` relocation; rejected only path-traversal instead.

**Deferred (own follow-up, with reasons):**
- **C-1 memory-streaming / per-project dedup** — every variant that bounds the dedup+eviction
  *memory* changes identity-reinforcement semantics (the dedup salience-fold interaction) or
  dedup scope; needs a focused PR with a chunk-size-equivalence test. Design captured.
- **M-8** full runtime vec0-format pin (visibility exists via `cdms doctor`; the `<0.2` cap stays).
- **M-M-3 / M-M-4** (associative-boost cap / valence-EMA) — identity-dynamics tuning; needs
  drift-harness validation as a deliberate change, not a sweep.
- **L-1 / L-C-1 / L-S-1 / L-6 / L-S-2 / L-S-3** — perf or low-value/high-false-positive
  (base64 redaction); deferred.
- **Philosophical P-1…P-5** — no code; acknowledged limitations, aligned with the DESIGN §1.1a
  ontological guardrail and the experiment plan's ethics posture.

## Cycle 9 — five-vantage multi-model audit triage

External reports: `docs/redteam/CYCLE9_*.md` (Hermes final + MiMo maximum-effort + Hy3/Kimi/Gemma
fuzz, reviewed tip `f4dd7cf`). Every actionable finding was **reproduced against the real code at
the current tip** before action (SHA-pin-and-reproduce); several headline severities were corrected
*down* once measured. Eight findings fixed across PRs #27–#30; all build→break→fix tested and
clearing `tools/drift_trajectory.py`.

**Fixed — PR #27 (salience/budget config-correctness):** **#3** `allocate_capped_proportional`'s
infeasible-cap branch (`cap*m < budget`) now enforces the per-key cap as a hard invariant (each
positive-weight key gets exactly `cap`, remainder unallocated) instead of an equal split that
*exceeded* the cap; **#4** a pathologically tiny `crisis_threshold` no longer makes the zero-goal
anti-bypass round every S0 weight to zero (which silently disabled salience) — the threshold is
repaired and the scale re-derived; **#7** `assoc_eta`/`assoc_boost_cap_frac` validators tightened
`≤1e3→≤1.0` (the old ceiling silently neutered the M-M-3 boost cap).

**Fixed — PR #28 (#1 associative-boost scar gate):** an associative boost can no longer lift a
neighbour *across* the crisis threshold (clamped strictly below it when the target was sub-crisis),
so a flood of benign-but-similar writes can't tip a planted near-crisis catastrophe into a permanent
scar. Consistent with the existing MAX-not-SUM dedup stance.

**Fixed — PR #29 (#5 fact decay + #8 resource):** **#5** `gist_support_decay_cap` (default 100)
caps the `support_count` that counts toward decay so an explicit fact re-asserted via
`upsert_fact` (unbounded `+=1`) can no longer become decay-immortal — the stored count (ranking)
is untouched; **#8** `Database.__init__` no longer leaks its sqlite connection on a partial/failed
open, and closes the first connection before quarantining a corrupt store (Windows rename); the
`pipeline._marker_re` `lru_cache` got a fixed cap as defence-in-depth (key space already finite).

**Fixed — PR #30 (I-1, the lone CRITICAL):** SessionStart's several separate reads now run under
one WAL `read_snapshot()` so a concurrent (non-atomic) consolidation can't splice pre- and post-pass
rows into one preamble; the path also closes the short-lived `MemoryService` it was leaking. Chosen
fix is snapshot-only (no cross-process lock) so SessionStart never blocks on consolidation.

**Verification corrections (report overstated / stale / false-negative):**
- **#1 was NOT unbounded HIGH.** Measured, the associative boost *saturates* (~+0.2 default config,
  ~+0.6 worst-case valid config — identical at 40 and 150 writes; KNN-crowding bounds it). Real but
  narrow injection vector (needs a planted near-crisis catastrophe + a flood) — realistically
  LOW–MEDIUM. Fixed regardless.
- **#6 "joint-leash doc fix"** — no real error; the Cycle-9 COGNITIVE_MATH review marks the leash
  docs/math correct. Dropped, not "fixed".
- **T-4 "no temperament-leash-under-drift test"** — false-negative: already covered by
  `tests/test_temperament_sim.py` (33 tests — randomized boiling-frog ratchet under the real
  `archetype_radius`, plus the no-archetype-hop invariant over all archetype pairs).
- The many **scale/architecture findings** (god-object, consolidation extraction, streaming
  `all_episodic`, dedup O(n²)) were **redefined piece-by-piece** rather than carried as a vague
  bucket — see the next section.

### Cycle 9 — deferred-debt redefinition (measured)

The Cycle-8/9 "deferred Phase-1+ scale/architecture debt" was re-characterized item-by-item
against the live tip (5-cluster parallel audit) with the same reproduce-and-measure discipline.
**Anchor:** this is a single-user daemon whose episodic store is decay/eviction-bounded
(accessibility floor, 29-day half-life, *no hard count cap*) → the live set ≈ the last couple
months of activity ≈ **low thousands**. Most theoretical-scale severities (OOM at 100K+, 480s
dedup at 500K, 750 MB vectors) describe a regime the forgetting design prevents. Net: ~⅔ of the
backlog is NON-ISSUE/already-handled.

**Shipped — PR #32 (quick wins):**
- **F-2** — corrupt-store quarantine is loud + file-preserving, but the only signal was hook
  stderr (easy to miss). Now a durable `quarantined_at`/`quarantined_from` marker is recorded in
  the fresh store and surfaced in `cdms stats`.
- **S-5** — `history()` now uses `db.recent_episodic()` (`ORDER BY timestamp DESC LIMIT ?`) instead
  of loading the whole table to return ~20 rows.
- **D-2** — regression test pinning the "persist cycle counter LAST" crash-safety invariant.
- **T-1** — regression test for the one lifecycle seam the drift harness misses: `retrieve()` over
  the gist tier + SessionStart scar injection over a *consolidated* store.

**Scale-gated — real only at large scale, defused at personal scale (guardrail, don't pre-build):**
- **S-3** streaming consolidation (full `all_episodic()` load, ~1.5 KB/episode loaded once/pass;
  bites >~100K eps), **S-4** dedup FLOP-quadratic per project (the "O(n²) Python/480s" claim is
  *stale* — now one BLAS matmul/episode, <0.1s at low-thousands; bites >~50K/project), **S-8**
  brute-force `vec0` KNN (~1 ms at low-thousands; bites >~500K eps). Their real fixes
  (windowed/LSH dedup, ANN) are *approximate* → perturb identity-reinforcement/recall and need a
  drift/recall harness. **Recommended instead:** a per-project episodic-count alarm in `cdms stats`
  so the threshold is observed before it bites.

**Needs-decision:** **T-2** clustering/individuation thresholds are hash-embedder-only (semantic
recall *is* real-tested; the thesis numbers aren't — and there is no CI yet, only local pytest);
**D-4** no `embed_dim`/model migration (deliberate fail-loud guard; build a `cdms rebuild` only if
model swaps become real); **E-2** per-project budget *floor* (only matters if non-default caps are
exposed).

**Non-issue / already-handled (with the honest reason):**
- **F-1** spool "sheds identity first" — *claim factually wrong*: tail-drop FIFO, salience-blind,
  and explicit identity writes (`store`/`pin_scar`/`upsert_fact`) bypass the spool entirely.
- **I-3** centroid → zero/sentinel — the embedder emits a *unit* sentinel `[1,0,…]`, never zero;
  support-weighted blend has no systematic pull to a degenerate point.
- **I-2** dedup on stale `access_count` — handled by Cycle-8 L-1; survivors are chosen by embedding
  argmax (never access_count), and the lock + step order makes the snapshot == live value.
- **E-2** at default caps — no cross-cycle accumulator; the 0.5 cap reserves ≥50% for non-dominant
  projects; a cumulative starvation cascade is unreachable.
- **D-1** `MemoryService` god-object *split* — cohesive facade, cognitive math already extracted; a
  split is net-negative surgery (only the redaction/DTO relocation is worth doing opportunistically).
- **S-7** DB bloat — gated VACUUM (M-S-1) + secure_delete + decay bound; not unbounded.
- **S-9** vector storage — ~1.5 MB/1000 rows; the "750 MB" figure assumes ~500× the realistic row
  ceiling.
- **S-11/12** transient/FTS — stale framing; current consolidation is single-load + per-project
  vector release, and FTS rows are lifecycle-coupled.
- **D-3** English FTS stemmer — only *stemming* is English-specific; `unicode61` indexes CJK/Cyrillic
  and the multilingual vector arm backstops recall via hybrid RRF.
