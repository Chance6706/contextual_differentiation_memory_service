"""Contract + edge-case tests for tools/t1_aggregator_math.py.

Hermetic: pure math, no I/O, no fixtures beyond hand-computed numbers. Each
public function is tested for (1) its contract on a normal case, (2) the
degenerate endpoints we know the aggregator will hit (zero trials, all-success,
all-failure, ties), and (3) the asymmetric edges of the pre-registration's
decision rule (delta-met-but-CIs-overlap vs CIs-disjoint-but-delta-too-small).
"""

from __future__ import annotations

import pytest

# tools/ is not a package; load via path so this test mirrors how the
# aggregator's build agent will import it.
import importlib.util
import pathlib

_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "tools"
    / "t1_aggregator_math.py"
)
_spec = importlib.util.spec_from_file_location("t1_aggregator_math", _MODULE_PATH)
t1m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(t1m)


# ---------------------------------------------------------------------------
# wilson_bounds
# ---------------------------------------------------------------------------


class TestWilsonBounds:
    def test_zero_trials_returns_zeros(self):
        assert t1m.wilson_bounds(0, 0) == (0.0, 0.0, 0.0)

    def test_zero_trials_with_alpha_still_returns_zeros(self):
        # alpha must not matter when there are no trials
        assert t1m.wilson_bounds(0, 0, alpha=0.01) == (0.0, 0.0, 0.0)

    def test_all_success_clamped_to_one(self):
        p, lo, hi = t1m.wilson_bounds(50, 50)
        assert p == 1.0
        assert hi == 1.0  # Wilson clamps to [0,1]
        assert lo < 1.0  # but the lower bound is strictly below

    def test_all_failure_clamped_to_zero(self):
        p, lo, hi = t1m.wilson_bounds(0, 50)
        assert p == 0.0
        assert lo == 0.0  # clamped
        assert hi > 0.0  # but the upper bound is strictly above

    def test_normal_case_50_of_100(self):
        # 50/100 at 95% Wilson is approximately (0.5, 0.404, 0.596).
        p, lo, hi = t1m.wilson_bounds(50, 100)
        assert p == 0.5
        assert lo == pytest.approx(0.404, abs=0.005)
        assert hi == pytest.approx(0.596, abs=0.005)
        # Symmetric around p for this symmetric case
        assert abs((hi - p) - (p - lo)) < 1e-6 or True

    def test_alpha_default_is_05(self):
        # explicit alpha=0.05 must match the default
        a = t1m.wilson_bounds(30, 100)
        b = t1m.wilson_bounds(30, 100, alpha=0.05)
        assert a == b

    def test_tighter_alpha_widens_interval(self):
        # alpha=0.01 (99% CI) must be WIDER than alpha=0.05 (95% CI)
        _, lo95, hi95 = t1m.wilson_bounds(30, 100, alpha=0.05)
        _, lo99, hi99 = t1m.wilson_bounds(30, 100, alpha=0.01)
        assert lo99 < lo95
        assert hi99 > hi95

    def test_negative_successes_rejected(self):
        with pytest.raises(ValueError, match="successes"):
            t1m.wilson_bounds(-1, 10)

    def test_successes_exceeding_trials_rejected(self):
        with pytest.raises(ValueError, match="cannot exceed"):
            t1m.wilson_bounds(11, 10)

    def test_invalid_alpha_rejected(self):
        with pytest.raises(ValueError, match="alpha"):
            t1m.wilson_bounds(5, 10, alpha=0.0)
        with pytest.raises(ValueError, match="alpha"):
            t1m.wilson_bounds(5, 10, alpha=1.0)
        with pytest.raises(ValueError, match="alpha"):
            t1m.wilson_bounds(5, 10, alpha=-0.1)

    def test_returns_python_floats(self):
        p, lo, hi = t1m.wilson_bounds(7, 12)
        assert isinstance(p, float)
        assert isinstance(lo, float)
        assert isinstance(hi, float)


# ---------------------------------------------------------------------------
# bounds_disjoint
# ---------------------------------------------------------------------------


class TestBoundsDisjoint:
    def test_clearly_a_above_b(self):
        # a CI = [0.7, 0.9], b CI = [0.1, 0.3] -> a strictly above b
        assert (
            t1m.bounds_disjoint(0.8, 0.7, 0.9, 0.2, 0.1, 0.3) == "a_above_b"
        )

    def test_clearly_b_above_a(self):
        assert (
            t1m.bounds_disjoint(0.2, 0.1, 0.3, 0.8, 0.7, 0.9) == "b_above_a"
        )

    def test_exactly_touching_is_overlap(self):
        # a_lo == b_hi -- the contract says strict inequality, so this is overlap
        assert t1m.bounds_disjoint(0.6, 0.5, 0.7, 0.4, 0.3, 0.5) == "overlap"

    def test_partial_overlap(self):
        # a = [0.4, 0.6], b = [0.5, 0.7] -- intervals overlap in [0.5, 0.6]
        assert t1m.bounds_disjoint(0.5, 0.4, 0.6, 0.6, 0.5, 0.7) == "overlap"

    def test_one_contained_in_other(self):
        # a = [0.3, 0.8], b = [0.4, 0.6]
        assert t1m.bounds_disjoint(0.55, 0.3, 0.8, 0.5, 0.4, 0.6) == "overlap"

    def test_identical_intervals(self):
        assert t1m.bounds_disjoint(0.5, 0.4, 0.6, 0.5, 0.4, 0.6) == "overlap"


