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
import time
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
        # Look at the few WORDS immediately before the marker, not a fixed 10-char
        # window — the 10-char window missed common multi-word negators ("without any
        # errors", "no further exceptions") and flipped a success to a failure (Cycle-5
        # C-MED-6). Bounded to the last 3 words so a negator further back ("no backups;
        # the deploy failed") does NOT wrongly negate the marker.
        window = " ".join(low[:i].split()[-3:])
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
    has_override = any(p in low for p in _POSITIVE_OVERRIDE)
    # The override is no longer an UNCONDITIONAL short-circuit. It used to return
    # True the instant any override phrase appeared, so "no errors BUT the test
    # failed" / "...actually the deploy failed catastrophically" inverted a real
    # failure into a confident success (poisoning stored valence). Instead, strip
    # the override phrases (so their internal err-words — "no errors", "cannot
    # reproduce", "no longer fails" — don't read as failures), then check for a
    # SEPARATE, still-present failure marker in the remainder.
    residual = low
    for p in _POSITIVE_OVERRIDE:
        residual = residual.replace(p, " ")
    has_err = any(_marker_unnegated(residual, m) for m in _ERR_MARKERS)
    has_ok = any(_marker_unnegated(low, m) for m in _OK_MARKERS)
    if has_override and not has_err:
        return True
    if has_err and not has_ok:
        return False
    if has_ok and not has_err:
        return True
    return None


def iter_turns(events):
    """Stream spooled events into ingestable turns (generator).

    Tracks the most recent user prompt per session so each tool execution is
    anchored to the intent that triggered it. Streaming (rather than building a
    full ``turns`` list) keeps drain memory O(per-session state), not O(spool
    size) — a large backlog otherwise inflated RSS to ~8x the spool on drain.

    Non-dict events (a valid-JSON-but-wrong-type spool line: ``42``, ``[1,2]``,
    ``"str"``) are skipped, not crashed on — one such line previously aborted the
    whole drain via ``ev.get`` and destroyed an entire session's captured turns.
    """
    last_prompt: dict[str, str] = {}
    last_cwd: dict[str, str] = {}

    for ev in events:
        if not isinstance(ev, dict):
            continue
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
            yield TurnEvent(
                trigger_prompt=last_prompt.get(sid, f"(tool {tool})"),
                action_taken=f"{tool}: {tin}" if tin else tool,
                outcome_feedback=tout,
                tool_name=tool,
                success=success,
                session_id=sid,
                project=cwd,
            )


def reconstruct_turns(events: list[dict]) -> list[TurnEvent]:
    """List form of :func:`iter_turns` (kept for tests / seeders)."""
    return list(iter_turns(events))


def _stream_spool(path: Path):
    """Yield parsed dict events from an NDJSON spool, one line at a time, skipping
    blank/unparseable lines. Streaming keeps drain memory bounded on a big backlog."""
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue


def _ingest_claim(claimed: Path, service: MemoryService) -> int:
    """Reconstruct + ingest one claimed spool file, then remove it. The claim is
    unlinked in `finally` so a reconstruction error never STRANDS it (the orphan
    reclaim handles the process-death case instead)."""
    ingested = 0
    try:
        for t in iter_turns(_stream_spool(claimed)):
            try:
                service.ingest(t)
            except Exception:  # never let one bad turn abort the drain
                continue
            ingested += 1
    finally:
        try:
            claimed.unlink()
        except OSError:
            pass
    return ingested


_RECLAIM_AGE_SECONDS = 3600  # reclaim a .processing claim older than this regardless of pid


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        return True  # exists but not ours -> treat as alive (don't steal)


def _is_orphan(path: Path) -> bool:
    """A claim is an orphan (its drain died) if the owning pid is gone, or it is
    older than the reclaim age (covers pid reuse). A fresh claim held by a live
    drain — including a sibling thread in this process — is left alone."""
    try:
        age = time.time() - path.stat().st_mtime
    except OSError:
        return False
    if age >= _RECLAIM_AGE_SECONDS:
        return True
    name = path.name
    try:
        # ...episodic_queue.ndjson.<pid>-<hex>.processing
        pid = int(name.rsplit(".processing", 1)[0].rsplit(".", 1)[1].split("-", 1)[0])
    except (ValueError, IndexError):
        return False  # can't identify owner and not old yet -> don't touch
    return not _pid_alive(pid)


def _reclaim_orphans(cfg: Config, service: MemoryService) -> int:
    """Re-ingest spool claims stranded by a drain that was killed after claiming
    but before finishing (e.g. a hook SIGKILLed at its timeout). Without this, the
    killed session's turns are lost forever — never ingested, never retried."""
    total = 0
    pattern = cfg.queue_path.name + ".*.processing"
    for path in sorted(cfg.queue_path.parent.glob(pattern)):
        if not _is_orphan(path):
            continue
        mine = Path(f"{cfg.queue_path}.{os.getpid()}-{uuid.uuid4().hex[:8]}.processing")
        try:
            os.replace(path, mine)  # atomic claim; a racing reclaimer misses
        except (FileNotFoundError, PermissionError, OSError):
            continue
        total += _ingest_claim(mine, service)
    return total


# Drain waits at most this long for the cross-process lock before skipping (the spool
# is untouched until the lock is held, so a skipped drain is reclaimed by the next one).
# Short so a hook can't hang waiting on a long consolidation.
_DRAIN_LOCK_TIMEOUT = 10.0


def drain_and_ingest(cfg: Config, service: MemoryService) -> int:
    """Atomically claim the queue, reconstruct turns, and ingest them.

    Held under the cross-process lock (Cycle-5 C-HIGH-1 / C-HIGH-3): without it a drain
    could ingest episodes into a store mid-consolidation, so consolidation clusters from a
    stale snapshot (missing/duplicate gists) and ingest's `_associate` salience writes race
    consolidation's renormalization. Serializing drain against consolidation/forget closes
    both. On lock timeout we SKIP (the spool's atomic claim only happens inside the lock, so
    nothing is lost — the next drain reclaims it) rather than hang the hook.
    """
    from .lock import cross_process_lock
    try:
        with cross_process_lock(cfg.lock_path, timeout=_DRAIN_LOCK_TIMEOUT):
            return _drain_locked(cfg, service)
    except TimeoutError:
        return 0


def _drain_locked(cfg: Config, service: MemoryService) -> int:
    total = _reclaim_orphans(cfg, service)
    q = cfg.queue_path
    if not q.exists() or q.stat().st_size == 0:
        return total
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
        return total
    return total + _ingest_claim(claimed, service)
