"""Lock + synthetic tests for the MULTIPLICITY-CONSERVATION ladder (CONSERVATION_PREREG.md).

Guards: the P3/P4 scaffold constants and their rendered byte-layout claims (renamed == triple modulo
tokens, replacement-T1@378; permuted = same line-set, T1@650); the P1 cache-key derivation (default
options MUST keep the legacy key so every committed epoch still reconstructs; non-default options MUST
change it, and the judge's reconstruction formula MUST reproduce the driver's); the analyzer's verdict
branches and band floor. The bank sha lock is appended at lock time (§9).
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import redteam_claude_md_interference as R  # noqa: E402
import conservation_analyze as CA  # noqa: E402


def test_conservation_constants_locked():
    assert R.CONSERVATION_TOKENS == ("limewater_feed", "saltmarsh_shard", "bayside_queue")
    assert R.PERMUTED_ORDER == (1, 2, 0)
    # byte-length match per token — the renamed preamble's positions depend on it
    for old, new in zip(R.MULTIFACT_TOKENS, R.CONSERVATION_TOKENS):
        assert len(old.encode()) == len(new.encode())
    # coined: replacement tokens must not collide with any other planted vocabulary
    assert not (set(R.CONSERVATION_TOKENS) & set(R.MULTIFACT_TOKENS))
    assert not (set(R.CONSERVATION_TOKENS) & set(R.FILLER_TOKENS))


def test_renamed_and_permuted_render_layout():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b, \
            tempfile.TemporaryDirectory() as c:
        p3 = R._real_preamble_for_mode(R.setup_bem_multifact(3), Path(a), "v1")
        pr = R._real_preamble_for_mode(R.setup_bem_renamed, Path(b), "v1")
        pp = R._real_preamble_for_mode(R.setup_bem_permuted, Path(c), "v1")
    # renamed: byte-identical to triple modulo the three token substitutions; positions preserved
    assert len(pr.encode()) == len(p3.encode())
    back = pr
    for new, old in zip(R.CONSERVATION_TOKENS, R.MULTIFACT_TOKENS):
        back = back.replace(new, old)
    assert back == p3
    assert pr.find(R.CONSERVATION_TOKENS[0]) == p3.find(R.MULTIFACT_TOKENS[0]) == 378
    # no old token may survive in the renamed render (G-FLOOR's static counterpart)
    for old in R.MULTIFACT_TOKENS:
        assert old not in pr
    # permuted: identical line-set, T1 demoted from slot 1 (@378) to slot 3 (@650)
    assert sorted(pp.splitlines()) == sorted(p3.splitlines())
    assert len(pp.encode()) == len(p3.encode())
    assert pp.find(R.MULTIFACT_TOKENS[0]) == 650
    # and the slot-1 occupant is the PERMUTED_ORDER[0] token at T1's old offset
    assert pp.find(R.MULTIFACT_TOKENS[R.PERMUTED_ORDER[0]]) == 378


def test_cache_key_derivation_default_and_opts(tmp_path):
    """ollama_chat's key: (a) defaults keep the LEGACY key (committed epochs must reconstruct);
    (b) non-default opts change it; (c) the judge-side formula reproduces the driver's exactly.
    Proven without network by pre-placing cache files at the derived paths."""
    model, system, user = "m1", "sys", "usr"
    legacy = hashlib.sha256(f"{model}\x00{system}\x00{user}".encode()).hexdigest()[:24]
    (tmp_path / f"{model}__{legacy}.json").write_text(json.dumps({"response": "LEGACY"}))
    assert R.ollama_chat(model, system, user, tmp_path) == "LEGACY"

    opts_tag = "opts:temp=0.7;seed=11"      # the exact judge-side reconstruction formula
    keyed = hashlib.sha256(f"{model}\x00{system}\x00{user}\x00{opts_tag}".encode()).hexdigest()[:24]
    assert keyed != legacy
    (tmp_path / f"{model}__{keyed}.json").write_text(json.dumps({"response": "SEEDED"}))
    assert R.ollama_chat(model, system, user, tmp_path, temperature=0.7, gen_seed=11) == "SEEDED"


@pytest.mark.parametrize("base,lb,ub,lo,hi,band,gated,expect", [
    (0.010, -0.030, 0.045, -0.040, 0.055, 0.061, True, "CONSERVED"),
    (0.100, 0.070, 0.130, 0.060, 0.140, 0.061, True, "BROKEN(+)"),
    (-0.100, -0.130, -0.070, -0.140, -0.060, 0.061, True, "BROKEN(-)"),
    (0.050, -0.010, 0.110, -0.020, 0.120, 0.061, True,
     "INCONCLUSIVE (margin straddle — not evidence either way)"),
    # significant but small: CI excludes 0 yet |D| <= band -> NOT broken (equivalence-consistent)
    (0.040, 0.010, 0.070, 0.005, 0.075, 0.061, True,
     "INCONCLUSIVE (margin straddle — not evidence either way)"),
    (0.010, -0.030, 0.045, -0.040, 0.055, 0.061, False, "WITHHELD (gate failed)"),
])
def test_verdict_branches(base, lb, ub, lo, hi, band, gated, expect):
    assert CA.verdict(base, lb, ub, lo, hi, band, gated) == expect


def test_p2_shaped_integrity_check():
    """Legituse pressure-test M1: the P2 arm (28 BEM + 32 recall per model) must PASS the analyzer's
    integrity check with expect_recall=32 and FAIL it with the default 16 — the exact defect the
    reviewer executed (EXPECT_RECALL hardcoded would SystemExit the headline-gating PRIMARY)."""
    from multifact_analyze import integrity_check, MECH_EXPECTED
    counts = {}
    models = set()
    for i, g in enumerate(sorted(MECH_EXPECTED)):
        m = f"{g}-q8"
        models.add(m)
        counts[(m, "BEM")] = 28
        counts[(m, "recall")] = 32
    c = {"models": models, "counts": counts, "expect_bem": 28,
         "generations": set(MECH_EXPECTED)}
    integrity_check(c, "mech", allow_incomplete=False, expect_recall=32)   # must not raise
    with pytest.raises(SystemExit):
        integrity_check(c, "mech", allow_incomplete=False)                 # default 16 -> hard fail


def test_bank_sha_locked():
    """The blind-authored paraphrase bank is LOCKED (CONSERVATION_PREREG §9); any edit is a NEW
    pre-registration."""
    p = Path(__file__).resolve().parent.parent / "tools" / "probes_conservation.py"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == \
        "ce8d56492d768e30acd0f96eb237f24c10443241374bf6580b4a4771646c4d07"
    import probes_conservation as pc
    import probes_sp_expansion as spx
    assert pc.REPRO_FACETS == spx.REPRO_FACETS
    assert pc.EXPECT_BEM == 28
    assert len(pc.PROBES) == 7 and all(len(v) == 3 for v in pc.REPHRASINGS.values())


def test_band_floor_refused(tmp_path):
    out = tmp_path / "x.jsonl"
    out.write_text("")
    argv = ["conservation_analyze.py", "--anchor", str(out), "--band", "0.05"]
    old = sys.argv
    sys.argv = argv
    try:
        with pytest.raises(SystemExit) as e:
            CA.main()
        assert "below the pre-registered floor" in str(e.value)
    finally:
        sys.argv = old


def test_band_above_floor_requires_approval(tmp_path):
    """Pressure-test M3: an above-floor band must not silently widen CONSERVED — it needs the
    explicit human-review flag."""
    out = tmp_path / "x.jsonl"
    out.write_text("")
    old = sys.argv
    try:
        sys.argv = ["conservation_analyze.py", "--anchor", str(out), "--band", "0.09"]
        with pytest.raises(SystemExit) as e:
            CA.main()
        assert "band-above-floor-approved" in str(e.value)
        # with the approval flag it proceeds past the band guard (and fails later on the empty
        # anchor file instead — any non-band error proves the guard released)
        sys.argv = ["conservation_analyze.py", "--anchor", str(out), "--band", "0.09",
                    "--band-above-floor-approved"]
        with pytest.raises(BaseException) as e2:
            CA.main()
        assert "band-above-floor-approved" not in str(e2.value)
    finally:
        sys.argv = old


def test_band_file_artifact(tmp_path):
    """Pressure-test S2/S7: the analyzer consumes the P0 band artifact; --band-file + --band together
    are refused (no silent precedence)."""
    art = tmp_path / "P0_BAND.json"
    art.write_text(json.dumps({"band": 0.061, "sigma_multiplicity": 0.0, "halt": False}))
    out = tmp_path / "x.jsonl"
    out.write_text("")
    old = sys.argv
    try:
        sys.argv = ["conservation_analyze.py", "--anchor", str(out),
                    "--band-file", str(art), "--band", "0.061"]
        with pytest.raises(SystemExit) as e:
            CA.main()
        assert "mutually exclusive" in str(e.value)
        sys.argv = ["conservation_analyze.py", "--anchor", str(out), "--band-file", str(art)]
        with pytest.raises(BaseException) as e2:
            CA.main()   # proceeds past band handling; fails on the empty anchor file
        assert "mutually exclusive" not in str(e2.value)
    finally:
        sys.argv = old
