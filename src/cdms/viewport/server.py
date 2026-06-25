"""CDMS Viewport — loopback web server for the memory dashboard.

Serves the static frontend and a thin **read-only** REST/SSE API over the CDMS store.
Binds 127.0.0.1 only. No auth (local operator tool).

    python -m cdms.viewport --port 8765      # or:  cdms viewport --port 8765

Originally authored in the standalone CDMS-viewport repo (owl-alpha); pulled into the
package and hardened:
  - SSE route un-shadowed (``/api/sse`` was captured by the ``/api/`` router → 404, so the
    live feed never connected);
  - search made NON-mutating (``retrieve(..., reinforce=False)`` — the default reinforces
    episodic memories, so the "read-only window" was perturbing the dynamics it observes);
  - static serving contained to the static dir (no ``..`` path traversal);
  - non-loopback binds refused (the dashboard exposes the whole store + operator-only dials);
  - all store access serialized (one sqlite connection shared across the threaded server).
"""
from __future__ import annotations

import argparse
import json
import queue as _queue_module
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Static frontend ships inside the package.
_STATIC_DIR = Path(__file__).resolve().parent / "static"

# --------------------------------------------------------------------------- #
# Store lifecycle (lazy, thread-safe single init) + a lock serializing all store
# access. ThreadingHTTPServer dispatches each request on its own thread and the
# watcher runs on another; sharing one sqlite connection across them is not
# concurrency-safe even with check_same_thread=False, so we serialize DB access.
# RLock so a handler that already holds it can call helpers that re-acquire.
# --------------------------------------------------------------------------- #
_lock = threading.Lock()
_svc = None
_DB_LOCK = threading.RLock()


def _get_store():
    global _svc
    if _svc is not None:
        return _svc
    with _lock:
        if _svc is not None:
            return _svc
        from cdms.config import load_config
        from cdms.store import MemoryService
        cfg = load_config()
        _svc = MemoryService(cfg)
        return _svc


def _json(obj) -> bytes:
    return json.dumps(obj, default=str).encode("utf-8")


# --------------------------------------------------------------------------- #
# SSE broadcaster (lightweight: one queue per connected client)
# --------------------------------------------------------------------------- #
_clients: set = set()
_clients_lock = threading.Lock()


def broadcast(event: str, data: dict) -> None:
    """Push an event to all connected SSE clients. Thread-safe."""
    payload = f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")
    with _clients_lock:
        dead = set()
        for q in _clients:
            try:
                q.put_nowait(payload)
            except Exception:
                dead.add(q)
        _clients.difference_update(dead)


# --------------------------------------------------------------------------- #
# Background watcher — polls DB for changes, broadcasts to SSE clients
# --------------------------------------------------------------------------- #
_watcher_stop = threading.Event()


def _watch_store(interval: float = 3.0) -> None:
    """Background thread: watch for new episodes/gists/scars and broadcast SSE events.

    Additive — no CDMS code changes; just reads the SQLite tables (under the shared
    store lock, since the request threads use the same connection)."""
    svc = _get_store()
    last_ep_id = ""
    last_gist_count = 0
    last_scar_count = 0

    with _DB_LOCK:
        try:
            rows = svc.db.conn.execute(
                "SELECT id FROM mem_episodic ORDER BY rowid DESC LIMIT 1"
            ).fetchall()
            if rows:
                last_ep_id = rows[0]["id"]
            last_gist_count = svc.db.conn.execute("SELECT COUNT(*) FROM mem_gist").fetchone()[0]
            last_scar_count = svc.db.conn.execute("SELECT COUNT(*) FROM mem_scars").fetchone()[0]
        except Exception:
            pass

    while not _watcher_stop.wait(timeout=interval):
        with _DB_LOCK:
            try:
                rows = svc.db.conn.execute(
                    "SELECT * FROM mem_episodic WHERE rowid > (SELECT rowid FROM mem_episodic WHERE id = ?) "
                    "ORDER BY rowid ASC",
                    (last_ep_id,),
                ).fetchall()
                if rows:
                    for r in rows:
                        broadcast("episode", _row_to_episodic_json(r))
                    last_ep_id = rows[-1]["id"]

                cur_gist = svc.db.conn.execute("SELECT COUNT(*) FROM mem_gist").fetchone()[0]
                if cur_gist > last_gist_count:
                    new_gists = svc.db.conn.execute(
                        "SELECT * FROM mem_gist WHERE rowid > (SELECT MAX(rowid) - ? FROM mem_gist)",
                        (cur_gist - last_gist_count,),
                    ).fetchall()
                    for r in new_gists:
                        broadcast("gist", _row_to_gist_json(r))
                    last_gist_count = cur_gist

                cur_scar = svc.db.conn.execute("SELECT COUNT(*) FROM mem_scars").fetchone()[0]
                if cur_scar > last_scar_count:
                    new_scars = svc.db.conn.execute(
                        "SELECT * FROM mem_scars WHERE rowid > (SELECT MAX(rowid) - ? FROM mem_scars)",
                        (cur_scar - last_scar_count,),
                    ).fetchall()
                    for r in new_scars:
                        broadcast("scar", _row_to_scar_json(r))
                    last_scar_count = cur_scar
            except Exception:
                pass  # DB may be mid-write; next tick catches up


