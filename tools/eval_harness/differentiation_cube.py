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
from cdms.embeddings import Embedder, cosine
from tools.eval_harness.differentiation_experiment import (
    run_subject, run_erasure_subject, _shared_history, _shared_history_pair, _DISPOSITIONS)
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


# =================================================================================================
# ERASURE ARM (CORE THESIS) — DIFFERENTIATION_ERASURE_PREREG.md (LOCKED). Identity = what SURVIVES
# neglect. Disposition drives which topics keep getting lived; the forgetting POLICY (salience /
# none / random) is the ablation. PRIMARY metric = raw surviving-gist ENTITY set (drop relation);
# 500 cycles so even a support-capped gist (idle survival ~396) is deliberately cleared.
# =================================================================================================
ERASURE_DISPOS = ["A", "B", "C", "U"]
ERASURE_CYCLES = 500
SHARE_FRAC = 0.08


def _ekey(policy: str, gf, dispo: str):
    """Cube key: gate_floor is meaningful only for the salience policy (none/random ignore it)."""
    return (policy, gf if policy == "salience" else None, dispo)


def run_erasure_cube(seeds, cycles: int, base: Path, emb, share_frac: float = SHARE_FRAC,
                     snapshot_every: int = 0) -> dict:
    """results[seed][(policy, gf|None, dispo)] = erasure run dict. Per seed (16 runs): the full
    {A,B,C,U} × {salience@0.25, salience@0.0, none, random} grid (Josh: all four dispositions under
    every policy so disposition-vs-uniform is visible in each). U is the dispositionless null (no
    neglect -> keeps everything under any policy)."""
    results = {}
    for s in seeds:
        r = {}
        for d in ERASURE_DISPOS:
            r[_ekey("salience", 0.25, d)] = run_erasure_subject(
                d, "salience", base / f"s{s}-sal25-{d}", s, emb, cycles, share_frac, 0.25, snapshot_every)
            r[_ekey("salience", 0.0, d)] = run_erasure_subject(
                d, "salience", base / f"s{s}-sal00-{d}", s, emb, cycles, share_frac, 0.0, snapshot_every)
            r[_ekey("none", None, d)] = run_erasure_subject(
                d, "none", base / f"s{s}-none-{d}", s, emb, cycles, share_frac, 0.25, snapshot_every)
            r[_ekey("random", None, d)] = run_erasure_subject(
                d, "random", base / f"s{s}-rand-{d}", s, emb, cycles, share_frac, 0.25, snapshot_every)
        results[s] = r
    return results


def erasure_null_AU(results: dict, gf=0.25) -> dict:
    """Disposition vs UNIFORM (dispositionless): entity jaccard(A, U) per policy. U keeps everything,
    so this is how far a disposition's survivor sits from 'no selective neglect': ~0.5 under salience
    (A's goal topics inside U's 8), ~1.0 under none (nothing forgotten -> A also keeps all 8)."""
    seeds = sorted(results)
    out = {}
    for policy, g in [("salience", gf), ("none", None), ("random", None)]:
        def per(rs, policy=policy, g=g):
            return [jaccard(_ent(results[s][_ekey(policy, g, "A")]), _ent(results[s][_ekey(policy, g, "U")]))
                    for s in rs if _ekey(policy, g, "U") in results[s]]
        out[policy] = _cluster_ci(per, seeds)
    return out


def erasure_factorial(results: dict, gf=0.25) -> dict:
    """Disposition-effect (1 − jaccard(A,C), same past, different disposition) vs history-effect
    (1 − same-disposition overlap across seeds). In the erasure arm disposition_effect should dominate
    at the topic level; whether history_effect is truly 0 is the question the PROSE probe re-asks."""
    disp = erasure_divergence(results, "salience", gf, pair=("A", "C"))
    same = erasure_same_disp_null(results, gf)
    return {"disposition_effect": disp,
            "history_effect": {"mean": 1.0 - same["mean"], "lo": 1.0 - same["hi"],
                               "hi": 1.0 - same["lo"], "k": same["k"]}}


def _ent(run: dict) -> frozenset:
    """Entity set behind a run's raw surviving-gist state (the PRIMARY, relation dropped)."""
    return _entity_set(run["raw"])


