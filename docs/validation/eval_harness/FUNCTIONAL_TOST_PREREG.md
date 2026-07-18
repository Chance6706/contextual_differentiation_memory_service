# The functional TOST — the terminal falsifier of the CDMS-A individuation thesis (task #10)

**STATUS: LOCKED (2026-07-18) — v3-FINAL, after PT8 (3 agents) + five measuring rounds ($5.04, all exploratory/excluded). Runner: tools/eval_harness/tost_main.py; sizing gate: tools/eval_harness/tost_power_sim_v3.py. Run authorized under Josh's $50 arm grant (2026-07-17: 'make it as far as you can'; hard stops = budget >$50, INCONCLUSIVE follow-on). No design change after this stamp; any deviation = a disclosed amendment.** On branch `research/differentiation`.

## FINAL DESIGN (v3, LOCKED) — every number pinned; §§9–11 = the audit trail that produced it

## 1. Decision rule (pre-committed)
**Operational definition (δ folded in, PT8-legit M4): individuation ≝ above-chance relational
distinguishability of enacted deeds BY A MARGIN ≥ δ, to a blind frontier judge.** δ = 0.10 (free
parameter; basis: acc 0.60 ≈ the weakest tell a downstream consumer could act on; sensitivity at
0.05/0.15 reported, never verdict-bearing). α = 0.05 both tests.
Primary statistic: judge 2AFC accuracy on the REAL arm. Tests: difference (one-sided, 95% one-sided
lower bound > 0.5) and TOST (90% CI ⊂ (0.40, 0.60)), both on the pinned bootstrap (§5).
**Precedence:** validity gates (§3) first — INVALID / LEAK / EXPRESSION-INERT / PROTOCOL-FAILURE block
any thesis branch (remediate + fresh re-run per rule 13; escalate to Josh if unfixable; NEVER converted
to INCONCLUSIVE). Then exactly one of:
1. **DISTINGUISHABLE** — diff rejects AND TOST does not: pinned sentence §11, anti-inflation bar.
2. **EQUIVALENT — thesis FALSE, HALT** — TOST rejects AND diff does NOT reject (disjointness fix,
   PT8-stats M3): pinned sentence §6/§11.
3. **INCONCLUSIVE** — neither rejects (or the in-run sig_t guard downgrades an EQUIVALENT, §5): reported
   plainly; any follow-on = new prereg + Josh (the pre-authorized $0 worktree exploration may proceed).

## 2. Design (all pinned)
- **Payloads:** valence-MATCHED fixture (`MATCHED_SUCCESS`, tost_pilot3.py — process-local; committed
  `_ENTITY_SUCCESS` untouched), dispositions A vs C, **S = 24 seeds/disposition**, 40 cycles, real v1
  SessionStart preamble render. Reader: **anthropic/claude-sonnet-4.6**, temp 0, n_predict 550.
- **Tasks: T = 20 identity-ELICITING tasks, frozen in the runner (`TASKS20`)** = the 6 measured
  (GATE_TASKS) + 14 fresh same-genre. **Robustness gate (PT8-legit M3b): branch-1 requires the
  14-fresh-task subset to independently clear the difference test; else downgrade INCONCLUSIVE.**
- **Deeds:** 2 × 24 × 20 = **960**, fresh cache (rule 13).
- **Judge:** **google/gemini-2.5-flash** primary (measured ≈ pro, 6× cheaper); **gemini-2.5-pro
  (reasoning=low, n_predict 2000) on a 100-item subset** = pre-registered robustness read (FDR).
- **Masker v3 (frozen):** static topic lexicon + suffixes + numeric-readback masking
  (tost_pilot3.strip_v3); NO data-driven divergence pass (PT8-construct M1: circular).

## 3. Arms + validity gates (tri-reference, all judged with POOLED refs per §4 unless stated)
- **REAL (confirmatory): stripped, A-vs-C, n = 800** (20 tasks × 40 sampled crossed pairs, balanced).
- **EXPRESSION GATE (replaces the old INERT anchor; pilot-3b lesson): SAME-SEED refs, unstripped,
  n = 48; 90% LB must be ≥ 0.80** (measured 1.000) — verifies the reader enacts the loaded payload at
  all. Failure ⇒ EXPRESSION-INERT (a validity block, not a verdict).
- **POOLED-UNSTRIPPED arm, n = 100 (reported, not verdict-bearing):** the content-included
  disposition-level signal (pilot band 0.57–0.61) — the tautology-channel anchor under the honest
  protocol.
- **NULL: A-vs-A stripped pooled, n = 100.** GATE-MANUFACTURE: X-rate outside the within-item
  label-shuffle permutation band (95th pct, B=1000) ⇒ INVALID.
- **LEAK gate ($0): BOW domain classifier** trained on UNSTRIPPED deeds (seed-fold split), tested on
  stripped: recovery CI must include 0.5. + **BOW LOSO diagnostic reported** (pilot: 0.708 — the
  stylometric-trace channel; S6 limitation registered: strip = domain-unrecoverable, not
  style-residue-free).
