"""Cycle 9 #1 — associative boost cannot, by itself, manufacture a scar.

The associative boost (store._associate) is a recall-ranking signal: the present retroactively
raises the salience of related faded episodes. It is bounded per-write (M-M-3 cap) and saturates
well below crisis for any sane config (KNN crowding limits how much a single target accumulates).
But for the worst-case VALID config (assoc_eta/assoc_boost_cap_frac at their post-PR-A ceiling of
1.0), a flood of benign-but-embedding-similar writes could lift a planted sub-crisis catastrophe
~+0.6 — enough to tip a memory already near crisis OVER the scar-elevation gate
(base_salience >= crisis_threshold) and mint a permanent guardrail it never earned.

Fix: a boost may raise a neighbour toward crisis but never across it. A memory that reaches crisis
on its own S0 still elevates; boost alone cannot.
"""

from __future__ import annotations

import os

import pytest

from cdms.config import Config
from cdms.consolidate import ConsolidationReport, Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent

_NEUTRAL = ("deployment pipeline schema migration users table records production database "
            "staging rollout config metrics")


def _worst_case_cfg(tmp_path):
    cfg = Config(home=tmp_path)
    cfg.assoc_eta = 1.0                 # post-PR-A ceiling — maximally aggressive
    cfg.assoc_boost_cap_frac = 1.0
    cfg.assoc_sim_floor = 0.0
    return cfg


def _plant_catastrophe(svc, base_salience, valence=-0.9):
    victim = svc.ingest(TurnEvent(
        trigger_prompt=f"{_NEUTRAL} incident review",
        action_taken="ran the migration on the users table during the deployment pipeline",
        outcome_feedback="deleted production database -- data loss, cannot recover",
        valence_hint=valence, project="P"))
    svc.db.set_salience([(victim.id, base_salience)])
    return victim


def _flood(svc, n):
    for i in range(n):
        svc.ingest(TurnEvent(
            trigger_prompt=f"{_NEUTRAL} routine note {i}",
            action_taken=f"reviewed the {_NEUTRAL} dashboard and updated config entry {i}",
            outcome_feedback="all checks passed, looks good",
            valence_hint=0.3, project="P"))


def test_1_boost_flood_cannot_push_subcrisis_catastrophe_into_a_scar(tmp_path):
    cfg = _worst_case_cfg(tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        # 2.5 is sub-crisis (crisis_threshold 3.0) but within the boost saturation band; pre-fix a
        # benign flood tips it over and elevates a scar.
        victim = _plant_catastrophe(svc, base_salience=2.5)
        _flood(svc, 40)

        v = svc.db.get_episodic(victim.id)
        assert v.base_salience < cfg.crisis_threshold, "boost lifted the victim across the crisis gate"

        rep = ConsolidationReport()
        Consolidator(cfg, db=svc.db, embedder=svc.embedder)._elevate_scars(svc.db.all_episodic(), rep)
        assert rep.scars_created == 0, "associative boost manufactured a scar"
    finally:
        svc.close()


def test_1_memory_that_earns_crisis_on_its_own_still_elevates(tmp_path):
    # The clamp must not block legitimate elevation: a catastrophe whose OWN salience reaches
    # crisis still becomes a scar (no flood involved).
    cfg = _worst_case_cfg(tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        _plant_catastrophe(svc, base_salience=3.5)   # earned >= crisis on its own
        rep = ConsolidationReport()
        Consolidator(cfg, db=svc.db, embedder=svc.embedder)._elevate_scars(svc.db.all_episodic(), rep)
        assert rep.scars_created == 1
    finally:
        svc.close()


def test_1_boost_still_raises_a_faded_neighbour_below_crisis(tmp_path):
    # The boost mechanism itself is not disabled — far from crisis it still strengthens a related
    # faded episode (this is its job; only the crisis-crossing is forbidden).
    cfg = _worst_case_cfg(tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        faded = svc.ingest(TurnEvent(
            trigger_prompt=f"{_NEUTRAL} earlier observation",
            action_taken=f"noted the {_NEUTRAL} baseline", outcome_feedback="ok", project="P"))
        svc.db.set_salience([(faded.id, 0.2)])        # low, well below crisis
        before = svc.db.get_episodic(faded.id).base_salience
        # A related write should retroactively boost it.
        svc.ingest(TurnEvent(
            trigger_prompt=f"{_NEUTRAL} follow-up",
            action_taken=f"revisited the {_NEUTRAL} baseline again", outcome_feedback="ok", project="P"))
        after = svc.db.get_episodic(faded.id).base_salience
        assert after > before, "associative boost no longer strengthens a faded neighbour"
        assert after < cfg.crisis_threshold
    finally:
        svc.close()
