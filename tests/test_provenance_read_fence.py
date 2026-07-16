"""Read-side Layer-3 provenance fence.

Untrusted-provenance episodes must not surface on any MODEL-facing read path
(retrieve, MCP-facing history, the self-layer preamble), while operator/
maintenance paths still see everything. Only the episodic tier can hold
untrusted content (gists/scars are trusted by construction), so the fence is
episodic-only and gated on cfg.enforce_provenance.
"""
from __future__ import annotations

import os

os.environ["CDMS_EMBED_BACKEND"] = "hash"   # offline, deterministic

from cdms.config import Config
from cdms.embeddings import Embedder
from cdms.hooks import _build_preamble_text, _session_start_context
from cdms.models import Episodic
from cdms.store import MemoryService


def _svc(home, **cfgkw):
    cfg = Config(home=home, **cfgkw)
    return MemoryService(cfg, embedder=Embedder(cfg))


def _add(svc, id_, text, provenance, project="", salience=0.5):
    ep = Episodic(id=id_, trigger_prompt=text, action_taken=text,
                  base_salience=salience, s0=salience, project=project,
                  provenance=provenance)
    svc.db.insert_episodic(ep, svc.embedder.embed_one(ep.search_text()))


def test_retrieve_filters_untrusted_by_default(tmp_path):
    svc = _svc(tmp_path)
    try:
        _add(svc, "trusted1", "harbor sync keeper detail", "trusted")
        _add(svc, "intruder", "harbor sync intruder detail", "untrusted")
        default = {h.id for h in svc.retrieve("harbor sync detail", top_k=10, tiers=("episodic",))}
        assert "trusted1" in default
        assert "intruder" not in default                      # filtered by default
        opted = {h.id for h in svc.retrieve("harbor sync detail", top_k=10,
                                            tiers=("episodic",), include_untrusted=True)}
        assert "intruder" in opted                            # explicit opt-in surfaces it
    finally:
        svc.close()


def test_retrieve_unfiltered_when_enforce_provenance_off(tmp_path):
    svc = _svc(tmp_path, enforce_provenance=False)
    try:
        _add(svc, "u", "kestrel log external entry", "untrusted")
        got = {h.id for h in svc.retrieve("kestrel log external entry", top_k=10, tiers=("episodic",))}
        assert "u" in got                                     # Layer-3 off -> read filter off
    finally:
        svc.close()


def test_history_model_facing_filters_operator_sees_all(tmp_path):
    svc = _svc(tmp_path)
    try:
        _add(svc, "t", "trusted timeline entry", "trusted")
        _add(svc, "u", "untrusted timeline entry", "untrusted")
        # Service layer is MODEL-facing and fail-closed by default; the operator opts in.
        operator = {e.id for e in svc.history(limit=50, include_untrusted=True)}
        model = {e.id for e in svc.history(limit=50)}                          # default: filtered
        assert {"t", "u"} <= operator
        assert "t" in model and "u" not in model
        # db primitive parity: the RAW maintenance primitive still defaults to ALL rows.
        assert "u" not in {e.id for e in svc.db.recent_episodic(50, include_untrusted=False)}
        assert "u" in {e.id for e in svc.db.recent_episodic(50)}               # default all
    finally:
        svc.close()


def test_untrusted_majority_does_not_starve_trusted(tmp_path):
    # Many untrusted + few trusted, all sharing the query tokens: the post-pool
    # provenance filter must trigger the widen loop so the 2 trusted aren't
    # crowded out of the top-k by the untrusted majority.
    svc = _svc(tmp_path)
    try:
        for i in range(30):
            _add(svc, f"noise{i}", "common shared retrieval topic", "untrusted")
        _add(svc, "keepA", "common shared retrieval topic", "trusted")
        _add(svc, "keepB", "common shared retrieval topic", "trusted")
        got = {h.id for h in svc.retrieve("common shared retrieval topic", top_k=5, tiers=("episodic",))}
        assert "keepA" in got and "keepB" in got
        assert not any(g.startswith("noise") for g in got)
    finally:
        svc.close()


def test_preamble_excludes_untrusted_recent(tmp_path):
    # The self-layer preamble (-D consumes this) must not surface untrusted
    # episodes in its "recent" window. Fresh store => 0 gists => recent path runs.
    for name, build in (("shipped", lambda c, p: _session_start_context(c, p)),
                        ("harness", lambda c, p: _build_preamble_text(c, p, "v1"))):
        home = tmp_path / name
        svc = _svc(home)
        _add(svc, "self", "TRUSTEDSELFMARKER did a real task", "trusted")
        _add(svc, "ext", "UNTRUSTEDINTRUDER planted external claim", "untrusted")
        svc.close()
        text = build(Config(home=home), {"cwd": ""})
        assert "UNTRUSTEDINTRUDER" not in text, name          # the security property
        assert "TRUSTEDSELFMARKER" in text, name             # positive control: recent path ran


# --------------------------------------------------------------------------- #
# Fixes folded from the double pressure test (rule 12) before landing.
# --------------------------------------------------------------------------- #
def test_history_default_is_fail_closed(tmp_path):
    # MemoryService.history is MODEL-facing by default: no include_untrusted -> filtered.
    # (Regression guard: the initial fence commit defaulted this True, trapping -D's library path.)
    svc = _svc(tmp_path)
    try:
        _add(svc, "t", "trusted timeline entry", "trusted")
        _add(svc, "u", "untrusted timeline entry", "untrusted")
        default = {e.id for e in svc.history(limit=50)}
        assert "t" in default and "u" not in default          # fail-closed at the service boundary
        opted = {e.id for e in svc.history(limit=50, include_untrusted=True)}
        assert {"t", "u"} <= opted                             # operator opt-in still works
    finally:
        svc.close()


