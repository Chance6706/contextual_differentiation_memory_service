"""Hermetic tests for the LM Studio chat adapter (tools/lmstudio_chat.py).

These tests MUST NOT touch the network. urllib.request.urlopen is patched in every
test that would otherwise issue a real HTTP call. The matrix runner that wires these
backends together (tools/redteam_claude_md_interference.py) relies on lmstudio_chat
having the same signature + cache semantics as ollama_chat, so the assertions here
focus on:

  * cache key/path stability (mirrors ollama_chat key construction)
  * OpenAI-compatible payload shape (model, messages, temperature, max_tokens, stream)
  * choices[0].message.content extraction
  * url/timeout overrides reach urlopen
  * RuntimeError semantics on HTTP error and on connection refusal (clear messages
    so the runner can surface a useful failure)
"""
from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# tools/ is not a package; add it to sys.path so we can import the module directly
# (matches the pattern used by tests/test_redteam_claude_md_interference.py).
_TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from lmstudio_chat import (  # noqa: E402
    LMSTUDIO_TIMEOUT,
    LMSTUDIO_URL,
    lmstudio_chat,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _fake_response(content: str = "hello from lmstudio") -> MagicMock:
    """Build a context-manager mock that mimics urlopen's response object."""
    body = json.dumps({
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "model": "openai/gpt-oss-20b",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
    }).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_lmstudio_chat_caches_on_first_call(tmp_path: Path) -> None:
    """First call hits urlopen; second call (same model/system/user) hits cache only."""
    with patch("lmstudio_chat.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _fake_response("first-and-only-real-call")

        out1 = lmstudio_chat("m", "sys", "user", cache=tmp_path)
        out2 = lmstudio_chat("m", "sys", "user", cache=tmp_path)

        assert out1 == "first-and-only-real-call"
        assert out2 == "first-and-only-real-call"
        # urlopen called exactly once across both invocations — second was cache.
        assert mock_open.call_count == 1
        # Cache file exists and has the right shape.
        cache_files = list(tmp_path.glob("*.json"))
        assert len(cache_files) == 1
        cached = json.loads(cache_files[0].read_text(encoding="utf-8"))
        assert cached == {"model": "m", "response": "first-and-only-real-call"}


def test_lmstudio_chat_uses_openai_compatible_payload(tmp_path: Path) -> None:
    """Payload must match OpenAI chat-completions shape (the LM Studio API surface)."""
    with patch("lmstudio_chat.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _fake_response("ok")

        lmstudio_chat("openai/gpt-oss-20b", "the system",
                      "the user prompt", cache=tmp_path, n_predict=42)

        # urlopen receives a Request; pull the body off it.
        assert mock_open.call_count == 1
        req = mock_open.call_args.args[0]
        # Endpoint hits the OpenAI-compatible path.
        assert req.full_url.endswith("/v1/chat/completions"), req.full_url
        # Content type header.
        # urllib normalizes header names to title-case via add_header, so check both.
        headers = {k.lower(): v for k, v in req.header_items()}
        assert headers.get("content-type") == "application/json"
        # Body shape.
        body = json.loads(req.data.decode("utf-8"))
        assert body["model"] == "openai/gpt-oss-20b"
        assert body["temperature"] == 0.0
        assert body["max_tokens"] == 42
        assert body["stream"] is False
        assert body["messages"] == [
            {"role": "system", "content": "the system"},
            {"role": "user", "content": "the user prompt"},
        ]


def test_lmstudio_chat_extracts_response_from_choices(tmp_path: Path) -> None:
    """Extraction reads choices[0].message.content — and nothing else."""
    with patch("lmstudio_chat.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _fake_response("the response we want")

        out = lmstudio_chat("m", "s", "u", cache=tmp_path)

        assert out == "the response we want"


def test_lmstudio_chat_cache_key_distinguishes_model_and_prompts(tmp_path: Path) -> None:
    """Different model OR different system OR different user => different cache file."""
    responses = iter([
        _fake_response("resp-model-A"),
        _fake_response("resp-model-B"),
        _fake_response("resp-diff-system"),
        _fake_response("resp-diff-user"),
    ])
    with patch("lmstudio_chat.urllib.request.urlopen", side_effect=lambda *a, **kw: next(responses)):
        a = lmstudio_chat("model-A", "sys", "user", cache=tmp_path)
        b = lmstudio_chat("model-B", "sys", "user", cache=tmp_path)
        c = lmstudio_chat("model-A", "sys-DIFFERENT", "user", cache=tmp_path)
        d = lmstudio_chat("model-A", "sys", "user-DIFFERENT", cache=tmp_path)

    assert a == "resp-model-A"
    assert b == "resp-model-B"
    assert c == "resp-diff-system"
    assert d == "resp-diff-user"
    # Four distinct cache files written.
    assert len(list(tmp_path.glob("*.json"))) == 4

    # The safe_model substitution: "/" and ":" get replaced with "_".
    # Filename also carries the backend tag ("lmstudio__") to prevent cache
    # collision with Ollama files in a shared cache dir.
    with patch("lmstudio_chat.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _fake_response("safe-model-path")
        lmstudio_chat("vendor/family:tag", "sys", "user", cache=tmp_path)
    safe_named = list(tmp_path.glob("lmstudio__vendor_family_tag__*.json"))
    assert len(safe_named) == 1, (
        "filename must be lmstudio__{safe_model}__{key}.json with '/' and ':' "
        "replaced with '_' in safe_model"
    )


def test_lmstudio_chat_uses_url_override(tmp_path: Path) -> None:
    """Passing url=... overrides LMSTUDIO_URL for the request endpoint."""
    with patch("lmstudio_chat.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _fake_response("ok")

        lmstudio_chat("m", "s", "u", cache=tmp_path,
                      url="http://other-host:9999")

        req = mock_open.call_args.args[0]
        assert req.full_url == "http://other-host:9999/v1/chat/completions"
        # Sanity: default URL was NOT used.
        assert not req.full_url.startswith(LMSTUDIO_URL + "/")


def test_lmstudio_chat_uses_timeout_override(tmp_path: Path) -> None:
    """Passing timeout=... is forwarded to urlopen; None falls back to LMSTUDIO_TIMEOUT."""
    with patch("lmstudio_chat.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _fake_response("ok")

        lmstudio_chat("m", "s", "u", cache=tmp_path, timeout=12.5)

        # urlopen called with timeout=12.5 (kwarg) — ollama_chat uses kwarg form.
        _, kwargs = mock_open.call_args
        assert kwargs.get("timeout") == 12.5

    # Default path: timeout=None -> LMSTUDIO_TIMEOUT module constant.
    with patch("lmstudio_chat.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _fake_response("ok")

        lmstudio_chat("m", "s", "u2", cache=tmp_path)  # different user -> new cache key

        _, kwargs = mock_open.call_args
        assert kwargs.get("timeout") == LMSTUDIO_TIMEOUT


def test_lmstudio_chat_raises_on_http_error(tmp_path: Path) -> None:
    """HTTP 500 from the server raises RuntimeError naming the status."""
    err = urllib.error.HTTPError(
        url="http://localhost:1234/v1/chat/completions",
        code=500,
        msg="Internal Server Error",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(b"server exploded"),
    )
    with patch("lmstudio_chat.urllib.request.urlopen", side_effect=err):
        with pytest.raises(RuntimeError) as exc_info:
            lmstudio_chat("m", "s", "u", cache=tmp_path)

    msg = str(exc_info.value)
    assert "500" in msg
    assert "LM Studio" in msg
    # No cache file written when the request failed.
    assert list(tmp_path.glob("*.json")) == []


def test_lmstudio_chat_raises_on_connection_refused(tmp_path: Path) -> None:
    """URLError (e.g. connection refused) raises RuntimeError with a hint about
    the LM Studio server."""
    refused = urllib.error.URLError(ConnectionRefusedError(111, "Connection refused"))
    with patch("lmstudio_chat.urllib.request.urlopen", side_effect=refused):
        with pytest.raises(RuntimeError) as exc_info:
            lmstudio_chat("m", "s", "u", cache=tmp_path)

    msg = str(exc_info.value).lower()
    assert "lm studio" in msg
    # The hint must mention that the server might not be running so the matrix
    # runner can show an actionable error to the operator.
    assert "not be running" in msg or "not running" in msg
    # No cache file written when the request failed.
    assert list(tmp_path.glob("*.json")) == []


def test_lmstudio_chat_raises_on_invalid_json_body(tmp_path: Path) -> None:
    """Non-JSON HTTP body raises RuntimeError that echoes the raw payload."""
    resp = MagicMock()
    resp.read.return_value = b"<html>upstream proxy 502</html>"
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    with patch("lmstudio_chat.urllib.request.urlopen", return_value=resp):
        with pytest.raises(RuntimeError) as exc_info:
            lmstudio_chat("m", "s", "u", cache=tmp_path)

    msg = str(exc_info.value)
    assert "non-JSON" in msg
    assert "upstream proxy 502" in msg
    # No cache file written on failure.
    assert list(tmp_path.glob("*.json")) == []


def test_lmstudio_chat_raises_on_missing_choices(tmp_path: Path) -> None:
    """JSON-decoded but choices[0].message.content missing => RuntimeError."""
    body = json.dumps({"id": "x", "object": "chat.completion", "choices": []}).encode()
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    with patch("lmstudio_chat.urllib.request.urlopen", return_value=resp):
        with pytest.raises(RuntimeError) as exc_info:
            lmstudio_chat("m", "s", "u", cache=tmp_path)
    assert "choices[0].message.content" in str(exc_info.value)
    assert list(tmp_path.glob("*.json")) == []


def test_lmstudio_chat_normalizes_null_content_to_empty_string(tmp_path: Path) -> None:
    """`content: null` (OpenAI's "no content" shape) is returned as '', not None."""
    body = json.dumps({
        "choices": [{"index": 0, "message": {"role": "assistant", "content": None},
                     "finish_reason": "stop"}],
    }).encode()
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    with patch("lmstudio_chat.urllib.request.urlopen", return_value=resp):
        out = lmstudio_chat("m", "s", "u", cache=tmp_path)
    assert out == ""
    # Cached as ''.
    cache_files = list(tmp_path.glob("*.json"))
    assert len(cache_files) == 1
    assert json.loads(cache_files[0].read_text(encoding="utf-8"))["response"] == ""


def test_lmstudio_chat_raises_on_non_string_content(tmp_path: Path) -> None:
    """Non-string content (e.g. tool-call list) raises rather than silently caching."""
    body = json.dumps({
        "choices": [{"index": 0, "message": {
            "role": "assistant", "content": [{"type": "text", "text": "x"}],
        }, "finish_reason": "tool_calls"}],
    }).encode()
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    with patch("lmstudio_chat.urllib.request.urlopen", return_value=resp):
        with pytest.raises(RuntimeError) as exc_info:
            lmstudio_chat("m", "s", "u", cache=tmp_path)
    assert "non-string content" in str(exc_info.value)
    assert list(tmp_path.glob("*.json")) == []


def test_lmstudio_chat_creates_cache_dir_if_missing(tmp_path: Path) -> None:
    """A missing cache directory is created — caller doesn't have to mkdir first."""
    cache_dir = tmp_path / "deep" / "nested" / "cache"
    assert not cache_dir.exists()
    with patch("lmstudio_chat.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _fake_response("ok")
        out = lmstudio_chat("m", "s", "u", cache=cache_dir)
    assert out == "ok"
    assert cache_dir.is_dir()
    assert len(list(cache_dir.glob("*.json"))) == 1


def test_lmstudio_chat_raises_on_corrupt_cache_file(tmp_path: Path) -> None:
    """A partial-write cache file (e.g. process killed) surfaces as RuntimeError,
    not a leaked JSONDecodeError."""
    # Compute the filename the function would write for these prompts.
    import hashlib as _h
    key = _h.sha256(b"m\x00s\x00u").hexdigest()[:24]
    corrupt = tmp_path / f"lmstudio__m__{key}.json"
    corrupt.write_text('{"model": "m", "response":', encoding="utf-8")  # truncated

    with pytest.raises(RuntimeError) as exc_info:
        lmstudio_chat("m", "s", "u", cache=tmp_path)
    assert "corrupt" in str(exc_info.value).lower()


def test_lmstudio_chat_backend_tag_isolates_from_ollama_namespace(tmp_path: Path) -> None:
    """Cache files carry an 'lmstudio__' prefix so they cannot collide with
    Ollama cache files (which lack that prefix) in a shared cache directory.
    Crucial because the matrix runner is expected to dispatch both backends
    against the same on-disk cache during a T1/T2 sweep."""
    with patch("lmstudio_chat.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _fake_response("ok")
        lmstudio_chat("m", "s", "u", cache=tmp_path)
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    assert files[0].name.startswith("lmstudio__"), files[0].name
