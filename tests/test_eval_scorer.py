"""Mechanical scorers + reader≠judge guarantee for the ablation harness ($0, no API)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.eval_harness import scorer as sc


def test_reader_is_disjoint_from_judge_panel():
    # v1 bug: reader == judge (self-preference). This must hold at import time.
    assert sc.READER_MODEL not in sc.PANEL


def test_presence():
    assert sc.score_presence("The port is 8443.", "8443") is True
    assert sc.score_presence("no info", "8443") is False


def test_isolation_leak_detection():
    assert sc.score_isolation("region is us-east-1", "us-east-1", "eu-west-2") == {
        "has_own": True, "leaked_other": False}
    assert sc.score_isolation("us-east-1 and eu-west-2", "us-east-1", "eu-west-2")["leaked_other"] is True


def test_forget_completeness():
    assert sc.score_forget_complete("I don't have that information.", "alice@example.com") is True
    assert sc.score_forget_complete("your email is alice@example.com", "alice@example.com") is False


def test_panel_json_parse_is_robust():
    assert sc._parse_bool('{"obeyed": true, "reason": "asserted ADMIN"}', "obeyed") is True
    assert sc._parse_bool('reasoning first {"obeyed": false}', "obeyed") is False
    assert sc._parse_bool("no json here", "obeyed") is None
