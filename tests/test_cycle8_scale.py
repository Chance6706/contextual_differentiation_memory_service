"""Cycle 8 — scale + config-hardening fixes (H-4, M-S-1, H-3, M-7, M-S-5, L-5, L-2)."""

from __future__ import annotations

import json

from cdms.config import Config, load_config
from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.models import Scar
from cdms.pipeline import _brief
from cdms.store import MemoryService


def _svc(tmp_path, **over):
    cfg = Config(home=tmp_path)
    for k, v in over.items():
        setattr(cfg, k, v)
    return MemoryService(cfg, embedder=Embedder(cfg)), cfg


def _mk_scar(svc, i, origin, project="proj", ts=None):
    s = Scar(id=f"s_{origin}_{i:03d}", crisis_trigger=f"crisis {i}",
             remediation_rule=f"rule {i}", project=project, origin=origin,
             timestamp=ts or f"2020-01-01T00:00:{i % 60:02d}Z")
    svc.db.insert_scar(s, svc.embedder.embed_one(s.search_text()))
    return s


# --- H-4: bounded L3 scar table, guardrails exempt -------------------------- #
def test_h4_pinned_scars_never_evicted_over_cap(tmp_path):
    svc, cfg = _svc(tmp_path, scar_project_cap=5)
    try:
        for i in range(50):
            _mk_scar(svc, i, "pinned")
        rep = Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        assert rep.scars_evicted == 0
        assert svc.db.stats()["scars"] == 50
    finally:
        svc.close()


def test_h4_only_elevated_evicted_pinned_uncounted(tmp_path):
    svc, cfg = _svc(tmp_path, scar_project_cap=3)
    try:
        for i in range(3):
            _mk_scar(svc, i, "pinned")
        for i in range(10):
            _mk_scar(svc, 100 + i, "elevated")
        rep = Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        survivors = svc.db.all_scars()
        assert sum(1 for s in survivors if s.origin == "pinned") == 3
        assert sum(1 for s in survivors if s.origin == "elevated") == 3
        assert rep.scars_evicted == 7
    finally:
        svc.close()


def test_h4_evicts_oldest_elevated_first(tmp_path):
    svc, cfg = _svc(tmp_path, scar_project_cap=2)
    try:
        for i in range(5):
            _mk_scar(svc, i, "elevated", ts=f"2021-01-0{i + 1}T00:00:00Z")
        rep = Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        survivors = {s.id for s in svc.db.all_scars()}
        assert rep.scars_evicted == 3
        assert survivors == {"s_elevated_003", "s_elevated_004"}  # newest two
    finally:
        svc.close()


def test_h4_under_cap_no_eviction(tmp_path):
    svc, cfg = _svc(tmp_path, scar_project_cap=10)
    try:
        for i in range(7):
            _mk_scar(svc, i, "elevated")
        rep = Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        assert rep.scars_evicted == 0
        assert svc.db.stats()["scars"] == 7
    finally:
        svc.close()


def test_h4_per_project_independent(tmp_path):
    svc, cfg = _svc(tmp_path, scar_project_cap=2)
    try:
        for i in range(5):
            _mk_scar(svc, i, "elevated", project="A")
        _mk_scar(svc, 99, "elevated", project="B")
        rep = Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        survivors = svc.db.all_scars()
        assert sum(1 for s in survivors if s.project == "A") == 2  # capped
        assert sum(1 for s in survivors if s.project == "B") == 1  # under cap
        assert rep.scars_evicted == 3
    finally:
        svc.close()


# --- M-S-1: gated VACUUM after bulk deletes --------------------------------- #
def test_msi_vacuum_runs_above_threshold(tmp_path, monkeypatch):
    svc, cfg = _svc(tmp_path, scar_project_cap=1, vacuum_after_deletes=1)
    try:
        calls = {"n": 0}
        monkeypatch.setattr(svc.db, "vacuum", lambda: calls.__setitem__("n", calls["n"] + 1))
        for i in range(5):
            _mk_scar(svc, i, "elevated")            # 4 will be evicted (>= threshold 1)
        rep = Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        assert rep.scars_evicted == 4
        assert calls["n"] == 1
    finally:
        svc.close()


def test_msi_vacuum_skipped_below_threshold(tmp_path, monkeypatch):
    svc, cfg = _svc(tmp_path, scar_project_cap=1, vacuum_after_deletes=10_000)
    try:
        calls = {"n": 0}
        monkeypatch.setattr(svc.db, "vacuum", lambda: calls.__setitem__("n", calls["n"] + 1))
        for i in range(5):
            _mk_scar(svc, i, "elevated")
        Consolidator(cfg, db=svc.db, embedder=svc.embedder).run()
        assert calls["n"] == 0                        # below threshold -> no rewrite
    finally:
        svc.close()


# --- H-3: home path-traversal rejected -------------------------------------- #
def test_h3_home_traversal_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", "../../etc/cdms-x")
    assert load_config().home == Config().home          # reset to default


def test_h3_absolute_home_preserved(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path / "relocated"))
    assert load_config().home == (tmp_path / "relocated")  # legit relocation untouched


# --- M-7 / M-S-5: loopback-only networking ---------------------------------- #
def test_m7_http_host_nonloopback_clamped(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_HTTP_HOST", "0.0.0.0")
    assert load_config().http_host == "127.0.0.1"


def test_m7_http_host_loopback_preserved(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_HTTP_HOST", "127.0.0.9")
    assert load_config().http_host == "127.0.0.9"


def test_ms5_render_url_nonloopback_clamped(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_RENDER_BASE_URL", "http://169.254.169.254/latest/meta-data/")
    assert load_config().render_base_url == Config().render_base_url


def test_ms5_render_url_loopback_preserved(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_RENDER_BASE_URL", "http://127.0.0.1:9999/v1")
    assert load_config().render_base_url == "http://127.0.0.1:9999/v1"


# --- L-5: JSON bool not coerced to a numeric field -------------------------- #
def test_l5_json_bool_rejected_for_int_field(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    (tmp_path / "config.json").write_text(json.dumps({"embed_dim": True}), encoding="utf-8")
    assert load_config().embed_dim == Config().embed_dim    # stays default, not int(True)==1


# --- L-2: redaction happens before truncation ------------------------------- #
def test_l2_brief_redacts_before_truncation():
    secret = "AKIA" + "B" * 16                          # AWS access key id shape, past the limit
    out = _brief("x" * 290 + " " + secret, limit=300)
    # Redact-before-truncate: no fragment of the key survives the clip (truncate-first would
    # have left an "AKIABBB…" prefix). A redaction marker is present.
    assert "AKIA" not in out
    assert "REDACT" in out
