"""`cdms` command-line interface — one binary, many subcommands.

This mirrors the spec's single-daemon-with-subcommands shape:

    cdms serve            run the MCP stdio server (Claude Code integration)
    cdms hook <Event>     handle a lifecycle hook (reads JSON on stdin)
    cdms consolidate      drain the queue and run the sleep/dream pass
    cdms drain            ingest spooled events without consolidating
    cdms retrieve <q>     query memory from the terminal
    cdms history          show the recent episodic timeline
    cdms paths            show the PersonaTree (subject/relation) paths
    cdms stats            show store statistics
    cdms doctor           verify the environment and warm the embedder
    cdms install          wire CDMS into Claude Code (hooks + MCP) for a project
    cdms uninstall        remove CDMS hooks + MCP config from a project
    cdms ingest           manually ingest a turn (testing / scripting)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .config import load_config


def _read_json_safe(path: Path) -> dict:
    """Read a JSON config file, aborting LOUDLY on malformed JSON.

    Previously a parse error reset the config to ``{}`` and the install then
    overwrote the file — so a transient typo in (e.g.) ``~/.claude.json`` silently
    destroyed the user's model/permissions/MCP approvals. Refuse instead.
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"ERROR: {path} contains invalid JSON ({exc}).\n"
            f"Refusing to overwrite it and lose your settings — fix or remove the "
            f"file, then re-run."
        )


def _atomic_write_json(path: Path, obj) -> None:
    """Write JSON via a UNIQUE temp file + os.replace so a crash/disk-full mid-write
    can never leave the user's settings truncated, and two concurrent writers don't
    race a shared temp name. The temp is same-directory (same fs => atomic replace).

    If ``path`` is a symlink (common: settings.json -> a dotfiles repo), write
    THROUGH to the link target instead of replacing the link with a detached file
    (which would silently sever the link and leave the real dotfile un-updated).

    ``realpath`` is applied UNCONDITIONALLY (it is idempotent for non-symlinks) rather
    than gated on ``is_symlink()`` — the check-then-use gate was a TOCTOU window where the
    symlink could be swapped between the check and the write (Cycle-4 A6-L1).
    """
    import tempfile

    real = Path(os.path.realpath(path))
    real.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(real.parent), prefix=real.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(obj, indent=2))
        os.replace(tmp, real)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

HOOK_EVENTS = {
    "SessionStart": 30,
    "UserPromptSubmit": 15,
    "PostToolUse": 15,
    "Stop": 15,
    "PreCompact": 120,
    "SessionEnd": 120,
}


# --------------------------------------------------------------------------- #
# command implementations
# --------------------------------------------------------------------------- #
def cmd_serve(args) -> int:
    from .mcp_server import main as serve_main
    serve_main()
    return 0


def cmd_hook(args) -> int:
    from .hooks import run_hook
    return run_hook(args.event)


def cmd_consolidate(args) -> int:
    from datetime import datetime, timezone

    from .consolidate import Consolidator
    from .pipeline import drain_and_ingest
    from .store import MemoryService

    cfg = load_config()
    svc = MemoryService(cfg)
    ingested = drain_and_ingest(cfg, svc)
    rep = Consolidator(cfg, db=svc.db, embedder=svc.embedder).run(now=datetime.now(timezone.utc))
    out = {"ingested": ingested, **rep.as_dict()}
    svc.close()
    print(json.dumps(out, indent=2))
    return 0


def cmd_drain(args) -> int:
    from .pipeline import drain_and_ingest
    from .store import MemoryService

    cfg = load_config()
    svc = MemoryService(cfg)
    n = drain_and_ingest(cfg, svc)
    svc.close()
    print(json.dumps({"ingested": n}))
    return 0


def cmd_retrieve(args) -> int:
    from .store import MemoryService

    cfg = load_config()
    svc = MemoryService(cfg)
    hits = svc.retrieve(args.query, top_k=args.k)
    svc.close()
    if args.json:
        print(json.dumps([{"id": h.id, "tier": h.tier, "score": round(h.score, 5),
                           "accessibility": round(h.accessibility, 4), "text": h.text} for h in hits], indent=2))
    else:
        if not hits:
            print("(no memories)")
        for h in hits:
            print(f"[{h.tier:8}] {h.score:.4f}  acc={h.accessibility:.3f}  {h.text[:100]}")
    return 0


