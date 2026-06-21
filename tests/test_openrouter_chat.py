"""Hermetic tests for `tools.openrouter_chat`.

No live HTTP, no live API key required. We mock `urllib.request.urlopen` (the
single network seam in the adapter) and `time.sleep` (so rate-limit retry
tests are instant). The OPENROUTER_API_KEY env var is set via `monkeypatch`.

Coverage matches the 14 tests in the build spec for the methodology-reset
matrix prerequisite. Each test name calls out what it asserts.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

# Make `tools/` importable the same way the main matrix runner does.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from openrouter_chat import (  # noqa: E402
    OPENROUTER_REFERER,
    OPENROUTER_TITLE,
    PER_CALL_COST_ESTIMATE,
    OpenRouterAPIError,
    RateLimitDeferred,
    estimate_cost,
    openrouter_chat,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok_response(content: str = "ok", usage: dict | None = None) -> MagicMock:
    """Build a mock urlopen context-manager that yields a JSON body."""
    body = {"choices": [{"message": {"content": content}}]}
    if usage is not None:
        body["usage"] = usage
    raw = json.dumps(body).encode("utf-8")
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=raw)))
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _http_error(code: int) -> urllib.error.HTTPError:
    """Construct an HTTPError that's safe to raise from a urlopen mock."""
    return urllib.error.HTTPError(
        url="https://openrouter.ai/api/v1/chat/completions",
        code=code,
        msg=f"HTTP {code}",
        hdrs=None,  # type: ignore[arg-type]
        fp=BytesIO(b""),
    )


class _StubCostGuard:
    """Records calls so tests can assert ordering + arguments."""

    def __init__(self, raise_on_check: Exception | None = None):
        self.checks: list[float] = []
        self.records: list[float] = []
        self._raise = raise_on_check

    def check_can_call(self, estimated: float) -> None:
        self.checks.append(estimated)
        if self._raise is not None:
            raise self._raise

    def record(self, actual: float) -> None:
        self.records.append(actual)


# ---------------------------------------------------------------------------
# 1. API-key gating
# ---------------------------------------------------------------------------

def test_openrouter_chat_requires_api_key(tmp_path, monkeypatch):
    """No API key → OpenRouterAPIError before any HTTP attempt."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with patch("urllib.request.urlopen") as urlopen:
        with pytest.raises(OpenRouterAPIError, match="OPENROUTER_API_KEY"):
            openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                            "sys", "usr", tmp_path)
        assert urlopen.call_count == 0  # never reached the network


# ---------------------------------------------------------------------------
# 2. Caching
# ---------------------------------------------------------------------------

def test_openrouter_chat_caches_on_first_call(tmp_path, monkeypatch):
    """First call hits the API + writes cache; second call returns from cache
    without hitting the API."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("urllib.request.urlopen", return_value=_ok_response("the answer")) as urlopen:
        r1 = openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                             "sys", "usr", tmp_path)
        r2 = openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                             "sys", "usr", tmp_path)
    assert r1 == "the answer"
    assert r2 == "the answer"
    assert urlopen.call_count == 1
    # A cache file should exist.
    cached = list(tmp_path.glob("*.json"))
    assert len(cached) == 1
    payload = json.loads(cached[0].read_text(encoding="utf-8"))
    assert payload["response"] == "the answer"
    assert payload["model"] == "anthropic/claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# 3. Payload shape
# ---------------------------------------------------------------------------

def test_openrouter_chat_uses_openai_compatible_payload(tmp_path, monkeypatch):
    """Payload follows OpenAI Chat Completions schema (messages, temperature,
    max_tokens, stream)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("urllib.request.urlopen", return_value=_ok_response("ok")) as urlopen:
        openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                        "SYS", "USR", tmp_path, n_predict=99)
    req = urlopen.call_args[0][0]
    payload = json.loads(req.data.decode("utf-8"))
    assert payload["model"] == "anthropic/claude-haiku-4-5-20251001"
    assert payload["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USR"},
    ]
    assert payload["temperature"] == 0.0
    assert payload["max_tokens"] == 99
    assert payload["stream"] is False
    # Endpoint suffix
    assert req.full_url.endswith("/chat/completions")


# ---------------------------------------------------------------------------
# 4. Headers
# ---------------------------------------------------------------------------

def test_openrouter_chat_sends_required_headers(tmp_path, monkeypatch):
    """Authorization Bearer + HTTP-Referer + X-Title must all be sent."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-xyz")
    with patch("urllib.request.urlopen", return_value=_ok_response("ok")) as urlopen:
        openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                        "sys", "usr", tmp_path)
    req = urlopen.call_args[0][0]
    # urllib.request.Request lowercases header names internally.
    assert req.get_header("Authorization") == "Bearer test-key-xyz"
    assert req.get_header("Http-referer") == OPENROUTER_REFERER
    assert req.get_header("X-title") == OPENROUTER_TITLE
    assert req.get_header("Content-type") == "application/json"


