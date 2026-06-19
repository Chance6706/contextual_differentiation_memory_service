"""Cycle 9 I-1 — SessionStart reads take one consistent snapshot (no torn mid-consolidation view).

SessionStart issues several separate SELECTs (scars, gists, episodics). In Python's default deferred
isolation each bare SELECT sees a different committed state, so a concurrent (non-atomic)
consolidation can splice pre- and post-pass rows into one preamble. db.read_snapshot() pins a single
WAL read snapshot for the whole block — without blocking writers (WAL readers never wait). The
SessionStart path also now closes its short-lived service (was leaking a connection per call).
"""

from __future__ import annotations

import os

import pytest

import cdms.hooks as hooks
from cdms.config import Config
from cdms.db import Database
from cdms.embeddings import Embedder
from cdms.models import Gist, new_id
from cdms.store import MemoryService


def _mk_gist(emb, subject):
    g = Gist(id=new_id("gist"), subject=subject, relation="prefers", object="tabs")
    return g, emb.embed_one(g.search_text())


def test_i1_read_snapshot_isolates_concurrent_writes(tmp_path, monkeypatch):
    monkeypatch.setenv("CDMS_EMBED_BACKEND", "hash")
    cfg = Config(home=tmp_path)
    emb = Embedder(cfg)
    reader = Database(cfg)
    writer = Database(cfg)              # a second connection = a concurrent consolidation writer
    try:
        assert reader.all_gist() == []
        with reader.read_snapshot():
            before = len(reader.all_gist())
            g, e = _mk_gist(emb, "concurrent")
            writer.insert_gist(g, e)    # commits on the writer mid-snapshot — must NOT block
            during = len(reader.all_gist())
            assert during == before, "snapshot read saw a write committed after it began"
        assert len(reader.all_gist()) == before + 1, "snapshot never released; write invisible after block"
    finally:
        reader.close()
        writer.close()


def test_i1_session_start_closes_its_connection(tmp_path, monkeypatch):
    monkeypatch.setenv("CDMS_EMBED_BACKEND", "hash")
    cfg = Config(home=tmp_path)
    closed = {"n": 0}
    orig = MemoryService.close

    def spy(self):
        closed["n"] += 1
        return orig(self)

    monkeypatch.setattr(MemoryService, "close", spy)
    hooks._session_start_context(cfg, {"cwd": ""})
    assert closed["n"] == 1, "SessionStart leaked its MemoryService connection"


def test_i1_session_start_still_renders_memory(tmp_path, monkeypatch):
    # Regression: wrapping the reads in a snapshot must not change what gets surfaced.
    monkeypatch.setenv("CDMS_EMBED_BACKEND", "hash")
    cfg = Config(home=tmp_path)
    seed = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        seed.pin_scar("deleted prod db", "always take a backup first", project="")
        seed.upsert_fact("user", "prefers", "tabs over spaces", project="")
    finally:
        seed.close()

    out = hooks._session_start_context(cfg, {"cwd": ""})
    assert "always take a backup first" in out
    assert "Guardrails" in out
