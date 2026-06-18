"""A small cross-process advisory lock used to serialize the non-atomic,
multi-step writers (consolidation, forget) that share one SQLite store.

Cycles 1–2 added per-statement transactions and WAL crash-recovery, but nothing
coordinated two *processes* both running a whole consolidation/forget pass at
once: a SessionEnd hook, a `cdms consolidate` cron, and the MCP daemon all share
the file. Without a mutex, two concurrent passes produce duplicate gists, double-
advance / lose the decay cycle counter, and let a concurrent consolidation
rebuild gists from episodes a `forget` is mid-delete on (resurrecting forgotten
content). This lock makes those passes mutually exclusive across processes.

POSIX uses ``fcntl.flock`` (auto-released if the holder dies — no stale locks).
Windows uses ``msvcrt.locking``. On any platform without either, the lock
degrades to a no-op (documented): correctness then relies on the operator not
running two daemons at once, which matches the pre-existing single-daemon design.
"""

from __future__ import annotations

import contextlib
import os
import time
from pathlib import Path

try:  # POSIX
    import fcntl

    def _try_acquire(fd) -> bool:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False

    def _release(fd) -> None:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass

    _HAVE_LOCK = True
except ImportError:  # pragma: no cover - Windows path
    try:
        import msvcrt

        def _try_acquire(fd) -> bool:
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                return True
            except OSError:
                return False

        def _release(fd) -> None:
            try:
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            except OSError:
                pass

        _HAVE_LOCK = True
    except ImportError:  # pragma: no cover - no advisory lock available
        _HAVE_LOCK = False


@contextlib.contextmanager
def cross_process_lock(path: Path, timeout: float = 90.0, poll: float = 0.05):
    """Hold an exclusive advisory lock on ``path`` for the duration of the block.

    Polls (non-blocking) so a wedged holder cannot hang a hook forever. Raises
    ``TimeoutError`` if the lock cannot be acquired within ``timeout`` seconds —
    callers decide whether to skip (consolidation) or surface it (forget).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not _HAVE_LOCK:
        yield  # best-effort no-op on platforms without an advisory lock primitive
        return
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
    deadline = time.monotonic() + max(0.0, timeout)
    try:
        while not _try_acquire(fd):
            if time.monotonic() >= deadline:
                raise TimeoutError(f"could not acquire {path} within {timeout}s")
            time.sleep(poll)
        yield
    finally:
        _release(fd)
        os.close(fd)
