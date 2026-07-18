"""Differentiation axis — the store-level Jaccard path ($0, hash embedder).

Two measurements, two honest states:
  * Cross-psyche overlap (thesis metric, single-pass): two distinct histories -> low overlap.
    The discard policy CANNOT move this in one pass (gists form before episodes are evicted) —
    a null BY CONSTRUCTION, locked here so a future change that breaks it is visible.
  * Self-shape (the salience-vs-random SHARP CONTROL, multi-cycle): the SAME history under
    salience vs random discard diverges — the forgetting policy shapes identity. Real but subtle.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["CDMS_EMBED_BACKEND"] = "hash"
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from tools.eval_harness.differentiation import measure_overlap, measure_selfshape


def test_gists_form_and_overlap_is_valid(tmp_path):
    r = measure_overlap("cdms-full", 0, tmp_path)
    assert r["traits_a"] > 0 and r["traits_b"] > 0        # gists actually formed (empty = no measurement)
    assert 0.0 <= r["overlap"] <= 1.0


def test_distinct_histories_are_differentiated(tmp_path):
    # Two psyches with disjoint entity vocabularies -> LOW cross-psyche overlap (the thesis).
    r = measure_overlap("cdms-full", 0, tmp_path)
    assert r["overlap"] < 0.5


def test_single_pass_is_condition_insensitive(tmp_path):
    # THE FINDING: in one pass, gists aggregate before episodes are evicted, so the discard
    # policy leaves the traits untouched — cdms-full and cdms-random-discard are identical.
    full = measure_overlap("cdms-full", 1, tmp_path / "full")
    rand = measure_overlap("cdms-random-discard", 1, tmp_path / "rand")
    assert full["overlap"] == rand["overlap"]
    assert full["traits_a"] == rand["traits_a"] and full["traits_b"] == rand["traits_b"]


def test_multicycle_salience_vs_random_diverges(tmp_path):
    # THE SHARP CONTROL: across aging cycles, WHICH episodes survive to reinforce gists depends
    # on the discard policy, so salience and random shape different final trait sets. Subtle
    # (mostly overlapping) but non-null for at least one seed — proving the policy is load-bearing.
    results = [measure_selfshape(seed, tmp_path / f"s{seed}", cycles=8) for seed in (0, 1, 2, 3)]
    for r in results:
        assert r["traits_salience"] > 0 and r["traits_random"] > 0
        assert 0.0 <= r["self_overlap"] <= 1.0
    assert any(r["diverged"] for r in results)             # policy shaped identity in >=1 seed
    assert any(r["self_overlap"] < 1.0 for r in results)   # and the divergence is measurable
