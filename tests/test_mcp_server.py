"""Smoke coverage for the MCP server tools (previously zero coverage).

The MCP server is the production integration with Claude Code; exercise each tool
end-to-end (store/retrieve/history/list_paths/create_link) on a temp store with the
offline embedder, including project scoping and create_link validation.
"""

from __future__ import annotations

import importlib


def _fresh_server(tmp_path, monkeypatch):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    import cdms.mcp_server as m
    importlib.reload(m)  # re-evaluate _CFG/_LAUNCH_CWD against the temp home
    return m


def test_mcp_tools_smoke(tmp_path, monkeypatch):
    m = _fresh_server(tmp_path, monkeypatch)
    proj = str(tmp_path)

    r = m.store(content="we fixed the flaky auth test", kind="episode", project=proj)
    assert r.tier == "episodic" and r.id

    rf = m.store(content="payments | handles_well | idempotency key", kind="fact", project=proj)
    assert rf.tier == "gist"

    rs = m.store(content="deleted prod db | always take a backup first", kind="scar", project=proj)
    assert rs.tier == "scar"

    hits = m.retrieve(query="auth test", k=5, tiers="all", project=proj)
    assert isinstance(hits, list)

    assert isinstance(m.history(limit=10, session_id=""), list)
    assert isinstance(m.list_paths(), list)


def test_mcp_create_link_validates(tmp_path, monkeypatch):
    m = _fresh_server(tmp_path, monkeypatch)
    link = m.create_link(source_id="does_not_exist", target_id="also_missing")
    assert link.created is False  # no dangling edge fabricated


def test_mcp_store_fact_with_too_few_parts_is_safe(tmp_path, monkeypatch):
    m = _fresh_server(tmp_path, monkeypatch)
    r = m.store(content="just a phrase with no pipes", kind="fact", project=str(tmp_path))
    assert r.tier == "gist"  # degrades to user|noted|... without crashing
