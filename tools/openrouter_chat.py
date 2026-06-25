"""OpenRouter chat adapter for the CDMS methodology-reset matrix (tier T3/T4).

Mirrors the interface of `tools.redteam_claude_md_interference.ollama_chat` so the
matrix runner can swap backends interchangeably. Adds three things the local-only
adapter doesn't need:

* **API key gating.** OPENROUTER_API_KEY env var; missing key raises
  OpenRouterAPIError BEFORE any HTTP call.
* **Cost-guard hook.** Optional `cost_guard` object with
  `check_can_call(estimated_cost)` (may raise) and `record(actual_cost)`. We
  check BEFORE the request and record AFTER. Cache hits skip the cost guard
  entirely (no spend, no record).
* **Rate-limit deferral.** HTTP 429 → sleep + retry up to
  `max_rate_limit_retries`; on exhaustion raise `RateLimitDeferred` so the
  matrix runner can resume the cell later instead of losing progress.

Pre-registered as part of the multi-tier matrix in
`docs/validation/claude_md_interference/PRE_REGISTRATION.md`. The cost guard
itself lives in a sibling module (`tools/openrouter_cost_guard.py`); this
adapter only consumes its public interface.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

# Allowed characters in the on-disk model token. We sanitize aggressively because
# `model` flows into a filename — anything outside [A-Za-z0-9._-] gets collapsed
# to "_" so a hostile model slug ("../../etc/passwd", "\x00", "..\\evil") cannot
# escape the cache directory. The (model, system, user) SHA256 is still part of
# the filename, so the sanitized model token is only for human-readability —
# collisions in the sanitized token never produce wrong responses.
_SAFE_MODEL_RE = re.compile(r"[^A-Za-z0-9._-]+")

# --- Module-level constants (env-overridable) ---------------------------------

OPENROUTER_URL = os.environ.get("CDMS_OPENROUTER_URL", "https://openrouter.ai/api/v1")
OPENROUTER_TIMEOUT = float(os.environ.get("CDMS_OPENROUTER_TIMEOUT", "300"))
OPENROUTER_REFERER = "https://github.com/Chance6706/contextual_differentiation_memory_service"
OPENROUTER_TITLE = "CDMS methodology-reset matrix"

# Cache filename prefix to dodge cross-backend collisions when the runner
# points multiple backends at the same cache dir. ollama_chat and lmstudio_chat
# use identical SHA256 key formulas; without a backend tag, a same-prompt rerun
# against a different backend could silently return the wrong-backend response.
# lmstudio_chat already uses "lmstudio__"; we mirror with "openrouter__".
# Integration-review finding F2.
_BACKEND_TAG = "openrouter"


# --- Exceptions ---------------------------------------------------------------

class RateLimitDeferred(Exception):
    """Raised when OpenRouter rate-limits us past `max_rate_limit_retries`.

    Signals the matrix runner to checkpoint and resume the cell later, rather
    than losing in-flight progress. Distinct from OpenRouterAPIError because
    it's recoverable on retry.
    """


# Re-export the canonical BudgetExceededError from the cost guard module so
# callers importing from openrouter_chat catch the SAME class the cost guard
# raises. Integration-review finding F1 caught a prior local stub that
# silently shadowed the cost-guard exception — `except openrouter_chat.BudgetExceededError`
# would fail to catch a real cap breach. The re-export fixes that without
# changing the runtime contract (cost guard is still where the exception lives).
from openrouter_cost_guard import BudgetExceededError  # noqa: F401,E402


class OpenRouterAPIError(RuntimeError):
    """Non-recoverable API failure (missing key, 4xx other than 429, exhausted
    5xx retries, malformed response)."""


# --- Cost estimates -----------------------------------------------------------

# Conservative per-call cost estimates (USD). Used by the cost guard for
# pre-call budget checking. Actual cost is read from `usage.cost` in the
# response when available; these are only the a-priori estimate.
PER_CALL_COST_ESTIMATE = {
    "anthropic/claude-sonnet-4-6": 0.020,
    "anthropic/claude-opus-4-7": 0.060,
    "anthropic/claude-haiku-4-5-20251001": 0.005,
    "default_free": 0.005,
    "default_paid": 0.020,
}


def estimate_cost(model: str) -> float:
    """Per-call USD estimate for `model`.

    Exact match in PER_CALL_COST_ESTIMATE wins; otherwise OpenRouter's `:free`
    convention picks the free default, anything else gets the paid default.
    """
    if model in PER_CALL_COST_ESTIMATE:
        return PER_CALL_COST_ESTIMATE[model]
    if ":free" in model:
        return PER_CALL_COST_ESTIMATE["default_free"]
    return PER_CALL_COST_ESTIMATE["default_paid"]


# --- Main adapter -------------------------------------------------------------

def openrouter_chat(model: str, system: str, user: str, cache: Path,
                    n_predict: int = 120, timeout: float | None = None,
                    url: str | None = None, cost_guard=None,
                    rate_limit_wait_secs: int = 600,
                    max_rate_limit_retries: int = 2) -> str:
    """Send a system+user chat to OpenRouter. Cached by SHA256 of (model, system+user).

    Mirrors `ollama_chat`'s signature + cache format so the matrix runner can
    treat the two backends as drop-in replacements.

    Args:
        model: OpenRouter model slug (e.g. "anthropic/claude-sonnet-4-6").
        system: System prompt.
        user: User prompt.
        cache: Directory for cache files (created upstream).
        n_predict: Max completion tokens.
        timeout: HTTP timeout in seconds (default OPENROUTER_TIMEOUT).
        url: Override base URL (default OPENROUTER_URL).
        cost_guard: Optional object with `check_can_call(est)` + `record(actual)`.
        rate_limit_wait_secs: Seconds to sleep on each 429 before retry.
        max_rate_limit_retries: How many 429 retries before raising
            RateLimitDeferred. The total attempts = 1 + max_rate_limit_retries.

    Returns:
        The model's response string.

    Raises:
        OpenRouterAPIError: No API key, exhausted 5xx retries, malformed response.
        RateLimitDeferred: Exhausted 429 retries; resume the cell later.
        BudgetExceededError: Re-raised from the cost guard.
    """
    # Cache key matches ollama_chat exactly so swapping backends keeps cache files
    # deterministically separable (different filenames per (model, prompt)).
    # SECURITY: `safe_model` is regex-sanitized (not just two `.replace`s) so a
    # hostile model slug containing path separators, NULs, or shell metachars
    # cannot escape `cache` or collide ambiguously with disk artifacts. The
    # SHA256 still pins the file to (model, system, user) — sanitization is a
    # defensive belt over the cryptographic suspenders.
    key = hashlib.sha256(f"{model}\x00{system}\x00{user}".encode("utf-8")).hexdigest()[:24]
    safe_model = _SAFE_MODEL_RE.sub("_", model).strip("._-") or "model"
    cp = cache / f"{_BACKEND_TAG}__{safe_model}__{key}.json"
    if cp.exists():
        # Cache hit: no API call, no spend, no cost-guard interaction. The
        # whole point of caching paid calls is the second run costs $0.
        # A corrupted/truncated cache file is treated as a miss (deleted) so we
        # don't blow up the matrix runner on a single bad entry — re-fetching
        # is cheap relative to losing the run.
        try:
            return json.loads(cp.read_text(encoding="utf-8"))["response"]
        except (json.JSONDecodeError, KeyError, OSError):
            try:
                cp.unlink()
            except OSError:
                pass  # fall through to re-fetch; next write will overwrite

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterAPIError(
            "OPENROUTER_API_KEY environment variable not set; cannot call OpenRouter.")
    # Reject control chars / whitespace in the API key BEFORE constructing the
    # Authorization header — defends against header smuggling via CR/LF in an
    # env var, and surfaces a clean error instead of urllib's opaque ValueError.
    if any(c.isspace() or ord(c) < 0x20 or ord(c) == 0x7F for c in api_key):
        raise OpenRouterAPIError(
            "OPENROUTER_API_KEY contains whitespace or control characters; refusing to send.")

    # Pre-call cost-guard check. Either it returns (we're cleared to spend) or
    # it raises (its own BudgetExceededError or whatever it wants — we propagate).
    if cost_guard is not None:
        cost_guard.check_can_call(estimate_cost(model))

    base = url or OPENROUTER_URL
    endpoint = f"{base}/chat/completions"
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
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_REFERER,
        "X-Title": OPENROUTER_TITLE,
    }
    data = json.dumps(payload).encode("utf-8")
    eff_timeout = timeout or OPENROUTER_TIMEOUT

    rate_retries = 0
    server_retried = False
    while True:
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=eff_timeout) as r:
                body = r.read()
            break  # success
        except urllib.error.HTTPError as e:
            code = e.code
            if code == 429:
                if rate_retries >= max_rate_limit_retries:
                    raise RateLimitDeferred(
                        f"OpenRouter rate-limited after {rate_retries + 1} attempts "
                        f"(max_rate_limit_retries={max_rate_limit_retries}); defer and resume later."
                    ) from e
                rate_retries += 1
                time.sleep(rate_limit_wait_secs)
                continue
            if 500 <= code < 600:
                if server_retried:
                    raise OpenRouterAPIError(
                        f"OpenRouter HTTP {code} after retry: {e.reason}") from e
                server_retried = True
                time.sleep(5)
                continue
            # Other 4xx — unrecoverable.
            raise OpenRouterAPIError(f"OpenRouter HTTP {code}: {e.reason}") from e
        except urllib.error.URLError as e:
            # Network-level failure (DNS, timeout, connection reset). Not
            # retried — caller can reissue if they want.
            raise OpenRouterAPIError(f"OpenRouter network error: {e.reason}") from e

    try:
        parsed = json.loads(body)
        out = parsed["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
        raise OpenRouterAPIError(f"Malformed OpenRouter response: {e}") from e
    # Defensive: some upstreams return `content: null` (refusal/safety stop) or
    # a structured list for multipart content. We require a string so cache
    # round-trips behave (a `null` cache hit silently returning None would be
    # nasty to debug downstream).
    if not isinstance(out, str):
        raise OpenRouterAPIError(
            f"OpenRouter response content was not a string (got {type(out).__name__}); "
            "refusing to cache.")

    # Post-call cost recording. Prefer the response's `usage.cost` if present
    # (OpenRouter sometimes returns it); fall back to our a-priori estimate.
    # If the field is present but malformed (None, list, "free"), we treat that
    # as "no usable real number" and fall back to the estimate rather than
    # crashing the call after the spend has already happened.
    usage = parsed.get("usage") if isinstance(parsed, dict) else None
    actual_cost = estimate_cost(model)
    if isinstance(usage, dict) and "cost" in usage:
        try:
            c = float(usage["cost"])
            # json.loads accepts the non-standard `NaN`/`Infinity` literals and float() does NOT raise
            # on them, so guard explicitly — a NaN cost would otherwise reach cost_guard.record(), raise
            # AFTER the cache write, get swallowed into a dropped judge vote, and read differently cold vs
            # warm (pressure-test SHOULD_FIX, agent 2). Non-finite => keep the a-priori estimate.
            if math.isfinite(c):
                actual_cost = c
        except (TypeError, ValueError):
            pass  # keep the a-priori estimate; the call really did happen

    # Atomic cache write: write to a sibling .tmp then rename, so an interrupted
    # write doesn't leave a half-written JSON file that later runs trip over.
    # Write BEFORE recording cost so a failed write doesn't get charged for a
    # call we then have to re-issue (the cache hit on retry is the receipt).
    tmp = cp.with_suffix(cp.suffix + ".tmp")
    tmp.write_text(json.dumps({"model": model, "response": out}), encoding="utf-8")
    os.replace(tmp, cp)

    if cost_guard is not None:
        cost_guard.record(actual_cost)
    return out
