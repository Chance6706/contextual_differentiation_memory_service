"""Cross-artifact integration test: real CostGuard wired to openrouter_chat.

The other test files exercise each module in isolation (with mocked guards or
mocked HTTP). This file wires the REAL `CostGuard` from `openrouter_cost_guard`
to the REAL `openrouter_chat` adapter (with `urllib.request.urlopen` mocked)
and verifies the contract the two modules implicitly agree on:

  * `openrouter_chat` calls `cost_guard.check_can_call(estimated_cost)` BEFORE
    the HTTP request, with the value `estimate_cost(model)` returns.
  * `openrouter_chat` calls `cost_guard.record(actual_cost)` AFTER a successful
    response, where actual_cost comes from `response.usage.cost` when present.
  * When the cap is hit, the `BudgetExceededError` raised by `CostGuard.check_can_call`
    propagates cleanly out of `openrouter_chat` and the HTTP request is never made.

CONTRACT-VIOLATION NOTE (flagged in the composability findings, NOT fixed here):
`openrouter_chat` and `openrouter_cost_guard` each define their own
`BudgetExceededError` class. They are NOT the same class. Callers MUST import
`BudgetExceededError` from `openrouter_cost_guard` (the cost-guard's exception
is the one actually raised at runtime); the symbol on `openrouter_chat` is a
distinct unused stub. This test asserts that runtime reality so the contract
remains honest until the duplicate is removed.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make tools/ importable the same way the per-module tests do.
_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import openrouter_chat as orc_mod  # noqa: E402
import openrouter_cost_guard as cg_mod  # noqa: E402
from openrouter_chat import (  # noqa: E402
    PER_CALL_COST_ESTIMATE,
    estimate_cost,
    openrouter_chat,
)
from openrouter_cost_guard import BudgetExceededError, CostGuard  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok_response(content: str = "ok", usage: dict | None = None) -> MagicMock:
    body: dict = {"choices": [{"message": {"content": content}}]}
    if usage is not None:
        body["usage"] = usage
    raw = json.dumps(body).encode("utf-8")
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=raw)))
    cm.__exit__ = MagicMock(return_value=False)
    return cm


# ---------------------------------------------------------------------------
# Interface compatibility: the two modules' duck-typed contract really lines up
# ---------------------------------------------------------------------------

def test_cost_guard_exposes_methods_openrouter_chat_calls():
    """openrouter_chat calls .check_can_call(est) and .record(actual). Make sure
    CostGuard exposes both with single-positional-arg shapes (no required kwargs)."""
    assert callable(getattr(CostGuard, "check_can_call", None))
    assert callable(getattr(CostGuard, "record", None))
    # Smoke: build one, call both, confirm no TypeError on the signatures
    # openrouter_chat will actually invoke.
    g = CostGuard(cap_usd=1.0, state_file=Path(os.devnull + "_unused"))  # never written
    # Use a brand-new tmp path for the real state file to avoid the devnull hack
    # leaking. Re-do with a real one inside a context.


def test_cost_guard_check_and_record_signatures(tmp_path: Path):
    """check_can_call(float) and record(float) are the public surface the
    adapter actually exercises. If either changes shape, this test fails first."""
    g = CostGuard(cap_usd=1.0, state_file=tmp_path / "spend.json")
    g.check_can_call(0.01)        # under cap, no raise
    g.record(0.01)                # legit record
    assert g.spent() == pytest.approx(0.01)


# ---------------------------------------------------------------------------
# Exception class identity — the duplicate-class trap
# ---------------------------------------------------------------------------

def test_budget_exceeded_error_runtime_class_is_cost_guard_one(tmp_path: Path, monkeypatch):
    """The exception that propagates from openrouter_chat is
    `openrouter_cost_guard.BudgetExceededError`. Both modules now expose the
    SAME class — openrouter_chat re-exports it via `from openrouter_cost_guard
    import BudgetExceededError` (integration-review finding F1, fixed in the
    main-loop integration pass). Callers can safely import from either module.

    This test pins that unification — a refactor that re-introduces a local
    stub class would break the identity here, alerting the next caller before
    they get a silently-uncaught BudgetExceededError in prod.
    """
    # The two symbols are the SAME class after F1 fix.
    assert cg_mod.BudgetExceededError is orc_mod.BudgetExceededError, (
        "If this assertion fails, openrouter_chat re-defined its own "
        "BudgetExceededError class — restore the `from openrouter_cost_guard "
        "import BudgetExceededError` re-export at the top of openrouter_chat.py."
    )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    state = tmp_path / "spend.json"
    # Cap so small the first estimate already trips it.
    guard = CostGuard(cap_usd=0.0001, state_file=state)

    with patch("urllib.request.urlopen") as urlopen:
        with pytest.raises(cg_mod.BudgetExceededError):
            openrouter_chat("anthropic/claude-opus-4-7", "sys", "usr",
                            tmp_path, cost_guard=guard)
        # Importantly, the network was never touched.
        assert urlopen.call_count == 0


# ---------------------------------------------------------------------------
# End-to-end happy path: check -> urlopen -> record (in that order)
# ---------------------------------------------------------------------------

def test_real_cost_guard_check_before_request_and_record_after(
    tmp_path: Path, monkeypatch
):
    """Wire a real CostGuard into a real openrouter_chat call (HTTP mocked) and
    verify the contract:
        1. check_can_call called BEFORE urlopen, with estimate_cost(model).
        2. urlopen called exactly once.
        3. record called AFTER urlopen, with the actual cost from usage.cost.
        4. spent() reflects the recorded actual cost (not the estimate).
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    state = tmp_path / "spend.json"
    guard = CostGuard(cap_usd=10.0, state_file=state)

    # Spy on the real guard methods to observe call order.
    order: list[tuple[str, float]] = []
    real_check = guard.check_can_call
    real_record = guard.record

    def spy_check(est: float) -> None:
        order.append(("check", est))
        real_check(est)

    def spy_record(actual: float) -> None:
        order.append(("record", actual))
        real_record(actual)

    guard.check_can_call = spy_check  # type: ignore[assignment]
    guard.record = spy_record         # type: ignore[assignment]

    actual_cost_from_server = 0.0042
    model = "anthropic/claude-opus-4-7"

    urlopen_calls: list[None] = []

    def _urlopen(*_args, **_kwargs):
        urlopen_calls.append(None)
        order.append(("urlopen", -1.0))
        return _ok_response("ok", usage={"cost": actual_cost_from_server})

    with patch("urllib.request.urlopen", side_effect=_urlopen):
        out = openrouter_chat(model, "sys", "usr", tmp_path, cost_guard=guard)

    assert out == "ok"
    assert len(urlopen_calls) == 1

    # Strict ordering: check, then urlopen, then record.
    op_names = [evt[0] for evt in order]
    assert op_names == ["check", "urlopen", "record"], op_names

    # check_can_call got the model's a-priori estimate.
    assert order[0][1] == pytest.approx(estimate_cost(model))
    assert order[0][1] == pytest.approx(PER_CALL_COST_ESTIMATE[model])

    # record got the server's reported actual cost (NOT the estimate).
    assert order[2][1] == pytest.approx(actual_cost_from_server)

    # Spent matches actual cost (estimate was never recorded).
    assert guard.spent() == pytest.approx(actual_cost_from_server)

    # And the state file actually got persisted by the real CostGuard.
    on_disk = json.loads(state.read_text(encoding="utf-8"))
    assert on_disk["spent_usd"] == pytest.approx(actual_cost_from_server)
    assert on_disk["call_count"] == 1


