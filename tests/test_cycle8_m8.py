"""Cycle 8 — M-8: runtime sqlite-vec (vec0) version pin.

The embedder fingerprint guards the embedding SPACE; it does not cover the vec0 on-disk
index FORMAT. A sqlite-vec upgrade could change that format and silently break KNN. We pin
the vec version on first open and WARN (not refuse — most upgrades are format-compatible) if
it changes under an existing store.
"""

from __future__ import annotations

from cdms.config import Config
from cdms.db import Database


def _vec_version(db):
    return db.conn.execute("SELECT vec_version()").fetchone()[0]


def test_m8_vec_version_pinned_on_first_open(tmp_path):
    db = Database(Config(home=tmp_path))
    try:
        assert db.get_meta("vec_version") == _vec_version(db)
    finally:
        db.conn.close()


def test_m8_stats_exposes_pinned_vec_version(tmp_path):
    db = Database(Config(home=tmp_path))
    try:
        assert db.stats()["vec_version_pinned"] == _vec_version(db)
    finally:
        db.conn.close()


def test_m8_vec_version_change_warns_and_reconciles(tmp_path, capsys):
    cfg = Config(home=tmp_path)
    db = Database(cfg)
    db.set_meta("vec_version", "v0.0.0-test-old")     # simulate a store built on an older vec
    db.conn.close()
    capsys.readouterr()                               # drop any setup output

    db2 = Database(cfg)                               # reopen -> detects the mismatch
    try:
        err = capsys.readouterr().err
        assert "sqlite-vec" in err and "v0.0.0-test-old" in err, err
        assert db2.get_meta("vec_version") == _vec_version(db2)   # reconciled to current
    finally:
        db2.conn.close()
