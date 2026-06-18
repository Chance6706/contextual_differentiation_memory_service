"""§8 temperament layer — Phase 0: archetype presets + pure-function control.

Phase 0 is **STATE + CONTROL only**. There is deliberately NO drift/learning here
(`current == seed`), no proposal lever, and no drift log — those are later phases of
the §8.7 prerequisite chain (Phase 1a proposal lever → 1b update rule → 2 survivability
→ 3 log). See `docs/TEMPERAMENT_PLAN.md`.

Two invariants this module must keep:

* **Pure function of its inputs.** No DB, no file/network I/O, and — critically — NO
  wall-clock. The drift discipline is activity-clock only (§8.3/§5.3); importing
  ``datetime``/``time`` here would let absence-loss back in via the magnitude.
* **Operator-only.** Nothing here may enter SessionStart ``additionalContext`` or any
  MCP ``retrieve`` tier (break-cycle principle #1 — the Bem self-perception firewall:
  a self that reads its own disposition would narrate it into a self-fulfilling story).

Scale: every dial is normalized to ``[0, 1]`` where 0 = the left pole of the §8.1
conceptual range and 1 = the right pole.
"""

from __future__ import annotations

from math import sqrt
from typing import Iterable, Mapping

from .models import Dial

# The eight dials (DESIGN §8.1), with the [0,1] pole semantics.
DIALS: tuple[str, ...] = (
    "autonomy_gate",            # 0 review-everything … 1 review-nothing
    "deference_independence",   # 0 yes-man … 1 adversarial-within-limits
    "emotional_gain",           # 0 stoic … 1 passionate
    "impact_sensitivity",       # 0 low … 1 high
    "exploration_radius",       # 0 focused … 1 adventurous
    "dream_damping",            # 0 none … 1 heavy REM damping
    "mood_half_life",           # 0 short … 1 long
    "discovered_emotion_cap",   # 0 strict cap … 1 loose cap
)

# §1.1 plasticity GRADIENT (not a frozen/free wall): substrate-like dials
# (reactivity / harm-avoidance analogs) drift little and sit in tight bands;
# character-like dials (self-directedness analogs) get more — still small — plasticity
# and wider bands. Coefficient in [0,1]; INERT in Phase 0 (no drift yet), stored so the
# Phase 1b update rule has the per-dial rate ready. First-cut, tunable in Phase 2.
PLASTICITY: dict[str, float] = {
    "emotional_gain": 0.10,
    "impact_sensitivity": 0.10,
    "discovered_emotion_cap": 0.10,
    "dream_damping": 0.20,
    "mood_half_life": 0.20,
    "autonomy_gate": 0.30,
    "deference_independence": 0.40,
    "exploration_radius": 0.40,
}

# Per-dial bound half-width = _MAX_BAND * plasticity (so tight dials ~0.05, wide ~0.20).
_MAX_BAND = 0.5

# Per-archetype seed set-points (§8.5). A dial omitted defaults to 0.5 (moderate).
_ARCHETYPE_SEEDS: dict[str, dict[str, float]] = {
    "co-pilot": {},  # moderate across all dials (the install default)
    "sparring-partner": {
        "deference_independence": 0.80, "autonomy_gate": 0.60, "exploration_radius": 0.60,
    },
    "apprentice": {
        "deference_independence": 0.20, "autonomy_gate": 0.20, "exploration_radius": 0.35,
        "emotional_gain": 0.55,
    },
    "stoic-analyst": {
        "emotional_gain": 0.15, "impact_sensitivity": 0.30, "discovered_emotion_cap": 0.20,
        "deference_independence": 0.60,
    },
    "maverick": {
        "exploration_radius": 0.90, "autonomy_gate": 0.85, "emotional_gain": 0.80,
        "deference_independence": 0.75, "impact_sensitivity": 0.70,
    },
}

