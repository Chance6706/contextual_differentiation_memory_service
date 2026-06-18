"""Ultra-light event spooling for the hot hook path.

Imports nothing heavy (no numpy / sqlite-vec / model code) so that a per-tool
``PostToolUse`` hook stays at roughly Python-startup latency. The heavyweight
drain/ingest path lives in :mod:`cdms.pipeline`.
"""

from __future__ import annotations

import json
import os
import sys

from .config import Config


def _over_cap(cfg: Config) -> bool:
    """True if the spool already exceeds its hard cap (drain isn't keeping up)."""
    try:
        return cfg.queue_path.stat().st_size >= cfg.spool_max_bytes
    except OSError:
        return False


def _append_bytes(path, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
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


def spool_event(cfg: Config, payload: dict) -> None:
    """Append a single hook event to the NDJSON queue (fast, no model load).

    Written as one ``os.write`` to an O_APPEND fd: a single append syscall is
    atomic with respect to other concurrent appenders (no torn/interleaved lines)
    and minimizes the window in which a killed subprocess could leave a partial
    line. The drain additionally skips any unparseable line defensively.

    If the spool has grown past ``spool_max_bytes`` (the drain is not running), the
    event is SHED — dropped with a one-line stderr warning — so a misconfigured
    daemon cannot grow the spool to GB and then OOM the eventual drain (which holds
    ~8x the file size in RAM). Bounded loss is preferable to an unrecoverable store.
    """
    cfg.ensure_home()
    if _over_cap(cfg):
        print(f"cdms: spool at {cfg.queue_path} exceeds {cfg.spool_max_bytes} bytes; "
              f"shedding event (is the drain running? run `cdms drain`).", file=sys.stderr)
        return
    data = (json.dumps(payload, ensure_ascii=False, default=str) + "\n").encode("utf-8")
    _append_bytes(cfg.queue_path, data)


def spool_event_lines(cfg: Config, lines: list[str]) -> None:
    """Append already-serialized NDJSON lines back to the spool (used by `forget`
    to rewrite the spool minus the events it dropped). One append syscall."""
    if not lines:
        return
    cfg.ensure_home()
    data = ("".join(ln if ln.endswith("\n") else ln + "\n" for ln in lines)).encode("utf-8")
    _append_bytes(cfg.queue_path, data)