# ---------------------------------------------------------------------------
# 5. Response extraction
# ---------------------------------------------------------------------------

def test_openrouter_chat_extracts_response_correctly(tmp_path, monkeypatch):
    """choices[0].message.content is what we return."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("urllib.request.urlopen",
               return_value=_ok_response("the precise extracted text")):
        out = openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                              "sys", "usr", tmp_path)
    assert out == "the precise extracted text"


# ---------------------------------------------------------------------------
# 6-9. Cost-guard interaction
# ---------------------------------------------------------------------------

def test_openrouter_chat_skips_cost_guard_on_cache_hit(tmp_path, monkeypatch):
    """A cache hit is FREE; the cost guard must NOT be touched. Otherwise we'd
    debit budget every re-run, defeating the point of caching paid calls."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    # Warm the cache (no cost guard yet).
    with patch("urllib.request.urlopen", return_value=_ok_response("warm")):
        openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                        "sys", "usr", tmp_path)
    guard = _StubCostGuard()
    with patch("urllib.request.urlopen") as urlopen:
        result = openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                                 "sys", "usr", tmp_path, cost_guard=guard)
    assert result == "warm"
    assert urlopen.call_count == 0
    assert guard.checks == []
    assert guard.records == []


def test_openrouter_chat_calls_cost_guard_before_request(tmp_path, monkeypatch):
    """check_can_call MUST run BEFORE urlopen, so a budget veto prevents spend."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    order: list[str] = []
    guard = MagicMock()
    guard.check_can_call.side_effect = lambda c: order.append("check")
    guard.record.side_effect = lambda c: order.append("record")

    def _urlopen_side_effect(*_args, **_kwargs):
        order.append("urlopen")
        return _ok_response("ok")

    with patch("urllib.request.urlopen", side_effect=_urlopen_side_effect):
        openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                        "sys", "usr", tmp_path, cost_guard=guard)
    assert order == ["check", "urlopen", "record"]
    guard.check_can_call.assert_called_once_with(
        PER_CALL_COST_ESTIMATE["anthropic/claude-haiku-4-5-20251001"])


def test_openrouter_chat_records_actual_cost_after_response(tmp_path, monkeypatch):
    """When no `usage.cost` in response, we record the estimate."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    guard = _StubCostGuard()
    with patch("urllib.request.urlopen", return_value=_ok_response("ok")):
        openrouter_chat("anthropic/claude-sonnet-4-6",
                        "sys", "usr", tmp_path, cost_guard=guard)
    assert guard.checks == [PER_CALL_COST_ESTIMATE["anthropic/claude-sonnet-4-6"]]
    # No usage.cost → falls back to estimate.
    assert guard.records == [PER_CALL_COST_ESTIMATE["anthropic/claude-sonnet-4-6"]]


def test_openrouter_chat_propagates_budget_exceeded(tmp_path, monkeypatch):
    """If the cost guard raises in check_can_call, we propagate AND don't call
    the API AND don't record anything."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    sentinel = RuntimeError("BUDGET_EXCEEDED")
    guard = _StubCostGuard(raise_on_check=sentinel)
    with patch("urllib.request.urlopen") as urlopen:
        with pytest.raises(RuntimeError, match="BUDGET_EXCEEDED"):
            openrouter_chat("anthropic/claude-opus-4-7",
                            "sys", "usr", tmp_path, cost_guard=guard)
    assert urlopen.call_count == 0
    assert guard.records == []  # never recorded — never spent


# ---------------------------------------------------------------------------
# 10-11. Rate-limit protocol
# ---------------------------------------------------------------------------

def test_openrouter_chat_rate_limit_retry_protocol(tmp_path, monkeypatch):
    """429 → wait → 429 → wait → 200 should return success after sleeping twice."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    sequence = [_http_error(429), _http_error(429), _ok_response("after retries")]

    def _urlopen(*_args, **_kwargs):
        nxt = sequence.pop(0)
        if isinstance(nxt, urllib.error.HTTPError):
            raise nxt
        return nxt

    with patch("urllib.request.urlopen", side_effect=_urlopen), \
         patch("time.sleep") as sleep:
        out = openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                              "sys", "usr", tmp_path,
                              rate_limit_wait_secs=0,
                              max_rate_limit_retries=2)
    assert out == "after retries"
    # Slept twice (once per 429).
    assert sleep.call_count == 2
    assert all(call.args[0] == 0 for call in sleep.call_args_list)


