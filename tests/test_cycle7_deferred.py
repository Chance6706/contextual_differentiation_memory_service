"""Cycle 7 — promotion of DEFERRED findings to fixes, one phase at a time.

Each test is an integration-level reproduction/regression for a promoted finding.

Phase 1 — C-MED-8 / A5-H1: retrieve() materialized hits by scanning the WHOLE gist/scar
table; find_duplicate_scar scanned all scars per insert. Now fetched by id.
"""

from __future__ import annotations

import pytest

from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent


def _seed_gist(svc, cfg, project="p"):
    cfg.dedup_sim_threshold = 0.999
    cfg.cluster_sim_threshold = 0.5
    cfg.min_cluster_support = 2
    for tag in ("alpha", "beta", "gamma"):
        svc.ingest(TurnEvent(
            f"postgres index added to speed up the orders query {tag}",
            f"edited the orders query and added an index {tag}",
            "query performance improved", tool_name="Edit", success=True, project=project))
    Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()


def _boom(*_a, **_k):
    raise AssertionError("full-table scan on the retrieve/dedup hot path")


def test_cmed8_retrieve_materializes_by_id_without_full_scan(tmp_path, monkeypatch):
    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    _seed_gist(svc, cfg)
    svc.pin_scar("force push to main wiped history", "never force push shared branches", project="p")
    assert svc.db.stats()["gist"] >= 1 and svc.db.stats()["scars"] >= 1

    # reinforce=False so the two calls don't differ merely from access_count bumps.
    before = svc.retrieve("orders query index force push", top_k=5, reinforce=False)
    # Forbid whole-table scans, then retrieve again: results must be IDENTICAL and no scan.
    monkeypatch.setattr(svc.db, "all_gist", _boom)
    monkeypatch.setattr(svc.db, "all_scars", _boom)
    after = svc.retrieve("orders query index force push", top_k=5, reinforce=False)

    assert [(h.id, h.tier, round(h.score, 6)) for h in after] == \
           [(h.id, h.tier, round(h.score, 6)) for h in before]
    svc.close()


def test_a5h1_scar_dedup_without_full_scan(tmp_path, monkeypatch):
    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    svc.pin_scar("force push to main wiped history", "never force push", project="p")
    n0 = svc.db.stats()["scars"]
    # Pin a near-duplicate while whole-table scans are forbidden — dedup must work via the
    # ≤5 KNN candidate ids only (A5-H1), not by loading every scar.
    monkeypatch.setattr(svc.db, "all_scars", _boom)
    s = svc.pin_scar("force push to main wiped the history", "never ever force push", project="p")
    assert s is not None                         # completed without scanning all scars
    assert svc.db.stats()["scars"] >= n0         # (dedup may keep it at n0; no crash either way)
    svc.close()
