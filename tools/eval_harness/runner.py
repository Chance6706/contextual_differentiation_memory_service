"""Scenario runner for the CDMS ablation harness.

Fixes the v1 wiring bugs: honors per-turn fixture `provenance` (v1 hardcoded
"trusted", disabling the fence), passes the query scope through, and surfaces
errored (condition, scenario) rows WITH axis/condition so a crashed condition can
never read as "fine". Mechanical scoring only here; panel/effect scoring is a
separate step (scorer.py) so a $0 mechanical run is always possible.
"""
from __future__ import annotations

import time
from typing import Any, Callable

from tools.eval_harness.adapter import (
    CdmsAdapter, NaiveDumpAdapter, NoMemoryAdapter,
    MemorySystem, Scope, Turn, ForgetSpec, Reader,
)
from tools.eval_harness.fixtures import SCENARIOS, Scenario


# condition name -> adapter factory. CDMS conditions are ABLATIONS (one toggle each);
# naive-dump / no-memory are the bookends. External systems are NOT here (they live in a
# separate, fenced commodity-channel module per the v2 prereg §7).
def _cdms(cond: str) -> Callable[[Reader | None], MemorySystem]:
    return lambda reader=None: CdmsAdapter(condition=cond, reader=reader)

CONDITIONS: dict[str, Callable[[Reader | None], MemorySystem]] = {
    "cdms-full":           _cdms("cdms-full"),
    "cdms-fence":          _cdms("cdms-fence"),
    "cdms-forgetting":     _cdms("cdms-forgetting"),
    "cdms-random-discard": _cdms("cdms-random-discard"),
    "naive-dump":          lambda reader=None: NaiveDumpAdapter(reader=reader),
    "no-memory":           lambda reader=None: NoMemoryAdapter(),
}


def run_scenario(scenario: Scenario, adapter: MemorySystem, condition: str) -> dict[str, Any]:
    run_id = f"{condition}-{scenario.id}"
    t0 = time.perf_counter()
    adapter.reset(run_id)

    # Ingest, threading per-turn provenance (default trusted for user/assistant facts;
    # injected/external turns carry "untrusted" in the fixture so the fence is under test).
    for t in scenario.turns:
        scope = Scope(project=t.get("_scope_project", "eval-project"),
                      provenance=t.get("provenance", "trusted"))
        adapter.ingest([Turn(
            role=t["role"],
            content=t["content"],
            tool_name=t.get("tool_name", ""),
            success=t.get("success"),
            timestamp=t.get("timestamp", ""),
            provenance=t.get("provenance", ""),   # "" -> adapter falls back to scope.provenance
        )], scope=scope)

    query_results = []
    for q in scenario.queries:
        scope = Scope(project=q.get("scope_project", "eval-project"), provenance="trusted")
        # Axis 11 right-to-forget: TARGETED delete of the fact's episode(s) if the fixture
        # names them, else fall back to project (documented over-broad case).
        if scenario.axis == 11 and q.get("_forget_before"):
            adapter.forget(ForgetSpec(ids=q.get("forget_ids"),
                                      session=q.get("forget_session"),
                                      project=None if q.get("forget_ids") else "eval-project"))
        ans = adapter.query(q["question"], scope=scope)
        query_results.append({
            "question": q["question"],
            "ground_truth": q["ground_truth"],
            "answer_text": ans.text[:800],
            "citations": ans.citations,
            "tokens_injected": ans.tokens_injected,
            "latency_ms": ans.latency_ms,
            "scope": {"project": scope.project, "provenance": scope.provenance},
        })

    elapsed = (time.perf_counter() - t0) * 1000
    health = adapter.health()
    if hasattr(adapter, "cleanup"):
        adapter.cleanup()
    return {
        "scenario_id": scenario.id,
        "axis": scenario.axis,
        "condition": condition,
        "content_hash": scenario.content_hash,
        "total_latency_ms": elapsed,
        "health": health,
        "queries": query_results,
    }


def run_all(conditions: list[str] | None = None, scenarios: list[str] | None = None,
            *, reader: Reader | None = None) -> list[dict[str, Any]]:
    conditions = conditions or list(CONDITIONS)
    targets = SCENARIOS if scenarios is None else [s for s in SCENARIOS if s.id in set(scenarios)]

    results: list[dict[str, Any]] = []
    for cond in conditions:
        factory = CONDITIONS.get(cond)
        if factory is None:
            results.append({"condition": cond, "axis": None, "error": "unknown condition"})
            continue
        for scenario in targets:
            adapter = factory(reader)
            try:
                results.append(run_scenario(scenario, adapter, cond))
            except Exception as exc:
                # Surfaced WITH axis + condition so a crashed condition is visible, never skipped.
                results.append({
                    "scenario_id": scenario.id, "axis": scenario.axis,
                    "condition": cond, "error": f"{type(exc).__name__}: {exc}",
                })
                if hasattr(adapter, "cleanup"):
                    adapter.cleanup()
    return results
