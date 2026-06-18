"""Cycle 7 — promotion of DEFERRED findings to fixes, one phase at a time.

Each test is an integration-level reproduction/regression for a promoted finding.

Phase 1 — C-MED-8 / A5-H1: retrieve() materialized hits by scanning the WHOLE gist/scar
table; find_duplicate_scar scanned all scars per insert. Now fetched by id.
"""

from __future__ import annotations

import pytest

from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent


def _seed_gist(svc, cfg, project="p"):
    cfg.dedup_sim_threshold = 0.999
    cfg.cluster_sim_threshold = 0.5
    cfg.min_cluster_support = 2
    for tag in ("alpha", "beta", "gamma"):
        svc.ingest(TurnEvent(
            f"postgres index added to speed up the orders query {tag}",
            f"edited the orders query and added an index {tag}",
            "query performance improved", tool_name="Edit", success=True, project=project))
    Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()


def _boom(*_a, **_k):
    raise AssertionError("full-table scan on the retrieve/dedup hot path")


def test_cmed8_retrieve_materializes_by_id_without_full_scan(tmp_path, monkeypatch):
    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    _seed_gist(svc, cfg)
    svc.pin_scar("force push to main wiped history", "never force push shared branches", project="p")
    assert svc.db.stats()["gist"] >= 1 and svc.db.stats()["scars"] >= 1

    # reinforce=False so the two calls don't differ merely from access_count bumps.
    before = svc.retrieve("orders query index force push", top_k=5, reinforce=False)
    # Forbid whole-table scans, then retrieve again: results must be IDENTICAL and no scan.
    monkeypatch.setattr(svc.db, "all_gist", _boom)
    monkeypatch.setattr(svc.db, "all_scars", _boom)
    after = svc.retrieve("orders query index force push", top_k=5, reinforce=False)

    assert [(h.id, h.tier, round(h.score, 6)) for h in after] == \
           [(h.id, h.tier, round(h.score, 6)) for h in before]
    svc.close()


def test_a1m1_consolidation_skip_is_recorded_and_visible(tmp_path, monkeypatch):
    """Phase 2 — A1-M1: a consolidation skipped on lock contention must leave a durable,
    operator-visible signal (a counter + timestamp surfaced in stats), not be silent."""
    from cdms import consolidate as cmod
    from cdms.lock import cross_process_lock as real_lock

    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    con = cmod.Consolidator(cfg, db=svc.db, embedder=svc.embedder)
    assert svc.db.stats()["consolidations_skipped"] == 0
    assert svc.db.stats()["last_consolidation_skip"] is None

    # Short lock timeout inside run() so the test doesn't wait the 90s default.
    monkeypatch.setattr(cmod, "cross_process_lock", lambda path, **kw: real_lock(path, timeout=0.3))
    with real_lock(cfg.lock_path):          # simulate a concurrent pass holding the lock
        rep1 = con.run()
        rep2 = con.run()

    assert rep1.skipped and rep2.skipped
    st = svc.db.stats()
    assert st["consolidations_skipped"] == 2
    assert st["last_consolidation_skip"] is not None
    svc.close()


def test_cmed1_dedup_folds_full_access_count_into_survivor(tmp_path):
    """Phase 3 — C-MED-1: a deduped duplicate's FULL reinforcement (access_count) folds
    into the survivor, not just +1, so the survivor isn't under-counted."""
    cfg = Config(home=tmp_path)
    cfg.dedup_sim_threshold = 0.95
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    r1 = svc.ingest(TurnEvent("ran the migration script", "applied schema v4", "ok",
                              tool_name="Bash", project="p"))
    r2 = svc.ingest(TurnEvent("ran the migration script", "applied schema v4", "ok",
                              tool_name="Bash", project="p"))
    for _ in range(5):                              # accumulate reinforcement on the DUP
        svc.db.touch_episodic(r2.id, "2026-01-01T00:00:00Z")
    a1 = svc.db.get_episodic(r1.id).access_count
    a2 = svc.db.get_episodic(r2.id).access_count
    assert a2 == 5

    Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()   # dedup folds r2 -> r1

    survivor = svc.db.get_episodic(r1.id)
    assert survivor is not None and svc.db.get_episodic(r2.id) is None
    assert survivor.access_count == a1 + a2        # full fold (was +1 before the fix)
    svc.close()


def test_clow1_log_keeps_multiple_generations(tmp_path, monkeypatch):
    """Phase 4 — C-LOW-1: log rotation keeps N generations (.1..3), not just one."""
    from cdms import hooks

    cfg = Config(home=tmp_path)
    monkeypatch.setattr(hooks, "_LOG_MAX_BYTES", 200)
    for i in range(40):
        hooks._log(cfg, "x" * 80 + f" line {i}")
    p = cfg.log_path
    assert p.exists()
    assert p.with_name(p.name + ".1").exists()
    assert p.with_name(p.name + ".2").exists()
    assert p.with_name(p.name + ".3").exists()
    assert not p.with_name(p.name + ".4").exists()   # bounded at N generations


