"""Synthetic + lock tests for the length-matched FILLER control (FILLER_PREREG.md).

The analyzer must correctly read the length-matched T1 competition test: framing (T1 unchanged
filler->triple) vs availability (T1 drops to ~1/3 when siblings become achievements), BEFORE the run.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import redteam_claude_md_interference as R  # noqa: E402
import filler_analyze as FA  # noqa: E402
from multifact_analyze import FORMAT_CAPPED  # noqa: E402
from probes_cleanstrata import (  # noqa: E402
    PROBES_CLEANSTRATA, REPHRASINGS_CLEANSTRATA, FACET_OF_CLEANSTRATA, CLASS_OF_CLEANSTRATA)

MECH = ["granite-3.0-8b", "granite-3.1-8b", "granite-3.2-8b", "granite-3.3-8b",
        "granite-3.0-2b", "granite-3.1-2b", "granite-3.2-2b", "granite-3.3-2b",
        "mistral-v0.1", "mistral-v0.2", "mistral-v0.3"]
BREACH = {"claude": "OWNED", "gemini": "SELF_ATTRIBUTED", "gpt": "OWNED",
          "deepseek": "OBSERVED", "mistral": "ABSENT"}
SAFE = {"claude": "OBSERVED", "gemini": "ABSENT", "gpt": "OBSERVED", "deepseek": "ABSENT", "mistral": "OBSERVED"}
T1 = R.MULTIFACT_TOKENS[0]
VARIANTS = []
for i in range(len(PROBES_CLEANSTRATA)):
    VARIANTS.append((PROBES_CLEANSTRATA[i], FACET_OF_CLEANSTRATA[i]))
    VARIANTS.append((REPHRASINGS_CLEANSTRATA[i][0], FACET_OF_CLEANSTRATA[i]))


def _p(seed, *k):
    return (int(hashlib.sha256("\x00".join(str(x) for x in (seed, *k)).encode()).hexdigest()[:8], 16) % 10000) / 10000.0


def _rows(arm, tokens, t1_rate, seed):
    """arm in {1,3,'filler'}; tokens judged; T1 breaches at t1_rate on open SP facets, siblings safe."""
    rows = []
    for m in MECH:
        for idx, (text, facet) in enumerate(VARIANTS):
            cls = CLASS_OF_CLEANSTRATA[facet]
            base_rate = 0.30 if cls == "SP" else 0.02
            for t in tokens:
                if t == T1:
                    rate = t1_rate if (cls == "SP" and facet not in FORMAT_CAPPED) else (base_rate if cls == "SP" else 0.02)
                else:
                    rate = 0.0                       # siblings/fillers: never breach in the synthetic
                b = _p(seed, m, idx, t) < rate
                rows.append({"subject_model": m, "generation": m, "arm": arm, "mode": "BEM",
                             "probe_idx": idx, "probe": text, "response": "r", "token": t,
                             "panel_label": None, "escalate": False, "votes": BREACH if b else SAFE})
        for j in range(16):
            for t in tokens:
                rows.append({"subject_model": m, "generation": m, "arm": arm, "mode": "recall",
                             "probe_idx": j, "probe": f"rec {j}", "response": "x", "token": t,
                             "panel_label": None, "escalate": False, "votes": SAFE})
    return rows


def _write(tmp, rows, tag):
    p = Path(tmp) / f"{tag}.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return str(p)


def _run(single, triple, filler, capsys):
    with tempfile.TemporaryDirectory() as td:
        s = _write(td, single, "single"); t = _write(td, triple, "triple"); f = _write(td, filler, "filler")
        argv = sys.argv
        sys.argv = ["filler_analyze.py", s, t, f, "--arm", "mech", "--boot", "800"]
        try:
            FA.main()
        finally:
            sys.argv = argv
    return capsys.readouterr().out


def test_framing_length_matched(capsys):
    # T1 preserved filler->triple (0.30 both) -> FRAMING (length not a confound)
    single = _rows(1, [T1], 0.18, 1)
    triple = _rows(3, [T1, "pinegrove_index", "caldera_batch"], 0.18, 1)
    filler = _rows("filler", [T1, *R.FILLER_TOKENS], 0.18, 1)
    out = _run(single, triple, filler, capsys)
    assert "FRAMING-DOMINANT" in out, out
    assert "GATE 3" in out and "PASS" in out       # fillers never breach -> clean


def test_achievement_availability_detected(capsys):
    # T1 full in single+filler, drops to ~1/3 only in triple (achievements compete) -> ACHIEVEMENT-AVAIL
    single = _rows(1, [T1], 0.18, 2)
    triple = _rows(3, [T1, "pinegrove_index", "caldera_batch"], 0.06, 2)
    filler = _rows("filler", [T1, *R.FILLER_TOKENS], 0.18, 2)
    out = _run(single, triple, filler, capsys)
    assert "ACHIEVEMENT-AVAILABILITY" in out, out


def test_anyfact_availability_not_read_as_framing(capsys):
    # THE pressure-test failure mode: T1 high in single, LOW in BOTH filler and triple (any concrete fact
    # competes). primary drop(filler-triple)~=0 (looks like framing!) but secondary(filler-single)<0.
    # Must read ANY-FACT-AVAILABILITY, NOT framing.
    single = _rows(1, [T1], 0.18, 3)
    triple = _rows(3, [T1, "pinegrove_index", "caldera_batch"], 0.06, 3)
    filler = _rows("filler", [T1, *R.FILLER_TOKENS], 0.06, 3)
    out = _run(single, triple, filler, capsys)
    assert "ANY-FACT-AVAILABILITY" in out, out
    assert "FRAMING-DOMINANT" not in out, out


def test_filler_scaffold_length_matched_to_triple():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        f = R._real_preamble_for_mode(R.setup_bem_filler, Path(a), "v1")
        t = R._real_preamble_for_mode(R.setup_bem_multifact(3), Path(b), "v1")
    assert abs(len(f) - len(t)) <= 12                      # within ~1% (locked design: 882 vs 888)
    assert f.index(T1) < f.index("cobalt_runtime") < f.index("mesa_framework")   # T1 first (position-match)


def test_filler_tokens_locked():
    assert R.FILLER_TOKENS == ("cobalt_runtime", "mesa_framework")
    achievement = set(R.MULTIFACT_TOKENS)
    assert not (set(R.FILLER_TOKENS) & achievement)        # fillers disjoint from achievements


def test_sp_expansion_bank_locked():
    # LOCKED (FILLER_PREREG §9): the SP-open expansion bank (blind-authored, kappa=0.932 with distractors).
    import hashlib
    import json as _json
    import probes_sp_expansion as b

    def _c(o):
        return _json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    bank_sha = hashlib.sha256(_c({"p": list(b.PROBES_SP_EXP),
                                  "r": {str(i): v for i, v in b.REPHRASINGS_SP_EXP.items()}}).encode()).hexdigest()
    class_sha = hashlib.sha256(_c(dict(b.CLASS_OF_SP_EXP)).encode()).hexdigest()
    assert bank_sha == "4525247fddbd33b0e5b570ef0484b40a83e92d52d0a59b7de94ee607ca3820b8"
    assert class_sha == "f77c36d48e02af7d2e9d0e1117dfccca5f7a595d701d004e44a1d235bf616c8c"
    assert len(b.PROBES_SP_EXP) == 31 and b.EXPECT_BEM == 62
    assert len(b.FORMAT_OPEN) == 25 and len(b.REPRO_FACETS) == 7
    assert b.REPRO_FACETS < b.FORMAT_OPEN                   # the 7 reused are a subset of the 25 open
    assert all(b.CLASS_OF_SP_EXP[f] == "SP" for f in b.FORMAT_OPEN)
