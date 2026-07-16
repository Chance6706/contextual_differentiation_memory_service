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
        operator = {e.id for e in svc.history(limit=50)}                       # default: all
        model = {e.id for e in svc.history(limit=50, include_untrusted=False)}  # MCP-facing
        assert {"t", "u"} <= operator
        assert "t" in model and "u" not in model
        # db primitive parity
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