def cmd_history(args) -> int:
    from .store import MemoryService

    cfg = load_config()
    svc = MemoryService(cfg)
    eps = svc.history(limit=args.n, session_id=args.session or None)
    svc.close()
    for e in eps:
        print(f"{e.timestamp}  S0={e.base_salience:.3f}  v={e.valence:+.2f}  {e.search_text()[:90]}")
    if not eps:
        print("(no history)")
    return 0


def cmd_paths(args) -> int:
    from .store import MemoryService

    cfg = load_config()
    svc = MemoryService(cfg)
    paths = svc.list_paths()
    svc.close()
    for subj, rel, sup in paths:
        print(f"{subj}  --{rel}-->   (support {sup})")
    if not paths:
        print("(no consolidated PersonaTree yet)")
    return 0


def cmd_stats(args) -> int:
    from .store import MemoryService

    cfg = load_config()
    svc = MemoryService(cfg)
    st = svc.db.stats()
    svc.close()
    st["db_path"] = str(cfg.db_path)
    st["embed_model"] = cfg.embed_model
    st["embed_dim"] = cfg.embed_dim
    print(json.dumps(st, indent=2))
    return 0


def cmd_temperament(args) -> int:
    """Operator-only view of the §8 temperament vector and its joint-leash status.

    NEVER injected into context (break-cycle principle #1 / Bem self-perception
    firewall): the agent must not read its own disposition. This is for the operator.
    """
    from .store import MemoryService
    from .temperament import leash_distance, leash_exceeded, near_bound, seed_vector, vector

    cfg = load_config()
    svc = MemoryService(cfg)
    dials = svc.db.all_dials()
    archetype = svc.db.get_archetype()
    radius = svc.db.get_archetype_radius()
    svc.close()

    cur, sd = vector(dials), seed_vector(dials)
    dist = leash_distance(cur, sd) if dials else 0.0
    # Verdict via leash_exceeded on the UNROUNDED value (don't re-implement `> R`
    # inline, and don't let display rounding flip the verdict) — Round-2 F6.
    exceeded = leash_exceeded(cur, sd, radius) if dials else False
    out = {
        "archetype": archetype,
        "R_archetype": radius,
        "leash_distance": round(dist, 6),
        "leash_exceeded": exceeded,
        "dials": [
            {"dial": d.name, "seed": d.seed, "current": d.current,
             "lower": d.lower, "upper": d.upper, "plasticity": d.plasticity,
             "near_bound": near_bound(d)}
            for d in dials
        ],
    }
    print(json.dumps(out, indent=2))
    return 0


def cmd_ingest(args) -> int:
    from .store import MemoryService, TurnEvent

    cfg = load_config()
    svc = MemoryService(cfg)
    success = None
    if args.success:
        success = True
    elif args.failure:
        success = False
    rec = svc.ingest(TurnEvent(
        trigger_prompt=args.trigger, action_taken=args.action, outcome_feedback=args.outcome or "",
        tool_name=args.tool or "", success=success, session_id=args.session or "",
        project=args.project or "",
    ))
    svc.close()
    print(json.dumps({"id": rec.id, "salience": round(rec.base_salience, 4),
                      "valence": round(rec.valence, 3)}))
    return 0


def cmd_forget(args) -> int:
    """Operator-only deletion / right-to-forget. Not exposed to the model."""
    from .store import MemoryService

    if not (args.project or args.session or args.id):
        print("ERROR: specify at least one of --project / --session / --id", file=sys.stderr)
        return 2
    cfg = load_config()
    svc = MemoryService(cfg)
    res = svc.forget(project=args.project or None, session=args.session or None,
                     ids=list(args.id) if args.id else None)
    svc.close()
    print(json.dumps({"forgot": res}))
    return 0


