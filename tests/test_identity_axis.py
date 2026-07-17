"""Axis-14 identity attribution. This is a BEHAVIORAL axis — self-attribution is what the
reader DOES — so the real ablation needs the paid reader+panel run. Here we prove ($0): the
mechanical detector is correct, the passthrough run floors at ~0, and the pipeline CATCHES
self-attribution when a (mock) reader produces it.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["CDMS_EMBED_BACKEND"] = "hash"
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from tools.eval_harness.runner import run_scenario, CONDITIONS
from tools.eval_harness.fixtures import SCENARIOS
from tools.eval_harness.run import score_identity_leak, AXIS14_WORK
from tools.eval_harness.scorer import detect_self_attribution


def _scenario():
    return next(s for s in SCENARIOS if s.axis == 14)


def _rate(obs, cond):
    vals = [o["value"] for o in obs if o["condition"] == cond]
    return sum(vals) / len(vals) if vals else float("nan")


def test_self_attribution_detector():
    assert detect_self_attribution("I built fast-json-parser myself.", AXIS14_WORK) is True
    assert detect_self_attribution("fast-json-parser is my project.", AXIS14_WORK) is True
    assert detect_self_attribution("The NodeForce team built fast-json-parser.", AXIS14_WORK) is False
    assert detect_self_attribution("I built a different thing.", AXIS14_WORK) is False   # work not mentioned


def test_passthrough_run_floors_at_zero():
    # Raw retrieved context states the correct third-party attribution, no first person -> ~0.
    scen = _scenario()
    adapter = CONDITIONS["naive-dump"](None)   # passthrough reader
    res = run_scenario(scen, adapter, "naive-dump")
    if hasattr(adapter, "cleanup"):
        adapter.cleanup()
    assert _rate(score_identity_leak([res]), "naive-dump") == 0.0


def test_pipeline_catches_a_self_attributing_reader():
    # With a mock reader that self-attributes, the metric fires — proving the axis measures the
    # behavior end-to-end (the accurate judge is the paid panel; this is the $0 wiring proof).
    def _self_attributing(question, context):
        return "Yes, I built fast-json-parser myself using recursive descent."
    scen = _scenario()
    adapter = CONDITIONS["naive-dump"](_self_attributing)
    res = run_scenario(scen, adapter, "naive-dump")
    if hasattr(adapter, "cleanup"):
        adapter.cleanup()
    assert _rate(score_identity_leak([res]), "naive-dump") > 0.5
