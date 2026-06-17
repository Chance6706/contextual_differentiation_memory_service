"""Ultra-light event spooling for the hot hook path.

Imports nothing heavy (no numpy / sqlite-vec / model code) so that a per-tool
``PostToolUse`` hook stays at roughly Python-startup latency. The heavyweight
drain/ingest path lives in :mod:`cdms.pipeline`.
"""

from __future__ import annotations

import json

from .config import Config


def spool_event(cfg: Config, payload: dict) -> None:
    """Append a single hook event to the NDJSON queue (fast, no model load)."""
    cfg.ensure_home()
    line = json.dumps(payload, ensure_ascii=False, default=str)
    with open(cfg.queue_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
