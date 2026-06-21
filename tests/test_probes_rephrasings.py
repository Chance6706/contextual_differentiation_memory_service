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
