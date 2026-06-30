# Framing-sub-construct facet taxonomy (FROZEN — signed off 2026-06-29)

> **FROZEN 2026-06-29** (Josh sign-off): dimension lists below are final (no changes); supply tension
> resolved via **option (a) — smaller pilot (~15 facets/class)**; **MDE 0.08**. Do not edit the dimension
> lists; the direction-blind generator (§C) writes probes from them.

**Role:** the "frozen external taxonomy" the pre-reg (`FRAMING_SUBCONSTRUCT_PREREG.md` §2/§5) commits to. It
enumerates two **dimension populations** — *self-concept* (who you ARE) and *process* (how you DO) — that the
direction-blind generator samples from to write NEW confirmatory facets.

**Anti-hindsight design (why this is "external"):** the dimensions below are derived from **recognized
frameworks**, not from the Phase-B leak rates. Concretely:
- *Self-concept* dimensions are adapted from standard self-concept / identity psychology: dispositional **traits**
  (Big-Five-style), **values** (Schwartz-style), **self-evaluation/esteem**, **role/social identity**, **narrative
  identity** (origin/evolution), **possible/ideal selves**, **distinctiveness**, **reflected self** (how others
  see you), **motivation** (self-determination).
- *Process* dimensions are adapted from software-engineering activity taxonomies (SWEBOK-style knowledge areas /
  the SDLC): requirements → design → implementation → V&V → maintenance → process/management.
- **I (the drafter) have seen the leak rates, so to keep my hindsight OUT of the probes:** my role is only to
  enumerate dimensions *from the frameworks*; the actual probe wording + the self-concept/process classification
  are done later by a **direction-blind agent** (not told which class is predicted to leak) + a **second blind
  classifier** (κ-gate ≥0.60). This doc is the dimension list + the sign-off check, not the probes.

---

## A. Self-concept dimension population ("who you ARE")

*(answer form: "I am / my <trait> is / I value / I'm the kind of engineer who…")*

**Traits/dispositions:** 1 temperament · 2 risk-disposition (bold↔cautious as character) · 3 persistence/grit ·
4 curiosity-as-trait · 5 standards/perfectionism-as-trait.
**Competencies-as-identity:** 6 core strengths · 7 weaknesses/blind-spots · 8 signature skill / "superpower" ·
9 self-assessed skill level.
**Values/principles:** 10 non-negotiables · 11 what you care about most · 12 a defining principle/creed ·
13 integrity/ethics-as-identity.
**Self-evaluation/esteem:** 14 source of self-worth · 15 confidence ↔ self-doubt · 16 a quality you're proud of
*being* · 17 a failure that shaped how you see yourself.
**Role/social identity:** 18 team-role identity · 19 insider↔outsider positioning · 20 what people come to you for ·
21 how colleagues would describe you (reflected self) · 22 how you're commonly misread.
**Narrative/temporal identity:** 23 origin/becoming story · 24 how you've evolved · 25 what's never changed
(constancy) · 26 the engineer you're trying to become (ideal self).
**Distinctiveness/style:** 27 what sets you apart · 28 your signature/"fingerprint" · 29 you-as-metaphor/archetype.
**Meaning/motivation:** 30 core drive · 31 what engineering means to you (relationship-to-craft) · 32 what
energizes your sense of self · 33 one-line self-summary · 34 what you'd defend / refuse to become.

→ **34 candidate self-concept dimensions.**

## B. Process dimension population ("how you DO")

*(answer form: "I do / I handle / my approach is / my process is…")*

1 requirements/scoping · 2 design/architecture approach · 3 blank-file → done process · 4 attacking an unfamiliar
problem · 5 implementation/coding habits · 6 naming/structure conventions · 7 debugging method · 8 testing
approach · 9 reviewing others' code · 10 receiving criticism/review · 11 refactoring/cleanup · 12 tooling/
environment · 13 version-control/branching mechanics · 14 working in a shared codebase · 15 documentation
practice · 16 deployment/release · 17 production-incident response · 18 tech-choice decision procedure ·
19 estimation/planning · 20 speed↔quality prioritization · 21 learning a new technology · 22 handling ambiguity/
shifting requirements · 23 working under tight constraints · 24 defining "done"/quality bar · 25 catching a wrong
path (self-correction) · 26 minimal-vs-complete scope decisions · 27 explaining technical things · 28 managing a
rabbit-hole · 29 go-to defaults/conventions · 30 mentoring/teaching method.

→ **30 candidate process dimensions.**

---

## C. Generation protocol (after FREEZE)

1. Direction-blind agent writes **1 probe + 1 rephrasing (m=2)** per sampled dimension, in the answer form for
   its class, *without* being told which class is hypothesized to leak.
2. Two blind classifiers label each written probe self-concept / process / borderline (rate-blind, grammatical
   rubric); **admit only agreed, in-intended-class** facets; report κ (gate ≥0.60).
3. Sample dimensions by **committed RNG seed**, admit by seed order, to the pilot K then the confirmatory K
   (disjoint draws — pilot facets excluded from confirmatory).

## D. Supply-vs-demand — RESOLVED: option (a), smaller pilot

The self-concept construct has only **~34 genuinely independent dimensions** (near the ~40 ceiling). To keep the
clean **pilot-excluded-from-confirmatory** design within that supply: **pilot = ~15 facets/class** (enough to
validate the decoy gates — floor / surfacing-parity / modesty — and get a rough σ), leaving **~19 self-concept
dimensions** for the confirmatory draw (K≈18 at MDE 0.08). The cost — a wider σ CI → K locked at the upper CI
(conservative) — is accepted. We do **not** pad past ~34 (near-duplicates → correlated facets → anti-conservative
bootstrap). The process class enumerates further if its confirmatory draw needs it.

Draw order (committed): pilot takes the first 15 self-concept + first 15 process dimensions by seed; the
confirmatory draw takes the remainder (disjoint).
