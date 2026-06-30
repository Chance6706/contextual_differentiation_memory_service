"""A2 (2026-06-29): CDMS-A store relocated to the dedicated ``~/.local_memory/cdms-a`` subtree (parallel to
CDMS-D's ``cdms-d``), with a one-time atomic-rename migration of a legacy root-level store. These lock the
relocation + migration safety (no clobber, no data-loss, idempotent, override-respecting)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from cdms.config import Config, _default_home  # noqa: E402

LEGACY_FILES = ["memory.db", "memory.db-wal", "memory.db-shm", "episodic_queue.ndjson",
                "state.json", "config.json", "cdms.log", "consolidate.lock"]


def _seed_legacy(root: Path, files=LEGACY_FILES):
    root.mkdir(parents=True, exist_ok=True)
    for f in files:
        (root / f).write_text(f"legacy::{f}", encoding="utf-8")


def test_default_home_is_cdms_a_subtree(monkeypatch):
    monkeypatch.delenv("CDMS_HOME", raising=False)
    assert _default_home() == Path.home() / ".local_memory" / "cdms-a"


def test_cdms_home_env_override_respected(monkeypatch, tmp_path):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path / "scoped"))
    assert _default_home() == tmp_path / "scoped"


def test_migration_moves_full_legacy_store(tmp_path):
    _seed_legacy(tmp_path)  # legacy store at tmp_path/memory.db etc.
    cfg = Config(home=tmp_path / "cdms-a")
    cfg.ensure_home()
    for f in LEGACY_FILES:
        assert (tmp_path / "cdms-a" / f).read_text(encoding="utf-8") == f"legacy::{f}", f"{f} not moved"
        assert not (tmp_path / f).exists(), f"{f} left behind in legacy root"


def test_migration_no_clobber_of_existing_subtree_store(tmp_path):
    _seed_legacy(tmp_path)
    (tmp_path / "cdms-a").mkdir()
    (tmp_path / "cdms-a" / "memory.db").write_text("NEW", encoding="utf-8")
    cfg = Config(home=tmp_path / "cdms-a")
    cfg.ensure_home()
    assert (tmp_path / "cdms-a" / "memory.db").read_text(encoding="utf-8") == "NEW"   # not clobbered
    assert (tmp_path / "memory.db").read_text(encoding="utf-8") == "legacy::memory.db"  # legacy untouched


def test_migration_idempotent(tmp_path):
    _seed_legacy(tmp_path)
    cfg = Config(home=tmp_path / "cdms-a")
    cfg.ensure_home()
    cfg.ensure_home()  # second call must be a clean no-op
    assert (tmp_path / "cdms-a" / "memory.db").read_text(encoding="utf-8") == "legacy::memory.db"


def test_no_op_without_legacy(tmp_path):
    cfg = Config(home=tmp_path / "cdms-a")
    cfg.ensure_home()
    assert (tmp_path / "cdms-a").is_dir()
    assert not (tmp_path / "cdms-a" / "memory.db").exists()


def test_non_cdms_a_home_not_migrated(tmp_path):
    _seed_legacy(tmp_path)
    cfg = Config(home=tmp_path / "custom")  # explicit, not a cdms-a subtree
    cfg.ensure_home()
    assert (tmp_path / "memory.db").exists()                  # legacy untouched
    assert not (tmp_path / "custom" / "memory.db").exists()   # nothing moved in


def test_partial_legacy_only_db(tmp_path):
    _seed_legacy(tmp_path, files=["memory.db"])  # db without sidecars
    cfg = Config(home=tmp_path / "cdms-a")
    cfg.ensure_home()
    assert (tmp_path / "cdms-a" / "memory.db").read_text(encoding="utf-8") == "legacy::memory.db"
    assert not (tmp_path / "memory.db").exists()
