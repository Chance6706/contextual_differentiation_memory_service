"""Axis-8 multi-project isolation, end-to-end ($0, passthrough reader).

The ablation: cdms-full (scoped retrieve) must NOT surface the other project's value;
cdms-no-scope (project filter dropped) leaks it — isolating the project-scoping mechanism.
This is the v1 bug turned into a measured control (v1's adapter always dropped the scope
and then scored the total leak as "100% isolation").
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["CDMS_EMBED_BACKEND"] = "hash"
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from tools.eval_harness.runner import run_all
from tools.eval_harness.run import score_isolation_leak
from tools.eval_harness.analyze import ablation_deltas


def _rate(obs, condition):
    vals = [o["value"] for o in obs if o["condition"] == condition]
    return sum(vals) / len(vals) if vals else float("nan")


def test_isolation_ablation_scoped_vs_unscoped():
    results = run_all(conditions=["cdms-full", "cdms-no-scope", "naive-dump", "no-memory"],
                      scenarios=["multi_project"])
    obs = score_isolation_leak(results)
    assert obs, "no isolation observations produced"
    full = _rate(obs, "cdms-full")
    noscope = _rate(obs, "cdms-no-scope")
    dump = _rate(obs, "naive-dump")

    assert full == 0.0, f"cdms-full leaked the other project's value ({full})"   # scoping works
    assert noscope > 0.5, f"cdms-no-scope should leak heavily ({noscope})"        # scoping off -> leaks
    assert dump > 0.5, f"naive-dump should leak ({dump})"                          # no isolation ceiling

    # The ablation delta isolates the scoping mechanism (higher leaked_other = worse).
    rows = ablation_deltas(obs, seed=1)
    ns = next(r for r in rows if r["condition"] == "cdms-no-scope")
    assert ns["delta_vs_ref"] > 0.5   # dropping the scope demonstrably increases cross-project leak
