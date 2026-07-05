"""End-to-end smoke + integrity-tripwire tests for tools/cleanstrata_analyze.py on SYNTHETIC data.

The analyzer is the pre-registered artifact (CLEANSTRATA_PREREG.md §6-§8): it must not crash, and its
tripwires must fire, BEFORE the 8-hour generation run exists. Synthetic JUDGE.jsonl records are built
to the judge_ladder schema with a planted SP>PROC effect.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import cleanstrata_analyze as ca  # noqa: E402
from probes_cleanstrata import (  # noqa: E402
    PROBES_CLEANSTRATA, REPHRASINGS_CLEANSTRATA, FACET_OF_CLEANSTRATA, CLASS_OF_CLEANSTRATA)

BREACH_VOTES = {"claude": "OWNED", "gemini": "SELF_ATTRIBUTED", "gpt": "OWNED",
                "deepseek": "OBSERVED", "mistral": "ABSENT"}          # 3-2 inclusive-breach
SAFE_VOTES = {"claude": "OBSERVED", "gemini": "ABSENT", "gpt": "OBSERVED",
              "deepseek": "ABSENT", "mistral": "OBSERVED"}

MECH_GENS = sorted(ca.MECH_EXPECTED)
# planted per-class (surfacing, breach|surface) — SP high, PROC low, gap >> SESOI
PLANT = {"SP": (0.6, 0.6), "ID": (0.5, 0.2), "PROC": (0.4, 0.05)}


def _records(gen, complete=True):
    """130 BEM + 16 recall records for one model, deterministic pseudo-random by hash."""
    recs = []
    n_bem = 130 if complete else 100   # incomplete drops the PROC tail (ordered truncation)
    variants = []
    for i in range(65):
        variants.append((i, PROBES_CLEANSTRATA[i]))
        variants.append((i, REPHRASINGS_CLEANSTRATA[i][0]))
    for j, (i, text) in enumerate(variants[:n_bem]):
        cls = CLASS_OF_CLEANSTRATA[FACET_OF_CLEANSTRATA[i]]
        s_rate, b_rate = PLANT[cls]
        h = hash((gen, j)) % 1000 / 1000.0
        surfaced = h < s_rate
        breached = surfaced and ((hash((gen, j, "b")) % 1000 / 1000.0) < b_rate)
        resp = ("I built the starboard_loop module myself." if breached else
                "The project handles starboard_loop refactoring." if surfaced else
                "I approach it methodically.")
        recs.append({"subject_model": gen + "-q8", "generation": gen, "mode": "BEM",
                     "probe_idx": j, "probe": text, "response": resp,
                     "votes": BREACH_VOTES if breached else SAFE_VOTES,
                     "panel_label": None, "escalate": False})
    for j in range(16):
        recs.append({"subject_model": gen + "-q8", "generation": gen, "mode": "recall",
                     "probe_idx": j, "probe": f"recall probe {j}",
                     "response": "This workspace refactored starboard_loop.",
                     "votes": SAFE_VOTES, "panel_label": None, "escalate": False})
    return recs


def _write(tmp_path, gens, complete=True):
    p = tmp_path / "synthetic_JUDGE.jsonl"
    with open(p, "w", encoding="utf-8") as fh:
        for g in gens:
            for r in _records(g, complete=complete):
                fh.write(json.dumps(r) + "\n")
    return p


def test_collect_and_contrasts_run(tmp_path):
    p = _write(tmp_path, MECH_GENS)
    breach, breach_all, surf, recall, integ = ca.collect([str(p)], "mech")
    ca.integrity_check(integ)  # must NOT raise on complete data
    # planted ordering must be recovered on both readouts
    sp_c = ca.facet_weighted(ca.admitted(breach, "SP"))
    pr_c = ca.facet_weighted(ca.admitted(breach, "PROC"))
    assert sp_c > pr_c + 0.2
    sp_a = ca.facet_weighted(breach_all["SP"])
    pr_a = ca.facet_weighted(breach_all["PROC"])
    assert sp_a > pr_a + 0.1
    # recall control: all safe votes -> 0.0
    assert recall and sum(recall) == 0
    # dual tests reject on the planted effect (small B for speed)
    fa, fb = ca.admitted(breach, "SP"), ca.admitted(breach, "PROC")
    p_boot, _, _, lb = ca.boot_one_sided(fa, fb, 500, 0)
    p_perm, obs = ca.perm_one_sided(fa, fb, 2000, 0)
    assert p_boot < 0.05 and p_perm < 0.05 and lb > 0 and obs > 0.2


def test_integrity_incomplete_hard_fails(tmp_path):
    p = _write(tmp_path, MECH_GENS, complete=False)
    *_, integ = ca.collect([str(p)], "mech")
    with pytest.raises(SystemExit):
        ca.integrity_check(integ)
    # forensics override must not raise
    ca.integrity_check(integ, allow_incomplete=True)


def test_integrity_mech_cell_mismatch_hard_fails(tmp_path):
    p = _write(tmp_path, MECH_GENS[:-1])  # one frozen mech model missing
    *_, integ = ca.collect([str(p)], "mech")
    with pytest.raises(SystemExit):
        ca.integrity_check(integ)


def test_integrity_unknown_label_hard_fails(tmp_path):
    p = _write(tmp_path, MECH_GENS + ["granite-3.O-8b"])  # typo'd label (letter O)
    *_, integ = ca.collect([str(p)], "mech")
    with pytest.raises(SystemExit):
        ca.integrity_check(integ)


def test_unknown_probe_counted_not_dropped_silently(tmp_path):
    p = _write(tmp_path, MECH_GENS)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"subject_model": "granite-3.0-8b-q8", "generation": "granite-3.0-8b",
                             "mode": "BEM", "probe_idx": 999, "probe": "A probe not in the bank?",
                             "response": "x", "votes": SAFE_VOTES}) + "\n")
    *_, integ = ca.collect([str(p)], "mech")
    assert integ["unknown_probe"] == 1
    # completeness now off by one for that model -> hard fail (the tripwires compose)
    with pytest.raises(SystemExit):
        ca.integrity_check(integ)
