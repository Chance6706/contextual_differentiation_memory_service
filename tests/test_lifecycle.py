"""Regression tests for the right-to-forget lifecycle (Cycle-2 HIGH).

Before this, there was no way to delete a leaked secret, a toxic trait, or an
ex-client's data — and scars had no deletion primitive at all.
"""

from __future__ import annotations

import pytest

from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent


def test_forget_by_project(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        svc.ingest(TurnEvent(trigger_prompt="A", action_taken="a", outcome_feedback="o", project="/A"))
        svc.ingest(TurnEvent(trigger_prompt="B", action_taken="b", outcome_feedback="o", project="/B"))
        svc.pin_scar("crisis A", "rule A", project="/A")
        svc.upsert_fact("A", "handles_well", "thing", project="/A")

        res = svc.forget(project="/A")
        assert res["episodic"] == 1 and res["scars"] == 1 and res["gist"] == 1
        # /B survives
        assert [e.project for e in svc.db.all_episodic()] == ["/B"]
        assert svc.db.all_scars() == []
    finally:
        svc.close()


def test_forget_by_session(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        svc.ingest(TurnEvent(trigger_prompt="x", action_taken="a", outcome_feedback="o",
                             project="/A", session_id="s1"))
        svc.ingest(TurnEvent(trigger_prompt="y", action_taken="a", outcome_feedback="o",
                             project="/A", session_id="s2"))
        res = svc.forget(session="s1")
        assert res["episodic"] == 1
        assert {e.session_id for e in svc.db.all_episodic()} == {"s2"}
    finally:
        svc.close()


def test_forget_by_id_scar(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        sc = svc.pin_scar("leaked secret", "rotate it", project="/A")
        res = svc.forget(ids=[sc.id])
        assert res["scars"] == 1
        assert svc.db.all_scars() == []
    finally:
        svc.close()


def test_forget_requires_a_selector(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        with pytest.raises(ValueError):
            svc.forget()  # must not blanket-wipe
    finally:
        svc.close()