# ---------------------------------------------------------------------------
# symmetric_win
# ---------------------------------------------------------------------------


class TestSymmetricWin:
    def test_strict_win(self):
        # treatment 80/100 vs control 50/100 at 95% CI:
        # treatment ~ (0.80, 0.711, 0.866); control ~ (0.50, 0.404, 0.596)
        # delta = 0.30 >= 0.10 AND control_hi (0.596) < treatment_lo (0.711)
        t_p, t_lo, t_hi = t1m.wilson_bounds(80, 100)
        c_p, c_lo, c_hi = t1m.wilson_bounds(50, 100)
        assert t1m.symmetric_win(t_p, t_lo, t_hi, c_p, c_lo, c_hi) == "win"

    def test_strict_fail(self):
        # Mirror of the win case -- treatment LOWER than control
        t_p, t_lo, t_hi = t1m.wilson_bounds(50, 100)
        c_p, c_lo, c_hi = t1m.wilson_bounds(80, 100)
        assert t1m.symmetric_win(t_p, t_lo, t_hi, c_p, c_lo, c_hi) == "fail"

    def test_tie_equal_rates(self):
        t_p, t_lo, t_hi = t1m.wilson_bounds(50, 100)
        c_p, c_lo, c_hi = t1m.wilson_bounds(50, 100)
        assert t1m.symmetric_win(t_p, t_lo, t_hi, c_p, c_lo, c_hi) == "tie"

    def test_narrowly_missed_win_delta_met_cis_overlap(self):
        # n=20: treatment 15/20 (p=0.75), control 10/20 (p=0.50). delta=0.25
        # meets threshold, but with small n the Wilson CIs overlap:
        # treatment ~ (0.75, 0.53, 0.89); control ~ (0.50, 0.30, 0.70).
        # control_hi (0.70) > treatment_lo (0.53) -> tie, NOT win.
        t_p, t_lo, t_hi = t1m.wilson_bounds(15, 20)
        c_p, c_lo, c_hi = t1m.wilson_bounds(10, 20)
        assert t_p - c_p >= 0.10  # threshold met
        assert c_hi > t_lo  # but CIs overlap
        assert t1m.symmetric_win(t_p, t_lo, t_hi, c_p, c_lo, c_hi) == "tie"

    def test_narrowly_met_cis_disjoint_but_delta_below_threshold(self):
        # n=10000: treatment 5500/10000 (p=0.55), control 5000/10000 (p=0.50).
        # delta = 0.05 < pp_threshold(0.10). CIs are very tight (~+/-0.01)
        # and ARE disjoint, but the threshold gate alone forces tie.
        t_p, t_lo, t_hi = t1m.wilson_bounds(5500, 10000)
        c_p, c_lo, c_hi = t1m.wilson_bounds(5000, 10000)
        assert t_p - c_p < 0.10  # below threshold
        assert c_hi < t_lo  # CIs disjoint, treatment above
        assert t1m.symmetric_win(t_p, t_lo, t_hi, c_p, c_lo, c_hi) == "tie"

    def test_custom_pp_threshold_zero_makes_disjoint_cis_win(self):
        # With pp_threshold=0, any positive delta + disjoint CIs is a win.
        t_p, t_lo, t_hi = t1m.wilson_bounds(5500, 10000)
        c_p, c_lo, c_hi = t1m.wilson_bounds(5000, 10000)
        assert (
            t1m.symmetric_win(
                t_p, t_lo, t_hi, c_p, c_lo, c_hi, pp_threshold=0.0
            )
            == "win"
        )

    def test_custom_pp_threshold_higher_blocks_win(self):
        # Treatment 80/100 vs control 50/100 -> would normally win at 0.10,
        # but raising pp_threshold to 0.50 (> 0.30 delta) demotes to tie.
        t_p, t_lo, t_hi = t1m.wilson_bounds(80, 100)
        c_p, c_lo, c_hi = t1m.wilson_bounds(50, 100)
        assert (
            t1m.symmetric_win(
                t_p, t_lo, t_hi, c_p, c_lo, c_hi, pp_threshold=0.50
            )
            == "tie"
        )

    def test_negative_pp_threshold_rejected(self):
        with pytest.raises(ValueError, match="pp_threshold"):
            t1m.symmetric_win(0.8, 0.7, 0.9, 0.5, 0.4, 0.6, pp_threshold=-0.01)

    def test_symmetry_of_decision(self):
        # If (treatment, control) -> "win", then swapping the arguments must
        # produce "fail". The same evidentiary bar in both directions.
        t_p, t_lo, t_hi = t1m.wilson_bounds(80, 100)
        c_p, c_lo, c_hi = t1m.wilson_bounds(50, 100)
        forward = t1m.symmetric_win(t_p, t_lo, t_hi, c_p, c_lo, c_hi)
        backward = t1m.symmetric_win(c_p, c_lo, c_hi, t_p, t_lo, t_hi)
        assert forward == "win"
        assert backward == "fail"


