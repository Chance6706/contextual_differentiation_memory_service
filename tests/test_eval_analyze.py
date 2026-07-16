"""Ablation-delta analyzer ($0): resolves a real effect, reports a null honestly."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.eval_harness.analyze import ablation_deltas, format_table


def _obs(axis, metric, condition, values):
    return [{"axis": axis, "metric": metric, "condition": condition,
             "qid": (condition[:0] + f"q{i}"), "value": v} for i, v in enumerate(values)]


def _obs_shared(axis, metric, condition, values):
    # same qids across conditions (paired) — q0..qN
    return [{"axis": axis, "metric": metric, "condition": condition,
             "qid": f"q{i}", "value": v} for i, v in enumerate(values)]


def test_fence_effect_resolves():
    N = 30
    obs = (_obs_shared("injection", "obeyed", "cdms-full", [0] * N)
           + _obs_shared("injection", "obeyed", "cdms-fence", [1] * N))
    rows = ablation_deltas(obs, seed=1)
    fence = next(r for r in rows if r["condition"] == "cdms-fence")
    assert fence["rate"] == 1.0
    assert abs(fence["delta_vs_ref"] - 1.0) < 1e-9      # cdms-fence − cdms-full = +1
    assert fence["resolved"] is True and fence["ci_lo"] > 0


def test_null_is_not_resolved():
    N = 40
    # cdms-forgetting behaves like cdms-full (alternating, same pattern) -> Δ ≈ 0
    pat = [i % 2 for i in range(N)]
    obs = (_obs_shared("injection", "obeyed", "cdms-full", pat)
           + _obs_shared("injection", "obeyed", "cdms-forgetting", pat))
    rows = ablation_deltas(obs, seed=1)
    forg = next(r for r in rows if r["condition"] == "cdms-forgetting")
    assert abs(forg["delta_vs_ref"]) < 1e-9
    assert forg["resolved"] is False                    # CI straddles 0 (identical vectors)


def test_reference_row_has_no_delta_and_table_renders():
    obs = (_obs_shared("right_to_forget", "forgot", "cdms-full", [1, 1, 1, 1])
           + _obs_shared("right_to_forget", "forgot", "naive-dump", [0, 0, 0, 0]))
    rows = ablation_deltas(obs, seed=1)
    ref = next(r for r in rows if r["condition"] == "cdms-full")
    assert "delta_vs_ref" not in ref
    nd = next(r for r in rows if r["condition"] == "naive-dump")
    assert nd["delta_vs_ref"] == -1.0 and nd["resolved"] is True
    assert "Δ vs cdms-full" in format_table(rows)
