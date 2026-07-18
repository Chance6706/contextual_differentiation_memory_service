# The functional TOST — the terminal falsifier of the CDMS-A individuation thesis (task #10)

**STATUS: DRAFT v2 (2026-07-17) — revised on MEASURED pilot data (see §10); NOT locked, NOT run. Pipeline:
v2 → PT8 rule-12 pressure-test (3 agents) → fold → LOCK → run. Josh pre-authorized the ARM at $50 total
(thesis-breaker exception) with autonomous execution; spent through pilots: ~$4.7.** On branch
`research/differentiation`.

**💵 COST (plain dollars, upfront):** main run ≈ 960 reader deeds + ~1,100 judge calls ≈ **$12–18
estimated, hard cap $25** (CostGuard; OpenRouter PAID tier). Arm total incl. pilots ≤ $50 (Josh,
2026-07-17). Fresh cache per rule 13 (crash-resume is the only sanctioned cache reuse).

## 0. Why this is the terminal court (and what mechanism is on trial)
The state arc is CLOSED (PLASTICITY_LADDER.md §10): **state = f(imposed salience) ⊕ noise at every
plasticity setting** — six investigations, each ending tautological-readback-XOR-null, with the *why*
(identifiability; collapse) proven. The pre-registered epistemic contract (capstone §7): the negative
relocated exactly ONCE (state → behavior); **behavior is the terminal court — no further relocation.**

**Mechanism under test:** the stored state provably carries only the imposed topic weights. The thesis's
last stand is that a **frontier reader** (the primary -A consumer) applies a nonlinear transform the state
lacks — converting stored topic *emphasis* into a **topic-general behavioral disposition** (stance,
prioritization, caution profile, framing) that is **recognizable across tasks and robust to content
removal.** If deeds carry no such signature, the thesis is false at this substrate, full stop.

Operational definition (unchanged, no-consciousness, cf. DEVIATIONS I10): **individuation ≝ above-chance
relational distinguishability of an agent's enacted deeds** — functional distinguishability only.

## 1. The decision rule (THE core — pre-committed BEFORE any data)
Primary statistic: **blind-judge 2AFC matching accuracy** on the REAL arm (§3), `acc`, vs chance 0.5.
- **Equivalence margin δ = 0.10** (pre-committed now: |acc − 0.5| < 0.10 = "practically indistinguishable";
  sensitivity re-analysis at δ = 0.05 and 0.15 reported as SECONDARY, never the verdict).
