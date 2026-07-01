# CDMS — Independent Repo Analysis (Science + Code)

_Date: 2026-07-01. Scope: full repository at commit `b5ba5ca`. Method: four parallel specialist
reviews (scientific methodology & statistics; core cognitive/data code; interface/security code;
claims-vs-evidence & test-quality audit), each working from source, validation artifacts, git
history, and live repro runs, synthesized here. The full offline test suite was executed
independently: **794 passed, 0 failed** (`CDMS_EMBED_BACKEND=hash`, Python 3.11, Linux)._

---

## 1. Executive summary

**CDMS-A is a genuinely well-engineered, unusually self-critical research codebase.** The claims
audit found the paper trail *intact*: 9 of 12 load-bearing claims verified against raw artifacts,
headline numbers that reproduce byte-for-byte live (`z = −3.33` from
`tools/individuation_experiment.py`), red-team fixes that cite their finding IDs in code and carry
1:1 regression tests, and every stale number drifting *against* the repo's interest (undercounted
tests, older/smaller dataset figures) — staleness, not inflation. The late-stage science (the
framing confirmatory study, the A′ instrument thread) reaches publication-grade pre-registration
discipline, including a git-verifiable temporal lock, exact permutation inference, a real TOST
equivalence gate, and — rarest of all — published self-corrections against interest
(the z=+6.5 pseudoreplication retraction; a follow-up that attenuated its own confirmed effect).

**The debits cluster in three places:**

1. **README/status.md harden early small-n claims beyond what their own validation docs support.**
   The single most misleading item is the README differentiation bullet, which stitches the
   z=−3.33 significance test (hash embedder, 4 *synthetic* psyches, observed overlap 0.048) onto
   the real-data "overlap 0.00 across 3 projects" observation as if they were one result. The
   real-data configuration has **no significance test attached**. Similarly, "statistically
   indistinguishable" (disposition null) is absence-of-evidence at n≈50 with no equivalence
   test — the project's own precision doc says so; the README doesn't.
2. **Three confirmed core-code defects at interaction seams** (exactly the residue expected after
   nine single-module red-team passes): budget renormalization silently defeats scar-elevation
   corroboration in busy stores (a recurring catastrophe never mints a guardrail — demonstrated);
   a transient embedder outage during drain permanently destroys the spooled backlog
   (demonstrated); project-scoped retrieval filters after pooling, starving scoped recall in
   shared stores (demonstrated).
3. **Four confirmed security gaps**, the sharpest being an asymmetry around scars: the MCP
   `store(kind="scar")` path bypasses the provenance/corroboration gate (one injected tool call
   mints a permanent, re-injected guardrail) while — per code bug #1 — *legitimate* catastrophes
   in busy stores can't mint one. The trust boundary is enforced hardest exactly where it matters
   least.

Nothing found is store-corrupting or thesis-fatal. The prioritized fix list is in §6.

---

## 2. Verification

- **Tests:** 794 passed, 0 failed, 3 warnings, ~37 s, offline (`CDMS_EMBED_BACKEND=hash`), fresh
  clone, Linux/py311. The README/status "~720 tests / 645 fns / 60 files" is a stale *undercount*
  (actual: 794 collected, 662 `def test_`, 62 files).
- **Reproductions:** `tools/individuation_experiment.py` reprints the documented
  `overlap 0.048 [null 0.167 ± 0.036; z = −3.33]` byte-for-byte. All six tools named in status.md
  exist and run. Fisher p for the BEM-vs-recall split recomputes (6.7e-21 ≈ "1e-20"). The framing
  confirmatory permutation p is internally exact (24/2^19 = 4.6e-5). Wilson CI code verified
  against reported intervals to 3 decimals.

---

## 3. Science evaluation

### 3.1 What is genuinely strong

- **The framing confirmatory study** (`docs/validation/runtime_instrument/framing_confirm/`,
  `FRAMING_CONFIRMATORY_LOCK.md`) is model pre-registration practice: lock committed hours before
  probes were frozen and results produced (git-verified), sha256-frozen condition strings, facet
  draw disjoint from the pilot, a CI guard test pinning bytes and thresholds
  (`tests/test_framing_lock.py`), one pre-committed decision rule with a genuine TOST equivalence
  gate, exact sign-flip permutation, a robustness ladder (model-cluster LB +0.077,
  adverse-exclusion +0.061, joint +0.052, drop-top-4 +0.048; 18/19 facets positive), and an
  explicitly upper-bounded estimand. The follow-up scaffold gradient then *attenuated its own
  confirmed effect* (+0.165 → +0.074 → −0.032 raw) and let a pre-registered gate fail to
  DESCRIPTIVE rather than forcing a story.
