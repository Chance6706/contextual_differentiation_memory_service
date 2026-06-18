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
def test_chigh1_drain_serialized_under_cross_process_lock(tmp_path, monkeypatch):
    """Drain must hold the cross-process lock so it can't ingest into a store that a
    consolidation/forget is mid-pass on. With the lock held elsewhere, drain SKIPS
    (returns 0) and leaves the spool intact for the next drain (C-HIGH-1 / C-HIGH-3)."""
    import json

    from cdms import pipeline
    from cdms.embeddings import Embedder
    from cdms.lock import cross_process_lock
    from cdms.pipeline import drain_and_ingest
    from cdms.store import MemoryService

    monkeypatch.setattr(pipeline, "_DRAIN_LOCK_TIMEOUT", 0.2)  # keep the test fast
    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    events = [
        {"hook_event_name": "UserPromptSubmit", "session_id": "s", "prompt": "do x", "cwd": "/p"},
        {"hook_event_name": "PostToolUse", "session_id": "s", "tool_name": "Edit",
         "tool_input": "f", "tool_output": "ok", "cwd": "/p"},
    ]
    cfg.queue_path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

    with cross_process_lock(cfg.lock_path):          # simulate a concurrent consolidation
        n_blocked = drain_and_ingest(cfg, svc)
    assert n_blocked == 0                            # drain skipped rather than racing in
    assert cfg.queue_path.exists()                   # spool preserved (atomic claim never fired)

    n_after = drain_and_ingest(cfg, svc)             # lock free now → drains
    assert n_after >= 1
    svc.close()


def _seed_gist(svc, cfg, sessions, project="p", per=3):
    """Form ONE gist supported by `per` distinct-but-similar episodes per session.
    Distinct text (per-episode tag) + a high dedup / low cluster threshold so the
    episodes CLUSTER into a gist rather than being deduped away (cf. test_consolidate)."""
    from cdms.consolidate import Consolidator
    from cdms.store import TurnEvent

    cfg.dedup_sim_threshold = 0.999
    cfg.cluster_sim_threshold = 0.5
    cfg.min_cluster_support = 2
    tags = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
    t = 0
    for sess in sessions:
        for _ in range(per):
            tag = tags[t % len(tags)]
            t += 1
            svc.ingest(TurnEvent(
                f"postgres index added to speed up the orders query {tag}",
                f"edited the orders query and added an index {tag}",
                "query performance improved", tool_name="Edit", success=True,
                session_id=sess, project=project))
    Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()


def test_a2m1_session_forget_removes_session_derived_gist(tmp_path):
    """forget(session=...) must also drop a gist that exists ONLY because of that
    session — previously the aggregated trait survived (right-to-forget leak)."""
    from cdms.embeddings import Embedder
    from cdms.store import MemoryService

    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    _seed_gist(svc, cfg, ["s1"])
    assert svc.db.stats()["gist"] >= 1
    svc.forget(session="s1")
    assert svc.db.stats()["episodic"] == 0
    assert svc.db.stats()["gist"] == 0          # session-derived trait removed (A2-M1)
    svc.close()


def test_a2m1_cross_session_gist_survives_session_forget(tmp_path):
    """...but a gist supported by MULTIPLE sessions is a genuine multi-session trait and
    must NOT be deleted when only one of its sessions is forgotten."""
    from cdms.embeddings import Embedder
    from cdms.store import MemoryService

    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    _seed_gist(svc, cfg, ["s1", "s2"])
    g0 = svc.db.stats()["gist"]
    assert g0 >= 1
    svc.forget(session="s1")
    assert svc.db.stats()["gist"] == g0         # cross-session trait preserved
    svc.close()


def test_cmed6_multiword_negation_not_read_as_failure():
    from cdms.pipeline import _infer_success

    # multi-word negators (>10 chars from the marker) must NOT read as failure now
    assert _infer_success("successfully resolved without any errors") is True
    assert _infer_success("the deploy completed; zero failures remained") is True
    # ...but a negator far back must NOT wrongly negate a real failure
    assert _infer_success("no backups existed and the deploy failed") is False


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
