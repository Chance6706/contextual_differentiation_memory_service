"""Regression tests for config validation + store recovery (Cycle-2 HIGH).

  - JSON config values are type-coerced (a stringified dim used to brick the store);
  - nonsensical values (K<=0, decay>=1, dim<=0) are repaired to defaults, not used;
  - conserve_budget with a non-positive budget is a no-op (never wipes memory);
  - a corrupt memory.db is quarantined and a fresh store started (capture survives);
  - `cdms doctor` detects an embedding-space fingerprint mismatch.
"""

from __future__ import annotations

import argparse
import json

from cdms.config import Config, load_config
from cdms.db import Database
from cdms.salience import conserve_budget


def test_json_config_is_type_coerced(tmp_path, monkeypatch):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    (tmp_path / "config.json").write_text(json.dumps({"embed_dim": "384", "max_field_chars": "5000"}))
    cfg = load_config()
    assert cfg.embed_dim == 384 and isinstance(cfg.embed_dim, int)
    assert cfg.max_field_chars == 5000 and isinstance(cfg.max_field_chars, int)


def test_invalid_config_values_repaired_to_default(tmp_path, monkeypatch):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    (tmp_path / "config.json").write_text(json.dumps({
        "salience_budget": 0, "gist_decay_per_cycle": 2.0, "embed_dim": -5,
        "project_budget_cap": 3.0, "reinforce_alpha": 1.0}))
    cfg, d = load_config(), Config()
    assert cfg.salience_budget == d.salience_budget
    assert cfg.gist_decay_per_cycle == d.gist_decay_per_cycle
    assert cfg.embed_dim == d.embed_dim
    assert cfg.project_budget_cap == d.project_budget_cap
    assert cfg.reinforce_alpha == d.reinforce_alpha


def test_conserve_budget_nonpositive_k_is_noop():
    assert conserve_budget([1.0, 2.0, 3.0], 0) == [1.0, 2.0, 3.0]
    assert conserve_budget([1.0, 2.0], -100) == [1.0, 2.0]


def test_corrupt_db_is_quarantined_and_recreated(tmp_path):
    (tmp_path / "memory.db").write_bytes(b"this is definitely not a sqlite database " * 200)
    db = Database(Config(home=tmp_path))
    try:
        assert db.stats()["episodic"] == 0           # fresh, working store
        assert list(tmp_path.glob("memory.db.corrupt-*"))  # bad file preserved
    finally:
        db.close()


def test_doctor_detects_fingerprint_mismatch(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    db = Database(Config(home=tmp_path))
    db.set_meta("embed_fingerprint", "fastembed:some-other-model:384")
    db.close()
    from cdms.cli import cmd_doctor
    rc = cmd_doctor(argparse.Namespace())
    out = capsys.readouterr().out
    assert "MISMATCH" in out
    assert rc == 1
