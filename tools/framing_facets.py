"""FROZEN facet-dimension populations + seeded sampler for the framing-sub-construct study.

Source of truth: `docs/validation/runtime_instrument/framing_taxonomy.md` (FROZEN 2026-06-29). The dimension
NAMES are class-labeled (self-concept / process) only so the generator can pick the right answer-form; the
direction-blind generator is NOT told which class is hypothesized to leak. Probe TEXT is written separately by
a blind agent and lives in `framing_facets_probes.py` (added after generation), not here — so this module
stays the immutable dimension+order spec.

Draw order (committed, seed=0): pilot = first 15/class; confirmatory = the disjoint remainder.
"""
from __future__ import annotations

import random

# 34 self-concept dimensions ("who you ARE"), grounded in self-concept/identity frameworks (see taxonomy §A).
SELF_CONCEPT = [
    "temperament", "risk-disposition", "persistence-grit", "curiosity-trait", "standards-perfectionism",
    "core-strengths", "weaknesses-blindspots", "signature-skill", "self-assessed-level",
    "non-negotiables", "what-you-care-about", "defining-creed", "integrity-ethics",
    "self-worth-source", "confidence-doubt", "pride-in-being", "shaping-failure",
    "team-role-identity", "insider-outsider", "what-people-come-for", "reflected-self", "misread",
    "origin-becoming", "evolution", "constancy", "ideal-self",
    "distinctiveness", "signature-fingerprint", "self-metaphor",
    "core-drive", "relationship-to-craft", "energizes-self", "self-summary", "defend-refuse",
]

# 30 process dimensions ("how you DO"), grounded in SE activity taxonomies / the SDLC (see taxonomy §B).
PROCESS = [
    "requirements-scoping", "design-architecture", "blank-file-process", "unfamiliar-problem",
    "implementation-habits", "naming-structure", "debugging-method", "testing-approach",
    "reviewing-others", "receiving-criticism", "refactoring", "tooling-environment", "version-control",
    "shared-codebase", "documentation", "deployment-release", "incident-response", "tech-choice-decision",
    "estimation-planning", "speed-quality-priority", "learning-new-tech", "handling-ambiguity",
    "working-under-constraint", "defining-done", "self-correction", "scope-decisions", "explaining-technical",
    "managing-rabbithole", "defaults-conventions", "mentoring-method",
]

assert len(SELF_CONCEPT) == 34 and len(set(SELF_CONCEPT)) == 34, "self-concept population changed"
assert len(PROCESS) == 30 and len(set(PROCESS)) == 30, "process population changed"


def _ordered(pop, seed):
    o = list(pop)
    random.Random(seed).shuffle(o)
    return o


def pilot_sample(seed=0, k=15):
    """(self_concept[:k], process[:k]) in committed seeded order — the pilot draw."""
    return _ordered(SELF_CONCEPT, seed)[:k], _ordered(PROCESS, seed)[:k]


def confirmatory_sample(seed=0, pilot_k=15, k_sc=None, k_proc=None):
    """The disjoint remainder after the pilot draw (pilot facets excluded from confirmatory)."""
    sc = _ordered(SELF_CONCEPT, seed)[pilot_k:]
    proc = _ordered(PROCESS, seed)[pilot_k:]
    return (sc if k_sc is None else sc[:k_sc]), (proc if k_proc is None else proc[:k_proc])


if __name__ == "__main__":
    sc, pr = pilot_sample()
    print(f"PILOT self-concept ({len(sc)}): {sc}")
    print(f"PILOT process ({len(pr)}): {pr}")
    rsc, rpr = confirmatory_sample()
    print(f"CONFIRMATORY-remainder self-concept ({len(rsc)}), process ({len(rpr)})")
