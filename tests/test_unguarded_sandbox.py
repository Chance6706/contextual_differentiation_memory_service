"""Lock tests for the unguarded-drift mechanical guard (PLASTICITY_LADDER, task #16).

The standing rule these enforce: unguarded execution happens ONLY through the double-key-armed,
temp-minted, crash-safe-burned UnguardedSandbox — convention is not isolation.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest


def _keys(monkeypatch, eval_mode="1", unguarded="1", home=None):
    monkeypatch.setenv("CDMS_EVAL_MODE", eval_mode)
    monkeypatch.setenv("CDMS_UNGUARDED_DRIFT", unguarded)
    if home is None:
        monkeypatch.delenv("CDMS_HOME", raising=False)
    else:
        monkeypatch.setenv("CDMS_HOME", str(home))


class _StubSvc:
    """Reaches the arming asserts without a real store (they must fire FIRST)."""
    def __init__(self, home):
        self.cfg = type("C", (), {"home": Path(home)})()
    def close(self):
        pass


def test_sandbox_refuses_without_second_key(monkeypatch):
    from tools.eval_harness.unguarded_sandbox import UnguardedSandbox
    _keys(monkeypatch, unguarded="0")
    with pytest.raises(RuntimeError, match="CDMS_UNGUARDED_DRIFT"):
        UnguardedSandbox()


def test_sandbox_refuses_without_eval_key(monkeypatch):
    from tools.eval_harness.unguarded_sandbox import UnguardedSandbox
    _keys(monkeypatch, eval_mode="0")
    with pytest.raises(RuntimeError, match="CDMS_EVAL_MODE"):
        UnguardedSandbox()


def test_sandbox_refuses_ambient_real_home(monkeypatch, tmp_path):
    from tools.eval_harness.unguarded_sandbox import UnguardedSandbox
    _keys(monkeypatch, home=tmp_path / "real-store")  # ambient CDMS_HOME set -> refuse
    with pytest.raises(RuntimeError, match="ambient CDMS_HOME"):
        UnguardedSandbox()


def test_drift_refuses_home_outside_sandbox(monkeypatch, tmp_path):
    from tools.eval_harness.unguarded_sandbox import UnguardedSandbox, drift_gists
    _keys(monkeypatch)
    with UnguardedSandbox() as sb:
        svc = _StubSvc(tmp_path / "elsewhere")  # NOT under sb.base
        with pytest.raises(RuntimeError, match="OUTSIDE the sandbox"):
            drift_gists(sb, svc, np.ones(4), 0.5,
                        resistance=False, cap=False, touched_only=False)


def test_drift_refuses_disarmed_env(monkeypatch):
    from tools.eval_harness.unguarded_sandbox import UnguardedSandbox, drift_gists
    _keys(monkeypatch)
    with UnguardedSandbox() as sb:
        svc = _StubSvc(sb.home("h"))
        monkeypatch.setenv("CDMS_UNGUARDED_DRIFT", "0")  # disarm AFTER sandbox creation
        with pytest.raises(RuntimeError, match="not armed"):
            drift_gists(sb, svc, np.ones(4), 0.5,
                        resistance=False, cap=False, touched_only=False)


def test_burn_on_success_and_on_exception(monkeypatch):
    from tools.eval_harness.unguarded_sandbox import UnguardedSandbox
    _keys(monkeypatch)
    # success path
    with UnguardedSandbox() as sb:
        base = sb.base
        h = sb.home("a"); h.mkdir(parents=True)
        (h / "memory.db").write_text("x")
    assert not base.exists(), "burn-on-success failed"
    # exception path: base must STILL be burned, exception re-raised
    with pytest.raises(ValueError, match="boom"):
        with UnguardedSandbox() as sb2:
            base2 = sb2.base
            (sb2.home("b")).mkdir(parents=True)
            raise ValueError("boom")
    assert not base2.exists(), "burn-on-exception failed"


def test_burn_closes_services_first(monkeypatch):
    from tools.eval_harness.unguarded_sandbox import UnguardedSandbox
    _keys(monkeypatch)
    closed = []
    class Svc(_StubSvc):
        def close(self):
            closed.append(True)
    with UnguardedSandbox() as sb:
        sb.register(Svc(sb.home("h")))
    assert closed == [True], "service not closed before burn"


def test_product_code_never_imports_unguarded():
    """src/cdms must have zero reference to the unguarded module (quarantine reachability)."""
    src = Path(__file__).resolve().parents[1] / "src" / "cdms"
    hits = [p for p in src.rglob("*.py") if "unguarded" in p.read_text(encoding="utf-8", errors="ignore")]
    assert not hits, f"product code references unguarded module: {hits}"


def test_bounded_rung_matches_shipped_guardrail_shape():
    """R1 spec sanity: bounded rung keeps all three guards; R4 removes all three; drive fixed."""
    from tools.eval_harness.unguarded_sandbox import RUNGS
    assert RUNGS["R1"] == dict(alpha=0.6, resistance=True, cap=True, touched_only=True)
    assert RUNGS["R4"] == dict(alpha=0.6, resistance=False, cap=False, touched_only=False)
    assert RUNGS["R0"]["alpha"] == 0.0
    drives = {RUNGS[r]["alpha"] for r in ("R1", "R2", "R3", "R4")}
    assert drives == {0.6}, "dose ladder requires FIXED drive across drift rungs"
