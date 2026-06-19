"""Cycle 9 quick-win bundle (from the redefined deferred-debt register).

F-2: a corrupt store is quarantined (not silently wiped) AND a durable marker is recorded in the
     fresh store so `cdms stats` can tell the operator it was reset (hook stderr is easy to miss).
S-5: history() uses SQL ORDER BY ... LIMIT instead of loading the whole table to slice in Python.
D-2: the consolidation "persist the cycle counter LAST" crash-safety invariant — a pass that raises
     mid-way must NOT advance the decay clock.
T-1: recall + SessionStart injection work over a CONSOLIDATED store (the one lifecycle seam the
     drift harness doesn't exercise — it asserts on gist sets, never on retrieve()/the preamble).
"""

from __future__ import annotations

import pathlib

import pytest

from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.db import Database
from cdms.store import TurnEvent


# --- F-2: durable quarantine marker ----------------------------------------- #
def test_f2_quarantine_records_durable_marker(tmp_path):
    cfg = Config(home=tmp_path)
    db = Database(cfg)
    db.set_meta("cycle", 3)
    db.close()
    # Corrupt the main db file so the next open quarantines it and starts fresh.
    pathlib.Path(str(cfg.db_path)).write_bytes(b"this is definitely not a sqlite database")

    db2 = Database(cfg)
    try:
        st = db2.stats()
        assert st["quarantined_at"], "no durable quarantine marker recorded"
        assert st["quarantined_from"] and ".corrupt-" in st["quarantined_from"]
        assert st["episodic"] == 0                 # started fresh
        assert db2.get_meta("cycle") is None        # prior data is gone (quarantined, not merged)
    finally:
        db2.close()


# --- S-5: history() pagination ---------------------------------------------- #
def test_s5_history_returns_most_recent_within_limit(service):
    ids = []
    for i in range(5):
        r = service.ingest(TurnEvent(f"note {i}", f"did {i}", "ok",
                                     session_id=("A" if i % 2 == 0 else "B")))
        ids.append(r.id)

    hist = service.history(limit=3)
    assert len(hist) == 3
    assert {e.id for e in hist} == set(ids[-3:]), "history did not return the 3 most recent"
    assert all(hist[k].timestamp >= hist[k + 1].timestamp for k in range(len(hist) - 1))

    sess_b = service.history(limit=10, session_id="B")
    assert sess_b and all(e.session_id == "B" for e in sess_b)


# --- D-2: consolidation crash-safety (cycle counter persisted LAST) --------- #
def test_d2_cycle_counter_not_advanced_when_a_pass_step_raises(service, cfg, monkeypatch):
    service.ingest(TurnEvent("did a thing", "ran it", "ok", project="P"))
    service.db.set_meta("cycle", 5)
    con = Consolidator(cfg, db=service.db, embedder=service.embedder)

    def boom(self, rep, cycle):                     # _decay_gists runs just before set_meta("cycle")
        raise RuntimeError("simulated mid-pass failure")

    monkeypatch.setattr(Consolidator, "_decay_gists", boom)
    with pytest.raises(RuntimeError):
        con.run()
    # The invariant: a crashed pass must not age the decay clock (else repeated interruptions
    # erode identity without reinforcing this cycle's gists).
    assert service.db.get_meta("cycle") == "5"


# --- T-1: recall + injection over a consolidated store ---------------------- #
def test_t1_recall_and_injection_over_a_consolidated_store(service, cfg):
    cfg.dedup_sim_threshold = 0.999                 # don't dedup the distinct cluster members
    cfg.cluster_sim_threshold = 0.5                 # hash geometry: lower the cluster gate
    for tag in ("alpha", "beta", "gamma"):
        service.ingest(TurnEvent(
            f"postgres index added to speed up the orders query {tag}",
            f"edited the orders query and added an index {tag}",
            "query performance improved", tool_name="Edit", success=True, project="P"))
    crisis = service.ingest(TurnEvent(
        "clean up the repo", "ran git push --force",
        "force push overwrote teammates commits, data loss",
        tool_name="Bash", success=False, valence_hint=-1.0, project="P"))
    service.db.set_salience([(crisis.id, cfg.crisis_threshold + 1.0)])

    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.gists_created >= 1 and rep.scars_created >= 1

    # Recall over the CONSOLIDATED store: the freshly-formed gist is retrievable from the gist tier.
    g = service.db.all_gist()[0]
    hits = service.retrieve(g.render(), tiers=("gist",), project="P")
    assert any(h.id == g.id for h in hits), "consolidated gist is not recallable"

    # The elevated scar is injected into the SessionStart preamble (L3 read path post-consolidation).
    from cdms.hooks import _session_start_context
    out = _session_start_context(cfg, {"cwd": "P"})
    assert "Guardrails" in out, "elevated scar not injected after consolidation"
