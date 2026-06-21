"""Hermetic tests for tools/openrouter_cost_guard.py.

No live HTTP, no real API keys. State is isolated per test via tmp_path.

Coverage:
  1.  Fresh state file (none on disk) → starts at $0 spent.
  2.  Existing state file is loaded.
  3.  record() increments spent and persists to disk.
  4.  check_can_call() allows calls strictly under cap.
  5.  check_can_call() raises at exactly cap (>= not >).
  6.  check_can_call() raises above cap.
  7.  Warning threshold logs but allows (caplog).
  8.  remaining() can go negative if record() overshoots cap.
  9.  reset() zeroes spent/call_count and persists.
  10. record() validates actual_cost >= 0.
  11. __init__ validates cap_usd > 0.
  12. __init__ validates warning_threshold_pct in (0, 1).
  13. Atomic write goes through {state_file}.tmp then os.replace().
  14. Concurrent record() calls serialize correctly (sum = N * per-call).
  15. call_count persists across CostGuard instances.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from pathlib import Path

import pytest

# Make tools/ importable in this test process.
_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from openrouter_cost_guard import BudgetExceededError, CostGuard  # noqa: E402


# --------------------------------------------------------------------- #
# 1. Fresh-state behavior
# --------------------------------------------------------------------- #
def test_cost_guard_starts_at_zero_spent_on_new_state_file(tmp_path: Path):
    state_file = tmp_path / "spend.json"
    assert not state_file.exists()
    g = CostGuard(cap_usd=75.0, state_file=state_file)
    assert g.spent() == 0.0
    assert g.remaining() == 75.0
    assert g.call_count == 0


# --------------------------------------------------------------------- #
# 2. Load existing state
# --------------------------------------------------------------------- #
def test_cost_guard_loads_existing_state_file(tmp_path: Path):
    state_file = tmp_path / "spend.json"
    state_file.write_text(
        json.dumps(
            {
                "spent_usd": 12.34,
                "last_updated": "2026-06-20T00:00:00+00:00",
                "cap_usd": 75.0,
                "call_count": 7,
            }
        ),
        encoding="utf-8",
    )
    g = CostGuard(cap_usd=75.0, state_file=state_file)
    assert g.spent() == pytest.approx(12.34)
    assert g.call_count == 7
    assert g.remaining() == pytest.approx(75.0 - 12.34)


# --------------------------------------------------------------------- #
# 3. record() increments and persists
# --------------------------------------------------------------------- #
def test_cost_guard_record_increments_spent_and_persists(tmp_path: Path):
    state_file = tmp_path / "spend.json"
    g = CostGuard(cap_usd=75.0, state_file=state_file)
    g.record(1.50)
    g.record(0.25)
    assert g.spent() == pytest.approx(1.75)
    assert g.call_count == 2

    # Persistence: a fresh instance should see the same numbers.
    g2 = CostGuard(cap_usd=75.0, state_file=state_file)
    assert g2.spent() == pytest.approx(1.75)
    assert g2.call_count == 2

    # The file itself has the expected shape.
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["spent_usd"] == pytest.approx(1.75)
    assert data["call_count"] == 2
    assert data["cap_usd"] == 75.0
    assert "last_updated" in data and data["last_updated"]


# --------------------------------------------------------------------- #
# 4. check_can_call allows under cap
# --------------------------------------------------------------------- #
def test_cost_guard_check_can_call_allows_under_cap(tmp_path: Path):
    g = CostGuard(cap_usd=75.0, state_file=tmp_path / "s.json")
    g.record(10.0)
    # 10 + 50 = 60 < 75 → allowed, no exception.
    g.check_can_call(estimated_cost=50.0)
    # State is unchanged after a check.
    assert g.spent() == 10.0
    assert g.call_count == 1


# --------------------------------------------------------------------- #
# 5. check_can_call raises at EXACTLY cap (>= boundary)
# --------------------------------------------------------------------- #
def test_cost_guard_check_can_call_raises_at_exactly_cap(tmp_path: Path):
    g = CostGuard(cap_usd=75.0, state_file=tmp_path / "s.json")
    g.record(50.0)
    # 50 + 25 = 75.0 exactly → must raise (>= cap).
    with pytest.raises(BudgetExceededError):
        g.check_can_call(estimated_cost=25.0)
    # No state mutation on raise.
    assert g.spent() == 50.0


# --------------------------------------------------------------------- #
# 6. check_can_call raises above cap
# --------------------------------------------------------------------- #
def test_cost_guard_check_can_call_raises_above_cap(tmp_path: Path):
    g = CostGuard(cap_usd=75.0, state_file=tmp_path / "s.json")
    g.record(74.0)
    with pytest.raises(BudgetExceededError):
        g.check_can_call(estimated_cost=2.0)  # 76 > 75


# --------------------------------------------------------------------- #
# 7. Warning threshold logs but allows
# --------------------------------------------------------------------- #
def test_cost_guard_warning_threshold_logs_but_allows(tmp_path: Path, caplog):
    g = CostGuard(
        cap_usd=100.0,
        state_file=tmp_path / "s.json",
        warning_threshold_pct=0.87,
    )
    g.record(80.0)
    # 80 + 10 = 90 → > 87, < 100 → warning fires but no raise.
    with caplog.at_level(logging.WARNING, logger="openrouter_cost_guard"):
        g.check_can_call(estimated_cost=10.0)  # must not raise
    assert any(
        "warning threshold crossed" in rec.getMessage().lower()
        for rec in caplog.records
    ), f"expected warning log, got: {[r.getMessage() for r in caplog.records]}"


# --------------------------------------------------------------------- #
# 8. remaining() can go negative if record() exceeds cap
# --------------------------------------------------------------------- #
def test_cost_guard_remaining_can_go_negative_if_external_bypass(tmp_path: Path):
    g = CostGuard(cap_usd=75.0, state_file=tmp_path / "s.json")
    # Simulate a caller that bypassed check_can_call() and recorded actual
    # spend exceeding the cap (e.g. estimate was wrong).
    g.record(80.0)
    assert g.spent() == 80.0
    assert g.remaining() == pytest.approx(-5.0)
    # And any subsequent check_can_call must refuse cleanly, not crash.
    with pytest.raises(BudgetExceededError):
        g.check_can_call(estimated_cost=0.0)


# --------------------------------------------------------------------- #
# 9. reset() zeroes spent and persists
# --------------------------------------------------------------------- #
def test_cost_guard_reset_zeroes_spent_and_persists(tmp_path: Path):
    state_file = tmp_path / "s.json"
    g = CostGuard(cap_usd=75.0, state_file=state_file)
    g.record(33.0)
    g.record(7.0)
    assert g.spent() == 40.0
    assert g.call_count == 2

    g.reset()
    assert g.spent() == 0.0
    assert g.call_count == 0

    # Persisted: a fresh instance reads zeros.
    g2 = CostGuard(cap_usd=75.0, state_file=state_file)
    assert g2.spent() == 0.0
    assert g2.call_count == 0


# --------------------------------------------------------------------- #
# 10. record() validates non-negative
# --------------------------------------------------------------------- #
def test_cost_guard_record_validates_non_negative(tmp_path: Path):
    g = CostGuard(cap_usd=75.0, state_file=tmp_path / "s.json")
    with pytest.raises(ValueError):
        g.record(-0.01)
    # State unchanged after invalid input.
    assert g.spent() == 0.0
    assert g.call_count == 0
    # Zero is permitted (free-tier calls).
    g.record(0.0)
    assert g.spent() == 0.0
    assert g.call_count == 1


# --------------------------------------------------------------------- #
# 11. __init__ validates cap_usd > 0
# --------------------------------------------------------------------- #
def test_cost_guard_init_validates_cap_positive(tmp_path: Path):
    with pytest.raises(ValueError):
        CostGuard(cap_usd=0.0, state_file=tmp_path / "s.json")
    with pytest.raises(ValueError):
        CostGuard(cap_usd=-1.0, state_file=tmp_path / "s.json")


# --------------------------------------------------------------------- #
# 12. __init__ validates warning_threshold_pct in (0, 1)
# --------------------------------------------------------------------- #
def test_cost_guard_init_validates_warning_threshold_range(tmp_path: Path):
    for bad in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError):
            CostGuard(
                cap_usd=75.0,
                state_file=tmp_path / "s.json",
                warning_threshold_pct=bad,
            )
    # Endpoints inside (0, 1) work.
    CostGuard(cap_usd=75.0, state_file=tmp_path / "ok1.json", warning_threshold_pct=0.001)
    CostGuard(cap_usd=75.0, state_file=tmp_path / "ok2.json", warning_threshold_pct=0.999)


# --------------------------------------------------------------------- #
# 13. Atomic write goes via {state_file}.tmp then os.replace()
# --------------------------------------------------------------------- #
def test_cost_guard_atomic_write_via_tmp_then_replace(tmp_path: Path, monkeypatch):
    state_file = tmp_path / "spend.json"
    g = CostGuard(cap_usd=75.0, state_file=state_file)

    seen: dict = {"tmp_existed": False, "replace_src": None, "replace_dst": None}

    real_replace = os.replace

    def fake_replace(src, dst):
        # When os.replace is invoked the source MUST exist (the tmp file just
        # written) — that's the whole point of write-then-replace.
        seen["tmp_existed"] = Path(src).exists()
        seen["replace_src"] = str(src)
        seen["replace_dst"] = str(dst)
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", fake_replace)
    g.record(1.23)

    assert seen["tmp_existed"] is True
    assert seen["replace_src"] is not None
    assert seen["replace_dst"] is not None
    # The tmp path is the state file path + ".tmp".
    assert seen["replace_src"].endswith(".tmp"), seen["replace_src"]
    assert seen["replace_dst"] == str(state_file)
    # And after os.replace, the .tmp sibling no longer exists.
    assert not Path(seen["replace_src"]).exists()
    assert state_file.exists()


# --------------------------------------------------------------------- #
# 14. Concurrent record() calls serialize correctly
# --------------------------------------------------------------------- #
def test_cost_guard_concurrent_records_serialize_correctly(tmp_path: Path):
    state_file = tmp_path / "spend.json"
    g = CostGuard(cap_usd=10_000.0, state_file=state_file)

    per_call = 0.13
    n_threads = 10
    barrier = threading.Barrier(n_threads)

    def worker():
        # Maximize contention: every thread parks on the barrier, then races.
        barrier.wait()
        g.record(per_call)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    expected = per_call * n_threads
    assert g.spent() == pytest.approx(expected, rel=1e-9, abs=1e-9)
    assert g.call_count == n_threads

    # And the persisted state matches.
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["spent_usd"] == pytest.approx(expected, rel=1e-9, abs=1e-9)
    assert data["call_count"] == n_threads


# --------------------------------------------------------------------- #
# 15. call_count persists across CostGuard instances
# --------------------------------------------------------------------- #
def test_cost_guard_persists_call_count(tmp_path: Path):
    state_file = tmp_path / "spend.json"
    g1 = CostGuard(cap_usd=75.0, state_file=state_file)
    g1.record(0.10)
    g1.record(0.20)
    g1.record(0.30)
    assert g1.call_count == 3

    g2 = CostGuard(cap_usd=75.0, state_file=state_file)
    assert g2.call_count == 3
    assert g2.spent() == pytest.approx(0.60)

    # And the next record() continues the count.
    g2.record(0.05)
    assert g2.call_count == 4
    g3 = CostGuard(cap_usd=75.0, state_file=state_file)
    assert g3.call_count == 4


# --------------------------------------------------------------------- #
# 16. NaN/Inf inputs are rejected at every numeric boundary (R1)
# --------------------------------------------------------------------- #
def test_cost_guard_rejects_nan_and_inf_inputs(tmp_path: Path):
    g = CostGuard(cap_usd=75.0, state_file=tmp_path / "s.json")
    nan = float("nan")
    inf = float("inf")
    for bad in (nan, inf, -inf):
        with pytest.raises(ValueError):
            g.check_can_call(estimated_cost=bad)
        with pytest.raises(ValueError):
            g.record(actual_cost=bad)
        with pytest.raises(ValueError):
            g.projected(estimated_cost=bad)
    # Guard state untouched after rejection storms.
    assert g.spent() == 0.0
    assert g.call_count == 0

    # __init__ also rejects NaN/Inf cap_usd and warning_threshold_pct.
    for bad in (nan, inf, -inf):
        with pytest.raises(ValueError):
            CostGuard(cap_usd=bad, state_file=tmp_path / "s_nan_cap.json")
    for bad in (nan,):
        with pytest.raises(ValueError):
            CostGuard(
                cap_usd=75.0,
                state_file=tmp_path / "s_nan_thr.json",
                warning_threshold_pct=bad,
            )


# --------------------------------------------------------------------- #
# 17. Corrupt state file → start fresh + warn, not crash (R5)
# --------------------------------------------------------------------- #
def test_cost_guard_corrupt_state_file_recovers_to_zero(tmp_path, caplog):
    # Case A: malformed JSON.
    a = tmp_path / "a.json"
    a.write_text("{not valid json", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="openrouter_cost_guard"):
        g = CostGuard(cap_usd=75.0, state_file=a)
    assert g.spent() == 0.0
    assert g.call_count == 0

    # Case B: wrong type for spent_usd.
    b = tmp_path / "b.json"
    b.write_text('{"spent_usd": "not_a_number", "call_count": 1}', encoding="utf-8")
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="openrouter_cost_guard"):
        g = CostGuard(cap_usd=75.0, state_file=b)
    assert g.spent() == 0.0

    # Case C: negative spent_usd (would grant fake budget).
    c = tmp_path / "c.json"
    c.write_text('{"spent_usd": -1000.0, "call_count": 0}', encoding="utf-8")
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="openrouter_cost_guard"):
        g = CostGuard(cap_usd=75.0, state_file=c)
    assert g.spent() == 0.0

    # Case D: JSON root is a list, not a dict.
    d = tmp_path / "d.json"
    d.write_text("[1, 2, 3]", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="openrouter_cost_guard"):
        g = CostGuard(cap_usd=75.0, state_file=d)
    assert g.spent() == 0.0


# --------------------------------------------------------------------- #
# 18. BudgetExceededError carries structured fields (L2)
# --------------------------------------------------------------------- #
def test_budget_exceeded_error_has_structured_attributes(tmp_path: Path):
    g = CostGuard(cap_usd=75.0, state_file=tmp_path / "s.json")
    g.record(50.0)
    try:
        g.check_can_call(estimated_cost=30.0)
    except BudgetExceededError as exc:
        assert exc.spent == pytest.approx(50.0)
        assert exc.estimated_cost == pytest.approx(30.0)
        assert exc.projected == pytest.approx(80.0)
        assert exc.cap_usd == pytest.approx(75.0)
    else:
        pytest.fail("Expected BudgetExceededError")


# --------------------------------------------------------------------- #
# 19. State file's cap_usd field is informational; constructor's cap wins
# --------------------------------------------------------------------- #
def test_state_file_cap_field_is_informational_only(tmp_path: Path):
    state_file = tmp_path / "s.json"
    state_file.write_text(
        json.dumps(
            {
                "spent_usd": 40.0,
                "last_updated": "2026-06-20T00:00:00+00:00",
                "cap_usd": 1000.0,   # huge cap in file
                "call_count": 1,
            }
        ),
        encoding="utf-8",
    )
    # Constructor passes a much smaller cap; it must win.
    g = CostGuard(cap_usd=50.0, state_file=state_file)
    assert g.cap_usd == 50.0
    assert g.spent() == 40.0
    # 40 + 20 = 60 >= 50 → must raise.
    with pytest.raises(BudgetExceededError):
        g.check_can_call(estimated_cost=20.0)


# --------------------------------------------------------------------- #
# 20. Warning threshold does NOT fire below the threshold (boundary)
# --------------------------------------------------------------------- #
def test_warning_threshold_does_not_fire_below(tmp_path: Path, caplog):
    g = CostGuard(
        cap_usd=100.0,
        state_file=tmp_path / "s.json",
        warning_threshold_pct=0.87,
    )
    g.record(50.0)
    # 50 + 20 = 70 → below 87 → no warning.
    with caplog.at_level(logging.WARNING, logger="openrouter_cost_guard"):
        g.check_can_call(estimated_cost=20.0)
    assert not any(
        "warning threshold crossed" in rec.getMessage().lower()
        for rec in caplog.records
    )

    # Exactly at threshold (87.0) → strict > → no warning (boundary lock).
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="openrouter_cost_guard"):
        g.check_can_call(estimated_cost=37.0)  # 50 + 37 = 87
    assert not any(
        "warning threshold crossed" in rec.getMessage().lower()
        for rec in caplog.records
    )