def cmd_doctor(args) -> int:
    import sqlite3

    cfg = load_config()
    ok = True
    print(f"CDMS_HOME           : {cfg.home}")
    print(f"db path             : {cfg.db_path}")
    print(f"sqlite version      : {sqlite3.sqlite_version}", "(>=3.41 OK)" if sqlite3.sqlite_version_info >= (3, 41) else "(TOO OLD)")
    try:
        import sqlite_vec  # noqa: F401
        c = sqlite3.connect(":memory:")
        c.enable_load_extension(True)
        sqlite_vec.load(c)
        print(f"sqlite-vec          : {c.execute('select vec_version()').fetchone()[0]} OK")
    except Exception as exc:
        ok = False
        print(f"sqlite-vec          : FAILED ({exc})")
    try:
        from .embeddings import get_embedder
        emb = get_embedder(cfg)
        v = emb.embed_one("doctor warmup test")
        print(f"embedder backend    : {emb.backend} (dim={len(v)}) OK")
        if emb.backend == "hash":
            print("  NOTE: deterministic offline backend (CDMS_EMBED_BACKEND=hash).")
    except Exception as exc:
        emb = None
        ok = False
        print(f"embedder            : FAILED ({exc})")
    try:
        from .store import MemoryService
        svc = MemoryService(cfg)
        print(f"store               : {json.dumps(svc.db.stats())} OK")
        # Integrity (catches subtle corruption that open() alone misses).
        if not svc.db.integrity_ok():
            ok = False
            print("integrity           : FAILED (quick_check not ok — store may be corrupt)")
        else:
            print("integrity           : ok")
        # Embedding-space fingerprint: a hash-vs-real / dim / model mismatch makes
        # every capture refuse — the silent failure doctor previously missed.
        pinned = svc.db.get_meta("embed_fingerprint")
        if pinned is None:
            print("embed fingerprint   : (unpinned — no vectors written yet)")
        elif emb is not None:
            current = emb.fingerprint()
            if pinned == current:
                print(f"embed fingerprint   : {pinned} MATCH")
            else:
                ok = False
                print(f"embed fingerprint   : MISMATCH (store={pinned} current={current}) "
                      "— captures will be REFUSED until the original embedder is restored")
        svc.close()
    except Exception as exc:
        ok = False
        print(f"store               : FAILED ({exc})")
    print("\nstatus:", "HEALTHY" if ok else "PROBLEMS DETECTED")
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
# install / uninstall — Claude Code wiring
# --------------------------------------------------------------------------- #
def _python_invocation() -> list[str]:
    """The command Claude Code should run to invoke this CLI."""
    return [sys.executable.replace("\\", "/"), "-m", "cdms"]


def _hook_command(event: str) -> str:
    py, *rest = _python_invocation()
    return f'"{py}" {" ".join(rest)} hook {event}'


def cmd_install(args) -> int:
    scope = getattr(args, "scope", "project") or "project"
    if scope == "user":
        # Global wiring: active in EVERY project. Hooks -> ~/.claude/settings.json,
        # MCP -> ~/.claude.json mcpServers (the user-scope registry).
        home_claude = Path.home() / ".claude"
        home_claude.mkdir(parents=True, exist_ok=True)
        if not args.no_hooks:
            _install_hooks(home_claude / "settings.json")
            print(f"✓ user-scope hooks written to {home_claude / 'settings.json'}")
        if not args.no_mcp:
            _install_mcp_user(Path.home() / ".claude.json")
            print(f"✓ user-scope MCP server written to {Path.home() / '.claude.json'}")
        print("\nCDMS is now active across ALL your projects (one shared store at ~/.local_memory).")
        print("Restart Claude Code; approve 'cdms-memory' once. Verify with `cdms doctor`.")
        return 0

    project = Path(args.project or Path.cwd()).resolve()
    claude_dir = project / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_hooks:
        _install_hooks(claude_dir / "settings.json")
        print(f"✓ hooks written to {claude_dir / 'settings.json'}")
    if not args.no_mcp:
        _install_mcp(project / ".mcp.json")
        print(f"✓ MCP server written to {project / '.mcp.json'}")

    print("\nNext steps:")
    print("  1. Restart Claude Code in this project (or run /hooks to reload).")
    print("  2. Approve the 'cdms-memory' MCP server when prompted (or `claude mcp list`).")
    print("  3. Run `cdms doctor` to verify, and `cdms stats` to watch memory grow.")
    print("  (Tip: `cdms install --scope user` wires CDMS into ALL projects at once.)")
    return 0


