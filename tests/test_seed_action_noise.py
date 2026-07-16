"""The seeder no longer bakes tool-call ARGS into the ingested action text —
those args were the dominant object-keyword noise (command/bash/file_path…) and
a raw credential surface. It keeps the assistant's words + the tool names only.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

_TOOL = pathlib.Path(__file__).resolve().parents[1] / "tools" / "seed_from_jsonl.py"


def _load_seeder():
    spec = importlib.util.spec_from_file_location("seed_from_jsonl", _TOOL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _transcript(tmp_path, events):
    p = tmp_path / "session.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    return p


def test_action_keeps_tool_names_drops_args_and_secrets(tmp_path):
    seed = _load_seeder()
    secret = "eyJhIjoiZGVhZGJlZWYiLCJ0IjoiMTIzNDU2Nzg5MCJ9longblobtoken"
    events = [
        {"type": "user", "message": {"content": "set up the tunnel please"},
         "timestamp": "2026-01-01T00:00:00Z", "sessionId": "s1"},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Installing the tunnel."},
            {"type": "tool_use", "name": "Bash",
             "input": {"command": f"cloudflared service install {secret}"}},
        ]}, "timestamp": "2026-01-01T00:00:01Z", "sessionId": "s1"},
    ]
    turns = seed.parse_file(_transcript(tmp_path, events), mc=1200)
    assert turns, "expected a reconstructed turn"
    act = turns[0].action_taken
    assert "Bash" in act                    # tool name kept (light signal)
    assert "Installing the tunnel" in act   # assistant's substantive words kept
    assert secret not in act                # arg payload (credential) gone
    assert "command" not in act             # arg-key keyword noise gone


def test_pure_tool_turn_keeps_name_not_args(tmp_path):
    # An assistant turn that is only a tool call keeps the tool name (so it isn't
    # dropped as empty) but carries no args.
    seed = _load_seeder()
    events = [
        {"type": "user", "message": {"content": "read the file"},
         "timestamp": "2026-01-01T00:00:00Z", "sessionId": "s1"},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/etc/secret.txt"}},
        ]}, "timestamp": "2026-01-01T00:00:01Z", "sessionId": "s1"},
    ]
    turns = seed.parse_file(_transcript(tmp_path, events), mc=1200)
    assert turns and turns[0].action_taken == "Read"
    assert "file_path" not in turns[0].action_taken and "secret" not in turns[0].action_taken


def test_nameless_tool_block_no_dangling_parens(tmp_path):
    # A malformed tool_use with no `name` + assistant text must NOT yield "text ()".
    seed = _load_seeder()
    events = [
        {"type": "user", "message": {"content": "do the thing"},
         "timestamp": "2026-01-01T00:00:00Z", "sessionId": "s1"},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Working on it."},
            {"type": "tool_use", "input": {"x": 1}},   # no "name" key
        ]}, "timestamp": "2026-01-01T00:00:01Z", "sessionId": "s1"},
    ]
    turns = seed.parse_file(_transcript(tmp_path, events), mc=1200)
    assert turns and turns[0].action_taken == "Working on it."
    assert "()" not in turns[0].action_taken
