"""Ultra-light event spooling for the hot hook path.

Imports nothing heavy (no numpy / sqlite-vec / model code) so that a per-tool
``PostToolUse`` hook stays at roughly Python-startup latency. The heavyweight
drain/ingest path lives in :mod:`cdms.pipeline`.
"""

from __future__ import annotations

import json
import os

from .config import Config


def spool_event(cfg: Config, payload: dict) -> None:
    """Append a single hook event to the NDJSON queue (fast, no model load).

    Written as one ``os.write`` to an O_APPEND fd: a single append syscall is
    atomic with respect to other concurrent appenders (no torn/interleaved lines)
    and minimizes the window in which a killed subprocess could leave a partial
    line. The drain additionally skips any unparseable line defensively.
    """
    cfg.ensure_home()
    data = (json.dumps(payload, ensure_ascii=False, default=str) + "\n").encode("utf-8")
    fd = os.open(cfg.queue_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        # Loop until the whole record (incl. its trailing newline) is written.
        # os.write may short-write under RLIMIT_FSIZE / ENOSPC / EINTR; a single
        # call could leave a newline-less partial line that swallows the NEXT
        # event when it concatenates onto it. The loop guarantees the newline lands.
        view = memoryview(data)
        off = 0
        while off < len(view):
            off += os.write(fd, view[off:])
    finally:
        os.close(fd)
