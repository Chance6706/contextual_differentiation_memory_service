"""Claude Code lifecycle hook handlers.

The capture path is deterministic and extractive — it never relies on the model
choosing to call a memory tool. Each event is handled as follows:

    SessionStart      -> inject guardrails + PersonaTree gist as additionalContext
    UserPromptSubmit  -> spool (records intent for turn reconstruction)
    PreToolUse        -> spool (lightweight; optional)
    PostToolUse       -> spool the tool trajectory + outcome
    Stop              -> spool a turn boundary marker
    PreCompact        -> drain + ingest (flush session learnings before compaction)
    SessionEnd        -> drain + ingest + consolidate (the offline "dreaming" pass)

Only SessionStart/PostToolUse/UserPromptSubmit/PreToolUse may emit
``additionalContext``; SessionEnd is observational-only. We never exit 2 (block).
"""

from __future__ import annotations

import json
import sys
from typing import Any

from .config import Config, load_config

_MAX_CONTEXT = 9000  # stay under the 10K additionalContext limit


def read_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return {}


def _session_start_context(cfg: Config, payload: dict) -> str:
    """Build the read-only memory preamble injected at session start.

    Pure DB reads — no embedding model is loaded, keeping SessionStart instant.
    """
    from .salience import accessibility, age_days
    from .store import MemoryService

    svc = MemoryService(cfg)
    project = payload.get("cwd", "") or ""
    scars = [s for s in svc.db.all_scars() if not s.project or not project or s.project == project]
    gists = svc.db.top_gist(limit=12, project=project)

    # Cold-start fallback: until episodes consolidate into gist, surface the most
    # *accessible* recent episodic memories so SessionStart is useful from day one.
    recent = []
    if len(gists) < 5:
        eps = svc.db.all_episodic()
        if project:
            eps = [e for e in eps if not e.project or e.project == project]
        scored = [(accessibility(e.base_salience, age_days(e.timestamp), e.access_count, cfg), e) for e in eps]
        scored = [(a, e) for a, e in scored if a >= cfg.retention_floor]
        scored.sort(key=lambda x: x[0], reverse=True)
        recent = [e for _a, e in scored[:5]]

    if not scars and not gists and not recent:
        return ""

    lines: list[str] = ["# Persistent memory (Contextual Differentiation Memory Service)"]
    if scars:
        lines.append("\n## ⚠ Guardrails — hard-won rules from past crises (do not repeat these):")
        for s in scars[:10]:
            lines.append(f"- {s.crisis_trigger.strip()} → **{s.remediation_rule.strip()}**")
    if gists:
        lines.append("\n## What I've learned about this workspace/user (PersonaTree):")
        for g in gists:
            lines.append(f"- {g.render()}  _(support {g.support_count}, seen {g.frequency}×)_")
    if recent:
        lines.append("\n## Recent salient activity in this workspace:")
        for e in recent:
            tone = "✓" if e.valence > 0.15 else ("✗" if e.valence < -0.15 else "·")
            lines.append(f"- {tone} {e.search_text()[:140].replace(chr(10), ' ')}")
    lines.append("\n_This memory is decayed and consolidated automatically; treat it as prior belief, not ground truth._")

    text = "\n".join(lines)
    return text[:_MAX_CONTEXT]


def _emit_session_start(context: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }


def _drain(cfg: Config) -> int:
    from .pipeline import drain_and_ingest
    from .store import MemoryService

    svc = MemoryService(cfg)
    try:
        return drain_and_ingest(cfg, svc)
    finally:
        svc.close()


def _drain_and_consolidate(cfg: Config) -> dict:
    from datetime import datetime, timezone

    from .consolidate import Consolidator
    from .pipeline import drain_and_ingest
    from .store import MemoryService

    svc = MemoryService(cfg)
    try:
        ingested = drain_and_ingest(cfg, svc)
        con = Consolidator(cfg, db=svc.db, embedder=svc.embedder)
        rep = con.run(now=datetime.now(timezone.utc))
        return {"ingested": ingested, **rep.as_dict()}
    finally:
        svc.close()


def dispatch(event_name: str, payload: dict, cfg: Config | None = None) -> dict:
    """Handle one hook event. Returns the JSON object to print on stdout (or {})."""
    cfg = cfg or load_config()
    cfg.ensure_home()
    event_name = event_name or payload.get("hook_event_name", "")

    if event_name == "SessionStart":
        try:
            ctx = _session_start_context(cfg, payload)
        except Exception as exc:  # never break the session over memory
            _log(cfg, f"SessionStart context failed: {exc}")
            return {}
        return _emit_session_start(ctx) if ctx else {}

    if event_name in ("UserPromptSubmit", "PreToolUse", "PostToolUse", "PostToolUseFailure", "Stop"):
        from .spool import spool_event
        try:
            spool_event(cfg, payload)
        except Exception as exc:
            _log(cfg, f"spool failed: {exc}")
        return {}

    if event_name == "PreCompact":
        try:
            from .spool import spool_event
            spool_event(cfg, payload)
            n = _drain(cfg)
            _log(cfg, f"PreCompact flushed {n} turns")
        except Exception as exc:
            _log(cfg, f"PreCompact drain failed: {exc}")
        return {}

    if event_name == "SessionEnd":
        try:
            from .spool import spool_event
            spool_event(cfg, payload)
            rep = _drain_and_consolidate(cfg)
            _log(cfg, f"SessionEnd consolidation: {json.dumps(rep)}")
        except Exception as exc:
            _log(cfg, f"SessionEnd consolidation failed: {exc}")
        return {}

    # Unknown event: spool defensively so nothing is silently dropped.
    try:
        from .spool import spool_event
        spool_event(cfg, payload)
    except Exception:
        pass
    return {}


def _log(cfg: Config, msg: str) -> None:
    try:
        with open(cfg.log_path, "a", encoding="utf-8") as f:
            from .models import utc_now_iso
            f.write(f"{utc_now_iso()} {msg}\n")
    except OSError:
        pass


def run_hook(event_name: str) -> int:
    """Entry point used by the CLI: read stdin, dispatch, print response, exit 0."""
    payload = read_payload()
    response = dispatch(event_name, payload)
    if response:
        sys.stdout.write(json.dumps(response))
    return 0
