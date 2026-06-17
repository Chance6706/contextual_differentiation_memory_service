"""Spool + drain pipeline connecting fast hooks to the (model-loading) ingest path.

Lifecycle hooks must be near-instant, so they only *append* raw event JSON to an
NDJSON spool (no embedding, no model load). The drain step — run by a long-lived
process (the MCP server's heartbeat thread) or explicitly at a rest boundary —
reconstructs interaction turns from the spooled events and ingests them.

Draining uses an atomic rename so events appended during processing are never
lost: the live queue is renamed aside, processed, then deleted; new events land
in a fresh queue.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Optional

from .config import Config
from .spool import spool_event  # re-exported for backwards compatibility
from .store import MemoryService, TurnEvent

__all__ = ["spool_event", "reconstruct_turns", "drain_and_ingest"]

_ERR_MARKERS = ("error", "failed", "failure", "exception", "traceback", "fatal",
                "denied", "cannot", "not found", "no such", "panic")
_OK_MARKERS = ("passed", "success", "succeeded", "ok", "done", "completed", "0 errors")
_NEGATORS = ("no", "not", "zero", "without", "n't", "free of", "free from")
# Phrases where an _ERR token actually signals the GOOD outcome (bug is gone).
_POSITIVE_OVERRIDE = ("cannot reproduce", "can't reproduce", "cannot repro", "no longer fails",
                      "no longer errors", "works fine", "works as expected", "no errors")


def _marker_unnegated(low: str, marker: str) -> bool:
    """True if ``marker`` occurs at least once NOT immediately preceded by a negator.

    'no errors found' / 'zero failures' / 'without errors' should not count as
    failure — negation-blind matching otherwise inverts a success into a failure
    and poisons the stored valence (which the gist-relation and temperament layers
    depend on)."""
    i = low.find(marker)
    while i != -1:
        window = low[max(0, i - 10):i]
        if not any(n in window for n in _NEGATORS):
            return True
        i = low.find(marker, i + 1)
    return False


def _brief(value, limit: int = 300) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, default=str)
    s = str(value)
    return s if len(s) <= limit else s[:limit] + "…"


def _infer_success(text: str) -> Optional[bool]:
    """Best-effort, NEGATION-AWARE success inference. Deliberately conservative:
    when the signal is mixed/ambiguous it returns None (a weak/neutral signal) rather
    than guessing — an inverted guess is worse than no guess. This is a crude lexical
    proxy (the design says so) and must never be the sole driver of temperament drift."""
    low = text.lower()
    if any(p in low for p in _POSITIVE_OVERRIDE):
        return True
    has_err = any(_marker_unnegated(low, m) for m in _ERR_MARKERS)
    has_ok = any(_marker_unnegated(low, m) for m in _OK_MARKERS)
    if has_err and not has_ok:
        return False
    if has_ok and not has_err:
        return True
    return None


def reconstruct_turns(events: list[dict]) -> list[TurnEvent]:
    """Pair spooled events into ingestable turns.

    Tracks the most recent user prompt per session so each tool execution is
    anchored to the intent that triggered it.
    """
    last_prompt: dict[str, str] = {}
    last_cwd: dict[str, str] = {}
    turns: list[TurnEvent] = []

    for ev in events:
        name = ev.get("hook_event_name", "")
        sid = ev.get("session_id", "") or ""
        cwd = ev.get("cwd", "") or last_cwd.get(sid, "")
        if cwd:
            last_cwd[sid] = cwd

        if name == "UserPromptSubmit":
            prompt = ev.get("prompt") or ev.get("user_prompt") or ""
            if prompt:
                last_prompt[sid] = _brief(prompt, 500)
            continue

        if name in ("PostToolUse", "PostToolUseFailure"):
            tool = ev.get("tool_name", "") or ""
            tin = _brief(ev.get("tool_input"))
            tout = _brief(ev.get("tool_output") if ev.get("tool_output") is not None
                          else ev.get("tool_response"), 1000)
            success = ev.get("success")
            if success is None:
                success = _infer_success(f"{tin}\n{tout}")
            if name == "PostToolUseFailure":
                success = False
            turns.append(TurnEvent(
                trigger_prompt=last_prompt.get(sid, f"(tool {tool})"),
                action_taken=f"{tool}: {tin}" if tin else tool,
                outcome_feedback=tout,
                tool_name=tool,
                success=success,
                session_id=sid,
                project=cwd,
            ))
    return turns


def drain_and_ingest(cfg: Config, service: MemoryService) -> int:
    """Atomically claim the queue, reconstruct turns, and ingest them.

    Returns the number of turns ingested.
    """
    q = cfg.queue_path
    if not q.exists() or q.stat().st_size == 0:
        return 0
    # Unique claim name per drain. A single fixed ".processing" path let two
    # concurrent drains (two sessions ending/compacting at once) clobber each
    # other: drain B's os.replace overwrote the file drain A was still reading,
    # silently dropping a whole session's captured turns. With a unique name, the
    # atomic os.replace picks exactly one winner per queue snapshot; the loser
    # simply finds the queue already claimed (FileNotFoundError) and returns.
    claimed = Path(f"{q}.{os.getpid()}-{uuid.uuid4().hex[:8]}.processing")
    try:
        os.replace(q, claimed)  # atomic on Windows + POSIX
    except (FileNotFoundError, PermissionError):
        return 0

    events: list[dict] = []
    with open(claimed, "r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError:
                continue

    turns = reconstruct_turns(events)
    for t in turns:
        try:
            service.ingest(t)
        except Exception:  # never let one bad turn abort the drain
            continue

    try:
        claimed.unlink()
    except OSError:
        pass
    return len(turns)
