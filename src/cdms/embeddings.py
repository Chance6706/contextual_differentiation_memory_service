"""CPU-bound text embeddings (0 GPU VRAM, per design directive #4).

The embedder is the only place the service touches a neural model, and it does
so exclusively on the CPU via ONNX Runtime (through ``fastembed``). This keeps
the GPU entirely free for the primary reasoning model.

A deterministic hashing fallback is provided so the cognitive core, storage
layer, and tests remain runnable in environments where the ONNX model has not
been downloaded yet. The fallback is clearly inferior semantically but keeps the
plumbing exercisable offline.
"""

from __future__ import annotations

import hashlib
import os
import threading
from typing import Iterable, Sequence

import numpy as np

from .config import Config


class Embedder:
    """Lazy, thread-safe, CPU-only sentence embedder.

    Loads the ONNX model on first use so that fast hook subprocesses (which only
    spool raw text) never pay model-load cost. Falls back to a deterministic
    hashing embedding if ``fastembed`` is unavailable.
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.dim = cfg.embed_dim
        self._model = None
        self._backend = "uninitialized"
        self._lock = threading.Lock()

    # -- backend management --------------------------------------------------
    def _ensure_model(self) -> None:
        if self._model is not None or self._backend == "hash":
            return
        # Escape hatch for tests / offline CI: force the deterministic backend.
        if os.environ.get("CDMS_EMBED_BACKEND", "").lower() == "hash":
            self._backend = "hash"
            return
        with self._lock:
            if self._model is not None or self._backend == "hash":
                return
            try:
                from fastembed import TextEmbedding  # type: ignore

                self._model = TextEmbedding(model_name=self.cfg.embed_model)
                self._backend = "fastembed"
            except Exception as exc:
                # CRITICAL: do NOT silently fall back to the hash backend here.
                # A transient fastembed failure (model download hiccup, OOM,
                # import error) would otherwise write hash-space vectors into a
                # real bge-space store, permanently corrupting recall for those
                # rows with no detection or self-heal. Failing loudly means the
                # caller (hooks swallow it; CLI/doctor surface it) skips this
                # write and retries later instead of poisoning the store. The
                # only way to get the hash backend is to ask for it explicitly
                # via CDMS_EMBED_BACKEND=hash.
                self._backend = "uninitialized"  # allow a later retry
                raise RuntimeError(
                    f"fastembed model '{self.cfg.embed_model}' is unavailable "
                    f"({exc!r}). Refusing to silently degrade to the hash backend, "
                    f"which would corrupt this store's vector space. Ensure network/"
                    f"model access, or set CDMS_EMBED_BACKEND=hash to opt in to the "
                    f"deterministic offline embedder for the WHOLE life of this store."
                ) from exc

    @property
    def backend(self) -> str:
        self._ensure_model()
        return self._backend

    def fingerprint(self) -> str:
        """Stable identity of the vector space this embedder produces.

        Pinned in the store (``cdms_meta``) on first write and verified on every
        later open so a backend/model/dimension change cannot silently mix
        incompatible vector spaces in one database.

        For the real (fastembed) backend the library VERSION is part of the
        identity: a fastembed upgrade can change the model weights / onnx export
        under the same model name, which would otherwise silently mix two
        incompatible geometries in one store (the exact C1 corruption) with no
        detection. Pinning the version turns that into a loud, recoverable refuse.
        The deterministic hash backend has no such drift, so it is version-free.
        """
        if self.backend == "fastembed":
            return f"fastembed-{_fastembed_version()}:{self.cfg.embed_model}:{self.dim}"
        return f"{self.backend}:{self.cfg.embed_model}:{self.dim}"

    # -- embedding API -------------------------------------------------------
    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Return an (n, dim) float32 array of L2-normalized embeddings."""
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        # Truncate explicitly (both backends) so embedding is bounded and the cut
        # is intentional, not a hidden ~512-token model limit that silently drops
        # the salient tail and collides distinct long inputs onto one vector.
        cap = self.cfg.embed_max_chars
        texts = [(t or "")[:cap] for t in texts]
        # Degeneracy is decided at the TEXT level (no alphanumeric content) so the
        # guarantee holds on the REAL backend too: bge never emits a zero vector,
        # so the zero-row guard below only ever fires for the hash backend. Without
        # this, empty/whitespace/control/emoji inputs each got a distinct real
        # vector and collided pairwise (cos≈1), polluting novelty/dedup.
        degenerate = [i for i, t in enumerate(texts) if not _has_content(t)]
        self._ensure_model()
        if self._backend == "fastembed" and self._model is not None:
            vecs = np.asarray(list(self._model.embed(list(texts))), dtype=np.float32)
            if vecs.ndim != 2 or vecs.shape[1] != self.dim:
                # The model's output dim must match the dim baked into the vec0
                # tables / pinned in the fingerprint. A mismatch (misconfigured
                # embed_dim, or a model that changed dim) otherwise surfaces only
                # later as a cryptic sqlite-vec error — fail clearly, here.
                got = vecs.shape[1] if vecs.ndim == 2 else vecs.shape
                raise RuntimeError(
                    f"Embedder produced dim {got} but config embed_dim is {self.dim} "
                    f"(model '{self.cfg.embed_model}'). Fix embed_dim to match the model, "
                    f"or rebuild the store."
                )
        else:
            vecs = np.stack([self._hash_embed(t) for t in texts]).astype(np.float32)
        vecs = _l2_normalize(vecs)
        # Map degenerate inputs AND any all-zero row (legacy / hash) to one stable
        # unit sentinel. A stored zero vector returns distance=NULL from sqlite-vec,
        # which sorts AHEAD of real matches and crashes the KNN consumer
        # (float(None)); a single canonical sentinel embeds harmlessly instead.
        zero_rows = ~vecs.any(axis=1)
        if degenerate:
            zero_rows[degenerate] = True
        if zero_rows.any():
            vecs[zero_rows] = 0.0
            vecs[zero_rows, 0] = 1.0
        return vecs

    def embed_one(self, text: str) -> np.ndarray:
        """Return a single (dim,) float32 normalized embedding."""
        return self.embed([text])[0]

    # -- deterministic fallback ---------------------------------------------
    def _hash_embed(self, text: str) -> np.ndarray:
        """Cheap, deterministic bag-of-token-hashes embedding.

        Not semantically strong, but stable and dependency-free: identical text
        maps to identical vectors and shares dimensionality with the real model,
        so the storage/retrieval plumbing behaves consistently in tests.
        """
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = _tokenize(text)
        if not tokens:
            return vec
        for tok in tokens:
            h = hashlib.blake2b(tok.encode("utf-8"), digest_size=8).digest()
            idx = int.from_bytes(h[:4], "little") % self.dim
            sign = 1.0 if h[4] & 1 else -1.0
            vec[idx] += sign
        return vec


