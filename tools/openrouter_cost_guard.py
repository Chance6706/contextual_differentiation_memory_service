"""OpenRouter cost guard — hard $-cap enforcement for the CDMS validation matrix.

PRE-REG §4 HARD COST STOPS:
  * cap_usd = $75 by convention (caller-configured) covers ALL OpenRouter API spend.
  * At/above cap: refuse the call (raise BudgetExceededError) BEFORE the HTTP request.
  * At warning_threshold_pct (default 87%): emit a warning to the module logger but
    allow the call to proceed.
  * State persists across runs to a JSON file so a fresh process re-loads prior spend.

State file format (JSON):
  {
    "spent_usd":   float,    # cumulative actual spend (sum of record() calls)
    "last_updated": str,     # ISO-8601 timestamp (UTC) of the most recent write
    "cap_usd":      float,   # the cap as configured by the most recent writer
    "call_count":   int      # number of successful record() invocations
  }

Persistence semantics:
  * Atomic write via {state_file}.tmp + os.replace() — readers either see the old
    file or the new file, never a half-written one. Survives process crash mid-write.
  * threading.Lock for in-process serialization of concurrent record() calls so
    spent_usd and call_count are not lost-update raced.
  * The persisted ``cap_usd`` field is informational only. On reload, the
    constructor's ``cap_usd`` argument always wins (so callers can lower the
    cap mid-run without editing the file). Reload validates spent_usd is a
    finite, non-negative number; any other shape → log warning + start fresh.

Scope limits (deliberate, not bugs):
  * Single-process only. ``threading.Lock`` does not coordinate across processes.
    Two CostGuard processes sharing the same state file WILL lost-update each
    other. The CDMS matrix runs one cost guard per matrix-runner process — if
    that ever changes, add a file lock (e.g. ``portalocker``) around _persist
    or move to a sqlite-based store.
  * Plaintext at rest. State file contains $-spend and call counts in cleartext.
    Caller is responsible for placing the file in an appropriate-permissioned
    directory (e.g. ``~/.cdms/`` with 0700). The guard does not chmod the file
    or its parent.

Operational discipline:
  * check_can_call() does NOT mutate state. It is a pre-flight gate; record() is
    called after the API responds with the actual billed cost. This split exists
    because OpenRouter's actual cost is only knowable post-response (model output
    token count is not pre-determined). Estimation gates; ground truth records.
    There is a TOCTOU window between check_can_call() and record(): a concurrent
    record() in another thread (or process) can change the budget state in
    between. The discipline that closes it is *always pair them*: check, call,
    record, in tight sequence, before any other check_can_call().
  * remaining() can return a negative value if a caller's record() exceeded the
    cap — e.g. if check_can_call's pre-estimate underestimated the actual cost,
    or if a different process bypassed the guard entirely. Negative remaining
    is a *signal* (you overspent), not a crash; the next check_can_call() will
    refuse cleanly.
  * NaN/+Inf/-Inf inputs to check_can_call(), record(), and projected() are
    rejected with ValueError. NaN comparisons always return False, which would
    silently bypass the cap; once NaN reaches self._spent, the guard is bricked
    (every comparison is False). Reject at the boundary.
"""

from __future__ import annotations

