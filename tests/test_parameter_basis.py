"""Parameter basis: regression-lock the genotype's inter-constant relationships.

Thread 1 of the "derive, don't dial" effort. An audit of every numeric cognitive
constant in ``Config`` (see docs/PARAMETER_BASIS.md) sorted them into three kinds:

  * FREE        — an independent principle-parameter, chosen, not derived.
  * DERIVED     — a CONSEQUENCE of free parameters; must track them by formula.
  * COINCIDENCE — equal in value to another constant by accident, NOT by relationship.

These tests lock all three. They assert that:
  1. each DERIVED property equals its formula and its documented default,
  2. each DERIVED property TRACKS its free parameters when they move (the whole point
     of deriving instead of dialing — change the free knob and the consequence follows),
  3. the derived saturation clamp is genuinely load-bearing in salience.accessibility,
  4. the laws already enforced in config._validate stay enforced (ladder, weight gate, band),
  5. the COINCIDENCES are independent — equal today, but not coupled, so a future edit
     to one must NOT be assumed to move the other.

If a future change breaks a real derivation, (1)-(3) fail loudly. If a future change
quietly couples two coincidentally-equal constants (manufacturing false structure —
exactly the trap that produced bogus "exact identities" in external analyses), (5) fails.
"""

import math

import pytest

from cdms.config import Config, _validate
from cdms.salience import accessibility


# --------------------------------------------------------------------------- #
# 1. DERIVED properties equal their formula and their documented default
# --------------------------------------------------------------------------- #
def test_decay_lambda_is_derived_from_halflife():
    # Supposition: lambda is fixed by the half-life, not an independent dial.
    cfg = Config()
    assert math.isclose(cfg.decay_lambda, math.log(2.0) / cfg.decay_halflife_days, rel_tol=1e-12)
    # Result: e^(-lambda * halflife) == 0.5 exactly (the defining property).
    assert math.isclose(math.exp(-cfg.decay_lambda * cfg.decay_halflife_days), 0.5, rel_tol=1e-12)


def test_decay_tau_is_derived_from_halflife_and_shape():
    # Supposition: tau is a CONSEQUENCE of the half-life and the power-law shape, pinned so
    # D(halflife)=0.5 for any beta. tau = halflife / (2^(1/beta) - 1).
    cfg = Config()
    expected = cfg.decay_halflife_days / (2.0 ** (1.0 / cfg.forgetting_shape) - 1.0)
    assert math.isclose(cfg.decay_tau, expected, rel_tol=1e-12)
    assert math.isclose(cfg.decay_tau, 70.0122, rel_tol=1e-4)  # halflife 29, beta 2


def test_decay_lambda_is_the_exponential_limit_not_the_live_rate():
    # decay_lambda is retained as the beta->inf limit / half-life reference, NOT the curve
    # the live code uses (that is decay_tau + forgetting_shape). Both still satisfy the anchor.
    cfg = Config()
    assert math.isclose(math.exp(-cfg.decay_lambda * cfg.decay_halflife_days), 0.5, rel_tol=1e-12)
    big = Config(forgetting_shape=1e6)  # near the exponential limit
    assert math.isclose(
        (1.0 + cfg.decay_halflife_days / big.decay_tau) ** (-big.forgetting_shape), 0.5, rel_tol=1e-4
    )


def test_reinforce_saturation_clamp_default_and_formula():
    # Supposition: the clamp is ceil(ln(cap)/ln(alpha)) + 1 (saturation count c*, plus a
    # one-step overflow-safety margin), not a hand-set integer.
    cfg = Config()
    c_star = math.ceil(math.log(cfg.reinforce_cap) / math.log(cfg.reinforce_alpha))
    assert c_star == 5  # alpha^5 = 1.15^5 = 2.011 first reaches cap 2.0
    assert cfg.reinforce_saturation_clamp == c_star + 1 == 6


def test_ema_floor_onset_support_default_and_formula():
    # Supposition: the adaptive EMA hits its floor at support = (ema/ema_min)^2.
    cfg = Config()
    expected = (cfg.gist_valence_ema / cfg.gist_valence_ema_min) ** 2
    assert math.isclose(cfg.ema_floor_onset_support, expected, rel_tol=1e-12)
    assert math.isclose(cfg.ema_floor_onset_support, 64.0, rel_tol=1e-12)


def test_gist_idle_survival_cycles_default_and_formula():
    # Supposition: a support-capped gist survives ln(cap/floor)/|ln(gamma)| idle cycles.
    cfg = Config()
    expected = math.log(cfg.gist_support_decay_cap / cfg.gist_retention_floor) / abs(
        math.log(cfg.gist_decay_per_cycle)
    )
    assert math.isclose(cfg.gist_idle_survival_cycles, expected, rel_tol=1e-12)
    # Result: ~396.18 cycles; the config comment's "~400" is this rounded.
    assert 396.0 < cfg.gist_idle_survival_cycles < 397.0


