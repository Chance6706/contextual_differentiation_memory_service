"""Regression tests for docs/REPO_ANALYSIS_2026-07-01.md §6 (fix-now + fix-soon tiers).

Covers, 1:1 with the findings:
  S1      — store db/-wal/-shm and home dir are owner-only (POSIX; no-op on Windows)
  S2      — `cdms observe` refuses a non-loopback bind (mirrors the viewport)
  core #2 — a transient embedder outage ABORTS the drain and PRESERVES the spooled
            backlog for retry, instead of skipping every turn and deleting the claim
  S4      — MCP store(kind="scar") mints a DEMOTED agent note (origin="mcp"): never
            rendered in the authoritative guardrails block, counted toward the L3 cap,
            evicted before auto-elevated scars, upgradeable only by an operator pin
  core #1 — scar elevation is scale-invariant: the crisis gate reads the persisted
            write-time s0 (renorm-immune); dedup preserves cross-session crisis
            multiplicity; a corroborated catastrophe promotes a matching agent note
  core #3 — project-scoped retrieval widens the candidate pool instead of starving
            small projects in a shared store; find_duplicate_scar likewise
  S3      — redaction covers JSON quoted-key secrets, URL userinfo passwords,
            Authorization: Bearer tokens, and Stripe sk_(live|test)_ keys
  item 8  — MCP tools serialize shared-connection DB access (concurrency hammer)
  core #4 — a failed forget-rewrite preserves the spool claim (reclaimable) instead
            of destroying the kept lines; the claim uses the reclaimable suffix
  core #5 — allocate_capped_proportional honors the cap in the all-zero branch
  core #6 — db.delete_* return actual rows deleted, not the requested count
  core #7 — list_paths is project-scoped through db/store/MCP layers
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


# --------------------------------------------------------------------------- #
# core #1 — scale-invariant scar elevation
# --------------------------------------------------------------------------- #
CRISIS_TRIGGER = "deploy went catastrophically wrong on production"
CRISIS_ACTION = "ran drop schema on the prod database, data lost, fatal corruption"
CRISIS_OUTCOME = "always take a verified backup before destructive operations"


def _ingest_crisis(service, session: str):
    return service.ingest(TurnEvent(
        trigger_prompt=CRISIS_TRIGGER, action_taken=CRISIS_ACTION,
        outcome_feedback=CRISIS_OUTCOME, success=False,
        session_id=session, project=PROJECT))


def _ingest_routine(service, session: str, n: int):
    for i in range(n):
        service.ingest(TurnEvent(
            trigger_prompt=f"please handle routine chore number {i}",
            action_taken=f"completed routine chore number {i} without issue",
            outcome_feedback="done", success=True,
            session_id=session, project=PROJECT))


def _consolidate(service, cfg):
    from datetime import datetime, timezone

    from cdms.consolidate import Consolidator
    con = Consolidator(cfg, db=service.db, embedder=service.embedder)
    return con.run(now=datetime.now(timezone.utc))


def test_scar_elevation_survives_renormalization_across_passes(service, cfg):
    """The review's repro: in a busy store, renormalization diluted an uncorroborated
    catastrophe's base_salience below crisis_threshold after its first pass, so a
    recurrence in a later session could never corroborate it (0 scars after distinct-
    session catastrophes). The gate now reads the persisted write-time s0."""
    cfg.salience_budget = 50.0   # deep dilution with a small episode count (fast test)

    rec = _ingest_crisis(service, "s1")
    assert rec.s0 == pytest.approx(cfg.crisis_threshold)   # flashbulb floor fired
    _ingest_routine(service, "s1", 40)

    rep1 = _consolidate(service, cfg)
    assert rep1.scars_created == 0                          # single session: uncorroborated
    diluted = service.db.get_episodic(rec.id)
    assert diluted is not None
    assert diluted.base_salience < cfg.crisis_threshold, "premise: renorm diluted the crisis"
    assert diluted.s0 == pytest.approx(cfg.crisis_threshold), "s0 is renorm-immune"

    _ingest_crisis(service, "s2")                           # the recurrence
    rep2 = _consolidate(service, cfg)
    assert rep2.scars_created == 1, "cross-pass corroboration must elevate despite dilution"
    scars = service.db.all_scars()
    assert len(scars) == 1 and scars[0].origin == "elevated"


def test_dedup_preserves_cross_session_crisis_multiplicity(service, cfg):
    """With min_sessions=3, two same-crisis episodes from different sessions are NOT
    corroborated yet — dedup previously folded them (dedup threshold == corroboration
    threshold), permanently destroying the session multiplicity the gate counts."""
    cfg.scar_elevation_min_sessions = 3

    a = _ingest_crisis(service, "s1")
    b = _ingest_crisis(service, "s2")
    rep1 = _consolidate(service, cfg)
    assert rep1.scars_created == 0
    live = {e.id for e in service.db.all_episodic()}
    assert a.id in live and b.id in live, "dedup must not fold pending cross-session crises"

    _ingest_crisis(service, "s3")
    rep2 = _consolidate(service, cfg)
    assert rep2.scars_created == 1, "third session completes corroboration"


def test_routine_dedup_still_folds(service, cfg):
    """The multiplicity guard is crisis-specific: ordinary near-duplicates across
    sessions still dedup."""
    for sess in ("s1", "s2"):
        service.ingest(TurnEvent(
            trigger_prompt="please tidy the workspace files",
            action_taken="tidied the workspace files carefully",
            outcome_feedback="done", success=True, session_id=sess, project=PROJECT))
    rep = _consolidate(service, cfg)
    assert rep.deduped == 1


def test_corroborated_catastrophe_promotes_matching_agent_note(service, cfg):
    """An agent-pinned (mcp) note must not SHADOW a real recurring catastrophe by
    consuming its episodes as 'already handled'; corroborated evidence promotes the
    note in place to an elevated guardrail (authority earned) — no duplicate row."""
    note = service.pin_scar(f"{CRISIS_TRIGGER} {CRISIS_ACTION}", CRISIS_OUTCOME,
                            project=PROJECT, origin="mcp")
    _ingest_crisis(service, "s1")
    _ingest_crisis(service, "s2")
    rep = _consolidate(service, cfg)
    assert rep.scars_created == 1
    scars = service.db.all_scars()
    assert len(scars) == 1, "promotion in place — no duplicate L3 row"
    assert scars[0].id == note.id and scars[0].origin == "elevated"
    crises = [e for e in service.db.all_episodic() if CRISIS_TRIGGER in e.trigger_prompt]
    assert not crises, "corroborating episodes consumed"


def test_uncorroborated_catastrophe_does_not_promote_agent_note(service, cfg):
    """One session of evidence is not corroboration: the note stays demoted."""
    note = service.pin_scar(f"{CRISIS_TRIGGER} {CRISIS_ACTION}", CRISIS_OUTCOME,
                            project=PROJECT, origin="mcp")
    _ingest_crisis(service, "s1")
    rep = _consolidate(service, cfg)
    assert rep.scars_created == 0
    assert [s.origin for s in service.db.all_scars() if s.id == note.id] == ["mcp"]


def test_legacy_store_without_s0_column_migrates(tmp_path):
    """A pre-s0 store gains the column on open; legacy rows read back s0=None and the
    elevation gate falls back (flashbulb floor on -> inferred crisis-salient)."""
    import sqlite3 as sq

    from cdms.db import Database

    cfg = Config(home=tmp_path / "cdms-a")
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    rec = _ingest_crisis(svc, "s1")
    svc.close()

    raw = sq.connect(str(cfg.db_path))
    raw.execute("ALTER TABLE mem_episodic DROP COLUMN s0")   # simulate a legacy store
    raw.commit()
    raw.close()

    db = Database(cfg)
    try:
        legacy = db.get_episodic(rec.id)
        assert legacy is not None and legacy.s0 is None
        cols = {r[1] for r in db.conn.execute("PRAGMA table_info(mem_episodic)")}
        assert "s0" in cols, "migration re-added the column"
    finally:
        db.conn.close()


# --------------------------------------------------------------------------- #
# core #3 — scoped retrieval pool starvation
# --------------------------------------------------------------------------- #
def test_scoped_retrieve_not_starved_in_shared_store(service, cfg):
    """The review's repro: 300 matching episodes in project A + 3 in project B; a
    B-scoped retrieve previously pooled 20 candidates (all A), filtered, and returned
    0 despite direct hits. The pool now widens until scoped hits fill or the index is
    exhausted."""
    from cdms.models import Episodic

    text = "database migration script run completed"
    ids_b = []
    for i in range(303):
        proj = "B" if i >= 300 else "A"
        e = Episodic(id=new_id("ep"), trigger_prompt=text,
                     action_taken=text, outcome_feedback="ok",
                     valence=0.2, base_salience=1.0, session_id=f"s{i % 7}", project=proj)
        service.db.insert_episodic(e, service.embedder.embed_one(e.search_text()))
        if proj == "B":
            ids_b.append(e.id)

    hits = service.retrieve(text, top_k=8, tiers=("episodic",), project="B", reinforce=False)
    assert len(hits) == 3, f"scoped recall starved: {len(hits)}/3 project-B hits"
    assert {h.id for h in hits} == set(ids_b)


def test_find_duplicate_scar_not_crowded_by_other_projects(service, cfg):
    """Same pattern at pool=5: another project's near-neighbours crowded out this
    project's true duplicate, so a recurring failure minted duplicate permanent rows."""
    text_t, text_r = "force push wiped shared history", "never force push shared branches"
    emb = None
    for i in range(8):
        s = Scar(id=new_id("scar"), crisis_trigger=text_t, remediation_rule=text_r,
                 project="A", origin="elevated")
        emb = service.embedder.embed_one(s.search_text())
        service.db.insert_scar(s, emb)
    sb = Scar(id=new_id("scar"), crisis_trigger=text_t, remediation_rule=text_r,
              project="B", origin="elevated")
    service.db.insert_scar(sb, service.embedder.embed_one(sb.search_text()))

    dup = service.db.find_duplicate_scar(emb, "B", cfg.scar_dedup_sim_threshold)
    assert dup is not None and dup.id == sb.id


