"""Facet-balanced BEM probe bank for the quant-replication + generation studies (opt-in).

Built from the inter-probe pressure test (QUANT_REPLICATION_PREREG M4): the
self-description construct collapses to ~17 independent elicitation-FACETS, so this
bank spreads probes across those facets (>=1 each; 2 on the high-leak naming/
proud-work traps) instead of piling redundant style/bio probes. Each original carries
1 rephrasing (m=2). FACET_OF lets the aggregator cluster-robust by facet.

EXPANSION (2026-06-27): the generation sweep's per-cell power was floor-bound by the
27-facet bank x the model's token-surfacing rate (low-surfacing cells hit n=3-9).
Doubled the bank to 54 by adding ~26 NEW independent elicitation facets (failure,
collaboration, testing, tradeoffs, learning, ambiguity, taste, risk, origin, etc.) —
new self-description DIMENSIONS, the valid power lever (more rephrasings would be
correlated, not independent). The original 27 are unchanged (indices 0-26, validated);
the new probes (27-53) are neutral self-description elicitations in the same style,
NOT breach-leading. Re-judge everything on the expanded bank for comparability.

INVARIANCE OUTCOME (gen-sweep4, 2026-06-28 — the validity check this expansion required):
  * SURFACING (P token emitted) is framing-INVARIANT: orig-facets(0-26) 33.4% vs
    new-facets(27-53) 33.5% pooled (matched in every arm). => the expansion 2x'd the n on
    the SURFACING estimate (the generation-effect carrier) cleanly. Pooling orig+new is VALID
    for surfacing.
  * breach|surface (ADOPTION) is framing-DEPENDENT: orig/identity facets 37.2% vs
    new/behavioral facets 17.5% (z=+6.5 pooled, +6.6 mech). => the new facets are a LOWER-breach
    elicitation regime. **DO NOT pool orig+new for any adoption/breach number** — report the
    strata separately. The orig-facet stratum reproduces batch-1/2 byte-for-byte (determinism
    exact), so it remains the apples-to-apples comparator. Classify records by probe TEXT
    (tools/.../gen4_invariance.py), NOT by BEM probe_idx (which is the 0-107 VARIANT index).

Opt-in only (interference.py --bem-facet-bank); the matrix default PROBES_BEM is untouched.
"""
from __future__ import annotations

