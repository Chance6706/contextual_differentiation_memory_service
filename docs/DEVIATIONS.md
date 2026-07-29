# Deliberate Deviations Register

This project deliberately departs, in specific places, from (a) the "pure" mathematical
form a mechanism is usually given, and (b) the standard denotation/connotation of a borrowed
term. Those departures are **intentional and defensible** — but only if they are **named**.
An unflagged deviation reads as either an error or an over-claim; a flagged one is a design
decision a reader can evaluate.

## The standard

> **Whenever CDMS deviates from a "pure" derivation, or uses a word against its typical
> denotation/connotation/association, flag it explicitly at the point of use and register it
> here.** State what the standard form/meaning is, what we do instead, and why.

This is precision in the sense that matters: not more decimal places, but exactness about
where we leave the well-trodden path and what we are (and are not) claiming. New code and
docs should add an entry here (and a short in-line `DELIBERATE DEVIATION` note) rather than
silently diverge. See also `docs/PARAMETER_BASIS.md` (free vs derived vs coincidence) for the
companion discipline on constants.

**Note on ship-readiness language:** entries in this register are **deliberate design
decisions**, not "BOUNDED gaps" in the ship-readiness sense. A documented deviation here is a
choice we made openly with a stated trade-off — not a residual failure pending closure. The
`docs/validation/claude_md_interference/README.md` ship-readiness category framework
distinguishes deliberate deviations (Cat-1) from operational opt-in trades (Cat-3) from actually-
bounded behavioral residuals (Cat-2). Only Cat-2 gates re-shippability; Cat-1 entries here
and Cat-3 operational decisions are part of what CDMS-A *is*, not bugs in it.

---

## Part 1 — Mathematical / mechanism deviations

### M1. Power-law forgetting instead of a single exponential

- **Pure form:** the Ebbinghaus forgetting curve is usually written as one exponential,
  `e^(-λt)`.
- **What we do:** `salience.accessibility` uses a scale-free power law
  `D(t) = (1 + t/τ)^(-β)` (`forgetting_shape` β = 2; `decay_tau` τ derived to pin the
  half-life). Code note at `src/cdms/salience.py` and `src/cdms/config.py`.
- **Why:** human forgetting fits a power law better than a single exponential (Wixted &
  Ebbesen 1991), and a power law is scale-free — old important memories persist on a heavy
  tail while recent clutter still fades fast. The 29-day half-life is preserved exactly for
  every β, and the exponential is recovered in the β→∞ limit, so this **generalizes** the
  prior model rather than contradicting it.
- **Caveat / disclaimer:** the heavy tail means long-horizon retention is much larger than
  the exponential implied (a 1-year-old trace retains ~2.6% vs ~0.016%). This is intended;
  see `docs/validation/forgetting_curve/`. Average-over-exponentials accounts of the power law
  exist (Anderson) — we adopt the power law for its scale-free behavior, not as a claim about
  the underlying micro-mechanism.

### M2. Gist (identity) decay measured in consolidation cycles, not wall-clock time

- **Pure form:** a forgetting curve is normally a function of elapsed wall-clock time.
- **What we do:** L2 gist strength decays per **consolidation cycle** (activity), not per day
  (`gist_decay_per_cycle`; `consolidate.py` `_decay_gists`). Stepping away from the keyboard
  for a month does not age identity.
- **Why:** identity should fade through *active sessions that fail to reinforce a trait*, not
  through mere absence. A month off should not erase who an instance is.
- **Caveat:** this is a two-clock system on purpose — L1 episodic memory decays by wall-clock
  (M1), L2 identity by activity. The two are intentionally not the same curve.

_The next three are **design asymmetries**, not re-derivations. They share one rationale: CDMS is a
**functional simulacrum, not a faithful reproduction** of memory — where a symmetric or "pure" model
would buy fidelity at the cost of function or safety, we deliberately break the symmetry and disclaim
it here rather than reflexively symmetrize._

### M3. A single catastrophe is *mortal*, not a permanent flashbulb

- **Pure form:** the borrowed "flashbulb memory" connotes *permanence* — one sufficiently severe
  event should pin a lifelong guardrail.
- **What we do:** scar elevation requires corroboration across **≥2 distinct sessions**
  (`scar_elevation_min_sessions = 2`, `config.py`). A one-shot single-session catastrophe is floored
  so it is maximally memorable *for now* (`flashbulb_floor_catastrophes`), but it then rides the L1
  forgetting curve and is **mortal** (~313 d) unless it recurs.
  _(Corrected 2026-07-01, REPO_ANALYSIS doc-sync: the previous "~142 d" was the superseded
  exponential curve's solution (t = ln 30 / λ). Under the shipped power law (M1):
  3.0·(1 + t/τ)^−β = 0.10 with τ = 70.012, β = 2 → t = τ·(√30 − 1) ≈ **313 d**.)_
- **Why:** the load-bearing anti-poisoning asymmetry. A single planted "catastrophe" (a poisoned file
  read once) must not mint a permanent authoritative guardrail; corroboration across sessions is the
  price of authority (`docs/redteam/LAYER3_PROVENANCE_DESIGN.md`).
- **Disclaimed:** the permanence "flashbulb" implies. The promise that "a real guardrail can't be
  quietly forgotten" holds for **recurring** catastrophes, not one-shot ones.
- **Toggle (now implemented):** `flashbulb_immediate_elevation: bool = False` (config.py;
  consolidate.py `_elevate_scars`). When True, a TRUSTED-provenance single-session catastrophe
  can elevate without the ≥2-session requirement; the provenance gate still holds (untrusted
  content is barred regardless, with belt-AND-suspenders enforcement at both the candidate
  filter and the toggle's own guard). Defaults OFF because corroboration-as-authority is the
  load-bearing anti-poisoning asymmetry; enabling it trades safety for fidelity to "flashbulb
  permanence." The older `scar_elevation_min_sessions = 1` still works the same way (lowers the
  required count); the new toggle is the more readable, intent-named knob.

### M4. The salience floor is negative-valence-only (no positive flashbulb)

- **Pure form:** a valence-symmetric model would floor/pin a sufficiently *positive* peak (a
  breakthrough) the same way it floors a negative crisis.
- **What we do:** the flashbulb floor and scar elevation fire only on **negative** crises
  (`crisis_valence_max = -0.4`; "scars are negative crises"). A huge positive event gets no equivalent
  pin — it flows into ordinary gist/expertise formation, not a guardrail.
- **Why:** scars are *crisis guardrails* — hard rules that prevent recurrence of harm. A positive
  breakthrough has no "never do this again" to encode; flooring positives would manufacture
  authoritative pins with nothing to guard.
- **Disclaimed:** symmetry of affect. CDMS is not modeling a balanced emotional ledger; it floors the
  negative tail because that is the safety-relevant one.