# --------------------------------------------------------------------------- #
# Filter metadata endpoints (for dropdowns)
# --------------------------------------------------------------------------- #
def _get_projects() -> list[str]:
    """Return distinct projects from all tiers."""
    svc = _get_store()
    projects: set[str] = set()
    with _DB_LOCK:
        try:
            for row in svc.db.conn.execute("SELECT DISTINCT project FROM mem_episodic WHERE project != ''"):
                projects.add(row["project"])
            for row in svc.db.conn.execute("SELECT DISTINCT project FROM mem_gist WHERE project != ''"):
                projects.add(row["project"])
        except Exception:
            pass
    return sorted(projects)


def _get_sessions() -> list[str]:
    """Return distinct session IDs from the episodic tier."""
    svc = _get_store()
    sessions: list[str] = []
    with _DB_LOCK:
        try:
            for row in svc.db.conn.execute(
                "SELECT DISTINCT session_id FROM mem_episodic WHERE session_id != '' ORDER BY session_id"
            ):
                sessions.append(row["session_id"])
        except Exception:
            pass
    return sessions[:200]


# --------------------------------------------------------------------------- #
# HTTP handler
# --------------------------------------------------------------------------- #
def _make_handler():
    """Build the HTTP handler class (no cfg needed — store is lazy-initialized)."""
    class H(BaseHTTPRequestHandler):
        server_version = "CDMS-Viewport/1.0"

        def log_message(self, *a):
            pass  # quiet

        # -- helpers ------------------------------------------------------- #
        def _send_bytes(self, data: bytes, ctype="text/html; charset=utf-8", code=200):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            if ctype.startswith("text/event-stream"):
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, obj, code=200):
            self._send_bytes(_json(obj), ctype="application/json", code=code)

        @staticmethod
        def _safe_static(rel: str):
            """Resolve a static-relative path, contained to _STATIC_DIR (no '..' escape)."""
            try:
                p = (_STATIC_DIR / rel).resolve()
                p.relative_to(_STATIC_DIR.resolve())  # raises ValueError if outside
            except (ValueError, OSError):
                return None
            return p if p.is_file() else None

        def _send_html(self, path: str):
            p = self._safe_static(path)
            if p is None:
                self._send_bytes(b"<p>not found</p>", code=404)
                return
            self._send_bytes(p.read_bytes(), ctype=_guess_mime(p.suffix))

        # -- routing ------------------------------------------------------- #
        def do_GET(self):
            u = urlparse(self.path)
            path = u.path.rstrip("/") or "/"
            q = parse_qs(u.query)

            # SSE FIRST — '/api/sse' must not be swallowed by the '/api/' router below.
            if path == "/api/sse" or path == "/sse":
                self._handle_sse()
                return

            if path.startswith("/api/"):
                self._handle_api(path[len("/api/"):], q)
                return

            if path == "/" or path == "/index.html":
                idx = self._safe_static("index.html")
                if idx is None:
                    self._send_bytes(b"<p>viewport: static/index.html missing</p>", code=404)
                else:
                    self._send_bytes(idx.read_bytes())
            else:
                self._send_html(path.lstrip("/"))

        # -- API handlers -------------------------------------------------- #
        def _handle_api(self, route: str, q: dict):
            with _DB_LOCK:
                self._dispatch_api(route, q)

        def _dispatch_api(self, route: str, q: dict):
            svc = _get_store()
            conn = svc.db  # Database instance

            if route == "stats":
                st = conn.stats()
                st["archetype"] = conn.get_archetype()
                self._send_json(st)

            elif route == "timeline":
                limit = _int(q.get("limit", [50])[0], 50, 1, 500)
                project = q.get("project", [None])[0] or None
                if project:
                    rows = conn.conn.execute(
                        "SELECT * FROM mem_episodic WHERE project = ? "
                        "ORDER BY timestamp DESC, rowid DESC LIMIT ?",
                        (project, limit),
                    ).fetchall()
                else:
                    rows = conn.conn.execute(
                        "SELECT * FROM mem_episodic "
                        "ORDER BY timestamp DESC, rowid DESC LIMIT ?",
                        (limit,),
                    ).fetchall()
                self._send_json([_row_to_episodic_json(r) for r in rows])

            elif route == "persona":
                rows = conn.conn.execute(
                    "SELECT * FROM mem_gist ORDER BY (support_count + frequency + survived_cycles) DESC LIMIT 200"
                ).fetchall()
                self._send_json([_row_to_gist_json(r) for r in rows])

            elif route == "paths":
                paths = svc.list_paths()
                self._send_json([{"subject": s, "relation": r, "support": sup} for s, r, sup in paths])

            elif route == "scars":
                rows = conn.conn.execute(
                    "SELECT * FROM mem_scars ORDER BY timestamp DESC"
                ).fetchall()
                self._send_json([_row_to_scar_json(r) for r in rows])

            elif route == "temperament":
                dials = conn.all_dials()
                archetype = conn.get_archetype()
                radius = conn.get_archetype_radius()
                self._send_json({
                    "archetype": archetype,
                    "radius": radius,
                    "dials": [
                        {"name": d.name, "seed": d.seed, "current": d.current,
                         "lower": d.lower, "upper": d.upper, "plasticity": d.plasticity}
                        for d in dials
                    ],
                })

            elif route == "projects":
                self._send_json(_get_projects())

            elif route == "sessions":
                self._send_json(_get_sessions())

            elif route == "search":
                query = q.get("q", [""])[0]
                if not query.strip():
                    self._send_json([])
                    return
                top_k = _int(q.get("top_k", [12])[0], 12, 1, 50)
                tiers_q = q.get("tiers", ["episodic,gist,scar"])[0]
                tiers = tuple(t.strip() for t in tiers_q.split(",") if t.strip())
                # reinforce=False: a viewport search must NOT mutate the store (the default
                # bumps access_count + reinforces episodic memories — the observer would
                # perturb the very salience/decay dynamics it is meant to display).
                hits = svc.retrieve(query, top_k=top_k,
                                    tiers=tiers if tiers else None, reinforce=False)
                self._send_json([{
                    "id": h.id, "tier": h.tier, "score": round(h.score, 5),
                    "accessibility": round(h.accessibility, 4), "text": h.text,
                    "payload": h.payload,
                } for h in hits])

            else:
                self._send_json({"error": "unknown endpoint"}, code=404)

        # -- SSE ----------------------------------------------------------- #
        def _handle_sse(self):
            q = _queue_module.Queue(maxsize=64)
            with _clients_lock:
                _clients.add(q)
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                self.wfile.write(b"event: connected\ndata: {}\n\n")
                self.wfile.flush()
                while True:
                    msg = q.get(timeout=30)
                    self.wfile.write(msg)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                pass
            finally:
                with _clients_lock:
                    _clients.discard(q)

    return H


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _int(v, default, lo=0, hi=999999):
    try:
        return max(lo, min(hi, int(v)))
    except (ValueError, TypeError):
        return default


