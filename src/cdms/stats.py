"""Measurement-precision primitives (Thread 3).

The project's headline numbers — trait overlap, adherence spread, coupling, disposition
rates — were reported as bare point estimates with no error bars. That is false precision
in the other direction: implying exactness we never established. This module provides the
small, reusable, dependency-light statistics the project lacked so a reported number can
carry its uncertainty:

  * ``mean_se``            — mean ± standard error.
  * ``wilson_interval``   — score interval for a binomial RATE (disposition / adherence /
                            rule-citation), well-behaved at the 0/1 extremes where the normal
                            approximation fails.
  * ``bootstrap_ci``      — percentile-bootstrap CI for any axis-aware statistic (default mean).
  * ``pooled_overlap_baseline`` / ``overlap_significance`` — a shuffle/permutation null for
                            the trait-overlap metric: how much pairwise Jaccard overlap would
                            arise by CHANCE if each project drew its traits independently from a
                            shared vocabulary. Turns "overlap 0.00" into "0.00 vs null μ±σ (z=…)".

Pure stdlib + numpy (already a runtime dep). Deterministic given a seed — no global RNG.
"""

from __future__ import annotations

import math
import statistics
from typing import Callable

import numpy as np


def _z(confidence: float) -> float:
    """Two-sided normal critical value for a confidence level (e.g. 0.95 -> 1.95996)."""
    return statistics.NormalDist().inv_cdf(1.0 - (1.0 - confidence) / 2.0)


def mean_se(values) -> tuple[float, float]:
    """Sample mean and standard error of the mean. SE is 0 for n<=1."""
    arr = np.asarray(values, dtype=float)
    n = arr.size
    if n == 0:
        return 0.0, 0.0
    if n == 1:
        return float(arr[0]), 0.0
    return float(arr.mean()), float(arr.std(ddof=1) / math.sqrt(n))


def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> tuple[float, float, float]:
    """Wilson score interval for a binomial proportion. Returns (point, lo, hi), clamped to [0,1].

    Preferred over the normal (Wald) interval because it stays inside [0,1] and is sensible at
    small n and at p=0 or p=1 — exactly the regime of the disposition/adherence probes.
    """
    if n <= 0:
        return 0.0, 0.0, 0.0
    z = _z(confidence)
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return p, max(0.0, center - half), min(1.0, center + half)


def bootstrap_ci(
    values,
    confidence: float = 0.95,
    n_resamples: int = 10000,
    seed: int = 0,
    statistic: Callable = np.mean,
) -> tuple[float, float, float]:
    """Percentile-bootstrap confidence interval. Returns (point, lo, hi).

    ``statistic`` must accept an ``axis`` keyword (np.mean / np.median / np.std). Degenerate
    inputs (n<2) return the point estimate for all three so callers never special-case.
    """
    arr = np.asarray(values, dtype=float)
    point = float(statistic(arr))
    if arr.size < 2:
        return point, point, point
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, arr.size, size=(n_resamples, arr.size))
    stats = np.asarray(statistic(arr[idx], axis=1), dtype=float)
    lo = float(np.percentile(stats, 100.0 * (1.0 - confidence) / 2.0))
    hi = float(np.percentile(stats, 100.0 * (1.0 - (1.0 - confidence) / 2.0)))
    return point, lo, hi


def _mean_pairwise_jaccard(groups: list[set]) -> float:
    k = len(groups)
    if k < 2:
        return 0.0
    total, pairs = 0.0, 0
    for i in range(k):
        for j in range(i + 1, k):
            union = len(groups[i] | groups[j])
            total += (len(groups[i] & groups[j]) / union) if union else 0.0
            pairs += 1
    return total / pairs if pairs else 0.0


def pooled_overlap_baseline(
    group_sizes: list[int],
    vocab_size: int,
    n_trials: int = 10000,
    seed: int = 0,
) -> tuple[float, float, np.ndarray]:
    """Null distribution of mean pairwise Jaccard overlap under random trait assignment.

    Each of the ``len(group_sizes)`` groups independently draws ``size`` DISTINCT items
    uniformly from a shared vocabulary of ``vocab_size`` items (a trait CAN therefore land in
    more than one group — that is the chance overlap we are testing against). Returns
    ``(null_mean, null_sd, distribution)``.

    This is the right null for "are these projects more differentiated than chance?": if the
    observed overlap sits far BELOW this null, the projects share less vocabulary than random
    sampling from the same pool would produce — genuine differentiation, not an artifact.
    """
    rng = np.random.default_rng(seed)
    dist = np.empty(n_trials, dtype=float)
    for t in range(n_trials):
        groups = [
            set(rng.choice(vocab_size, size=min(s, vocab_size), replace=False).tolist())
            for s in group_sizes
        ]
        dist[t] = _mean_pairwise_jaccard(groups)
    sd = float(dist.std(ddof=1)) if n_trials > 1 else 0.0
    return float(dist.mean()), sd, dist


def overlap_significance(
    observed: float,
    group_sizes: list[int],
    vocab_size: int,
    n_trials: int = 10000,
    seed: int = 0,
) -> dict:
    """Compare an observed overlap to the pooled-resampling null. Returns a dict with the
    null mean/sd, the z-score (observed - null_mean)/null_sd, and the left-tail p
    ("percentile" key kept for compatibility). A strongly negative z (e.g. <= -2)
    means the observed overlap is meaningfully lower than chance — real differentiation.

    The left-tail p uses the add-one (b+1)/(n+1) permutation estimator (REPO_ANALYSIS
    P2): a Monte-Carlo p can never legitimately be 0 — "0.000" over 10k trials means
    p < ~1e-4, which is what (0+1)/(10000+1) reports. NOTE: the z <= -2 "meaningful"
    verdict cut is a descriptive reporting convention, not a pre-registered decision
    rule — confirmatory work uses its own locked gates.
    """
    null_mean, null_sd, dist = pooled_overlap_baseline(group_sizes, vocab_size, n_trials, seed)
    z = (observed - null_mean) / null_sd if null_sd > 0 else 0.0
    percentile = float((np.sum(dist <= observed) + 1) / (len(dist) + 1))
    return {
        "observed": float(observed),
        "null_mean": null_mean,
        "null_sd": null_sd,
        "z": z,
        "percentile": percentile,
        "verdict": "meaningful" if z <= -2.0 else ("inconclusive" if z < 2.0 else "above-chance"),
    }
