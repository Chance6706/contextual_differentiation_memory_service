"""Ablation-delta analysis — the v2 primary endpoints.

For each (axis, metric), report each condition's rate and the DELTA vs the reference
(cdms-full) with a PAIRED bootstrap 95% CI (paired by query id, since every condition
runs the same queries). A mechanism "resolves" when its delta CI excludes 0. This is
the whole point: we read ablation contrasts (Δ = ablation − full), not a leaderboard.
"""
from __future__ import annotations

import random
from collections import defaultdict

REFERENCE = "cdms-full"

# Per (axis, metric): does a HIGHER metric value mean the mechanism is FAILING (a leak /
# obedience / cross-contamination) or WORKING? Used only to annotate the "protective
# direction" of a resolved delta — never to change the numbers.
#   "harm"    : higher = worse (injection obeyed, isolation leak, self-attribution)
#   "benefit" : higher = better (forget-complete, differentiation, recall)
METRIC_SENSE = {
    ("injection", "obeyed"): "harm",
    ("injection", "surfaced"): "harm",   # $0 retrieval-layer proxy: higher = fence let it through
    ("multi_project", "leaked_other"): "harm",
    ("identity_leak", "self_attributed"): "harm",
    ("right_to_forget", "forgot"): "benefit",
    ("differentiation", "overlap"): "harm",   # lower trait overlap = more differentiated
}


def paired_bootstrap_delta(a: list[float], b: list[float], n_boot: int = 2000, seed: int = 0):
    """Δ = mean(a) − mean(b), paired by index (a,b same queries, same length). Percentile
    95% CI over n_boot paired resamples. Deterministic (seeded)."""
    n = len(a)
    if n == 0 or len(b) != n:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed)
    point = sum(a) / n - sum(b) / n
    deltas = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        deltas.append(sum(a[i] for i in idx) / n - sum(b[i] for i in idx) / n)
    deltas.sort()
    lo = deltas[int(0.025 * n_boot)]
    hi = deltas[min(int(0.975 * n_boot), n_boot - 1)]
    return point, lo, hi


def ablation_deltas(observations: list[dict], *, reference: str = REFERENCE,
                    n_boot: int = 2000, seed: int = 0) -> list[dict]:
    """observations = [{condition, axis, metric, qid, value}, ...]. Returns one row per
    (axis, metric, condition): its rate + (for non-reference conditions) Δ vs reference
    with a paired bootstrap CI aligned on shared query ids."""
    by: dict[tuple, dict] = defaultdict(dict)   # (axis, metric, condition) -> {qid: value}
    for o in observations:
        by[(o["axis"], o["metric"], o["condition"])][o["qid"]] = float(o["value"])

    axes_metrics = sorted({(a, m) for (a, m, _c) in by})
    out: list[dict] = []
    for axis, metric in axes_metrics:
        ref = by.get((axis, metric, reference))
        conds = sorted({c for (a, m, c) in by if a == axis and m == metric})
        for cond in conds:
            vals = by[(axis, metric, cond)]
            rate = sum(vals.values()) / len(vals) if vals else float("nan")
            row = {"axis": axis, "metric": metric, "condition": cond,
                   "n": len(vals), "rate": rate, "sense": METRIC_SENSE.get((axis, metric), "?")}
            if ref and cond != reference:
                shared = sorted(set(vals) & set(ref))
                if shared:
                    a = [vals[q] for q in shared]
                    b = [ref[q] for q in shared]
                    d, lo, hi = paired_bootstrap_delta(a, b, n_boot, seed)
                    row.update({"delta_vs_ref": d, "ci_lo": lo, "ci_hi": hi,
                                "n_paired": len(shared), "resolved": (lo > 0 or hi < 0)})
            out.append(row)
    return out


def format_table(rows: list[dict]) -> str:
    """Human-readable ablation-delta table grouped by (axis, metric)."""
    lines = []
    cur = None
    for r in sorted(rows, key=lambda r: (r["axis"], r["metric"], r["condition"] != REFERENCE, r["condition"])):
        key = (r["axis"], r["metric"])
        if key != cur:
            cur = key
            lines.append(f"\n== {r['axis']} / {r['metric']} ({r['sense']}: higher = "
                         f"{'worse' if r['sense']=='harm' else 'better' if r['sense']=='benefit' else '?'}) ==")
            lines.append(f"  {'condition':20} {'n':>4} {'rate':>7}   Δ vs cdms-full [95% CI]")
        base = f"  {r['condition']:20} {r['n']:>4} {r['rate']:>7.3f}"
        if "delta_vs_ref" in r:
            mark = "  RESOLVED" if r["resolved"] else ""
            base += f"   {r['delta_vs_ref']:+.3f} [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]{mark}"
        elif r["condition"] == REFERENCE:
            base += "   (reference)"
        lines.append(base)
    return "\n".join(lines)
