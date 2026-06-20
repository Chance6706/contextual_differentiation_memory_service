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

---

## How to add an entry

1. Put a one-line `DELIBERATE DEVIATION (see docs/DEVIATIONS.md)` note at the point of use.
2. Add a register entry: standard form/meaning → what we do → why → what we disclaim.
3. If it's a math deviation that changes behavior, add an A/B note under `docs/validation/`.
