"""Cycle 7, Pass C — regressions for findings the *re-run* audit surfaced against the
true branch tip (the prior external review had read a stale revision).

Each test is a falsifiable reproduction of a finding fixed in this pass:

* HIGH-1 — `_infer_success` matched negators/markers/override phrases as bare SUBSTRINGS,
  so ordinary words ("tokens" ⊃ "ok", "casino" ⊃ "no", "casino errors" ⊃ "no errors")
  spuriously flipped a real failure to success/neutral and poisoned stored valence.
* MED-1 — a partially-seeded store whose archetype label was also lost was completed from
  the DEFAULT archetype, silently mixing two dispositions; it now recovers the archetype
  from the seeds already present.
* LOW-1 — `doctor --purge-quarantines` used a bare `*.corrupt-[0-9]*` glob that could
  delete unrelated operator files; it is now anchored to the db filename prefix.
* LOW-2 — dedup folded `max(1, access_count)`, crediting a phantom +1 to a never-retrieved
  duplicate; it now folds the real (possibly zero) count.
* LOW-3 — `mem_temperament` gained CHECK constraints (range + band) as defense-in-depth.
"""

from __future__ import annotations

import sqlite3

import pytest

import cdms.temperament as T
from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.db import Database
from cdms.embeddings import Embedder
from cdms.pipeline import _infer_success
from cdms.store import MemoryService, TurnEvent


# --- HIGH-1: word-boundary success inference -------------------------------- #
@pytest.mark.parametrize("text, expected", [
    # The headline regressions: the negator/marker/override token is an INTERNAL
    # substring of an ordinary word and must NOT match.
    ("casino errors everywhere", False),   # "casino" ⊅ "no"; "casino errors" ⊅ "no errors"
    ("lookup failed", False),              # "lookup" ⊅ "ok"
    ("annotation error in tokens", False),  # "annotation" ⊅ "not"; "tokens" ⊅ "ok"
    ("broken pipe, build failed", False),  # "broken" ⊅ "ok"
    # Genuine signals still resolve correctly.
    ("all tests passed", True),
    ("no errors found", True),             # real negation/override → not a failure
    ("the deploy failed", False),
    # The exact inversion the override-stripping guards: override phrase present, but a
    # SEPARATE real failure remains → still a failure.
    ("no errors but the deploy failed", False),
])
def test_infer_success_is_word_boundary_not_substring(text, expected):
    assert _infer_success(text) is expected


# --- MED-1: partial-seed archetype recovery --------------------------------- #
def test_match_archetype_by_partial_seed_unambiguous_and_ambiguous():
    mav = {d.name: d.seed for d in T.preset_dials("maverick")}
    # A distinctive subset uniquely identifies maverick.
    assert T.match_archetype_by_partial_seed(
        {k: mav[k] for k in ("exploration_radius", "autonomy_gate")}) == "maverick"
    # A single moderate dial that several archetypes share (all default 0.5) is ambiguous.
    assert T.match_archetype_by_partial_seed({"dream_damping": 0.5}) is None
    assert T.match_archetype_by_partial_seed({}) is None


def test_partial_store_with_lost_label_recovers_from_present_seeds(tmp_path, monkeypatch):
    """A truncated maverick store whose archetype-meta row is ALSO gone must not be
    completed from the default (co-pilot) — that would mix two dispositions. It recovers
    the archetype from the seeds still present (Cycle-7 MED-1)."""
    monkeypatch.setenv("CDMS_EMBED_BACKEND", "hash")
    cfg = Config(home=tmp_path, archetype_default="maverick")
    db = Database(cfg)
    # Simulate truncation + lost label: keep 3 distinctive maverick dials, drop the rest
    # AND the archetype meta row.
    keep = ("exploration_radius", "autonomy_gate", "emotional_gain")
    ph = ",".join("?" * len(keep))
    db.conn.execute(f"DELETE FROM mem_temperament WHERE dial NOT IN ({ph})", keep)
    db.conn.execute("DELETE FROM cdms_meta WHERE key = 'archetype'")
    db.conn.commit()
    db.close()

    # Re-open with a DIFFERENT configured default: recovery must win over the config so the
    # completed dials stay internally maverick, not a maverick/co-pilot hybrid.
    cfg2 = Config(home=tmp_path, archetype_default="co-pilot")
    db2 = Database(cfg2)
    dials = {d.name: d for d in db2.all_dials()}
    assert len(dials) == 8                         # completed
    assert db2.get_archetype() == "maverick"       # recovered from seeds, not defaulted
    mav = {d.name: d for d in T.preset_dials("maverick")}
    assert dials["exploration_radius"].seed == mav["exploration_radius"].seed
    db2.close()


# --- LOW-1: purge glob is anchored to the db filename ----------------------- #
def test_purge_quarantines_spares_unrelated_corrupt_named_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    from cdms.cli import main

    quarantine = tmp_path / "memory.db.corrupt-20200101-000000"
    quarantine.write_text("plaintext store", encoding="utf-8")
    unrelated = tmp_path / "dump.corrupt-1"           # operator's own file, not ours
    unrelated.write_text("keep me", encoding="utf-8")

    main(["doctor", "--purge-quarantines"])
    assert not quarantine.exists()                    # ours is scrubbed
    assert unrelated.exists()                         # the bare-glob collateral is spared
    assert "purged 1" in capsys.readouterr().out


# --- LOW-2: dedup folds the real (possibly zero) access count --------------- #
def test_dedup_does_not_fabricate_access_on_never_retrieved_dup(tmp_path):
    cfg = Config(home=tmp_path)
    cfg.dedup_sim_threshold = 0.95
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    # Two identical episodes, NEITHER ever retrieved → both access_count == 0.
    r1 = svc.ingest(TurnEvent("ran the migration", "applied schema", "ok",
                              tool_name="Bash", project="p"))
    r2 = svc.ingest(TurnEvent("ran the migration", "applied schema", "ok",
                              tool_name="Bash", project="p"))
    assert svc.db.get_episodic(r1.id).access_count == 0
    assert svc.db.get_episodic(r2.id).access_count == 0

    Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()   # dedup folds r2 → r1

    survivor = svc.db.get_episodic(r1.id) or svc.db.get_episodic(r2.id)
    assert survivor is not None
    # The old `max(1, …)` floor would leave access_count == 1 (a phantom retrieval).
    assert survivor.access_count == 0
    svc.close()


# --- LOW-3: DB-level CHECK constraints on the temperament table ------------- #
def test_mem_temperament_rejects_out_of_range_rows(tmp_path):
    cfg = Config(home=tmp_path)
    db = Database(cfg)
    bad_rows = [
        ("x1", 1.5, 0.5, 0.2, 0.8, 0.3),   # seed > 1
        ("x2", 0.5, 0.1, 0.2, 0.8, 0.3),   # current < lower
        ("x3", 0.5, 0.5, 0.8, 0.2, 0.3),   # lower > upper
        ("x4", 0.5, 0.5, 0.2, 0.8, -0.1),  # negative plasticity
    ]
    for row in bad_rows:
        with pytest.raises(sqlite3.IntegrityError):
            with db.tx() as c:
                c.execute("INSERT INTO mem_temperament VALUES (?,?,?,?,?,?)", row)
    db.close()