- **The correction record is real and against self-interest:** the response-pooled z=+6.5 framing
  significance was retracted and re-analyzed cluster-correct; the quant study overturned its own
  draft headline (the coherence/token-presence confound); the aggregator deadlock fix moved
  numbers against the preferred conclusion and was reported anyway; PARAMETER_BASIS caught its own
  false-precision half-life identity.
- **Instrument engineering:** 5-vendor judge panel with self-family exclusion enforced in code
  (`tools/ownership_judge.py`), planted leniency tripwires, Gwet AC1 correctly chosen over kappa
  for prevalence skew *and* reported alongside raw cell agreement, deterministic invalid
  pre-filter, per-rung NOT-CLEAN gates, instructed-control token never pooled into breach.
- **Statistical code is largely correct** (§3.4).

### 3.2 Confirmed methodological problems

- **P1 — Composite differentiation claim (README.md:172-181).** z=−3.33 comes from the offline
  hash-embedder 4-synthetic-psyche run (observed overlap 0.048); the "0.00 / 3 projects" figure is
  the real-embedder cycle9 run with no significance test attached. "The real run is even stronger"
  is asserted, never computed. status.md:98-100 further contradicts with "~8.6k turns / 4
  projects" (stale; the artifact shows 3 projects, 10,104 turns).
- **P2 — The pooled-resampling null is an artifact check, not a thesis test.** It answers "is
  near-zero overlap explainable by chance draws from a shared vocabulary?" — the vocabulary itself
  is defined post hoc as the union of observed traits, so *any* near-disjoint trait sets pass,
  including from an extractor that never reproduces the same trait twice. The discriminant-validity
  control that would carry the thesis (clone overlap ~0.76 vs distinct ~0.11 in
  `drift_trajectory.py`) exists but is synthetic/hash-backend and never integrated into headline
  inference. Also: `percentile = 0.000` should be p < 1e-4 ((b+1)/(n+1)); the z≤−2 "MEANINGFUL"
  cut is arbitrary and unregistered.
- **P3 — A′ admissibility gate redefined after failing its pre-registered bar.** BEM AC1 0.768 →
  rubric sharpened + 6 gold labels corrected → re-validated on the *same* 228-item gold (classic
  validation-set reuse); the rev-7 bias fixes regressed 4-way BEM AC1 to 0.789 (< the locked 0.80
  bar), and rev 8 replaced the gated metric with the inclusive-breach collapse (0.827) instead of
  the pre-registered STOP. Disclosed and argued at length, and the substantive argument is
  respectable — but it remains outcome-informed. The decisive fresh evidence (AC1 0.836,
  CI [0.808, 0.864], n=645) is single-model (qwen2.5-72b), single-mode (BEM), judge-only;
  generalization to the 24-model 2B–72B deployment population is extrapolated, not measured.
- **P4 — The §3.5 framing-dissociation "significant" cell (mech p=0.043) rests on a method its own
  docstring calls anti-conservative** (`tools/gen_sweep_facet_cluster.py:20-22`: one-stage,
  facet-only clustering; "true p if anything larger"). The docs label the result "not yet
  confirmed"; status.md and RESEARCH_ARC still carry "mech-arm-significant (p=0.043)" as a
  headline token.
- **P5 — "Recall yes, disposition no" is a non-detection, not equivalence.** No TOST/SESOI
  anywhere for the disposition null; dex/uma CIs ~0.20 wide, so a true shift of ~0.10 would be
  invisible; ~196 obs/arm needed per the project's own precision doc. README's "statistically
  indistinguishable" and the architecture-level conclusion overstate it. The project's own flagged
  anomaly (any injection lowers P_careful ~0.12 across all 5 models, marked OPEN) coexists
  unexplained with the "no disposition" headline.
- **P6 — Enriched-phenotype and tone headlines drop their fragility qualifiers in README.** The
  pre-registered *primary* criterion (Δcites ≥ +3) was missed (+2.67; verdict fired on the OR
  branch — legitimate under the lock, unnoted in README). "9×" is 1/30 → 9/30 whose Wilson CIs
  touch at the third decimal. The voice ~58% figure rests on n=6 prompts with a judge that was
  also a subject (disclosed only in the sub-doc); the +0.3 coupling is method-dependent at n=5
  ("suggestive, not established" per the precision doc; no qualifier in README).
