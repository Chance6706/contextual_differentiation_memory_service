"""Cycle 8 — M-M-3: cap the total associative boost a single write may inject.

`_associate` boosts up to 6 KNN neighbours per write; previously the total was unbounded
(η·sim·s_new summed across neighbours). One write now injects at most
`assoc_boost_cap_frac * s_new` across its neighbourhood, scaled down proportionally if
exceeded — bounding cross-episode amplification between consolidations.
"""

from __future__ import annotations

from cdms.config import Config
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent

_TXT = ("recurring similar task", "same kind of action that repeats", "ok")


def _run_assoc(tmp_path, **over):
    """Ingest 6 similar episodes, then one more (the write); return (total boost the write
    injected into the 6 pre-existing neighbours, the write's own base_salience)."""
    cfg = Config(home=tmp_path)
    cfg.assoc_sim_floor = 0.0            # all neighbours qualify
    cfg.dedup_sim_threshold = 0.999      # don't merge them
    cfg.retention_floor = 0.0            # don't evict
    for k, v in over.items():
        setattr(cfg, k, v)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        for _ in range(6):
            svc.ingest(TurnEvent(*_TXT, project="P"))
        before = {e.id: e.base_salience for e in svc.db.all_episodic()}
        rec = svc.ingest(TurnEvent(*_TXT, project="P"))
        after = {e.id: e.base_salience for e in svc.db.all_episodic()}
        injected = sum(after[i] - before[i] for i in before if i in after)
        return injected, rec.base_salience
    finally:
        svc.close()


def test_mm3_total_boost_is_capped(tmp_path):
    injected, s_new = _run_assoc(tmp_path, assoc_eta=0.5, assoc_boost_cap_frac=0.1)
    cap = 0.1 * s_new
    assert injected > 0, "neighbours were not boosted at all (cap test would be vacuous)"
    assert injected <= cap + 1e-6, f"per-write boost {injected} exceeded cap {cap}"


def test_mm3_without_cap_far_more_is_injected(tmp_path):
    # Same neighbourhood, generous cap: the unscaled total is many times the small cap above,
    # confirming the cap in the previous test is what limited the injection.
    injected, s_new = _run_assoc(tmp_path, assoc_eta=0.5, assoc_boost_cap_frac=100.0)
    assert injected > 0.1 * s_new + 1e-6
