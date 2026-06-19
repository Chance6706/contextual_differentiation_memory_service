"""Cycle 9 — salience/budget config-correctness fixes (PR A).

#3: allocate_capped_proportional enforces the per-key cap as a HARD invariant. When the
    cap is infeasible (cap * m < budget) the old code fell back to an equal split of
    `remaining / m`, which *exceeds* the cap — the very thing the cap exists to prevent.
    The fix hands each positive-weight key exactly `cap` and leaves the remainder
    unallocated. Default project/session caps (0.5) are always feasible for m >= 2, so
    default budgets are unaffected and still conserve the full total.

#4: the H-2 anti-bypass that scales S0 weights down (so a zero-goal memory can't self-
    elevate to crisis) must not, for a pathologically tiny crisis_threshold, round every
    weight to zero — that silently DISABLES salience (S0 == 0 for every episode). The
    threshold, not the weights, is the offender: it gets repaired and the scale re-derived.

#7: assoc_eta and assoc_boost_cap_frac are a learning rate / fraction-of-self and must be
    <= 1.0. The old 1e3 ceiling let one write inject ~100x K_budget via the associative
    boost and silently neutered the M-M-3 boost cap.
"""

from __future__ import annotations

import pytest

from cdms.config import Config, load_config
from cdms.salience import allocate_capped_proportional


# --- #3: allocate_capped_proportional enforces the cap ----------------------- #
def test_3_infeasible_cap_is_enforced_not_equal_split():
    # cap = 0.2, three positive keys: cap * 3 = 0.6 < 1.0 => infeasible.
    # Old fallback gave each remaining/m = 0.333 > cap. The fix must cap each at 0.2.
    alloc = allocate_capped_proportional({"a": 1.0, "b": 1.0, "c": 1.0}, total=1.0, cap_fraction=0.2)
    cap = 0.2
    assert max(alloc.values()) <= cap + 1e-9, f"per-key cap violated: {alloc}"
    assert sum(alloc.values()) <= 1.0 + 1e-9          # remainder left unallocated, never over-spent
    assert all(abs(v - cap) < 1e-9 for v in alloc.values())


def test_3_infeasible_cap_zero_weight_key_still_gets_nothing():
    alloc = allocate_capped_proportional({"a": 1.0, "b": 1.0, "c": 0.0}, total=1.0, cap_fraction=0.2)
    assert alloc["c"] == 0.0                            # zero-weight key never receives a share
    assert alloc["a"] <= 0.2 + 1e-9 and alloc["b"] <= 0.2 + 1e-9
    assert sum(alloc.values()) <= 1.0 + 1e-9


def test_3_feasible_default_cap_still_conserves_total():
    # Regression guard: the default 0.5 cap is feasible for n >= 2, so the whole budget
    # is still distributed (no behavior change for real configs).
    alloc = allocate_capped_proportional({"a": 1.0, "b": 1.0}, total=1.0, cap_fraction=0.5)
    assert abs(sum(alloc.values()) - 1.0) < 1e-9
    assert max(alloc.values()) <= 0.5 + 1e-9


# --- #4: tiny crisis_threshold must not zero the S0 weights ------------------- #
def test_4_tiny_crisis_threshold_does_not_disable_salience(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_CRISIS_THRESHOLD", "1e-7")   # in-range (<= 1e6) but pathological
    cfg = load_config()
    wsum = cfg.w_surprise + cfg.w_contingency + cfg.w_self_ref + cfg.w_affect
    assert wsum > 0.0, "S0 weights rounded to zero -> salience disabled"
    # The real offender was repaired, restoring the invariant.
    assert cfg.crisis_threshold == Config().crisis_threshold
    assert cfg.goal_gate_floor * wsum < cfg.crisis_threshold


def test_4_tiny_crisis_threshold_with_huge_weights_rescales_after_repair(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_CRISIS_THRESHOLD", "1e-7")
    for ev in ("CDMS_W_SURPRISE", "CDMS_W_CONTINGENCY", "CDMS_W_SELF_REF", "CDMS_W_AFFECT"):
        monkeypatch.setenv(ev, "10")                      # each at the per-field cap
    cfg = load_config()
    wsum = cfg.w_surprise + cfg.w_contingency + cfg.w_self_ref + cfg.w_affect
    assert wsum > 0.0
    assert cfg.crisis_threshold == Config().crisis_threshold
    # After repairing the threshold, the weights are scaled so a zero-goal memory stays sub-crisis.
    assert cfg.goal_gate_floor * wsum < cfg.crisis_threshold


def test_4_sane_tight_threshold_still_scales_weights(monkeypatch, tmp_path):
    # A non-pathological-but-tight threshold must still trigger the original H-2 scaling
    # (this path must not be broken by the #4 collapse-guard).
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_CRISIS_THRESHOLD", "1.0")
    for ev in ("CDMS_W_SURPRISE", "CDMS_W_CONTINGENCY", "CDMS_W_SELF_REF", "CDMS_W_AFFECT"):
        monkeypatch.setenv(ev, "10")
    cfg = load_config()
    wsum = cfg.w_surprise + cfg.w_contingency + cfg.w_self_ref + cfg.w_affect
    assert cfg.crisis_threshold == 1.0                    # sane threshold preserved
    assert cfg.goal_gate_floor * wsum < cfg.crisis_threshold


# --- #7: tightened associative caps ------------------------------------------ #
def test_7_assoc_eta_above_one_clamped_to_default(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_ASSOC_ETA", "100")           # was allowed (<= 1e3)
    assert load_config().assoc_eta == Config().assoc_eta


def test_7_assoc_boost_cap_frac_above_one_clamped_to_default(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_ASSOC_BOOST_CAP_FRAC", "50")
    assert load_config().assoc_boost_cap_frac == Config().assoc_boost_cap_frac


def test_7_sane_assoc_values_preserved(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_ASSOC_ETA", "0.8")
    monkeypatch.setenv("CDMS_ASSOC_BOOST_CAP_FRAC", "0.9")
    cfg = load_config()
    assert cfg.assoc_eta == 0.8 and cfg.assoc_boost_cap_frac == 0.9
