"""Seed a CDMS store from a Hermes agent message DB (real historical sessions).

Reads ``hermes/state.db`` read-only, reconstructs user->assistant->tool turns
with their REAL timestamps (so the Ebbinghaus decay curve is actually exercised),
and ingests them into a CDMS store. Raw conversation text stays on disk — only
aggregate progress is printed.

Usage:
    python tools/seed_from_hermes.py --db <path> --home <cdms_home> [--limit N]
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# allow running from repo root without install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cdms.config import Config            # noqa: E402
from cdms.store import MemoryService, TurnEvent  # noqa: E402

_ERR = ("error", "failed", "failure", "exception", "traceback", "fatal", "denied",
        "cannot", "no such", "not found")
_OK = ("passed", "success", "succeeded", "completed", "done", "ok", "fixed", "merged")


def to_iso(ts) -> str | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)) or (isinstance(ts, str) and ts.strip().lstrip("-").isdigit()):
        v = float(ts)
        if v > 1e12:      # milliseconds
            v /= 1000.0
        try:
            return datetime.fromtimestamp(v, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, OSError):
            return None
    s = str(ts).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def text_of(content) -> str:
    """Hermes content may be plain text or a JSON list of blocks."""
    if content is None:
        return ""
    s = str(content)
    if s[:1] in "[{":
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            return s
        parts = []
        if isinstance(obj, list):
            for b in obj:
                if isinstance(b, dict):
                    parts.append(b.get("text") or b.get("content") or "")
                else:
                    parts.append(str(b))
        elif isinstance(obj, dict):
            parts.append(obj.get("text") or obj.get("content") or s)
        return " ".join(p for p in parts if p).strip() or s
    return s


def infer_success(text: str):
    low = text.lower()
    e = any(m in low for m in _ERR)
    o = any(m in low for m in _OK)
    if e and not o:
        return False
    if o and not e:
        return True
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/AppData/Local/hermes/state.db"))
    ap.add_argument("--home", required=True, help="CDMS_HOME for the seed store")
    ap.add_argument("--limit", type=int, default=0, help="max turns (0 = all)")
    ap.add_argument("--max-chars", type=int, default=1200)
    args = ap.parse_args()

    cfg = Config(home=Path(os.path.abspath(args.home)))
    cfg.ensure_home()
    svc = MemoryService(cfg)

    src = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    sessions = {r["id"]: (r["title"] or r["id"]) for r in src.execute("SELECT id, title FROM sessions")}

    rows = src.execute(
        "SELECT session_id, role, content, tool_name, tool_calls, timestamp "
        "FROM messages ORDER BY session_id, timestamp, id"
    ).fetchall()

    turns = 0
    last_user: dict[str, str] = {}
    pending: dict | None = None
    t0 = time.time()
    mc = args.max_chars

    def flush(p):
        nonlocal turns
        if p is None:
            return
        ev = TurnEvent(
            trigger_prompt=(p["trigger"] or "(session activity)")[:mc],
            action_taken=p["action"][:mc] or "(assistant turn)",
            outcome_feedback=p["outcome"][:mc],
            tool_name=p["tool"],
            success=infer_success(p["action"] + "\n" + p["outcome"]),
            session_id=p["sid"],
            project=sessions.get(p["sid"], p["sid"]),
            timestamp=p["ts"],
        )
        svc.ingest(ev)
        turns += 1
        if turns % 250 == 0:
            print(f"  ingested {turns} turns... ({turns/(time.time()-t0):.0f}/s)")

    for r in rows:
        if args.limit and turns >= args.limit:
            break
        sid, role = r["session_id"], (r["role"] or "").lower()
        body = text_of(r["content"])
        if role == "user":
            flush(pending); pending = None
            last_user[sid] = body
        elif role == "assistant":
            flush(pending)
            pending = {"sid": sid, "trigger": last_user.get(sid, ""), "action": body,
                       "outcome": "", "tool": "", "ts": to_iso(r["timestamp"])}
        elif role == "tool":
            if pending is None:
                pending = {"sid": sid, "trigger": last_user.get(sid, ""), "action": "",
                           "outcome": "", "tool": "", "ts": to_iso(r["timestamp"])}
            pending["outcome"] = (pending["outcome"] + "\n" + body).strip()
            pending["tool"] = r["tool_name"] or pending["tool"]
    flush(pending)

    elapsed = time.time() - t0
    st = svc.db.stats()
    svc.close()
    print(json.dumps({
        "turns_ingested": turns,
        "elapsed_s": round(elapsed, 1),
        "rate_per_s": round(turns / elapsed, 1) if elapsed else None,
        "sessions": len(sessions),
        "stats": st,
        "db_bytes": os.path.getsize(cfg.db_path) if cfg.db_path.exists() else 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
