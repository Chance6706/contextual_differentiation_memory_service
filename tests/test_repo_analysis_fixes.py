"""Regression tests for the fix-now tier of docs/REPO_ANALYSIS_2026-07-01.md §6.

Covers, 1:1 with the findings:
  S1      — store db/-wal/-shm and home dir are owner-only (POSIX; no-op on Windows)
  S2      — `cdms observe` refuses a non-loopback bind (mirrors the viewport)
  core #2 — a transient embedder outage ABORTS the drain and PRESERVES the spooled
            backlog for retry, instead of skipping every turn and deleting the claim
  S4      — MCP store(kind="scar") mints a DEMOTED agent note (origin="mcp"): never
            rendered in the authoritative guardrails block, counted toward the L3 cap,
            evicted before auto-elevated scars, upgradeable only by an operator pin
"""

from __future__ import annotations

import importlib
import os
import time
from pathlib import Path

import pytest

from cdms.config import Config
from cdms.embeddings import Embedder, EmbedderUnavailableError
from cdms.models import Scar, new_id
from cdms.pipeline import drain_and_ingest
from cdms.spool import spool_event
from cdms.store import MemoryService, TurnEvent

PROJECT = "P"


# --------------------------------------------------------------------------- #
# S1 — owner-only modes
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits; NTFS ACLs govern on Windows")
def test_store_files_and_home_are_owner_only(tmp_path):
    cfg = Config(home=tmp_path / "cdms-a")
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        svc.ingest(TurnEvent(trigger_prompt="p", action_taken="a", outcome_feedback="ok",
                             session_id="s1", project=PROJECT))
    finally:
        svc.close()
    assert (cfg.home.stat().st_mode & 0o777) == 0o700
    assert (cfg.db_path.stat().st_mode & 0o777) == 0o600
    for suffix in ("-wal", "-shm"):
        p = Path(f"{cfg.db_path}{suffix}")
        if p.exists():
            assert (p.stat().st_mode & 0o777) == 0o600, suffix


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits; NTFS ACLs govern on Windows")
def test_reopen_tightens_preexisting_world_readable_store(tmp_path):
    """A store created before this fix (0644 under the default umask) is tightened
    on the next open, not just at creation."""
    cfg = Config(home=tmp_path / "cdms-a")
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    svc.close()
    os.chmod(cfg.db_path, 0o644)   # simulate the legacy mode
    os.chmod(cfg.home, 0o755)
    svc2 = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        assert (cfg.db_path.stat().st_mode & 0o777) == 0o600
        assert (cfg.home.stat().st_mode & 0o777) == 0o700
    finally:
        svc2.close()


# --------------------------------------------------------------------------- #
# S2 — observer loopback refusal
# --------------------------------------------------------------------------- #
def test_observer_refuses_non_loopback_bind(tmp_path, capsys):
    from cdms.observer import serve

    cfg = Config(home=tmp_path / "cdms-a")
    assert serve(cfg, host="0.0.0.0", port=0) == 2
    assert "REFUSING" in capsys.readouterr().out
    # Loopback hosts pass the refusal; with no store yet, serve exits 1 (not 2),
    # proving the refusal gate doesn't block the legitimate bind path.
    assert serve(cfg, host="127.0.0.1", port=0) == 1
    assert serve(cfg, host="localhost", port=0) == 1


