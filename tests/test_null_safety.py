"""None-safety regression guards.

An adversarial None-safety sweep of the runtime surfaced two latent footguns (neither
reachable on the normal production path, both cheap to harden). These tests pin the
guards so a future change can't silently reintroduce the crash:

  1. Config.decay_tau must be TOTAL — never ZeroDivisionError — even for an absurd
     forgetting_shape that bypasses _validate (a directly-constructed Config).
  2. Hook payload handling must coerce non-object JSON to {} so the downstream
     payload.get(...) cannot AttributeError on a list/str/int.
"""

import io
import json

import pytest

from cdms.config import Config
from cdms.salience import accessibility


# --------------------------------------------------------------------------- #
# 1. decay_tau is total across the whole (even invalid) shape range
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("beta", [2.0, 1e3, 1e6, 1e15, 1e16, 1e18, 1e300])
def test_decay_tau_never_raises_and_is_finite(beta):
    # A Config built directly (bypassing _validate) can carry any beta. The denominator
    # 2^(1/beta)-1 underflows to 0.0 for beta >~ 1e16; decay_tau must fall back, not crash.
    cfg = Config(forgetting_shape=beta)
    tau = cfg.decay_tau
    import math
    assert math.isfinite(tau) and tau > 0.0


@pytest.mark.parametrize("beta", [1e16, 1e18, 1e300])
def test_accessibility_does_not_crash_for_extreme_shape(beta):
    # The eviction loop calls accessibility(); it must stay finite and still decay
    # (D(0)=1, D(large age) < 1), never raise, for an extreme unvalidated shape.
    cfg = Config(forgetting_shape=beta)
    import math
    d0 = accessibility(1.0, 0.0, 0, cfg)
    d_old = accessibility(1.0, 365.0, 0, cfg)
    assert math.isfinite(d0) and math.isfinite(d_old)
    assert d0 == pytest.approx(1.0)
    assert 0.0 <= d_old <= 1.0
    assert d_old < d0  # still a decaying curve, just degenerate parameters


def test_decay_tau_unchanged_in_valid_range():
    # The guard must not perturb the valid range: default beta=2 still gives tau ~ 70.01.
    assert Config().decay_tau == pytest.approx(70.0122, rel=1e-4)


# --------------------------------------------------------------------------- #
# 2. Hook payload handling coerces non-object JSON to {}
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("raw", ["[]", '"a string"', "5", "true", "null", "", "   ", "{not json", "[1,2,3]"])
def test_read_payload_always_returns_dict(monkeypatch, raw):
    from cdms import hooks
    monkeypatch.setattr("sys.stdin", io.StringIO(raw))
    out = hooks.read_payload()
    assert isinstance(out, dict)  # never a list/str/int/None, even for valid non-object JSON


def test_read_payload_passes_through_objects(monkeypatch):
    from cdms import hooks
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"hook_event_name": "Stop", "x": 1})))
    out = hooks.read_payload()
    assert out == {"hook_event_name": "Stop", "x": 1}


@pytest.mark.parametrize("payload", [[], "a string", 5, None, ["a", "b"]])
def test_dispatch_tolerates_non_dict_payload(tmp_path, payload):
    # dispatch did `payload.get("hook_event_name", ...)` on line 1 — an AttributeError on a
    # non-dict. With the coercion it must return a dict and never raise, regardless of payload.
    from cdms import hooks
    cfg = Config(home=tmp_path)
    out = hooks.dispatch("", payload, cfg=cfg)  # "" -> unknown event -> defensive {} return
    assert isinstance(out, dict)
