"""Full cube runner + analysis for the differentiation experiment (CORE THESIS).
See DIFFERENTIATION_PREREG.md. Read two ways: CROSS-DISPOSITION (similar>different?) and
DRIFT-AGAINST-SELF (does disposition-salience move the self from its keep-all baseline?).

Efficiency: under none/uniform/random the disposition enters only via goal_hint (=None there), so
A, B, C, U are BYTE-IDENTICAL — the collapse is structural. Per seed we run 3 disposition-blind
baselines + (A,B,C × {0.25, 0.0}) under disposition-salience = 9 runs (not 32). U's disposition-
salience column ≡ the uniform baseline (no goals). The same-disposition NULL = focal disposition
across DIFFERENT histories (seeds), which must stay HIGH.
"""
from __future__ import annotations

import json
import random
import statistics
from pathlib import Path

from cdms.config import Config
from cdms.embeddings import Embedder
from tools.eval_harness.differentiation_experiment import (
    run_subject, _shared_history, _shared_history_pair, _DISPOSITIONS)
from tools.eval_harness.provenance import assert_worktree_cdms, cdms_provenance

DISPOS = ["A", "B", "C"]
GATE_FLOORS = [0.25, 0.0]
METRICS = ["raw", "surfaced"]
_BLIND = ["none", "uniform", "random"]
F_LEVELS = [0.0, 0.25, 0.5, 0.75, 1.0]


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def run_cube(seeds, cycles: int, base: Path, emb) -> dict:
    """results[seed][key] = run dict. key = (condition, gate_floor|None, dispo|'blind')."""
    results = {}
    for s in seeds:
        hist = _shared_history(s, cycles)
        r = {}
        for cond in _BLIND:                      # disposition-blind: A=B=C=U, run once
            r[(cond, None, "blind")] = run_subject("A", cond, base / f"s{s}-{cond}", s, emb, cycles, hist=hist)
        for gf in GATE_FLOORS:                   # disposition-salience: A,B,C differ; U == uniform baseline
            for d in DISPOS:
                r[("disposition-salience", gf, d)] = run_subject(
                    d, "disposition-salience", base / f"s{s}-ds{gf}-{d}", s, emb, cycles, hist=hist, gate_floor=gf)
        results[s] = r
    return results


def _ci(vals, n=2000, seed=0):
    """Bootstrap 95% CI over SEEDS (the independent unit). Deterministic."""
    vals = [v for v in vals if v is not None]
    if len(vals) < 2:
        return {"mean": (vals[0] if vals else float("nan")), "lo": float("nan"), "hi": float("nan"), "k": len(vals)}
    rng = random.Random(seed)
    means = sorted(sum(vals[rng.randrange(len(vals))] for _ in vals) / len(vals) for _ in range(n))
    return {"mean": statistics.mean(vals), "lo": means[int(0.025 * n)], "hi": means[int(0.975 * n)], "k": len(vals)}


def cross_disposition(results: dict) -> dict:
    """Per (gate_floor, metric): similar (A·B), different (A·C), null (A·U=uniform) under disposition-
    salience, with CIs over seeds. Baselines give 1.0 by construction (A=B=C) — the collapse."""
    out = {}
    seeds = sorted(results)
    for gf in GATE_FLOORS:
        for m in METRICS:
            sim, dif, nul = [], [], []
            for s in seeds:
                r = results[s]
                A, B, C = (r[("disposition-salience", gf, d)][m] for d in ("A", "B", "C"))
                U = r[("uniform", None, "blind")][m]
                sim.append(jaccard(A, B)); dif.append(jaccard(A, C)); nul.append(jaccard(A, U))
            out[(gf, m)] = {"similar_AB": _ci(sim), "different_AC": _ci(dif), "null_AU": _ci(nul),
                            "separation": _ci([a - b for a, b in zip(sim, dif)])}
    # the structural collapse: A=B=C under every blind condition -> cross-disposition overlap == 1.0
    out["blind_collapse"] = {c: 1.0 for c in _BLIND}
    return out


def drift_against_self(results: dict, dispo="A") -> dict:
    """How far each condition moves the self from its keep-all `none` baseline (lower overlap = more
    drift). Does disposition-salience move it MORE than generic (uniform) / random forgetting?"""
    out = {}
    seeds = sorted(results)
    for m in METRICS:
        row = {}
        for cond, key in [("uniform", ("uniform", None, "blind")), ("random", ("random", None, "blind")),
                          ("disposition-salience@0.25", ("disposition-salience", 0.25, dispo)),
                          ("disposition-salience@0.0", ("disposition-salience", 0.0, dispo))]:
            ov = [jaccard(results[s][key][m], results[s][("none", None, "blind")][m]) for s in seeds]
            row[cond] = _ci(ov)   # overlap WITH the none baseline; lower = more drift
        out[m] = row
    return out