# Joint-leash radius per archetype (Euclidean; an OWNED STIPULATION per §1.5, not a
# discovered identity threshold). Maverick gets a wider leash ("highest drift", §8.5).
# A Mahalanobis Σ from the Phase 2 survivable region replaces this later (Round-2 P2).
_ARCHETYPE_RADIUS: dict[str, float] = {
    "co-pilot": 0.30, "sparring-partner": 0.30, "apprentice": 0.30,
    "stoic-analyst": 0.30, "maverick": 0.45,
}

DEFAULT_ARCHETYPE = "co-pilot"


def archetypes() -> tuple[str, ...]:
    """Names of the known starter archetypes (§8.5)."""
    return tuple(_ARCHETYPE_SEEDS.keys())


def _seed_for(archetype: str, dial: str) -> float:
    return _ARCHETYPE_SEEDS.get(archetype, {}).get(dial, 0.5)


def preset_dials(archetype: str) -> list[Dial]:
    """The seeded dial set for an archetype: ``current == seed`` (Phase 0 — no drift),
    bounds = ``seed ± band`` clamped to [0,1]. Pure; used to seed the store at install.

    Unknown archetype falls back to the default rather than raising — seeding must
    never brick a fresh store on a config typo (config validation warns separately).
    """
    if archetype not in _ARCHETYPE_SEEDS:
        archetype = DEFAULT_ARCHETYPE
    out: list[Dial] = []
    for name in DIALS:
        seed = _seed_for(archetype, name)
        plast = PLASTICITY[name]
        band = _MAX_BAND * plast
        lower = max(0.0, seed - band)
        upper = min(1.0, seed + band)
        out.append(Dial(name=name, seed=seed, current=seed,
                        lower=lower, upper=upper, plasticity=plast))
    return out


def archetype_radius(archetype: str) -> float:
    return _ARCHETYPE_RADIUS.get(archetype, _ARCHETYPE_RADIUS[DEFAULT_ARCHETYPE])


# --------------------------------------------------------------------------- #
# pure-function CONTROL  (zero storage; no wall-clock; §8.3 / §8.7 "control is a
# pure function of state (seed, current, bounds)")
# --------------------------------------------------------------------------- #
def near_bound(dial: Dial, eps: float = 0.02) -> bool:
    """True if ``current`` sits within ``eps`` of either per-dial bound (a nudge that
    would route to the proposal lever in Phase 1b)."""
    return dial.current <= dial.lower + eps or dial.current >= dial.upper - eps


def large_shift(old: float, new: float, theta: float) -> bool:
    """True if a proposed single move is large enough to surface as a proposal."""
    return abs(new - old) >= theta


def leash_distance(current: Mapping[str, float], seed: Mapping[str, float]) -> float:
    """Euclidean distance of the ``current`` vector from the **static** ``seed`` vector.

    Anchored to the immutable seed — never the previous step. This is exactly what makes
    the "no archetype-hopping" guarantee survive a sub-threshold "boiling-frog" ratchet
    (Round-2 G-A): many tiny per-step moves that each clear a per-step gate still trip
    the leash once their *cumulative* distance from seed exceeds the radius.
    """
    return sqrt(sum((current[d] - seed[d]) ** 2 for d in seed))


def leash_exceeded(current: Mapping[str, float], seed: Mapping[str, float],
                   r_archetype: float) -> bool:
    """True if the joint vector has drifted past the archetype leash — a bound-event
    that (in Phase 1b) routes to the §7.6 proposal lever instead of drifting silently."""
    return leash_distance(current, seed) > r_archetype


def vector(dials: Iterable[Dial]) -> dict[str, float]:
    """``{name: current}`` helper for leash checks."""
    return {d.name: d.current for d in dials}


def seed_vector(dials: Iterable[Dial]) -> dict[str, float]:
    """``{name: seed}`` helper for leash checks (the static anchor)."""
    return {d.name: d.seed for d in dials}