- **P7 — "Human" labeling language obscures that most annotators are LLM agents.** Gold first-pass
  labels are Claude-family while the judged panel contains a Claude judge (partial circularity;
  the human ceiling covers only disagreements); INSTRUMENT_FINDINGS calls a 98-item check a
  "2-agent human label"; the framing studies' "blind coders" are orchestrator-spawned agents whose
  blinding is unverifiable in the way human protocols are.
- **P8 — Judge-model deviation from the locked panel** (gpt-5-mini pinned; gpt-4o-mini shipped)
  handled via code comment rather than the pre-reg's own versioned-amendment rule.

### 3.3 Claim-by-claim calibration

| Claim (README/status) | Evidence strength | Note |
|---|---|---|
| Trait overlap ≈ 0.00, 3 real projects, 6 windows | **Directional** | Solid observation; no inference on this configuration |
| "Meaningfully below chance", z=−3.33 | **Directional** | Arithmetic exact; artifact-null only; belongs to the synthetic run |
| Recall/override steering positive (5-model panel) | **Directional-solid** | Consistent direction; n=10 greedy, no CI |
| "Disposition no" (dex/uma indistinguishable) | **Weak as a null** | No equivalence test; honest as non-detection only |
| Enriched phenotype 1.67→3.67, citation 9× | **Directional** | Genuinely pre-registered; primary missed, OR-branch confirm; n=3×10 |
| Voice ≈58%, +0.8 vs placebo | **Weak-to-directional** | Round-robin de-circularization is a real strength; tiny n |
| Voice↔choice coupling +0.3 | **Weak (suggestive)** | Bootstrap and t-interval disagree at n=5 |
| A′ AC1 0.836 | **Solid** for qwen-72B-BEM-like text; **directional** as a general instrument | Gate redefinition + gold reuse (P3) |
| BEM breach 39% vs recall 1%, p≈1e-20 | **Solid** | Recomputed; clean control; the thread's best result |
| Quant moves coherence, not adoption | **Directional-solid** | Twice pressure-tested; low-bit cells power-starved |
| Generation moves surfacing 4.5–12×; adoption flat | Surfacing **solid**; flatness **directional** | Two clean ladders; collider disclaimed |
| Framing dissociation ~1.6–1.8×, mech p=0.043 | **Weak-to-directional** | Anti-conservative method at the margin (P4) |
| Ownership-framing lift +0.165 (p=4.6e-5) | **Solid within scope** | Best-practice pre-reg; upper-bound estimand, mech-only, scaffold-bound |
| Scaffold gradient attenuation | **Directional-solid** | Pre-registered reuse; gate honored into a FAIL |
| "MoE leaks less" | **Retracted (honestly)** | Residual stale framing in README §Status |
| Power-law forgetting / parameter basis | **Solid** | Analytic; deviations registered |

### 3.4 Statistical code

`src/cdms/stats.py`: Wilson interval textbook-correct (verified numerically); percentile bootstrap
standard and deterministic; `overlap_significance` implements its spec (design-level issues per
P2); `mean_se` returns (0,0) on empty input (footgun). `tools/framing_pilot_analyze.py` is the
strongest module: two-stage triplet bootstrap, exact sign-flip permutation including identity,
correct CI-TOST, correct ESCALATE/INVALID/MISSING bucket handling, and a rare null type-I
calibration selftest (loose bound: ≤0.12 at 250 sims). `tools/gen_sweep_facet_cluster.py` is
self-aware but its "cluster-p" is a bootstrap crossing probability, not a permutation p.
`gwet_ac1` multi-rater implementation is correct, and AC1 is the right coefficient for the
prevalence skew. `breach_from_votes` collapse-before-plurality fixes a real conservative-direction
bug.

### 3.5 The hash-embedder question

The overlap statistic itself is embedding-free (set Jaccard over gist tuples); the embedder shapes
which gists form upstream. The z=−3.33 run is hash-backend/synthetic; the 0.00 headline run is
real bge-small. Steering/tone/identity-power tools force `hash` for preamble construction
(undocumented in those experiment docs); the A′ thread outcomes are LLM-behavioral, so expected
sensitivity is marginal. Enriched-phenotype recall claims correctly use the real embedder. The
acknowledged gap stands: dedup/cluster/gist thresholds (0.95/0.78/0.90) were tuned under hash
cosine geometry and never benchmarked for code-heavy content under the real model
(`docs/redteam/CYCLE9_ARCHITECTURE.md:409-421`).

