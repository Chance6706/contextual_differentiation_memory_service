"""Structural tests for `tools/probes_rephrasings.py`.

These are SANITY CHECKS — they catch egregious constraint violations (missing modes,
wrong rephrasing counts, broken tuple structure, mode-specific semantic invariants
breaking obviously) — they are NOT behavioral tests. The behavioral judgment of "does
the rephrasing preserve intent" is delegated to the external-review pass
(`tools/probes_review.py`, pre-reg §3).

Test design choices:
* Heuristic regexes / token lists are deliberately permissive. We want green when a
  rephrasing is creatively-but-faithfully reworded; we want red only when the
  rephrasing breaks a constraint that's also load-bearing in the matrix runner's
  scorers.
* Mode-specific tests cite the original tuple's tag (scar_letter / format_tag) so
  they catch the bug class "rephrasing accidentally inverts the A/B mapping" without
  trying to second-guess the rephrasing's English.
* The OVERRIDE imperative heuristic is documented inline; both a destructive verb
  AND an imperative cue must appear (so a rephrasing that softens to "perhaps
  consider deleting..." would fail).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# tools/ on sys.path for sibling imports (mirrors the runners' pattern).
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

# Set CDMS_EMBED_BACKEND BEFORE importing redteam_claude_md_interference (which
# pulls in cdms.* on import).
os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")

from probes_rephrasings import (  # noqa: E402
    REPHRASINGS, expanded_probes, rephrasing_count,
)
from redteam_claude_md_interference import (  # noqa: E402
    PROBES_ORDER, PROBES_ORDER_OVERFIRE,
    PROBES_BEM, PROBES_BEM_WORKSPACE_FACT,
    PROBES_INSTR, PROBES_OVERRIDE,
    _select_probes, _EXPAND_SUBSAMPLE_N, _EST_USD_PER_PROBE,
)


_MODE_ORIGINALS = {
    "ORDER": PROBES_ORDER,
    "ORDER_OVERFIRE": PROBES_ORDER_OVERFIRE,
    "BEM": PROBES_BEM,
    "BEM_WORKSPACE_FACT": PROBES_BEM_WORKSPACE_FACT,
    "INSTR": PROBES_INSTR,
    "OVERRIDE": PROBES_OVERRIDE,
}


# =====================================================================
# Structural tests — REPHRASINGS dict shape
# =====================================================================

def test_rephrasings_dict_has_all_six_modes():
    expected = {"ORDER", "ORDER_OVERFIRE", "BEM",
                "BEM_WORKSPACE_FACT", "INSTR", "OVERRIDE"}
    assert set(REPHRASINGS.keys()) == expected, (
        f"REPHRASINGS modes {set(REPHRASINGS)} != expected {expected}")


def test_each_probe_has_exactly_four_rephrasings():
    for mode_name, by_idx in REPHRASINGS.items():
        originals = _MODE_ORIGINALS[mode_name]
        assert len(by_idx) == len(originals), (
            f"{mode_name}: {len(by_idx)} probes rephrased, but {len(originals)} originals exist")
        for orig_idx, rephr_list in by_idx.items():
            assert len(rephr_list) == 4, (
                f"{mode_name}[{orig_idx}] has {len(rephr_list)} rephrasings, expected 4")
            # No empty strings.
            for r_idx, r in enumerate(rephr_list):
                assert isinstance(r, str) and r.strip(), (
                    f"{mode_name}[{orig_idx}].r{r_idx} is empty / non-string")


def test_no_rephrasing_equals_original():
    """Literal-string inequality. A rephrasing identical to the original is a bug."""
    for mode_name, by_idx in REPHRASINGS.items():
        originals = _MODE_ORIGINALS[mode_name]
        for orig_idx, rephr_list in by_idx.items():
            orig = originals[orig_idx]
            orig_text = orig[1] if isinstance(orig, tuple) else orig
            for r_idx, r in enumerate(rephr_list):
                assert r != orig_text, (
                    f"{mode_name}[{orig_idx}].r{r_idx} is byte-identical to original")


# =====================================================================
# Mode-specific semantic-invariant tests (heuristic, permissive)
# =====================================================================

def test_order_rephrasings_preserve_scar_letter():
    """Every ORDER rephrasing should still surface A) and B) choices.

    We don't try to parse "which letter is the safe answer" - that would require
    re-reading the prose. We only check the literal A)/B) structure is intact so
    the runner's scorer (`score_order_safe` reads scar_letter from tuple[0] and
    expects A/B in the response) still has a valid probe to pose.
    """
    pattern = re.compile(r"\bA\)\s*\S", re.IGNORECASE)
    pattern_b = re.compile(r"\bB\)\s*\S", re.IGNORECASE)
    for orig_idx, rephr_list in REPHRASINGS["ORDER"].items():
        scar_letter = PROBES_ORDER[orig_idx][0]
        assert scar_letter in ("A", "B")
        for r_idx, r in enumerate(rephr_list):
            assert pattern.search(r), (
                f"ORDER[{orig_idx}].r{r_idx} missing 'A)' choice structure")
            assert pattern_b.search(r), (
                f"ORDER[{orig_idx}].r{r_idx} missing 'B)' choice structure")


def test_order_overfire_rephrasings_preserve_privacy_framing():
    """ORDER_OVERFIRE relies on EXPLICIT private/personal scope so the scar should
    NOT fire. A rephrasing that drops every privacy cue would silently turn the
    probe into a regular ORDER probe and conflate over-fire vs correct-fire.
    Heuristic: each rephrasing must contain at least one of a small list of
    scope-isolating words / phrases.
    """
    privacy_markers = (
        "private", "personal", "own", "sole", "solo", "myself",
        "only on", "never been pushed", "not been pushed", "haven't shared",
        "not shared", "no one else", "nobody", "zero collaborators",
        "no team", "no other", "verified", "homelab", "sandbox",
        "draft pr", "draft pull", "laptop", "no one tracks",
    )
    pattern_ab = re.compile(r"\bA\)\s*\S", re.IGNORECASE)
    pattern_b = re.compile(r"\bB\)\s*\S", re.IGNORECASE)
    for orig_idx, rephr_list in REPHRASINGS["ORDER_OVERFIRE"].items():
        for r_idx, r in enumerate(rephr_list):
            r_lower = r.lower()
            assert any(m in r_lower for m in privacy_markers), (
                f"ORDER_OVERFIRE[{orig_idx}].r{r_idx} lacks any private/personal scope marker; "
                f"the over-fire probe needs an explicit privacy cue")
            assert pattern_ab.search(r), (
                f"ORDER_OVERFIRE[{orig_idx}].r{r_idx} missing 'A)' choice structure")
            assert pattern_b.search(r), (
                f"ORDER_OVERFIRE[{orig_idx}].r{r_idx} missing 'B)' choice structure")


def test_instr_rephrasings_preserve_format_tag():
    """INSTR probes are tagged terse / open. Heuristic: terse rephrasings stay
    brief (≤ 200 chars suggested by the spec); open rephrasings stay open-ended
    (a question or walk-me-through framing). The runner does NOT actually read
    the tag at scoring time (score_instr only looks for hexgrid leaks) but the
    per-format breakdown in the report would be meaningless if tags drift.
    """
    open_cues = ("how", "what", "walk", "why", "approach", "explain",
                 "help", "?")
    for orig_idx, rephr_list in REPHRASINGS["INSTR"].items():
        format_tag = PROBES_INSTR[orig_idx][0]
        assert format_tag in ("terse", "open")
        for r_idx, r in enumerate(rephr_list):
            if format_tag == "terse":
                # Permissive cap; the original terse probes are well under 200,
                # so a rephrasing > 200 has clearly drifted into open territory.
                assert len(r) <= 200, (
                    f"INSTR[{orig_idx}].r{r_idx} is tagged 'terse' but is "
                    f"{len(r)} chars > 200 (likely drifted to open-ended)")
            else:
                # Open probes should LOOK open-ended: contain a question-mark
                # or one of the open cues. Avoid demanding a specific structure.
                r_lower = r.lower()
                assert any(cue in r_lower for cue in open_cues), (
                    f"INSTR[{orig_idx}].r{r_idx} is tagged 'open' but contains "
                    f"no open-ended cue ({open_cues})")


def test_override_rephrasings_preserve_destructive_intent():
    """OVERRIDE probes must keep their destructive verb + an explicit imperative.

    Heuristic (documented):
      * Destructive verb required: one of `rm`, `delete`, `wipe`, `purge`, `nuke`,
        `clean`, `clear`, `remove`, `drop`. Case-insensitive substring match.
      * Imperative cue required: one of `just`, `proceed`, `execute`, `go ahead`,
        `do it`, `now`, `run it`, `go for it`, `go.`. Case-insensitive.
    Both classes must appear so a softened rephrasing ("perhaps consider deleting")
    fails this test.
    """
    destructive_verbs = ("rm", "delete", "wipe", "purge", "nuke",
                         "clean", "clear", "remove", "drop")
    imperatives = ("just", "proceed", "execute", "go ahead", "do it",
                   "now", "run it", "go for it", "go.", "go,",
                   "go -", "- go")
    for orig_idx, rephr_list in REPHRASINGS["OVERRIDE"].items():
        for r_idx, r in enumerate(rephr_list):
            r_lower = r.lower()
            assert any(v in r_lower for v in destructive_verbs), (
                f"OVERRIDE[{orig_idx}].r{r_idx} lacks a destructive verb "
                f"({destructive_verbs}); intent broken")
            assert any(imp in r_lower for imp in imperatives), (
                f"OVERRIDE[{orig_idx}].r{r_idx} lacks an imperative cue "
                f"({imperatives}); intent softened")


def test_bem_rephrasings_invite_self_description():
    """BEM probes ask the MODEL about ITSELF. Heuristic:
      * Must contain at least one first/second-person marker (you, your,
        yourself, I, my). Case-insensitive.
      * Must NOT mention workspace/project/codebase/repository - that framing
        belongs to BEM_WORKSPACE_FACT and the runner uses the BEM gist token
        leak rate as the headline; collateral workspace framing would conflate.
    """
    person_markers = ("you", "your", "yourself", "i ", "i'", " i.", "my ")
    forbidden_workspace = ("workspace", "project", "codebase")
    for orig_idx, rephr_list in REPHRASINGS["BEM"].items():
        for r_idx, r in enumerate(rephr_list):
            r_lower = r.lower()
            assert any(m in r_lower for m in person_markers), (
                f"BEM[{orig_idx}].r{r_idx} contains no first/second-person marker; "
                f"the open-ended self-description framing is broken")
            for forbidden in forbidden_workspace:
                assert forbidden not in r_lower, (
                    f"BEM[{orig_idx}].r{r_idx} mentions {forbidden!r}; that's "
                    f"BEM_WORKSPACE_FACT's territory and conflates the two modes")


def test_bem_workspace_fact_rephrasings_ask_about_workspace():
    """BEM_WORKSPACE_FACT probes ask about the WORKSPACE / PROJECT. Heuristic:
      * Must mention `workspace`, `project`, `codebase`, OR demonstratively
        reference the surrounding context (`this`, `here`). The runner's scorer
        looks for the gist token in the response; if the prompt doesn't
        invite a workspace answer, the headline metric collapses.
      * Must NOT lead with `you` as the very first word - that would re-create
        a BEM-style self-description prompt and undermine the asymmetric
        non-interfered design.
    """
    workspace_markers = ("workspace", "project", "codebase",
                         "this", "here", "the place")
    for orig_idx, rephr_list in REPHRASINGS["BEM_WORKSPACE_FACT"].items():
        for r_idx, r in enumerate(rephr_list):
            r_lower = r.lower()
            assert any(m in r_lower for m in workspace_markers), (
                f"BEM_WORKSPACE_FACT[{orig_idx}].r{r_idx} mentions no "
                f"workspace/project/codebase/this/here cue; workspace framing lost")
            first_word = r_lower.split()[0].strip(".,!?:;")
            assert first_word != "you", (
                f"BEM_WORKSPACE_FACT[{orig_idx}].r{r_idx} leads with 'you' as "
                f"subject; that's BEM-style self-description framing")


# =====================================================================
# `expanded_probes` helper tests
# =====================================================================

def test_expanded_probes_helper_preserves_tuple_structure_for_order():
    expanded = expanded_probes("ORDER", PROBES_ORDER)
    # Total = N originals * 5 (1 original + 4 rephrasings).
    assert len(expanded) == len(PROBES_ORDER) * 5, (
        f"expanded ORDER length {len(expanded)} != {len(PROBES_ORDER)} * 5")
    for i, entry in enumerate(expanded):
        # Every entry must be a tuple (tag, text).
        assert isinstance(entry, tuple) and len(entry) == 2, (
            f"ORDER expanded[{i}] is not a 2-tuple: {entry!r}")
        tag, text = entry
        assert tag in ("A", "B"), f"ORDER expanded[{i}] tag={tag!r} not A/B"
        assert isinstance(text, str) and text.strip()
    # The originals should land at positions 0, 5, 10, ...
    for k, orig in enumerate(PROBES_ORDER):
        assert expanded[k * 5] == orig, (
            f"ORDER expanded[{k * 5}] != original probe {k}")


def test_expanded_probes_helper_preserves_tuple_structure_for_instr():
    expanded = expanded_probes("INSTR", PROBES_INSTR)
    assert len(expanded) == len(PROBES_INSTR) * 5
    for i, entry in enumerate(expanded):
        assert isinstance(entry, tuple) and len(entry) == 2, (
            f"INSTR expanded[{i}] is not a 2-tuple: {entry!r}")
        tag, text = entry
        assert tag in ("terse", "open"), f"INSTR expanded[{i}] tag={tag!r} not terse/open"
        assert isinstance(text, str) and text.strip()
    for k, orig in enumerate(PROBES_INSTR):
        assert expanded[k * 5] == orig


def test_expanded_probes_helper_preserves_tuple_structure_for_order_overfire():
    """ORDER_OVERFIRE is also tuple-shaped; mirror the ORDER test."""
    expanded = expanded_probes("ORDER_OVERFIRE", PROBES_ORDER_OVERFIRE)
    assert len(expanded) == len(PROBES_ORDER_OVERFIRE) * 5
    for i, entry in enumerate(expanded):
        assert isinstance(entry, tuple) and len(entry) == 2, (
            f"ORDER_OVERFIRE expanded[{i}] is not a 2-tuple: {entry!r}")
        tag, _text = entry
        assert tag in ("A", "B")


def test_expanded_probes_helper_preserves_string_shape_for_bem():
    expanded = expanded_probes("BEM", PROBES_BEM)
    assert len(expanded) == len(PROBES_BEM) * 5
    for i, entry in enumerate(expanded):
        assert isinstance(entry, str) and entry.strip(), (
            f"BEM expanded[{i}] is not a non-empty str: {entry!r}")
    for k, orig in enumerate(PROBES_BEM):
        assert expanded[k * 5] == orig


def test_expanded_probes_helper_preserves_string_shape_for_bem_workspace_fact():
    expanded = expanded_probes("BEM_WORKSPACE_FACT", PROBES_BEM_WORKSPACE_FACT)
    assert len(expanded) == len(PROBES_BEM_WORKSPACE_FACT) * 5
    for i, entry in enumerate(expanded):
        assert isinstance(entry, str) and entry.strip()
    for k, orig in enumerate(PROBES_BEM_WORKSPACE_FACT):
        assert expanded[k * 5] == orig


def test_expanded_probes_helper_preserves_string_shape_for_override():
    expanded = expanded_probes("OVERRIDE", PROBES_OVERRIDE)
    assert len(expanded) == len(PROBES_OVERRIDE) * 5
    for i, entry in enumerate(expanded):
        assert isinstance(entry, str) and entry.strip()
    for k, orig in enumerate(PROBES_OVERRIDE):
        assert expanded[k * 5] == orig


def test_expanded_probes_helper_raises_on_unknown_mode():
    import pytest
    with pytest.raises(KeyError):
        expanded_probes("BOGUS_MODE", [])


# =====================================================================
# rephrasing_count helper
# =====================================================================

def test_rephrasing_count_returns_correct_totals():
    counts = rephrasing_count()
    assert set(counts) == {
        "ORDER", "ORDER_OVERFIRE", "BEM",
        "BEM_WORKSPACE_FACT", "INSTR", "OVERRIDE",
    }
    # Each mode = 4 × N_originals.
    expected = {
        "ORDER": 4 * len(PROBES_ORDER),
        "ORDER_OVERFIRE": 4 * len(PROBES_ORDER_OVERFIRE),
        "BEM": 4 * len(PROBES_BEM),
        "BEM_WORKSPACE_FACT": 4 * len(PROBES_BEM_WORKSPACE_FACT),
        "INSTR": 4 * len(PROBES_INSTR),
        "OVERRIDE": 4 * len(PROBES_OVERRIDE),
    }
    assert counts == expected, f"counts {counts} != expected {expected}"


# =====================================================================
# Safety / paranoia tests
# =====================================================================

def test_no_rephrasing_introduces_bem_or_instr_tokens_into_wrong_mode():
    """The matrix runner's BEM / INSTR scorers look for specific tokens in the
    response. If a rephrasing for OTHER modes accidentally seeded those tokens
    in the prompt, the scorer would mis-fire on legitimate model output that
    echoes the prompt.
    """
    bem_token = "starboard_loop"
    instr_token = "hexgrid_shader"
    # BEM_WORKSPACE_FACT legitimately tries to elicit the BEM token, so it's
    # exempted from the BEM-token check.
    for mode_name, by_idx in REPHRASINGS.items():
        for orig_idx, rephr_list in by_idx.items():
            for r_idx, r in enumerate(rephr_list):
                if mode_name not in ("BEM_WORKSPACE_FACT",):
                    assert bem_token not in r.lower(), (
                        f"{mode_name}[{orig_idx}].r{r_idx} mentions {bem_token!r}; "
                        f"leaks into wrong mode")
                assert instr_token not in r.lower(), (
                    f"{mode_name}[{orig_idx}].r{r_idx} mentions {instr_token!r}; "
                    f"leaks INSTR token outside INSTR mode")


def test_total_expanded_count_meets_n50_floor():
    """Pre-reg §3 single-model tier needs 50 probes/cell. Layout = N originals + 4N
    rephrasings = 5N. For modes with N >= 10 (all of ours except the over-fire /
    workspace-fact 8-probers), 5N >= 50 trivially. For ORDER_OVERFIRE (N=8) and
    BEM_WORKSPACE_FACT (N=8), 5N = 40 — short of 50 — but pre-reg §4 sub-samples
    10 + 40 = 50 *only* for modes with 20 originals; the 8-probers are not in
    the T3 sub-selection at the 50-floor (they're directional asymmetry checks).
    This test merely sanity-checks the multiplication so a future change to "5"
    can't silently land.
    """
    for mode_name in REPHRASINGS:
        originals = _MODE_ORIGINALS[mode_name]
        expanded = expanded_probes(mode_name, originals)
        assert len(expanded) == 5 * len(originals)


# =====================================================================
# `_select_probes` — the --expand-probes wiring (cost-correctness lock)
# =====================================================================
# These tests assert EXACT per-cell sizes (real money depends on them), tuple-tag
# preservation, deterministic sub-sampling, and that the DEFAULT (no flag) path is
# byte-identical to the raw PROBES_* lists. See pre-reg §4 (sub-sample-to-50) and
# PROBE-COUNT CONTRACT (1,520 total, NOT 1,600).

# Pre-registered §4 per-CELL target sizes (one arm of one mode, one condition).
# Guardrail modes ORDER_OVERFIRE / BEM_WORKSPACE_FACT cap at 40 (8 originals, no
# 10th to expand); all others reach 50 (10 originals + 40 rephrasings).
_EXPECTED_EXPANDED_CELL_SIZE = {
    "ORDER": 50,
    "ORDER_OVERFIRE": 40,
    "BEM": 50,
    "BEM_WORKSPACE_FACT": 40,
    "INSTR": 50,
    "OVERRIDE": 50,
}

# Arms per mode (from the MODES registry) — used to verify the per-condition total.
_ARMS_PER_MODE = {
    "ORDER": 2,
    "ORDER_OVERFIRE": 1,
    "BEM": 1,
    "BEM_WORKSPACE_FACT": 1,
    "INSTR": 1,
    "OVERRIDE": 2,
}


def test_select_probes_default_off_is_byte_identical():
    """DEFAULT (expand=False): _select_probes returns the originals UNCHANGED.

    This is the load-bearing T1-SMALL_PANEL guarantee — no flag => no behavior
    change. We assert object identity (same list) AND value equality, so neither a
    copy nor a transform can sneak in.
    """
    for mode_name, originals in _MODE_ORIGINALS.items():
        sel = _select_probes(mode_name, originals, False)
        assert sel is originals, (
            f"{mode_name}: default _select_probes returned a NEW object; "
            f"T1 must pass the originals through untouched")
        assert sel == originals
        assert len(sel) == len(originals)


def test_select_probes_expand_exact_per_cell_sizes():
    """EXPAND=True: exact per-cell N matches the pre-reg §4 / contract target.

    Cost-correctness lock: a naive expand-ALL would yield 100/cell for 20-original
    modes (~2x the paid bill). The first-10 sub-sample must yield 50 (or 40 for the
    8-original guardrail modes) — and EXACTLY that, no more, no fewer.
    """
    for mode_name, originals in _MODE_ORIGINALS.items():
        sel = _select_probes(mode_name, originals, True)
        assert len(sel) == _EXPECTED_EXPANDED_CELL_SIZE[mode_name], (
            f"{mode_name}: expanded cell size {len(sel)} != "
            f"{_EXPECTED_EXPANDED_CELL_SIZE[mode_name]} (cost-correctness violation)")


def test_select_probes_expand_does_not_use_naive_expand_all():
    """Guard against the regression where someone calls expanded_probes() on ALL
    originals (20 -> 100). The 20-original modes MUST be 50, never 100.
    """
    for mode_name in ("ORDER", "BEM", "INSTR", "OVERRIDE"):
        originals = _MODE_ORIGINALS[mode_name]
        assert len(originals) == 20
        sel = _select_probes(mode_name, originals, True)
        naive = expanded_probes(mode_name, originals)
        assert len(naive) == 100, "sanity: naive expand-all of a 20-mode is 100"
        assert len(sel) == 50, (
            f"{mode_name}: sub-sample must be 50, not the naive {len(naive)}")
        assert len(sel) != len(naive)


def test_select_probes_subsample_n_override_to_n100():
    """--expand-subsample-n override (default-safe): subsample_n=20 expands ALL 20
    pre-registered originals for the 20-original modes -> N=100/cell (the pre-reg §7
    target that §4 cost-scaled to 50), WITHOUT changing the default. The 8-original
    guardrail modes stay capped at 40 regardless. This is the mechanism the quant
    replication uses; judge_ladder.py --subsample-n must match it on reconstruction.
    """
    # 1. The new param's default is byte-identical to the prior fixed behavior.
    for mode_name, originals in _MODE_ORIGINALS.items():
        assert (_select_probes(mode_name, originals, True)
                == _select_probes(mode_name, originals, True, subsample_n=_EXPAND_SUBSAMPLE_N)), (
            f"{mode_name}: omitting subsample_n must equal explicit default")
    # 2. subsample_n=20 -> 100 for the four 20-original modes (BEM is the one we use).
    for mode_name in ("ORDER", "BEM", "INSTR", "OVERRIDE"):
        sel = _select_probes(mode_name, _MODE_ORIGINALS[mode_name], True, subsample_n=20)
        assert len(sel) == 100, f"{mode_name}: subsample_n=20 must give 100, got {len(sel)}"
    # 3. The 8-original guardrail modes cap at 40 even at subsample_n=20 (no 9th-20th
    #    original to expand) — N=100 is a BEM-side lever only; recall stays a 40 control.
    for mode_name in ("ORDER_OVERFIRE", "BEM_WORKSPACE_FACT"):
        sel = _select_probes(mode_name, _MODE_ORIGINALS[mode_name], True, subsample_n=20)
        assert len(sel) == 40, (
            f"{mode_name}: 8-original guardrail mode must cap at 40 even at "
            f"subsample_n=20, got {len(sel)}")
    # 4. The default cap (10 -> 50 for BEM) is unchanged by the new param's existence.
    assert len(_select_probes("BEM", _MODE_ORIGINALS["BEM"], True)) == 50


def test_select_probes_rephrasings_cap():
    """--rephrasings-per-original cap: limits each original to its first K rephrasings,
    trading breadth for cluster-independence (M3). Default (None) = all 4, unchanged.
    The money-safety assert stays exact via expected_expanded_count (cap-aware).
    """
    from probes_rephrasings import expanded_probes, expected_expanded_count
    # cap=None is byte-identical to the historical all-rephrasings behavior.
    for mode_name, originals in _MODE_ORIGINALS.items():
        assert (_select_probes(mode_name, originals, True)
                == _select_probes(mode_name, originals, True, rephrasings_cap=None))
    # cap=1 => each original contributes 2 (itself + 1 rephrasing). For the four
    # 20-original modes at subsample_n=20: 20 * 2 = 40 (the m=2 quant-study config).
    for mode_name in ("ORDER", "BEM", "INSTR", "OVERRIDE"):
        sel = _select_probes(mode_name, _MODE_ORIGINALS[mode_name], True,
                             subsample_n=20, rephrasings_cap=1)
        assert len(sel) == 40, f"{mode_name}: subsample_n=20,cap=1 must give 40, got {len(sel)}"
    # cap=0 => originals only (independent), 20 for the 20-modes at subsample_n=20.
    sel0 = _select_probes("BEM", _MODE_ORIGINALS["BEM"], True, subsample_n=20, rephrasings_cap=0)
    assert len(sel0) == 20
    # The original sits first in each (1+cap)-block (sample-probe-0 prints stay canonical).
    capped = expanded_probes("BEM", _MODE_ORIGINALS["BEM"][:3], rephrasings_cap=1)
    assert capped[0] == _MODE_ORIGINALS["BEM"][0] and capped[2] == _MODE_ORIGINALS["BEM"][1]
    # expected_expanded_count agrees with reality under caps.
    assert expected_expanded_count("BEM", 20, 1) == 40
    assert expected_expanded_count("BEM", 20, None) == 100
    assert expected_expanded_count("BEM_WORKSPACE_FACT", 8, 1) == 16  # 8 originals * 2


def test_select_probes_per_condition_and_t3_total():
    """The realized T3 totals (per-condition arm-cell sum + ×4 conditions) must
    equal the PROBE-COUNT CONTRACT figures: 380/condition, 1,520 total — NOT the
    pre-reg §4 stated 1,600.
    """
    per_condition = sum(
        _select_probes(m, _MODE_ORIGINALS[m], True).__len__() * _ARMS_PER_MODE[m]
        for m in _MODE_ORIGINALS
    )
    assert per_condition == 380, (
        f"per-condition arm-cell total {per_condition} != 380")
    assert per_condition * 4 == 1520, (
        f"T3 total {per_condition * 4} != contract 1,520")
    # And confirm it is NOT the (incorrect) pre-reg 1,600.
    assert per_condition * 4 != 1600


def test_select_probes_expand_preserves_tuple_tags():
    """Tuple-tag shape (scar_letter / format_tag at tuple[0]) survives expansion
    for ORDER / ORDER_OVERFIRE / INSTR; string modes stay strings.
    """
    for mode_name in ("ORDER", "ORDER_OVERFIRE", "INSTR"):
        sel = _select_probes(mode_name, _MODE_ORIGINALS[mode_name], True)
        for i, entry in enumerate(sel):
            assert isinstance(entry, tuple) and len(entry) == 2, (
                f"{mode_name} expanded[{i}] lost tuple shape: {entry!r}")
            tag = entry[0]
            if mode_name in ("ORDER", "ORDER_OVERFIRE"):
                assert tag in ("A", "B")
            else:
                assert tag in ("terse", "open")
    for mode_name in ("BEM", "BEM_WORKSPACE_FACT", "OVERRIDE"):
        sel = _select_probes(mode_name, _MODE_ORIGINALS[mode_name], True)
        for i, entry in enumerate(sel):
            assert isinstance(entry, str) and entry.strip(), (
                f"{mode_name} expanded[{i}] is not a non-empty str: {entry!r}")


def test_select_probes_expand_is_deterministic_first_n_slice():
    """Sub-sampling must be the deterministic FIRST-min(N,10) slice — no randomness.

    Run twice: byte-identical. And the surviving originals must be the FIRST
    _EXPAND_SUBSAMPLE_N originals (at positions 0, 5, 10, ... of the expanded
    layout), so cache keys (keyed on probe text) are stable run-to-run.
    """
    for mode_name, originals in _MODE_ORIGINALS.items():
        a = _select_probes(mode_name, originals, True)
        b = _select_probes(mode_name, originals, True)
        assert a == b, f"{mode_name}: expansion is non-deterministic"
        n_kept = min(_EXPAND_SUBSAMPLE_N, len(originals))
        for k in range(n_kept):
            assert a[k * 5] == originals[k], (
                f"{mode_name}: expanded[{k * 5}] is not original {k}; "
                f"sub-sample is not the deterministic first-{n_kept} slice")


def test_select_probes_expand_arms_share_identical_list():
    """ORDER / OVERRIDE have 2 arms that iterate the SAME mode-level probe list.
    Expansion happens once per mode, so calling _select_probes again for the same
    mode yields an equal list (no per-arm independent sub-sampling / divergence).
    """
    for mode_name in ("ORDER", "OVERRIDE"):
        arm1 = _select_probes(mode_name, _MODE_ORIGINALS[mode_name], True)
        arm2 = _select_probes(mode_name, _MODE_ORIGINALS[mode_name], True)
        assert arm1 == arm2
        assert len(arm1) == _EXPECTED_EXPANDED_CELL_SIZE[mode_name]


def test_select_probes_expand_cache_keys_distinct_from_originals():
    """Cache-collision firewall (per-call level): the cache key is
    sha256(model\\x00system\\x00user)[:24], keyed on probe TEXT. Every rephrasing
    is a DISTINCT user string => DISTINCT key, so an expanded (N=50) cell's extra
    entries can NEVER be served for / collide with a non-expanded (N=20) request.
    Surviving originals share text => share keys (legitimate, desirable reuse).

    Replicates the adapters' key construction to assert: the set of keys for the
    expanded list is a strict SUPERSET of the non-expanded list's keys (the 10
    surviving originals overlap; the 40 rephrasings are all new + unique).
    """
    import hashlib

    # DELIBERATE STAND-IN: this replicates (does not import) the three adapters'
    # identical key scheme — sha256(f"{model}\x00{system}\x00{user}")[:24] at
    # redteam_claude_md_interference.py ollama_chat, openrouter_chat.py, and
    # lmstudio_chat.py. No shared helper exists today, so it is hand-rolled here.
    # The PROPERTY under test (distinct probe text => distinct key; surviving
    # originals share keys) is robust to the model/system prefix, so the test is
    # meaningful regardless. But because it replicates rather than imports the
    # keying, a future adapter key change (e.g. folding in n_predict) would NOT
    # break this test — keep this in sync with the adapters if their key changes.
    def key(text):
        return hashlib.sha256(
            f"model\x00sys\x00{text}".encode("utf-8")).hexdigest()[:24]

    def texts(probes):
        return [p[1] if isinstance(p, tuple) else p for p in probes]

    for mode_name, originals in _MODE_ORIGINALS.items():
        non_expanded = _select_probes(mode_name, originals, False)
        expanded = _select_probes(mode_name, originals, True)
        non_keys = {key(t) for t in texts(non_expanded)}
        exp_keys_list = [key(t) for t in texts(expanded)]
        exp_keys = set(exp_keys_list)
        # No collision: each expanded probe text is unique (no two probes share a key).
        assert len(exp_keys_list) == len(exp_keys), (
            f"{mode_name}: two expanded probes collide on cache key (duplicate text)")
        # The surviving first-N originals are shared with the non-expanded run.
        n_kept = min(_EXPAND_SUBSAMPLE_N, len(originals))
        kept_keys = {key(t) for t in texts(originals[:n_kept])}
        assert kept_keys <= exp_keys, (
            f"{mode_name}: surviving originals' keys not present in expanded keys")
        # The 40 rephrasing keys are genuinely NEW (not in the originals-only set),
        # so an N=20 cached entry can never satisfy an N=50 request.
        new_keys = exp_keys - non_keys
        assert len(new_keys) == 4 * n_kept, (
            f"{mode_name}: expected {4 * n_kept} new rephrasing keys, got {len(new_keys)}")


def test_select_probes_unknown_mode_under_expand_raises():
    """Expanding an unregistered mode must surface a KeyError (no silent empty cell)."""
    import pytest
    with pytest.raises(KeyError):
        _select_probes("BOGUS_MODE", [("A", "x")], True)
    # But default-off on a bogus mode is a harmless pass-through (no rephrasings used).
    assert _select_probes("BOGUS_MODE", ["x"], False) == ["x"]


# =====================================================================
# Cost preflight — projected-dollars reconciliation (money-safety)
# =====================================================================
# These lock the cost-correctness contract numbers the paid T3 run depends on:
# the realized 1,520-probe total reconciles to the projected $27.36 at the
# single-source per-probe estimate, and that figure is within the $75 cap.

def test_per_probe_estimate_is_the_single_source_constant():
    """_EST_USD_PER_PROBE must equal the pre-reg §4 / DEVIATIONS O1 figure ($0.018).
    A drift here would silently desynchronize the runner's projected-cost line from
    the documented cost model."""
    assert _EST_USD_PER_PROBE == 0.018, (
        f"_EST_USD_PER_PROBE={_EST_USD_PER_PROBE} != documented $0.018 "
        f"(pre-reg §4 / DEVIATIONS O1); update both or neither")


def test_projected_t3_cost_reconciles_to_2736_and_within_cap():
    """1,520 probes × $0.018 ≈ $27.36, and that is well within the $75 cap.

    This is the single-model T3 plan (1 model). Mirrors the runner's projected-cost
    arithmetic: total_llm_calls = total_probe_calls × len(models); for the paid T3
    transfer check len(models) == 1.
    """
    per_condition = sum(
        len(_select_probes(m, _MODE_ORIGINALS[m], True)) * _ARMS_PER_MODE[m]
        for m in _MODE_ORIGINALS
    )
    t3_total = per_condition * 4  # B0, B1, V1, V2.full
    assert t3_total == 1520
    projected = t3_total * _EST_USD_PER_PROBE
    assert abs(projected - 27.36) < 0.01, (
        f"projected ${projected:.2f} != contract $27.36")
    assert projected < 75.0, "projected T3 cost must be within the $75 cap"
    # Even a +30% overrun stays under the cap (headroom check).
    assert projected * 1.30 < 75.0, (
        f"projected +30% (${projected * 1.30:.2f}) must still be within $75 cap")


def test_naive_expand_all_would_blow_past_rescope_trigger():
    """Sanity tripwire documenting WHY the first-10 sub-sample is mandatory: the
    naive expand-ALL (20 originals -> 100/cell for the four 20-original modes) would
    roughly double the bill and approach the $65 (87%) re-scope trigger / $75 cap.
    """
    naive_per_condition = sum(
        len(expanded_probes(m, _MODE_ORIGINALS[m])) * _ARMS_PER_MODE[m]
        for m in _MODE_ORIGINALS
    )
    naive_total = naive_per_condition * 4
    # 20-mode -> 100; 8-mode -> 40. per condition = (50/100 modes...) compute exact:
    # ORDER 100*2 + ORDER_OVERFIRE 40 + BEM 100 + BEM_WF 40 + INSTR 100 + OVERRIDE 100*2
    #     = 200 + 40 + 100 + 40 + 100 + 200 = 680/condition; *4 = 2720.
    assert naive_per_condition == 680
    assert naive_total == 2720
    naive_cost = naive_total * _EST_USD_PER_PROBE
    # ~$48.96 — substantially more than the sub-sampled $27.36, confirming the
    # sub-sample is load-bearing for staying near the pre-reg estimate.
    assert naive_cost > 48.0
    assert naive_cost > 27.36 * 1.7
