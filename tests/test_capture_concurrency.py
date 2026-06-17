"""Regression test for H2: concurrent drains must not lose events.

A single fixed ".processing" claim path let two overlapping drains clobber each
other's in-flight file, silently dropping a whole session's captured turns. With
a unique per-drain claim name the atomic rename picks one winner per queue
snapshot and nothing is lost.
"""

from __future__ import annotations

import threading
import time

from cdms.embeddings import Embedder
from cdms.pipeline import drain_and_ingest
from cdms.spool import spool_event
from cdms.store import MemoryService


def _ev(i: int) -> dict:
    return {"hook_event_name": "PostToolUse", "session_id": "s", "tool_name": "Bash",
            "tool_input": {"i": i}, "tool_output": f"result {i} ok done", "cwd": "proj"}


def test_concurrent_overlapping_drains_lose_no_events(cfg, monkeypatch):
    for i in range(8):                      # wave 1
        spool_event(cfg, _ev(i))

    orig = MemoryService.ingest

    def slow(self, ev):                     # make the drain slow so the two overlap
        time.sleep(0.01)
        return orig(self, ev)

    monkeypatch.setattr(MemoryService, "ingest", slow)

    counts: list[int] = []

    def drain():
        svc = MemoryService(cfg, embedder=Embedder(cfg))
        try:
            counts.append(drain_and_ingest(cfg, svc))
        finally:
            svc.close()

    a = threading.Thread(target=drain)
    a.start()
    time.sleep(0.02)                        # let A claim wave 1 and start ingesting
    for i in range(8, 16):                  # wave 2 appended DURING A's drain
        spool_event(cfg, _ev(i))
    b = threading.Thread(target=drain)
    b.start()
    a.join()
    b.join()

    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        n = len(svc.db.all_episodic())
    finally:
        svc.close()
    assert sum(counts) == 16, f"events lost: drained {counts}"
    assert n == 16, f"store has {n}, expected 16"


def test_spool_appends_are_well_formed_under_concurrency(cfg):
    import json

    threads = [threading.Thread(target=lambda i=i: [spool_event(cfg, _ev(i * 100 + j)) for j in range(50)])
               for i in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    lines = cfg.queue_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 8 * 50
    for ln in lines:                        # no torn/interleaved lines
        json.loads(ln)