---

## 4. Core code review (`src/cdms/`)

### 4.1 Verdict

Well-engineered; no incorrect formula implementations against the documented parameter basis; the
storage layer's failure-mode handling (quarantine guard, fingerprint pinning, no-silent-fallback,
atomic spool claims, orphan reclaim, secure_delete+VACUUM forget) is unusually thorough. The
architectural blind spot is **salience scale**: `base_salience` means write-time S0 (calibrated
scale; crisis at 3.0) before the first consolidation and an arbitrary budget share (~1 to ~500
observed) after it, while three consumers compare it against S0-scale constants.

### 4.2 Confirmed bugs (each demonstrated with a deterministic repro, hash backend)

1. **HIGH — Renormalization dilutes catastrophes below `crisis_threshold`, permanently defeating
   scar corroboration in busy stores.** `consolidate.py:272-279` gates elevation on
   `base_salience ≥ crisis_threshold` (S0-calibrated, `docs/PARAMETER_BASIS.md:41`), but
   `_compete_and_renormalize` (`consolidate.py:441-484`) rescales `base_salience` to budget
   shares. Repro: 4 sessions × 250 routine episodes + a genuine catastrophe (S0 floored to 3.0) →
   after pass 1 its salience is 1.129; recurrences in two more sessions never corroborate (dedup
   folds the new copy into the old survivor, destroying session multiplicity) → **0 scars after 3
   distinct-session catastrophes**. Control at small store size elevates correctly, so failure
   onsets silently with scale. Inverse symptom: a singleton-session episode renormalized 3.0 →
   500.0 (unevictable ~13 years; also weakens the Cycle-9 #1 boost backstop at `store.py:311`).
   Fix direction: gate elevation on a scale-invariant signal (persist a crisis flag / write-time
   S0), preserve session provenance through dedup for catastrophe-flagged rows.
2. **HIGH (durability) — Transient embedder failure during drain permanently destroys the spooled
   backlog.** `pipeline.py:264-297`: per-turn `except Exception: continue` swallows the
   `RuntimeError` that `embeddings.py:67-73` raises expressly so the caller can "retry later," and
   the `finally: claimed.unlink()` deletes the claim. Repro: 5 spooled events + embedder outage →
   `ingested: 0`, spool gone, claim gone, DB empty. Fix: distinguish infrastructure failure (abort
   drain, leave claim for orphan reclaim) from bad-turn failure (skip turn).
3. **MEDIUM — Project-scoped retrieval filters after pooling → recall starvation in shared
   stores.** `store.py:374-391` pools `max(top_k*3, 20)` KNN/FTS hits with no project predicate,
   then filters. Repro: 300 relevant episodes in project A, 3 in B → scoped retrieve for B returns
   **0** despite direct hits existing. Correct isolation, broken recall for the advertised
   `--scope user` deployment; also silently biases differentiation measurements. Fix: push the
   predicate into vec0/FTS or inflate the pool adaptively.
4. **MEDIUM-LOW — `_forget_from_spool` (`store.py:542-585`) can strand or lose unrelated events:**
   crash between rename and rewrite strands `.forget-*.tmp` (orphan reclaim only globs
   `*.processing`); a rewrite failure (ENOSPC) hits `finally` unlink and loses kept lines.
5. **LOW — `allocate_capped_proportional` all-zero-weight branch violates the "cap is a hard
   invariant" contract** (`salience.py:168-188`): `{a:0,b:0}, total=100, cap=0.1` → 50/50 (5× cap).
   50k-case fuzz confirms the invariant holds whenever ≥1 weight is positive. Harmless today
   (zero-weights no-op upstream); the contract text is wrong; half-disclosed in DEVIATIONS M5.
6. **LOW — `db.delete_*` return the requested count, not rows deleted** (`db.py:606-616,705-726`)
   → `ConsolidationReport` counters and `forget()` can overstate.
7. **LOW — `db.list_paths(project=…)` is dead (no WHERE), so MCP `list_paths` leaks cross-project
   subject/relation metadata** while `store`/`retrieve` in the same file deliberately enforce
   scoping (`mcp_server.py:166-167,191-195`).

### 4.3 Plausible concerns

- **Shared-connection tx interleaving under concurrent MCP calls:** one connection,
  `check_same_thread=False` (`db.py:256`), no in-process mutex around `tx()`; FastMCP dispatches
  to worker threads and Claude Code issues parallel tool calls — interleaved commit/rollback can
  tear a mem/vec/fts triplet. (Viewport wraps its shared DB in an RLock; the MCP server doesn't.)
  `read_snapshot`'s bare `BEGIN` also raises if the connection is mid-transaction (latent; current
  callers use private connections).
- **Hierarchical softmax saturates post-renorm** (temperature 1.0 on totals of O(100–500) →
  effective argmax; "competition" degenerates; downstream caps largely mask it).
- **Eviction horizon scales with store size** (post-renorm salience ≈ K/N: a quiet store evicts
  nothing for decades) — `retention_floor=0.10` doesn't mean what PARAMETER_BASIS implies in
  either regime.
- `find_duplicate_scar` KNN pool of 5 is pre-project-filter (same pattern as bug #3, smaller blast
  radius). Spool shedding drops the *newest* events at cap (polarity arguably backwards).
  `age_days` returns 0.0 for malformed timestamps (never-decaying memory).

### 4.4 Math-vs-docs consistency

All spot-checked constants and derivations verified: D(29)=0.5 with τ=70.012; λ=ln2/29;
reinforcement min(α^c, Cap) with saturation c*=5 and clamp 6; K conservation to 1e-13; capped
allocation invariants (fuzzed); Wilson CI; flashbulb floor; boost clamp `nextafter(3.0, 0)`.
**Two stale doc items:** DEVIATIONS M3's "mortal (~142d)" is exponential-era math (power law gives
~313d), and `salience.py`'s module docstring still prints the exponential formula the code
deviates from (flagged correctly at `accessibility()` but contradicted in the header). Also stale:
`pipeline.py:5` references a nonexistent "MCP heartbeat thread"; `CYCLE9_COGNITIVE_MATH.md`
Part IV describes the pre-fix allocator.

