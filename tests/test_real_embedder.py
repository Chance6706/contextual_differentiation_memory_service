"""Non-hash CI path: exercises the REAL fastembed backend.

The rest of the suite forces CDMS_EMBED_BACKEND=hash, so it is structurally blind
to real-embedder behavior (the contamination/semantic-recall surfaces). These
tests run against the actual bge-small model and SKIP cleanly when it cannot be
loaded (offline CI / no model cache), so they harden coverage without making the
suite flaky.

Includes Gemini's "Echo Chamber" R2 test: verify semantic (vector) recall works
when the BM25 keyword arm scores zero (synonyms only), so the dreaming phase does
not hallucinate false epistemic gaps just because exact keywords are absent.
"""

from __future__ import annotations

import numpy as np
import pytest

from cdms.config import Config
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent


@pytest.fixture
def real_service(tmp_path, monkeypatch):
    monkeypatch.delenv("CDMS_EMBED_BACKEND", raising=False)  # un-force the hash backend
    cfg = Config(home=tmp_path)
    emb = Embedder(cfg)
    try:
        emb.embed_one("warmup")
    except Exception as exc:  # noqa: BLE001 - model unavailable / offline
        pytest.skip(f"real fastembed embedder unavailable: {exc!r}")
    if emb.backend != "fastembed":
        pytest.skip("fastembed backend not active")
    svc = MemoryService(cfg, embedder=emb)
    yield svc
    svc.close()


def test_semantic_recall_when_bm25_scores_zero(real_service):
    """Echo Chamber: recall a memory via vector similarity when no keywords match."""
    svc = real_service
    svc.ingest(TurnEvent(
        trigger_prompt="investigate the production incident",
        action_taken="analyzed the heap dump",
        outcome_feedback="the service crashed because it exhausted available memory (OOM)",
        project="ops", success=False))
    svc.ingest(TurnEvent(
        trigger_prompt="documentation chore",
        action_taken="wrote a guide about CSS flexbox layout",
        outcome_feedback="published", project="ops", success=True))

    # Semantically-related query with NO exact keyword overlap with the stored
    # incident (different vocabulary for the same "out of memory" event).
    query = "kubernetes pod evicted due to resource starvation"
    assert svc.db.fts("episodic", query, 8) == []  # BM25 arm is genuinely starved

    hits = svc.retrieve(query, top_k=3, tiers=("episodic",), reinforce=False)
    assert hits, "vector arm failed to recall a semantically-related memory"
    assert any(kw in hits[0].text.lower() for kw in ("memory", "oom", "crashed")), hits[0].text


def test_real_backend_pins_fingerprint_and_refuses_mixing(real_service):
    svc = real_service
    svc.ingest(TurnEvent(trigger_prompt="t", action_taken="a", outcome_feedback="o", project="p"))
    fp = svc.db.get_meta("embed_fingerprint")
    assert fp and fp.startswith("fastembed:")
    # The hash backend must be refused against a real-vector store (no contamination).
    with pytest.raises(RuntimeError, match="mismatch"):
        svc.db.reconcile_embedder("hash:BAAI/bge-small-en-v1.5:384")


def test_real_embeddings_are_unit_norm_and_finite(real_service):
    for text in ["a normal sentence", "", "   ", "!!!"]:
        v = real_service.embedder.embed_one(text)
        assert np.isfinite(v).all() and v.any()
        assert abs(float(np.linalg.norm(v)) - 1.0) < 1e-4