def test_openrouter_chat_rate_limit_defer_after_max_retries(tmp_path, monkeypatch):
    """429, 429, 429 with max_rate_limit_retries=2 → 3 attempts then RateLimitDeferred."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    errors = [_http_error(429), _http_error(429), _http_error(429)]

    def _urlopen(*_args, **_kwargs):
        raise errors.pop(0)

    with patch("urllib.request.urlopen", side_effect=_urlopen) as urlopen, \
         patch("time.sleep"):
        with pytest.raises(RateLimitDeferred):
            openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                            "sys", "usr", tmp_path,
                            rate_limit_wait_secs=0,
                            max_rate_limit_retries=2)
    # 1 initial + 2 retries = 3 attempts.
    assert urlopen.call_count == 3


# ---------------------------------------------------------------------------
# 12-13. estimate_cost defaults
# ---------------------------------------------------------------------------

def test_openrouter_chat_estimate_cost_uses_free_default_for_free_model():
    """Unknown model containing `:free` → default_free."""
    assert estimate_cost("meta-llama/llama-3.1-405b-instruct:free") == \
           PER_CALL_COST_ESTIMATE["default_free"]


def test_openrouter_chat_estimate_cost_uses_paid_default_for_unknown_paid_model():
    """Unknown model without `:free` → default_paid."""
    assert estimate_cost("some-unknown-org/some-unknown-paid-model") == \
           PER_CALL_COST_ESTIMATE["default_paid"]


# ---------------------------------------------------------------------------
# 14. usage.cost is preferred over estimate when present
# ---------------------------------------------------------------------------

def test_openrouter_chat_uses_response_usage_cost_when_available(tmp_path, monkeypatch):
    """When OpenRouter returns `usage.cost`, that's what we record (not the estimate)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    guard = _StubCostGuard()
    with patch("urllib.request.urlopen",
               return_value=_ok_response("ok", usage={"cost": 0.0123})):
        openrouter_chat("anthropic/claude-opus-4-7",
                        "sys", "usr", tmp_path, cost_guard=guard)
    # Pre-call check used the ESTIMATE.
    assert guard.checks == [PER_CALL_COST_ESTIMATE["anthropic/claude-opus-4-7"]]
    # Post-call record used the ACTUAL from usage.cost.
    assert guard.records == [0.0123]


# ---------------------------------------------------------------------------
# 15. Red-team: path-traversal-resistant cache filenames
# ---------------------------------------------------------------------------

def test_openrouter_chat_sanitizes_hostile_model_slug(tmp_path, monkeypatch):
    """A model slug with path separators / NULs / `..` MUST NOT escape the cache
    directory or create unexpected files outside `tmp_path`."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    hostile = "../../etc/passwd\x00\\evil"
    with patch("urllib.request.urlopen", return_value=_ok_response("ok")):
        openrouter_chat(hostile, "sys", "usr", tmp_path)
    # Exactly one cache file, inside tmp_path, with no traversal artifacts.
    files = list(tmp_path.rglob("*.json"))
    assert len(files) == 1
    assert files[0].parent.resolve() == tmp_path.resolve()
    # Sanitized token contains no slashes, backslashes, NULs, or dot-runs.
    name = files[0].name
    for bad in ("/", "\\", "\x00", "..", ":"):
        assert bad not in name, f"{bad!r} leaked into cache filename {name!r}"


# ---------------------------------------------------------------------------
# 16. Red-team: API-key header smuggling
# ---------------------------------------------------------------------------

def test_openrouter_chat_rejects_api_key_with_control_chars(tmp_path, monkeypatch):
    """CR/LF or other control chars in the API key would let an attacker inject
    HTTP headers via the Authorization line. We reject before constructing the
    request."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "good\r\nX-Evil: 1")
    with patch("urllib.request.urlopen") as urlopen:
        with pytest.raises(OpenRouterAPIError, match="control characters"):
            openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                            "sys", "usr", tmp_path)
        assert urlopen.call_count == 0


# ---------------------------------------------------------------------------
# 17. Red-team: malformed usage.cost doesn't crash the call after spend
# ---------------------------------------------------------------------------