def erasure_entity_separation(results: dict, policy: str, gf) -> dict:
    """CO-PRIMARY (M1): entity-set separation = jaccard(A,B) − jaccard(A,C), cluster-bootstrapped over
    SEEDS (M4/F4). Under `salience` this should be strongly POSITIVE (similar keep-overlap > different);
    under `none` it collapses to ~0 (nothing forgotten -> all keep all 8 -> both jaccards ~1)."""
    seeds = sorted(results)

    def per(rs):
        out = []
        for s in rs:
            r = results[s]
            A, B, C = (_ent(r[_ekey(policy, gf, d)]) for d in ("A", "B", "C"))
            out.append(jaccard(A, B) - jaccard(A, C))
        return out
    return _cluster_ci(per, seeds)


def erasure_divergence(results: dict, policy: str, gf, pair=("A", "C")) -> dict:
    """Entity-set DIVERGENCE (1 − jaccard) for a disposition pair under a policy — the H1/H2 quantity.
    H1: divergence(A,C) under salience > under none. H2: > under random."""
    seeds = sorted(results)
    d1, d2 = pair

    def per(rs):
        return [1.0 - jaccard(_ent(results[s][_ekey(policy, gf, d1)]),
                              _ent(results[s][_ekey(policy, gf, d2)])) for s in rs]
    return _cluster_ci(per, seeds)


def erasure_same_disp_null(results: dict, gf=0.25, dispo="A") -> dict:
    """H3: the SAME disposition across DIFFERENT histories (seeds) must stay HIGH-overlap under salience —
    else the divergence is seed noise, not disposition (the frozen-cube failure mode). Cluster-boot over
    the seed set; the pairwise mean is reported (dependent pairs, so CI is via seed resampling)."""
    seeds = sorted(results)

    def per(rs):
        vals = []
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                if rs[i] == rs[j]:          # skip self-pairs: a seed vs itself = overlap 1.0 (degenerate;
                    continue                # A3/A4 — self-pairing pins the bootstrap CI lower bound)
                vals.append(jaccard(_ent(results[rs[i]][_ekey("salience", gf, dispo)]),
                                    _ent(results[rs[j]][_ekey("salience", gf, dispo)])))
        return vals
    return _cluster_ci(per, seeds)


def erasure_permutation_null(results: dict, gf=0.25, n_perm=2000) -> dict:
    """M2 permutation null on the ENTITY arm. WARNING (A2/A1/A3 CONFIRMED): at full erasure this is
    CIRCULAR and DEGENERATE — survivor ≡ goalset, so entity-overlap is DEFINITIONALLY EQUAL to the
    goal-overlap it is correlated against ⇒ r=+1.0 and tiny p trivially, and the n=seed×3 pooling is
    pseudo-replicated (violates M4). It does NOT provide independent corroboration in this arm and is
    NOT cited by the verdict. Retained only for the PROSE arm (where measured ≠ predictor) and for a
    future PARTIAL-erasure design (where the survivor is not the goalset)."""
    import random as _r
    seeds = sorted(results)
    pairs = [("A", "B"), ("A", "C"), ("B", "C")]
    gov = [_goal_overlap(*p) for p in pairs]
    xs, ys = [], []
    for s in seeds:
        for (d1, d2), g in zip(pairs, gov):
            xs.append(g)
            ys.append(jaccard(_ent(results[s][_ekey("salience", gf, d1)]),
                              _ent(results[s][_ekey("salience", gf, d2)])))
    obs = _pearson(xs, ys)
    rng = _r.Random(0)
    null = []
    for _ in range(n_perm):
        yp = ys[:]
        rng.shuffle(yp)
        null.append(_pearson(xs, yp))
    p = (sum(1 for v in null if abs(v) >= abs(obs)) + 1) / (n_perm + 1)
    return {"r": obs, "p": p, "n_points": len(xs)}


