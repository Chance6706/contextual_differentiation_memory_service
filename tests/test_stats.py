"""Tests for the measurement-precision primitives (Thread 3).

Known-answer checks where a closed form exists (Wilson interval, mean/SE), coverage and
degeneracy checks for the bootstrap, and property checks for the overlap shuffle baseline
(disjoint vocab -> meaningful; huge vocab -> chance overlap ~0 -> inconclusive; determinism).
"""

import math

import numpy as np
import pytest

from cdms.stats import (
    bootstrap_ci,
    mean_se,
    overlap_significance,
    pooled_overlap_baseline,
    wilson_interval,
)


# --------------------------------------------------------------------------- #
# mean_se
# --------------------------------------------------------------------------- #
def test_mean_se_known_values():
    m, se = mean_se([1, 2, 3, 4, 5])
    assert m == pytest.approx(3.0)
    # sample sd = 1.58114; se = sd/sqrt(5)
    assert se == pytest.approx(1.5811388 / math.sqrt(5), rel=1e-6)


def test_mean_se_degenerate():
    assert mean_se([]) == (0.0, 0.0)
    assert mean_se([7.0]) == (7.0, 0.0)


# --------------------------------------------------------------------------- #
# wilson_interval
# --------------------------------------------------------------------------- #
def test_wilson_known_50_of_100():
    p, lo, hi = wilson_interval(50, 100)
    assert p == 0.5
    assert lo == pytest.approx(0.4038, abs=1e-3)   # textbook Wilson 95% for 50/100
    assert hi == pytest.approx(0.5962, abs=1e-3)


def test_wilson_extremes_stay_in_unit_interval():
    # Wald would give a degenerate zero-width interval at p=0/1; Wilson must not.
    p0, lo0, hi0 = wilson_interval(0, 10)
    assert p0 == 0.0 and lo0 == pytest.approx(0.0, abs=1e-9) and 0.0 < hi0 < 1.0
    p1, lo1, hi1 = wilson_interval(10, 10)
    assert p1 == 1.0 and hi1 == pytest.approx(1.0, abs=1e-9) and 0.0 < lo1 < 1.0


def test_wilson_n_zero():
    assert wilson_interval(0, 0) == (0.0, 0.0, 0.0)


def test_wilson_narrows_with_n():
    _, lo_small, hi_small = wilson_interval(5, 10)
    _, lo_big, hi_big = wilson_interval(500, 1000)
    assert (hi_big - lo_big) < (hi_small - lo_small)  # same rate 0.5, larger n -> tighter


# --------------------------------------------------------------------------- #
# bootstrap_ci
# --------------------------------------------------------------------------- #
def test_bootstrap_constant_is_degenerate():
    point, lo, hi = bootstrap_ci([4.0, 4.0, 4.0, 4.0])
    assert point == lo == hi == 4.0


def test_bootstrap_single_value():
    assert bootstrap_ci([2.5]) == (2.5, 2.5, 2.5)


def test_bootstrap_ci_brackets_point_and_is_deterministic():
    rng = np.random.default_rng(123)
    data = rng.normal(10.0, 2.0, size=200).tolist()
    point, lo, hi = bootstrap_ci(data, seed=42)
    assert lo < point < hi
    # determinism: same seed -> identical interval
    assert bootstrap_ci(data, seed=42) == (point, lo, hi)
    # the CI for a mean of ~200 N(10,2) points should be tight and contain 10
    assert lo < 10.0 < hi
    assert (hi - lo) < 1.5


def test_bootstrap_supports_other_statistics():
    data = list(range(1, 101))
    point, lo, hi = bootstrap_ci(data, seed=1, statistic=np.median)
    assert lo <= point <= hi
    assert point == pytest.approx(50.5, abs=1.0)


# --------------------------------------------------------------------------- #
# overlap shuffle baseline
# --------------------------------------------------------------------------- #
def test_pooled_baseline_disjoint_vocab_has_chance_overlap():
    # 4 groups of 10 drawn from a pool of only 40 distinct traits: independent draws WILL
    # collide, so the null mean overlap is clearly positive.
    null_mean, null_sd, dist = pooled_overlap_baseline([10, 10, 10, 10], vocab_size=40, n_trials=2000, seed=0)
    assert null_mean > 0.05
    assert null_sd > 0.0
    assert dist.shape == (2000,)


def test_observed_zero_overlap_is_meaningful_against_small_vocab():
    # Observed 0.00 overlap when chance (small shared pool) would give ~0.14 -> meaningful.
    res = overlap_significance(0.0, [10, 10, 10, 10], vocab_size=40, n_trials=2000, seed=0)
    assert res["null_mean"] > 0.05
    assert res["z"] <= -2.0
    assert res["verdict"] == "meaningful"
    assert res["percentile"] < 0.05


def test_observed_zero_overlap_is_inconclusive_against_huge_vocab():
    # If the vocabulary is enormous relative to group size, chance overlap ~0, so observing 0
    # tells us nothing — the baseline correctly reports inconclusive (no false significance).
    res = overlap_significance(0.0, [10, 10, 10, 10], vocab_size=100_000, n_trials=2000, seed=0)
    assert res["null_mean"] < 0.01
    assert res["verdict"] != "meaningful"


def test_overlap_baseline_is_deterministic():
    a = overlap_significance(0.0, [8, 12, 10], vocab_size=50, n_trials=1000, seed=7)
    b = overlap_significance(0.0, [8, 12, 10], vocab_size=50, n_trials=1000, seed=7)
    assert a == b