- **NEUTRAL secondary, n = 48** (5 pilot-1 neutral tasks): the passive-leak scope read (pilot ~chance).

## 4. Judge protocol (pinned)
Reference-based 2AFC: **K = 5 refs/side, POOLED — drawn from seeds ∉ {probe seeds} and tasks ≠ probe
task**; position/labels **exactly balanced** across items per arm; single judgment (temp 0); parse =
final ANSWER line + lenient fallback + **one re-ask** ("Reply with only ANSWER: X or ANSWER: Y");
unparse-after-re-ask excluded + counted; **>12% unparse in any arm ⇒ PROTOCOL-FAILURE halt.**

## 5. Statistics (pinned)
- **Bootstrap: 3-way (task, seedA, seedC) SETS-variant cluster bootstrap, B = 10,000** (PT8-stats:
  conservative-to-nominal at the operating point; variant pinned because the choice swings power).
- power_sim: committed at `tools/eval_harness/tost_power_sim_v3.py` (det@0.60 ≥ 0.91, TOST@0.50 ≈ 0.88
  at sig_t ≤ 0.4, sig_s ≈ 0 — both measured on the actual protocol).
- **In-run sig_t guard:** noise-corrected per-task sd on REAL > 0.4-equivalent ⇒ an EQUIVALENT verdict
  downgrades to INCONCLUSIVE (PT8-stats M4).
- **Unparse dual-analysis:** primary = excluded; sensitivity = impute-as-miss; the two must AGREE on
  the branch, else INCONCLUSIVE (PT8-stats M5).
- Exploratory (pro subset, δ-sensitivity, per-task, BOW diagnostics, neutral) under BH-FDR; BCa
  robustness re-analysis reported.
- No optional stopping: one pass, analyze once. Per-item JSONL retained + cache dirs RETAINED (M5).

## 6. Verdicts — mechanized; §11's pinned sentences are the ceiling AND floor of any narrative.

## 7. Scope (pre-committed): branch-1 is mechanism-tier (one reader/judge/substrate, eliciting tasks,
imposed dispositions); branch-2 kills THIS substrate's thesis; the BOW stylometric trace is reported
either way as a diagnostic, never a verdict. No phenomenology (I10).

## 8. Cost + ops: 💵 est ~$13–16, **hard cap $30** (CostGuard). Wall-clock ≈ 2.5–4 h serial (payloads
~25 min CPU + 960 deeds + ~1,100 judge calls). Fresh cache; crash-resume via cache is the only reuse.
Arm total incl. pilots ≤ $50 (spent $5.04).

## 9. Pressure-test record (rule-12) — PT8 ROUND 1 DONE (3 agents, 2026-07-17). v2 NOT lockable; → v3.
**Consolidated verdict:** salvageable; thesis still live; one fold-and-pin pass + ONE more measuring round
(pilot 3, blocking) → lock. Key findings + dispositions (all three reports verbatim in session log):

**PT8-construct (empirical, $0 on cached deeds) — the round's decisive result:**
- **The 0.837 DECOMPOSES: ~47% seed-fingerprinting** (same-seed references let the judge identify the
  particular HISTORY: BOW LOTO 0.854 → LOSO 0.688; within-disposition seed-2AFC 0.83–0.97 ≥ the
  cross-disposition signal) **+ ~50% imposed-valence readback** (fixture wires A-goalset mean success 0.71
  vs C 0.54 → "A" ≡ "the more confident persona" by construction — the state arc's cell-② tautology in
  prose) **+ ~10–15% residual domain lexemes. Format: 0%** (honest negative). **A bag-of-words classifier
  reproduces the LLM judge (0.854 ≈ 0.837)** — the signature is linearly decodable; the "nonlinear reader
  transform" story unsupported. **§10's content/stance line: UNTENABLE as pre-registered.**
- **HONEST NEGATIVE THAT KEEPS THE THESIS ALIVE: a real cross-seed signal ≈0.69 LOSO survives** — failure
  is attribution/confound + protocol, NOT signal absence.
- **DISPOSITIONS → v3:** (1) **POOLED-across-seed references** (test disposition, not history);
  (2) **VALENCE-MATCHED fixture** (equal mean success across goalsets via a TOST-specific success table —
  do NOT edit the committed `_ENTITY_SUCCESS`, parameterize; the state-arc artifacts must reproduce);
  (3) **stance-eliciting, inventory-suppressing task genre** (T=20 ALL-FRESH — also resolves legit-M3's
  discovery-task contamination; guardrail: reject tasks whose reference answers enumerate areas/counts);
  (4) **masker v3 = static topic lexicon only** (+ plurals/stems, curated short words, MASK NUMERIC
  READBACKS "(17 trouble / 38 seen)") — the data-driven divergence pass is KILLED (circular: strips the
  signal itself; unpinned threshold = verdict knob); (5) **leak gate = trained BOW classifier, honest
  split, CI must include 0.5** (the LLM probe read 0.520 while BOW recovered 0.688 from the same deeds).