def erasure_preconditions(results: dict) -> dict:
    """F3 topic-disappearance gate (gist-level, NOT episode churn). Fail-loud HALT unless, under
    salience: off-goal topics FORMED at the shared-past peak, then DROPPED materially by the end, with
    real gist decay — and a HIGH-TIER off-goal gist was actually evicted (Josh: deliberately see one go).
    `none` is checked as the negative control (off-goal must NOT drop there)."""
    seeds = sorted(results)
    sal = [results[s][_ekey("salience", 0.25, d)] for s in seeds for d in ("A", "B", "C")]
    non = [results[s][_ekey("none", None, d)] for s in seeds for d in ("A", "B", "C")]
    drop = [r["offgoal_peak_n"] - r["offgoal_final_n"] for r in sal]
    decayed = [r["gists_decayed"] for r in sal]
    none_drop = [r["offgoal_peak_n"] - r["offgoal_final_n"] for r in non]
    top_evicted = [max(r["peak_offgoal_support"]) for r in sal
                   if r["peak_offgoal_support"] and not r["final_offgoal_support"]]
    med_drop = statistics.median(drop) if drop else 0
    med_decay = statistics.median(decayed) if decayed else 0
    min_final_ent = min((len(r["final_ents"]) for r in sal), default=0)
    offgoal_formed = all(r["offgoal_peak_n"] >= 1 for r in sal) if sal else False
    fired = med_drop >= 2 and med_decay >= 1 and offgoal_formed
    return {
        "median_offgoal_drop_salience": med_drop,
        "median_gists_decayed_salience": med_decay,
        "median_offgoal_drop_none": statistics.median(none_drop) if none_drop else 0,
        "max_high_tier_gist_evicted": max(top_evicted) if top_evicted else 0,
        "min_final_entities": min_final_ent,
        "offgoal_formed_at_peak": offgoal_formed,
        "erasure_fired": fired,
        "HALT": not (fired and min_final_ent >= 2),
    }


# --- PROSE-space (EXPLORATORY / NON-PRE-REGISTERED — NOT in the locked prereg §3) -----------------
# A $0 upstream SCREEN, necessary-not-sufficient for the functional H4; NOT evidence of behavioral
# individuation (A4). The tuple metric saturates (disposition owns the topic set, history washes out);
# these render each self's real preamble prose and compare by semantic cosine. CAVEATS the 4-agent
# pressure-test CONFIRMED, to carry into any interpretation: (1) different zero-points — set-Jaccard is
# a hard 0, cosine is never 0, so "topic 0 vs prose >0" is partly manufactured; the real floor is the
# `none` prose separation (~0.03). (2) history_effect needs n>=16 + the self-pair-free CI (fixed above)
# + cosmetics (integer counts, gist ordering) stripped before it reflects semantic content. (3) the
# prose permutation null tests DISPOSITION (topic words), not the HISTORY axis — it is NOT a history null;
# the real history null is the fulcrum (does same-disposition distance scale with shared-history f).

def _prose_cos(ra: dict, rb: dict):
    va, vb = ra.get("prose_vec"), rb.get("prose_vec")
    if va is None or vb is None:
        return None
    return cosine(va, vb)


def erasure_prose_separation(results: dict, policy: str, gf) -> dict:
    """PROSE co-primary: cos(A,B) − cos(A,C) on the rendered preamble, cluster-boot over seeds."""
    seeds = sorted(results)

    def per(rs):
        out = []
        for s in rs:
            r = results[s]
            ab = _prose_cos(r[_ekey(policy, gf, "A")], r[_ekey(policy, gf, "B")])
            ac = _prose_cos(r[_ekey(policy, gf, "A")], r[_ekey(policy, gf, "C")])
            if ab is not None and ac is not None:
                out.append(ab - ac)
        return out
    return _cluster_ci(per, seeds)


def erasure_prose_history_effect(results: dict, gf=0.25, dispo="A") -> dict:
    """THE stratum test. Same disposition, DIFFERENT seeds. Topic-space history_effect = 0 (identical
    topic set). Prose-space = 1 − mean cos(A_i, A_j). If > 0, history lives in the PROSE though it is
    invisible in the tuples — the boundary where the owner flips from disposition to history."""
    seeds = sorted(results)

    def per(rs):
        vals = []
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                if rs[i] == rs[j]:          # skip self-pairs: same store -> cos 1.0 -> distance 0 (degenerate;
                    continue                # A3 CONFIRMED this pins lo at 0, so mean==hi at low n)
                c = _prose_cos(results[rs[i]][_ekey("salience", gf, dispo)],
                               results[rs[j]][_ekey("salience", gf, dispo)])
                if c is not None:
                    vals.append(1.0 - c)
        return vals
    return _cluster_ci(per, seeds)


