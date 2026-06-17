"""Shared fixtures. Tests run on the deterministic hash embedder (no downloads)."""

from __future__ import annotations

import os

import pytest

# Force the offline deterministic embedding backend for all tests.
os.environ["CDMS_EMBED_BACKEND"] = "hash"

from cdms.config import Config  # noqa: E402
from cdms.embeddings import Embedder  # noqa: E402
from cdms.store import MemoryService  # noqa: E402


@pytest.fixture
def cfg(tmp_path) -> Config:
    return Config(home=tmp_path)


@pytest.fixture
def service(cfg) -> MemoryService:
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    yield svc
    svc.close()
