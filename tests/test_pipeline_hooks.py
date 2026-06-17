import json

from cdms.hooks import dispatch
from cdms.pipeline import (
    _infer_success,
    drain_and_ingest,
    reconstruct_turns,
    spool_event,
)
from cdms.store import MemoryService, TurnEvent


def test_infer_success():
    assert _infer_success("2 failed: traceback") is False
    assert _infer_success("all tests passed, ok") is True
    assert _infer_success("neutral output") is None


def test_reconstruct_pairs_prompt_with_tool():
    events = [
        {"hook_event_name": "UserPromptSubmit", "session_id": "s", "cwd": "C:/p", "prompt": "fix the bug"},
        {"hook_event_name": "PostToolUse", "session_id": "s", "cwd": "C:/p",
         "tool_name": "Edit", "tool_input": {"file": "a.py"}, "tool_output": "applied"},
    ]
    turns = reconstruct_turns(events)
    assert len(turns) == 1
    assert turns[0].trigger_prompt == "fix the bug"
    assert turns[0].tool_name == "Edit"
    assert turns[0].project == "C:/p"


def test_post_tool_failure_marks_unsuccessful():
    events = [{"hook_event_name": "PostToolUseFailure", "session_id": "s",
               "tool_name": "Bash", "tool_input": {}, "tool_output": "boom"}]
    turns = reconstruct_turns(events)
    assert turns[0].success is False


def test_spool_and_drain(cfg):
    spool_event(cfg, {"hook_event_name": "UserPromptSubmit", "session_id": "s", "prompt": "do x"})
    spool_event(cfg, {"hook_event_name": "PostToolUse", "session_id": "s",
                      "tool_name": "Write", "tool_input": {"f": "x"}, "tool_output": "done"})
    svc = MemoryService(cfg)
    n = drain_and_ingest(cfg, svc)
    assert n == 1
    assert svc.db.stats()["episodic"] == 1
    # queue consumed
    assert not cfg.queue_path.exists() or cfg.queue_path.stat().st_size == 0
    svc.close()


def test_session_start_injects_scar(cfg):
    svc = MemoryService(cfg)
    svc.pin_scar("ran a dangerous command", "always confirm destructive ops", project="C:/p")
    svc.close()
    out = dispatch("SessionStart", {"hook_event_name": "SessionStart", "cwd": "C:/p"}, cfg)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "Guardrails" in ctx
    assert "confirm destructive ops" in ctx


def test_session_start_empty_returns_nothing(cfg):
    out = dispatch("SessionStart", {"hook_event_name": "SessionStart", "cwd": "C:/empty"}, cfg)
    assert out == {}


def test_dispatch_posttooluse_spools(cfg):
    dispatch("PostToolUse", {"hook_event_name": "PostToolUse", "session_id": "s",
                             "tool_name": "Read", "tool_input": {}, "tool_output": "x"}, cfg)
    assert cfg.queue_path.exists()
    assert cfg.queue_path.stat().st_size > 0