import json
import logging
import math
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def _validate_finite_nonneg(name: str, value: object) -> float:
    """Reject non-numeric, NaN, +/-Inf, and negative values. Return as float.

    Critical because Python comparisons against NaN always return False — so a
    NaN slipping into estimated_cost would silently bypass the cap check, and a
    NaN landing in self._spent via record() would brick the guard forever
    (every subsequent comparison would say 'fine, allow'). +Inf is rejected for
    similar reasons: stdlib json will serialize it as the literal 'Infinity',
    which json.loads() then rejects on re-read.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number >= 0, got {value!r}")
    f = float(value)
    if math.isnan(f) or math.isinf(f):
        raise ValueError(f"{name} must be a finite number >= 0, got {value!r}")
    if f < 0:
        raise ValueError(f"{name} must be >= 0, got {value!r}")
    return f


class BudgetExceededError(Exception):
    """Raised by CostGuard.check_can_call when (spent + estimated_cost) >= cap_usd.

    Carries structured attributes so callers can branch on them without parsing
    the message: ``spent``, ``estimated_cost``, ``projected``, ``cap_usd``.
    """

    def __init__(
        self,
        message: str,
        *,
        spent: float,
        estimated_cost: float,
        projected: float,
        cap_usd: float,
    ) -> None:
        super().__init__(message)
        self.spent = spent
        self.estimated_cost = estimated_cost
        self.projected = projected
        self.cap_usd = cap_usd


class CostGuard:
    """Thread-safe, crash-safe $-cap enforcer for OpenRouter API spend.

    Typical use:
        guard = CostGuard(cap_usd=75.0, state_file=Path("./.openrouter_spend.json"))
        guard.check_can_call(estimated_cost=0.04)   # raises if cap would be crossed
        actual = call_openrouter(...)
        guard.record(actual)
    """

    def __init__(
        self,
        cap_usd: float,
        state_file: Path,
        warning_threshold_pct: float = 0.87,
    ) -> None:
        if (
            not isinstance(cap_usd, (int, float))
            or isinstance(cap_usd, bool)
            or math.isnan(float(cap_usd))
            or math.isinf(float(cap_usd))
            or cap_usd <= 0
        ):
            raise ValueError(f"cap_usd must be a finite number > 0, got {cap_usd!r}")
        if (
            not isinstance(warning_threshold_pct, (int, float))
            or isinstance(warning_threshold_pct, bool)
            or math.isnan(float(warning_threshold_pct))
            or not (0 < warning_threshold_pct < 1)
        ):
            raise ValueError(
                f"warning_threshold_pct must be in (0, 1), got {warning_threshold_pct!r}"
            )

        self._cap_usd = float(cap_usd)
        self._state_file = Path(state_file)
        self._warning_threshold_pct = float(warning_threshold_pct)
        self._lock = threading.Lock()
        self._spent = 0.0
        self._call_count = 0

        self._load_state()

    # ------------------------------------------------------------------
    # State I/O
    # ------------------------------------------------------------------
    def _load_state(self) -> None:
        """Initialize spent/call_count from state_file if it exists; else zero.

        Recoverable corruption (missing file, unreadable file, malformed JSON,
        wrong field types, negative numbers, NaN/Inf) is treated as 'start
        fresh at $0' with a warning log. The alternative — crash on load —
        would brick a whole matrix run on a transient disk hiccup or a
        hand-edited typo, with no recovery path. A warning is visible in logs
        and the guard remains usable.

        NOTE: the state file's ``cap_usd`` field is informational only — the
        constructor's ``cap_usd`` argument always wins. If you persist with a
        $75 cap and reopen with $50, the guard runs at $50 regardless of what
        the file says.
        """
        if not self._state_file.exists():
            self._spent = 0.0
            self._call_count = 0
            return
        try:
            raw = self._state_file.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError(f"state file root is not an object: {type(data).__name__}")
            spent_raw = data.get("spent_usd", 0.0)
            count_raw = data.get("call_count", 0)
            # Reject non-numeric, NaN, Inf, negative — see _validate_finite_nonneg
            # rationale above.
            spent = float(spent_raw)
            count = int(count_raw)
            if math.isnan(spent) or math.isinf(spent) or spent < 0:
                raise ValueError(f"spent_usd out of range: {spent_raw!r}")
            if count < 0:
                raise ValueError(f"call_count must be >= 0: {count_raw!r}")
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(
                "CostGuard: could not read state file %s (%s); starting fresh at $0",
                self._state_file,
                e,
            )
            self._spent = 0.0
            self._call_count = 0
            return
        self._spent = spent
        self._call_count = count

    def _persist(self) -> None:
        """Atomically write current state to disk. Caller must hold self._lock."""
        payload = {
            "spent_usd": self._spent,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "cap_usd": self._cap_usd,
            "call_count": self._call_count,
        }
        # Ensure parent directory exists.
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._state_file.with_suffix(self._state_file.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self._state_file)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def check_can_call(self, estimated_cost: float) -> None:
        """Pre-flight gate. Raises BudgetExceededError if the call would cross the cap.

        Does NOT modify state. Emits a warning (does not raise) if the call would
        cross warning_threshold_pct * cap_usd. Rejects NaN, +/-Inf, and negative
        ``estimated_cost`` so a bad input cannot silently bypass the cap (NaN
        comparisons always return False).
        """
        estimated = _validate_finite_nonneg("estimated_cost", estimated_cost)
        with self._lock:
            projected = self._spent + estimated
            if projected >= self._cap_usd:
                raise BudgetExceededError(
                    f"OpenRouter budget would be exceeded: spent=${self._spent:.4f} "
                    f"+ estimated=${estimated:.4f} = ${projected:.4f} "
                    f">= cap=${self._cap_usd:.4f}",
                    spent=self._spent,
                    estimated_cost=estimated,
                    projected=projected,
                    cap_usd=self._cap_usd,
                )
            if projected > self._cap_usd * self._warning_threshold_pct:
                logger.warning(
                    "CostGuard warning threshold crossed: projected=$%.4f "
                    "cap=$%.4f threshold_pct=%.2f",
                    projected,
                    self._cap_usd,
                    self._warning_threshold_pct,
                )

    def record(self, actual_cost: float) -> None:
        """Add actual_cost to cumulative spend; persist atomically.

        Does NOT enforce the cap itself; that's check_can_call()'s job. record()
        will faithfully record overspend (so remaining() goes negative) — a
        diagnostic signal that callers bypassed the gate or underestimated cost.
        Rejects NaN/Inf/negative so a poisoned cost cannot brick subsequent
        check_can_call() comparisons.
        """
        actual = _validate_finite_nonneg("actual_cost", actual_cost)
        with self._lock:
            self._spent += actual
            self._call_count += 1
            self._persist()

    def spent(self) -> float:
        """Cumulative recorded spend in USD."""
        with self._lock:
            return self._spent

    def remaining(self) -> float:
        """cap_usd minus spent. Can be negative if external bypass occurred."""
        with self._lock:
            return self._cap_usd - self._spent

    def projected(self, estimated_cost: float) -> float:
        """spent + estimated_cost.

        Does not mutate state. Raises ValueError for NaN/Inf/negative inputs
        (matching check_can_call's validation; better to fail fast than to
        return a NaN that the caller will then misinterpret).
        """
        estimated = _validate_finite_nonneg("estimated_cost", estimated_cost)
        with self._lock:
            return self._spent + estimated

    def reset(self) -> None:
        """Zero out spend and call_count; persist."""
        with self._lock:
            self._spent = 0.0
            self._call_count = 0
            self._persist()

    # Convenience accessors (read-only properties)
    @property
    def cap_usd(self) -> float:
        return self._cap_usd

    @property
    def call_count(self) -> int:
        with self._lock:
            return self._call_count

    @property
    def warning_threshold_pct(self) -> float:
        return self._warning_threshold_pct

    @property
    def state_file(self) -> Path:
        return self._state_file
