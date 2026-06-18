"""Regression tests for cross-project isolation (Cycle-2 HIGH findings).

  - consolidation must not merge episodes from different projects into one gist
    (cross-project identity contamination), even when subjects collide by basename;
  - retrieve() must scope to the given project + global memories;
  - upsert_fact identity is keyed by project (basename collision stays distinct).
"""

from __future__ import annotations

from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent


_ACTIONS = [
    "edited the auth token refresh handler",
    "fixed the auth token expiry logic",
    "tested the auth token validation flow",
    "refactored the auth token cache layer",
]


def _seed(svc, project, outcome, success):
    # Same topic (clusters together) but varied phrasing (survives dedup).
    for act in _ACTIONS:
        svc.ingest(TurnEvent(
            trigger_prompt="work on the auth token system",
            action_taken=act, outcome_feedback=outcome, project=project, success=success,
            session_id=f"{project}-s"))


def test_consolidation_does_not_merge_across_projects_or_collide(cfg):
    """Two repos sharing the basename 'app', same topic, OPPOSITE outcomes — must
    stay two distinct gists with opposite dispositions, not one blended identity."""
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        _seed(svc, "/work/client/app", "failed with an error, exception in the log", success=False)
        _seed(svc, "/home/me/app", "passed cleanly, all tests green", success=True)
        Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()

        app_gists = [g for g in svc.db.all_gist() if g.subject == "app"]
        projects = {g.project for g in app_gists}
        assert projects == {"/work/client/app", "/home/me/app"}, projects  # not merged
        by_proj = {g.project: g for g in app_gists}
        # opposite dispositions preserved (no cross-project valence contamination)
        assert by_proj["/work/client/app"].relation == "has_trouble_with"
        assert by_proj["/home/me/app"].relation == "handles_well"
    finally:
        svc.close()


def test_retrieve_scopes_to_project_plus_global(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        svc.ingest(TurnEvent(trigger_prompt="deploy alphasecret service",
                             action_taken="touched alphasecret config", outcome_feedback="done",
                             project="/work/A"))
        svc.ingest(TurnEvent(trigger_prompt="deploy betapublic service",
                             action_taken="touched betapublic config", outcome_feedback="done",
                             project="/work/B"))
        # From project B, A's memory must not surface.
        b_hits = svc.retrieve("alphasecret", top_k=5, project="/work/B", reinforce=False)
        assert not any("alphasecret" in h.text for h in b_hits)
        # From project A, it does.
        a_hits = svc.retrieve("alphasecret", top_k=5, project="/work/A", reinforce=False)
        assert any("alphasecret" in h.text for h in a_hits)
        # Unscoped (CLI) still returns it.
        assert any("alphasecret" in h.text for h in svc.retrieve("alphasecret", top_k=5, reinforce=False))
    finally:
        svc.close()


def test_upsert_fact_identity_keyed_by_project(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        g1 = svc.upsert_fact("app", "handles_well", "routing", project="/work/x")
        g2 = svc.upsert_fact("app", "handles_well", "routing", project="/home/y")
        assert g1.id != g2.id                       # distinct repos -> distinct gists
        assert {g.project for g in svc.db.all_gist()} == {"/work/x", "/home/y"}
    finally:
        svc.close()
