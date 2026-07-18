"""Mechanically-guarded sandbox for the plasticity-ladder UNGUARDED drift ablation (task #16).

DELIBERATE DEVIATION (see docs/DEVIATIONS.md I11): `drift_gists` below can run with the product's
anti-poisoning / anti-confabulation plasticity guardrails REMOVED. That mode exists ONLY for the
sealed characterization experiment; it is unreachable from product code (nothing in src/cdms imports
this module) and refuses to run outside the double-key-armed, temp-minted, burned sandbox below.

STANDING RULE (Josh, 2026-07-17): unguarded execution — by the main session or ANY agent — goes only
through this module. Convention is not isolation; this is the mechanical guard.

Arming (ALL required, asserted inside the drift function — the single choke point):
  1. CDMS_EVAL_MODE=1                (the eval key)
  2. CDMS_UNGUARDED_DRIFT=1          (the explicit second key; nothing else in the repo sets it)
  3. the store home resolves INSIDE an UnguardedSandbox-minted temp base (a real CDMS_HOME,
     or any path outside the sandbox, is a hard error)
  4. the imported cdms is this worktree's src (provenance.assert_worktree_cdms)

Burn (crash-safe): UnguardedSandbox is a context manager owning ONE mkdtemp base; every store home
is minted under it. __exit__ closes every registered service THEN removes the whole base — on success
AND on exception (re-raised) — with a verified-gone check. An atexit backstop sweeps the base on
hard exit. SQLite WAL sidecars live under the homes, so base removal covers them; services are closed
first because Windows locks openly-held db files against rmtree.
"""
from __future__ import annotations

import atexit
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np

from tools.eval_harness.provenance import assert_worktree_cdms


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


class UnguardedSandbox:
    """Owns the temp base for unguarded runs; burns it, crash-safe."""

    def __init__(self):
        if os.environ.get("CDMS_EVAL_MODE") != "1":
            raise RuntimeError("UnguardedSandbox: CDMS_EVAL_MODE=1 required (key 1 of 2).")
        if os.environ.get("CDMS_UNGUARDED_DRIFT") != "1":
            raise RuntimeError("UnguardedSandbox: CDMS_UNGUARDED_DRIFT=1 required (key 2 of 2).")
        ambient = os.environ.get("CDMS_HOME")
        self.base = Path(tempfile.mkdtemp(prefix="unguarded-ladder-")).resolve()
        if ambient and not Path(ambient).resolve().is_relative_to(self.base):
            # never inherit an ambient (potentially real) home into an unguarded run
            shutil.rmtree(self.base, ignore_errors=True)
            raise RuntimeError(f"UnguardedSandbox: ambient CDMS_HOME is set ({ambient}); refuse.")
        self._services: list = []
        self._burned = False
        atexit.register(self._burn)  # hard-kill backstop

    def home(self, name: str) -> Path:
        """Mint a store home under the sandbox base."""
        h = (self.base / name).resolve()
        assert h.is_relative_to(self.base)
        return h

    def register(self, svc) -> None:
        """Register a MemoryService (or anything with .close()) for close-before-burn."""
        self._services.append(svc)

    def assert_inside(self, home: Path) -> None:
        h = Path(home).resolve()
        if not h.is_relative_to(self.base):
            raise RuntimeError(f"UnguardedSandbox: home {h} is OUTSIDE the sandbox base {self.base}.")

    def _burn(self) -> None:
        if self._burned:
            return
        for s in self._services:
            try:
                s.close()
            except Exception:
                pass
        self._services.clear()
        shutil.rmtree(self.base, ignore_errors=True)
        if self.base.exists():  # verified-gone: retry once after a beat (Windows lock lag)
            shutil.rmtree(self.base, ignore_errors=True)
        if self.base.exists():
            raise RuntimeError(f"BURN FAILED: {self.base} still exists — delete manually.")
        self._burned = True

    def __enter__(self) -> "UnguardedSandbox":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._burn()
        return False  # re-raise any exception


def drift_gists(sandbox: UnguardedSandbox, svc, attractor: np.ndarray, alpha: float, *,
                resistance: bool, cap: bool, touched_only: bool,
                touched_supports: dict | None = None,
                cap_step: float = 0.1) -> int:
    """The ladder drift step (post-consolidation). THE choke point — asserts arming every call.

    Bounded (R1) = resistance + cap + touched_only all True (the PT3-design guardrails).
    Fully unguarded (R4) = all False: every gist, full step alpha, no support resistance.
      resistance: per-gist effective step = alpha / sqrt(support)  (support-weighted plasticity)
      cap:        effective step clamped to <= cap_step
      touched_only: drift only gists whose support increased this window (touched_supports =
                    {gist_id: prev_support}; required when touched_only)
    """
    # --- arming (never skipped; a stub svc fails on the home assert before any db touch) ---
    if os.environ.get("CDMS_EVAL_MODE") != "1" or os.environ.get("CDMS_UNGUARDED_DRIFT") != "1":
        raise RuntimeError("drift_gists: not armed (CDMS_EVAL_MODE + CDMS_UNGUARDED_DRIFT required).")
    sandbox.assert_inside(Path(svc.cfg.home))
    assert_worktree_cdms()
    if alpha <= 0:
        return 0
    if touched_only and touched_supports is None:
        raise ValueError("touched_only requires touched_supports (prev support per gist id).")
    att = _unit(np.asarray(attractor, np.float64))
    n = 0
    for g in svc.db.all_gist():
        if touched_only and g.support_count <= touched_supports.get(g.id, 0):
            continue  # not reinforced this window
        c = svc.db.get_gist_centroid(g.id)
        if c is None:
            continue
        step = alpha
        if resistance:
            step = alpha / max(1.0, float(g.support_count)) ** 0.5
        if cap:
            step = min(step, cap_step)
        newc = _unit((1 - step) * np.asarray(c, np.float64) + step * att).astype(np.float32)
        emb = svc.embedder.embed_one(g.search_text())  # tuple unchanged; re-embed for insert API
        svc.db.insert_gist(g, emb, newc)
        n += 1
    return n


# The five ladder rungs (cumulative guardrail removal at FIXED drive alpha — a dose ladder,
# NOT per-guardrail attribution; see PLASTICITY_LADDER.md sec.2).
RUNGS = {
    "R0": dict(alpha=0.0, resistance=True, cap=True, touched_only=True),    # frozen
    "R1": dict(alpha=0.6, resistance=True, cap=True, touched_only=True),    # shipped-bounded
    "R2": dict(alpha=0.6, resistance=False, cap=True, touched_only=True),   # - support resistance
    "R3": dict(alpha=0.6, resistance=False, cap=False, touched_only=True),  # - magnitude cap
    "R4": dict(alpha=0.6, resistance=False, cap=False, touched_only=False), # - selectivity = unguarded
}
