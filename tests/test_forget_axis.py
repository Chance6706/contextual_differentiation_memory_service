"""Axis-11 right-to-forget, end-to-end ($0). The genuine differentiation from the pressure
test: cdms-full performs a TARGETED content delete (deleted PII gone, a later re-write SURVIVES),
while naive-dump cannot delete and keeps leaking the PII.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["CDMS_EMBED_BACKEND"] = "hash"
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from tools.eval_harness.runner import run_scenario, CONDITIONS
from tools.eval_harness.fixtures import SCENARIOS
from tools.eval_harness.run import score_forget_leak, AXIS11_PII
from tools.eval_harness.analyze import ablation_deltas
from tools.eval_harness.adapter import Scope, Turn, ForgetSpec


def _scenario():
    return next(s for s in SCENARIOS if s.id == "right_to_forget")


def _rate(obs, cond):
    vals = [o["value"] for o in obs if o["condition"] == cond]
    return sum(vals) / len(vals) if vals else float("nan")


def test_forget_ablation_cdms_deletes_dump_cannot():
    scen = _scenario()
    results = []
    for cond in ("cdms-full", "naive-dump", "no-memory"):
        adapter = CONDITIONS[cond](None)   # passthrough reader
        results.append(run_scenario(scen, adapter, cond, forget_facts=AXIS11_PII))
        if hasattr(adapter, "cleanup"):
            adapter.cleanup()
    obs = score_forget_leak(results)
    assert obs
    assert _rate(obs, "cdms-full") == 0.0      # targeted delete worked — PII gone
    assert _rate(obs, "naive-dump") > 0.5      # a dump cannot delete — keeps leaking PII
    assert _rate(obs, "no-memory") == 0.0      # floor (stores nothing)

    rows = ablation_deltas(obs, seed=1)
    nd = next(r for r in rows if r["condition"] == "naive-dump")
    assert nd["delta_vs_ref"] > 0.5            # dump leaks the deleted PII that cdms-full removed


def test_targeted_delete_spares_the_rewrite(tmp_path):
    # The later re-write email must SURVIVE a targeted delete of the OLD PII (not a project nuke).
    from tools.eval_harness.adapter import CdmsAdapter
    a = CdmsAdapter("cdms-full", base_path=tmp_path)
    a.reset("rw")
    a.ingest([Turn(role="user", content="My email is alice.chen@example.com")], scope=Scope(project="P"))
    a.ingest([Turn(role="user", content="Actually my email is now alice.chen@new-company.com")], scope=Scope(project="P"))
    a.forget(ForgetSpec(facts=["alice.chen@example.com"]))
    ans = a.query("what is my current email?", scope=Scope(project="P"))
    assert "alice.chen@example.com" not in ans.text          # old PII deleted
    assert "new-company.com" in ans.text                     # re-write survived
    a.cleanup()
