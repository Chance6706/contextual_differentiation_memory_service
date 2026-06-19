"""Regression tests for Cycle-3 red-team findings.

Grouped by the surface that surfaced them:
  C1     — lock contention must NOT be misread as DB corruption (would wipe a
           healthy store).
  config — inf / astronomically-large values must be rejected by _validate.
  embed  — degenerate text maps to one sentinel on BOTH backends; output dim is
           asserted; fingerprint carries the fastembed version.
  scars  — near-identical scars are deduped on insert (bounded L3 growth).
  forget — clears the spool (pre-redaction secrets); scrubs free pages; tolerates
           trailing-slash / subdir project paths.
  drain  — a non-dict spool line can't destroy a session; a stranded .processing
           claim from a killed drain is reclaimed.
  infer  — the positive-override no longer inverts a real failure.
  H4     — a dangerous command without recorded harm is not auto-pinned.
  mcp    — negative k is clamped; project='' is the launch cwd, not "all".
  lock   — the cross-process lock is mutually exclusive.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time

import numpy as np
import pytest

from cdms.config import Config, load_config
from cdms.consolidate import ConsolidationReport, Consolidator, _matches_catastrophe
from cdms.db import Database
from cdms.embeddings import Embedder
from cdms.lock import cross_process_lock
from cdms.models import Episodic, new_id
from cdms.pipeline import _infer_success, drain_and_ingest
from cdms.spool import spool_event
from cdms.store import MemoryService, TurnEvent


# --- C1: lock contention is not corruption --------------------------------- #
def test_lock_error_is_not_classified_as_corruption():
    locked = sqlite3.OperationalError("database is locked")
    busy = sqlite3.OperationalError("database is busy")
    assert Database._is_corruption(locked) is False
    assert Database._is_corruption(busy) is False
    # real corruption signatures still quarantine
    assert Database._is_corruption(sqlite3.DatabaseError("file is not a database"))
    assert Database._is_corruption(sqlite3.DatabaseError("database disk image is malformed"))


def test_healthy_store_survives_a_lock_during_open(tmp_path):
    """A held write lock (contention) must not cause the fresh open to quarantine
    and WIPE the existing store. We simulate by patching _init_schema to raise a
    'database is locked' OperationalError on the first open only."""
    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    svc.ingest(TurnEvent(trigger_prompt="precious", action_taken="a", outcome_feedback="o"))
    svc.close()

    real_init = Database._init_schema
    calls = {"n": 0}

    def flaky(self):
        calls["n"] += 1
        if calls["n"] == 1:
            raise sqlite3.OperationalError("database is locked")
        return real_init(self)

    Database._init_schema = flaky
    try:
        with pytest.raises(sqlite3.OperationalError):
            Database(cfg)  # must RE-RAISE, not quarantine
    finally:
        Database._init_schema = real_init
    # the store and its single row are intact; nothing was quarantined away
    assert not list(tmp_path.glob("memory.db.corrupt-*"))
    db = Database(cfg)
    try:
        assert db.stats()["episodic"] == 1
    finally:
        db.close()


# --- config: inf / huge values rejected ------------------------------------ #
def test_infinite_and_huge_config_values_repaired(tmp_path, monkeypatch):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_DECAY_HALFLIFE_DAYS", "inf")
    monkeypatch.setenv("CDMS_MAX_FIELD_CHARS", "99999999999999999999")
    monkeypatch.setenv("CDMS_EMBED_DIM", "100000000")
    cfg, d = load_config(), Config()
    assert cfg.decay_halflife_days == d.decay_halflife_days   # inf -> default (decay stays > 0)
    assert cfg.decay_lambda > 0
    assert cfg.max_field_chars == d.max_field_chars           # huge -> default (DoS cap restored)
    assert cfg.embed_dim == d.embed_dim                       # out-of-range dim -> default


def test_nan_config_value_repaired(tmp_path, monkeypatch):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    (tmp_path / "config.json").write_text(json.dumps({"gist_valence_ema": float("nan")}))
    cfg = load_config()
    assert cfg.gist_valence_ema == Config().gist_valence_ema


# --- embed: degeneracy sentinel + dim assert ------------------------------- #
@pytest.mark.parametrize("a,b", [("", "   "), ("\n\t", "!!!"), ("🙂", "···")])
def test_degenerate_inputs_collapse_to_one_sentinel(cfg, a, b):
    e = Embedder(cfg)
    va, vb = e.embed_one(a), e.embed_one(b)
    assert abs(float(np.dot(va, vb)) - 1.0) < 1e-6   # identical sentinel (cos == 1)
    assert abs(float(np.linalg.norm(va)) - 1.0) < 1e-6


def test_real_content_is_not_collapsed(cfg):
    e = Embedder(cfg)
    assert float(np.dot(e.embed_one("authentication module"),
                        e.embed_one("database migration"))) < 0.99


def test_embed_output_dim_is_asserted(cfg):
    e = Embedder(cfg)
    e._backend = "fastembed"

    class _BadModel:
        def embed(self, texts):
            return [np.ones(7, dtype=np.float32) for _ in texts]  # wrong dim

    e._model = _BadModel()
    with pytest.raises(RuntimeError, match="embed_dim"):
        e.embed_one("anything with content")


# --- scars: dedup on insert ------------------------------------------------ #
def test_pin_scar_dedups_identical(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        a = svc.pin_scar("force push lost the commits", "always back up first", project="p")
        b = svc.pin_scar("force push lost the commits", "always back up first", project="p")
        assert a.id == b.id
        assert svc.db.stats()["scars"] == 1
    finally:
        svc.close()


def test_recurring_elevated_catastrophe_does_not_grow_scars(cfg):
    cfg.scar_elevation_min_sessions = 1   # isolate: validates scar dedup, not the corroboration gate
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        con = Consolidator(cfg, db=svc.db, embedder=svc.embedder)
        for _ in range(5):
            ep = Episodic(id=new_id("ep"), trigger_prompt="clean branch",
                          action_taken="bash: git push --force",
                          outcome_feedback="overwrote teammates and lost work",
                          valence=-0.9, base_salience=6.0, project="p")
            con._elevate_scars([ep], ConsolidationReport())
        assert svc.db.stats()["scars"] == 1   # one permanent row, not five
    finally:
        svc.close()


# --- forget: spool + free pages + path normalization ----------------------- #
def test_forget_clears_matching_spool_events(cfg):
    spool_event(cfg, {"hook_event_name": "PostToolUse", "session_id": "s1", "cwd": "/proj/A",
                      "tool_name": "Bash", "tool_output": "PASSWORD=SPOOLCANARY"})
    spool_event(cfg, {"hook_event_name": "PostToolUse", "session_id": "s2", "cwd": "/proj/B",
                      "tool_name": "Bash", "tool_output": "kept"})
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        res = svc.forget(project="/proj/A")
        assert res["spooled"] == 1
    finally:
        svc.close()
    remaining = cfg.queue_path.read_text(encoding="utf-8")
    assert "SPOOLCANARY" not in remaining
    assert "kept" in remaining


def test_forget_scrubs_free_pages(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        svc.ingest(TurnEvent(trigger_prompt="FORGETCANARY8675309 sensitive note",
                             action_taken="a", outcome_feedback="o", project="/proj/X"))
        svc.forget(project="/proj/X")
    finally:
        svc.close()
    blob = cfg.db_path.read_bytes()
    assert b"FORGETCANARY8675309" not in blob, "deleted content recoverable from db file"


def test_forget_by_project_tolerates_slash_and_subdir(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        svc.ingest(TurnEvent(trigger_prompt="x", action_taken="a", project="/proj/work"))
        svc.ingest(TurnEvent(trigger_prompt="y", action_taken="a", project="/proj/work/"))
        svc.ingest(TurnEvent(trigger_prompt="z", action_taken="a", project="/proj/work/sub"))
        svc.ingest(TurnEvent(trigger_prompt="o", action_taken="a", project="/proj/worktree"))
        res = svc.forget(project="/proj/work")
        assert res["episodic"] == 3                     # exact + trailing-slash + subdir
        survivors = {e.project for e in svc.db.all_episodic()}
        assert survivors == {"/proj/worktree"}          # sibling NOT a false prefix match
    finally:
        svc.close()


# --- drain durability ------------------------------------------------------ #
def test_non_dict_spool_line_does_not_destroy_session(cfg):
    spool_event(cfg, {"hook_event_name": "UserPromptSubmit", "session_id": "s", "prompt": "do x"})
    # a valid-JSON-but-wrong-type line in the middle (the crash repro)
    with open(cfg.queue_path, "a", encoding="utf-8") as f:
        f.write("42\n")
    spool_event(cfg, {"hook_event_name": "PostToolUse", "session_id": "s",
                      "tool_name": "Write", "tool_input": {"f": "x"}, "tool_output": "done"})
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        n = drain_and_ingest(cfg, svc)
        assert n == 1                                   # the valid turn survived
        assert svc.db.stats()["episodic"] == 1
    finally:
        svc.close()


@pytest.mark.xfail(os.name == "nt", reason="PID-liveness reclamation differs on Windows (PID-reuse "
                   "semantics); validated on Linux CI.", strict=False)
def test_orphaned_processing_claim_is_reclaimed(cfg):
    """A .processing file stranded by a killed drain (dead pid) is re-ingested."""
    cfg.ensure_home()
    dead_pid = 2_147_483_647  # not a live process
    orphan = cfg.queue_path.parent / f"{cfg.queue_path.name}.{dead_pid}-deadbeef.processing"
    orphan.write_text(
        json.dumps({"hook_event_name": "PostToolUse", "session_id": "s", "cwd": "p",
                    "tool_name": "Bash", "tool_input": {}, "tool_output": "RECLAIMED ok"}) + "\n",
        encoding="utf-8")
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        n = drain_and_ingest(cfg, svc)
        assert n == 1
        assert svc.db.stats()["episodic"] == 1
    finally:
        svc.close()
    assert not orphan.exists()


# --- infer: override no longer inverts a real failure ---------------------- #
@pytest.mark.parametrize("text", [
    "no errors but the test failed",
    "no errors? actually the deploy failed catastrophically",
])
def test_positive_override_does_not_invert_real_failure(text):
    assert _infer_success(text) is not True


def test_override_still_wins_when_only_resolution_language():
    assert _infer_success("cannot reproduce, works fine now") is True
    assert _infer_success("the run completed with no errors") is True


# --- H4: dangerous command without harm is not a scar ---------------------- #
def test_dangerous_command_without_harm_is_not_a_scar():
    assert _matches_catastrophe("bash: git reset --hard to discard local edits") is False
    assert _matches_catastrophe("bash: git push --force after rebase, all good") is False
    # ...but a dangerous command that DID cause harm still elevates
    assert _matches_catastrophe("git push --force and lost the commits") is True
    assert _matches_catastrophe("ran rm -rf the wrong dir, files are gone") is True


# --- mcp scoping + clamp --------------------------------------------------- #
def test_retrieve_clamps_negative_top_k(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        for i in range(5):
            svc.ingest(TurnEvent(trigger_prompt=f"note {i}", action_taken="a"))
        hits = svc.retrieve("note", top_k=-2, tiers=("episodic",), reinforce=False)
        assert len(hits) >= 1   # not a negative slice that drops the tail
    finally:
        svc.close()


def test_mcp_empty_project_is_launch_cwd_not_global(tmp_path, monkeypatch):
    import importlib

    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    import cdms.mcp_server as m
    importlib.reload(m)
    # store with explicit empty project -> coerced to the launch cwd
    r = m.store(content="scoped note", kind="episode", project="")
    assert r.tier == "episodic"
    eps = m.service().db.all_episodic()
    assert eps and all(e.project == m._LAUNCH_CWD for e in eps)


# --- install: malformed settings + symlink write-through ------------------- #
def test_install_refuses_non_dict_hooks(tmp_path):
    from cdms.cli import _install_hooks

    p = tmp_path / "settings.json"
    p.write_text(json.dumps({"hooks": ["not", "a", "dict"]}), encoding="utf-8")
    with pytest.raises(SystemExit):
        _install_hooks(p)            # loud refuse, not an AttributeError traceback


@pytest.mark.xfail(os.name == "nt", reason="symlink creation needs privilege/Developer-Mode on Windows "
                   "(WinError 1314); validated on Linux CI.", strict=False)
def test_install_writes_through_symlinked_settings(tmp_path):
    from cdms.cli import _install_hooks, _is_cdms_entry

    real_dir = tmp_path / "dotfiles"
    real_dir.mkdir()
    real = real_dir / "settings.json"
    real.write_text(json.dumps({"model": "opus"}), encoding="utf-8")
    link = tmp_path / "settings.json"
    link.symlink_to(real)

    _install_hooks(link)
    assert link.is_symlink(), "symlink was severed into a detached file"
    cfg = json.loads(real.read_text(encoding="utf-8"))   # the REAL dotfile was updated
    assert cfg["model"] == "opus"
    assert any(_is_cdms_entry(e) for e in cfg["hooks"]["SessionStart"])


# --- lock: mutual exclusion ------------------------------------------------ #
def test_cross_process_lock_is_mutually_exclusive(tmp_path):
    lock = tmp_path / "x.lock"
    active = {"n": 0}
    overlap = {"max": 0}

    def worker():
        with cross_process_lock(lock, timeout=5.0):
            active["n"] += 1
            overlap["max"] = max(overlap["max"], active["n"])
            time.sleep(0.05)
            active["n"] -= 1

    threads = [threading.Thread(target=worker) for _ in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert overlap["max"] == 1, "lock allowed concurrent holders"