def _install_mcp_user(claude_json: Path) -> None:
    """Register the MCP server at user scope by editing ~/.claude.json mcpServers.

    Preserves every other key in the (large) global config file.
    """
    config = _require_dict(_read_json_safe(claude_json), claude_json, "top-level value")
    servers = config.setdefault("mcpServers", {})
    _require_dict(servers, claude_json, "'mcpServers' value")
    py, *rest = _python_invocation()
    servers["cdms-memory"] = {"type": "stdio", "command": py, "args": rest + ["serve"], "env": {}}
    _atomic_write_json(claude_json, config)


def _require_dict(obj, path: Path, what: str):
    """Refuse loudly (don't traceback) on a malformed settings shape, mirroring the
    _read_json_safe contract: never silently rewrite a file we can't parse."""
    if not isinstance(obj, dict):
        raise SystemExit(
            f"ERROR: {path} has a non-object {what} ({type(obj).__name__}).\n"
            f"Refusing to modify it — fix or remove the file, then re-run."
        )
    return obj


def _install_hooks(settings_path: Path) -> None:
    settings = _require_dict(_read_json_safe(settings_path), settings_path, "top-level value")
    hooks = settings.setdefault("hooks", {})
    _require_dict(hooks, settings_path, "'hooks' value")
    for event, timeout in HOOK_EVENTS.items():
        matcher = "*" if event == "PostToolUse" else ""
        entry = {
            "matcher": matcher,
            "hooks": [{"type": "command", "command": _hook_command(event), "timeout": timeout}],
        }
        # replace any existing CDMS entry for this event, keep foreign ones. Tolerate
        # a non-list event value or non-dict entries (malformed but non-fatal).
        cur = hooks.get(event, [])
        cur = cur if isinstance(cur, list) else []
        existing = [e for e in cur if not _is_cdms_entry(e)]
        hooks[event] = existing + [entry]
    _atomic_write_json(settings_path, settings)


def _is_cdms_entry(entry) -> bool:
    if not isinstance(entry, dict):
        return False
    for h in entry.get("hooks", []):
        if isinstance(h, dict) and ("cdms hook" in h.get("command", "") or "-m cdms" in h.get("command", "")):
            return True
    return False


def _install_mcp(mcp_path: Path) -> None:
    config = _require_dict(_read_json_safe(mcp_path), mcp_path, "top-level value")
    servers = config.setdefault("mcpServers", {})
    _require_dict(servers, mcp_path, "'mcpServers' value")
    py, *rest = _python_invocation()
    servers["cdms-memory"] = {"command": py, "args": rest + ["serve"]}
    _atomic_write_json(mcp_path, config)


def _remove_cdms_hooks(settings_path: Path) -> None:
    if not settings_path.exists():
        return
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    if not isinstance(settings, dict):
        return
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        return
    for event in list(hooks.keys()):
        cur = hooks[event] if isinstance(hooks[event], list) else []
        hooks[event] = [e for e in cur if not _is_cdms_entry(e)]
        if not hooks[event]:
            del hooks[event]
    _atomic_write_json(settings_path, settings)
    print(f"✓ removed CDMS hooks from {settings_path}")


def _remove_cdms_mcp(json_path: Path) -> None:
    if not json_path.exists():
        return
    try:
        config = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    if not isinstance(config, dict) or not isinstance(config.get("mcpServers", {}), dict):
        return
    if config.get("mcpServers", {}).pop("cdms-memory", None) is not None:
        _atomic_write_json(json_path, config)
        print(f"✓ removed cdms-memory MCP server from {json_path}")


