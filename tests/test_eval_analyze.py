"""Ablation-delta analyzer ($0): scenario-clustered CIs, honest edge cases."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.eval_harness.analyze import ablation_deltas, format_table


def _obs(axis, metric, condition, scenario, values):
    return [{"axis": axis, "metric": metric, "condition": condition, "scenario": scenario,
             "qid": f"{scenario}#{i}", "value": v} for i, v in enumerate(values)]


def test_single_scenario_delta_has_no_CI():
    # One scenario (100 reads of one store) -> a mechanism outcome, NOT a sampled CI.
    obs = (_obs("injection", "surfaced", "cdms-full", "inj", [0] * 100)
           + _obs("injection", "surfaced", "cdms-fence", "inj", [1] * 100))
    rows = ablation_deltas(obs, seed=1)
    fence = next(r for r in rows if r["condition"] == "cdms-fence")
    assert fence["delta_vs_ref"] == 1.0 and fence["n_paired_scenarios"] == 1
    assert fence["resolved"] is None and "CI-undefined" in fence["status"]
    assert "ci_lo" not in fence          # no false-tight [+1,+1]


def test_multi_scenario_consistent_effect_is_deterministic():
    # Fence flips on 3 separate scenarios -> deterministic effect (not a probabilistic CI).
    obs = []
    for s in ("a", "b", "c"):
        obs += _obs("injection", "surfaced", "cdms-full", s, [0] * 10)
        obs += _obs("injection", "surfaced", "cdms-fence", s, [1] * 10)
    fence = next(r for r in ablation_deltas(obs, seed=1) if r["condition"] == "cdms-fence")
    assert fence["n_scenarios"] == 3 and fence["delta_vs_ref"] == 1.0
    assert "deterministic across 3" in fence["status"] and fence["resolved"] is True


def test_multi_scenario_variable_effect_gets_a_real_CI():
    # Per-scenario fence effect varies (1.0, 0.5, 0.0) -> a genuine cluster-bootstrap CI.
    obs = []
    obs += _obs("injection", "surfaced", "cdms-full", "a", [0]*10) + _obs("injection","surfaced","cdms-fence","a",[1]*10)
    obs += _obs("injection", "surfaced", "cdms-full", "b", [0]*10) + _obs("injection","surfaced","cdms-fence","b",[1]*5+[0]*5)
    obs += _obs("injection", "surfaced", "cdms-full", "c", [0]*10) + _obs("injection","surfaced","cdms-fence","c",[0]*10)
    fence = next(r for r in ablation_deltas(obs, seed=1) if r["condition"] == "cdms-fence")
    assert fence["n_scenarios"] == 3 and "ci_lo" in fence
    assert 0.0 <= fence["delta_vs_ref"] <= 1.0
    assert isinstance(fence["resolved"], bool)


def test_true_null_not_resolved_and_table_renders():
    obs = []
    for s in ("a", "b", "c"):
        pat = [1, 0] * 5
        obs += _obs("injection", "surfaced", "cdms-full", s, pat) + _obs("injection", "surfaced", "cdms-forgetting", s, pat)
    forg = next(r for r in ablation_deltas(obs, seed=1) if r["condition"] == "cdms-forgetting")
    assert abs(forg["delta_vs_ref"]) < 1e-9 and forg["resolved"] is False
    assert "cluster-bootstrap over SCENARIOS" in format_table(ablation_deltas(obs, seed=1))
