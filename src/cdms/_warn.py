"""Operator warnings that can never take a hook down.

Library code warns on stderr for skipped drains/consolidations, shed spool
events and embedder drift. When a hook runs at SessionEnd the parent may have
already closed the stderr pipe; on Windows a write then raises
``OSError: [Errno 22] Invalid argument`` (EINVAL), and a warning raised from
inside an ``except TimeoutError`` handler turned a benign "skip" into
``SessionEnd consolidation failed: [Errno 22] Invalid argument`` (seen eight
times in a real store, 2026-07-30 .. 2026-09-06, always coinciding with a
drain/consolidation skip). The warning is best-effort by definition: the
durable signal is the meta counter / cdms.log line, never stderr.
"""
from __future__ import annotations

import os
import sys


def warn(msg: str) -> None:
    """Print ``msg`` to stderr; silently give up if stderr is gone or broken.

    After the first failed write ``sys.stderr`` is swapped for ``os.devnull``:
    the dead wrapper still holds the unflushed text, and the interpreter's
    shutdown flush of ``sys.stderr`` would fail again and turn a clean run into
    exit status 120, which the hook host reports as a failed hook.
    """
    try:
        print(msg, file=sys.stderr)
    except (OSError, ValueError, AttributeError):
        try:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")
        except Exception:
            pass
