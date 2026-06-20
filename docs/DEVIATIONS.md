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
  forgetting curve and is **mortal** (~142d) unless it recurs.
- **Why:** the load-bearing anti-poisoning asymmetry. A single planted "catastrophe" (a poisoned file
  read once) must not mint a permanent authoritative guardrail; corroboration across sessions is the
  price of authority (`docs/redteam/LAYER3_PROVENANCE_DESIGN.md`).
- **Disclaimed:** the permanence "flashbulb" implies. The promise that "a real guardrail can't be
  quietly forgotten" holds for **recurring** catastrophes, not one-shot ones. Toggle:
  `scar_elevation_min_sessions = 1` (and a proposed `flashbulb_immediate_elevation`) restores it.

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
  negative tail because that is the safety-relevant one. A proposed `peak_floor_positives` toggle
  would add a positive floor for callers who want it.

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

## How to add an entry

1. Put a one-line `DELIBERATE DEVIATION (see docs/DEVIATIONS.md)` note at the point of use.
2. Add a register entry: standard form/meaning → what we do → why → what we disclaim.
3. If it's a math deviation that changes behavior, add an A/B note under `docs/validation/`.
