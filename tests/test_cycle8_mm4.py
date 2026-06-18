"""Cycle 8 — M-M-4: valence-EMA poisoning. Adaptive EMA (rate ∝ 1/sqrt(prior support)) so an
ESTABLISHED trait can't be flipped by a couple of injected episodes, while a fresh trait stays
malleable and sustained REAL change still flips.
"""

from __future__ import annotations

from cdms.config import Config, load_config
from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent


def _svc(tmp_path, **over):
    cfg = Config(home=tmp_path)
    cfg.dedup_sim_threshold = 0.999      # keep cluster members distinct (don't merge away)
    cfg.cluster_sim_threshold = 0.5
    cfg.retention_floor = 0.0            # isolate EMA dynamics from eviction
    for k, v in over.items():
        setattr(cfg, k, v)
    return MemoryService(cfg, embedder=Embedder(cfg)), cfg


def _run(svc, cfg):
    return Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()


def _the_gist(svc):
    gs = svc.db.all_gist()
    return gs[0] if len(gs) == 1 else None


def _pos(svc, tag, n, val=0.6):
    for i in range(n):
        svc.ingest(TurnEvent(f"work on auth module {tag}{i}", f"improve the auth module {tag}{i}",
                             "passed cleanly", success=True, valence_hint=val, project="P"))


def _neg(svc, tag, n, val=-0.9):
    for i in range(n):
        svc.ingest(TurnEvent(f"work on auth module {tag}{i}", f"debug the auth module {tag}{i}",
                             "failed with an error", success=False, valence_hint=val, project="P"))


def test_mm4_established_trait_resists_two_injected_episodes(tmp_path):
    svc, cfg = _svc(tmp_path)
    try:
        _pos(svc, "e", 12)                       # establish a well-supported positive trait
        _run(svc, cfg)
        g0 = _the_gist(svc)
        assert g0 is not None and g0.relation == "handles_well"
        assert g0.support_count >= 10

        _neg(svc, "n", 2)                        # inject a small contradicting cluster
        _run(svc, cfg)
        g1 = next(g for g in svc.db.all_gist() if g.id == g0.id)
        assert g1.frequency > g0.frequency, "injected episodes did not reach the established gist"
        assert g1.relation == "handles_well", "established trait was flipped by 2 episodes (M-M-4)"
    finally:
        svc.close()


def test_mm4_fresh_trait_is_still_malleable(tmp_path):
    """A weakly-supported trait must still be flippable by contradicting evidence (we did not
    just freeze everything)."""
    svc, cfg = _svc(tmp_path)
    try:
        _pos(svc, "e", 2)                        # weak positive trait (support ~2)
        _run(svc, cfg)
        g0 = _the_gist(svc)
        assert g0 is not None and g0.relation == "handles_well"

        flipped = False
        for r in range(6):                       # sustained contradicting evidence
            _neg(svc, f"r{r}", 2)
            _run(svc, cfg)
            if next(g for g in svc.db.all_gist() if g.id == g0.id).relation != "handles_well":
                flipped = True
                break
        assert flipped, "a fresh trait never flipped under sustained contradiction"
    finally:
        svc.close()


def test_mm4_ema_floor_clamped_below_base(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_GIST_VALENCE_EMA", "0.3")
    monkeypatch.setenv("CDMS_GIST_VALENCE_EMA_MIN", "0.9")   # floor > base: must clamp down
    cfg = load_config()
    assert cfg.gist_valence_ema_min <= cfg.gist_valence_ema
