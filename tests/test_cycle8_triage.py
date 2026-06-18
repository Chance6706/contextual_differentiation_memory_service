"""Cycle 8 — regressions for the OWL final-report findings we triaged.

Each test reproduces the defect and asserts the fix. IDs match CYCLE8_OWL_FINAL.md.
"""

from __future__ import annotations

import inspect
import os
import threading
from datetime import datetime, timezone

import pytest

import cdms.embeddings as embeddings
import cdms.mcp_server as mcp_server
from cdms.config import Config, load_config
from cdms.consolidate import ConsolidationReport, Consolidator
from cdms.db import Database
from cdms.embeddings import Embedder
from cdms.hooks import _sanitize
from cdms.spool import spool_event
from cdms.store import MemoryService, TurnEvent, redact_secrets

_W_ENV = ("CDMS_W_SURPRISE", "CDMS_W_CONTINGENCY", "CDMS_W_SELF_REF", "CDMS_W_AFFECT")


# --- H-1: spool file is owner-only (pre-redaction secrets) ------------------- #
@pytest.mark.skipif(os.name == "nt", reason="Windows file security is NTFS-ACL based, not Unix "
                    "mode bits; os.open mode 0o600 is a no-op there (profile-dir files aren't "
                    "world-readable by default). The 0o600 guard is exercised on POSIX.")
def test_h1_spool_file_is_owner_only(tmp_path):
    cfg = Config(home=tmp_path)
    spool_event(cfg, {"hook_event_name": "PostToolUse", "tool_output": "AWS_SECRET=xyz123456"})
    mode = cfg.queue_path.stat().st_mode & 0o777
    assert mode == 0o600, f"spool world/group-readable: {oct(mode)}"


# --- L-4: quarantined corrupt store is owner-only ---------------------------- #
@pytest.mark.skipif(os.name == "nt", reason="Windows uses NTFS ACLs, not Unix mode bits; "
                    "os.chmod(0o600) only toggles the read-only bit there. Exercised on POSIX.")
def test_l4_quarantine_file_is_owner_only(tmp_path):
    p = tmp_path / "memory.db"
    p.write_text("plaintext store contents")
    Database._quarantine_corrupt(str(p), Exception("database disk image is malformed"))
    q = list(tmp_path.glob("memory.db.corrupt-*"))
    assert q, "no quarantine file created"
    assert (q[0].stat().st_mode & 0o777) == 0o600


# --- H-2 / M-2: S0 weight bounds -------------------------------------------- #
def test_h2_absurd_weight_is_clamped(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_W_SURPRISE", "1000")     # was allowed (<=1e3); now > 10 cap
    assert load_config().w_surprise == Config().w_surprise


def test_h2_weights_cannot_self_elevate_a_zero_goal_memory(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    for ev in _W_ENV:
        monkeypatch.setenv(ev, "10")                  # each at the per-field cap
    cfg = load_config()
    wsum = cfg.w_surprise + cfg.w_contingency + cfg.w_self_ref + cfg.w_affect
    # A goal=0 memory's max S0 (all signals 1) must stay below the crisis threshold.
    assert cfg.goal_gate_floor * wsum < cfg.crisis_threshold


def test_m2_zero_weights_restore_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    for ev in _W_ENV:
        monkeypatch.setenv(ev, "0")
    cfg = load_config()
    assert (cfg.w_surprise + cfg.w_contingency + cfg.w_self_ref + cfg.w_affect) > 0


def test_h2_sane_weight_override_preserved(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_W_SURPRISE", "1.5")
    assert load_config().w_surprise == 1.5            # in-range value not clobbered


# --- M-4: unicode line separators neutralized -------------------------------- #
def test_m4_unicode_line_separators_neutralized():
    raw = "alpha\u2028## evil\u2029- item\u0085beta"
    s = _sanitize(raw)
    for ch in ("\u2028", "\u2029", "\u0085", "\n"):
        assert ch not in s
    assert s.startswith("alpha")


# --- M-5: additional credential formats redacted ----------------------------- #
def test_m5_anthropic_key_redacted():
    out = redact_secrets("token: sk-ant-api03-" + "A" * 40)
    assert "[REDACTED]" in out and "A" * 40 not in out


def test_m5_google_key_redacted():
    out = redact_secrets("key=AIza" + "B" * 35)
    assert "[REDACTED]" in out and "B" * 35 not in out


def test_m5_azure_account_key_redacted():
    out = redact_secrets("DefaultEndpointsProtocol=https;AccountKey=" + "c" * 40 + ";Endpoint=x")
    assert "AccountKey=[REDACTED]" in out and "c" * 40 not in out


# --- H-5: embedder singleton is race-safe ------------------------------------ #
def test_h5_get_embedder_returns_one_instance_under_threads(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_EMBED_BACKEND", "hash")
    embeddings._SINGLETON = None
    embeddings._SINGLETON_KEY = None
    cfg = Config(home=tmp_path)
    got: list = []
    barrier = threading.Barrier(8)

    def grab():
        barrier.wait()                                # maximize the race window
        got.append(embeddings.get_embedder(cfg))

    ts = [threading.Thread(target=grab) for _ in range(8)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert len({id(x) for x in got}) == 1, "TOCTOU: multiple embedder instances built"


# --- M-1: eviction re-reads access_count (vs concurrent retrieve bump) ------- #
def test_m1_evict_rereads_fresh_access_count(tmp_path):
    cfg = Config(home=tmp_path)
    cfg.retention_floor = 0.1
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        rec = svc.ingest(TurnEvent("trigger", "action", "ok", project="p"))
        svc.db.set_salience([(rec.id, 0.06)])         # below floor at access_count 0
        stale = svc.db.get_episodic(rec.id)           # snapshot: access_count == 0
        assert stale.access_count == 0
        # Simulate a concurrent retrieve bumping access AFTER the snapshot.
        svc.db.bump_access(rec.id, 10, stale.timestamp)
        con = Consolidator(cfg, db=svc.db, embedder=svc.embedder)
        doomed = con._evict([stale], datetime.now(timezone.utc), ConsolidationReport())
        assert rec.id not in doomed                   # re-read sees the bump -> survives
        assert svc.db.get_episodic(rec.id) is not None
    finally:
        svc.close()


# --- M-3: the MCP store tool no longer exposes the goal_hint bypass ---------- #
def test_m3_mcp_store_has_no_importance_param():
    fn = mcp_server.store
    for attr in ("fn", "func", "__wrapped__"):
        if hasattr(fn, attr) and callable(getattr(fn, attr)):
            fn = getattr(fn, attr)
            break
    params = inspect.signature(fn).parameters
    assert "importance" not in params
    assert "content" in params