# --------------------------------------------------------------------------- #
# core #2 — drain vs. embedder outage
# --------------------------------------------------------------------------- #
class _DownEmbedder:
    """Embedder stub whose backend is down. fingerprint() matches the hash backend
    so the store pinned during the outage reconciles with the healthy retry."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.dim = cfg.embed_dim

    def fingerprint(self) -> str:
        return f"hash:{self.cfg.embed_model}:{self.dim}"

    def embed(self, texts):
        raise EmbedderUnavailableError("embedding model unavailable (test outage)")

    def embed_one(self, text):
        raise EmbedderUnavailableError("embedding model unavailable (test outage)")


def _spool_turns(cfg: Config, n: int) -> None:
    for i in range(n):
        spool_event(cfg, {"hook_event_name": "PostToolUse", "session_id": "s1",
                          "cwd": PROJECT, "tool_name": "Bash",
                          "tool_input": f"command {i}", "tool_output": f"output {i} ok",
                          "success": True})


def _claims(cfg: Config) -> list[Path]:
    return sorted(cfg.queue_path.parent.glob(cfg.queue_path.name + ".*.processing"))


def test_drain_preserves_backlog_on_embedder_outage(tmp_path):
    """The review's repro: 3+ spooled events + embedder outage previously yielded
    ingested=0 with the spool and claim DELETED (backlog destroyed). Now the drain
    aborts, keeps the claim for the orphan reclaim, records the abort in meta, and
    a later healthy drain ingests everything."""
    cfg = Config(home=tmp_path / "cdms-a")
    _spool_turns(cfg, 3)

    down = MemoryService(cfg, embedder=_DownEmbedder(cfg))
    try:
        assert drain_and_ingest(cfg, down) == 0
        claims = _claims(cfg)
        assert len(claims) == 1, "backlog must be preserved as a .processing claim"
        assert down.db.get_meta("drains_aborted") == "1"
        assert down.db.get_meta("last_drain_abort")
        assert down.db.stats()["episodic"] == 0
    finally:
        down.close()

    # The claim's owning pid (this test process) is alive, so reclaim needs the age
    # fallback — age the claim past _RECLAIM_AGE_SECONDS.
    old = time.time() - 3700
    os.utime(claims[0], (old, old))

    healthy = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        assert drain_and_ingest(cfg, healthy) == 3
        assert healthy.db.stats()["episodic"] == 3
        assert not _claims(cfg), "claim consumed after successful retry"
    finally:
        healthy.close()


def test_drain_still_skips_bad_turns_and_consumes_claim(tmp_path, monkeypatch):
    """The bad-turn contract is unchanged: a turn-specific error skips that turn only,
    the rest ingest, and the claim is consumed (no stranded backlog)."""
    cfg = Config(home=tmp_path / "cdms-a")
    _spool_turns(cfg, 3)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    real_ingest = svc.ingest
    seen = {"n": 0}

    def flaky(t):
        seen["n"] += 1
        if seen["n"] == 2:
            raise ValueError("bad turn (test)")
        return real_ingest(t)

    monkeypatch.setattr(svc, "ingest", flaky)
    try:
        assert drain_and_ingest(cfg, svc) == 2
        assert not _claims(cfg)
        assert svc.db.get_meta("drains_aborted") is None
    finally:
        svc.close()


# --------------------------------------------------------------------------- #
# S4 — MCP scar gate
# --------------------------------------------------------------------------- #
def _fresh_server(tmp_path, monkeypatch):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    import cdms.mcp_server as m
    importlib.reload(m)
    return m


def test_mcp_scar_is_agent_note_not_operator_pin(tmp_path, monkeypatch):
    m = _fresh_server(tmp_path, monkeypatch)
    r = m.store(content="deleted prod db | always take a backup first", kind="scar",
                project=PROJECT)
    assert r.tier == "scar"
    assert "agent note" in r.summary
    svc = m.service()
    scars = svc.db.all_scars()
    assert len(scars) == 1 and scars[0].origin == "mcp"


def test_pin_scar_origin_validation(service):
    with pytest.raises(ValueError):
        service.pin_scar("t", "r", project=PROJECT, origin="elevated")


def test_agent_note_renders_demoted_never_authoritative(service, cfg):
    service.pin_scar("operator crisis", "operator remediation rule", project=PROJECT)
    service.pin_scar("agent crisis xyz", "agent remediation abc", project=PROJECT,
                     origin="mcp")

    from cdms.hooks import _build_preamble_text, _session_start_context

    out = _session_start_context(cfg, {"cwd": PROJECT})
    guard = out.split("<memory:guardrails>")[1].split("</memory:guardrails>")[0]
    assert "operator remediation rule" in guard
    assert "agent remediation abc" not in guard, "agent pin must not enter the guardrails block"
    notes = out.split("<memory:agent-notes>")[1].split("</memory:agent-notes>")[0]
    assert "agent remediation abc" in notes
    assert "NOT authoritative" in out

    # The shared builder stays byte-identical to the shipped v1 path (its contract).
    assert _build_preamble_text(cfg, {"cwd": PROJECT}, variant="v1") == out

    # v4 frames guardrails as "take precedence over project conventions" — the agent
    # note must not ride that authority band there either.
    out4 = _build_preamble_text(cfg, {"cwd": PROJECT}, variant="v4")
    guard4 = out4.split("<memory:guardrails>")[1].split("</memory:guardrails>")[0]
    assert "agent remediation abc" not in guard4
    assert "agent remediation abc" in out4.split("<memory:agent-notes>")[1]


def test_agent_note_alone_still_produces_preamble(service, cfg):
    service.pin_scar("agent-only caution", "agent-only rule", project=PROJECT, origin="mcp")
    from cdms.hooks import _session_start_context
    out = _session_start_context(cfg, {"cwd": PROJECT})
    assert "<memory:agent-notes>" in out and "<memory:guardrails>" not in out


def test_l3_cap_evicts_mcp_before_elevated(service, cfg):
    """A flood of one-call MCP pins must consume ITSELF under the L3 cap instead of
    flushing corroborated elevated guardrails out of the project."""
    from cdms.consolidate import ConsolidationReport, Consolidator

    cfg.scar_project_cap = 2
    rows = []
    for i, (origin, ts) in enumerate([
        ("elevated", "2026-01-01T00:00:00+00:00"),   # oldest overall
        ("mcp", "2026-01-02T00:00:00+00:00"),
        ("mcp", "2026-01-03T00:00:00+00:00"),
    ]):
        s = Scar(id=new_id("scar"), crisis_trigger=f"crisis {i}", remediation_rule=f"rule {i}",
                 project=PROJECT, origin=origin, timestamp=ts)
        service.db.insert_scar(s, service.embedder.embed_one(s.search_text()))
        rows.append(s)

    con = Consolidator(cfg, db=service.db, embedder=service.embedder)
    rep = ConsolidationReport()
    con._evict_scars(rep)

    left = {s.id for s in service.db.all_scars()}
    assert rows[0].id in left, "elevated (corroborated) survives despite being oldest"
    assert rows[1].id not in left, "oldest mcp note evicted first"
    assert rows[2].id in left


def test_operator_pin_upgrades_agent_note_but_never_downgrades(service):
    a = service.pin_scar("db wipe danger", "always snapshot first", project=PROJECT,
                         origin="mcp")
    assert a.origin == "mcp"
    # Operator pin over the near-duplicate: corroboration by higher authority → upgrade in place.
    b = service.pin_scar("db wipe danger", "always snapshot first", project=PROJECT)
    assert b.id == a.id and b.origin == "pinned"
    assert [s.origin for s in service.db.all_scars()] == ["pinned"]
    # Reverse direction: an MCP re-pin of an operator scar returns it unchanged.
    c = service.pin_scar("db wipe danger", "always snapshot first", project=PROJECT,
                         origin="mcp")
    assert c.id == a.id and c.origin == "pinned"