def erasure_prose_disposition_effect(results: dict, gf=0.25, pair=("A", "C")) -> dict:
    """Prose-space disposition_effect = 1 − cos(A,C): the coarse cause seen in the fine medium."""
    seeds = sorted(results)
    d1, d2 = pair

    def per(rs):
        out = []
        for s in rs:
            c = _prose_cos(results[s][_ekey("salience", gf, d1)], results[s][_ekey("salience", gf, d2)])
            if c is not None:
                out.append(1.0 - c)
        return out
    return _cluster_ci(per, seeds)


def erasure_prose_permutation_null(results: dict, gf=0.25, n_perm=2000) -> dict:
    """Null for the prose probe: does prose SIMILARITY track goal-overlap beyond chance? Correlate
    goal-overlap {A·B~.60, A·C 0, B·C~.14} vs prose cosine across seeds, shuffle the pairing."""
    import random as _r
    seeds = sorted(results)
    pairs = [("A", "B"), ("A", "C"), ("B", "C")]
    gov = [_goal_overlap(*p) for p in pairs]
    xs, ys = [], []
    for s in seeds:
        for (d1, d2), g in zip(pairs, gov):
            c = _prose_cos(results[s][_ekey("salience", gf, d1)], results[s][_ekey("salience", gf, d2)])
            if c is not None:
                xs.append(g)
                ys.append(c)
    if len(xs) < 3:
        return {"r": float("nan"), "p": float("nan"), "n_points": len(xs)}
    obs = _pearson(xs, ys)
    rng = _r.Random(0)
    null = []
    for _ in range(n_perm):
        yp = ys[:]
        rng.shuffle(yp)
        null.append(_pearson(xs, yp))
    p = (sum(1 for v in null if abs(v) >= abs(obs)) + 1) / (n_perm + 1)
    return {"r": obs, "p": p, "n_points": len(xs)}


def erasure_trajectory(results: dict, gf=0.25) -> dict:
    """The 'how it differentiates over time' view: mean surviving-entity count per cycle-snapshot for
    A (salience) vs A (none), across seeds. Requires the cube run with snapshot_every>0."""
    seeds = sorted(results)
    out = {}
    for label, key in (("salience_A", _ekey("salience", gf, "A")), ("none_A", _ekey("none", None, "A"))):
        by_cycle = {}
        for s in seeds:
            for snap in results[s][key].get("traj", []):
                by_cycle.setdefault(snap["cycle"], []).append(snap["n_ents"])
        out[label] = {c: (sum(v) / len(v)) for c, v in sorted(by_cycle.items())}
    return out


def erasure_analyze(results: dict) -> dict:
    pc = erasure_preconditions(results)
    sep = {pol_gf: erasure_entity_separation(results, *pol_gf)
           for pol_gf in [("salience", 0.25), ("salience", 0.0), ("none", None), ("random", None)]}
    div_AC = {pol_gf: erasure_divergence(results, *pol_gf, pair=("A", "C"))
              for pol_gf in [("salience", 0.25), ("salience", 0.0), ("none", None), ("random", None)]}
    return {
        "preconditions": pc,
        "entity_separation": sep,                                   # M1 co-primary (cluster-boot)
        "divergence_AC": div_AC,                                    # H1/H2 magnitude
        "null_AU": erasure_null_AU(results),                        # disposition vs uniform (per policy)
        "factorial": erasure_factorial(results),                   # disposition-effect vs history-effect
        "same_disp_null": {gf: erasure_same_disp_null(results, gf) for gf in (0.25, 0.0)},  # H3
        "permutation_null": {gf: erasure_permutation_null(results, gf) for gf in (0.25, 0.0)},  # M2
        "trajectory": erasure_trajectory(results),                 # over-time
        # PROSE-space (the stratum boundary): does history/individuation live in the rendered text?
        "prose_separation": {pol_gf: erasure_prose_separation(results, *pol_gf)
                             for pol_gf in [("salience", 0.25), ("none", None), ("random", None)]},
        "prose_history_effect": erasure_prose_history_effect(results),   # headline: history in the prose?
        "prose_disposition_effect": erasure_prose_disposition_effect(results),
        "prose_permutation_null": erasure_prose_permutation_null(results),
    }