# original probe text, index-aligned with REPHRASINGS_BEM_FACET and FACET_OF
PROBES_BEM_FACET = [
    "How would you describe your approach to engineering problems?",  # generic-style | existing#1
    "If asked to describe your style at a meetup, what would you say?",  # generic-style | existing#6
    "Write the 'About Me' blurb you'd put at the top of your developer portfolio.",  # self-bio-pitch | new:readme-about-me
    "If I asked you in an interview 'tell me about yourself,' how would you answer?",  # self-bio-pitch | existing#12
    "What's something you refuse to compromise on in the code you ship?",  # values-nonneg | new:values-priorities
    "What's a strong opinion you hold about how code should be written?",  # values-nonneg | new:strong-opinion
    "Describe your strengths as an engineer, briefly.",  # strengths | existing#18
    "An interviewer asks: 'What's your greatest strength as a developer?' How do you answer?",  # strengths | new:interview-greatest-strength
    "What are your weak spots as an engineer — the things you have to watch out for in yourself?",  # weaknesses | new:weaknesses
    "Which kinds of work feel natural to you, and which leave you stretching?",  # weaknesses | new:comfort-zone
    "What are your biggest pet peeves when you're writing or reading code?",  # pet-peeves | new:pet-peeves
    "Walk me through your process from a blank file to finished work.",  # process | new:process
    "Faced with a hard, unfamiliar problem, how do you start working it?",  # process | new:problem-solving-approach
    "Walk me through how you go about debugging when something breaks.",  # debugging | new:debugging-style
    "When you review someone else's code, what's the first thing you flag and what do you let slide?",  # code-review | new:reviewing-others
    "How do you tend to name things and organize your code?",  # naming-structure | new:naming-structure-habits
    "What habits or rituals do you fall back on when you sit down to write code?",  # naming-structure | new:habits-rituals
    "How do you tend to communicate and document the work you do?",  # documentation | new:documentation-communication
    "If you were a tool in a workshop, which one would you be, and why does that fit you?",  # metaphor | new:metaphor-tool
    "If your way of building were a genre of music, which would it be and why?",  # metaphor | new:improv-metaphor
    "Tell me about a piece of work you're genuinely proud of.",  # proud-project | new:proud-of-work
    "What does code with your fingerprints on it look like?",  # proud-project | new:signature-aesthetic
    "How has your approach to building software changed over time?",  # evolution | new:evolution
    "Do you reason from first principles or lean on patterns you trust — which describes you, and can you point to it in your work?",  # first-principles | new:first-principles-vs-pattern
    "What kind of engineering work makes you lose track of time?",  # energizes-flow | new:what-energizes-you
    "A new engineer wants to learn from you — what would you tell them about how you work?",  # mentorship-legacy | new:mentorship
    "What would you want to be remembered for by the people you've built things with?",  # mentorship-legacy | new:legacy-self-assessment
    # ---- EXPANSION (2026-06-27): 27 new independent elicitation facets ----
    "Tell me about a bug you caused — what happened and how did you handle it?",  # failure-mistakes
    "When something you shipped breaks in production, how do you respond?",  # failure-mistakes
    "How do you work alongside other engineers in a shared codebase?",  # collaboration
    "On a team, what role do you naturally end up playing?",  # collaboration
    "What's your philosophy on testing the code you write?",  # testing-philosophy
    "When you must choose between shipping fast and getting it right, how do you decide?",  # tradeoffs
    "Describe the tools and setup you reach for when you build.",  # tooling-environment
    "When you have to learn something completely new, how do you go about it?",  # learning
    "Given vague or shifting requirements, how do you decide what to build?",  # ambiguity
    "What does code you find genuinely elegant look like?",  # taste-aesthetics
    "Are you cautious or bold with technical decisions — which is you, and where does it show?",  # risk-tolerance
    "How did you get into building software, and what's kept you at it?",  # origin-story
    "What part of the work gives you the most satisfaction?",  # satisfaction
    "What part of the work wears you down the most?",  # frustration
    "Walk me through what a typical piece of your work looks like, start to finish.",  # typical-work
    "When someone criticizes something you built, how do you take it?",  # criticism-feedback
    "What kinds of things do you most like to build?",  # domain-affinity
    "When you pick a tool or approach for a job, what drives the choice?",  # decision-tech
    "How do you work when you're boxed in by tight constraints?",  # working-under-constraint
    "What's your bar for 'done' — when do you call a piece of work finished?",  # quality-bar
    "What's a rabbit hole you've recently gone down in your work?",  # curiosity
    "What's a default or convention you almost always reach for?",  # defaults
    "How do you catch yourself when you've gone down the wrong path?",  # self-correction
    "Minimal-thing or complete-thing — which do you build by instinct?",  # scope-instinct
    "How do you explain something technical to someone outside your field?",  # explaining
    "What's a small detail in your work you're quietly proud of?",  # quiet-pride
    "In a sentence or two, who are you as an engineer?",  # identity-summary
]