def serialize_f32(vec: np.ndarray | Sequence[float]) -> bytes:
    """Pack a vector into raw little-endian float32 bytes for sqlite-vec.

    Mirrors ``sqlite_vec.serialize_float32`` but avoids importing it where only
    serialization is needed.
    """
    arr = np.asarray(vec, dtype="<f4")
    return arr.tobytes()


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors."""
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return (mat / norms).astype(np.float32)


def _tokenize(text: str) -> list[str]:
    return [t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if t]


def _has_content(text: str) -> bool:
    """True if the text carries any alphanumeric signal worth embedding.

    Empty / whitespace / punctuation / emoji-only text is "degenerate" and maps to
    a single canonical sentinel vector. CJK and accented letters ARE alphanumeric
    (``str.isalnum`` is unicode-aware), so real non-Latin content is never nuked.
    """
    return any(c.isalnum() for c in (text or ""))


def _fastembed_version() -> str:
    try:
        from importlib.metadata import version

        return version("fastembed")
    except Exception:  # pragma: no cover - metadata always present when fastembed loads
        return "unknown"


# A process-wide singleton keeps the (heavy) ONNX session resident across calls
# inside the long-lived daemon, while short hook subprocesses simply never build it.
_SINGLETON: Embedder | None = None


def get_embedder(cfg: Config) -> Embedder:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = Embedder(cfg)
    return _SINGLETON
