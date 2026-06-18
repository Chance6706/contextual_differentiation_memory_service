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
- **Dreamer/httpx path is dead code** (Cycle 2) — `dreamer_*`/`http_*` config is never
  imported; no runtime risk. Left as a documented placeholder for the designed feature.

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

**Not addressed here (open engineering track):** the *mechanical* code-level findings from
these passes — e.g. GLM C-HIGH-1 (drain not under the cross-process lock), C-HIGH-2
(`get_embedder()` singleton ignores config changes), C-HIGH-3 (`_associate`
read-modify-write race), and the DeepSeek/Owl mechanical items — remain to be triaged and
**independently reproduced** before any fix, in a later cycle. They are out of scope for
this documentation-only change.