def test_operator_cli_sees_untrusted(tmp_path, monkeypatch, capsys):
    # M1/M2: operator surfaces must keep FULL visibility, or `cdms retrieve`/`history` report a
    # poisoned store "clean". cli.cmd_retrieve/cmd_history opt in explicitly.
    import argparse

    from cdms import cli
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    svc = _svc(tmp_path)
    _add(svc, "u", "OPERATORVISIBLE planted external note", "untrusted", salience=5.0)
    svc.close()

    cli.cmd_retrieve(argparse.Namespace(query="planted external note", k=10, json=False))
    assert "OPERATORVISIBLE" in capsys.readouterr().out       # operator recall shows untrusted
    cli.cmd_history(argparse.Namespace(n=50, session=""))
    assert "OPERATORVISIBLE" in capsys.readouterr().out       # operator timeline shows untrusted


def test_mcp_history_tool_filters_untrusted(tmp_path, monkeypatch):
    # S4: the MODEL-facing MCP history tool must not surface untrusted — pinned so a refactor
    # dropping its include_untrusted=False is caught (previously only the service layer was tested).
    import importlib

    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    import cdms.mcp_server as m
    importlib.reload(m)
    svc = _svc(tmp_path)
    _add(svc, "t", "trusted mcp entry", "trusted")
    _add(svc, "u", "untrusted mcp entry", "untrusted")
    svc.close()
    ids = {h.id for h in m.history(limit=50, session_id="")}
    assert "t" in ids and "u" not in ids


def test_canon_provenance_normalizes_and_fails_closed(tmp_path):
    # Non-canonical provenance must not slip past the `!= "untrusted"` fences.
    from cdms.models import canon_provenance
    from cdms.store import TurnEvent
    assert canon_provenance("trusted") == "trusted"
    assert canon_provenance("  Untrusted ") == "untrusted"     # case/space normalized
    assert canon_provenance("ambiguous") == "ambiguous"
    for weird in ("synthetic", "external", "", None, "hermes"):
        assert canon_provenance(weird) == "untrusted"          # unrecognized -> fail closed

    # End-to-end: a synthetic-labelled ingest is stored untrusted and stays out of model reads.
    svc = _svc(tmp_path)
    try:
        rec = svc.ingest(TurnEvent("SYNTHDREAM speculative content", "dreamed", "",
                                   provenance="synthetic", project=""))
        assert svc.db.get_episodic(rec.id).provenance == "untrusted"
        got = {h.id for h in svc.retrieve("speculative content", top_k=10, tiers=("episodic",))}
        assert rec.id not in got                                # fenced from model recall
    finally:
        svc.close()


def test_dedup_survivor_adopts_most_trusted_provenance(tmp_path):
    # red-S3: a trusted episode folded into an earlier untrusted near-duplicate must not be
    # buried inside a read-fenced untrusted survivor. The survivor is promoted to trusted so the
    # content stays model-visible.
    from cdms.consolidate import Consolidator
    cfg = Config(home=tmp_path)
    cfg.dedup_sim_threshold = 0.99
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        _add(svc, "u", "shared corroborated retrieval content", "untrusted", salience=5.0)  # earlier rowid
        _add(svc, "t", "shared corroborated retrieval content", "trusted", salience=5.0)    # folds in
        Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        survivor = svc.db.get_episodic("u")
        assert survivor is not None and svc.db.get_episodic("t") is None   # t folded into u
        assert survivor.provenance == "trusted"                            # promoted, not buried
        got = {h.id for h in svc.retrieve("shared corroborated retrieval content",
                                          top_k=10, tiers=("episodic",))}
        assert "u" in got                                                  # survives the read fence
    finally:
        svc.close()


def test_ambiguous_still_surfaces_on_model_read(tmp_path):
    # Design pin (LAYER3 table): the fence drops ONLY untrusted; ambiguous (quarantine) still
    # surfaces on model reads and can gist — it just can't elevate. Guards against an over-broad
    # future refactor to an allowlist.
    svc = _svc(tmp_path)
    try:
        _add(svc, "amb", "AMBIGUOUSMARKER quarantined content", "ambiguous")
        got = {h.id for h in svc.retrieve("quarantined content", top_k=10, tiers=("episodic",))}
        assert "amb" in got
        assert "amb" in {e.id for e in svc.history(limit=50)}   # model-facing history too
    finally:
        svc.close()


def test_enforce_provenance_off_surfaces_everywhere(tmp_path):
    # Layer-3 OFF => the read fence is fully disabled (history + preamble), symmetric with retrieve.
    home = tmp_path / "off"
    svc = _svc(home, enforce_provenance=False)
    _add(svc, "u", "OFFSWITCHUNTRUSTED external entry", "untrusted")
    assert "u" in {e.id for e in svc.history(limit=50)}         # history unfiltered when off
    svc.close()
    text = _build_preamble_text(Config(home=home, enforce_provenance=False), {"cwd": ""})
    assert "OFFSWITCHUNTRUSTED" in text                         # preamble unfiltered when off