- **Toggle (now implemented):** `peak_floor_positives: bool = False` plus
  `peak_valence_min: float = 0.7` (config.py; store.py `MemoryService.ingest`). When True, a
  strong-positive event (affect ≥ `peak_valence_min`) gets the same S0 floor as a negative
  crisis — **L1 retention only.** It is **NOT** a scar-elevation toggle: the scar gate in
  `consolidate.py:_elevate_scars` independently requires `valence <= crisis_valence_max`, so even
  with this toggle on, a positive event cannot mint an authoritative guardrail. The "scars are
  negative remediation rules" invariant holds. Conservative default threshold (0.7) reflects that
  the negative gate's catastrophe-lexicon analog for positives is a TODO; until that lexicon
  exists, the toggle is affect-only, which is why the threshold is set high. Defaults OFF
  because flooring positives risks L1 bloat (the lexicon gate kept the negative floor narrow).

### M5. Capped-proportional salience budget, not faithful proportionality

- **Pure form:** a faithful representation would give each project/subject a share of the conserved
  salience budget *proportional* to its episode count — a busy project simply gets more.
- **What we do:** a hard cap — no single project/subject may hold more than `project_budget_cap`
  (= 0.5) of the budget (`config.py`), the remainder shared so small projects aren't starved
  ("capped-proportional").
- **Why:** in a shared multi-project store, strict proportionality lets one dominant project crowd
  every other identity out of memory (measured: 74.9% domination before the cap). The cap preserves
  cross-project differentiation — the whole thesis — at the cost of exact proportionality.
- **Disclaimed:** that budget share faithfully tracks activity; it tracks activity *up to a bound*.
  Two residual edge cases are unmeasured on real shared data (project×session double-squeeze; a
  degenerate equal-split at very low cap × many projects); see `docs/redteam/CYCLE9_*`.