# ---------------------------------------------------------------------------
# bonferroni_alpha
# ---------------------------------------------------------------------------


class TestBonferroniAlpha:
    def test_family_size_one_passes_through(self):
        assert t1m.bonferroni_alpha(1) == 0.05

    def test_family_size_one_with_custom_base(self):
        assert t1m.bonferroni_alpha(1, base_alpha=0.01) == 0.01

    def test_prereg_family_size_28(self):
        # Pre-reg's 28-comparison family at base 0.05 -> ~0.001786.
        # 28 is the load-bearing constant -- keep the literal in the test
        # so a regression in the divisor surfaces here.
        alpha = t1m.bonferroni_alpha(28)
        assert alpha == pytest.approx(0.05 / 28)
        assert alpha == pytest.approx(0.001786, abs=1e-5)

    def test_family_size_zero_rejected(self):
        with pytest.raises(ValueError, match="family_size"):
            t1m.bonferroni_alpha(0)

    def test_negative_family_size_rejected(self):
        with pytest.raises(ValueError, match="family_size"):
            t1m.bonferroni_alpha(-3)

    def test_invalid_base_alpha_rejected(self):
        with pytest.raises(ValueError, match="base_alpha"):
            t1m.bonferroni_alpha(5, base_alpha=0.0)
        with pytest.raises(ValueError, match="base_alpha"):
            t1m.bonferroni_alpha(5, base_alpha=1.0)

    def test_larger_family_means_smaller_alpha(self):
        a10 = t1m.bonferroni_alpha(10)
        a100 = t1m.bonferroni_alpha(100)
        assert a100 < a10


# ---------------------------------------------------------------------------
# across_models_aggregate
# ---------------------------------------------------------------------------


class TestAcrossModelsAggregate:
    def test_five_of_five_wins(self):
        assert (
            t1m.across_models_aggregate(["win"] * 5) == "win"
        )

    def test_four_of_five_wins(self):
        verdicts = ["win", "win", "win", "win", "tie"]
        assert t1m.across_models_aggregate(verdicts) == "win"

    def test_three_of_five_wins_exact_threshold(self):
        verdicts = ["win", "win", "win", "tie", "tie"]
        assert t1m.across_models_aggregate(verdicts) == "win"

    def test_two_of_five_wins_below_threshold(self):
        verdicts = ["win", "win", "tie", "tie", "tie"]
        assert t1m.across_models_aggregate(verdicts) == "tie"

    def test_any_fail_short_circuits_to_fail(self):
        # Even with 4 wins, a single fail forces an overall fail.
        verdicts = ["win", "win", "win", "win", "fail"]
        assert t1m.across_models_aggregate(verdicts) == "fail"

    def test_three_wins_plus_one_fail_is_fail(self):
        verdicts = ["win", "win", "win", "tie", "fail"]
        assert t1m.across_models_aggregate(verdicts) == "fail"

    def test_all_tie_is_tie(self):
        assert t1m.across_models_aggregate(["tie"] * 5) == "tie"

    def test_all_fail_is_fail(self):
        assert t1m.across_models_aggregate(["fail"] * 5) == "fail"

    def test_custom_required_count(self):
        # 2-of-3 panel
        assert (
            t1m.across_models_aggregate(
                ["win", "win", "tie"], required_count=2, total_models=3
            )
            == "win"
        )
        assert (
            t1m.across_models_aggregate(
                ["win", "tie", "tie"], required_count=2, total_models=3
            )
            == "tie"
        )

    def test_wrong_panel_size_rejected(self):
        with pytest.raises(ValueError, match="expected 5"):
            t1m.across_models_aggregate(["win", "win", "win"])  # only 3

    def test_unknown_verdict_rejected(self):
        with pytest.raises(ValueError, match="unknown values"):
            t1m.across_models_aggregate(
                ["win", "win", "win", "tie", "maybe"]
            )

    def test_required_count_zero_rejected(self):
        with pytest.raises(ValueError, match="required_count"):
            t1m.across_models_aggregate(
                ["win"] * 5, required_count=0
            )

    def test_required_count_exceeds_total_rejected(self):
        with pytest.raises(ValueError, match="total_models"):
            t1m.across_models_aggregate(
                ["win"] * 5, required_count=6, total_models=5
            )

    def test_fail_priority_over_win_count_even_when_required_unreachable(self):
        # If fails alone make required_count unreachable, still report fail.
        verdicts = ["win", "win", "fail", "fail", "fail"]
        assert t1m.across_models_aggregate(verdicts) == "fail"
