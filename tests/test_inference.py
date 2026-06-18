"""Regression tests for negation-aware outcome inference (Cycle-2 HIGH) and seeder
parser robustness. _infer_success feeds valence at LIVE capture (pipeline) and in
both seeders; negation-blindness inverted successes into failures and poisoned traits.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from cdms.pipeline import _infer_success

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("text, expected", [
    ("the run completed with no errors", True),     # was wrongly False (negation-blind)
    ("cannot reproduce, works fine now", True),     # positive override
    ("failed with a fatal error", False),           # genuine failure
    ("all tests passed", True),                     # genuine success
    ("here is a neutral note about the design", None),  # no signal -> neutral
    ("ran without errors", None),                   # negated err, no ok marker -> neutral (NOT False)
])
def test_infer_success_negation_aware(text, expected):
    assert _infer_success(text) is expected


def test_no_errors_is_not_a_failure():
    # The exact inversion the red-team flagged: a success phrased with resolution
    # language must not become a failure.
    assert _infer_success("no errors found, no failures") is not False


def _load_seeder():
    spec = importlib.util.spec_from_file_location("seed_from_jsonl", REPO / "tools" / "seed_from_jsonl.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_seeder_skips_non_dict_lines_without_crashing(tmp_path):
    seeder = _load_seeder()
    import json
    bad = tmp_path / "s.jsonl"
    bad.write_text("\n".join([
        json.dumps([1, 2, 3]),                                   # top-level array -> must skip
        json.dumps("a bare string"),                            # scalar -> must skip
        json.dumps({"type": "user", "sessionId": "s",
                    "message": {"content": [{"type": "text", "text": "do the thing"}]}}),
        json.dumps({"type": "assistant", "sessionId": "s",
                    "message": {"content": [{"type": "text", "text": "did the thing"},
                                            {"type": "tool_use", "name": "Bash", "input": {}}]}}),
        json.dumps({"type": "user", "sessionId": "s",
                    "message": {"content": [{"type": "tool_result", "content": "all tests passed"}]}}),
    ]), encoding="utf-8")
    turns = seeder.parse_file(bad, 1200, 0)   # must not raise on the array/scalar lines
    assert turns, "valid turns should still parse around the bad lines"