---

## 5. Security & interface review

### 5.1 Verdict

The best-defended surface is the prompt-injection fencing (`hooks._sanitize`, hooks.py:55-74):
every escape attempt tried (fence forgery, newline block-injection, ZWSP/bidi/TAG obfuscation)
collapsed safely, and the budget packer reserves room for close-tags so truncation can never strip
a fence. Temperament no-hop invariant verified numerically for every archetype pair; config
validation resisted every hostile env var tried; install/uninstall is atomic and never clobbers
unparseable settings; MCP input validation is loud and correct.

### 5.2 Confirmed issues

1. **Main SQLite store is world-readable (0644); home dir 0755.** Only the spool got 0600
   (Cycle-8), yet the DB holds the same content persisted — including anything that slips past the
   best-effort redactor. Fix: chmod 0600 db + `-wal`/`-shm` after open; `mkdir(mode=0o700)` for
   home. (`db.py` open path; `config.py:348`.)
2. **`cdms observe` lacks the loopback-bind refusal the viewport has** (`observer.py:248-262` vs
   `server.py:424-428`): `--host 0.0.0.0` exposes the whole store *and* `/diagnostics`
   (temperament dials) to the network, no auth.
3. **Redaction misses common secret shapes** (`store.py:86-119`): JSON quoted-key secrets
   (`{"api_key": "sk_live_…"}` — the `\b(NAME)\s*[=:]` anchor breaks on the quote),
   connection-string passwords (`postgres://user:pass@host`), `Authorization: Bearer …`, and
   Stripe `sk_(live|test)_` entirely. These persist plaintext and re-inject every SessionStart.
4. **MCP `store(kind="scar")` mints a permanent authoritative guardrail with no provenance or
   corroboration gate** (`mcp_server.py:138-141` → `pin_scar`, `store.py:319-331`), bypassing both
   `enforce_provenance` and `scar_elevation_min_sessions` — while auto-elevation and gist
   formation are correctly gated. A single induced tool call plants a persistent instruction
   re-injected into every future session (v2+ render: "take precedence over project conventions").
   Combined with core bug #1 this is a striking asymmetry: **injected content can mint a scar in
   one call; a real recurring catastrophe in a busy store can't mint one at all.**

