"""T1 aggregator math helpers.

Pure-math primitives used by the T1 matrix-run aggregator to turn per-arm
success/trial counts into the pre-registered ship/no-ship verdicts:

  * ``wilson_bounds`` — thin wrapper over ``cdms.stats.wilson_interval`` that
    accepts an ``alpha`` instead of a ``confidence`` so the rest of the
    aggregator can speak the same vocabulary as the Bonferroni helper. Returns
    ``(p, lo, hi)`` and degrades gracefully at ``trials=0``.
  * ``bounds_disjoint`` — three-way ordering test between two Wilson CIs.
  * ``symmetric_win`` — the pre-registration §7 "Wilson-bound symmetric
    comparison": treatment wins iff the point-estimate delta meets the
    pp_threshold AND the two CIs are disjoint in the right direction. Same
    discipline for declaring a fail. Anything else is a tie. This is the
    function the aggregator calls once per (mode, model, arm-pair) cell.
  * ``bonferroni_alpha`` — base_alpha / family_size, with a guard so a
    silently-empty family doesn't become an infinity.
  * ``across_models_aggregate`` — promote a list of per-model verdicts to a
    cross-model verdict using the pre-reg's >=3-of-5 rule. ANY per-model fail
    short-circuits to a fail (we don't ship a mode that regresses on any
    panel model).

Hermetic, no I/O, no global state. The wilson math is deliberately not
re-implemented here — ``cdms.stats.wilson_interval`` is the one place that
formula lives in the codebase.
"""

from __future__ import annotations

from cdms.stats import wilson_interval


def wilson_bounds(
    successes: int,
    trials: int,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """Wilson score interval for a binomial proportion at the given alpha.

    Returns ``(p, lo, hi)``. ``alpha=0.05`` -> 95% CI. ``trials=0`` returns
    ``(0.0, 0.0, 0.0)`` so callers can compare zero-trial cells without
    a special case.
    """
    if trials <= 0:
        return 0.0, 0.0, 0.0
    if successes < 0:
        raise ValueError(f"successes must be >= 0, got {successes}")
    if successes > trials:
        raise ValueError(
            f"successes ({successes}) cannot exceed trials ({trials})"
        )
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    confidence = 1.0 - alpha
    return wilson_interval(successes, trials, confidence=confidence)


def bounds_disjoint(
    a_p: float,
    a_lo: float,
    a_hi: float,
    b_p: float,
    b_lo: float,
    b_hi: float,
) -> str:
    """Three-way relation between two Wilson CIs.

    Returns:
      * ``"a_above_b"`` if ``a_lo > b_hi`` (a strictly above b's interval),
      * ``"b_above_a"`` if ``b_lo > a_hi``,
      * ``"overlap"`` otherwise (including the exact-touching boundary).
    """
    if a_lo > b_hi:
        return "a_above_b"
    if b_lo > a_hi:
        return "b_above_a"
    return "overlap"


def symmetric_win(
    treatment_p: float,
    treatment_lo: float,
    treatment_hi: float,
    control_p: float,
    control_lo: float,
    control_hi: float,
    pp_threshold: float = 0.10,
) -> str:
    """Pre-registration §7 Wilson-bound symmetric comparison.

    Returns one of:
      * ``"win"``  -- ``treatment - control >= pp_threshold`` AND
                      ``control_hi < treatment_lo`` (CIs strictly disjoint,
                      treatment above).
      * ``"fail"`` -- ``control - treatment >= pp_threshold`` AND
                      ``treatment_hi < control_lo``.
      * ``"tie"``  -- neither.

    The symmetry is the point: the same evidentiary bar applies to declaring
    a regression as to declaring a win.
    """
    if pp_threshold < 0:
        raise ValueError(f"pp_threshold must be >= 0, got {pp_threshold}")
    delta = treatment_p - control_p
    if delta >= pp_threshold and control_hi < treatment_lo:
        return "win"
    if -delta >= pp_threshold and treatment_hi < control_lo:
        return "fail"
    return "tie"


def bonferroni_alpha(family_size: int, base_alpha: float = 0.05) -> float:
    """Bonferroni-adjusted alpha: ``base_alpha / family_size``.

    The pre-reg's ``family_size=28`` yields ``alpha ~= 0.001786``. Validates
    ``family_size >= 1`` so an empty-family bug surfaces immediately rather
    than producing an infinite alpha.
    """
    if family_size < 1:
        raise ValueError(f"family_size must be >= 1, got {family_size}")
    if not 0.0 < base_alpha < 1.0:
        raise ValueError(f"base_alpha must be in (0, 1), got {base_alpha}")
    return base_alpha / family_size


def across_models_aggregate(
    per_model_verdicts: list[str],
    required_count: int = 3,
    total_models: int = 5,
) -> str:
    """Promote per-model verdicts to a cross-model verdict.

    Pre-reg §7 rule: a mode ships iff ``>= required_count`` models WIN and
    ZERO models FAIL. Any per-model fail short-circuits to ``"fail"`` (we
    won't ship a change that regresses on any panel model). Otherwise tie.

    Args:
      per_model_verdicts: list of ``"win"`` / ``"tie"`` / ``"fail"``.
      required_count: minimum number of wins for a cross-model win.
      total_models: expected panel size; the list length is checked against
        this so a missing-model bug surfaces here instead of being silently
        treated as a tie.
    """
    if required_count < 1:
        raise ValueError(f"required_count must be >= 1, got {required_count}")
    if total_models < required_count:
        raise ValueError(
            f"total_models ({total_models}) must be >= required_count "
            f"({required_count})"
        )
    if len(per_model_verdicts) != total_models:
        raise ValueError(
            f"expected {total_models} per-model verdicts, "
            f"got {len(per_model_verdicts)}"
        )
    allowed = {"win", "tie", "fail"}
    bad = [v for v in per_model_verdicts if v not in allowed]
    if bad:
        raise ValueError(
            f"per_model_verdicts must each be one of {sorted(allowed)}; "
            f"got unknown values {bad}"
        )
    if any(v == "fail" for v in per_model_verdicts):
        return "fail"
    wins = sum(1 for v in per_model_verdicts if v == "win")
    if wins >= required_count:
        return "win"
    return "tie"
