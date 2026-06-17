"""The cognitive core: write-time salience gating and decay-driven accessibility.

This module is pure Python (stdlib + math only) so the "genotype" — the cheap,
slightly-wrong discard policy that gives each deployment its identity — is fully
inspectable, deterministic, and unit-testable in isolation.

Two formulas from the spec are implemented here:

    Write-time salience (surprisal gating):
        S0 = G_goal * (S_surprise + C_contingency + W_self_ref + A_affect)

    Decay-driven accessibility (Ebbinghaus, retrieval-reinforced):
        A(m, t) = S0 * exp(-λ t) * min(α^c, Cap)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from .config import Config


# --------------------------------------------------------------------------- #
# Write path: surprisal-gated initial salience S0
# --------------------------------------------------------------------------- #
@dataclass
class SalienceSignals:
    """The four additive drivers plus the multiplicative goal gate.

    All components are expected in roughly [0, 1] except ``affect`` which is a
    signed valence in [-1, 1]; only its magnitude contributes to memorability,
    while its sign is stored separately as emotional tone.
    """
    goal: float = 1.0          # G_goal multiplicative veto gate, [0, 1]
    surprise: float = 0.0      # S_surprise: novelty / prediction-error proxy, [0, 1]
    contingency: float = 0.0   # C_contingency: did our action change the world, [0, 1]
    self_ref: float = 0.0      # W_self_ref: touches agent's own rules/identity, [0, 1]
    affect: float = 0.0        # A_affect: emotional valence, [-1, 1]


def compute_s0(sig: SalienceSignals, cfg: Config) -> float:
    """Compute initial salience S0 with a multiplicative goal-relevance veto.

    Low goal relevance actively *suppresses* a memory regardless of how novel or
    emotionally charged it was — this is the gate that stops the store from
    filling with loud-but-irrelevant noise. A small floor keeps merely-neutral
    interactions from being annihilated entirely.
    """
    additive = (
        cfg.w_surprise * _clamp01(sig.surprise)
        + cfg.w_contingency * _clamp01(sig.contingency)
        + cfg.w_self_ref * _clamp01(sig.self_ref)
        + cfg.w_affect * abs(_clamp(sig.affect, -1.0, 1.0))
    )
    gate = cfg.goal_gate_floor + (1.0 - cfg.goal_gate_floor) * _clamp01(sig.goal)
    return gate * additive


# --------------------------------------------------------------------------- #
# Read/maintenance path: decay-driven accessibility A(m, t)
# --------------------------------------------------------------------------- #
def accessibility(
    s0: float,
    age_days: float,
    access_count: int,
    cfg: Config,
) -> float:
    """A(m, t) = S0 * exp(-λ t) * min(α^c, Cap).

    * ``exp(-λ t)`` is the Ebbinghaus forgetting curve (λ from a 29-day half-life).
    * ``min(α^c, Cap)`` is retrieval-induced strengthening (the testing effect):
      each recall multiplicatively reinforces the trace, capped so one hot memory
      cannot permanently dominate attention.
    """
    decay = math.exp(-cfg.decay_lambda * max(0.0, age_days))
    # Clamp the exponent BEFORE exponentiating: alpha**access_count overflows for a
    # very hot, long-lived memory (e.g. access_count >= 1e4) and would crash the
    # consolidation eviction loop — even though the cap saturates alpha**c at c≈5.
    c = max(0, access_count)
    if cfg.reinforce_alpha > 1.0 and cfg.reinforce_cap > 0.0:
        c_max = math.ceil(math.log(cfg.reinforce_cap) / math.log(cfg.reinforce_alpha)) + 1
        c = min(c, c_max)
    reinforcement = min(cfg.reinforce_alpha ** c, cfg.reinforce_cap)
    return s0 * decay * reinforcement


def age_days(timestamp_iso: str, now: datetime | None = None) -> float:
    """Elapsed days since an ISO-8601 UTC timestamp."""
    now = now or datetime.now(timezone.utc)
    try:
        ts = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return max(0.0, (now - ts).total_seconds() / 86400.0)


def is_evictable(accessibility_score: float, cfg: Config) -> bool:
    """An episode falls out of reach once accessibility drops below the floor."""
    return accessibility_score < cfg.retention_floor


# --------------------------------------------------------------------------- #
# Consolidation maths: conserved budget + hierarchical softmax competition
# --------------------------------------------------------------------------- #
def conserve_budget(saliences: list[float], k_budget: float) -> list[float]:
    """Renormalize all saliences so they sum to a fixed constant K_budget.

    This is the Anti-RISM (Recursive Internal Salience Misreinforcement / "neural
    howlround") shield: because total attention is zero-sum, boosting one memory
    thread *necessarily* accelerates the decay of unrelated stale items. A runaway
    reinforcement loop becomes mathematically impossible.
    """
    total = sum(saliences)
    if total <= 0.0:
        return list(saliences)
    scale = k_budget / total
    return [s * scale for s in saliences]


def allocate_capped_proportional(
    weights: dict[str, float],
    total: float,
    cap_fraction: float,
) -> dict[str, float]:
    """Split ``total`` across keys proportionally to ``weights``, but with no key
    exceeding ``cap_fraction * total``. Excess from capped keys is redistributed
    proportionally among the rest (water-filling).

    This is the multi-project salience budget: a busy primary keeps the largest
    share (up to the cap) while smaller projects retain a real, un-starved slice —
    "focus on your primaries, but not to the exclusion of the others."
    """
    keys = list(weights)
    n = len(keys)
    if n == 0:
        return {}
    if n == 1:
        return {keys[0]: total}
    cap = cap_fraction * total
    # Infeasible cap (too tight to cover everyone): fall back to an equal split.
    if cap * n < total:
        return {k: total / n for k in keys}

    w = {k: max(0.0, weights[k]) for k in keys}
    alloc: dict[str, float] = {}
    remaining = total
    uncapped = set(keys)
    while uncapped:
        wsum = sum(w[k] for k in uncapped)
        if wsum <= 0.0:                       # no signal left: split remainder evenly
            share = remaining / len(uncapped)
            for k in uncapped:
                alloc[k] = share
            break
        newly_capped = [k for k in uncapped if w[k] / wsum * remaining > cap + 1e-12]
        if not newly_capped:
            for k in uncapped:
                alloc[k] = w[k] / wsum * remaining
            break
        for k in newly_capped:
            alloc[k] = cap
            remaining -= cap
            uncapped.discard(k)
    return alloc


def associative_boost(
    s_old: float,
    s_new: float,
    similarity: float,
    cfg: Config,
) -> float:
    """s_old <- s_old + η * (sim(e_new, e_old) * s_new).

    The present retroactively rewrites the importance of a related past episode.
    Boost is applied only above ``assoc_sim_floor`` to keep the operation local.
    Renormalization via :func:`conserve_budget` afterward keeps the system stable.
    """
    if similarity < cfg.assoc_sim_floor:
        return s_old
    return s_old + cfg.assoc_eta * (similarity * s_new)


def softmax(values: list[float], temperature: float = 1.0) -> list[float]:
    """Numerically stable softmax used for competitive normalization."""
    if not values:
        return []
    t = max(1e-6, temperature)
    m = max(values)
    exps = [math.exp((v - m) / t) for v in values]
    z = sum(exps)
    if z == 0.0:
        n = len(values)
        return [1.0 / n] * n
    return [e / z for e in exps]


def hierarchical_competition(
    grouped: dict[str, list[tuple[str, float]]],
    temperature: float = 1.0,
) -> dict[str, float]:
    """Two-stage softmax competition to protect highlights from quiet periods.

    ``grouped`` maps a session id -> list of (episode_id, salience). We run a
    local softmax *within* each session (so a single noisy debugging marathon
    cannot drown out a quiet but important week), then weight each session by its
    aggregate salience at the epoch level. Returns episode_id -> competition score
    in [0, 1] that can be multiplied into the conserved-budget salience.
    """
    # Session-level salience totals for the epoch-level pass.
    session_totals = {sid: sum(s for _, s in eps) for sid, eps in grouped.items()}
    epoch_weights = softmax(list(session_totals.values()), temperature)
    epoch_by_session = dict(zip(session_totals.keys(), epoch_weights))

    out: dict[str, float] = {}
    for sid, eps in grouped.items():
        local = softmax([s for _, s in eps], temperature)
        w = epoch_by_session.get(sid, 0.0)
        for (eid, _), local_share in zip(eps, local):
            out[eid] = local_share * w
    return out


# --------------------------------------------------------------------------- #
# small numeric helpers
# --------------------------------------------------------------------------- #
def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _clamp01(x: float) -> float:
    return _clamp(x, 0.0, 1.0)
