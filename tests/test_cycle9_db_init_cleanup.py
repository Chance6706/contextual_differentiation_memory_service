"""Cycle 9 #8 — Database.__init__ never leaks its sqlite connection on a partial failure.

__init__ opens self.conn, then runs _init_schema() and _reconcile_vec_version(). Before the fix,
a non-corruption DatabaseError (re-raised, not quarantined) or any later failure propagated out of
__init__ with the connection still open and the half-built object discarded unclosed — a handle
leak (and on Windows a held file lock). The fix closes whatever was opened before re-raising.
"""

from __future__ import annotations

import sqlite3

import pytest

from cdms.config import Config
from cdms.db import Database


class _FakeConn:
    def __init__(self):
        self.closed = 0

    def close(self):
        self.closed += 1


def test_8_non_corruption_init_failure_closes_connection(monkeypatch, tmp_path):
    cfg = Config(home=tmp_path)
    fake = _FakeConn()
    monkeypatch.setattr(Database, "_open", lambda self, path: fake)
    # A non-corruption DatabaseError (ProgrammingError is a DatabaseError subclass, but its message
    # carries no corruption signature) is re-raised rather than quarantined — the leak path.
    monkeypatch.setattr(Database, "_init_schema",
                        lambda self: (_ for _ in ()).throw(sqlite3.ProgrammingError("schema boom")))
    with pytest.raises(sqlite3.ProgrammingError):
        Database(cfg)
    assert fake.closed == 1, "connection was leaked on a non-corruption init failure"


def test_8_failure_after_schema_also_closes_connection(monkeypatch, tmp_path):
    # A failure in the post-schema vec-version reconcile must also clean up.
    cfg = Config(home=tmp_path)
    fake = _FakeConn()
    monkeypatch.setattr(Database, "_open", lambda self, path: fake)
    monkeypatch.setattr(Database, "_init_schema", lambda self: None)
    monkeypatch.setattr(Database, "_reconcile_vec_version",
                        lambda self: (_ for _ in ()).throw(RuntimeError("vec reconcile boom")))
    with pytest.raises(RuntimeError):
        Database(cfg)
    assert fake.closed == 1, "connection was leaked when reconcile failed after schema init"


def test_8_healthy_init_still_works(tmp_path):
    # Regression: the cleanup wrapper must not disturb the normal construction path.
    cfg = Config(home=tmp_path)
    db = Database(cfg)
    try:
        assert db.conn is not None
        db.set_meta("cycle", 1)
        assert db.get_meta("cycle") == "1"
    finally:
        db.close()