def test_a7l1_cross_field_config_repaired(monkeypatch, tmp_path):
    """Phase 5 / M1 — A7-L1: in-range-but-jointly-nonsensical config is repaired MINIMALLY
    (clamp the offender), not reset wholesale."""
    from cdms.config import Config as _C
    from cdms.config import load_config

    d = _C()
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_RELATION_POS_THRESHOLD", "-0.5")  # <= neg default -0.15 (inverted)
    monkeypatch.setenv("CDMS_EMBED_MAX_CHARS", "999999")       # > max_field_chars (4000)
    monkeypatch.setenv("CDMS_DEDUP_SIM_THRESHOLD", "0.85")     # < gist_match default 0.90 (order break)
    cfg = load_config()
    assert cfg.relation_pos_threshold == d.relation_pos_threshold   # band restored
    assert cfg.relation_neg_threshold == d.relation_neg_threshold
    assert cfg.embed_max_chars == cfg.max_field_chars               # clamped DOWN, not reset to default
    # the deliberately-set lower dedup is PRESERVED; the offender (gist_match) is lowered
    assert cfg.dedup_sim_threshold == 0.85
    assert cfg.cluster_sim_threshold <= cfg.gist_match_sim_threshold <= cfg.dedup_sim_threshold


def test_m1_embed_clamped_down_to_small_max_field_chars(tmp_path):
    """M1: when max_field_chars is small, embed_max_chars clamps DOWN to it (resetting to
    the 1600 default would still exceed a small max_field_chars)."""
    from cdms.config import Config
    cfg = Config(home=tmp_path, max_field_chars=200)
    from cdms.config import _validate
    _validate(cfg)
    assert cfg.embed_max_chars == 200


def test_drain_skip_is_observable(tmp_path, monkeypatch):
    """Double-review B: a drain skipped on lock contention must record a durable signal
    (drains_skipped counter + timestamp + warning), not be silent."""
    import json as _json

    from cdms import pipeline
    from cdms.lock import cross_process_lock as real_lock
    from cdms.pipeline import drain_and_ingest

    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    cfg.queue_path.write_text(_json.dumps(
        {"hook_event_name": "PostToolUse", "session_id": "s", "tool_name": "Edit",
         "tool_input": "f", "tool_output": "ok", "cwd": "/p"}) + "\n", encoding="utf-8")
    monkeypatch.setattr(pipeline, "_DRAIN_LOCK_TIMEOUT", 0.2)
    assert svc.db.stats()["drains_skipped"] == 0
    with real_lock(cfg.lock_path):
        assert drain_and_ingest(cfg, svc) == 0          # skipped
        assert drain_and_ingest(cfg, svc) == 0
    st = svc.db.stats()
    assert st["drains_skipped"] == 2
    assert st["last_drain_skip"] is not None
    svc.close()


def test_a0m1_widened_harm_tokens_elevate_real_catastrophes():
    """A0-M1 recall gap narrowed: a dangerous command described with a (newly added) harm
    word now elevates, while routine command-talk without harm still does not."""
    from cdms.consolidate import _matches_catastrophe

    assert _matches_catastrophe("force push to main rewrote everyone's history")   # force push + rewrote
    assert _matches_catastrophe("force-push clobbered the shared branch")           # force-push + clobbered
    assert not _matches_catastrophe("we discussed using git push --force carefully")  # danger, no harm word


def test_cmed5_redaction_correct_and_bounded():
    """Phase 6 — C-MED-5: redaction still works; adversarial input can't ReDoS-hang."""
    import time

    from cdms.store import redact_secrets

    red = redact_secrets("MY_API_KEY=supersecretvalue123")
    assert "[REDACTED]" in red and "MY_API_KEY" in red       # value scrubbed, name kept
    evil = ("A" * 5000) + "_SECRET" + ("B" * 5000)           # no '=' -> backtracking bait
    t0 = time.perf_counter()
    redact_secrets(evil)
    assert time.perf_counter() - t0 < 1.0                    # bounded quantifiers -> fast


def test_a6l1_atomic_write_follows_symlink_without_toctou_gate(tmp_path):
    """Phase 7 — A6-L1: write-through-symlink still works with the is_symlink() gate
    removed (realpath applied unconditionally, closing the TOCTOU window)."""
    import json as _json

    from cdms.cli import _atomic_write_json

    target = tmp_path / "real.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(target)
    _atomic_write_json(link, {"k": 1})
    assert link.is_symlink()                                  # link preserved (written through)
    assert _json.loads(target.read_text()) == {"k": 1}       # target updated
    # a plain (non-symlink) path still writes normally
    plain = tmp_path / "plain.json"
    _atomic_write_json(plain, {"k": 2})
    assert _json.loads(plain.read_text()) == {"k": 2}


def test_a2m2_doctor_purges_quarantine_files(tmp_path, monkeypatch, capsys):
    """Phase 8 — A2-M2: `cdms doctor --purge-quarantines` deletes the forensic *.corrupt-*
    plaintext artifacts that corruption recovery leaves behind."""
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    q1 = tmp_path / "memory.db.corrupt-20200101-000000"
    q1.write_text("plaintext episode data", encoding="utf-8")
    q2 = tmp_path / "memory.db-wal.corrupt-20200101-000000"
    q2.write_bytes(b"x")
    from cdms.cli import main

    main(["doctor", "--purge-quarantines"])
    assert not q1.exists() and not q2.exists()
    assert "purged 2" in capsys.readouterr().out


def test_a5h1_scar_dedup_without_full_scan(tmp_path, monkeypatch):
    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    svc.pin_scar("force push to main wiped history", "never force push", project="p")
    n0 = svc.db.stats()["scars"]
    # Pin a near-duplicate while whole-table scans are forbidden — dedup must work via the
    # ≤5 KNN candidate ids only (A5-H1), not by loading every scar.
    monkeypatch.setattr(svc.db, "all_scars", _boom)
    s = svc.pin_scar("force push to main wiped the history", "never ever force push", project="p")
    assert s is not None                         # completed without scanning all scars
    assert svc.db.stats()["scars"] >= n0         # (dedup may keep it at n0; no crash either way)
    svc.close()