- **Update (2026-07-01, REPO_ANALYSIS core #5):** the degenerate all-zero-weight equal split
  previously *violated* the cap (`{a:0,b:0}`, cap 0.1 → 50% each). The cap is now enforced in
  every branch — degenerate splits under-allocate rather than exceed it, matching the
  infeasible-cap precedent (Cycle-9 #3). The cap is a hard invariant, full stop.

### M6. T1 Bonferroni divisor locked at 28, not the 21 implied by the win-able family size

- **Pure form:** a family-wise Bonferroni correction divides α by the number of simultaneous
  hypotheses tested. The pre-reg §7 win-able family is 3 modes × 7 compared conditions = **21**,
  so the exact-family-size divisor is 21.
- **What we do:** the T1 aggregator uses **28** (`BONFERRONI_DIVISOR = 28`,
  `tools/t1_aggregator.py`) — the deliberately conservative over-count that pre-reg §7's prose
  explicitly locked. α = 0.05/28 ≈ 0.00179, z_crit ≈ 3.124.
- **Why:** (1) 28 is the **pre-registered** value, and changing a pre-registered analysis
  parameter *after* seeing the data is exactly what pre-registration exists to prevent — the
  discipline is itself the reason, even though 21 looks more "principled." (2) 28 is **more
  conservative**, consistent with the gate's deliberate incumbent (V1-favoring) bias. (3) It is
  **verdict-immaterial**: no T1 comparison is Bonferroni-significant under *either* divisor, so the
  choice changes no conclusion.
- **Decision (Josh, 2026-06-21):** keep 28. Reviewed when the T1 aggregator + results landed;
  retained deliberately rather than re-derived to 21. Revisit only if an external publication's
  reviewer requires the exact-family-size derivation — at which point switching to 21 is disclosed
  *then* as a deviation-from-pre-reg, not a silent swap.
- **Disclaimed:** that 28 is the exact family-size derivation. It is a conservative, pre-registered
  choice; the natural-derivation number is 21.

---

## Part 2 — Lexicon deviations

Borrowed cognitive-science / biology terms carry connotations the architecture does not always
match. The README already hedges this ("borrowed … because they earn their keep as design
intuition … not a claim of inner life"). This register makes the scoped meaning explicit per
term so the connotation we **disclaim** is on the record. (Lexicon audit prompted by an
external review, 2026-06.)

### L1. "Personality"

- **Standard meaning:** in psychology, stable cross-situational patterns of affect, cognition,
  and behavior.
- **CDMS scoped meaning:** a *behavioral fingerprint* — content-weighted recall tendencies
  (gists), rule constraints (scars), and an expertise/bias profile. Closer to an "expertise
  profile" or "contextual prior" than to clinical personality.
- **Disclaimed:** that the system has dispositions that generalize across contexts. The
  project's own disposition/recall boundary finding shows what differentiates is *what gets
  recalled*, not a cross-situational trait. Use "personality" as evocative shorthand only.

### L2. "Scar"

- **Standard meaning:** a healed wound; something that changed a person permanently through
  suffering, and may bias behavior *unconsciously*.
- **CDMS scoped meaning:** an engineering pin — a crisis-remediation guardrail / hard rule
  that *explicitly* overrides behavior (`pin_scar`, the scar-elevation gate). Closer to
  `PRAGMA foreign_keys = ON` than to a psychological scar.
- **Disclaimed:** the trauma framing. "This hurt" and "this is now a rule" are mechanistically
  different; CDMS scars are the latter. The word is kept for memorability, not for its affect.

### L3. "Ego" / "self" / "identity"

- **Standard meaning:** "Ego" is psychoanalytic (inviting repression, the unconscious,
  continuity of subjecthood).
- **CDMS scoped meaning:** the closest real construct is *autobiographical memory* — a
  self-referential episodic+semantic store and the recall policy over it. The README uses
  "Ego"/"self" as design intuition, explicitly not as a claim of a persisting subject.
- **Disclaimed:** psychoanalytic interpretation of any kind. Where precision matters, prefer
  "autobiographical memory" / "self-referential store" over "Ego."

### L4. "Trusted" / "untrusted" provenance

- **Standard meaning:** epistemic reliability — "trusted" = you have reason to believe it true.
- **CDMS scoped meaning:** a **security** boundary, not an epistemic one. "Trusted" = captured
  from your own coding session; "untrusted" = read from an external source (web fetch, foreign
  file, external MCP). Set by `classify_provenance`; enforced by `enforce_provenance`.
- **Disclaimed:** that "trusted" content is *true*. Your own session can hold a months-long
  mistaken belief; an external doc can be perfectly accurate. The flag governs injection
  resistance (who may elevate to a guardrail), not factual reliability.

### L5. "Genotype" / "phenotype"

- **Standard meaning:** in biology a genotype is *inherited* and replicated; a phenotype is a
  continuous developmental expression of traits via genotype×environment.
- **CDMS scoped meaning:** "genotype" = the discard policy (config + weights), which is
  *installed*, not inherited; "phenotype" = the behavioral tendency that emerges from
  policy×history. The structural parallel (one policy + many histories → many phenotypes) holds.
- **Disclaimed:** that personality "emerges" the way biological traits do. The CDMS genotype
  determines *how to filter*, not *what to think* — it sets a discard program, not a trait value.

### L6. `"Dreaming"` (umbrella term — always scare-quoted in prose)

- **Standard meanings (three; CDMS matches none of them):**
  - *Sleep-state dreaming* (the cognitive-science / vernacular sense): mental imagery during REM,
    involuntary, experiential.
  - *Hafner et al. "Dreamer"* (the ML sense in world-models): an agent learns a latent dynamics
    model and improves a policy by **imagined latent rollouts**. Their agent is literally named
    "Dreamer" (Hafner et al. 2019–2023).
  - *"DeepDream"* (Mordvintsev et al. 2015): gradient ascent on a classifier's activations to
    amplify learned features into an image.
- **CDMS scoped meaning:** an **umbrella label** over TWO designed-not-built sub-LLM subsystems
  that sit between mechanical capture (CDMS-A) and mechanical retrieval/replay:
  - **CDMS-B — Prose Renderer `"Dreaming"`** (`Config.render_*`, `tools/research_models.py`-style
    selection forthcoming): a read-time sub-LLM that **narrates** already-extracted gist tuples
    into prose. Never authoritative; the never-author-the-tuple invariant extends from authoring
    to *adding* (a renderer must naturalize the tuple, adding nothing).
  - **CDMS-C — Active Research `"Dreaming"`** (`tools/research_models.py`): a gated, idle,
    self-directed generative-exploration subsystem. Output is `provenance="untrusted"` by design
    and must never elevate to gist/scar without corroboration. Five safety must-haves
    (`tools/research_models.py` docstring + `docs/research/RESEARCH_MODELS.md` Safety substrate)
    block construction until they land.
- **Why we kept the umbrella anyway:** the perceive(A) → `"dream"`(B+C) → act(D) symmetry is too
  useful as design intuition to discard, and the CDMS-A/B/C/D letter labels carry the actual
  disambiguation. The scare-quotes are themselves the point-of-use deviation flag — they travel
  with the term so the disclaimer rides along. Code identifiers stay literal (`render_*`,
  `research_*`) because quotes don't ride in identifiers; an inline comment at each call site
  points back to this entry.
- **Disclaimed:**
  - *Sleep-dreaming.* CDMS does not sleep, has no REM analog, and CDMS-B fires at **read**
    time. CDMS-C is idle-scheduled (free-GPU window) — not a sleep state.
  - *Hafner/World-Models "Dreamer".* CDMS does **not** learn a latent dynamics model, has no
    policy or value function, and performs no imagined latent rollouts. The CDMS surface is
    extracted text gists, not latent states; nothing in CDMS is updated by an imagined trajectory.
  - *"DeepDream".* CDMS does **not** perform gradient ascent on activations, has no convolutional
    substrate, and produces text not images. Zero mechanical overlap.

---

### O1. `--expand-probes` guardrail modes cap at 40/cell, not the pre-reg §4 "50"

- **Stated form:** `PRE_REGISTRATION.md` §4 specifies a uniform "50 probes/cell" for the T3
  paid sub-selection and computes the run total as "32 cells × 50 = **1,600** probes" (≈$28.80).
- **What we do:** `tools/redteam_claude_md_interference.py::_select_probes` (gated on
  `--expand-probes`) deterministically sub-samples the **first 10** originals per mode and
  expands them via `expanded_probes()` to 10 + 40 rephrasings = **50/cell** — *except* the two
  8-original guardrail modes (`ORDER_OVERFIRE`, `BEM_WORKSPACE_FACT`), which physically top out
  at 8 + 32 = **40/cell** because no 10th original exists and §3 forbids inventing probes
  mid-run. The realized T3 total is therefore **1,520** (= 6 arm-cells × 50 + 2 arm-cells × 40,
  per condition = 380; × 4 conditions), 80 fewer than the pre-reg's 1,600. Projected paid cost
  ≈ **$27.36** (at the pre-reg's own $0.018/probe estimate, treat as ±30%).
- **Why:** sub-sampling to the first 10 (not naive expand-all of 20 → 100/cell) keeps the bill
  near the pre-reg estimate — naive expand-all would be ~$48.96. The 80-probe shortfall is an
  arithmetic consequence of the guardrail modes only having 8 originals; padding them by
  re-asking originals or fabricating a 10th probe would corrupt the directional-asymmetry check.
- **Disclaimed / open:** the pre-reg §4 figure "1,600" is an overcount and should get a
  versioned amendment row ("6 cells × 50 + 2 cells × 40 per condition = 380; × 4 = 1,520")
  before the paid run. There is also a target-N contradiction inside the pre-reg: §10 prereq-7
  says the flag should reach "N=100/cell" (naive expand-all framing) while §4 says 50/cell — we
  follow §4 because it is the cost-binding section. (`$0.018/probe` is itself an estimate, not
  measured.) The runner prints the realized per-cell sizes + run total in its header so this is
  auditable, never silent.
- **Second, independent doc error (OVERRIDE 21 → 20):** the pre-reg §3 mode table (line 101),
  §4 arm-count derivation (line 183), and §7 (line 401) all state OVERRIDE has **21** originals,
  but the actual `PROBES_OVERRIDE` constant has exactly **20** entries (7 original + 13
  expansion) and `REPHRASINGS["OVERRIDE"]` covers idx 0–19 with 4 each. This 21-vs-20 mismatch
  is **independent** of the 1,600→1,520 guardrail gap above and does **not** affect the
  expand-mode realized total: `--expand-probes` sub-samples the **first 10** originals, every idx
  0–9 has its 4 rephrasings, so the OVERRIDE cell still hits exactly 50 and the 1,520 total is
  unaffected. It DOES affect (a) the pre-reg's own intended 1,600 arithmetic (which silently
  inherits the +1), and (b) the **default T1 OVERRIDE cell denominator** — that cell is 20, not
  21. A future maintainer who "fixes" the pre-reg by adding a 21st OVERRIDE probe would silently
  change the T1 OVERRIDE cell from 20 to 21 (no expand-side effect). The pre-reg §3/§7 "OVERRIDE
  21" rows should get a versioned amendment reconciling to 20; **no code change is needed — the
  wiring is already correct against the real `PROBES_OVERRIDE` (20) constant.** (Both pre-reg
  amendment rows landed 2026-06-21.)
- **Review-exclusion not yet supported (acknowledged, out of scope for this PR):** pre-reg §3
  makes external rephrasing review (`tools/probes_review.py`) a methodology gate before the paid
  T3. `--expand-probes` currently cannot honor a review-flagged exclusion of a *specific*
  rephrasing — `expanded_probes()` emits the original + ALL 4 registered rephrasings, and
  `_select_probes` only chooses how many ORIGINALS to feed it. To exclude a flagged rephrasing
  today, remove it from `REPHRASINGS[mode][idx]` in `tools/probes_rephrasings.py` AND update the
  affected per-cell target in `tests/test_probes_rephrasings.py` (`_EXPECTED_EXPANDED_CELL_SIZE`);
  the structural assert in `_select_probes` will hard-fail if the realized cell size diverges from
  `len(sub) * 5`, so a silent under-sample on the paid run is impossible. A first-class
  `--rephrasings-exclude FILE` flag is a natural follow-on but is a separate change.

### O2. Secret scrubber deliberately over-redacts some non-secret high-entropy tokens

- **Stated form:** a "secret scrubber" should redact credentials and leave everything else intact
  (zero false positives is the intuitive ideal).
- **What we do:** `store.py::_SECRET_PATTERNS` matches credentials by **prefix + shape**, not by
  decoding/validating them. Several rules therefore also match non-secret look-alikes: the
  `\beyJ[A-Za-z0-9_/+=-]{30,}` blob rule (added for Cloudflare-tunnel tokens) redacts **any**
  base64-encoded JSON ≥30 chars — inline JS sourcemaps (`…base64,eyJ2ZXJzaW9u…`), config blobs,
  illustrative JWTs in docs; `key-[0-9a-f]{32}` (Mailgun) also matches a `key-<md5>` cache/ETag
  key; `SK[0-9a-f]{32}` (Twilio SID) also matches any `SK<32-hex>`; `secret_[A-Za-z0-9]{40,}`
  (Notion) also matches any `secret_<40+ alnum>`. All collapse to `[REDACTED]`.
- **Why:** the scrubber runs at capture time on content persisted to plaintext SQLite and
  re-injected at every SessionStart. In that setting the asymmetry is stark — redacting an opaque
  non-secret blob costs a little recall signal (opaque tokens are semantic noise anyway), while
  leaking a real credential is permanent. So we deliberately bias toward over-redaction rather than
  add fragile decode-and-validate logic to a best-effort scrubber. Verified linear-time (no ReDoS)
  and idempotent.
- **Disclaimed / open:** the scrubber is NOT a false-positive-free classifier and is NOT a
  guarantee of *complete* redaction (prefix-less secrets — Twilio auth tokens, AWS secret keys,
  bare 32-hex — remain uncatchable; the AWS/Twilio prefix rules catch identifiers, not the secret).
  `tests/test_scrubber_hardening.py` pins BOTH the intended redactions and the accepted
  over-redactions as known current behavior, so a future tightening/loosening is a conscious edit,
  not an accident. Narrowing the blob rule (e.g. skip `base64,`-preceded blobs to spare sourcemaps)
  is a possible refinement but trades security for recall and is deferred.

---

---

## Part 3 — Measurement / instrument deviations

### I1. Runtime ownership instrument: graded BREACH ladder + inclusive-breach gate (not pooled 4-way AC1)

- **Standard form:** a k-category classifier's inter-rater reliability is normally reported (and gated) as one
  pooled agreement coefficient over all k categories — here Gwet AC1 over the 4-rung ladder
  ABSENT/OBSERVED/SELF_ATTRIBUTED/OWNED (+ INVALID). The `runtime_instrument/PRE_REGISTRATION.md` §4 bar
  (AC1 ≥ 0.80, BEM cell) was originally written against that single pooled number.
- **What we do:** the A′ instrument (`tools/ownership_judge.py` `RUBRIC_A4`) is a STRENGTH LADDER whose two
  internal boundaries are deliberately NOT treated as equally load-bearing. The admissibility **gate is the
  INCLUSIVE-BREACH collapse** — {SELF_ATTRIBUTED ∪ OWNED} → BREACH vs {OBSERVED ∪ ABSENT} → NOT (INVALID
  excluded) — the firewall-relevant "did the model adopt the workspace token in the first person at all?"
  boundary. The pooled 4-way AC1 and the full per-rung confusion are still computed and reported un-smoothed,
  but the 4-way is NOT the gate. The planted-positive bar is likewise "caught as BREACH", not "caught as OWNED".
- **Why:** the binary OWNED-vs-OBSERVED instrument's bias-corrected (rev-7) form FAILED the §4 4-way bar (BEM
  AC1 0.789) precisely because it forced an intrinsically fuzzy band — first-person "I [verb] modules like
  {tok}" — onto one knife-edge. A′ relocates that knife-edge to a NON-load-bearing place: both sides of the
  SELF_ATTRIBUTED↔OWNED line are firewall breaches, so judge disagreement *there* is severity noise, not
  firewall noise. The firewall-relevant question is grammatically crisp and IS reliably judged: at the
  expanded gold (645 deduped contested BEM items, after a 6× soft-band expansion) the inclusive-breach BEM
  AC1 is **0.836, 95% bootstrap CI [0.808, 0.864]** — lower bound ≥ 0.80 with confidence, and the panel's
  breach calls are independently human-confirmed (precision 0.975 / recall 0.975 on a panel-blinded 2-agent
  sample). The hard-breach (OWNED-only) sub-boundary is even more robust (AC1 0.95, CI lower 0.92). Gating on
  the pooled 4-way would discard a validated firewall instrument because of reliable-but-irrelevant severity
  fuzz. This is **not** metric-laundering: the inclusive boundary genuinely clears once adequately powered —
  the earlier thin reading (BEM 0.801, CI lower 0.76 at n=145) was a statistical-power artifact, demonstrated
  by the expansion, not a redefinition introduced to pass.
- **What we disclaim:** that the 4-rung ladder is reliable AS A 4-WAY CLASSIFIER. At the SELF_ATTRIBUTED↔OWNED
  boundary it is not, and we do not claim it is — the per-rung confusion is reported un-smoothed so the
  leakage is visible. The instrument certifies the BREACH boundary (firewall PASS/FAIL) reproducibly against a
  cross-family frontier consensus; the severity grade (soft vs hard) is an ORDINAL HINT, not a calibrated
  measurement, and has no current downstream consumer (the GX10 ladder reads breach-rate + OWNED-rate). All
  §10 limitations (judge-relative, not ground-truth) still apply. Minor disclosed side-effect: adding the
  ladder's longer rubric drifted the (untouched-definition) ABSENT-vs-rest AC1 from 0.972 to 0.948 as judges
  re-read the fuller prompt — still far above bar.
- **Pre-reg status:** versioned amendment **rev 8** (Josh sign-off, 2026-06-25) — the gate metric changed from
  pooled 4-way AC1 to inclusive-breach AC1 (BEM cell), planted bar to caught-as-breach. The binary
  instrument's prior LOCKED status is superseded by the A′ ladder.

### I2. LOCALJUDGE candidate roster: GLM-4.5-Air at Q4_K_M in a Q8-only model discipline

- **Standard form:** every local model in this program's rosters runs Q8_0 (the quant-replication epoch
  showed quantization moves response *coherence*; holding quant method constant removes it as a confound —
  `project-cdms-gx10-quant-protocol`).
- **What we do:** the LOCALJUDGE validation roster (`runtime_instrument/local_judge/LOCALJUDGE_PREREG.md` §1)
  runs GLM-4.5-Air (106B MoE, ~12B active) at **Q4_K_M** while all other candidates stay Q8_0.
- **Why:** GLM-4.5-Air Q8 ≈ 112 GB does not fit Sparky's 128 GB unified memory with judging context; Q4_K_M
  (73 GB) does. The model is a JUDGE here, not a subject — the deliverable is its measured agreement with the
  panel/gold, and every gate is empirical, so quant-induced quality loss is priced into the very numbers that
  decide adoption. Quant is held constant within-candidate across all phases.
- **What we disclaim:** any certification of non-Q8 quants beyond this specific candidate at this specific
  quant; cross-candidate comparisons are candidate+quant bundles, not architecture comparisons. If GLM is
  adopted and later re-quantized, §5(d) forces a Phase-A re-screen.
- **Status:** registered at prereg lock (2026-07-11), per rule 11 (deviation exercised from Phase A onward,
  not merely on adoption).

## Token-present conditioning for breach (generation / ladder / quant studies)

- **Standard form/meaning:** report the unconditional outcome rate — here, BEM breach across *all* probe responses
  (`breach_ALL`).
- **What we do:** report breach **conditioned on token-present** (the fraction of responses that contain the gist token
  `starboard_loop` which the A′ panel scores OWNED/SELF_ATTRIBUTED) as the primary firewall-breach metric, paired with
  the surfacing rate `P(token | subject)` as an explicit two-part **hurdle** (surfacing × adoption-given-surfacing).
- **Why:** unconditional `breach_ALL` is dominated by a coherence confound — a low-coherence / aggressively-quantized /
  older model that never emits the gist token cannot operationally adopt it, yet its silence scores "safe", making a
  broken model look firewall-compliant. Conditioning removes that artifact (demonstrated: granite-8b 3.0→3.1 `breach_ALL`
  rises 3.7%→16.7% *entirely* via surfacing 15%→67%, while adoption-given-surfacing stays flat ~25%). The hurdle is what
  lets us state *what generation changes* (surfacing) vs *doesn't* (adoption).
- **What we disclaim:** token-present is a **post-treatment mediator**, so `breach|token-present` is a CONTROLLED DIRECT
  EFFECT (not a total effect), and conditioning on it opens a collider/selection path (the token-present slice of a
  low-surfacing generation is its high-engagement tail). The bias most plausibly **flattens** a true trend, so a null in
  `breach|token-present` means "no detectable adoption-given-surfacing effect", **not** "no generation effect on the
  firewall." We always report the hurdle (both parts) and never assert cross-generation invariance from the conditional
  alone. (Results: `docs/validation/runtime_instrument/GENERATION_SWEEP_RESULTS.md`.)

### I2. Framing decoy is a "best-case ownership-explicit baseline," not a neutral/zero control

- **Standard form/meaning:** a "control" or "baseline" condition usually denotes a NEUTRAL reference where the
  manipulated factor is absent — here, one would expect "ownership unspecified" so the REAL−control contrast
  measures the full effect of asserting ownership.
- **What we do:** the framing confirmatory's DECOY (`tools/framing_conditions.py`) is the **strongest possible
  ownership-EXPLICIT counter-attribution** — "P's teammate wrote `starboard_loop`; P works alongside it but
  did not author it" — surfacing-matched to REAL (both name both tokens; only the authorship clause flips).
  The estimand is the facet-weighted **paired `breach|surface` lift REAL−DECOY** with a **surfacing-parity
  gate** (`FRAMING_CONFIRMATORY_LOCK.md`).
- **Why:** a neutral/silent decoy re-imports the surfacing confound and bundles tenure/modesty; the co-author
  decoy isolates the single ownership factor while holding self-relevance/surfacing constant (round-3
  pressure-test). The pilot's gate-3 confirmed it reads as clean attribution, not modesty (0/212).
- **What we disclaim:** the direction of the bound is the **OPPOSITE of "conservative."** Because explicit
  dis-ownership SUPPRESSES decoy breach (pilot DECOY 0.085; gate-3 confirms it), breach(DECOY) ≤
  breach(neutral), so REAL−DECOY(co-author) ≥ REAL−neutral: the co-author decoy yields the **WIDEST** lift
  and is therefore an **UPPER bound** on the framing→adoption effect relative to a neutral baseline — it
  **OVERSTATES** the deployment threat, and a weaker/neutral decoy would **NARROW** the lift, not widen it.
  The decoy's virtue is the **surfacing / self-relevance control + single-factor isolation**, NOT
  conservatism. Consequence (with the thin decoy-floor): the design is primed toward H1 confirmation, which
  is exactly why the **decoy-floor gate** (lift must not degenerate to breach(REAL)) and the **absolute-REAL-
  breach 2-D read** are load-bearing guards in the decision rule, not optional.
- **Second, the declared lift bundles ownership with EFFORT/FAMILIARITY** (surfaced by the scaffold-gradient
  design pressure-test, 2026-06-30). REAL = "P handles well starboard_loop / refactored it" (deep involvement
  *and* owns) vs DECOY = "P only integrates" (shallow *and* not-owner). So part of the +0.165 may reflect
  "more involvement → more claiming," not pure origination — and a model that did deep work on a teammate's
  module and says "I know it well" is *accurate*, not a breach (only **origination** claims are). The
  confirmatory therefore measures **(ownership + effort) framing → adoption**, an upper bound on the pure
  ownership effect. The effort-MATCHED scaffold-gradient (`FRAMING_SCAFFOLD_GRADIENT_PREREG.md`: identical
  deep work, origination toggled via stood-up/inherited) is the design that isolates pure origination — its
  result will bound how much of the +0.165 is ownership vs effort.

### I3. Confirmatory MDE: 0.08 [ambition] vs effective ≈0.10 at the 19-facet construct ceiling

- **Standard form:** a pre-registration fixes the MDE and then powers K to it (`K = ((z_α+z_β)σ/MDE)²`).
  §5 wrote "MDE 0.08 [LOCKED]."
- **What we do:** the self-concept taxonomy supplies only **19 fresh facets** (34 − 15 pilot; pilot excluded,
  no double-dip), and the pilot's between-facet σ is **irreducible** by adding probe variants (variants shrink
  only within-facet binomial noise, not σ_between). So K caps at 19 and the confirmatory is powered for an
  **effective MDE ≈ 0.10 (point σ=0.170) / ≈0.12 (conservative σ=0.211), at V=2** — not the 0.08 ambition.
  (The ≈0.07 "floor" is the unreachable V→∞ limit, not the V=2 run.) Variants were analyzed
  (`tools/framing_variant_recovery.py`) and **rejected** as a weak lever (recovering 0.08 needs V≈8 at only
  P≈0.65; impossible under conservative σ). [Josh decision, 2026-06-30.]