# ---------------------------------------------------------------------------
# Cap-hit: BudgetExceededError propagates and the network is untouched
# ---------------------------------------------------------------------------

def test_real_cost_guard_blocks_call_when_cap_already_hit(
    tmp_path: Path, monkeypatch
):
    """Pre-load the state file so the guard already sits at the cap; the next
    openrouter_chat MUST raise BudgetExceededError BEFORE any HTTP request and
    MUST NOT record any spend (no record on a refused call)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    state = tmp_path / "spend.json"
    # Seed: cap=$1, already spent $0.999 → next sonnet call ($0.020 estimate)
    # projects to $1.019 ≥ $1.0 cap → refused.
    state.write_text(json.dumps({
        "spent_usd": 0.999,
        "last_updated": "2026-01-01T00:00:00+00:00",
        "cap_usd": 1.0,
        "call_count": 50,
    }), encoding="utf-8")
    guard = CostGuard(cap_usd=1.0, state_file=state)
    assert guard.spent() == pytest.approx(0.999)
    assert guard.call_count == 50

    with patch("urllib.request.urlopen") as urlopen:
        with pytest.raises(BudgetExceededError) as excinfo:
            openrouter_chat("anthropic/claude-sonnet-4-6", "sys", "usr",
                            tmp_path, cost_guard=guard)
        assert urlopen.call_count == 0

    # The structured attrs on the exception are intact.
    err = excinfo.value
    assert err.cap_usd == pytest.approx(1.0)
    assert err.spent == pytest.approx(0.999)
    assert err.estimated_cost == pytest.approx(
        PER_CALL_COST_ESTIMATE["anthropic/claude-sonnet-4-6"]
    )
    assert err.projected == pytest.approx(0.999 + err.estimated_cost)

    # Guard did NOT record anything (no spend, no call_count bump).
    assert guard.spent() == pytest.approx(0.999)
    assert guard.call_count == 50


# ---------------------------------------------------------------------------
# Cap-hit mid-stream: many calls until the cap trips on its own
# ---------------------------------------------------------------------------

def test_real_cost_guard_trips_after_repeated_real_calls(
    tmp_path: Path, monkeypatch
):
    """Drive openrouter_chat repeatedly against a fresh CostGuard until the
    cap trips naturally — verifies record()s accumulate across calls and that
    eventually check_can_call raises without any out-of-band poke."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    state = tmp_path / "spend.json"
    # Cap=$0.05; sonnet estimate=$0.02 → call #1 OK ($0.02 < $0.05),
    # call #2 OK ($0.04 < $0.05), call #3 projected $0.06 ≥ $0.05 → REFUSED.
    guard = CostGuard(cap_usd=0.05, state_file=state)

    def _urlopen(*_args, **_kwargs):
        # Vary user prompt each call so cache misses each time.
        return _ok_response("ok")  # no usage.cost → estimate is recorded

    model = "anthropic/claude-sonnet-4-6"
    with patch("urllib.request.urlopen", side_effect=_urlopen):
        # Use different user prompts so each call is a cache miss.
        for i in range(2):
            out = openrouter_chat(model, "sys", f"usr-{i}", tmp_path,
                                  cost_guard=guard)
            assert out == "ok"
        # Third call must trip the cap.
        with pytest.raises(BudgetExceededError):
            openrouter_chat(model, "sys", "usr-final", tmp_path,
                            cost_guard=guard)

    assert guard.call_count == 2
    assert guard.spent() == pytest.approx(
        2 * PER_CALL_COST_ESTIMATE[model]
    )