# --------------------------------------------------------------------------- #
# S3 — redaction coverage
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("payload,secret", [
    ('config: {"api_key": "sk_live_4eC39HqLyjWDarjtT1zd"}', "sk_live_4eC39HqLyjWDarjtT1zd"),
    ('{"DB_PASSWORD": "hunter2secret"}', "hunter2secret"),
    ("DATABASE_URL=postgres://admin:hunter2secret@db.example.com:5432/app", "hunter2secret"),
    ("curl -H 'Authorization: Bearer o9uP3.opaque-token_1234'", "o9uP3.opaque-token_1234"),
    ("stripe key sk_test_FAKEFAKEFAKEFAKE1234", "sk_test_FAKEFAKEFAKEFAKE1234"),
    ("restricted rk_live_FAKEFAKEFAKEFAKE1234", "rk_live_FAKEFAKEFAKEFAKE1234"),
])
def test_redaction_covers_reported_misses(payload, secret):
    from cdms.store import redact_secrets

    out = redact_secrets(payload)
    assert secret not in out, out
    assert "[REDACTED]" in out


def test_redaction_keeps_nonsecret_structure_legible():
    from cdms.store import redact_secrets

    out = redact_secrets("postgres://admin:hunter2secret@db.example.com/app")
    assert out.startswith("postgres://admin:[REDACTED]@db.example.com"), out