def cmd_uninstall(args) -> int:
    scope = getattr(args, "scope", "project") or "project"
    if scope == "user":
        _remove_cdms_hooks(Path.home() / ".claude" / "settings.json")
        _remove_cdms_mcp(Path.home() / ".claude.json")
        if getattr(args, "purge", False):
            _purge_store()
        return 0
    project = Path(args.project or Path.cwd()).resolve()
    _remove_cdms_hooks(project / ".claude" / "settings.json")
    _remove_cdms_mcp(project / ".mcp.json")
    if getattr(args, "purge", False):
        _purge_store()
    return 0


def _purge_store() -> None:
    """Delete the entire memory store (opt-in via --purge). Irreversible."""
    import shutil

    cfg = load_config()
    if cfg.home.exists():
        shutil.rmtree(cfg.home, ignore_errors=True)
        print(f"✓ purged memory store at {cfg.home}")


# --------------------------------------------------------------------------- #
# argument parser
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cdms", description="Contextual Differentiation Memory Service")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("serve", help="run the MCP stdio server").set_defaults(func=cmd_serve)

    h = sub.add_parser("hook", help="handle a Claude Code lifecycle hook (stdin JSON)")
    h.add_argument("event", help="hook event name, e.g. SessionStart")
    h.set_defaults(func=cmd_hook)

    sub.add_parser("consolidate", help="drain queue and run the sleep/dream pass").set_defaults(func=cmd_consolidate)
    sub.add_parser("drain", help="ingest spooled events without consolidating").set_defaults(func=cmd_drain)

    r = sub.add_parser("retrieve", help="query memory")
    r.add_argument("query")
    r.add_argument("-k", type=int, default=8)
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=cmd_retrieve)

    hi = sub.add_parser("history", help="recent episodic timeline")
    hi.add_argument("-n", type=int, default=20)
    hi.add_argument("--session", default="")
    hi.set_defaults(func=cmd_history)

    sub.add_parser("paths", help="show PersonaTree paths").set_defaults(func=cmd_paths)
    sub.add_parser("stats", help="store statistics").set_defaults(func=cmd_stats)
    sub.add_parser("temperament",
                   help="show the §8 temperament vector + leash status (operator-only)"
                   ).set_defaults(func=cmd_temperament)
    sub.add_parser("doctor", help="verify environment + warm embedder").set_defaults(func=cmd_doctor)

    ing = sub.add_parser("ingest", help="manually ingest a turn")
    ing.add_argument("--trigger", required=True)
    ing.add_argument("--action", required=True)
    ing.add_argument("--outcome", default="")
    ing.add_argument("--tool", default="")
    ing.add_argument("--session", default="")
    ing.add_argument("--project", default="")
    ing.add_argument("--success", action="store_true")
    ing.add_argument("--failure", action="store_true")
    ing.set_defaults(func=cmd_ingest)

    ins = sub.add_parser("install", help="wire CDMS into Claude Code (project or user scope)")
    ins.add_argument("--scope", choices=["project", "user"], default="project",
                     help="'project' (this repo only) or 'user' (ALL projects, shared store)")
    ins.add_argument("--project", default="", help="project dir (default: cwd)")
    ins.add_argument("--no-hooks", action="store_true")
    ins.add_argument("--no-mcp", action="store_true")
    ins.set_defaults(func=cmd_install)

    un = sub.add_parser("uninstall", help="remove CDMS wiring (project or user scope)")
    un.add_argument("--scope", choices=["project", "user"], default="project")
    un.add_argument("--project", default="")
    un.add_argument("--purge", action="store_true",
                    help="also delete the memory store (~/.local_memory). Irreversible.")
    un.set_defaults(func=cmd_uninstall)

    fg = sub.add_parser("forget", help="delete stored memory by project / session / id (operator-only)")
    fg.add_argument("--project", default="", help="delete all memory for this project path")
    fg.add_argument("--session", default="", help="delete all episodes for this session id")
    fg.add_argument("--id", action="append", help="delete a specific memory id (repeatable)")
    fg.set_defaults(func=cmd_forget)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
