"""Ablation-delta analysis — the v2 primary endpoints.

For each (axis, metric): each condition's rate, and the DELTA vs the reference (cdms-full).

CLUSTERING (rule-12 fix): the unit of independence is the SCENARIO/store, NOT the query.
N queries against one ~6-episode store are N reads of one binary mechanism decision, not N
independent trials — bootstrapping over queries manufactures a false-tight CI (e.g. a
degenerate [+1,+1] "RESOLVED"). So we aggregate to per-scenario rates first, pair by
scenario, and cluster-bootstrap the delta over SCENARIOS. Honest edge cases:
  * < 2 paired scenarios     -> CI UNDEFINED (a single-scenario mechanism outcome, not a
                                sampled estimate);
  * zero variance across ≥2  -> DETERMINISTIC (consistent effect; CI degenerate but reported
                                as a deterministic finding, not a probabilistic one).
Multiplicity: each (axis, metric, condition) is a separate contrast at 95%; correct/flag for
the noisy paid-panel axes when many are tested.
"""
from __future__ import annotations

import random
from collections import defaultdict

REFERENCE = "cdms-full"

# Per (axis, metric): does a HIGHER value mean the mechanism is FAILING or WORKING? Annotation
# of the protective direction only — never changes the numbers.
METRIC_SENSE = {
    ("injection", "obeyed"): "harm",
    ("injection", "surfaced"): "harm",   # $0 retrieval-layer proxy: higher = fence let it through
    ("multi_project", "leaked_other"): "harm",
    ("identity_leak", "self_attributed"): "harm",
    ("right_to_forget", "forgot"): "benefit",
    ("right_to_forget", "leaked_deleted"): "harm",   # deleted PII still surfaced = worse
    ("differentiation", "overlap"): "harm",   # lower trait overlap = more differentiated
}


def _mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def cluster_bootstrap_ci(per_scenario_diffs: list[float], n_boot: int = 2000, seed: int = 0):
    """95% CI for the mean of per-scenario deltas, resampling SCENARIOS with replacement."""
    m = len(per_scenario_diffs)
    if m < 2:
        return None, None
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        idx = [rng.randrange(m) for _ in range(m)]
        means.append(_mean([per_scenario_diffs[i] for i in idx]))
    means.sort()
    return means[int(0.025 * n_boot)], means[min(int(0.975 * n_boot), n_boot - 1)]


def ablation_deltas(observations: list[dict], *, reference: str = REFERENCE,
                    n_boot: int = 2000, seed: int = 0) -> list[dict]:
    """observations = [{condition, axis, metric, scenario, qid, value}, ...]. Returns one row per
    (axis, metric, condition): rate + n_queries + n_scenarios, and for non-reference conditions the
    scenario-clustered Δ vs reference with a status of RESOLVED / null / deterministic / CI-undefined."""
    # (axis, metric, condition) -> {scenario -> [values]}
    by: dict[tuple, dict] = defaultdict(lambda: defaultdict(list))
    for o in observations:
        scen = o.get("scenario") or str(o.get("qid", "?")).split("#")[0]
        by[(o["axis"], o["metric"], o["condition"])][scen].append(float(o["value"]))

    axes_metrics = sorted({(a, m) for (a, m, _c) in by})
    out: list[dict] = []
    for axis, metric in axes_metrics:
        ref = by.get((axis, metric, reference))
        conds = sorted({c for (a, m, c) in by if a == axis and m == metric})
        for cond in conds:
            per_scen = by[(axis, metric, cond)]
            all_vals = [v for lst in per_scen.values() for v in lst]
            row = {"axis": axis, "metric": metric, "condition": cond,
                   "n_queries": len(all_vals), "n_scenarios": len(per_scen),
                   "rate": _mean(all_vals), "sense": METRIC_SENSE.get((axis, metric), "?")}
            if ref and cond != reference:
                shared = sorted(set(per_scen) & set(ref))
                diffs = [_mean(per_scen[s]) - _mean(ref[s]) for s in shared]
                point = _mean(diffs)
                row["delta_vs_ref"] = point
                row["n_paired_scenarios"] = len(shared)
                if len(shared) < 2:
                    row["status"] = "CI-undefined (single scenario — mechanism outcome, not sampled)"
                    row["resolved"] = None
                elif all(abs(d - diffs[0]) < 1e-12 for d in diffs):
                    row["status"] = f"deterministic across {len(shared)} scenarios (Δ={point:+.3f})"
                    row["resolved"] = (abs(point) > 1e-12)
                else:
                    lo, hi = cluster_bootstrap_ci(diffs, n_boot, seed)
                    row["ci_lo"], row["ci_hi"] = lo, hi
                    row["resolved"] = (lo > 0 or hi < 0)
                    row["status"] = "RESOLVED" if row["resolved"] else "null (CI straddles 0)"
            out.append(row)
    return out


def format_table(rows: list[dict]) -> str:
    lines = ["(CI = cluster-bootstrap over SCENARIOS; single-scenario deltas are mechanism outcomes, "
             "CI undefined; multiplicity uncorrected across contrasts)"]
    cur = None
    for r in sorted(rows, key=lambda r: (r["axis"], r["metric"], r["condition"] != REFERENCE, r["condition"])):
        key = (r["axis"], r["metric"])
        if key != cur:
            cur = key
            worse = {"harm": "worse", "benefit": "better"}.get(r["sense"], "?")
            lines.append(f"\n== {r['axis']} / {r['metric']} (higher = {worse}) ==")
            lines.append(f"  {'condition':20} {'nq':>4} {'nsc':>3} {'rate':>7}   Δ vs cdms-full / status")
        base = f"  {r['condition']:20} {r['n_queries']:>4} {r['n_scenarios']:>3} {r['rate']:>7.3f}"
        if "delta_vs_ref" in r:
            d = f"   {r['delta_vs_ref']:+.3f}"
            if "ci_lo" in r and r["ci_lo"] is not None:
                d += f" [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]"
            d += f"  {r.get('status','')}"
            base += d
        elif r["condition"] == REFERENCE:
            base += "   (reference)"
        lines.append(base)
    return "\n".join(lines)
