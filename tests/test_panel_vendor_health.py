"""Lock tests for the calibrated vendor-health check (DISAMBIG D-F3 fix)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from panel_vendor_health import CALIBRATION, vendor_degenerate, ABSOLUTE_COLLAPSE  # noqa: E402


def test_disambig_h_deepseek_false_alarm_now_healthy():
    # The exact D-F3 case: deepseek 0.9511 with 4 labels in a BEM-mix arm.
    bad, reason = vendor_degenerate("deepseek", 0.9511, 4, "bem-mix")
    assert not bad, reason


def test_cons_p2_deepseek_committed_max_healthy():
    # The committed healthy max itself must not trip its own line.
    bad, _ = vendor_degenerate("deepseek", 0.9606, 3, "bem-mix")
    assert not bad


def test_per_vendor_drift_line_trips():
    # deepseek above committed max + margin -> degenerate.
    bad, reason = vendor_degenerate("deepseek", 0.9810, 3, "bem-mix")
    assert bad and "drift line" in reason
    # mistral (low baseline 0.7805) trips far earlier than deepseek would.
    bad, _ = vendor_degenerate("mistral", 0.8100, 4, "bem-mix")
    assert bad


def test_single_label_always_degenerate():
    bad, reason = vendor_degenerate("claude", 0.60, 1, "bem-mix")
    assert bad and "single label" in reason


def test_absolute_collapse_line():
    # Above 0.995 trips even for a vendor whose baseline+margin exceeds it (recall-only claude
    # baseline 0.9939 + 0.02 > 0.995: the absolute line must dominate).
    bad, reason = vendor_degenerate("claude", 0.9960, 3, "recall-only")
    assert bad and "collapse" in reason
    bad, _ = vendor_degenerate("claude", 0.9939, 3, "recall-only")
    assert not bad


def test_unknown_vendor_falls_back_to_absolute_rules():
    bad, reason = vendor_degenerate("newvendor", 0.9700, 3, "bem-mix")
    assert not bad and "no committed baseline" in reason
    bad, _ = vendor_degenerate("newvendor", 0.9960, 3, "bem-mix")
    assert bad


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        vendor_degenerate("claude", 0.5, 3, "mixed")


def test_calibration_table_shape():
    assert set(CALIBRATION) == {"bem-mix", "recall-only"}
    for kind, d in CALIBRATION.items():
        assert set(d) == {"claude", "deepseek", "gemini", "gpt", "mistral"}
        for v, s in d.items():
            assert 0.5 < s < ABSOLUTE_COLLAPSE, (kind, v, s)