def _row_to_episodic_json(r) -> dict:
    return {
        "id": r["id"], "trigger_prompt": r["trigger_prompt"],
        "action_taken": r["action_taken"], "outcome_feedback": r["outcome_feedback"] or "",
        "valence": r["valence"], "base_salience": r["base_salience"],
        "access_count": r["access_count"], "timestamp": r["timestamp"],
        "last_accessed": r["last_accessed"], "session_id": r["session_id"] or "",
        "project": r["project"] or "", "provenance": r["provenance"] or "trusted",
    }


def _row_to_gist_json(r) -> dict:
    return {
        "id": r["id"], "subject": r["subject"], "relation": r["relation"],
        "object": r["object"], "valence": r["valence"], "frequency": r["frequency"],
        "support_count": r["support_count"], "survived_cycles": r["survived_cycles"],
        "project": r["project"] or "", "last_reinforced": r["last_reinforced"],
        "exemplar": r["exemplar"] or "",
    }


def _row_to_scar_json(r) -> dict:
    return {
        "id": r["id"], "crisis_trigger": r["crisis_trigger"],
        "remediation_rule": r["remediation_rule"], "timestamp": r["timestamp"],
        "project": r["project"] or "", "origin": r["origin"] or "pinned",
    }


def _guess_mime(suffix: str) -> str:
    return {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".ico": "image/x-icon",
    }.get(suffix.lower(), "application/octet-stream")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cdms viewport",
                                description="CDMS Viewport — read-only memory dashboard (loopback)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--host", default="127.0.0.1")
    args = p.parse_args(argv)

    # Loopback-only: the dashboard exposes the entire store AND operator-only temperament
    # dials with no auth. Refuse a non-loopback bind; use an authenticated tunnel for remote.
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print(f"REFUSING to bind {args.host!r}: the viewport serves the full memory store and "
              "operator-only temperament dials with NO auth, so it is loopback-only by design. "
              "For remote access, put it behind an authenticated tunnel/reverse proxy.")
        return 2

    try:
        svc = _get_store()
        st = svc.db.stats()
        print(f"CDMS store loaded: episodic={st['episodic']} gist={st['gist']} scars={st['scars']}")
    except Exception as exc:
        print(f"ERROR: cannot load CDMS store: {exc}")
        return 1

    if not (_STATIC_DIR / "index.html").exists():
        print(f"WARNING: no index.html at {_STATIC_DIR} — serving API only.")

    _watcher_stop.clear()
    watcher = threading.Thread(target=_watch_store, daemon=True)
    watcher.start()

    srv = ThreadingHTTPServer((args.host, args.port), _make_handler())
    print(f"CDMS Viewport → http://{args.host}:{args.port}  (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        _watcher_stop.set()
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