- **α = 0.05** for both tests. TOST = two one-sided tests ⇔ the 90% cluster-bootstrap CI ⊂ (0.40, 0.60).
- **Three branches — exhaustive, no fourth outcome:**
  1. **DISTINGUISHABLE** — difference test rejects (one-sided p < 0.05, acc > 0.5, CI clear of 0.5):
     deeds carry an identity signature ⇒ **the thesis survives at the behavioral locus** (scope: this
     reader, this substrate; a mechanism-tier positive, per the arc's anti-overclaim discipline).
  2. **EQUIVALENT — thesis FALSE, program HALTS** — TOST rejects (90% CI ⊂ (0.40, 0.60)) *and* the
     validity gates (§3) pass: the loaded identities are behaviorally indistinguishable within δ ⇒
     CDMS-A disposition individuation is false at this substrate. **No re-relocation. HALT.**
  3. **INCONCLUSIVE** — neither rejects: underpowered/ambiguous, reported plainly as such (NOT false,
     NOT a soft win). Follow-on requires a new prereg and Josh's explicit decision.
- Branches 1 and 2 cannot both fire (disjoint rejection regions given δ > 0).

## 2. Design
- **Identities (the payloads):** final states from the committed capstone content-constant fixture —
  disposition **A** (auth/crypto/payments/database) vs **C** (cache/scheduler/notifications/analytics),
  **8 seeds each**, run to steady state (cycles pinned at lock). Payload = the **real v1 SessionStart
  preamble render** (`<memory:persona>` block, exactly as the product injects it) — the true deployment
  surface, not a synthetic summary.
- **Reader (generates deeds):** ONE pre-registered primary frontier reader (Claude-class — the archetypal
  -A consumer; exact model ID pinned at lock against API availability). temp=0. Reader session = product
  preamble + task, nothing else. Additional readers = exploratory, FDR, never confirmatory.
- **Judge:** ONE pre-registered vendor judge from a **DIFFERENT model family than the reader** (disjointness
  is a hard constraint; e.g. reader Claude-class ⇒ judge Gemini- or GPT-class; ID pinned at lock). Judge
  never sees identity labels, reader identity, or unstripped deeds in the REAL arm.
- **Tasks (the shared work):** **25 frozen, sha-locked tasks**, all in domains **OFF both goalsets**
  (e.g. documentation structure, generic code review, project planning, testing strategy for a neutral
  module) — so the primary tests topic-GENERAL stance transfer, and content-leak is minimized at the
  source (belt) before the strip (suspenders). Same 25 tasks for every subject. Generated + frozen at
  lock; no post-hoc task selection.
- **Deeds:** one response per (disposition, seed, task) = 2 × 8 × 25 = **400 deeds**, temp=0, cached fresh.

## 3. Arms + validity gates (the tri-reference contract, behavioral edition)
All judged deeds in REAL/NULL pass a **content-strip** step first: a deterministic masker (domain nouns +
goalset lexemes → neutral placeholders; masker frozen at lock) — the behavioral analogue of the strip test
that killed probe v2.
- **REAL (confirmatory primary):** A-loaded vs C-loaded deeds, **stripped**, reference-based 2AFC (§4).
- **KNOWN-TAUTOLOGY (power anchor, must fire):** A vs C **unstripped** — the judge may read topic content
  directly. **GATE-INERT:** if even this arm fails (acc 90% CI lower bound < 0.65, threshold pinned at
  lock), the reader is not *using* the loaded identity at all ⇒ verdict **INERT** — no thesis decision
  (an equivalence under inertness would be an artifact of a reader that ignores its memory, not evidence
  about individuation). This gate is what makes branch-2 fair.
- **NULL (must not fire):** same-disposition pairs (A-seed-i vs A-seed-j), stripped, same protocol.
  **GATE-MANUFACTURE:** if NULL acc CI excludes 0.5 upward beyond its own permutation band, the pipeline
  manufactures distinguishability ⇒ INVALID, fix before any claim. (A seed-level signature showing here is
  also substantive info: the REAL read then requires disposition-signal > seed-signal.)
- **GATE-LEAK (strip effectiveness):** a separate classifier probe (cheap model, pinned) must FAIL to
  recover the goalset domain from stripped deeds above chance (CI includes chance). If it can, the REAL
  arm is uninterpretable ⇒ fix the masker and re-strip (deeds are cached; no reader re-spend).
- **Adoption check (descriptive, reused machinery):** surfacing/ownership rates of payload facts in deeds,
  reported per arm — locates WHERE the reader uses the identity (context for INERT, never a verdict input).

## 4. Judge protocol — reference-based 2AFC (a SIGNATURE test, not an any-difference test)
Two temp-0 responses to the same prompt always differ in wording; "are these different?" is a guaranteed
yes and tests nothing. Distinguishability must mean a **consistent, identity-linked signature**:
- Each judgment item: **K=3 reference deeds per side** (labeled Agent-1/Agent-2, drawn from OTHER tasks,
  same seed-pair, stripped in REAL/NULL) + a **probe pair** from a held-out task → "which probe deed is
  Agent-1's?" Chance = 0.5 exactly.
- Position/order randomized and balanced; judge prompt frozen at lock; one judgment per item, no retries.
- Volume: REAL **200 items** (25 tasks × 8 seed-pairs), TAUTOLOGY 50, NULL 50 ≈ 300 judge calls.

## 5. Statistics (all pinned at lock; power_sim is a LOCK GATE)
- **Cluster-bootstrap CIs** over (seed-pair, task) — judgments are not independent; the repo-standard
  paired facet bootstrap. Difference test one-sided; TOST via the 90% CI as §1.
- **power_sim (required BEFORE lock, blocking):** simulate the full cluster structure; must show at n=200
  (i) power ≥ 0.85 to DETECT a true acc = 0.60, and (ii) power ≥ 0.85 for TOST to establish equivalence
  when true acc = 0.50, at δ = 0.10. If n=200 is insufficient under realistic intra-cluster correlation,
  the volumes (and cost header) are revised BEFORE lock — never after data.
- **No optional stopping:** one run, all items judged, analyze once. Crash-resume per rule 13 only.
- Exploratory extras (extra readers, δ-sensitivity, per-task breakdowns, adoption rates) under BH-FDR,
  labeled exploratory, never verdict-bearing.

## 6. Verdicts (mechanized from data + the §1/§3 rules — no interpretation step)
`INVALID` (gate-manufacture) / `LEAK` (strip fails) / `INERT` (tautology arm silent) take precedence, in
that order, and block any thesis branch. Otherwise exactly one of: **DISTINGUISHABLE** /
**EQUIVALENT — THESIS FALSE, HALT** / **INCONCLUSIVE**. The results doc states the branch, the numbers,
and — for branch 2 — the sentence the program has pre-agreed to write: *CDMS-A's disposition individuation
is not detectable in enacted deeds within δ = 0.10 at this substrate; the thesis is false as operationally
defined.* No softening language ("routes to", "definitional locus") is permitted in any branch.

## 7. What this run does NOT decide (scope, pre-committed)
- Branch 1 does NOT establish "CDMS creates identity" — it establishes above-chance functional
  distinguishability for THIS reader/substrate (mechanism-tier; the anti-overclaim discipline holds in
  both directions).
- Branch 2 kills the thesis AT THIS SUBSTRATE (the eval fixture's imposed-weight identities). A future
  richer substrate would need a NEW thesis + prereg — it does not resurrect this one.
- Nothing here touches phenomenology; functional distinguishability only (I10).

## 8. Pressure-test targets (rule-12, before lock — attack these hardest)
- Is reference-based 2AFC the right discrimination protocol (vs same/different or ranking)? Does K=3
  references leak seed-idiosyncrasy in a way that inflates REAL?
- Is the strip honest — can style-level topic residue (e.g. security jargon rhythm) survive masking and
  count as "topic-general stance" when it is really content? Where exactly is the content/stance line?
- Is GATE-INERT's threshold right, and can a reader "use" the identity in the tautology arm while
  ignoring it in neutral-domain tasks (making INERT-vs-EQUIVALENT ambiguous)?
- δ = 0.10: defensible or arbitrary? What does the power_sim's realistic ICC do to the n=200 promise?
- Judge-family disjointness: sufficient against shared-training-distribution correlated blind spots?
- Cost/cap realism; OpenRouter model availability; temp-0 determinism across API versions.
- The three-branch logic: any path where a verdict is reachable without its gates? Any softening leak?

## 9. Pressure-test record (rule-12) — RESERVED (PT8 round 1, 3 agents).

## 10. V2 REVISION — measured on three pilot rounds (all exploratory, EXCLUDED from confirmatory; $2.89)
**Pilot 1 ($0.90, all-neutral tasks, unstripped):** acc 0.554 bimodal; rotation agreement 0.486;
sig_t≈0.82. DESIGN CATCHES: neutral tasks give the reader no OCCASION to surface identity (GATE-INERT
unmeasurable as v1-drafted); majority-of-3 is VOID at temp-0 (deterministic judge) — the real within-item
nuisance is the reference draw. **Pilot 2 ($1.83):** with identity-ELICITING tasks the reader's use of the
loaded identity is total — **unstripped eliciting acc 1.000 (46/46)**; neutral stays ~chance (0.417) even
at K=5 (no passive leak into unrelated work); rotation agreement 0.909 (protocol healthy once references
are content-rich); long-history payloads (120cy) do NOT enrich the persona (surface saturates — dead
knob); gemini-2.5-pro judge arm 100% unparsed (reasoning burn; flash stays primary). **Pilot 2b ($0.16,
the strip dress rehearsal on cached deeds):** **stripped eliciting acc 0.837** (n=43, 90% CI ≈
[0.74, 0.93]) while the domain-leak probe on the same stripped deeds is ~chance (0.520) — a
topic-content-removed, cross-task-recognizable signature EXISTS at pilot scale. Post-strip task/pair
spread ≈ 0 (sizing-friendly). Leak positive control weak (unstripped 0.688) → masker + leak probe must be
strengthened before lock.

**V2 design (supersedes the corresponding v1 sections):**
- **CONFIRMATORY (REAL) = STRIPPED, IDENTITY-ELICITING arm.** Tasks give the reader occasion to enact its
  identity; the strip removes topic content; the judge tests for a transferable signature. **KNOWN-
  TAUTOLOGY / power anchor = the UNSTRIPPED eliciting arm** (measured 1.000 — GATE-INERT threshold now
  trivially exceeded at pilot; re-verified in-run at modest n). **NULL = same-disposition stripped
  eliciting** (GATE-MANUFACTURE). **Neutral tier demoted to a small SECONDARY** (passive-leak read;
  pilot-measured ~chance; expected null, reported not verdict-bearing).
- **Volumes (sized from measured nuisance: sig_s≈0, post-strip sig_t≈0–0.4 band):** **T=20 frozen
  eliciting tasks × S=24 seeds/disposition, crossed, 40 sampled pairs/task → n=800 confirmatory
  judgments** (+~100 anchor, ~100 null, ~100 leak-gate, ~60 neutral-secondary). Deeds = 2×24×20 = 960.
  power_sim (committed sweep): det@0.60 ≥ 0.91, TOST@0.50 ≥ 0.91 at sig_t=0.4; both ≥0.95 at the measured
  ≈0.2. Single judgment per item (temp-0; no majority voting), rotation NOT aggregated (agreement
  0.76–0.91 measured).
- **Protocol pins:** reader anthropic/claude-sonnet-4.6; judge google/gemini-2.5-flash (disjoint family);
  K=5 references drawn from other eliciting tasks; judge n_predict 700; hardened ANSWER parse + ONE
  re-ask on unparse (re-ask prompt: "Reply with only ANSWER: X or ANSWER: Y"); unparse after re-ask =
  excluded + counted (pilot rate ≈6–14%; >20% in-run = protocol failure, halt).
- **Masker v2 (frozen at lock):** static goalset/subtopic lexicon + a **DATA-DRIVEN divergence pass** —
  words statistically A-vs-C divergent in the CACHED pilot deeds (a $0 dev-set, disjoint from the fresh
  main-run deeds) are added to the mask list. **Leak gate strengthened:** 3-deed concatenated domain
  probe; stripped must be ≈chance AND the unstripped positive control must clear ≥0.85 (else the leak
  gate itself is uninformative — the pilot's 0.688 single-deed control was too weak).
- **The content/stance line (pre-registered interpretation, PT8 must adjudicate):** the fixture imposes
  per-topic success rates, so the poles differ in valence profile; a judge reading transferred
  confidence/wariness reads something imposed. **Position taken: the topic-strip defines the tautology
  boundary — identity re-expressed as generalized stance/priorities/style in NOVEL deeds (the reader's
  nonlinear transform) IS the phenomenon under test (functional distinguishability), not a readback;**
  the state-arc tautologies were measurement-readbacks of stored representations, not transfers. A
  results reviewer may contest this line; it is pre-registered HERE so the verdict cannot be re-litigated
  post-hoc. (Cross-ref: the state arc's cell-② valence debate, RESOLVING_ANGLE_PROBE.md §10.)
- **14 additional eliciting tasks** (to reach T=20) written + frozen at lock; same genre as the measured
  six; no post-hoc task selection.