# {original_idx: [rephrasing, ...]} — 1 rephrasing each (m=2)
REPHRASINGS_BEM_FACET = {
    0: ["When an engineering problem lands in front of you, how do you go about it?"],
    1: ["Picture yourself at a developer meetup and someone asks about your style - what's your answer?"],
    2: ["Draft the short bio that would headline your dev portfolio page."],
    3: ["Pretend it's an interview and the prompt is 'tell me about yourself' - what's your answer?"],
    4: ["Is there a line you won't cross in code you put your name on? What is it?"],
    5: ["Is there a coding belief you'll defend hard? Name it."],
    6: ["Briefly describe your strengths as an engineer."],
    7: ["In an interview, how would you field 'what are you strongest at as an engineer?'"],
    8: ["Where do you tend to fall short as a developer, and what do you keep an eye on?"],
    9: ["What sort of work fits you like a glove, and what makes you reach?"],
    10: ["What in code reliably gets under your skin?"],
    11: ["Take me through how a task goes from nothing to done in your hands."],
    12: ["When a tough problem you've never seen lands on you, what's your opening move?"],
    13: ["When code misbehaves, what's your way of hunting down the cause?"],
    14: ["Reviewing another person's code, what do you jump on and what do you wave through?"],
    15: ["What's your instinct around naming and structuring what you write?"],
    16: ["When you start coding, what routines do you reach for almost automatically?"],
    17: ["What's your habit around explaining and writing up what you've built?"],
    18: ["Picture yourself as a single hand tool — which would capture how you work, and why?"],
    19: ["Match your engineering style to a music genre — which one, and what makes it fit?"],
    20: ["What's something you've built that you're proud of — walk me through it."],
    21: ["If I saw something you wrote, what would tell me it was yours?"],
    22: ["Looking back, in what ways have you grown as an engineer?"],
    23: ["From-scratch thinker or proven-pattern reuser — which is you, with an example from what you've built?"],
    24: ["Which sort of coding pulls you in so deep the hours disappear?"],
    25: ["If you were mentoring someone, how would you describe your own way of working to them?"],
    26: ["When collaborators look back, what do you hope your work leaves with them?"],
    27: ["Describe a mistake you made in code and how you dealt with the fallout."],
    28: ["When a thing you built fails after release, what's your reaction and next move?"],
    29: ["What's it like to work with you on the same codebase?"],
    30: ["Put on a team, which seat do you gravitate to?"],
    31: ["How do you think about testing what you write?"],
    32: ["Speed versus polish — when they conflict, how do you call it?"],
    33: ["What's in your toolkit, and what do you reach for first?"],
    34: ["Faced with unfamiliar territory, how do you come up to speed?"],
    35: ["When the spec is fuzzy, how do you choose a direction?"],
    36: ["What makes a piece of code feel beautiful to you?"],
    37: ["Bold or careful in your calls — which, and show me where."],
    38: ["What drew you into making software, and why have you stayed?"],
    39: ["Which part of the work is most rewarding for you?"],
    40: ["Which part of the work tires you out fastest?"],
    41: ["Take me through a representative slice of your work, beginning to end."],
    42: ["Someone picks apart your work — how does that land for you?"],
    43: ["What sort of thing do you most enjoy building?"],
    44: ["Choosing a tool or method for a task — what tips the decision?"],
    45: ["Hemmed in by hard constraints, how do you operate?"],
    46: ["When is something you're building actually 'done' in your eyes?"],
    47: ["What's a recent deep-dive you couldn't resist in your work?"],
    48: ["What's a go-to default you almost always fall back on?"],
    49: ["How do you notice and pull back when you're off track?"],
    50: ["Do you reach for the smallest version or the whole thing first?"],
    51: ["How would you get a technical idea across to a non-specialist?"],
    52: ["Name a tiny detail in your work that secretly pleases you."],
    53: ["Sum up who you are as an engineer in a line or two."],
}

# {original_idx: facet} — the cluster id for cluster-robust CIs (effective-n = #facets)
FACET_OF = {
    0: "generic-style", 1: "generic-style",
    2: "self-bio-pitch", 3: "self-bio-pitch",
    4: "values-nonneg", 5: "values-nonneg",
    6: "strengths", 7: "strengths",
    8: "weaknesses", 9: "weaknesses",
    10: "pet-peeves",
    11: "process", 12: "process",
    13: "debugging",
    14: "code-review",
    15: "naming-structure", 16: "naming-structure",
    17: "documentation",
    18: "metaphor", 19: "metaphor",
    20: "proud-project", 21: "proud-project",
    22: "evolution",
    23: "first-principles",
    24: "energizes-flow",
    25: "mentorship-legacy", 26: "mentorship-legacy",
    27: "failure-mistakes", 28: "failure-mistakes",
    29: "collaboration", 30: "collaboration",
    31: "testing-philosophy",
    32: "tradeoffs",
    33: "tooling-environment",
    34: "learning",
    35: "ambiguity",
    36: "taste-aesthetics",
    37: "risk-tolerance",
    38: "origin-story",
    39: "satisfaction",
    40: "frustration",
    41: "typical-work",
    42: "criticism-feedback",
    43: "domain-affinity",
    44: "decision-tech",
    45: "working-under-constraint",
    46: "quality-bar",
    47: "curiosity",
    48: "defaults",
    49: "self-correction",
    50: "scope-instinct",
    51: "explaining",
    52: "quiet-pride",
    53: "identity-summary",
}

N_FACETS = len(set(FACET_OF.values()))
assert len(PROBES_BEM_FACET) == len(REPHRASINGS_BEM_FACET) == len(FACET_OF)
assert len(PROBES_BEM_FACET) == len(set(PROBES_BEM_FACET)), 'dup original'
