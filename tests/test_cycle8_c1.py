"""Cycle 8 — C-1: memory-bounded consolidation (per-project dedup + aggregation).

The vector-heavy steps (dedup, gist aggregation) now scope per project so the resident
vector matrix is bounded by the largest single project, not the whole store. Budget
renormalization stays global. The one behaviour change is that cross-project near-duplicates
no longer merge — a fix for a latent cross-project budget leak. These tests pin both the
preserved within-project behaviour and the corrected cross-project behaviour.
"""

from __future__ import annotations

from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent

_DUP = ("a recurring task description", "the identical action that was taken", "ok")


def _svc(tmp_path):
    cfg = Config(home=tmp_path)
    cfg.dedup_sim_threshold = 0.95
    cfg.retention_floor = 0.0          # isolate dedup: don't let low-salience episodes evict
    return MemoryService(cfg, embedder=Embedder(cfg)), cfg


def test_c1_within_project_duplicates_still_merge(tmp_path):
    """Within a project, near-identical episodes still dedup (behaviour preserved)."""
    svc, cfg = _svc(tmp_path)
    try:
        svc.ingest(TurnEvent(*_DUP, project="A"))
        svc.ingest(TurnEvent(*_DUP, project="A"))
        rep = Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        assert rep.deduped == 1
        assert len(svc.db.all_episodic()) == 1
    finally:
        svc.close()


def test_c1_cross_project_duplicates_not_merged(tmp_path):
    """Identical episodes in DIFFERENT projects must NOT merge (the latent cross-project
    budget-leak fix). On the pre-C-1 global dedup this would have reported deduped == 1 and
    dropped one project's episode."""
    svc, cfg = _svc(tmp_path)
    try:
        svc.ingest(TurnEvent(*_DUP, project="A"))
        svc.ingest(TurnEvent(*_DUP, project="B"))
        rep = Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        assert rep.deduped == 0
        assert {e.project for e in svc.db.all_episodic()} == {"A", "B"}
    finally:
        svc.close()


def test_c1_mixed_dedup_is_per_project(tmp_path):
    """Two dups in A + two dups in B → one survivor per project (2 deduped total), proving
    dedup is scoped per project and folds within-project only."""
    svc, cfg = _svc(tmp_path)
    try:
        for _ in range(2):
            svc.ingest(TurnEvent(*_DUP, project="A"))
        for _ in range(2):
            svc.ingest(TurnEvent(*_DUP, project="B"))
        rep = Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        assert rep.deduped == 2
        survivors = svc.db.all_episodic()
        assert len(survivors) == 2
        assert {e.project for e in survivors} == {"A", "B"}
    finally:
        svc.close()


def test_c1_per_project_aggregation_unchanged(tmp_path):
    """Per-project gist aggregation still forms a project-scoped gist (byte-identical path);
    the gist's project column matches and no cross-project contamination occurs."""
    svc, cfg = _svc(tmp_path)
    cfg.dedup_sim_threshold = 0.999     # don't merge the cluster members away before aggregation
    cfg.cluster_sim_threshold = 0.5
    cfg.min_cluster_support = 2
    try:
        for tag in ("alpha", "beta", "gamma"):
            svc.ingest(TurnEvent(f"optimize the postgres index {tag}",
                                 f"added an index to speed the query {tag}",
                                 "query latency dropped", success=True, project="proj-X"))
        Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        gists = svc.db.all_gist()
        assert gists, "no gist formed from a same-project cluster"
        assert all(g.project == "proj-X" for g in gists)
    finally:
        svc.close()
