"""Cycle 8 — H-M-2: budget-exhaustion mitigation via a per-session cap.

Within a project's conserved-salience share, no single session may hold more than
``session_budget_cap``. This bounds a flood concentrated in one session (e.g. the empty/
default session that MCP-injected notes share) from diluting real per-session memory below
the retention floor. Magnitude was already bounded by H-2 (S0 cap) + M-3 (no goal_hint);
this caps the volume/concentration lever.
"""

from __future__ import annotations

from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent


def _svc(tmp_path, **over):
    cfg = Config(home=tmp_path)
    cfg.retention_floor = 0.0          # isolate the budget allocation from eviction
    for k, v in over.items():
        setattr(cfg, k, v)
    return MemoryService(cfg, embedder=Embedder(cfg)), cfg


def _ingest_session(svc, project, session, n, prefix):
    for i in range(n):
        svc.ingest(TurnEvent(f"{prefix} trigger {i}", f"{prefix} action {i}", "ok",
                             project=project, session_id=session))


def test_hm2_flood_session_capped_within_project(tmp_path):
    """A 1-real-turn legitimate session must keep a protected slice of the project budget when
    a second session floods it with many low-value turns — the flood session is capped at
    session_budget_cap of the project's share."""
    svc, cfg = _svc(tmp_path, session_budget_cap=0.5, salience_budget=1000.0)
    try:
        _ingest_session(svc, "P", "legit", 1, "legit")
        _ingest_session(svc, "P", "flood", 50, "flood")
        Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        eps = svc.db.all_episodic()
        legit = [e for e in eps if e.session_id == "legit"]
        flood = [e for e in eps if e.session_id == "flood"]
        legit_total = sum(e.base_salience for e in legit)
        flood_total = sum(e.base_salience for e in flood)
        # Single project => its whole share is the budget; the flood session is capped at 50%,
        # so the lone legit turn's session retains the other ~50% (vs ~2% under a flat split).
        assert flood_total <= 0.5 * cfg.salience_budget + 1e-6
        assert legit_total >= 0.5 * cfg.salience_budget - 1e-6
    finally:
        svc.close()


def test_hm2_single_session_project_unchanged(tmp_path):
    """A project with a single session gets its whole share (the cap never binds) — the
    pre-H-M-2 behaviour is preserved for the common single-session case."""
    svc, cfg = _svc(tmp_path, session_budget_cap=0.5, salience_budget=1000.0)
    try:
        _ingest_session(svc, "P", "only", 6, "x")
        Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        total = sum(e.base_salience for e in svc.db.all_episodic())
        assert abs(total - cfg.salience_budget) < 1e-3   # whole budget, uncapped
    finally:
        svc.close()


def test_hm2_balanced_sessions_roughly_even(tmp_path):
    """Two balanced sessions in a project split its share without the cap distorting them
    (each ~50%, both under the 0.5 cap boundary)."""
    svc, cfg = _svc(tmp_path, session_budget_cap=0.6, salience_budget=1000.0)
    try:
        _ingest_session(svc, "P", "s1", 5, "alpha")
        _ingest_session(svc, "P", "s2", 5, "beta")
        Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        eps = svc.db.all_episodic()
        s1 = sum(e.base_salience for e in eps if e.session_id == "s1")
        s2 = sum(e.base_salience for e in eps if e.session_id == "s2")
        assert abs((s1 + s2) - cfg.salience_budget) < 1e-3   # budget conserved
        assert min(s1, s2) > 0.25 * cfg.salience_budget       # neither session starved
    finally:
        svc.close()
