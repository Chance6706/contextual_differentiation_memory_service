"""Regression tests for embedder-integrity defects found in red-team review.

Covers:
  C1 — no silent fastembed->hash degrade; vector-space fingerprint pin.
  C2 — degenerate (empty/punctuation) text must not produce a zero vector
       that returns NULL distance and crashes KNN.
  M7 — a dimension mismatch surfaces loudly instead of silent empty recall.
"""

from __future__ import annotations

import numpy as np
import pytest

from cdms.config import Config
from cdms.db import Database
from cdms.embeddings import Embedder, serialize_f32
from cdms.store import MemoryService, TurnEvent


# --- C2: zero-vector guard ------------------------------------------------- #
@pytest.mark.parametrize("text", ["", "   ", "\n\t ", "!!!", "...", "🙂🙂"])
def test_degenerate_text_yields_finite_unit_vector(cfg, text):
    v = Embedder(cfg).embed_one(text)
    assert v.shape == (cfg.embed_dim,)
    assert np.isfinite(v).all()
    assert v.any(), "degenerate text must not produce an all-zero vector"
    assert abs(float(np.linalg.norm(v)) - 1.0) < 1e-5


def test_knn_skips_null_distance_from_legacy_zero_vector(cfg):
    """A pre-existing zero vector (NULL distance) must not crash the tier."""
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        svc.ingest(TurnEvent(trigger_prompt="real turn", action_taken="bash: ls", outcome_feedback="ok"))
        # Inject a degenerate zero vector directly, bypassing the embedder guard.
        zero = serialize_f32(np.zeros(cfg.embed_dim, dtype=np.float32))
        with svc.db.tx() as c:
            c.execute("INSERT INTO vec_episodic(id, embedding) VALUES (?, ?)", ("ep_zerorow", zero))
        hits = svc.db.knn("episodic", Embedder(cfg).embed_one("real turn"), 5)
        assert all(isinstance(d, float) for _, d in hits)  # no float(None) crash
        assert "ep_zerorow" not in {i for i, _ in hits}     # NULL row skipped
    finally:
        svc.close()


# --- C1: fingerprint pin / no space mixing --------------------------------- #
def test_first_write_pins_fingerprint(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        assert svc.db.get_meta("embed_fingerprint") is None
        svc.ingest(TurnEvent(trigger_prompt="t", action_taken="a", outcome_feedback="o"))
        assert svc.db.get_meta("embed_fingerprint") == svc.embedder.fingerprint()
    finally:
        svc.close()


def test_mismatched_fingerprint_refused(cfg):
    db = Database(cfg)
    try:
        db.set_meta("embed_fingerprint", "fastembed:BAAI/bge-small-en-v1.5:384")
        with pytest.raises(RuntimeError, match="Embedding-space mismatch"):
            db.reconcile_embedder("hash:BAAI/bge-small-en-v1.5:384")
    finally:
        db.close()


def test_no_silent_hash_fallback_when_model_unavailable(cfg, monkeypatch):
    """A fastembed failure must raise, never silently write hash vectors."""
    monkeypatch.delenv("CDMS_EMBED_BACKEND", raising=False)
    import fastembed

    def _boom(*a, **k):
        raise RuntimeError("model download failed")

    monkeypatch.setattr(fastembed, "TextEmbedding", _boom)
    e = Embedder(cfg)
    with pytest.raises(RuntimeError, match="Refusing to silently degrade"):
        e.embed_one("hello")
    assert e._backend != "hash"  # did not silently pin the wrong backend


# --- M7: dimension mismatch is loud ---------------------------------------- #
def test_dimension_mismatch_raises_on_knn(tmp_path):
    Database(Config(home=tmp_path, embed_dim=384)).close()
    db = Database(Config(home=tmp_path, embed_dim=256))  # baked tables are still 384
    try:
        with pytest.raises(Exception):  # OperationalError: dimension mismatch, surfaced not swallowed
            db.knn("episodic", np.zeros(256, dtype=np.float32), 3)
    finally:
        db.close()
