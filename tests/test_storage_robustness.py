"""Regression tests for storage/consolidation robustness (red-team MEDIUMs).

  M2 — accessibility() overflowed for very large access_count (crashed eviction).
  M1 — a crash mid-consolidation must not advance the gist-decay cycle counter.
  M4 — schema migration sets user_version LAST and adds v3 columns idempotently.
"""

from __future__ import annotations

import sqlite3

import pytest

from cdms.config import Config
from cdms.db import SCHEMA_VERSION, Database
from cdms.embeddings import Embedder
from cdms.salience import accessibility
from cdms.store import MemoryService, TurnEvent


# --- M2: no overflow ------------------------------------------------------- #
@pytest.mark.parametrize("count", [0, 10, 1000, 10_000, 100_000, 10**9])
def test_accessibility_never_overflows(cfg, count):
    a = accessibility(1.0, 1.0, count, cfg)
    assert a == a and a >= 0.0            # finite, no NaN/overflow
    assert a <= 1.0 * cfg.reinforce_cap + 1e-9  # cap still respected


# --- M1: crash must not age the decay clock -------------------------------- #
def test_cycle_counter_not_advanced_on_crash(cfg, monkeypatch):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        from cdms.consolidate import Consolidator
        svc.ingest(TurnEvent(trigger_prompt="t", action_taken="bash: ls", outcome_feedback="ok", project="p"))
        con = Consolidator(cfg, db=svc.db, embedder=svc.embedder)

        def _boom(*a, **k):
            raise RuntimeError("crash during aggregation")

        monkeypatch.setattr(con, "_aggregate_gists", _boom)
        before = svc.db.get_meta("cycle", "0")
        with pytest.raises(RuntimeError):
            con.run()
        assert svc.db.get_meta("cycle", "0") == before  # decay clock did not advance
    finally:
        svc.close()


def test_cycle_counter_advances_on_success(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        from cdms.consolidate import Consolidator
        con = Consolidator(cfg, db=svc.db, embedder=svc.embedder)
        con.run()
        assert int(svc.db.get_meta("cycle", "0")) == 1
        con.run()
        assert int(svc.db.get_meta("cycle", "0")) == 2
    finally:
        svc.close()


# --- M4: migration ordering + idempotent column adds ----------------------- #
def test_migration_v2_to_v3(tmp_path):
    dbfile = tmp_path / "memory.db"
    raw = sqlite3.connect(str(dbfile))
    raw.execute("""CREATE TABLE mem_gist (id TEXT PRIMARY KEY, subject TEXT, relation TEXT,
                   object TEXT, valence REAL, frequency INT, support_count INT,
                   survived_cycles INT, project TEXT)""")
    raw.execute("""CREATE TABLE mem_scars (id TEXT PRIMARY KEY, timestamp TEXT,
                   crisis_trigger TEXT, remediation_rule TEXT, project TEXT)""")
    raw.execute("PRAGMA user_version = 2")
    raw.execute("INSERT INTO mem_scars VALUES ('s1','2026-01-01T00:00:00Z','t','r','')")
    raw.commit()
    raw.close()

    db = Database(Config(home=tmp_path))
    try:
        gcols = {r[1] for r in db.conn.execute("PRAGMA table_info(mem_gist)")}
        scols = {r[1] for r in db.conn.execute("PRAGMA table_info(mem_scars)")}
        assert {"last_reinforced", "last_cycle", "centroid"} <= gcols
        assert "origin" in scols
        assert db.conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        # legacy scar survives and defaults to a trusted (pinned) origin
        scars = db.all_scars()
        assert scars and scars[0].origin == "pinned"
    finally:
        db.close()

    # Reopening is idempotent (no error, version stable).
    db2 = Database(Config(home=tmp_path))
    try:
        assert db2.conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    finally:
        db2.close()
