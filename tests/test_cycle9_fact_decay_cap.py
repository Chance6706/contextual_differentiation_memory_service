"""Cycle 9 #5 — explicit facts cannot become decay-immortal via unbounded support_count.

upsert_fact() increments support_count by 1 on every call with no cap, while gist decay is
strength = support_count * gist_decay_per_cycle ** idle. So a frequently re-asserted explicit
fact ratchets its idle-survival up without limit. The fix caps the support_count that counts
toward decay resistance (gist_support_decay_cap, default 100 — well above any real cluster size),
so inferred gists are untouched and only the runaway explicit fact is bounded. The STORED
support_count is left intact (ranking still reflects true support).
"""

from __future__ import annotations

import pytest

from cdms.config import Config, load_config
from cdms.consolidate import ConsolidationReport, Consolidator
from cdms.embeddings import Embedder
from cdms.models import Gist, new_id
from cdms.store import MemoryService


def _insert_gist(svc, support_count, last_cycle=0):
    g = Gist(id=new_id("gist"), subject="user", relation="prefers", object="tabs",
             support_count=support_count, last_cycle=last_cycle, project="P")
    svc.db.insert_gist(g, svc.embedder.embed_one(g.search_text()))
    return g


def _ids(svc):
    return {g.id for g in svc.db.all_gist()}


def test_5_unbounded_support_no_longer_grants_immortality(tmp_path):
    # At idle=500: capped support (100) -> strength 100*0.985^500 ~= 0.05 < floor 0.25 -> decays.
    # Uncapped support (10000) -> ~5.25 > floor -> would survive forever. The cap forces decay.
    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        g = _insert_gist(svc, support_count=10_000, last_cycle=0)
        rep = ConsolidationReport()
        Consolidator(cfg, db=svc.db, embedder=svc.embedder)._decay_gists(rep, cycle=500)
        assert g.id not in _ids(svc), "a fact with runaway support_count never decayed"
    finally:
        svc.close()


def test_5_normal_gist_decay_is_unchanged_by_the_cap(tmp_path):
    # A real consolidated gist (small cluster) is well under the cap, so its decay decision is
    # identical: survives while fresh, decays once genuinely idle.
    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        fresh = _insert_gist(svc, support_count=5, last_cycle=480)   # idle 20 -> persists
        stale = _insert_gist(svc, support_count=5, last_cycle=0)     # idle 500 -> faded
        rep = ConsolidationReport()
        Consolidator(cfg, db=svc.db, embedder=svc.embedder)._decay_gists(rep, cycle=500)
        ids = _ids(svc)
        assert fresh.id in ids, "a recently-reinforced gist was wrongly decayed"
        assert stale.id not in ids, "a long-idle small-support gist failed to decay"
    finally:
        svc.close()


def test_5_support_decay_cap_validator(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    assert load_config().gist_support_decay_cap == Config().gist_support_decay_cap == 100
    monkeypatch.setenv("CDMS_GIST_SUPPORT_DECAY_CAP", "0")        # < 1 is invalid
    assert load_config().gist_support_decay_cap == 100           # restored to default
    monkeypatch.setenv("CDMS_GIST_SUPPORT_DECAY_CAP", "250")     # sane override kept
    assert load_config().gist_support_decay_cap == 250
