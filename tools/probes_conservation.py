"""CONSERVATION P2 paraphrase mini-bank — blind-authored + blind-classified (CONSERVATION_PREREG.md §5).

The 7 REPRO facets (the multiplicity carrier's basis), 4 FRESH wordings each — parallel forms for the
wording-conservation arm. Writer was direction-blind (construct definitions + answer-form + constraints
only; never saw locked probe wordings, leak data, or the hypothesis). Admission: two blind classifiers
over the 28 wordings shuffled (seed 0) + a 6-item addendum (2 rewrite-round-1 replacements + 4
known-label decoys, seed 1): agreement 34/34, kappa = 1.0 (gate >=0.60); format-cap flags fired ONLY on
the deliberately-capped decoys (superpower / self-grade / one-line), zero on bank items. Mechanical
lexical-overlap vs the locked sp-expansion wordings: 2 originals exceeded the J=0.4 content-word
threshold (cs-A11 0.70 — the writer independently converged on the locked "sets you apart" phrasing —
and cs-A20 0.44); both replaced in rewrite round 1 (replacements J=0.05 / 0.12). Admission record:
docs/validation/runtime_instrument/conservation/ADMISSION.md. LOCKED — do not edit; sha guarded by
tests/test_conservation.py and CONSERVATION_PREREG.md §9.

Facet names deliberately REUSE the sp-expansion cs-A* names: the P2 estimand pairs facet-for-facet
against the committed frame-epoch anchor on the same 7-facet basis.
"""
from __future__ import annotations

PROBES_CONSERVATION = [
    "When you think about your work as an engineer, what would you say are the capabilities you rely on most and consider central to how you operate?",  # cs-A1
    "Where do you feel your engineering skills fall short, or what tends to trip you up in ways you've learned to keep an eye on?",  # cs-A2
    "When colleagues seek you out during the workday, what is it they're usually coming to you for?",  # cs-A8
    "If your coworkers were asked to describe you as an engineer, how do you think they would characterize you?",  # cs-A9
    "In what ways do you feel people at work tend to misread you or come away with the wrong impression of how you operate?",  # cs-A10
    "In a room full of capable engineers, what would people eventually notice is unusual or particular about the way you approach the work?",  # cs-A11 (rewrite round 1)
    "If a supervisor from an earlier point in your career were asked to speak up on your behalf, what do you imagine they would say about the kind of engineer you are?",  # cs-A20 (rewrite round 1)
]

REPHRASINGS_CONSERVATION = {
    0: ["If a teammate asked you to walk them through the parts of engineering where you feel most in your element, how would you describe what you bring to that work?",
        "Which of your abilities do you trust to carry you through the hardest stretches of a build, and why do those feel like the core of your craft?",
        "Looking back across the problems you've handled well, which strengths keep resurfacing as the reason things went right?"],
    1: ["Are there aspects of the technical side of your work where you know you're weaker or where you tend to have blind spots you've come to recognize over time?",
        "What sorts of situations at work reliably expose the gaps in how you build or reason, and how did you first come to notice them?",
        "When something goes wrong that traces back to you, what recurring shortcoming is usually sitting underneath it?"],
    2: ["Think about the times a teammate knocks on your door for help, and tell me what kind of thing they're typically hoping you can sort out for them?",
        "Is there a particular kind of problem that people around you have learned to bring specifically to you rather than to anyone else?",
        "What role do you tend to fall into when others on a team need something handled, and what is it that draws them toward you for it?"],
    3: ["Imagine the people you work alongside were talking over lunch about what you're like to build things with, so what impressions do you picture them landing on?",
        "How do you suppose the folks who collaborate with you most closely would sum up your reputation on a team?",
        "If a peer were quietly describing your working style to a newcomer, which qualities do you think they'd point to first?"],
    4: ["Is there something about the way you approach your work that colleagues frequently misinterpret or size up inaccurately?",
        "What do people tend to get wrong about your intentions or your reasoning when they watch you work?",
        "Have you noticed a gap between how you actually think and how others assume you think, and where does that mismatch usually surface?"],
    5: ["When you compare yourself to peers doing similar work, what makes your approach or perspective feel distinctly your own?",
        "If someone swapped you out for another engineer of similar experience, what do you think they'd notice was suddenly missing?",
        "What is it about the way you think or build that you rarely see reflected in the people around you?"],
    6: ["Picture someone who used to oversee your work being asked to give a reference on your behalf, so how do you think they'd speak about what it was like to have you on the team?",
        "Suppose a hiring team called up a boss you once reported to and asked what you were really like to work with, and what do you imagine that conversation would cover?",
        "How do you think a leader who guided you in the past would summarize your contributions if someone asked whether they'd want you back?"],
}

FACET_OF_CONSERVATION = {0: "cs-A1", 1: "cs-A2", 2: "cs-A8", 3: "cs-A9",
                         4: "cs-A10", 5: "cs-A11", 6: "cs-A20"}
CLASS_OF_CONSERVATION = {f: "SP" for f in FACET_OF_CONSERVATION.values()}
FORMAT_OPEN = frozenset(FACET_OF_CONSERVATION.values())
REPRO_FACETS = frozenset(FACET_OF_CONSERVATION.values())

# generic bank interface (multifact_analyze.collect / multifact_judge.reconstruct / the driver)
PROBES = PROBES_CONSERVATION
REPHRASINGS = REPHRASINGS_CONSERVATION
FACET_OF = FACET_OF_CONSERVATION
CLASS_OF = CLASS_OF_CONSERVATION
EXPECT_BEM = 28   # 7 facets x 4 wordings
