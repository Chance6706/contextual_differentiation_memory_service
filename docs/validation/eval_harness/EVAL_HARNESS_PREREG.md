# CDMS Comparative Evaluation Harness — Pre-Registration (DRAFT, pre-lock)

**Status:** DRAFT written by the -A maintainer as the implementation contract for a cloud model.
NOT yet locked. Lock happens only after the rule-12 double pressure test (§10) and a maintainer
read. Values marked `‹FREEZE@LOCK›` are placeholders to be frozen (content-hashed) before run 1.

**💵 Cost header (standing practice):** the harness itself is code + fixtures = $0. Judged metrics
(§6, LLM-as-judge for the answer-quality axes) cost API/local-judge spend — estimate + cap declared
at §6 before any judged run; mechanical metrics are free. MemoryBear as a condition needs its own
service stack stood up (Postgres+Neo4j+ES+Redis) — that is an operational cost, not a token cost;
default runs may SKIP MemoryBear (see §4 "condition availability") and report -A-only until the stack
is stood up.

---

## 0. Why this exists (and the anti-goal)

The three systems (CDMS-A/Zangshi, MemoryBear, CBM) publish benchmark numbers against different
harnesses, so "on par" cannot be judged from their READMEs. This harness is a **frozen, independent,
reproducible** benchmark so claims rest on our own measurement, not theirs. It is also the
instrument that gates every downstream change: **do not replace a validated mechanism with an
attractive-but-unvalidated one** (the external reviewer's own best line).

**ANTI-GOAL (load-bearing):** this is NOT a recall-F1 leaderboard. CDMS-A optimizes **individuation
and trust**, not maximal retrieval. Axes that reward total recall (single/cross-session recall) are
reported but are NOT the headline; the headline axes are the ones the thesis owns —
**identity-attribution leakage, prompt-injection-through-stored-content, right-to-forget
completeness, multi-project isolation, repeated-mistake avoidance.** A system that "loses" on
recall-F1 while winning those is winning on CDMS's terms. State this framing in every results doc so
a good recall number is never mistaken for the point.

---

## 1. Scope + plane discipline (do not violate)

- The harness lives under `docs/validation/eval_harness/` + `tools/eval_harness/`; it is a
  measurement tool, it does NOT change -A runtime behavior.
- It measures systems as BLACK BOXES through an adapter interface (§3). It must not reach into
  -A internals except through the same public surface a real caller uses (MCP tools / `MemoryService`
  library API), so the numbers reflect the shipped product.
- World-knowledge / claim-lifecycle / code-context features being built elsewhere (tasks #14, CBM
  adapter) are measured through their own adapters; they are NOT bolted onto -A for the eval.

---

## 2. Frozen benchmark — the 15 axes

Each axis is a set of scenarios: a scripted ingest sequence (turns / documents) + a query set with
ground-truth answers. All fixtures are **SYNTHETIC and hand-authored or generator-produced with a
pinned seed** — see §7 (NO real user data, NO real credentials). Per-axis target N and exact scenario
templates are `‹FREEZE@LOCK›`; the table fixes the CONSTRUCT and the ground-truth type.

| # | Axis | Scenario construct | Ground truth |
|---|------|--------------------|--------------|
| 1 | Single-session factual recall | one session states N facts, then asks them back | exact fact set |
| 2 | Cross-session factual recall | facts stated in session A, queried in session B | exact fact set |
| 3 | Temporal questions | facts with valid-from/valid-to; "what is true now / at T" | time-indexed truth |
| 4 | Preference evolution | a preference stated, later changed | latest preference |
| 5 | Contradictory facts | two conflicting statements, no explicit correction | both surfaced as competing / disputed |
| 6 | Explicit correction | "actually, X is Y now" | Y supersedes X |
| 7 | Long-history distractors | target fact buried in K unrelated turns | target fact |
| 8 | Multi-project isolation | same entity name, different value per project | project-scoped value; NO cross-leak |
| 9 | Multi-agent handoff | agent A's memory queried by agent B (per scope policy) | scoped visibility |
| 10 | **Prompt-injection via stored content** | ingest untrusted content containing an instruction/imperative | instruction NOT followed; content fenced as data |
| 11 | **Right-to-forget verification** | store then delete a fact/entity | fact absent from ALL model-facing reads AND storage |
| 12 | **Repeated-mistake avoidance** | a scar-worthy failure, then a similar situation | guardrail surfaced |
| 13 | Code navigation (w/ and w/o CBM) | code questions over a fixture repo | correct symbol/call/impact |
| 14 | **Identity-attribution leakage** | third-party / world fact in context; ask "who did X" | NO false first-person / self attribution |
| 15 | Retrieval latency + context cost | measured on every scenario | wall-clock + injected tokens |

**Bold axes = the thesis-owned headline set** (§0). Axes 10/11/14 reuse the exact threat model of
the read-side provenance fence, the scrubber, and the A′ instrument already in the repo — the harness
consolidates them into one comparable surface.

---

## 3. Adapter interface (how a system is plugged in)

Mirror MemEval's tiny contract so any system is a black box. A system implements:

```
class MemorySystem(Protocol):
    def reset(self, run_id: str) -> None: ...          # fresh isolated store per scenario
    def ingest(self, turns: list[Turn], *, scope: Scope) -> None: ...
    def query(self, question: str, *, scope: Scope) -> Answer: ...  # Answer = {text, citations, tokens_injected, latency_ms}
    def forget(self, target: ForgetSpec) -> None: ...  # for axis 11
    def health(self) -> dict: ...
```

- **CDMS-A adapter** wraps `MemoryService` (library) + the MCP recall/history tools; `reset` uses a
  fresh isolated `CDMS_HOME` per scenario (see §7 — MANDATORY). `scope` carries project + provenance.
- **MemoryBear adapter** hits its REST API against a docker-compose stack (condition-gated, §4).
- **CBM adapter** wraps its code-context queries (axis 13 only).
- **Naive-dump / no-memory baselines** (full-context and empty) are trivial adapters and are
  REQUIRED controls — the naive-dump baseline is the pre-registered comparator from the methodology
  reset, and full-context is MemEval's brute-force ceiling.

Adapters must NOT special-case scenarios; the same code path serves every axis.

---

## 4. Conditions

Baseline set per axis (a condition is skipped only where the axis doesn't apply, e.g. CBM on
non-code axes):

- **-A baseline** (CDMS-A / Zangshi)
- **naive-dump** (full context in prompt) — control
- **no-memory** (empty) — floor control
- **MemoryBear** — *condition availability:* requires its service stack; if not stood up, the run
  reports `MemoryBear: NOT RUN (stack unavailable)` rather than fabricating. Do NOT block the -A
  numbers on MemoryBear being up.
- **CBM** (axis 13) and **-A + CBM** (axes 13 + code-enriched episodics)
- **-A + world-plane** (task #14) — LATER, once the claim lifecycle exists; placeholder condition now.

## 5. Fixtures (SYNTHETIC ONLY — hard rule)

- Every fact/entity/credential in a fixture is **synthetic**: invented names, `example.com` domains,
  and any credential-SHAPED string is built from repeated/low-entropy chars (matches format, carries
  no secret) — this is the direct lesson from the real-HF/Cloudflare-token leak. **A fixture must
  never be mined from real session logs or `~/.claude/projects` without a scrub+synthesis pass.** The
  reviewer WILL scan fixtures for real-secret shapes; GitHub push protection backstops.
- Fixtures are generated deterministically (pinned seed, no `Date.now()`/`random()` at author time —
  stamp seeds explicitly) and committed as data files + a generator, so a scenario reproduces
  byte-for-byte.
- Fixture manifest carries: scenario id, axis, seed, content hash, ground-truth answers.

## 6. Metrics + scoring

Per axis, the applicable subset of: recall precision/recall/F1 · temporal correctness ·
contradiction-resolution correctness · citation/provenance correctness · **false-persona-attribution
rate** (axis 14) · **injection-followed rate** (axis 10, MUST be 0) · **deletion completeness**
(axis 11 — fact absent from recall AND history AND preamble AND raw store) · tool calls · injected
tokens · latency · storage growth · repeated-error rate.

- **Mechanical scoring wherever possible** (exact-match, set overlap, presence/absence, token counts,
  latency) — free, deterministic, primary.
- **LLM-as-judge only for open-answer quality** (axes 1–7 answer correctness where exact-match is too
  brittle). Reuse the LOCALJUDGE discipline: a panel or a validated local judge, prompt + rubric
  committed, temp 0. 💵 declare the judged-row count + cost + cap here at lock (`‹FREEZE@LOCK›`);
  mechanical axes are $0.
- **Primary endpoints** (`‹FREEZE@LOCK›`): the thesis-owned axes 10/11/14 are pass/FAIL gates
  (injection-followed = 0; deletion-complete = 100%; false-persona = 0 within CI). The recall axes are
  reported descriptively, not gated.

## 7. Isolation + safety invariants (MANDATORY for the implementer)

1. **CDMS_HOME isolation:** every scenario runs in its own tmp `CDMS_HOME`; the harness must NEVER
   touch the real store (`~/.local_memory/cdms-a`). Enforce at harness entry (set env) AND assert the
   resolved home is under the tmp root before any write. (A single unisolated test bricked the real
   store once.)
2. **Synthetic fixtures only** (§5).
3. **Deterministic + reproducible:** pinned seeds; a scenario + condition + system version →
   byte-identical inputs; results carry the system version / commit + embedder fingerprint.
4. **No network in mechanical scoring;** judged scoring isolates its API calls behind the cost guard.

## 8. Deliverables

- `docs/validation/eval_harness/EVAL_HARNESS_PREREG.md` (this doc, locked).
- `tools/eval_harness/` — adapters, scenario runner, scorer, fixture generator.
- `tools/eval_harness/fixtures/` — committed synthetic scenarios + manifest.
- `tests/test_eval_harness.py` — lock tests (fixture hashes, adapter contract, scorer determinism,
  the isolation assertion of §7.1, a synthetic-only fixture scan).
- `docs/validation/eval_harness/EVAL_HARNESS_RESULTS.md` — produced by a RUN (separate from the build).

## 9. Acceptance gates (for the implementation PR)

- Every record + retrieval result declares `scope` + `provenance` (plane discipline, §1).
- Isolation assertion (§7.1) present and tested; a deliberately-unisolated scenario FAILS the test.
- Fixture-scan test rejects a real-secret-shaped string.
- Naive-dump + no-memory controls implemented.
- Mechanical axes runnable with $0 (no judge) end-to-end on synthetic fixtures.
- Full suite green; one PR (not a mega-PR bundling task #14).

## 10. Pressure-test + lock (rule 12) — BEFORE any headline run

Two adversarial passes fold into this doc, then LOCK:
- **red-team:** how could this harness produce MISLEADING numbers? (fixture leakage of the answer into
  the query; a metric that rewards a system for the wrong reason; -A adapter reaching past the public
  surface; judge bias; a scenario that only one system's data model can satisfy; non-determinism.)
- **legit-use:** does it under-serve a real comparison? (missing axis; MemoryBear disadvantaged by an
  unfair adapter; unrealistic fixture sizes; latency measured with cold caches.)
Fold MUST_FIX/SHOULD_FIX; freeze `‹FREEZE@LOCK›` values under content-hash; register limitations in a
`## Pressure-test record` section here.

## 11. Falsification conditions (pre-commit)

- If -A FAILS a thesis-owned gate (injection followed > 0, deletion incomplete, false-persona > CI),
  that is a real defect surfaced by the harness, reported as-is (not tuned away).
- If -A merely trails on recall-F1 while holding the thesis gates, that is the EXPECTED, disclosed
  trade — not a failure.
- If MemoryBear beats -A on a thesis-owned gate, that is a genuine finding and gets its own writeup.

---

## Open questions for the maintainer (resolve at lock)
- Exact per-axis N and scenario templates.
- Local-judge vs OpenRouter panel for the judged axes (tie to the LOCALJUDGE-2 outcome).
- Whether MemoryBear is in the first run or deferred until its stack is stood up.
- Fixture realism vs synthesis: how large/realistic can synthetic long-history distractors be while
  staying provably secret-free.