def test_openrouter_chat_handles_malformed_usage_cost(tmp_path, monkeypatch):
    """If usage.cost is non-numeric (None / string / list), fall back to the
    estimate rather than raising AFTER the API has already been billed."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    guard = _StubCostGuard()
    with patch("urllib.request.urlopen",
               return_value=_ok_response("ok", usage={"cost": "free"})):
        openrouter_chat("anthropic/claude-opus-4-7",
                        "sys", "usr", tmp_path, cost_guard=guard)
    # Recorded the estimate, did NOT raise.
    assert guard.records == [PER_CALL_COST_ESTIMATE["anthropic/claude-opus-4-7"]]


# ---------------------------------------------------------------------------
# 18. Red-team: non-string response content surfaces as APIError, never cached
# ---------------------------------------------------------------------------

def test_openrouter_chat_rejects_non_string_content(tmp_path, monkeypatch):
    """`content: null` (refusal) or `content: [...]` (multipart) must raise
    OpenRouterAPIError and write NO cache file (silently caching `None` would
    be a debugging nightmare on the next run)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("urllib.request.urlopen", return_value=_ok_response(None)):  # type: ignore[arg-type]
        with pytest.raises(OpenRouterAPIError, match="not a string"):
            openrouter_chat("anthropic/claude-opus-4-7",
                            "sys", "usr", tmp_path)
    assert list(tmp_path.glob("*.json")) == []


# ---------------------------------------------------------------------------
# 19. Red-team: corrupted cache files are recovered, not propagated
# ---------------------------------------------------------------------------

def test_openrouter_chat_recovers_from_corrupted_cache(tmp_path, monkeypatch):
    """A truncated/garbage cache file (e.g. interrupted prior write) is treated
    as a miss; the matrix runner gets a fresh fetch instead of crashing."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    # Pre-seed a corrupt cache entry with the exact filename the next call will
    # look for.
    import hashlib as _h
    model = "anthropic/claude-haiku-4-5-20251001"
    key = _h.sha256(f"{model}\x00sys\x00usr".encode()).hexdigest()[:24]
    safe = model.replace("/", "_").replace(":", "_")
    # F2 fix: cache filenames now carry the openrouter__ backend tag to dodge
    # cross-backend collisions (same SHA256 formula as ollama/lmstudio).
    bad = tmp_path / f"openrouter__{safe}__{key}.json"
    bad.write_text("{this is not json", encoding="utf-8")

    with patch("urllib.request.urlopen", return_value=_ok_response("recovered")):
        out = openrouter_chat(model, "sys", "usr", tmp_path)
    assert out == "recovered"
    # The corrupted file was replaced (or removed-then-rewritten) with valid JSON.
    assert json.loads(bad.read_text(encoding="utf-8"))["response"] == "recovered"


# ---------------------------------------------------------------------------
# 20. Legitimate-use: non-429/5xx HTTP errors raise OpenRouterAPIError cleanly
# ---------------------------------------------------------------------------

def test_openrouter_chat_4xx_raises_api_error(tmp_path, monkeypatch):
    """401/403/404 are unrecoverable from inside the adapter and must surface as
    OpenRouterAPIError with the status code in the message."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def _urlopen(*_args, **_kwargs):
        raise _http_error(401)

    with patch("urllib.request.urlopen", side_effect=_urlopen):
        with pytest.raises(OpenRouterAPIError, match="401"):
            openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                            "sys", "usr", tmp_path)


# ---------------------------------------------------------------------------
# 21. Legitimate-use: 5xx single-retry policy is correct
# ---------------------------------------------------------------------------

def test_openrouter_chat_5xx_retries_once_then_succeeds(tmp_path, monkeypatch):
    """One 5xx → sleep 5s → retry → success."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    sequence = [_http_error(503), _ok_response("recovered")]

    def _urlopen(*_args, **_kwargs):
        nxt = sequence.pop(0)
        if isinstance(nxt, urllib.error.HTTPError):
            raise nxt
        return nxt

    with patch("urllib.request.urlopen", side_effect=_urlopen), \
         patch("time.sleep"):
        out = openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                              "sys", "usr", tmp_path)
    assert out == "recovered"


def test_openrouter_chat_5xx_persistent_raises_api_error(tmp_path, monkeypatch):
    """Two consecutive 5xx → retry exhausted → OpenRouterAPIError."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    errors = [_http_error(502), _http_error(502)]

    def _urlopen(*_args, **_kwargs):
        raise errors.pop(0)

    with patch("urllib.request.urlopen", side_effect=_urlopen), \
         patch("time.sleep"):
        with pytest.raises(OpenRouterAPIError, match="502"):
            openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                            "sys", "usr", tmp_path)


# ---------------------------------------------------------------------------
# 22. Legitimate-use: malformed JSON response surfaces as OpenRouterAPIError
# ---------------------------------------------------------------------------

def test_openrouter_chat_malformed_response_raises_api_error(tmp_path, monkeypatch):
    """A 200 with non-JSON or missing-fields body must NOT bubble up as a
    generic JSONDecodeError/KeyError — the matrix runner pattern-matches on
    OpenRouterAPIError to know it can skip the cell cleanly."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"not json at all")))
    cm.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=cm):
        with pytest.raises(OpenRouterAPIError, match="Malformed"):
            openrouter_chat("anthropic/claude-haiku-4-5-20251001",
                            "sys", "usr", tmp_path)
