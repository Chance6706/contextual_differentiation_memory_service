"""Cycle 8 — low-severity cleanups.

L-1: dedup uses the in-memory survivor (no per-duplicate get_episodic round-trip) and keeps
     it consistent across folds — so a later, lower-salience duplicate can't regress the
     survivor's already-folded (max) salience.
L-S-1: the MCP store tool rejects an unknown `kind` instead of silently filing it as an episode.
"""

from __future__ import annotations

import pytest

import cdms.mcp_server as mcp_server
from cdms.config import Config
from cdms.consolidate import ConsolidationReport, Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent

_TXT = ("identical recurring task", "identical action taken", "ok")


def test_l1_multi_fold_keeps_max_salience_and_sums_access(tmp_path):
    cfg = Config(home=tmp_path)
    cfg.dedup_sim_threshold = 0.95
    cfg.retention_floor = 0.0
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        recs = [svc.ingest(TurnEvent(*_TXT, project="P")) for _ in range(3)]
        s, d1, d2 = (r.id for r in recs)         # rowid order: first kept, rest fold in
        # Survivor low, first dup HIGH, second dup LOW: the second fold must not regress the
        # survivor from the high value (the bug if the in-memory survivor is stale).
        svc.db.set_salience([(s, 0.2), (d1, 0.9), (d2, 0.5)])
        ts = svc.db.get_episodic(s).timestamp
        svc.db.bump_access(d1, 3, ts)
        svc.db.bump_access(d2, 4, ts)

        episodes = svc.db.all_episodic()         # fresh: reflects the salience/access above
        rep = ConsolidationReport()
        Consolidator(cfg, db=svc.db, embedder=svc.embedder)._dedup(episodes, rep)

        assert rep.deduped == 2
        assert svc.db.get_episodic(d1) is None and svc.db.get_episodic(d2) is None
        survivor = svc.db.get_episodic(s)
        assert survivor is not None
        assert survivor.base_salience == 0.9          # max fold, not regressed to 0.5
        assert survivor.access_count == 7             # 0 + 3 + 4 (real access summed)
    finally:
        svc.close()


def _store_fn():
    fn = mcp_server.store
    for attr in ("fn", "func", "__wrapped__"):
        if hasattr(fn, attr) and callable(getattr(fn, attr)):
            return getattr(fn, attr)
    return fn


def test_ls1_unknown_kind_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_EMBED_BACKEND", "hash")
    store = _store_fn()
    with pytest.raises(ValueError):
        store(content="deleted prod | always back up first", kind="scra", project=str(tmp_path))


def test_ls1_known_kinds_accepted(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_EMBED_BACKEND", "hash")
    store = _store_fn()
    r = store(content="a normal observation", kind="episode", project=str(tmp_path))
    assert r.tier == "episodic"
