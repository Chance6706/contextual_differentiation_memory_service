"""Lock tests for the DISAMBIG ladder (DISAMBIG_PREREG.md).

Guards: the two CONSTRUCTED intermediate fixtures (M neutral-header / H -D-header) — content shas
(normalized newlines), layout facts (T1@378, persona prefix byte-identical to the committed
worldblock fixture's, fillers only in the tail section, persona-format filler lines byte-copied
from the A anchor render), the byte-length match between the M and H header slots, the M fixture's
absence of every de-attribution marker, and the locked analyzer constants.
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import redteam_claude_md_interference as R  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
BF = REPO / "docs" / "validation" / "runtime_instrument" / "blockframe"


def _norm(text: str) -> bytes:
    return text.replace("\r\n", "\n").encode("utf-8")


def _read(name: str) -> str:
    return (BF / name).read_text(encoding="utf-8").replace("\r\n", "\n")


def test_fixture_shas_locked():
    for key, (fn, want) in R.DISAMBIG_FIXTURES.items():
        got = hashlib.sha256(_norm((BF / fn).read_text(encoding="utf-8"))).hexdigest()
        assert got == want, f"{key}: {got}"


def test_loader_asserts():
    # the loader is the single seam generation AND judge use — it must return the same bytes
    for key in R.DISAMBIG_FIXTURES:
        assert R.load_disambig_fixture(key).replace("\r\n", "\n") == _read(R.DISAMBIG_FIXTURES[key][0])


def test_layouts():
    wb = _read("worldblock_fixture.txt")
    m, h = _read("disambig_m_fixture.txt"), _read("disambig_h_fixture.txt")
    prefix = wb[:wb.index("# World context")]
    for text in (m, h):
        # persona prefix byte-identical to the committed composite fixture (=> T1@378 preserved)
        assert text.startswith(prefix)
        assert text.find(R.MULTIFACT_TOKENS[0]) == 378
        # persona-format filler lines present, and ONLY in the tail section
        tail = text[len(prefix):]
        persona = text[:len(prefix)]
        for tok in R.FILLER_TOKENS:
            assert tok in tail and tok not in persona
        assert '- P depends on cobalt_runtime  (support 10, seen 10x)' in tail
        assert 'e.g. "the services depend on the cobalt_runtime' in tail
        # NOT the -D one-liner format
        assert "[P]" not in text
    # M and H are byte-length-identical and differ ONLY in the header slot
    assert len(m.encode()) == len(h.encode()) == 1332
    f0_m, f0_h = m.index("- P depends on"), h.index("- P depends on")
    assert m[f0_m:] == h[f0_h:]                     # identical fact tails
    assert m[:len(prefix)] == h[:len(prefix)]       # identical persona prefixes
    # H's header slot is the byte-exact -D header block from the committed fixture
    d_header = wb[wb.index("# World context"):wb.index("- the services depend on")]
    assert d_header in h and d_header not in m
    # M's header carries NO de-attribution / -D markers (the whole point of the rung)
    for marker in ("NOT about the assistant", "read-only for assistant", "retrieve_world",
                   "CDMS-D", "editable"):
        assert marker not in m, marker


def test_filler_lines_match_anchor_render():
    with tempfile.TemporaryDirectory() as td:
        a = R._real_preamble_for_mode(R.setup_bem_filler, Path(td), "v1").replace("\r\n", "\n")
    filler_block = a[a.index("- P depends on cobalt_runtime"):a.index("</memory:persona>")]
    m = _read("disambig_m_fixture.txt")
    assert filler_block in m


def test_locked_analyzer_constants():
    import disambig_analyze as DA
    assert DA.NULL_BAND == 0.037
    assert DA.T1_BAND == 0.071
    assert DA.AVAIL_FLOOR == 0.30
    assert DA.DRIFT_WARN == 0.05