def same_disposition_null(results: dict, dispo="A", gf=0.25) -> dict:
    """NULL: focal disposition across DIFFERENT histories (seed pairs) must stay HIGH — differentiation
    tracks disposition, not the forgetting process manufacturing divergence from noise."""
    seeds = sorted(results)
    out = {}
    for m in METRICS:
        vals = []
        for i in range(len(seeds)):
            for j in range(i + 1, len(seeds)):
                a = results[seeds[i]][("disposition-salience", gf, dispo)][m]
                b = results[seeds[j]][("disposition-salience", gf, dispo)][m]
                vals.append(jaccard(a, b))
        out[m] = _ci(vals)
    return out


def factorial_decomposition(results: dict, gf=0.25) -> dict:
    """From the 3-disposition × N-history disposition-salience runs (a factorial): the MAIN EFFECT of
    disposition (same history, A vs C), the MAIN EFFECT of history (same disposition A, seed i vs j),
    the BOTH-differ cell, and the interaction (is both ≈ additive?). Effect = 1 − overlap (drop from a
    self-identical 1.0). Bootstrap over histories (the independent unit)."""
    seeds = sorted(results)
    out = {}
    for m in METRICS:
        def ident(s, d):
            return results[s][("disposition-salience", gf, d)][m]
        disp = [jaccard(ident(s, "A"), ident(s, "C")) for s in seeds]                       # only disposition differs
        hist = [jaccard(ident(seeds[i], "A"), ident(seeds[j], "A"))
                for i in range(len(seeds)) for j in range(i + 1, len(seeds))]                # only history differs
        both = [jaccard(ident(seeds[i], "A"), ident(seeds[j], "C"))
                for i in range(len(seeds)) for j in range(i + 1, len(seeds))]                # both differ
        d_eff, h_eff = _ci([1 - x for x in disp]), _ci([1 - x for x in hist])
        b_eff = _ci([1 - x for x in both])
        additive = d_eff["mean"] + h_eff["mean"]                                             # if separable
        out[m] = {"disposition_effect": d_eff, "history_effect": h_eff, "both_effect": b_eff,
                  "additive_prediction": additive, "interaction": b_eff["mean"] - additive}
    return out


def fsweep(seeds, cycles: int, base: Path, emb, gate_floor=0.25) -> dict:
    """The FULCRUM: two subjects sharing fraction f of their history, diverging after, crossed with
    disposition SAME (A,A) vs DIFF (A,C). Overlap vs f, per pair. New runs (paired histories)."""
    out = {}
    for s in seeds:
        for f in F_LEVELS:
            h1, h2 = _shared_history_pair(s, f, cycles)
            for name, (d1, d2) in (("same", ("A", "A")), ("diff", ("A", "C"))):
                r1 = run_subject(d1, "disposition-salience", base / f"fs{s}-{f}-{name}-1", s, emb, cycles,
                                 hist=h1, gate_floor=gate_floor)
                r2 = run_subject(d2, "disposition-salience", base / f"fs{s}-{f}-{name}-2", s, emb, cycles,
                                 hist=h2, gate_floor=gate_floor)
                out[(s, f, name)] = {mm: jaccard(r1[mm], r2[mm]) for mm in METRICS}
    return out


def fsweep_analysis(fs: dict) -> dict:
    seeds = sorted({s for (s, _, _) in fs})
    out = {}
    for m in METRICS:
        for name in ("same", "diff"):
            out[(m, name)] = {f: _ci([fs[(s, f, name)][m] for s in seeds]) for f in F_LEVELS}
    return out


def _entity_set(idset):
    return frozenset(e for (_, e) in idset)


def _goal_overlap(d1, d2):
    a, b = _DISPOSITIONS[d1], _DISPOSITIONS[d2]
    return len(a & b) / len(a | b) if (a | b) else 1.0


def _pearson(x, y):
    n = len(x)
    if n < 2:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    vx = sum((a - mx) ** 2 for a in x)
    vy = sum((b - my) ** 2 for b in y)
    return cov / ((vx * vy) ** 0.5) if vx > 0 and vy > 0 else 0.0


