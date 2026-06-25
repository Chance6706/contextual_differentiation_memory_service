"""CDMS Viewport — a loopback, read-only browser dashboard over the CDMS store.

A window into the agent's accumulated self: the three tiers (episodic / gist / scars),
the temperament disposition, and a live ingestion feed. Read-only consumer of
``cdms.store``; it never modifies CDMS state. Launch with ``cdms viewport`` or
``python -m cdms.viewport``.
"""
from .server import main

__all__ = ["main"]
