"""Lock guard for the clean-strata pre-registration (CLEANSTRATA_PREREG.md §13).

The bank and its blind classification are LOCKED: any edit to tools/probes_cleanstrata.py that
changes probe text, rephrasings, or class assignments breaks the sha256s below and fails this
test — the intended tripwire. If the bank must legitimately change (it shouldn't, post-lock),
that is a NEW pre-registration, not an edit.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from probes_cleanstrata import (  # noqa: E402
    PROBES_CLEANSTRATA, REPHRASINGS_CLEANSTRATA, FACET_OF_CLEANSTRATA, CLASS_OF_CLEANSTRATA)

BANK_SHA = "22f86a9ce24251d2dae1dc4473d624b577a8691c63f22083df7acaa821e92bad"
CLASS_SHA = "803356c202fb3f2f0cbb345d5d2dae73d1105ebeafee56ca7657a2dcb09a4cf2"


def _canon(o):
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def test_bank_hash_locked():
    got = hashlib.sha256(_canon({
        "probes": list(PROBES_CLEANSTRATA),
        "reph": {str(i): v for i, v in REPHRASINGS_CLEANSTRATA.items()},
    }).encode()).hexdigest()
    assert got == BANK_SHA, "probes_cleanstrata.py bank text changed post-lock"


def test_classification_hash_locked():
    got = hashlib.sha256(_canon(dict(CLASS_OF_CLEANSTRATA)).encode()).hexdigest()
    assert got == CLASS_SHA, "CLASS_OF_CLEANSTRATA changed post-lock"


def test_bank_structure():
    assert len(PROBES_CLEANSTRATA) == 65
    assert set(REPHRASINGS_CLEANSTRATA) == set(range(65))
    assert all(len(v) == 1 for v in REPHRASINGS_CLEANSTRATA.values())
    assert set(FACET_OF_CLEANSTRATA) == set(range(65))
    counts = {}
    for f in FACET_OF_CLEANSTRATA.values():
        counts[CLASS_OF_CLEANSTRATA[f]] = counts.get(CLASS_OF_CLEANSTRATA[f], 0) + 1
    assert counts == {"SP": 16, "ID": 20, "PROC": 29}
    # facet ids unique (one facet per original — single-probed by design)
    assert len(set(FACET_OF_CLEANSTRATA.values())) == 65


def test_attribution_audit_clean():
    """CLEANSTRATA_PREREG §4a — the bait-echo constraints, kept as a permanent regression guard:
    no second-person content attribution, no planted-token/preamble vocabulary, no imperative bait
    (the CDMS-D powered battery measured one assistant-attributed sentence at +52pp adoption)."""
    attr = re.compile(r"\b(you|you've|you have|your)\s+(wrote|written|built|created|authored|made|"
                      r"designed|refactored|shipped|coded|implemented|developed|maintained)\b", re.I)
    own = re.compile(r"\byou\s+own(ed)?\s+\w+|\byour\s+(project|module|repo|codebase|library|tool|system|app)\b", re.I)
    toks = re.compile(r"starboard|quartz|meridian|handles_well|giraffe", re.I)
    imper = re.compile(r"\b(admit|confess|claim|acknowledge)\b", re.I)
    texts = list(PROBES_CLEANSTRATA) + [r for v in REPHRASINGS_CLEANSTRATA.values() for r in v]
    assert len(texts) == 130
    for t in texts:
        for rx in (attr, own, toks, imper):
            assert not rx.search(t), f"attribution-audit hit in probe: {t!r}"
        assert 8 <= len(t.split()) <= 30, f"length band violated: {t!r}"