### 5.3 Plausible concerns

Bem-firewall inconsistency over HTTP (CLI enforces TTY/opt-in; viewport `/api/temperament` and
observer `/diagnostics` serve the dials over unauthenticated loopback — an agent with Bash can
`curl` its own temperament if a server is running; the observer docstring says "gated" when it is
banner-warned only). The self-subject firewall is trivially paraphrased ("yours truly", "me, the
AI" — disclaimed in code, confirmed live). Untrusted-provenance episodic content is recallable
verbatim and unfenced via direct `retrieve` tool results.

---

## 6. Prioritized recommendations

**Fix now (small, high leverage):**
1. Chmod 0600 the main DB (+wal/shm) and 0700 the home dir (security C1).
2. Add the loopback refusal to `observer.serve` (C2).
3. Make drain distinguish infrastructure failure from bad-turn failure — abort and leave the claim
   rather than unlink on embedder outage (core #2).
4. Gate or visibly demote MCP-originated scar pins (provenance + corroboration, or a
   lower-authority render band) (C4).

**Fix soon (correctness of the cognitive model):**
5. Make scar elevation scale-invariant (persist write-time S0 or a crisis flag; preserve session
   provenance through dedup for catastrophe rows) (core #1 — this silently disables the flashbulb
   guarantee at exactly the store sizes the project targets).
6. Push the project predicate into KNN/FTS or adaptively inflate the pool for scoped retrieval
   (core #3); same for `find_duplicate_scar`.
7. Extend redaction: quoted-key JSON secrets, connection-string passwords, bearer tokens,
   `sk_(live|test)_` (C3).
8. Add an in-process lock (or per-call connections) around MCP tool DB access.

**Science/documentation debt:**
9. De-composite the README differentiation bullet: either run the pooled-resampling null on the
   real-data configuration, or attribute z=−3.33 explicitly to the synthetic offline harness in
   the same sentence. Reconcile status.md's "4 projects / ~8.6k" with the artifact (3 / 10,104).
10. Replace "statistically indistinguishable" with the precision doc's own language, or run the
    TOST the rigor skill demands (rule 5) for the disposition null.
11. Carry the fragility qualifiers into README for the enriched-phenotype (primary endpoint
    missed; OR-branch confirm) and tone/coupling (suggestive; judge-as-subject) bullets.
12. Rename "2-agent human label" and similar; state plainly where annotators are LLM agents (P7).
13. Doc-sync pass: DEVIATIONS M3 (~142d → ~313d), `salience.py` header formula, `pipeline.py`
    heartbeat comment, CYCLE9_COGNITIVE_MATH Part IV, DESIGN.md line-number citations, stale test
    counts, README's "quant-vs-architecture follow-up in flight" (it completed).
14. Register the gpt-4o-mini judge swap as a versioned pre-reg amendment (P8). Add the M2
    point-of-use `DELIBERATE DEVIATION` marker (the one rule-11 miss on runtime code).

**Hygiene:**
15. Move the 1.56 MB binary-content `[Gemini Canvas] ….md` out of root (or mark `-text` /
    LFS — with `* text=auto` it is a latent LF-normalization corruption risk). Consider LFS for
    the multi-MB `*_JUDGE.jsonl` artifacts. Consider a coverage gate in CI (currently the only CI
    gap; the three-job hash/Windows/real-embedder matrix is otherwise strong).

---

## 7. Test & CI quality (verified)

Tests are behavioral, not shallow: exact-count concurrency conservation, with-cap/without-cap
contrast pairs proving fixes do something, randomized boiling-frog + all-pairs no-hop invariants,
line-level injection-neutralization asserts; zero assert-free test files; all 8 skip markers are
platform-conditional with the Linux CI gating the same tests; `test_real_embedder.py` escalates
skip→fail in CI (`CDMS_REQUIRE_REAL_EMBEDDER=1`). The red-team register maps 1:1 to
`test_cycle*_*.py` regression files, and fixed code cites finding IDs inline. CI runs three gates
(hash py3.11/3.12, Windows mirror with `-rxX`, real-embedder required job). No coverage
measurement — the one gap.

---

_Provenance of this document: independent analysis session; findings above were each verified
against source or demonstrated with deterministic repros as noted. Repro scripts for core bugs
#1–#3 used `CDMS_EMBED_BACKEND=hash`, throwaway `CDMS_HOME`, `PYTHONPATH=src`._
