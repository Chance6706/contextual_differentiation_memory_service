"""LM Studio chat adapter for the CLAUDE.md/SOUL.md interference matrix (T2 tier).

Mirrors the interface of `tools.redteam_claude_md_interference.ollama_chat` so the
matrix runner can dispatch to either backend with no changes to per-probe logic.

LM Studio exposes an OpenAI-compatible HTTP API on (by default) http://localhost:1234.
The payload shape, response shape, and endpoint path therefore differ from Ollama, but
the surrounding ergonomics (signature, cache key/path, error semantics) are deliberately
identical.

Defaults:
    LMSTUDIO_URL     = $CDMS_LMSTUDIO_URL     or http://localhost:1234
    LMSTUDIO_TIMEOUT = $CDMS_LMSTUDIO_TIMEOUT or 900.0 seconds

Tests live in `tests/test_lmstudio_chat.py` and are hermetic (no live HTTP — they
patch `urllib.request.urlopen`).
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

LMSTUDIO_URL = os.environ.get("CDMS_LMSTUDIO_URL", "http://localhost:1234")
LMSTUDIO_TIMEOUT = float(os.environ.get("CDMS_LMSTUDIO_TIMEOUT", "900"))

# Filename tag distinguishing LM Studio cache files from Ollama cache files in
# the same directory. Without this, an Ollama tag "vendor:tag" and an LM Studio
# id "vendor/tag" would both collapse to "vendor_tag" after the safe_model
# substitution AND share the same SHA256 prompt key — silently cross-contaminating
# the two backends (a same-prompt rerun against the other backend would hit the
# wrong response). See R3 in the lmstudio_chat double-pressure-test.
_BACKEND_TAG = "lmstudio"


def lmstudio_chat(model: str, system: str, user: str, cache: Path,
                  n_predict: int = 120, timeout: float | None = None,
                  url: str | None = None) -> str:
    """Send a system+user chat to an LM Studio backend (OpenAI-compatible API).

    Cached by SHA256 of (model, system, user). Signature mirrors `ollama_chat` so
    the matrix runner can swap backends without per-probe changes.

    Args:
        model:      LM Studio model identifier (e.g. "openai/gpt-oss-20b").
        system:     System prompt.
        user:       User turn.
        cache:      Directory for response cache files. Created if missing.
        n_predict:  Maps to OpenAI-compatible `max_tokens`. Default 120.
                    NOTE: n_predict is NOT part of the cache key (mirrors
                    ollama_chat). A rerun with a bumped n_predict will return
                    the cached truncated response — clear the cache when you
                    change n_predict.
        timeout:    Per-request timeout in seconds. Default LMSTUDIO_TIMEOUT.
        url:        Base URL override. Default LMSTUDIO_URL.

    Returns:
        The assistant's response text (choices[0].message.content). Always a
        `str`; an explicit-null content from the server is normalized to "".

    Raises:
        RuntimeError: on HTTP non-2xx, connection refused, JSON parse failure,
                      missing/non-string content, or corrupt cache file. The
                      message includes enough detail (status, body, hint) for
                      the matrix runner to surface a useful failure.

    Cache layout:
        `{cache}/{_BACKEND_TAG}__{safe_model}__{key24}.json` where
        `safe_model = model.replace('/', '_').replace(':', '_')` and `key24` is
        the first 24 hex chars of SHA256(model\\x00system\\x00user). The
        `lmstudio__` prefix prevents collision with Ollama cache files in a
        shared cache directory.
    """
    cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{model}\x00{system}\x00{user}".encode("utf-8")).hexdigest()[:24]
    safe_model = model.replace("/", "_").replace(":", "_")
    cp = cache / f"{_BACKEND_TAG}__{safe_model}__{key}.json"
    if cp.exists():
        try:
            cached = json.loads(cp.read_text(encoding="utf-8"))
            response = cached["response"]
        except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
            # Corrupt cache (e.g. partial write from a killed process). Surface
            # an actionable error instead of letting a JSONDecodeError leak out.
            raise RuntimeError(
                f"LM Studio cache file is corrupt: {cp}. "
                f"Delete it and re-run. ({type(e).__name__}: {e})"
            ) from e
        if not isinstance(response, str):
            raise RuntimeError(
                f"LM Studio cache file has non-string response: {cp}. "
                f"Got {type(response).__name__}. Delete it and re-run."
            )
        return response

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
        "max_tokens": n_predict,
        "stream": False,
    }
    endpoint = f"{url or LMSTUDIO_URL}/v1/chat/completions"
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout or LMSTUDIO_TIMEOUT) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        # HTTP 4xx/5xx: server responded with an error status.
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = "<unreadable body>"
        raise RuntimeError(
            f"LM Studio HTTP {e.code} from {endpoint}: {body}"
        ) from e
    except urllib.error.URLError as e:
        # Connection refused, DNS failure, etc. — server not reachable at all.
        raise RuntimeError(
            f"LM Studio request to {endpoint} failed: {e.reason!r}. "
            "Hint: LM Studio server may not be running, or CDMS_LMSTUDIO_URL is wrong. "
            "Start the server in LM Studio (Developer tab -> Start Server) and re-check."
        ) from e

    try:
        decoded = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        try:
            raw_text = raw.decode("utf-8", errors="replace")
        except Exception:
            raw_text = repr(raw)
        raise RuntimeError(
            f"LM Studio returned non-JSON response from {endpoint}: {raw_text!r}"
        ) from e

    try:
        out = decoded["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(
            f"LM Studio response from {endpoint} missing choices[0].message.content: "
            f"{decoded!r}"
        ) from e
    if out is None:
        # OpenAI-style "no content" (e.g. pure tool-call response). Normalize so
        # the caller always receives a str. Documented in the docstring.
        out = ""
    if not isinstance(out, str):
        # Defensive: tool-call shape would put a list/dict here; we don't ship
        # tool-use through the matrix and downstream scorers assume str.
        raise RuntimeError(
            f"LM Studio response from {endpoint} returned non-string content "
            f"(type={type(out).__name__}): {decoded!r}"
        )

    # Atomic cache write: write to a temp file in the same directory then
    # os.replace. Prevents a killed-mid-write process from leaving a partial
    # JSON file that the next call would JSONDecodeError on.
    tmp = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False,
        dir=str(cache), prefix=f".{cp.name}.", suffix=".tmp",
    )
    try:
        json.dump({"model": model, "response": out}, tmp)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        os.replace(tmp.name, cp)
    except Exception:
        try:
            tmp.close()
        except Exception:
            pass
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise
    return out
