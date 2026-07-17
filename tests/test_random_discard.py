"""Random-discard ablation seam (eval-only control).

Guards the two properties that matter: (1) with discard_policy="salience" (default,
shipped) eviction is UNCHANGED — the branch is a pure no-op; (2) "random" evicts the
SAME COUNT the salience policy would, chosen seeded-random from ALL episodes,
deterministically, and NOT salience-locked. See EVAL_HARNESS IMPLEMENTATION_NOTES Gap 1.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

os.environ["CDMS_EMBED_BACKEND"] = "hash"
os.environ["CDMS_EVAL_MODE"] = "1"   # random-discard is eval-gated; these tests drive it directly

from cdms.config import Config
from cdms.consolidate import ConsolidationReport, Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent


def _make(home, **cfgkw):
    cfg = Config(home=home, **cfgkw)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    ids = [svc.ingest(TurnEvent(f"q{i}", f"a{i}", "", project="P")).id for i in range(6)]
    # first 3 below the retention floor (evictable by salience); last 3 well above (kept).
    svc.db.set_salience([(ids[i], 0.001) for i in range(3)] + [(ids[i], 5.0) for i in range(3, 6)])
    return svc, cfg, ids


def _con(svc, cfg):
    return Consolidator(cfg, db=svc.db, embedder=svc.embedder)


def test_salience_mode_is_a_noop(tmp_path):
    # Default policy evicts EXACTLY the below-floor set — unchanged by the new branch.
    svc, cfg, ids = _make(tmp_path / "s")
    assert cfg.discard_policy == "salience"
    evicted = _con(svc, cfg)._evict(svc.db.all_episodic(), datetime.now(timezone.utc), ConsolidationReport())
    assert evicted == set(ids[:3])          # the 3 low-salience ones, nothing else
    svc.close()


def test_random_matches_salience_count(tmp_path):
    svc, cfg, ids = _make(tmp_path / "r", discard_policy="random", discard_random_seed=1729)
    evicted = _con(svc, cfg)._evict(svc.db.all_episodic(), datetime.now(timezone.utc), ConsolidationReport())
    assert len(evicted) == 3                # rate-matched by COUNT to what salience would evict
    assert evicted <= set(ids)             # drawn from the whole snapshot
    svc.close()


def test_random_is_deterministic(tmp_path):
    # _random_victims (no delete side effect) returns the same subset twice for one seed/cycle.
    svc, cfg, ids = _make(tmp_path / "d", discard_policy="random", discard_random_seed=42)
    con = _con(svc, cfg)
    eps = svc.db.all_episodic()
    a = con._random_victims(eps, n=3)
    b = con._random_victims(eps, n=3)
    assert a == b and len(a) == 3
    svc.close()


def test_random_refuses_outside_eval_mode(tmp_path, monkeypatch):
    # Eval-gate (rule-12 S2): random discard must REFUSE in a non-eval context (production).
    import pytest
    monkeypatch.delenv("CDMS_EVAL_MODE", raising=False)
    svc, cfg, ids = _make(tmp_path / "gate", discard_policy="random", discard_random_seed=1)
    with pytest.raises(RuntimeError):
        _con(svc, cfg)._evict(svc.db.all_episodic(), datetime.now(timezone.utc), ConsolidationReport())
    svc.close()


def test_random_is_not_salience_locked(tmp_path):
    # Across seeds, random forgetting can evict episodes salience would KEEP (ids[3:6]) —
    # the whole point of the null control. (One seed might coincide; the union must not.)
    high = set()
    for seed in range(12):
        svc, cfg, ids = _make(tmp_path / f"n{seed}", discard_policy="random", discard_random_seed=seed)
        picked = set(_con(svc, cfg)._random_victims(svc.db.all_episodic(), n=3))
        high |= (picked & set(ids[3:6]))
        svc.close()
    assert high, "random-discard never touched a high-salience episode across 12 seeds — not random"