**PT8-stats (independent sim rebuild) —** det@0.60 replicates (0.91✓); tost 0.88 (not 0.91 — restate);
  valid ONLY at sig_t≤0.4 (at 0.8: power collapses, false-thesis-kill ≈0.10); 3-way (task,seedA,seedC)
  bootstrap is the RIGHT dependence model incl. shared-deed reuse (1-way fails, false-eq 0.185); the SETS
  resample variant is conservative-to-nominal at the operating point (pin it EXPLICITLY — variant choice
  swings tost power 0.55→0.96). **DISPOSITIONS:** commit the v2/v3 sizing sim as the lock-gate artifact
  (replace the dead n=200 sim); pin bootstrap=3-way-SETS + B; **branch disjointness fix: EQUIVALENT ≡
  TOST-rejects AND diff-NOT-rejects** (both-fire cell confirmed P 0.002–0.01; at true 0.55 verdicts
  coin-flip — precedence pinned); **in-run sig_t guard** (measured on the actual 20 tasks; >~0.4 ⇒ an
  EQUIVALENT verdict downgrades to INCONCLUSIVE); **unparse dual-analysis** (excluded AND impute-as-miss
  must AGREE on the branch; halt tightened ≤12%); power detection at 0.65 (margin-edge tension); NULL-gate
  permutation band = within-item label shuffle, 95th pct; exact position balancing; anchor re-verify n +
  threshold + mid-run-fail branch; BCa robustness re-analysis.
**PT8-legit —** M1 doc-migration (interim stamp committed cd8d33e; full §§1–6 consolidation AT LOCK);
  **M2 branch-1 sentence PINNED (see §11) + anti-inflation bar**; M3 → superseded by all-fresh tasks;
  M4 → δ folded into the §0 operational definition ("…distinguishable BY A MARGIN ≥ δ"), validity gates
  walled off from INCONCLUSIVE (protocol-failure = remediate + fresh re-run, NOT a verdict); **M5 per-item
  JSONL retention + cache dirs RETAINED (not burned)** — required by the pre-authorized $0
  INCONCLUSIVE/INERT worktree paths; M6 → moot (divergence pass killed); S2 δ=0.10 basis → one-line
  justification + PARAMETER_BASIS (free); S3 cost header fixed ($2.89 verified); S4 wall-clock envelope
  (~3–4 h serial); S5 report ALL arms with CIs regardless of verdict; **S6 registered limitation: the
  leak gate excludes domain-RECOVERABILITY, not content-correlated STYLE** — baked into the branch-1
  sentence; S7 neutral-demotion disclosure sentence pinned (construct-validity move, pilots exploratory
  + excluded, neutral retained as secondary).

**→ PILOT 3 (BLOCKING, ~$1.5–2.5):** valence-matched payloads + pooled refs + stance-genre tasks +
masker v3 + classifier leak gate → measures the post-fix REAL preview + post-strip sig_t/sig_s on the
ACTUAL protocol → final sizing → full §§1–6 v3 consolidation → LOCK → main run. Expected REAL after
de-confounding: ≤0.69 and possibly ~chance — the outcome is genuinely open, as a terminal falsifier
should be.

## 11. Pinned branch sentences (PT8-legit M2; the ceiling and the floor of any results narrative)
**Branch-1 (DISTINGUISHABLE) — pinned ceiling, no inflating language permitted ("CDMS creates identity",
"individuation confirmed", "distinct selves", "personality" are all barred):** *"With one frontier reader
(anthropic/claude-sonnet-4.6) and one blind cross-family judge (google/gemini-2.5-flash), enacted deeds
from two valence-matched imposed-disposition identities were distinguishable above chance by ≥ δ=0.10
after topic-content stripping, on identity-eliciting tasks, on this eval fixture. This establishes
above-chance functional distinguishability for this reader/judge/substrate when the task occasions
identity enactment — a mechanism-tier positive — and no more: it does NOT show CDMS creates identity;
does NOT generalize beyond these dispositions, reader, or task genre (neutral-task distinguishability was
~chance); 'content-stripped' means topic-content not domain-recoverable, NOT proven free of
content-correlated style; and no claim about phenomenology (I10)."*
**Branch-2 (EQUIVALENT) — unchanged from §6:** thesis FALSE as operationally defined, HALT.
**Neutral-demotion disclosure (pinned, must appear in results):** *"The confirmatory arm was moved from
neutral to identity-eliciting tasks after exploratory pilots (excluded from confirmatory) showed neutral
tasks give the reader no occasion to enact its disposition (neutral 2AFC ≈ chance), making the hypothesis
untestable on that tier; the neutral arm is retained and reported as a secondary passive-leak read, and
branch-1 distinguishability is therefore scoped to identity-eliciting tasks."*

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
