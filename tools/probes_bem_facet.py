"""Facet-balanced BEM probe bank for the quant-replication study (opt-in).

Built from the inter-probe pressure test (QUANT_REPLICATION_PREREG M4): the
self-description construct collapses to ~17 independent elicitation-FACETS, so this
bank spreads 27 originals across those facets (>=1 each; 2 on the high-leak naming/
proud-work traps) instead of piling redundant style/bio probes. Each original carries
1 rephrasing (m=2). FACET_OF lets the aggregator cluster-robust by facet (effective-n ~17).

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
}

# {original_idx: facet} — the cluster id for cluster-robust CIs (effective-n = #facets)
FACET_OF = {
    0: "generic-style",
    1: "generic-style",
    2: "self-bio-pitch",
    3: "self-bio-pitch",
    4: "values-nonneg",
    5: "values-nonneg",
    6: "strengths",
    7: "strengths",
    8: "weaknesses",
    9: "weaknesses",
    10: "pet-peeves",
    11: "process",
    12: "process",
    13: "debugging",
    14: "code-review",
    15: "naming-structure",
    16: "naming-structure",
    17: "documentation",
    18: "metaphor",
    19: "metaphor",
    20: "proud-project",
    21: "proud-project",
    22: "evolution",
    23: "first-principles",
    24: "energizes-flow",
    25: "mentorship-legacy",
    26: "mentorship-legacy",
}

N_FACETS = len(set(FACET_OF.values()))
assert len(PROBES_BEM_FACET) == len(REPHRASINGS_BEM_FACET) == len(FACET_OF)
assert len(PROBES_BEM_FACET) == len(set(PROBES_BEM_FACET)), 'dup original'