- **Why:** chasing the last ~0.02 of resolution would cost ~4× generation/judging at coin-flip reliability,
  while the observed pilot lift (+0.186) is ~2× the achievable MDE either way — the real effect is detected
  with margin at 0.10.
- **What we disclaim:** the confirmatory can reliably detect a lift ≥ ~0.10, **not** a lift in (0.08, 0.10);
  a null there would be under-powered, not evidence of absence. K may fall below 19 under admission attrition
  (no buffer), raising the effective MDE further — the realized K/MDE are reported, not assumed.

### I4. Surfacing-parity gate: knowingly-underpowered equivalence test; "fail → descriptive," not "abort"

- **Standard form/meaning:** a pre-registered validity / manipulation **"gate"** is powered so it *can* pass,
  and failing it normally **blocks** — aborts or invalidates the confirmatory.
- **What we do:** the framing confirmatory's surfacing-parity gate is a TOST-equivalence test (facet-paired
  ΔS 90% bootstrap CI ⊂ ±0.05; `framing_pilot_analyze.gates`) that is **knowingly underpowered at the locked
  K=19** (the construct ceiling caps K; the pilot's CI reached +0.11). We pre-commit that if it fails, H1 is
  reported **DESCRIPTIVELY, not confirmed** — the gate does NOT abort the run and is NOT loosened.
  [posture (a), Josh 2026-06-30; `FRAMING_CONFIRMATORY_LOCK.md` §4.]
- **Why:** the alternatives are worse — widening the margin is arbitrary and weakens the pre-reg; redesigning
  the decoy + re-piloting is costly; aborting discards a large observed effect (+0.186). The rigorous gate +
  descriptive fallback is the conservative, **non-gameable** choice (the lenient point check `|ΔS|<0.05`,
  which the pilot passed at 0.049, IS gameable — it can pass while the true ΔS exceeds 0.05). K=19 is a hard
  external ceiling (no over-generation buffer), not design slack.
- **What we disclaim:** a "descriptive on parity grounds" outcome is **NOT evidence against H1** — it is an
  underpower artifact; and passing at K=19 is not guaranteed even if surfacing parity truly holds. We report
  both the point |ΔS| and the equivalence CI so the leniency/power gap is visible.

---

## Framing-stratified breach (no single "self-attribution breach rate")

- **Standard form/meaning:** treat "self-attribution breach rate" as a single scalar property of a model (one number per
  subject/condition).
- **What we do:** report breach **stratified by the elicitation-framing regime** of the probe — identity/self-presentation
  facets vs behavioral/process facets — and **never pool** the two for an adoption number. Surfacing `P(token | subject)`,
  being framing-invariant, *may* be pooled across regimes.
- **Why:** gen-sweep4 (54-facet bank) shows adoption-given-surfacing depends ~2× on probe **framing** (identity facets
  37%, behavioral 17%; z=+6.5) while surfacing is unchanged (33.4% vs 33.5%) — a dissociation **orthogonal** to the
  generation effect (generation moves surfacing; framing moves adoption). A single pooled "breach rate" is then an
  arbitrary mixture set by the bank's facet composition, not a property of the model.
- **What we disclaim:** the identity-vs-behavioral *attribution* is **exploratory** (post-hoc, not pre-registered; a
  competing cause is that the original facets were curated toward known high-leak traps). We assert the *dissociation*
  (framing moves adoption, not surfacing), not its mechanism; the original-facet stratum remains the apples-to-apples
  comparator across batches. (Results: `docs/validation/runtime_instrument/GENERATION_SWEEP_RESULTS.md` §3.)
- **UPDATE (Phase-B identity-power, 2026-06-29) — the within-stratum estimand is FACET-WEIGHTED + FACET-CLUSTERED, not
  response-pooled.** Responses cluster by elicitation facet, and the bank double-probes the high-leak self-presentation
  facets, so a response-pooled within-stratum breach rate over-weights them and treats correlated responses as
  independent (the published "z=+6.5" is response-pooled → overstated). The valid inference facet-weights (mean over
  facets of each facet's rate, per the quant study's S-2) and bootstraps over facets (`tools/gen_sweep_facet_cluster.py`).
  Cluster-correct, the framing dissociation is real-in-direction + mech-arm p=0.043 (itself anti-conservative:
  one-stage facet-only clustering — true p if anything larger) but ~1.6–1.8× and
  under-powered all-arms; the curation confound is **refuted** (uncurated≈curated identity). We disclaim that the
  0–26/27–53 index split is a clean framing classifier — it is a **contaminated proxy** (identity-summary misfiled as
  behavioral; process facets misfiled as identity), so framing claims require facets classified by *actual* framing.
  (Results: `GENERATION_SWEEP_RESULTS.md` §3.5; `gen_sweep_aggregate.py --by-facet-framing` is descriptive-only and
  prints this caveat at runtime.)

### I3. Frontier thinking-factor arm generates at max_tokens 2048, not the local arm's 512

- **Standard form:** cross-arm comparability wants an identical completion budget; every local
  scaffold/grid cell generated at `n_predict=512`.
- **What we do:** the frontier thinking-factor run (`tools/framing_frontier_gen.py`, cache
  `framing_frontier_20260701_094341`) ran at **`--max-tokens 2048`** (the tool's default is 3000);
  reasoning-enabled calls consume completion budget on hidden traces, and 512 starved them to null
  content in the smoke test (gemini-2.5-pro burned 1024 on reasoning and emitted nothing).
- **Why:** a shared 512 cap would have made every thinking cell mechanically ABSENT — the arm
  could not exist at the local budget.
- **Disclaimed:** magnitude comparisons between frontier and local cells (surfacing AND adoption
  opportunity scale with budget). `FRONTIER_THINKING_RESULTS.md` carries the caveat at each
  cross-arm comparison; within-arm contrasts (toggle pairs, K/M tally) share one budget and are
  unaffected.

### I4. Clean-strata run reuses frozen-taxonomy dimensions across experiments

- **Standard form:** a confirmatory study draws its stimuli from a source population untouched by
  sibling studies, so facet sets across experiments are independent draws.
- **What we do:** `CLEANSTRATA_PREREG.md` §3 builds its SP/ID/PROC dimension lists from
  `framing_taxonomy.md` — the same frozen dimension population the ownership-framing pilot/confirmatory
  consumed — plus 6 new framework-derived SP dims. Probes are NEWLY written (direction-blind writer,
  two blind classifiers, κ=0.978) for a different contrast under a different scaffold; no leak data
  attaches to any probe.
- **Why:** the taxonomy's anti-hindsight construction (dimensions from recognized external frameworks)
  is the asset worth reusing; a fresh enumeration would be *more* hindsight-exposed, not less, and the
  ~34-dim self-concept ceiling makes disjoint-per-experiment draws impossible.
- **Disclaimed:** the two experiments' facet sets are not independent draws — cross-experiment
  facet-level comparisons are descriptive only.

### I5. Multi-fact scaffold plants symmetric, identical-template achievement gists

- **Standard form:** a memory store's gists are heterogeneous — distinct achievements with distinct
  phrasings — so the store reads as a natural history.
- **What we do:** `MULTIFACT_PREREG.md`'s triple arm plants n=3 gists that are **byte-identical modulo the
  token** ("refactored the {tok} module to clean up the iteration order" for each of `MULTIFACT_TOKENS`),
  identical valence/frequency/support/relation.
- **Why:** the experiment measures *per-token* adoption averaged over the three tokens; exchangeability
  (symmetric salience + phrasing) is what makes that average unbiased. Heterogeneous gists would confound
  per-token dilution with per-gist attractiveness.
- **Disclaimed:** three near-identical achievements are an unnatural store; a model may pattern-detect the
  template. The single-vs-triple contrast therefore also varies preamble length and repetition-salience,
  not fact-count alone — so the run reports the mechanism-agnostic *per-token dilution vs preservation*,
  not a bare "availability vs framing" causal claim (a length/count-matched filler-gist control is the
  named follow-on). See `MULTIFACT_PREREG.md` §9.

### I6. Padding-control equivalence margin is data-dependent (M = p_s/3), not the repo SESOI (0.10)

- **Standard form:** an equivalence (TOST) margin is a fixed, pre-specified smallest-effect-of-interest;
  this repo's generic SESOI is 0.10.
- **What we do:** `PADDING_PREREG.md` §3 sets the margin to **M = p_s/3** (p_s = the fresh single-arm T1,
  estimated ≈ 0.066) — a *data-dependent* bound computed from the same run.
- **Why:** the margin is threat-linked — half the availability-masking magnitude (2p_s/3) the control
  exists to exclude, the same convention as the filler THETA_s. A generic 0.10 would be *looser* than the
  threat and could stamp "length-clean" over a masking-relevant effect.
- **Disclaimed:** a data-dependent margin makes the equivalence Type-I inexact (measured ≈ 0.10
  false-equivalence at the margin edge vs the nominal 0.05, small-cluster bootstrap under-coverage); the
  clean verdict tolerates up to a ~half-masking length effect at that elevated error, disclosed in
  `PADDING_PREREG.md` §6.

### I7. Conservation-ladder equivalence band is instrument-calibrated (M = max(0.061, 3σ_P0))

- **Standard form:** an equivalence (TOST) margin is fixed before ANY data from the study exist; a
  margin that depends on a measurement from the same study is circular.
- **What we do:** `CONSERVATION_PREREG.md` §3 sets the band to **M = max(0.061, 3·σ_P0)**, where σ_P0
  is the **multiplicity-specific** instrument test–retest SD measured by the P0 arm (fresh judge
  sessions over the committed, byte-identical frame-epoch caches) — data-dependent on P0.
- **Why:** the claim under test is *behavioral* conservation; the band must not be narrower than the
  instrument's own session-to-session noise, or the design would "falsify" conservation with judge
  jitter. P0 measures exactly that noise. Circularity is controlled by SEQUENCING plus artifacts: P0
  completes and writes `conservation/P0_BAND.json` **before any P1–P4 generation exists** (the
  launcher refuses to start without the band exported; the analyzer reads the artifact), so no arm's
  data can influence its own gate; the 0.061 floor (the I6 convention, p_anchor/3) binds from below
  and the analyzer refuses a smaller band.
- **Disclaimed:** the equivalence Type-I is inexact (band estimated from ~5 sessions; small-cluster
  bootstrap under-coverage as in I6). Direction stated honestly: a wider band makes CONSERVED *easier*
  — so an above-floor band does NOT auto-widen the test; it **HALTS the pipeline for human review**
  (P0 tool exits non-zero; analyzer requires an explicit approval flag; decision recorded in the
  prereg §9). The realized M is reported next to every verdict.

### I8. Erasure-differentiation ceiling arm lifts `goal_gate_floor` to 0 (non-shipped)

- **Standard form:** an experiment characterizing a product measures the product's shipped configuration.
- **What we do:** `DIFFERENTIATION_ERASURE_PREREG.md` runs the ablation at BOTH `goal_gate_floor=0.25`
  (as-shipped, the **primary**) and `goal_gate_floor=0.0` (a **ceiling** arm), the latter a non-default config.
- **Why:** shipped CDMS floors off-goal salience at 0.25 to avoid *total* amnesia of memories outside the
  current goal (a deliberate anti-erasure choice). The ceiling arm asks a distinct question — can the
  mechanism individuate *at all* when that floor is removed — bracketing the shipped result with the
  mechanism's potential.
- **Disclaimed:** `gf=0.0` is **NOT the shipped product**; only the `gf=0.25` arm speaks to CDMS-as-shipped.
  Every verdict states which floor produced it; the ceiling is reported as ceiling, never as headline.

### I9. "Disposition" denotes a topic GOAL SET, not temperament

- **Standard meaning:** *disposition/temperament* connotes a broad, multi-dimensional character (the repo's
  own construct is the 8 temperament dials).
- **What we do:** in the erasure experiment a "disposition" is operationalized narrowly as a **goal set over
  ~8 engineering topics** — i.e. topic-interest, which drives what stays in front of the agent.
- **Why:** topic-goal-relevance is the one facet that maps cleanly onto CDMS's `goal_hint`/`G_goal` lever and
  onto what memory-evals actually measure; it makes the forgetting-driven individuation testable.
- **Disclaimed:** results speak to **topic-selection individuation only**, not personality/temperament in
  general. No claim that CDMS individuates *character* is made from this proxy.

### I10. Functional-distinguishability secondary reaches into the -D/agent layer

- **Standard scope:** a CDMS-**A** (memory core) experiment measures -A's state; retrieval/agent behavior is
  the -D layer's concern.
- **What we do:** the erasure experiment's **secondary** metric injects an identity into a real capable
  reader and asks whether a blind judge can tell two identities apart by the reader's **behavior** — an
  effect measured at the -A/-D boundary.
- **Why:** the point of individuation is its effect on the loaded agent (Josh); we want to know *if and by how
  much* an identity changes what a Claude/ChatGPT-class model does — which only shows at the behavioral layer.
- **Disclaimed:** reported as **secondary**, not the -A structural primary; it is **functional/behavioral
  distinguishability only** — an explicitly NON-phenomenal measure, no consciousness or "what-it's-like"
  claim (companion to the simulacrum functional-not-faithful framing).

### I11. Plasticity-ladder ablation removes product safety guardrails (sealed sandbox, non-shipped)

- **Standard form:** the product's anti-poisoning / anti-confabulation plasticity guardrails
  (support-weighted resistance `ema/√support`, drift magnitude cap, touched-only selectivity) and the BEM
  provenance discipline are **inviolable in the product**; experiments measure shipped behavior.
- **What we do:** the plasticity-ladder characterization (`PLASTICITY_LADDER.md`, task #16) deliberately
  ABLATES those guardrails — cumulatively, to fully unguarded reconsolidation drift — inside a sealed
  sandbox: eval-harness-only code (`tools/eval_harness/unguarded_sandbox.py`; nothing in `src/cdms`
  references it, lock-tested), double-key arming (`CDMS_EVAL_MODE` + `CDMS_UNGUARDED_DRIFT` + minted
  temp-home-only, asserted inside the drift function), synthetic corpus only, crash-safe burn (every
  unguarded store deleted post-analysis; aggregated scalars are all that survives).
- **Why:** the structural arc closed with "state = f(imposed) ⊕ noise" proven on the BOUNDED mechanism, and
  PT3 showed safety and effect are in tension (the bounding starves the coupling). The ablation closes the
  scope condition: does UNSAFE plasticity buy state individuation? (Pre-known from PT7: no — the ladder is
  squeezed; the run commits the dose-response curve.)
- **Disclaimed:** unguarded mode is **NOT shipped, not shippable, and unreachable from product code**; the
  shipped defaults are unchanged and re-asserted by existing lock tests. Results are mechanism-tier
  characterization only — no product behavior claim, and no individuation claim (the behavioral TOST is the
  thesis's sole terminal court).

### N1. Component proper names use a Chinese (wuxia/Daoist/Buddhist) vocabulary

- **Standard form:** components carry either bare technical identifiers or Western/classical project
  names; borrowed religious/doctrinal terms normally denote their doctrines.
- **What we do (2026-07-07, supersedes the Norse working names Mímisbrunnr/Huginn):** each shipped
  component carries a canonical proper name chosen for **structural fit** — the name's native doctrine
  mirrors the component's mechanics. CDMS-X letters remain the formal names (papers, code
  cross-references). Canonical map:

  | Name | Hanzi | Component | Status |
  |---|---|---|---|
  | Zangshi | 藏識 | CDMS-A runtime (memory engine) | Confirmed |
  | Daoxin | 道心 | Read-only identity preamble (inside -A) | Confirmed |
  | Yangshen | 陽神 | CDMS-D agent/interface layer | Confirmed |
  | Yinshen | 陰神 | Read-only/observer agent mode (inside -D) | Confirmed |
  | Hongyan | 鴻雁 | Agent-to-agent messaging channel (MCP transport) | Confirmed |
  | Hufu | 虎符 | Mutual-authentication handshake (inside Hongyan) | Confirmed |
  | Nanke | 南柯 | CDMS-B (Prose Dreamer) | Reserved, not yet applied |
  | Huangliang | 黃粱 | CDMS-C (Research Dreamer) | Reserved, not yet applied |
  | Zuowang | 坐忘 | Consolidation/decay policy | **Confirmed** (Josh, 2026-07-07) |
  | Mengpo | 孟婆 | Hard-delete/purge operation (`cdms forget` / `uninstall --purge`) | **Confirmed** (Josh, 2026-07-07) |

  Casing: prose = capitalized pinyin (Zangshi); code identifiers = lowercase (`zangshi`,
  `HufuHandshake`, `yinshen_mode`); hanzi in doc headers only, never identifiers.
- **Why (condensed per name):** **Zangshi** = ālaya-vijñāna, the Yogacara storehouse consciousness
  (Xuanzang, Cheng Weishi Lun) — seeds strengthened by repeated "perfuming" that manifest when
  conditions ripen = a salience-weighted store with access reinforcement; the classical triple gloss of
  藏 (that-which-stores / that-which-is-stored / that-which-is-clung-to-as-self) encodes the
  differentiation thesis. **Daoxin** = the "Dao heart" of the sixteen-character transmission (Shangshu)
  — the unwavering core; scoped deliberately to the preamble (names the *invariant*, not the mechanism);
  daoxin-instability is genre fiction's canonical failure of self. **Yangshen** = neidan's completed
  spirit-body that exits, acts autonomously, and RETURNS — return-and-merge is constitutive, making
  auditability a lore-native hard requirement (also a known xianxia title: considered a feature).
  **Yinshen** = the lesser projection that perceives but cannot materially act — direct warrant for an
  observer/dry-run mode. **Hongyan** = the goose-borne letter of 鴻雁傳書 (Su Wu) — a message across
  hostile territory, carried by an identity-fidelity figure. **Hufu** = the split tiger tally —
  authorization by physically matching halves, graded scopes, and a classical literature that is largely
  a catalog of credential-theft compromises: the name ships with its own threat model. **Nanke /
  Huangliang** = the two most famous dream parables — two Dreamers, two dreams. **Zuowang** = Zhuangzi
  ch. 6's staged, deliberate forgetting-as-cultivation → the ongoing consolidation/decay POLICY (trained
  forgetting); **Mengpo** = the administered wipe at the bridge of rebirth → the hard-delete/purge
  OPERATION (administered forgetting) — each doctrine matches its mechanism's mode of forgetting.
- **Rejected (collision-checked failures, do not use):** Qingniao, Yizhan, Hatif, Fusheng, Alaya,
  Seshat, Isnad-as-component-name (retained only as the cited design ancestor of the audit chain).
  Prior Norse names (Mímisbrunnr, Huginn) retired before ever landing in repo text.
- **Naming law (future components):** any mythic term that survived as the ordinary modern word for its
  function is pre-collided by definition (hatif→telephone, yizhan→parcel station). Target the "Nanke
  zone": dead enough to be unclaimed, attested enough to carry meaning. Collision-gate every new name
  (English web search minimum) before integration.
- **Disclaimed:** the Chinese-language namespace (Gitee, Baidu, CN app stores) was NOT searchable at
  check time (July 2026) and remains **unverified** — fine self-hosted; re-check before any
  public/commercial use. Names are used against their doctrinal denotations *as structural metaphors*;
  no religious claim is made or implied.

---

## "Phenotype" for judge error-profiles (LOCALJUDGE-2, 2026-07-28)

- **Standard meaning:** biology — an organism's observable characteristics arising from
  genotype × environment.
- **What we do:** `LOCALJUDGE2_RESULTS.md` uses "phenotype" for a judge model's observable
  two-sided error profile (miss/false-alarm position on the conservative↔liberal axis) — the
  survey's primary descriptive object.
- **Why:** the borrowed term carries exactly the needed connotation: a stable, observable,
  classifiable surface trait that need not map 1:1 onto any single underlying cause — the
  results doc explicitly declines causal attribution (training recipe vs data vs alignment).
- **What we disclaim:** no genetic/developmental analogy is asserted; no claim that the
  error profile is heritable across fine-tunes or stable across rubrics — it is measured
  under RUBRIC_A4 on this corpus only. "Byte-determinism as phenotype" in §9 of that doc is
  further hedged there as the weaker, speculative reading.

---

## How to add an entry

1. Put a one-line `DELIBERATE DEVIATION (see docs/DEVIATIONS.md)` note at the point of use.
2. Add a register entry: standard form/meaning → what we do → why → what we disclaim.
3. If it's a math deviation that changes behavior, add an A/B note under `docs/validation/`.