# --------------------------------------------------------------------------- #
# 2. DERIVED properties TRACK their free parameters (derive, don't dial)
# --------------------------------------------------------------------------- #
def test_decay_lambda_tracks_halflife():
    # Procedure: halve the half-life -> lambda must double.
    base = Config()
    fast = Config(decay_halflife_days=base.decay_halflife_days / 2)
    assert math.isclose(fast.decay_lambda, 2 * base.decay_lambda, rel_tol=1e-12)


def test_decay_tau_tracks_halflife_and_shape():
    base = Config()  # beta=2
    # tau scales linearly with the half-life at fixed shape.
    assert math.isclose(Config(decay_halflife_days=58.0).decay_tau, 2 * base.decay_tau, rel_tol=1e-12)
    # a heavier tail (smaller beta) at fixed half-life uses a smaller tau.
    assert Config(forgetting_shape=1.0).decay_tau < base.decay_tau < Config(forgetting_shape=8.0).decay_tau


def test_saturation_clamp_tracks_alpha_and_cap():
    # A larger cap (harder to saturate) or a weaker alpha (slower) -> more reinforcements
    # needed -> a larger clamp. The number is never hand-edited; it follows the two knobs.
    base = Config()  # alpha=1.15, cap=2.0 -> clamp 6
    bigger_cap = Config(reinforce_cap=4.0)  # ceil(ln4/ln1.15)=10, clamp 11
    assert bigger_cap.reinforce_saturation_clamp == math.ceil(math.log(4.0) / math.log(1.15)) + 1 == 11
    weaker_alpha = Config(reinforce_alpha=1.05)  # ceil(ln2/ln1.05)=15, clamp 16
    assert weaker_alpha.reinforce_saturation_clamp == math.ceil(math.log(2.0) / math.log(1.05)) + 1 == 16
    assert bigger_cap.reinforce_saturation_clamp > base.reinforce_saturation_clamp


def test_ema_floor_onset_tracks_floor():
    # The audited counter-intuitive lever: LOWERING ema_min raises the onset support
    # (makes mature traits MORE rigid, not less). Lock that direction.
    onset_002 = Config(gist_valence_ema_min=0.02).ema_floor_onset_support  # (0.4/0.02)^2 = 400
    onset_005 = Config(gist_valence_ema_min=0.05).ema_floor_onset_support  # 64
    onset_010 = Config(gist_valence_ema_min=0.10).ema_floor_onset_support  # 16
    assert math.isclose(onset_002, 400.0, rel_tol=1e-12)
    assert math.isclose(onset_005, 64.0, rel_tol=1e-12)
    assert math.isclose(onset_010, 16.0, rel_tol=1e-12)
    assert onset_002 > onset_005 > onset_010  # lower floor => higher onset => more rigid


def test_idle_survival_tracks_decay_and_cap():
    # Gentler per-cycle decay or a higher support cap -> longer survival.
    base = Config()
    gentler = Config(gist_decay_per_cycle=0.99)  # closer to 1 => slower fade
    assert gentler.gist_idle_survival_cycles > base.gist_idle_survival_cycles


# --------------------------------------------------------------------------- #
# 3. The derived clamp is LOAD-BEARING in salience.accessibility (not decorative)
# --------------------------------------------------------------------------- #
def test_saturation_clamp_governs_accessibility_saturation():
    cfg = Config()
    # Reinforcement saturates at the cap and stays there for any access_count >= clamp.
    at_clamp = accessibility(1.0, 0.0, cfg.reinforce_saturation_clamp, cfg)
    way_past = accessibility(1.0, 0.0, cfg.reinforce_saturation_clamp + 1000, cfg)
    assert math.isclose(at_clamp, cfg.reinforce_cap, rel_tol=1e-9)
    assert math.isclose(at_clamp, way_past, rel_tol=1e-12)


def test_saturation_clamp_prevents_overflow():
    # The clamp's real job: keep alpha**access_count from overflowing for a very hot,
    # long-lived memory. Without it, 1.15**1e9 overflows; with it, we get the cap.
    cfg = Config()
    huge = accessibility(1.0, 0.0, 10**9, cfg)
    assert math.isclose(huge, cfg.reinforce_cap, rel_tol=1e-9)


# --------------------------------------------------------------------------- #
# 4. Laws already enforced in _validate stay enforced (invariant regression-lock)
# --------------------------------------------------------------------------- #
def test_similarity_ladder_ordering_holds_at_defaults():
    cfg = Config()
    assert cfg.cluster_sim_threshold <= cfg.gist_match_sim_threshold <= cfg.dedup_sim_threshold


def test_similarity_ladder_violation_is_repaired():
    # Procedure: invert the ladder (match below cluster); _validate must restore ordering.
    cfg = Config()
    cfg.gist_match_sim_threshold = 0.70  # below cluster 0.78 -> illegal
    _validate(cfg)
    assert cfg.cluster_sim_threshold <= cfg.gist_match_sim_threshold <= cfg.dedup_sim_threshold


