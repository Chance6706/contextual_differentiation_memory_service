"""CDMS Viewport — locks the hardening applied when it was pulled into the package:
the SSE route is reachable, search is non-mutating (reinforce=False), static serving is
contained (no '..' traversal), and the core endpoints serve the store read-only."""
from __future__ import annotations

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import cdms.viewport.server as vp
from cdms.config import Config
from cdms.embeddings import Embedder
from cdms.models import Gist, new_id
from cdms.store import MemoryService


def _seed(home):
    cfg = Config(home=home)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    for subj, rel, obj in [("alpha", "handles_well", "database migrations"),
                           ("beta", "frequently_works_on", "react components")]:
        g = Gist(id=new_id("gist"), subject=subj, relation=rel, object=obj,
                 valence=0.5, frequency=5, support_count=5, project=subj)
        svc.db.insert_gist(g, svc.embedder.embed_one(g.search_text()))
    svc.pin_scar("force-pushed to shared main", "NEVER force-push to shared branches", project="alpha")
    svc.close()


@pytest.fixture
def viewport_base(tmp_path, monkeypatch):
    """A running viewport bound to an ephemeral port over a freshly seeded store."""
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    _seed(tmp_path)
    vp._svc = None  # reset module-global cache so the server picks up CDMS_HOME
    srv = ThreadingHTTPServer(("127.0.0.1", 0), vp._make_handler())
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown(); srv.server_close()
        if vp._svc is not None:
            try:
                vp._svc.close()
            except Exception:
                pass
        vp._svc = None


def _get(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read()


def test_safe_static_blocks_traversal():
    """The static handler must contain requests to the static dir — no '..' escape."""
    H = vp._make_handler()
    assert H._safe_static("../server.py") is None
    assert H._safe_static("../../pyproject.toml") is None
    assert H._safe_static("index.html") is not None  # a legit bundled file still resolves


def test_core_endpoints_serve_the_store(viewport_base):
    code, body = _get(viewport_base + "/api/stats")
    assert code == 200
    st = json.loads(body)
    assert st["gist"] == 2 and st["scars"] == 1 and "archetype" in st

    code, body = _get(viewport_base + "/api/persona")
    assert code == 200 and len(json.loads(body)) == 2

    code, body = _get(viewport_base + "/api/temperament")
    assert code == 200 and json.loads(body)["dials"]  # operator-facing dials present


def test_sse_route_is_not_shadowed(viewport_base):
    """`/api/sse` must reach the SSE handler — it used to be swallowed by the `/api/` router
    (404), so the live feed never connected."""
    req = urllib.request.urlopen(viewport_base + "/api/sse", timeout=3)
    try:
        assert req.status == 200
        assert req.headers.get("Content-Type", "").startswith("text/event-stream")
    finally:
        req.close()


def test_search_does_not_mutate_store(viewport_base, monkeypatch):
    """The viewport must call retrieve with reinforce=False — the default reinforces episodic
    memory, so a 'read-only' search would perturb the salience/decay it is meant to display."""
    captured = {}

    def spy(self, query, **kw):
        captured.update(kw)
        return []

    monkeypatch.setattr(MemoryService, "retrieve", spy)
    code, _ = _get(viewport_base + "/api/search?q=database")
    assert code == 200
    assert captured.get("reinforce") is False
