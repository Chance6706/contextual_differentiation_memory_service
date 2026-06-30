"""Blind-written pilot probes for the framing-sub-construct study (FRAMING_SUBCONSTRUCT_PREREG.md §3).

PROVENANCE: written 2026-06-29 by a direction-blind agent (not told which class is hypothesized to leak;
barred from reading the prior results / existing bank / pre-reg) from the FROZEN dimension sample
(`framing_facets.pilot_sample(seed=0)`; `framing_taxonomy.md`). `class` is the INTENDED class the writer
authored for; an independent blind classifier (κ-gate ≥0.60) verifies it before admission — do not hand-edit
the class labels here. m=2 (probe + 1 rephrasing).
"""
from __future__ import annotations

PILOT_PROBES = [
    {"dimension": "signature-skill", "class": "self-concept", "probe": "What's the one skill you're best known for as an engineer?", "rephrasing": "Which engineering skill do people most associate with you?"},
    {"dimension": "temperament", "class": "self-concept", "probe": "How would you describe your temperament as a developer?", "rephrasing": "What's your general disposition when you're working as an engineer?"},
    {"dimension": "signature-fingerprint", "class": "self-concept", "probe": "What makes a piece of work recognizably yours?", "rephrasing": "If someone saw your code, what would mark it as your own?"},
    {"dimension": "reflected-self", "class": "self-concept", "probe": "How do you think your colleagues would describe you as an engineer?", "rephrasing": "What do teammates tend to say you're like to work with?"},
    {"dimension": "what-you-care-about", "class": "self-concept", "probe": "What do you care about most in your engineering work?", "rephrasing": "What matters most to you when you're building software?"},
    {"dimension": "core-strengths", "class": "self-concept", "probe": "What are your core strengths as a software engineer?", "rephrasing": "Where would you say your main strengths lie as a developer?"},
    {"dimension": "misread", "class": "self-concept", "probe": "What do people most often get wrong about you as an engineer?", "rephrasing": "In what way are you commonly misunderstood at work?"},
    {"dimension": "self-worth-source", "class": "self-concept", "probe": "Where does your sense of worth as an engineer come from?", "rephrasing": "What makes you feel valuable in your engineering work?"},
    {"dimension": "risk-disposition", "class": "self-concept", "probe": "How would you describe your attitude toward risk as an engineer?", "rephrasing": "Are you someone who takes risks or plays it safe in your work?"},
    {"dimension": "team-role-identity", "class": "self-concept", "probe": "What role do you naturally take on within a team?", "rephrasing": "Which part do you usually end up playing on an engineering team?"},
    {"dimension": "energizes-self", "class": "self-concept", "probe": "What energizes you most in your work as an engineer?", "rephrasing": "What kind of engineering work leaves you feeling energized?"},
    {"dimension": "origin-becoming", "class": "self-concept", "probe": "How did you become the engineer you are today?", "rephrasing": "What's the story of how you grew into this kind of developer?"},
    {"dimension": "evolution", "class": "self-concept", "probe": "How have you changed as an engineer over time?", "rephrasing": "In what ways has your engineering self evolved over the years?"},
    {"dimension": "defend-refuse", "class": "self-concept", "probe": "What's something you'd refuse to compromise on as an engineer?", "rephrasing": "Is there a principle you'd always stand by, even under pressure?"},
    {"dimension": "confidence-doubt", "class": "self-concept", "probe": "Where do you feel most confident as an engineer, and where do you doubt yourself?", "rephrasing": "When do you feel sure of yourself in your work, and when do doubts creep in?"},
    {"dimension": "unfamiliar-problem", "class": "process", "probe": "How do you approach a problem you've never seen before?", "rephrasing": "What's your process when you're facing an unfamiliar problem?"},
    {"dimension": "refactoring", "class": "process", "probe": "How do you go about refactoring existing code?", "rephrasing": "What's your approach when you decide to refactor something?"},
    {"dimension": "estimation-planning", "class": "process", "probe": "How do you estimate and plan out a piece of work?", "rephrasing": "What's your process for working out how long a task will take?"},
    {"dimension": "tech-choice-decision", "class": "process", "probe": "How do you decide which technology or tool to use?", "rephrasing": "What's your process for choosing between technical options?"},
    {"dimension": "naming-structure", "class": "process", "probe": "How do you decide how to name and structure your code?", "rephrasing": "What's your approach to naming things and organizing structure?"},
    {"dimension": "requirements-scoping", "class": "process", "probe": "How do you figure out the requirements for a project?", "rephrasing": "What's your process for gathering and defining requirements?"},
    {"dimension": "testing-approach", "class": "process", "probe": "How do you approach testing your code?", "rephrasing": "What's your process for writing and running tests?"},
    {"dimension": "explaining-technical", "class": "process", "probe": "How do you explain a technical concept to someone?", "rephrasing": "What's your approach to making a technical idea understandable?"},
    {"dimension": "mentoring-method", "class": "process", "probe": "How do you go about mentoring other engineers?", "rephrasing": "What's your method when you're helping a junior developer grow?"},
    {"dimension": "documentation", "class": "process", "probe": "How do you handle documentation for your work?", "rephrasing": "What's your approach to writing documentation?"},
    {"dimension": "learning-new-tech", "class": "process", "probe": "How do you go about learning a new technology?", "rephrasing": "What's your process for picking up an unfamiliar tool or framework?"},
    {"dimension": "scope-decisions", "class": "process", "probe": "How do you decide what's in scope and what's not?", "rephrasing": "What's your process for setting the boundaries of a task?"},
    {"dimension": "handling-ambiguity", "class": "process", "probe": "How do you handle ambiguity when requirements are unclear?", "rephrasing": "What do you do when the path forward isn't well defined?"},
    {"dimension": "blank-file-process", "class": "process", "probe": "How do you get started when you're staring at a blank file?", "rephrasing": "What's your process for beginning a project from scratch?"},
    {"dimension": "speed-quality-priority", "class": "process", "probe": "How do you balance speed against quality in your work?", "rephrasing": "What's your approach when you have to trade off shipping fast and getting it right?"},
]

assert len(PILOT_PROBES) == 30
assert sum(p["class"] == "self-concept" for p in PILOT_PROBES) == 15
assert sum(p["class"] == "process" for p in PILOT_PROBES) == 15

# Blind κ-classification gate (FRAMING_SUBCONSTRUCT_PREREG §4): an INDEPENDENT blind classifier (rate-blind,
# interleaved order, no hypothesis) re-labelled the 30 probes; Cohen's κ vs the writer-intended classes =
# **0.935** (gate ≥0.60 → PASS). One disagreement → excluded (admit only both-agreed):
EXCLUDED = {"origin-becoming"}  # classifier called "How did you become the engineer you are today?" borderline
#   (narrative-identity vs "how"-process ambiguity) — correctly caught; dropped from the admitted set.
ADMITTED = [p for p in PILOT_PROBES if p["dimension"] not in EXCLUDED]  # 14 self-concept + 15 process
assert len(ADMITTED) == 29
assert sum(p["class"] == "self-concept" for p in ADMITTED) == 14
assert sum(p["class"] == "process" for p in ADMITTED) == 15