def test_zero_goal_memory_stays_sub_crisis():
    # The H-2 weight gate: a goal=0 memory's max salience is goal_gate_floor * sum(weights);
    # it must stay under crisis_threshold so noise can't self-elevate to a scar.
    cfg = Config()
    weights = cfg.w_surprise + cfg.w_contingency + cfg.w_self_ref + cfg.w_affect
    zero_goal_max = cfg.goal_gate_floor * weights
    assert math.isclose(zero_goal_max, 1.0, rel_tol=1e-12)  # 0.25 * 4.0
    assert zero_goal_max < cfg.crisis_threshold  # 1.0 < 3.0


def test_overpowered_weights_are_scaled_below_crisis():
    # Procedure: weights large enough that a zero-goal memory would self-elevate; _validate
    # must scale them down so goal_gate_floor * sum(weights) stays under crisis_threshold.
    cfg = Config()
    for w in ("w_surprise", "w_contingency", "w_self_ref", "w_affect"):
        setattr(cfg, w, 10.0)  # 0.25 * 40 = 10.0 >> crisis_threshold 3.0
    _validate(cfg)
    weights = cfg.w_surprise + cfg.w_contingency + cfg.w_self_ref + cfg.w_affect
    assert cfg.goal_gate_floor * weights < cfg.crisis_threshold


def test_relation_band_ordering_and_mapping():
    cfg = Config()
    assert cfg.relation_neg_threshold < cfg.relation_pos_threshold  # ordered band
    # Boundary behaviour of the three-way map.
    assert cfg.relation_from_valence(cfg.relation_pos_threshold + 0.01) == "handles_well"
    assert cfg.relation_from_valence(cfg.relation_neg_threshold - 0.01) == "has_trouble_with"
    assert cfg.relation_from_valence(0.0) == "frequently_works_on"


# --------------------------------------------------------------------------- #
# 5. COINCIDENCES are independent — equal today, NOT coupled
# --------------------------------------------------------------------------- #
def test_three_half_caps_are_independent():
    # project_budget_cap, session_budget_cap, assoc_boost_cap_frac are all 0.5 by default
    # but live in unrelated computations. They must be independently settable and survive
    # validation as distinct values — proof they are not one shared parameter.
    cfg = Config(project_budget_cap=0.5, session_budget_cap=0.3, assoc_boost_cap_frac=0.7)
    _validate(cfg)
    assert (cfg.project_budget_cap, cfg.session_budget_cap, cfg.assoc_boost_cap_frac) == (0.5, 0.3, 0.7)


def test_two_min_counts_are_independent():
    # min_cluster_support (clustering geometry) and scar_elevation_min_sessions (cross-session
    # recurrence) are both 2 by default but semantically unrelated.
    cfg = Config(min_cluster_support=2, scar_elevation_min_sessions=5)
    _validate(cfg)
    assert cfg.min_cluster_support == 2
    assert cfg.scar_elevation_min_sessions == 5


def test_two_hundred_caps_are_independent():
    # gist_support_decay_cap (idle-decay resistance) and scar_project_cap (L3 quota) are both
    # 100 by default but unrelated resource controls.
    cfg = Config(gist_support_decay_cap=100, scar_project_cap=250)
    _validate(cfg)
    assert cfg.gist_support_decay_cap == 100
    assert cfg.scar_project_cap == 250


def test_crisis_threshold_is_not_derived_from_weight_count():
    # The tempting coincidence: crisis_threshold (3.0) == sum(weights) - 1 == 4 - 1. It is NOT.
    # crisis_threshold is calibrated to real incident data (a measured 2.8 data-loss crisis vs
    # the 3.0 gate), independent of how many S0 drivers there are. Prove independence: change
    # the weights so the "sum - 1" identity would predict a different threshold; crisis_threshold
    # must stay put (and must NOT be scaled, since the zero-goal max stays sub-crisis).
    cfg = Config()
    for w in ("w_surprise", "w_contingency", "w_self_ref", "w_affect"):
        setattr(cfg, w, 2.0)  # sum = 8 -> "sum - 1" would be 7; zero-goal max = 0.25*8 = 2.0 < 2.7
    _validate(cfg)
    weights = cfg.w_surprise + cfg.w_contingency + cfg.w_self_ref + cfg.w_affect
    assert cfg.crisis_threshold == 3.0  # unchanged
    assert cfg.crisis_threshold != weights - 1  # 3.0 != 7.0 — the "4-1=3" was a coincidence


@pytest.mark.parametrize(
    "field, value",
    [
        ("decay_halflife_days", 14.0),
        ("reinforce_cap", 3.0),
        ("gist_valence_ema_min", 0.02),
        ("gist_decay_per_cycle", 0.99),
    ],
)
def test_derived_properties_never_raise_across_reasonable_configs(field, value):
    # The properties are pure functions of valid free params; they must compute (not raise)
    # for any in-range configuration, so callers can treat them as plain attributes.
    cfg = Config(**{field: value})
    assert cfg.decay_lambda > 0
    assert cfg.reinforce_saturation_clamp >= 1
    assert cfg.ema_floor_onset_support > 0
    assert cfg.gist_idle_survival_cycles > 0
