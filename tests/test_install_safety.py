"""Regression tests for install/config safety (red-team MEDIUMs M5, M6).

  M5 — malformed config JSON must abort, never silently reset-and-overwrite
       (which destroyed the user's model/permissions/MCP approvals).
  M6 — config writes are atomic (temp + os.replace), leaving no partial file.
  Plus: install stays idempotent and preserves foreign hook entries + other keys.
"""

from __future__ import annotations

import json

import pytest

from cdms.cli import (
    _atomic_write_json,
    _install_hooks,
    _is_cdms_entry,
    _read_json_safe,
    _remove_cdms_hooks,
)


def test_malformed_json_aborts_without_overwrite(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text('{ "model": "opus", THIS IS BROKEN', encoding="utf-8")
    original = p.read_text(encoding="utf-8")
    with pytest.raises(SystemExit):
        _install_hooks(p)
    assert p.read_text(encoding="utf-8") == original  # untouched, not clobbered


def test_install_preserves_foreign_and_is_idempotent(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({
        "model": "opus",
        "permissions": {"allow": ["Bash"]},
        "hooks": {"PostToolUse": [
            {"matcher": "*", "hooks": [{"type": "command", "command": "my-foreign-linter"}]}]},
    }), encoding="utf-8")

    _install_hooks(p)
    _install_hooks(p)  # twice -> must not duplicate CDMS entries
    cfg = json.loads(p.read_text(encoding="utf-8"))

    assert cfg["model"] == "opus"
    assert cfg["permissions"] == {"allow": ["Bash"]}
    cmds = [h["command"] for e in cfg["hooks"]["PostToolUse"] for h in e["hooks"]]
    assert "my-foreign-linter" in cmds                       # foreign hook preserved
    cdms_entries = [e for e in cfg["hooks"]["PostToolUse"] if _is_cdms_entry(e)]
    assert len(cdms_entries) == 1                            # idempotent

    _remove_cdms_hooks(p)
    cfg2 = json.loads(p.read_text(encoding="utf-8"))
    post = cfg2.get("hooks", {}).get("PostToolUse", [])
    assert any("my-foreign-linter" == h["command"] for e in post for h in e["hooks"])
    assert not any(_is_cdms_entry(e) for e in post)          # only CDMS removed


def test_atomic_write_leaves_no_tmp_file(tmp_path):
    p = tmp_path / "x.json"
    _atomic_write_json(p, {"a": 1, "b": [2, 3]})
    assert json.loads(p.read_text(encoding="utf-8")) == {"a": 1, "b": [2, 3]}
    assert not (tmp_path / "x.json.cdms-tmp").exists()


def test_read_json_safe_handles_missing_and_empty(tmp_path):
    assert _read_json_safe(tmp_path / "nope.json") == {}
    empty = tmp_path / "empty.json"
    empty.write_text("   \n", encoding="utf-8")
    assert _read_json_safe(empty) == {}
