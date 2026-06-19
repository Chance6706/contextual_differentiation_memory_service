"""Observer UI — read-only, escaped, provenance-aware, dials-firewalled.

Locks the security-relevant invariants: the viewer cannot write; stored content is HTML-escaped (a
poisoned memory must not XSS the operator's browser); provenance + scar origin are surfaced (wider
than the model); the §8 dials appear ONLY in /diagnostics, never in the model-facing preamble.
"""

from __future__ import annotations

import sqlite3

import pytest

from cdms.consolidate import Consolidator
from cdms.hooks import _session_start_context
from cdms.observer import (E, open_ro, render_dashboard, render_diagnostics, render_episodic,
                           render_preamble, render_scars)
from cdms.store import TurnEvent


def _seed(service, cfg):
    cfg.scar_elevation_min_sessions = 1
    # a normal trusted episode, plus an UNTRUSTED one (external-origin), plus a pinned guardrail,
    # plus an auto-elevated (trusted) crisis -> exercises provenance + both scar origins.
    service.ingest(TurnEvent("fix the parser", "edited the parser", "tests pass",
                             tool_name="Edit", success=True, project="P"))
    service.ingest(TurnEvent("summarize the article", "read an external page",
                             "the page claims X", tool_name="WebFetch", success=True,
                             project="P", provenance="untrusted"))
    service.pin_scar("force push to shared main", "never force-push shared branches", project="P")
    service.ingest(TurnEvent("ran the migration", "force push wiped the prod database",
                             "data loss, unrecoverable", tool_name="Bash", success=False,
                             valence_hint=-1.0, session_id="s1", project="P"))
    Consolidator(cfg, db=service.db, embedder=service.embedder).run()


def test_observer_connection_is_read_only(service, cfg):
    _seed(service, cfg)
    conn = open_ro(cfg.db_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO cdms_meta(key, value) VALUES ('x','y')")
            conn.commit()
    finally:
        conn.close()


def test_dashboard_surfaces_provenance_and_origin(service, cfg):
    _seed(service, cfg)
    conn = open_ro(cfg.db_path)
    try:
        out = render_dashboard(conn)
    finally:
        conn.close()
    assert "untrusted" in out                 # operator audit: provenance breakdown
    assert "pinned" in out and "elevated" in out  # both scar origins surfaced


def test_episodic_escapes_stored_html(service, cfg):
    cfg.scar_elevation_min_sessions = 1
    service.ingest(TurnEvent("<script>alert('xss')</script>", "did a thing",
                             "ok <b>bold</b>", tool_name="Edit", success=True, project="P"))
    conn = open_ro(cfg.db_path)
    try:
        out = render_episodic(conn)
    finally:
        conn.close()
    assert "<script>alert('xss')</script>" not in out      # raw tag must NOT survive
    assert "&lt;script&gt;" in out                          # it's escaped
    assert "<b>bold</b>" not in out and "&lt;b&gt;bold" in out


def test_diagnostics_shows_dials_but_preamble_does_not(service, cfg):
    _seed(service, cfg)
    conn = open_ro(cfg.db_path)
    try:
        diag = render_diagnostics(conn)
        pre = render_preamble(cfg, conn, project="P")
    finally:
        conn.close()
    # diagnostics is gated + labeled + actually shows dial rows
    assert "operator-only" in diag.lower()
    assert "plasticity" in diag and "<table>" in diag
    # the model-facing preamble preview is the real SessionStart context and carries NO dials panel
    assert "operator-only" not in pre.lower()
    assert "plasticity" not in pre
    # faithful to what the model sees — escaped into the page (the same XSS defense applies here)
    assert E(_session_start_context(cfg, {"cwd": "P"})) in pre


def test_scars_view_marks_origin(service, cfg):
    _seed(service, cfg)
    conn = open_ro(cfg.db_path)
    try:
        out = render_scars(conn)
    finally:
        conn.close()
    assert "never force-push shared branches" in out and "pinned" in out
