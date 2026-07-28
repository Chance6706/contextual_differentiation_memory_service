"""Shared fixtures. Tests run on the deterministic hash embedder (no downloads)."""

from __future__ import annotations

import os
import tempfile

import pytest

# Force the offline deterministic embedding backend for all tests.
os.environ["CDMS_EMBED_BACKEND"] = "hash"
# Never let a test resolve CDMS_HOME to the real user store. The hash backend above makes
# an unisolated write doubly destructive: one dev-loop run (2026-06-18) leaked a single
# hash-space row into the real store, pinning its embedder fingerprint and refusing every
# real capture for a month. Session-level fallback here (covers import-time code); a
# per-test tmp dir via the autouse fixture below.
os.environ["CDMS_HOME"] = tempfile.mkdtemp(prefix="cdms-test-home-")

from cdms.config import Config  # noqa: E402
from cdms.embeddings import Embedder  # noqa: E402
from cdms.store import MemoryService  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_cdms_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))


@pytest.fixture
def cfg(tmp_path) -> Config:
    return Config(home=tmp_path)


@pytest.fixture
def service(cfg) -> MemoryService:
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    yield svc
    svc.close()