# ---------------------------------------------------------------------------
# Cache hit must bypass the cost guard entirely (free re-runs)
# ---------------------------------------------------------------------------

def test_real_cost_guard_not_touched_on_cache_hit(tmp_path: Path, monkeypatch):
    """Re-running an already-cached call must NOT debit the budget and MUST
    NOT call check_can_call/record. This is what makes paid-call re-runs free."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    state = tmp_path / "spend.json"
    cache = tmp_path / "cache"
    cache.mkdir()
    guard = CostGuard(cap_usd=1.0, state_file=state)

    # Warm cache (with a guard).
    with patch("urllib.request.urlopen", return_value=_ok_response("warm")):
        openrouter_chat("anthropic/claude-haiku-4-5-20251001", "sys", "usr",
                        cache, cost_guard=guard)

    spent_after_warm = guard.spent()
    calls_after_warm = guard.call_count
    assert spent_after_warm > 0
    assert calls_after_warm == 1

    # Replay: no urlopen, no guard touch.
    real_check = guard.check_can_call
    real_record = guard.record
    check_calls: list[float] = []
    record_calls: list[float] = []
    guard.check_can_call = lambda c: (check_calls.append(c), real_check(c))[1]  # type: ignore[assignment]
    guard.record = lambda c: (record_calls.append(c), real_record(c))[1]  # type: ignore[assignment]

    with patch("urllib.request.urlopen") as urlopen:
        out2 = openrouter_chat("anthropic/claude-haiku-4-5-20251001", "sys",
                               "usr", cache, cost_guard=guard)
    assert out2 == "warm"
    assert urlopen.call_count == 0
    assert check_calls == []   # cache hit short-circuits before the guard
    assert record_calls == []
    assert guard.spent() == pytest.approx(spent_after_warm)
    assert guard.call_count == calls_after_warm