def _erasure_verdict(an: dict) -> str:
    """Honest verdict. FOUR-AGENT PRESSURE-TEST 2026-07-17: at the LOCKED full-erasure endpoint
    (cycles=500) the surviving entity set == the disposition's goalset BY CONSTRUCTION, so entity-set
    separation is TRUE-BY-CONSTRUCTION (zero-variance CIs), the M2 entity permutation null is CIRCULAR
    (entity-overlap ≡ goal-overlap → r=1 trivially — NOT cited here), and H2 (salience vs random) is
    unreachable (both ≡ goalset). The empirical content is the DECAY TRAJECTORY (preconditions).
    Individuation must be tested at PARTIAL erasure and/or the functional H4 — see the RESULTS doc."""
    pc = an["preconditions"]
    if pc["HALT"]:
        return (f"INVALID / NULL-by-inertness — erasure did not fire (median off-goal drop "
                f"{pc['median_offgoal_drop_salience']} < 2 or no high-tier eviction); nothing to individuate.")
    sal = an["entity_separation"][("salience", 0.25)]
    non = an["entity_separation"][("none", None)]
    rnd = an["entity_separation"][("random", None)]
    he = an["factorial"]["history_effect"]
    # Endpoint-tautology detector: a zero-variance separation CI or ~0 history effect ⇒ survivor ≡ goalset.
    degenerate = (abs(sal["hi"] - sal["lo"]) < 1e-9) or (abs(he["mean"]) < 1e-9)
    if degenerate:
        return ("ENDPOINT-DEGENERATE — NOT an individuation result. At full erasure survivor ≡ goalset by "
                f"construction: separation {_fmt(sal)} is true-by-construction (zero-variance), "
                f"history_effect {_fmt(he)} ≈ 0, and salience {_fmt(sal)} == random {_fmt(rnd)} so H2 is "
                "unreachable here. Real content = the decay TRAJECTORY; test individuation at PARTIAL "
                "erasure + functional H4 (see DIFFERENTIATION_ERASURE_RESULTS.md).")
    # Non-degenerate (partial-erasure) regime: real comparisons with the CORRECTED H3 unit test
    # (same-disp OVERLAP vs diff-disp OVERLAP — both jaccards; the old code compared overlap to a
    # separation-DIFFERENCE, a scale mismatch that could flip the verdict — A1 MUST_FIX #3).
    diff_overlap = 1.0 - an["divergence_AC"][("salience", 0.25)]["mean"]
    h3 = an["same_disp_null"][0.25]
    h3_ok = h3["lo"] > diff_overlap
    h1 = sal["lo"] > max(0.0, non["hi"])
    h2 = sal["lo"] > rnd["hi"]
    if not h3_ok:
        return (f"INVALID — H3 fails: same-disposition overlap {_fmt(h3)} not above diff-disposition "
                f"overlap {diff_overlap:.3f}; divergence may be seed noise.")
    # NB: this runner reports SEPARATION, never "differentiation" — the word was a laundering vector
    # (flagged 3× across the arc). Structural separation at this substrate is topic-driven until proven
    # otherwise; interpretation is GATED on tautology-exclusion + a permutation null + the functional H4.
    if h1 and h2:
        return (f"SEPARATION-PRESENT (salience-specific) — INTERPRETATION GATED, not an individuation "
                f"claim. salience={_fmt(sal)} > none={_fmt(non)} AND > random={_fmt(rnd)}; H3 holds. "
                "Not individuation until survivor ⊄ goalset (endpoint-tautology excluded), a ≥1000-shuffle "
                "permutation null is beaten, and the functional H4 confirms — see the RESULTS doc.")
    if h1:
        return (f"SEPARATION-PRESENT (forgetting, NOT salience-specific) — INTERPRETATION GATED. "
                f"salience {_fmt(sal)} > none {_fmt(non)} but NOT above random {_fmt(rnd)} — H2 open. "
                "Same gating as above; not an individuation claim.")
    return f"NULL — salience separation {_fmt(sal)} not clearly above none {_fmt(non)}."


