"""Seed a CDMS store from Claude Code session transcripts (*.jsonl).

Claude Code logs every session as JSONL under ~/.claude/projects/<slug>/*.jsonl.
Each line is an event; the ones we care about are type 'user' and 'assistant',
whose message.content is a list of blocks (text / tool_use / tool_result). We
reconstruct user->assistant->tool turns with their REAL timestamps and tag each
by its project, then ingest into a CDMS store.

Multi-project by construction: point --path at ~/.claude/projects and every
project becomes its own (project-tagged) slice of memory — real cross-repo
individuation, not synthetic personas.

Raw conversation text stays on disk; only aggregate progress is printed.

Usage:
    python tools/seed_from_jsonl.py --path ~/.claude/projects --home <cdms_home> [--limit N]
    python tools/seed_from_jsonl.py --path <one-project-dir-or-file> --home <store>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cdms.config import Config                     # noqa: E402
from cdms.store import MemoryService, TurnEvent    # noqa: E402

_ERR = ("error", "failed", "failure", "exception", "traceback", "fatal", "denied",
        "cannot", "no such", "not found")
_OK = ("passed", "success", "succeeded", "completed", "done", "ok", "fixed", "merged")


def _blocks(content):
    return content if isinstance(content, list) else []


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for b in _blocks(content):
        if isinstance(b, dict) and b.get("type") == "text":
            parts.append(b.get("text") or "")
    return " ".join(p for p in parts if p).strip()


def tool_uses(content):
    out = []
    for b in _blocks(content):
        if isinstance(b, dict) and b.get("type") == "tool_use":
            out.append((b.get("name") or "", b.get("input")))
    return out


def tool_results(content) -> str:
    parts = []
    for b in _blocks(content):
        if isinstance(b, dict) and b.get("type") == "tool_result":
            c = b.get("content")
            if isinstance(c, str):
                parts.append(c)
            elif isinstance(c, list):
                parts.append(text_of(c))
    return " ".join(p for p in parts if p).strip()


def infer_success(text: str):
    low = text.lower()
    e = any(m in low for m in _ERR)
    o = any(m in low for m in _OK)
    if e and not o:
        return False
    if o and not e:
        return True
    return None


def _brief(s: str, n: int) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n] + "…"


def project_of(path: Path) -> str:
    """Project tag = the slug segment right after '.claude/projects'."""
    parts = path.parts
    slug = path.parent.name
    if "projects" in parts:
        i = parts.index("projects")
        if i + 1 < len(parts):
            slug = parts[i + 1]
    return slug.replace("D--", "").replace("--", "/").replace("-", "_") or "unknown"


def iter_files(root: Path):
    """Yield main session transcripts, skipping nested subagent/workflow logs
    (those are orchestration noise, not the user's lived history)."""
    if root.is_file():
        yield root
        return
    for p in sorted(root.rglob("*.jsonl")):
        s = str(p).replace("\\", "/")
        if "/subagents/" in s or "/workflows/" in s:
            continue
        yield p


def process_file(path: Path, svc: MemoryService, mc: int, remaining: int) -> int:
    project = project_of(path)
    last_user: dict[str, str] = {}
    pending: dict | None = None
    count = 0

    def flush(p):
        nonlocal count
        if p is None or not (p["action"] or p["outcome"]):
            return
        svc.ingest(TurnEvent(
            trigger_prompt=_brief(p["trigger"] or "(session activity)", mc),
            action_taken=_brief(p["action"] or "(assistant turn)", mc),
            outcome_feedback=_brief(p["outcome"], mc),
            tool_name=p["tool"],
            success=infer_success(p["action"] + "\n" + p["outcome"]),
            session_id=p["sid"],
            project=project,
            timestamp=p["ts"],
        ))
        count += 1

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if remaining and count >= remaining:
                break
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            typ = ev.get("type")
            if typ not in ("user", "assistant"):
                continue
            msg = ev.get("message") or {}
            content = msg.get("content")
            ts = ev.get("timestamp")
            sid = ev.get("sessionId") or path.stem

            if typ == "user":
                tr = tool_results(content)
                if tr:                                  # a tool result -> outcome of the pending turn
                    if pending is None:
                        pending = {"sid": sid, "trigger": last_user.get(sid, ""), "action": "",
                                   "outcome": "", "tool": "", "ts": ts}
                    pending["outcome"] = (pending["outcome"] + "\n" + tr).strip()
                else:                                   # a real user prompt
                    flush(pending); pending = None
                    last_user[sid] = text_of(content)
            else:  # assistant
                flush(pending)
                txt = text_of(content)
                tus = tool_uses(content)
                action = txt
                if tus:
                    action = (txt + " " + "; ".join(f"{n}({_brief(json.dumps(i, default=str), 120)})"
                                                    for n, i in tus)).strip()
                pending = {"sid": sid, "trigger": last_user.get(sid, ""), "action": action,
                           "outcome": "", "tool": (tus[0][0] if tus else ""), "ts": ts}
    flush(pending)
    return count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="a .jsonl file, a project dir, or ~/.claude/projects")
    ap.add_argument("--home", required=True, help="CDMS_HOME for the seed store")
    ap.add_argument("--limit", type=int, default=0, help="max turns PER FILE (0 = all)")
    ap.add_argument("--max-chars", type=int, default=1200)
    args = ap.parse_args()

    cfg = Config(home=Path(os.path.abspath(args.home)))
    cfg.ensure_home()
    svc = MemoryService(cfg)

    root = Path(os.path.expanduser(args.path))
    files = list(iter_files(root))
    t0 = time.time()
    total = 0
    by_project: dict[str, int] = {}
    for i, fp in enumerate(files, 1):
        n = process_file(fp, svc, args.max_chars, args.limit)
        total += n
        by_project[project_of(fp)] = by_project.get(project_of(fp), 0) + n
        if i % 5 == 0 or i == len(files):
            print(f"  [{i}/{len(files)}] {total} turns ingested "
                  f"({total/(time.time()-t0):.0f}/s)")

    elapsed = time.time() - t0
    st = svc.db.stats()
    svc.close()
    print(json.dumps({
        "files": len(files),
        "turns_ingested": total,
        "by_project": by_project,
        "elapsed_s": round(elapsed, 1),
        "rate_per_s": round(total / elapsed, 1) if elapsed else None,
        "stats": st,
        "db_mb": round(os.path.getsize(cfg.db_path) / 1048576, 1) if cfg.db_path.exists() else 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
