"""Regression tests for Cycle-2 robustness fixes:
  - spool os.write loops on a short write (no swallowed next event);
  - atomic config write is concurrency-safe (unique temp, no leftover tmp);
  - create_link validates endpoints (no dangling/fabricated support edges).
"""

from __future__ import annotations

import json
import os
import threading

import pytest

from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent


def test_spool_loops_on_short_write(cfg, monkeypatch):
    import cdms.spool as sp

    real_write = os.write
    state = {"did_short": False}

    def short_write(fd, data):
        if not state["did_short"]:
            state["did_short"] = True
            return real_write(fd, bytes(data)[:7])  # write only a few bytes first
        return real_write(fd, data)

    monkeypatch.setattr(sp.os, "write", short_write)
    sp.spool_event(cfg, {"hook_event_name": "X", "msg": "hello world " * 5})

    lines = cfg.queue_path.read_text(encoding="utf-8").splitlines()
    assert state["did_short"] and len(lines) == 1
    assert json.loads(lines[0])["msg"].startswith("hello world")


@pytest.mark.xfail(os.name == "nt", reason="Windows raises PermissionError on concurrent rename/open here "
                   "(NTFS vs POSIX file-locking); validated on Linux CI.", strict=False)
def test_atomic_write_concurrent_no_race_no_leftover(tmp_path):
    from cdms.cli import _atomic_write_json

    p = tmp_path / "settings.json"
    errors: list = []

    def w(i):
        try:
            _atomic_write_json(p, {"writer": i})
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    ts = [threading.Thread(target=w, args=(i,)) for i in range(12)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errors
    assert isinstance(json.loads(p.read_text(encoding="utf-8")), dict)  # valid, one winner
    assert not list(tmp_path.glob("*.tmp"))                            # no orphaned temp


def test_fts_handles_non_latin_queries(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        svc.ingest(TurnEvent(trigger_prompt="исправил парсер", action_taken="отладка парсера",
                             outcome_feedback="готово", project="p"))
        assert len(svc.db.fts("episodic", "парсер", 10)) == 1   # Cyrillic reaches the index
        q = svc.db._fts_query('"; DROP TABLE x; -- парсер')      # still injection-safe
        assert "DROP" in q and '";' not in q and "--" not in q
    finally:
        svc.close()


def test_create_link_validates_endpoints(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        assert svc.create_link("ghost1", "ghost2") is False           # dangling -> rejected
        assert svc.db.stats()["support_edges"] == 0
        rec = svc.ingest(TurnEvent(trigger_prompt="t", action_taken="a", outcome_feedback="o"))
        g = svc.upsert_fact("s", "handles_well", "obj")
        assert svc.create_link(rec.id, g.id) is True                  # valid -> created
        assert svc.create_link(rec.id, g.id) is False                 # duplicate -> not newly created
        assert svc.create_link(rec.id, "ghost") is False              # bad target -> rejected
        assert svc.db.stats()["support_edges"] == 1
    finally:
        svc.close()
