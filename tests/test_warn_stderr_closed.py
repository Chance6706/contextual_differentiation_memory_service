"""A closed/broken stderr must never turn a lock-busy skip into a failed hook.

Regression for the real-store log line ``SessionEnd consolidation failed:
[Errno 22] Invalid argument``: Claude Code can tear down the hook's stderr pipe
at SessionEnd; on Windows the skip warning's ``print(..., file=sys.stderr)``
then raised EINVAL from inside the ``except TimeoutError`` handler."""
from __future__ import annotations

import sys

import pytest

from cdms import _warn
from cdms.lock import cross_process_lock
from cdms.pipeline import drain_and_ingest
from cdms.spool import spool_event


class _BrokenStderr:
    def write(self, *_a, **_k):
        raise OSError(22, "Invalid argument")

    def flush(self):
        raise OSError(22, "Invalid argument")


def test_warn_swallows_a_broken_stderr(monkeypatch):
    broken = _BrokenStderr()
    monkeypatch.setattr(sys, "stderr", broken)
    _warn.warn("hello")                       # no raise
    assert sys.stderr is not broken           # swapped for devnull so the shutdown flush cannot fail
    sys.stderr.write("still writable")
    _warn.warn("again")                       # goes to devnull, no raise
    monkeypatch.setattr(sys, "stderr", None)  # pythonw / detached: print(file=None) goes to stdout
    _warn.warn("hello")


def test_hook_exits_zero_when_the_host_closed_stderr(cfg):
    """End-to-end: a child whose stderr pipe the parent tore down (Claude Code at
    SessionEnd) must still exit 0 after a warning, not 120 from the shutdown flush."""
    import subprocess
    code = "from cdms._warn import warn; warn('lock busy'); warn('again')"
    p = subprocess.Popen([sys.executable, "-c", code], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stderr.close()
    p.wait(timeout=30)
    assert p.returncode == 0


def test_warn_still_reaches_a_working_stderr(capsys):
    _warn.warn("visible")
    assert "visible" in capsys.readouterr().err


def test_drain_skip_on_busy_lock_survives_a_broken_stderr(cfg, service, monkeypatch):
    spool_event(cfg, {"hook_event_name": "UserPromptSubmit", "session_id": "s", "prompt": "hi", "cwd": "x"})
    monkeypatch.setattr(sys, "stderr", _BrokenStderr())
    monkeypatch.setattr("cdms.pipeline._DRAIN_LOCK_TIMEOUT", 0.2)
    with cross_process_lock(cfg.lock_path):    # another "process" holds the store
        assert drain_and_ingest(cfg, service) == 0
    assert int(service.db.get_meta("drains_skipped", "0")) == 1
    assert cfg.queue_path.exists()            # nothing lost: the spool waits for the next drain


def test_consolidation_skip_survives_a_broken_stderr(cfg, service, monkeypatch):
    from cdms.consolidate import Consolidator
    monkeypatch.setattr(sys, "stderr", _BrokenStderr())
    con = Consolidator(cfg, db=service.db, embedder=service.embedder)
    with cross_process_lock(cfg.lock_path):
        monkeypatch.setattr("cdms.consolidate.cross_process_lock",
                            lambda path, timeout=90.0, poll=0.05: cross_process_lock(path, timeout=0.2, poll=poll))
        rep = con.run()
    assert rep.skipped is True
    assert int(service.db.get_meta("consolidations_skipped", "0")) == 1