def entity_separation(results: dict) -> dict:
    """CO-PRIMARY (M1): separation on ENTITY sets (drop the noisy relation label). ~0 => NO entity-level
    individuation, stated plainly regardless of the tuple-metric numbers."""
    seeds = sorted(results)
    out = {}
    for gf in GATE_FLOORS:
        for m in METRICS:
            sim = [jaccard(_entity_set(results[s][("disposition-salience", gf, "A")][m]),
                           _entity_set(results[s][("disposition-salience", gf, "B")][m])) for s in seeds]
            dif = [jaccard(_entity_set(results[s][("disposition-salience", gf, "A")][m]),
                           _entity_set(results[s][("disposition-salience", gf, "C")][m])) for s in seeds]
            out[(gf, m)] = _ci([a - b for a, b in zip(sim, dif)])
    return out


def permutation_null(results: dict, n_perm=2000) -> dict:
    """M2 (kills the tautology): does identity-overlap TRACK goal-set overlap beyond chance? The 3 pairs
    have fixed goal-overlaps {A·B~.60, A·C 0, B·C~.14}; correlate goal-overlap vs identity-overlap across
    seeds, then SHUFFLE the pairing for the null. r>0 & small p => disposition individuates in a
    goal-STRUCTURED way (not a construction artifact); r~0 => the separation is noise."""
    import random as _r
    seeds = sorted(results)
    pairs = [("A", "B"), ("A", "C"), ("B", "C")]
    gov = [_goal_overlap(*p) for p in pairs]
    out = {}
    for gf in GATE_FLOORS:
        for m in METRICS:
            xs, ys = [], []
            for s in seeds:
                for (d1, d2), g in zip(pairs, gov):
                    xs.append(g)
                    ys.append(jaccard(results[s][("disposition-salience", gf, d1)][m],
                                      results[s][("disposition-salience", gf, d2)][m]))
            obs = _pearson(xs, ys)
            rng = _r.Random(0)
            null = []
            for _ in range(n_perm):
                yp = ys[:]; rng.shuffle(yp)
                null.append(_pearson(xs, yp))
            p = (sum(1 for v in null if abs(v) >= abs(obs)) + 1) / (n_perm + 1)
            out[(gf, m)] = {"r": obs, "p": p, "n_points": len(xs)}
    return out


def _cluster_ci(per_seed_pairs_fn, seeds, n=2000, seed=0):
    """Cluster-bootstrap over SEEDS (M4): resample seeds, recompute the pairwise statistic on the resampled
    seed set — not over dependent seed-pairs. per_seed_pairs_fn(resampled_seeds) -> list of pair values."""
    import random as _r
    base = per_seed_pairs_fn(seeds)
    if not base:
        return {"mean": float("nan"), "lo": float("nan"), "hi": float("nan"), "k": 0}
    rng = _r.Random(seed)
    means = []
    for _ in range(n):
        rs = [seeds[rng.randrange(len(seeds))] for _ in seeds]
        vals = per_seed_pairs_fn(rs)
        if vals:
            means.append(sum(vals) / len(vals))
    means.sort()
    return {"mean": sum(base) / len(base), "lo": means[int(0.025 * len(means))],
            "hi": means[int(0.975 * len(means))], "k": len(seeds)}


def _preconditions(results: dict, cycles: int) -> dict:
    """Fail-loud (M5): eviction fraction correctly scaled (evicted / (cycles*TURNS_PER_CYCLE)); traits
    formed; whether forgetting actually fired. HALT flag for the caller to enforce."""
    from tools.eval_harness.differentiation_experiment import TURNS_PER_CYCLE
    ingested = max(1, cycles * TURNS_PER_CYCLE)
    ev, ntr = [], []
    for s in results:
        for run in results[s].values():
            ev.append(run["evicted"] / ingested)
            ntr.append(len(run["raw"]))
    med_ev = statistics.median(ev) if ev else 0.0
    min_ntr = min(ntr) if ntr else 0
    return {"median_evicted_frac": med_ev, "median_n_traits": statistics.median(ntr) if ntr else 0,
            "min_n_traits": min_ntr, "erasure_fired": med_ev >= 0.20,
            "HALT": (med_ev < 0.20 or min_ntr < 3)}


def analyze(results: dict, cycles: int, fs: dict = None) -> dict:
    a = {"cross_disposition": cross_disposition(results),
         "entity_separation": entity_separation(results),        # CO-PRIMARY (M1)
         "permutation_null": permutation_null(results),          # M2 — the tautology-killer
         "drift_against_self": drift_against_self(results),
         "factorial_decomposition": {gf: factorial_decomposition(results, gf) for gf in GATE_FLOORS},
         "preconditions": _preconditions(results, cycles)}
    if fs is not None:
        a["fsweep"] = fsweep_analysis(fs)
    return a


def _fmt(ci):
    return f"{ci['mean']:.3f} [{ci['lo']:.3f},{ci['hi']:.3f}]"


