"""Power-law forgetting curve — properties, anchoring, and the exponential limit.

Thread 2 of the "precision like nature" effort. The episodic decay term changed from
a single exponential ``e^(-λt)`` to a scale-free power law ``D(t) = (1 + t/τ)^(-β)``
(a DELIBERATE DEVIATION; see docs/DEVIATIONS.md). These tests lock the properties that
make the deviation safe and principled:

  * the half-life anchor is preserved for EVERY shape β (D(0)=1, D(halflife)=0.5),
  * τ is derived from the half-life and β (not an independent dial),
  * the tail is heavier than an exponential's (the scale-free property we want) while
    recent decay is slightly faster,
  * the exponential is recovered exactly in the β→∞ limit (generalizes, never contradicts),
  * the closed-form eviction horizon matches the live accessibility curve,
  * the curve stays finite and well-behaved across the validated parameter range.
"""

import math

import pytest

from cdms.config import Config
from cdms.salience import accessibility


def _exp_decay(cfg, t):
    """The pure-exponential curve the power law generalizes (β→∞ limit)."""
    return math.exp(-cfg.decay_lambda * t)


# --------------------------------------------------------------------------- #
# Anchors: D(0)=1 and D(halflife)=0.5 for EVERY shape β
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("beta", [0.5, 1.0, 2.0, 4.0, 8.0, 100.0])
def test_halflife_anchor_invariant_across_shape(beta):
    cfg = Config(forgetting_shape=beta)
    assert math.isclose(accessibility(1.0, 0.0, 0, cfg), 1.0, rel_tol=1e-12)
    assert math.isclose(accessibility(1.0, cfg.decay_halflife_days, 0, cfg), 0.5, rel_tol=1e-9)


def test_halflife_anchor_holds_when_halflife_changes():
    # Move the free anchor; D(new_halflife) must still be 0.5 (τ tracks it).
    cfg = Config(decay_halflife_days=14.0, forgetting_shape=2.0)
    assert math.isclose(accessibility(1.0, 14.0, 0, cfg), 0.5, rel_tol=1e-9)


# --------------------------------------------------------------------------- #
# τ is DERIVED, not dialed
# --------------------------------------------------------------------------- #
def test_decay_tau_formula_and_default():
    cfg = Config()
    expected = cfg.decay_halflife_days / (2.0 ** (1.0 / cfg.forgetting_shape) - 1.0)
    assert math.isclose(cfg.decay_tau, expected, rel_tol=1e-12)
    assert math.isclose(cfg.decay_tau, 70.0122, rel_tol=1e-4)  # halflife 29, β=2


def test_decay_tau_tracks_shape_and_halflife():
    base = Config()  # β=2
    # Heavier tail (smaller β) at a fixed half-life uses a SMALLER τ.
    assert Config(forgetting_shape=1.0).decay_tau < base.decay_tau
    # τ scales linearly with the half-life at fixed β.
    assert math.isclose(Config(decay_halflife_days=58.0).decay_tau, 2 * base.decay_tau, rel_tol=1e-12)


# --------------------------------------------------------------------------- #
# Shape: monotone, heavier tail than exponential, slightly faster early
# --------------------------------------------------------------------------- #
def test_curve_is_monotone_decreasing():
    cfg = Config()
    prev = accessibility(1.0, 0.0, 0, cfg)
    for t in range(1, 2000, 7):
        cur = accessibility(1.0, float(t), 0, cfg)
        assert cur < prev
        prev = cur


def test_tail_is_heavier_than_exponential():
    # The scale-free property: well past the half-life the power law retains MUCH more.
    cfg = Config()
    for t in (90.0, 180.0, 365.0, 730.0):
        assert accessibility(1.0, t, 0, cfg) > _exp_decay(cfg, t)
    # At one year the gap is large, not marginal.
    assert accessibility(1.0, 365.0, 0, cfg) > 100 * _exp_decay(cfg, 365.0)


def test_recent_decay_is_slightly_faster_than_exponential():
    # Below the half-life the power law sits just under the exponential (faster early
    # forgetting of recent clutter); they cross exactly at the half-life.
    cfg = Config()
    for t in (3.0, 7.0, 14.0):
        assert accessibility(1.0, t, 0, cfg) < _exp_decay(cfg, t)
    assert math.isclose(accessibility(1.0, 29.0, 0, cfg), _exp_decay(cfg, 29.0), rel_tol=1e-9)


# --------------------------------------------------------------------------- #
# The exponential is the β→∞ limit (generalizes, never contradicts)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("t", [5.0, 29.0, 90.0, 365.0])
def test_large_shape_converges_to_exponential(t):
    cfg = Config(forgetting_shape=1e6)
    assert math.isclose(accessibility(1.0, t, 0, cfg), _exp_decay(Config(), t), rel_tol=1e-4)


# --------------------------------------------------------------------------- #
# Closed-form eviction horizon matches the live curve
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("s0", [1.0, 2.0, 3.0])
def test_eviction_horizon_matches_curve(s0):
    # Evict when A = s0 * D(t) < retention_floor (c=0). Closed form:
    #   t* = τ * [ (s0 / floor)^(1/β) - 1 ]
    cfg = Config()
    floor = cfg.retention_floor
    t_star = cfg.decay_tau * ((s0 / floor) ** (1.0 / cfg.forgetting_shape) - 1.0)
    just_before = accessibility(s0, t_star - 1e-3, 0, cfg)
    just_after = accessibility(s0, t_star + 1e-3, 0, cfg)
    assert just_before > floor > just_after  # the curve crosses the floor exactly at t*


def test_flashbulb_survives_far_longer_than_exponential():
    # A floored catastrophe (S0=3, c=0) under the exponential evicted at ~142.3 d
    # (ln(30)/λ). Under β=2 it survives to ~313 d — the heavy tail in action.
    cfg = Config()
    floor = cfg.retention_floor
    t_star = cfg.decay_tau * ((3.0 / floor) ** (1.0 / cfg.forgetting_shape) - 1.0)
    assert 300.0 < t_star < 320.0
    exp_t_star = math.log(3.0 / floor) / cfg.decay_lambda
    assert math.isclose(exp_t_star, 142.30, abs_tol=0.1)
    assert t_star > 2 * exp_t_star - 30  # materially longer survival


# --------------------------------------------------------------------------- #
# Numerical robustness across the validated parameter range
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("beta", [0.5, 1.0, 2.0, 8.0, 1e6])
@pytest.mark.parametrize("t", [0.0, 1.0, 365.0, 1e6])
def test_curve_finite_and_in_unit_interval(beta, t):
    cfg = Config(forgetting_shape=beta)
    d = accessibility(1.0, t, 0, cfg)
    assert math.isfinite(d)
    assert 0.0 <= d <= 1.0


def test_reinforcement_still_applies_on_top_of_power_law():
    # Decay and reinforcement compose unchanged: a reinforced trace is the decayed
    # trace times the (capped) testing-effect multiplier.
    cfg = Config()
    bare = accessibility(1.0, 50.0, 0, cfg)
    hot = accessibility(1.0, 50.0, 1000, cfg)  # saturates at the cap
    assert math.isclose(hot, bare * cfg.reinforce_cap, rel_tol=1e-9)