@pytest.mark.parametrize("benign", [
    "the ratio is 3:2 at scale",
    "see https://example.com/path for details",
    "authorization of the budget was approved yesterday",
    "meeting rescheduled to 10:30 tomorrow",
    "the token bucket algorithm rate-limits requests",
])
def test_redaction_does_not_over_redact(benign):
    from cdms.store import redact_secrets

    assert redact_secrets(benign) == benign


# --------------------------------------------------------------------------- #
# item 8 — MCP shared-connection serialization
# --------------------------------------------------------------------------- #
def test_mcp_tools_survive_concurrent_hammer(tmp_path, monkeypatch):
    import threading

    m = _fresh_server(tmp_path, monkeypatch)
    errors: list[BaseException] = []

    def worker(w: int):
        try:
            for i in range(8):
                m.store(content=f"worker {w} observation {i} about the build",
                        kind="episode", project=PROJECT)
                m.retrieve(query="observation about the build", k=4, tiers="episodic",
                           project=PROJECT)
        except BaseException as exc:   # noqa: BLE001 - the assertion IS "no exception"
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(w,)) for w in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors
    assert m.service().db.stats()["episodic"] == 32   # every write intact, none torn


# --------------------------------------------------------------------------- #
# core #4 — forget-from-spool durability
# --------------------------------------------------------------------------- #
def test_forget_spool_rewrite_failure_preserves_kept_lines(tmp_path, monkeypatch):
    """A rewrite failure (e.g. ENOSPC) previously hit an unconditional unlink and
    silently destroyed every KEPT (unrelated) line. Now the claim survives, the
    error propagates loudly, and the orphan reclaim can re-ingest the backlog."""
    cfg = Config(home=tmp_path / "cdms-a")
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        for i, cwd in enumerate(["/proj/forget-me", "/proj/keep-me", "/proj/keep-me"]):
            spool_event(cfg, {"hook_event_name": "PostToolUse", "session_id": f"s{i}",
                              "cwd": cwd, "tool_name": "Bash", "tool_input": f"c{i}",
                              "tool_output": "ok", "success": True})

        import cdms.store as store_mod

        def boom(cfg_, lines):
            raise OSError(28, "No space left on device (test)")

        monkeypatch.setattr(store_mod, "spool_event_lines", boom, raising=False)
        # _forget_from_spool imports spool_event_lines from cdms.spool at call time
        import cdms.spool as spool_mod
        monkeypatch.setattr(spool_mod, "spool_event_lines", boom)

        with pytest.raises(OSError):
            svc._forget_from_spool("/proj/forget-me", None)

        claims = _claims(cfg)
        assert len(claims) == 1, "claim must survive a failed rewrite (reclaimable)"
        surviving = claims[0].read_text(encoding="utf-8")
        assert "keep-me" in surviving, "kept lines must not be destroyed"
    finally:
        svc.close()


