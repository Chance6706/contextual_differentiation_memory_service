"""Lock tests for the BLOCK-frame arms (BLOCK_PREREG.md).

Guards: the byte-frozen CDMS-D world-block fixture (arm C) — content sha (canonical, line-ending
normalized: the CRLF lesson from PR #118), layout facts (T1@378 preserved, persona fences intact,
world header + both fact lines present, no support-metadata leak into world lines); and the arm-B
(v2b) render — third-person header, filler layout stable under the variant.
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import redteam_claude_md_interference as R  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "docs" / "validation" / "runtime_instrument" / "blockframe" / "worldblock_fixture.txt"


def _norm(text: str) -> bytes:
    return text.replace("\r\n", "\n").encode("utf-8")


def test_worldblock_fixture_locked():
    text = FIXTURE.read_text(encoding="utf-8")
    # content sha over normalized newlines (platform-stable; PREREG manifest value)
    assert hashlib.sha256(_norm(text)).hexdigest() == \
        "8b54c73994d6a9fa5a8c96c43ec792cf093b6e67fd76d0f30b763be36657b830"


def test_worldblock_fixture_layout():
    text = FIXTURE.read_text(encoding="utf-8")
    # persona block byte-identical to the single arm (T1@378 preserved -> no position confound)
    assert text.find(R.MULTIFACT_TOKENS[0]) == 378
    assert "<memory:persona>" in text and "</memory:persona>" in text
    # -D world section present, both facts rendered by -D's native fact.render()
    assert "# World context (CDMS-D" in text
    assert "## User preferences and conventions (editable)" in text
    assert "- the services depend on cobalt_runtime [P]" in text
    assert "- the services run on mesa_framework [P]" in text
    # the world lines carry NO persona decoration (support metadata / exemplar) — the production
    # -D format; and the fillers appear ONLY in the world section (not in the persona block)
    world = text[text.index("# World context"):]
    persona = text[:text.index("# World context")]
    for tok in R.FILLER_TOKENS:
        assert tok in world and tok not in persona
    assert "(support" not in world
    # persona prefix is byte-identical to the freshly-built single-arm preamble
    with tempfile.TemporaryDirectory() as td:
        single = R._real_preamble_for_mode(R.setup_bem_multifact(1), Path(td), "v1")
    assert text.startswith(single)


def test_locked_analyzer_constants():
    """BLOCK_PREREG §4/§9 constants (pressure-test folds): the G-AVAIL floor, the corrected T1 band
    (p_T1/3, red-team S1), and the J0 tolerance are locked."""
    import blockframe_analyze as BA
    import blockframe_j0_check as J0
    assert BA.AVAIL_FLOOR == 0.30
    assert BA.T1_BAND == 0.071
    assert J0.TOL == 0.05
    assert J0.SENTINELS == ("granite-3.0-8b-q8", "mistral-g-v0.1")


def test_v2b_filler_render():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        v1 = R._real_preamble_for_mode(R.setup_bem_filler, Path(a), "v1")
        v2b = R._real_preamble_for_mode(R.setup_bem_filler, Path(b), "v2b")
    # v1 anchor layout (matches every prior filler epoch)
    assert v1.find(R.MULTIFACT_TOKENS[0]) == 378
    # v2b: third-person header replaces the self-frame header; same gists render
    assert "NOT about you" in v2b
    assert "What I've learned about this workspace/user" not in v2b
    for tok in (R.MULTIFACT_TOKENS[0],) + R.FILLER_TOKENS:
        assert tok in v2b
    # the bundle disclosure numbers (header shift): T1 moves with the longer header
    assert v2b.find(R.MULTIFACT_TOKENS[0]) == 486