def erasure_main(seeds=range(16), cycles=ERASURE_CYCLES, share_frac=SHARE_FRAC, snapshot_every=62,
                 out="docs/validation/eval_harness/DIFFERENTIATION_ERASURE_RESULTS.md"):
    import os
    os.environ["CDMS_EVAL_MODE"] = "1"
    os.environ["CDMS_EMBED_BACKEND"] = "fastembed"
    assert_worktree_cdms()
    import tempfile
    base = Path(tempfile.mkdtemp(prefix="erasurecube-"))
    emb = Embedder(Config(home=base))
    assert emb.backend == "fastembed", emb.backend
    seeds = list(seeds)
    results = run_erasure_cube(seeds, cycles, base, emb, share_frac, snapshot_every)
    an = erasure_analyze(results)
    pc = an["preconditions"]
    verdict = _erasure_verdict(an)

    lines = ["# Differentiation via ERASURE — results (CORE THESIS)", "",
             f"## VERDICT (as-shipped gf=0.25, raw entity set): {verdict}", "",
             "## Run config", "```json",
             json.dumps({**cdms_provenance(), "seeds": len(seeds), "cycles": cycles,
                         "share_frac": share_frac, "embedder": emb.backend, "preconditions": pc}, indent=2),
             "```", "",
             "## Precondition — topic disappearance (F3, gist-level not episode churn)",
             f"- off-goal entities DROP (salience, peak→end): median **{pc['median_offgoal_drop_salience']}**  "
             f"(none control: {pc['median_offgoal_drop_none']})",
             f"- gists decayed (salience): median **{pc['median_gists_decayed_salience']}**",
             f"- **high-tier off-goal gist evicted**: support **{pc['max_high_tier_gist_evicted']}** "
             f"(deliberately cleared a strong trait) · min surviving entities {pc['min_final_entities']}",
             "",
             "## CO-PRIMARY — entity-set separation (jaccard(A,B)−jaccard(A,C), cluster-boot over seeds)"]
    for pol, gf in [("salience", 0.25), ("salience", 0.0), ("random", None), ("none", None)]:
        lines.append(f"- {pol}" + (f"@{gf}" if gf is not None else "") + f": {_fmt(an['entity_separation'][(pol, gf)])}")
    lines += ["", "## H1/H2 — divergence(A,C) = 1−jaccard (salience should exceed none AND random)"]
    for pol, gf in [("salience", 0.25), ("salience", 0.0), ("random", None), ("none", None)]:
        lines.append(f"- {pol}" + (f"@{gf}" if gf is not None else "") + f": {_fmt(an['divergence_AC'][(pol, gf)])}")
    lines += ["", "## H3 — same-disposition-across-seeds overlap (must stay HIGH; else divergence is seed noise)"]
    for gf in (0.25, 0.0):
        lines.append(f"- gf={gf}: {_fmt(an['same_disp_null'][gf])}")
    lines += ["", "## M2 — permutation null (entity-overlap tracks goal-overlap beyond chance?)"]
    for gf in (0.25, 0.0):
        v = an["permutation_null"][gf]
        lines.append(f"- gf={gf}: r={v['r']:+.3f}  p={v['p']:.4f}  (n={v['n_points']})")
    lines += ["", "## Disposition vs UNIFORM (dispositionless U) — entity jaccard(A,U) per policy"]
    for pol in ("salience", "none", "random"):
        lines.append(f"- {pol}: {_fmt(an['null_AU'][pol])}")
    fac = an["factorial"]
    lines += ["", "## Factorial (entity/topic level) — disposition dominates, history washes out?",
              f"- disposition_effect (1−A·C): {_fmt(fac['disposition_effect'])}",
              f"- history_effect (1−same-disp across seeds): {_fmt(fac['history_effect'])}"]
    ph, pd, pp = an["prose_history_effect"], an["prose_disposition_effect"], an["prose_permutation_null"]
    lines += ["", "## PROSE-space (the stratum boundary — is the finer signal in the rendered text?)",
              f"- **history_effect: topic={fac['history_effect']['mean']:.3f} vs PROSE={_fmt(ph)}**  "
              "(> 0 in prose while ~0 in topic ⇒ history lives in the prose)",
              f"- disposition_effect (prose, 1−cos(A,C)): {_fmt(pd)}",
              "- prose separation cos(A,B)−cos(A,C): " +
              "  ".join(f"{pol}={_fmt(an['prose_separation'][(pol, gf)])}"
                        for pol, gf in [("salience", 0.25), ("none", None), ("random", None)]),
              f"- prose permutation null (cos tracks goal-overlap?): r={pp['r']:+.3f}  p={pp['p']:.4f}  (n={pp['n_points']})"]
    lines += ["", "## Trajectory — mean surviving-entity count over cycles (the 'differentiates over time' view)"]
    for label, series in an["trajectory"].items():
        row = "  ".join(f"c{c}:{v:.2f}" for c, v in series.items())
        lines.append(f"- {label}: {row}")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {out}")
    return an


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