def main(seeds=range(16), cycles=250, out="docs/validation/eval_harness/DIFFERENTIATION_RESULTS.md"):
    import os
    os.environ["CDMS_EVAL_MODE"] = "1"
    os.environ["CDMS_EMBED_BACKEND"] = "fastembed"
    assert_worktree_cdms()
    import tempfile
    base = Path(tempfile.mkdtemp(prefix="diffcube-"))
    emb = Embedder(Config(home=base))
    assert emb.backend == "fastembed", emb.backend
    seeds = list(seeds)
    results = run_cube(seeds, cycles, base, emb)
    fs = fsweep(seeds, cycles, base, emb)
    an = analyze(results, cycles, fs)
    pc = an["preconditions"]

    # Verdict from the CO-PRIMARY (entity-set) + permutation null, per the pre-registered decision rule.
    es = an["entity_separation"][(0.25, "surfaced")]
    pn = an["permutation_null"][(0.25, "surfaced")]
    if pc["HALT"]:
        verdict = ("INVALID / NULL-by-inertness — forgetting did not fire "
                   f"(median evicted {pc['median_evicted_frac']:.2f} < 0.20); nothing to individuate.")
    elif es["lo"] <= 0 and pn["p"] > 0.05:
        verdict = ("NULL — no entity-level individuation (entity-set sep CI includes 0) AND identity-overlap "
                   f"does not track goal-overlap (permutation r={pn['r']:+.2f}, p={pn['p']:.3f}).")
    else:
        verdict = (f"SIGNAL — entity-set sep={_fmt(es)}, permutation r={pn['r']:+.2f} p={pn['p']:.3f} "
                   "(check H3 same-disp vs diff-disp before claiming).")

    lines = ["# Differentiation experiment — results", "",
             f"## VERDICT (as-shipped gf=0.25, surfaced): {verdict}", "",
             "## Run config", "```json",
             json.dumps({**cdms_provenance(), "seeds": len(seeds), "cycles": cycles,
                         "embedder": emb.backend, "preconditions": pc}, indent=2), "```",
             "", "## CO-PRIMARY — entity-set separation (drop relation; ~0 => NO entity-level individuation)"]
    for gf in GATE_FLOORS:
        for m in METRICS:
            lines.append(f"- gate_floor={gf} [{m}]: entity-set sep={_fmt(an['entity_separation'][(gf, m)])}")
    lines += ["", "## Permutation null (M2) — does identity-overlap TRACK goal-overlap beyond chance?"]
    for gf in GATE_FLOORS:
        for m in METRICS:
            v = an["permutation_null"][(gf, m)]
            lines.append(f"- gate_floor={gf} [{m}]: r={v['r']:+.3f}  p={v['p']:.4f}  (n={v['n_points']})")
    lines += ["", "## Cross-disposition tuple metric (similar > different; NOTE: separation lives in the "
              "relation label — see co-primary above)"]
    cd = an["cross_disposition"]
    for gf in GATE_FLOORS:
        for m in METRICS:
            v = cd[(gf, m)]
            lines.append(f"- gate_floor={gf} [{m}]: similar_AB={_fmt(v['similar_AB'])}  "
                         f"different_AC={_fmt(v['different_AC'])}  **sep={_fmt(v['separation'])}**  null_AU={_fmt(v['null_AU'])}")
    lines += ["", "blind conditions collapse cross-disposition overlap to 1.0 by construction "
              "(A=B=C under none/uniform/random).", "",
              "## Factorial: disposition vs history main effects + interaction (effect = 1 − overlap)"]
    for gf in GATE_FLOORS:
        for m in METRICS:
            fd = an["factorial_decomposition"][gf][m]
            lines.append(f"- gate_floor={gf} [{m}]: disposition_effect={_fmt(fd['disposition_effect'])}  "
                         f"history_effect={_fmt(fd['history_effect'])}  both={_fmt(fd['both_effect'])}  "
                         f"interaction={fd['interaction']:+.3f}")
    lines += ["", "## Fulcrum — overlap vs shared-history fraction f (SAME vs DIFF disposition)"]
    for m in METRICS:
        for name in ("same", "diff"):
            row = "  ".join(f"f={f}:{an['fsweep'][(m, name)][f]['mean']:.3f}" for f in F_LEVELS)
            lines.append(f"- [{m}] {name}-disposition: {row}")
    lines += ["", "## Drift-against-self (overlap WITH the keep-all `none` baseline; lower = more drift)"]
    for m in METRICS:
        lines.append(f"- [{m}]: " + "  ".join(f"{c}={_fmt(v)}" for c, v in an["drift_against_self"][m].items()))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {out}")
    return an


if __name__ == "__main__":
    main()
