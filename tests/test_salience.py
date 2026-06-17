import math

from cdms.config import Config
from cdms.salience import (
    SalienceSignals,
    accessibility,
    age_days,
    allocate_capped_proportional,
    compute_s0,
    conserve_budget,
    hierarchical_competition,
    softmax,
)


def test_capped_proportional_caps_dominant_and_redistributes():
    # a project that wants 75% is capped at 50%; excess goes to the others
    alloc = allocate_capped_proportional({"big": 75, "mid": 17.5, "small": 7.5}, 1000.0, 0.5)
    assert math.isclose(sum(alloc.values()), 1000.0, rel_tol=1e-9)
    assert alloc["big"] <= 500.0 + 1e-6                 # capped at 50%
    assert math.isclose(alloc["big"], 500.0, rel_tol=1e-6)
    assert alloc["mid"] > 175.0                          # mid gained from redistribution
    assert alloc["small"] > 75.0


def test_capped_proportional_uncapped_when_under_cap():
    # nobody exceeds the cap -> plain proportional
    alloc = allocate_capped_proportional({"a": 1, "b": 1, "c": 1}, 900.0, 0.5)
    for v in alloc.values():
        assert math.isclose(v, 300.0, rel_tol=1e-9)


def test_capped_proportional_single_project_gets_all():
    assert allocate_capped_proportional({"only": 5}, 1000.0, 0.5) == {"only": 1000.0}


def test_decay_halflife():
    cfg = Config()
    s0 = 1.0
    assert accessibility(s0, 0.0, 0, cfg) == s0                      # t=0, no reinforcement
    half = accessibility(s0, cfg.decay_halflife_days, 0, cfg)
    assert math.isclose(half, 0.5, rel_tol=1e-6)                     # one half-life -> 0.5


def test_reinforcement_cap():
    cfg = Config()
    # many accesses saturate at the cap, not unbounded geometric growth
    big = accessibility(1.0, 0.0, 1000, cfg)
    assert math.isclose(big, cfg.reinforce_cap, rel_tol=1e-9)


def test_s0_goal_veto():
    cfg = Config()
    sig = SalienceSignals(goal=1.0, surprise=1.0, contingency=1.0, self_ref=1.0, affect=1.0)
    full = compute_s0(sig, cfg)
    sig_low = SalienceSignals(goal=0.0, surprise=1.0, contingency=1.0, self_ref=1.0, affect=1.0)
    vetoed = compute_s0(sig_low, cfg)
    assert vetoed < full
    # goal floor keeps it from annihilating entirely
    assert vetoed == cfg.goal_gate_floor * full / 1.0 or vetoed > 0


def test_affect_magnitude_only():
    cfg = Config()
    pos = compute_s0(SalienceSignals(affect=0.8), cfg)
    neg = compute_s0(SalienceSignals(affect=-0.8), cfg)
    assert math.isclose(pos, neg)   # only |affect| drives memorability


def test_conserved_budget_sums_to_constant_and_preserves_ratio():
    vals = [1.0, 2.0, 3.0, 4.0]
    out = conserve_budget(vals, 100.0)
    assert math.isclose(sum(out), 100.0, rel_tol=1e-9)
    # proportional (SHY-style) downscaling preserves ratios
    assert math.isclose(out[1] / out[0], 2.0, rel_tol=1e-9)
    assert math.isclose(out[3] / out[0], 4.0, rel_tol=1e-9)


def test_softmax_normalized():
    out = softmax([1.0, 2.0, 3.0])
    assert math.isclose(sum(out), 1.0, rel_tol=1e-9)
    assert out[2] > out[1] > out[0]


def test_hierarchical_competition_keys():
    grouped = {
        "s1": [("a", 1.0), ("b", 3.0)],
        "s2": [("c", 2.0)],
    }
    comp = hierarchical_competition(grouped)
    assert set(comp.keys()) == {"a", "b", "c"}
    assert comp["b"] > comp["a"]   # local winner in s1 scores higher


def test_age_days_parsing():
    assert age_days("not-a-date") == 0.0