def test_forget_spool_claim_uses_reclaimable_suffix(tmp_path):
    """The claim name follows the standard .processing convention, so a crash
    between rename and rewrite is covered by the orphan reclaim (the old
    .forget-<pid>.tmp name was invisible to its glob)."""
    cfg = Config(home=tmp_path / "cdms-a")
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        spool_event(cfg, {"hook_event_name": "PostToolUse", "session_id": "s1",
                          "cwd": "/keep", "tool_name": "Bash", "tool_input": "c",
                          "tool_output": "ok", "success": True})
        dropped = svc._forget_from_spool("/nomatch", None)
        assert dropped == 0
        assert not list(cfg.queue_path.parent.glob("*.tmp")), "no unreclaimable tmp files"
        assert not _claims(cfg), "claim consumed on success"
        assert cfg.queue_path.exists(), "kept lines rewritten to the live queue"
    finally:
        svc.close()


# --------------------------------------------------------------------------- #
# core #5 — allocator cap in the degenerate branch
# --------------------------------------------------------------------------- #
def test_allocator_all_zero_weights_respect_cap():
    from cdms.salience import allocate_capped_proportional

    alloc = allocate_capped_proportional({"a": 0.0, "b": 0.0}, total=100.0, cap_fraction=0.1)
    assert all(v <= 10.0 + 1e-9 for v in alloc.values()), alloc
    # And the normal path is unchanged: positive weights still conserve the total.
    alloc2 = allocate_capped_proportional({"a": 3.0, "b": 1.0}, total=100.0, cap_fraction=0.5)
    assert sum(alloc2.values()) == pytest.approx(100.0)
    assert max(alloc2.values()) <= 50.0 + 1e-9


# --------------------------------------------------------------------------- #
# core #6 — delete counts are actual rowcounts
# --------------------------------------------------------------------------- #
def test_delete_counts_report_actual_rows(service):
    rec = service.ingest(TurnEvent(trigger_prompt="a", action_taken="b",
                                   outcome_feedback="c", session_id="s1", project=PROJECT))
    assert service.db.delete_episodic([rec.id, "ep_does_not_exist"]) == 1
    assert service.db.delete_episodic([rec.id]) == 0          # already gone
    s = service.pin_scar("t", "r", project=PROJECT)
    assert service.db.delete_scar([s.id, "scar_missing"]) == 1
    g = service.upsert_fact("subj", "rel", "obj", project=PROJECT)
    assert service.db.delete_gist([g.id, g.id, "gist_missing"]) == 1   # dup ids don't double-count


# --------------------------------------------------------------------------- #
# core #7 — list_paths scoping
# --------------------------------------------------------------------------- #
def test_list_paths_is_project_scoped(service):
    service.upsert_fact("alpha-subj", "uses", "x", project="A")
    service.upsert_fact("beta-subj", "uses", "y", project="B")
    service.upsert_fact("global-subj", "uses", "z", project="")

    scoped = service.list_paths("B")
    subjects = {s for s, _r, _n in scoped}
    assert subjects == {"beta-subj", "global-subj"}, subjects
    # Unscoped (operator paths: CLI/viewport) unchanged.
    assert {s for s, _r, _n in service.list_paths()} == {"alpha-subj", "beta-subj", "global-subj"}


def test_mcp_list_paths_scoped_to_launch_project(tmp_path, monkeypatch):
    m = _fresh_server(tmp_path, monkeypatch)
    svc = m.service()
    svc.upsert_fact("other-proj-subj", "uses", "x", project="/some/other/project")
    svc.upsert_fact("here-subj", "uses", "y", project=m._LAUNCH_CWD)

    # Empty project coerces to the launch cwd (same rule as store/retrieve); direct
    # calls bypass pydantic's Field-default resolution, so pass it explicitly.
    subjects = {p.subject for p in m.list_paths(project="")}
    assert "here-subj" in subjects
    assert "other-proj-subj" not in subjects, "cross-project metadata leak (core #7)"
