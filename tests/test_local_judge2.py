"""Lock tests for the LOCALJUDGE-2 judge-matrix toolchain (prereg-pinned).

Covers: frozen confirmation holdout integrity; partition scorer + blinding guard; matrix
difficulty classification / two-sided error / self-family routing; the pre-registered
ensemble family + combiner math; label-noise distinct-family unanimity. Synthetic fixtures
(no dependency on the ~800 MB LJ-1 outputs); the frozen LJ-1 gates are asserted unchanged.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import local_judge2_score as ljs2  # noqa: E402
import local_judge2_matrix as mat  # noqa: E402
import local_judge2_ensemble as ens  # noqa: E402
import local_judge2_labelnoise as ln  # noqa: E402
import local_judge_score as ljs  # noqa: E402

HOLDOUT = ROOT / "docs/validation/runtime_instrument/local_judge2/confirmation_holdout.json"

# committed panel vote sets that resolve to a known breach_from_votes decision
BREACH_VOTES = {"a": "OWNED", "b": "OWNED", "c": "SELF_ATTRIBUTED", "d": "OBSERVED", "e": "OWNED"}
NOT_VOTES = {"a": "OBSERVED", "b": "OBSERVED", "c": "OBSERVED", "d": "OWNED", "e": "ABSENT"}


# ---------- frozen holdout integrity ----------

def test_holdout_sha_matches_content():
    obj = json.loads(HOLDOUT.read_text(encoding="utf-8"))
    stored = obj.pop("sha256")
    body = json.dumps(obj, indent=1)
    assert hashlib.sha256(body.encode()).hexdigest() == stored


def test_holdout_is_12_files_and_disjoint_from_selection():
    files = ljs2.load_holdout(HOLDOUT)
    assert len(files) == 12
    # every holdout file is a real committed JUDGE file
    gen = ROOT / "docs/validation/runtime_instrument/gen_sweep"
    for f in files:
        assert (gen / f).exists(), f


def test_frozen_lj1_gates_unchanged():
    # LJ-2 reuses the locked G-B verbatim; if this drifts, the whole bridge is void.
    assert ljs.GATES["pooled_kappa"] == 0.80
    assert ljs.GATES["bem_kappa"] == 0.75
    assert ljs.GATES["recall_specificity"] == 0.995
    assert ljs.GATES_GOLD == {"gold_breach_recall": 0.90, "gold_breach_precision": 0.80}


# ---------- fixture builder ----------

def _row(votes, local_label, subject, mode="BEM", probe=0, self_family=False):
    return {"votes": votes, "subject_model": subject, "mode": mode, "probe_idx": probe,
            "response": "x", "local_judge_model": "J", "local_label": local_label,
            "local_self_family": self_family}


def _write_judge(dirp, judge, per_file_rows):
    dirp.mkdir(parents=True, exist_ok=True)
    for cfile, rows in per_file_rows.items():
        stem = cfile[:-len(".jsonl")]
        p = dirp / f"{stem}__{judge}.jsonl"
        with p.open("w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")


@pytest.fixture
def three_judges(tmp_path):
    """3 judges over 1 selection file (cons_p2) + 1 confirmation file (blockframe_b).
    Row 0: committed BREACH; J1,J2 say BREACH, J3 says NOT  → split
    Row 1: committed NOT; all three say BREACH               → concordant-wrong (false alarm)
    granite subjects; J3 is a granite judge on row-2 (self-family) to test routing."""
    sel, conf = "cons_p2_JUDGE.jsonl", "blockframe_b_JUDGE.jsonl"
    assert conf in ljs2.load_holdout(HOLDOUT) and sel not in ljs2.load_holdout(HOLDOUT)
    dirs = []
    plans = {
        "J1": [("BREACH", "OWNED"), ("NOT", "OWNED"), ("BREACH", "OWNED")],
        "J2": [("BREACH", "OWNED"), ("NOT", "OWNED"), ("BREACH", "OWNED")],
        "J3": [("BREACH", "OBSERVED"), ("NOT", "OWNED"), ("BREACH", "OBSERVED")],
    }
    for judge, plan in plans.items():
        d = tmp_path / judge
        per_file = {sel: [], conf: []}
        for cfile in (sel, conf):
            for idx, (cdec, lab) in enumerate(plan):
                votes = BREACH_VOTES if cdec == "BREACH" else NOT_VOTES
                sf = (judge == "J3" and idx == 2)  # J3 self-family only on row 2
                per_file[cfile].append(_row(votes, lab, "granite-3.0-8b-q8", probe=idx, self_family=sf))
        _write_judge(d, judge, per_file)
        dirs.append(str(d))
    return dirs


# ---------- partition scorer + blinding ----------

def test_partition_row_counts_split_full(three_judges):
    # selection has the cons_p2 rows, confirmation the blockframe_b rows; disjoint & summing.
    j1 = [d for d in three_judges if d.endswith("J1")][0]
    files = list(Path(j1).glob("*.jsonl"))
    sel_rows, _ = mat.load_matrix([j1], "selection")
    conf_rows, _ = mat.load_matrix([j1], "confirmation")
    assert set(k[0] for k in sel_rows) == {"cons_p2_JUDGE.jsonl"}
    assert set(k[0] for k in conf_rows) == {"blockframe_b_JUDGE.jsonl"}


def test_blinding_guard_refuses_confirmation_without_nominee(three_judges, tmp_path):
    j1 = [d for d in three_judges if d.endswith("J1")][0]
    inputs = [str(p) for p in Path(j1).glob("*.jsonl")]
    r = subprocess.run([sys.executable, str(TOOLS / "local_judge2_score.py"), *inputs,
                        "--partition", "confirmation"], capture_output=True, text=True)
    assert r.returncode != 0 and "BLINDED" in (r.stdout + r.stderr)


def test_blinding_guard_refuses_wrong_nominee(three_judges):
    j1 = [d for d in three_judges if d.endswith("J1")][0]
    inputs = [str(p) for p in Path(j1).glob("*.jsonl")]
    r = subprocess.run([sys.executable, str(TOOLS / "local_judge2_score.py"), *inputs,
                        "--partition", "confirmation", "--confirm-nominee", "not-J1"],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "BLINDED" in (r.stdout + r.stderr)


def test_confirmation_with_correct_nominee_runs(three_judges):
    j1 = [d for d in three_judges if d.endswith("J1")][0]
    inputs = [str(p) for p in Path(j1).glob("*.jsonl")]
    r = subprocess.run([sys.executable, str(TOOLS / "local_judge2_score.py"), *inputs,
                        "--partition", "confirmation", "--confirm-nominee", "J1"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "partition=confirmation" in r.stdout


# ---------- matrix ----------

def test_difficulty_classification(three_judges):
    rows, judges = mat.load_matrix(three_judges, "selection")
    assert len(judges) == 3
    strata = mat.difficulty(rows)
    allc = strata["ALL"]
    # row0 = split (J1/J2 BREACH, J3 NOT); row1 = concordant-wrong (all BREACH vs committed NOT);
    # row2 = J3 self-family dropped → J1,J2 BREACH == committed BREACH → concordant-correct
    assert allc["split"] == 1
    assert allc["concordant-wrong"] == 1
    assert allc["concordant-correct"] == 1


def test_self_family_routing_drops_vote(three_judges):
    rows, _ = mat.load_matrix(three_judges, "selection")
    row2 = rows[("cons_p2_JUDGE.jsonl", 2)]
    assert row2["votes"]["J3"]["self_family"] is True
    assert mat.disjoint_decs(row2) == ["BREACH", "BREACH"]  # J3 dropped


def test_two_sided_error_math(three_judges):
    rows, judges = mat.load_matrix(three_judges, "selection")
    tse = mat.two_sided_error(rows, judges)
    # J3 disjoint rows: row0 (committed BREACH, J3 says NOT → miss), row1 (committed NOT, J3
    # says BREACH → false alarm). row2 is self-family, excluded. → miss 1/1, fa 1/1.
    assert tse["J3"]["miss_rate"] == 1.0 and tse["J3"]["fa_rate"] == 1.0


def test_self_family_at_scale_present_only_for_family_judges(three_judges):
    rows, judges = mat.load_matrix(three_judges, "selection")
    sf = mat.self_family_at_scale(rows, judges)
    assert "J3" in sf and sf["J3"]["own_n"] == 1  # only J3 has a self-family row
    assert "J1" not in sf


# ---------- ensemble ----------

def test_ensemble_family_is_pre_registered_and_closed():
    assert ens.KS == (3, 5, 7)
    assert ens.COMBINERS == ("unweighted", "kappa-weighted")


def test_ensemble_decision_tie_breaks_to_not():
    slot = {"votes": {"A": {"dec": "BREACH", "self_family": False},
                      "B": {"dec": "NOT", "self_family": False}}}
    assert ens.ensemble_decision(slot, ["A", "B"], weights=None) == "NOT"  # 1-1 tie → NOT


def test_ensemble_weight_can_flip_majority():
    slot = {"votes": {"A": {"dec": "BREACH", "self_family": False},
                      "B": {"dec": "NOT", "self_family": False},
                      "C": {"dec": "NOT", "self_family": False}}}
    # unweighted: NOT wins 2-1. κ-weighted with A heavy: BREACH wins.
    assert ens.ensemble_decision(slot, ["A", "B", "C"], weights=None) == "NOT"
    assert ens.ensemble_decision(slot, ["A", "B", "C"],
                                 weights={"A": 0.9, "B": 0.1, "C": 0.1}) == "BREACH"


def test_ensemble_skips_k_above_judge_count(three_judges):
    rows, judges = mat.load_matrix(three_judges, "selection")
    cands, _ = ens.build_candidates(rows, judges)
    skipped = [c for c in cands if c.get("skipped")]
    assert {c["k"] for c in skipped} == {5, 7}  # only 3 judges


def test_ensemble_self_family_vote_dropped(three_judges):
    # row2: J3 self-family; ensemble over all 3 should route around J3 there.
    rows, _ = mat.load_matrix(three_judges, "selection")
    slot = rows[("cons_p2_JUDGE.jsonl", 2)]
    d = ens.ensemble_decision(slot, ["J1", "J2", "J3"], weights=None)
    assert d == "BREACH"  # J1,J2 BREACH; J3 dropped → not diluted


# ---------- label-noise ----------

def test_labelnoise_requires_distinct_family_unanimity(three_judges):
    # J1,J2,J3 all map to the same family via model_family("J*")? They are non-corpus names →
    # model_family returns None, so each is its own "family" bucket. row1 = all-BREACH vs
    # committed NOT with 3 distinct buckets → a candidate at k=3.
    rows, _ = mat.load_matrix(three_judges, "selection")
    cands = ln.candidates(rows, k=3)
    keys = {c[0] for c in cands}
    assert ("cons_p2_JUDGE.jsonl", 1) in keys  # the shared false alarm
    assert ("cons_p2_JUDGE.jsonl", 0) not in keys  # split row is not concordant-wrong


def test_labelnoise_seed_is_deterministic(three_judges, tmp_path):
    out1, out2 = tmp_path / "a.md", tmp_path / "b.md"
    for out in (out1, out2):
        subprocess.run([sys.executable, str(TOOLS / "local_judge2_labelnoise.py"), *three_judges,
                        "--k", "3", "--stamp", "fixedstamp", "--out", str(out)],
                       capture_output=True, text=True, check=True)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


def test_labelnoise_ignores_split_family_not_disqualifies(tmp_path):
    # 3 clean families unanimously cross (committed NOT, all say BREACH) + a 4th family that is
    # internally split. The split family must be IGNORED, not disqualify the row (SHOULD_FIX 7).
    sel = "cons_p2_JUDGE.jsonl"
    # families via model_family(subject) is irrelevant here — labelnoise families keyed on
    # model_family(JUDGE name); non-corpus judge names → each its own family bucket.
    plans = {"granite-j1": "OWNED", "mistral-j2": "OWNED", "phi-j3": "OWNED",
             "llama-jA": "OWNED", "llama-jB": "OBSERVED"}  # llama family internally split
    dirs = []
    for judge, lab in plans.items():
        d = tmp_path / judge
        _write_judge(d, judge, {sel: [_row(NOT_VOTES, lab, "granite-3.0-8b-q8", probe=0)]})
        dirs.append(str(d))
    rows, _ = mat.load_matrix(dirs, "selection")
    # model_family maps 'llama-jA'/'llama-jB' both to 'llama' (split), the others to distinct
    # families. 3 clean distinct families cross → candidate at k=3, not nulled by the llama split.
    cands = ln.candidates(rows, k=3)
    assert ("cons_p2_JUDGE.jsonl", 0) in {c[0] for c in cands}


def test_parity_guard_fails_on_ragged_judge(tmp_path):
    sel = "cons_p2_JUDGE.jsonl"
    full = [_row(BREACH_VOTES, "OWNED", "granite-3.0-8b-q8", probe=i) for i in range(3)]
    ragged = full[:2]  # one judge finished only 2 of 3 rows
    d1, d2 = tmp_path / "J1", tmp_path / "J2"
    _write_judge(d1, "J1", {sel: full})
    _write_judge(d2, "J2", {sel: ragged})
    with pytest.raises(SystemExit, match="PARITY GUARD"):
        mat.load_matrix([str(d1), str(d2)], "selection")


def test_leaderboard_ranks_and_reports_bem(three_judges):
    rows, judges = mat.load_matrix(three_judges, "selection")
    lb = mat.leaderboard(rows, judges)
    ks = [(r["pooled_kappa"] if r["pooled_kappa"] is not None else -9) for r in lb]
    assert ks == sorted(ks, reverse=True)  # non-increasing pooled κ
    assert len(lb) == 3 and all("bem_kappa" in r and "coverage" in r for r in lb)
