"""Cycle 7 — triage of the open Cycle 4–5 external-report findings.

Discipline: a finding is untrusted until independently reproduced. Each test below is a
reproduction that FAILS on the pre-fix code and passes after the fix, named by the
report id it adjudicates.

Batch 1 (confirmed CRIT/HIGH, clear wins):
  * A7-H1  — config left S0 weights + several thresholds unvalidated (injectable).
  * A0-C1  — _open leaked the OS file handle on a failed open (Windows quarantine brick).
  * C-HIGH-2 / A3-M1 — get_embedder() singleton ignored later config changes.
"""

from __future__ import annotations

import sqlite3

import pytest

from cdms import db as dbmod
from cdms import embeddings
from cdms.config import Config, load_config


# --------------------------------------------------------------------------- #
# A7-H1 — unvalidated config fields (S0 weights + thresholds)
# --------------------------------------------------------------------------- #
def test_a7h1_absurd_config_values_are_clamped(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    # Each of these silently disabled a guard before the fix; they must now clamp.
    monkeypatch.setenv("CDMS_W_SURPRISE", "1e9")            # disable salience gate
    monkeypatch.setenv("CDMS_DEDUP_SIM_THRESHOLD", "2.0")   # disable episodic dedup (cosine<=1)
    monkeypatch.setenv("CDMS_CRISIS_VALENCE_MAX", "5")      # out of [-1,1]
    monkeypatch.setenv("CDMS_RELATION_POS_THRESHOLD", "2")  # out of [-1,1]
    monkeypatch.setenv("CDMS_HTTP_PORT", "999999")          # out of port range
    monkeypatch.setenv("CDMS_GOAL_GATE_FLOOR", "-3")        # out of [0,1]
    d = Config()
    cfg = load_config()
    assert cfg.w_surprise == d.w_surprise            # clamped to default, not 1e9
    assert cfg.dedup_sim_threshold == d.dedup_sim_threshold
    assert cfg.crisis_valence_max == d.crisis_valence_max
    assert cfg.relation_pos_threshold == d.relation_pos_threshold
    assert cfg.http_port == d.http_port
    assert cfg.goal_gate_floor == d.goal_gate_floor


def test_a7h1_sane_overrides_still_accepted(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_W_SURPRISE", "1.5")
    monkeypatch.setenv("CDMS_DEDUP_SIM_THRESHOLD", "0.9")
    cfg = load_config()
    assert cfg.w_surprise == 1.5            # in-range values are NOT clobbered
    assert cfg.dedup_sim_threshold == 0.9


# --------------------------------------------------------------------------- #
# A0-C1 — _open must close the connection on a failed open (no handle leak)
# --------------------------------------------------------------------------- #
def test_a0c1_open_closes_handle_on_failure(monkeypatch, tmp_path):
    import sqlite_vec

    real_connect = sqlite3.connect
    closed = {"n": 0}

    class TrackedConn:
        def __init__(self, c):
            object.__setattr__(self, "_c", c)
        def __getattr__(self, k):
            return getattr(self._c, k)
        def close(self):
            closed["n"] += 1
            return self._c.close()

    monkeypatch.setattr(dbmod.sqlite3, "connect", lambda *a, **k: TrackedConn(real_connect(*a, **k)))
    # Force a failure AFTER the connection is opened (simulates a corrupt/locked store
    # tripping a PRAGMA / extension load).
    monkeypatch.setattr(sqlite_vec, "load",
                        lambda conn: (_ for _ in ()).throw(sqlite3.DatabaseError("boom")))

    with pytest.raises(sqlite3.DatabaseError):
        dbmod.Database._open(tmp_path / "x.db")
    assert closed["n"] >= 1, "open failure leaked the connection handle (Windows quarantine brick)"


# --------------------------------------------------------------------------- #
# C-HIGH-2 / A3-M1 — get_embedder must rebuild when the relevant config changes
# --------------------------------------------------------------------------- #
def test_chigh2_get_embedder_rebuilds_on_config_change(tmp_path):
    embeddings._SINGLETON = None
    embeddings._SINGLETON_KEY = None
    e1 = embeddings.get_embedder(Config(home=tmp_path, embed_max_chars=1600))
    e2 = embeddings.get_embedder(Config(home=tmp_path, embed_max_chars=1600))
    assert e1 is e2                              # identical config → cached (still a singleton)
    e3 = embeddings.get_embedder(Config(home=tmp_path, embed_max_chars=2000))
    assert e3 is not e1                          # config changed → rebuilt, not stale
    assert e3.cfg.embed_max_chars == 2000
    # cleanup so the global doesn't leak into other tests
    embeddings._SINGLETON = None
    embeddings._SINGLETON_KEY = None
