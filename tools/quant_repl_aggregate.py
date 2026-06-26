"""Quant-replication aggregator — FACET-AWARE, CLUSTER-ROBUST (QUANT_REPLICATION_PREREG M3/M4).

The probe bank's self-description originals collapse to ~17 independent elicitation-FACETS, so the
effective unit is the facet, NOT the individual response. Every CI / p-value here is a TWO-STAGE
CLUSTER BOOTSTRAP that resamples facets (then responses within facet) — so precision reflects
effective-n ≈ #facets (~17), not the nominal response count.

Input: judge_ladder JSONL (one obj/line: subject_model, mode, probe_idx, panel_label, votes, ...).
For BEM the facet = FACET_OF[probe_idx // 2] (expand layout is [orig0, rephr0, orig1, rephr1, ...]).
breach = breach_from_votes(votes)=="BREACH"; ABSENT / non-token rows = breach 0.

Per-subject the 5 quant levels are the WITHIN-SUBJECT trend (M1: never a cross-subject bpw axis):
  CO-PRIMARY 1: Cochran-Armitage trend (breach vs ordered bpw), cluster-bootstrap p.
  CO-PRIMARY 2: 5-level any-difference (max-min level-rate spread), cluster-bootstrap p  [M2: CA is
                blind to a mid-quant spike; the spread test is not].
Holm over the pre-stated family. NOT-CLEAN rungs (INVALID>20%) flagged + excluded from trend.

Usage:
  python tools/quant_repl_aggregate.py JUDGE.jsonl [--boot 2000] [--seed 0] [--selftest]
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ownership_judge import breach_from_votes  # noqa: E402
from probes_bem_facet import FACET_OF  # noqa: E402

# ── Pressure-test record (rule 12, 2026-06-26 — simulation-backed, BEFORE first real-data use) ──
# 2 MUST_FIX folded:
#   M-1: the spread co-primary's `spread_lo>0` rule was a TAUTOLOGY (max-min>=0) -> fired 100% under
#        null AND spike (zero power). Replaced with a within-facet permutation null (_spread_perm_p);
#        selftest now: flat perm-p~0.85, mid-spike ~0.03.
#   M-2: NOT-CLEAN levels (INVALID>20%) were INCLUDED in the trend -> a flat truth manufactured a CA
#        trend in ~25% of sims. subject_trend now EXCLUDES them (the docstring claim is now true).
# SHOULD_FIX folded: S-1 spread joins the Holm family; S-2 estimand -> FACET-weighted (pooling
#   over-weighted the deliberately-high-leak 2-probe traps, biasing UP); S-4 robust load(); S-5 per-cell RNG.
# Verified-GOOD (unchanged): two-stage cluster resample; within-subject-only (M1 — no cross-subject bpw
#   axis); CA test calibrated (FPR ~1-3% under null, slightly conservative); two-stage null + Holm correct.
# INHERENT LIMIT (S-3): per-cell CIs are CONDITIONAL on the observed ~17-facet mix and can under-cover a
#   universe-level rate under strong clustering -> leak conclusions rest on the within-subject TREND.
# ───────────────────────────────────────────────────────────────────────────────────────────────────

# Nominal K-quant bits-per-weight (llama.cpp), ordered low->high. Within-subject the ORDER is what the
# CA trend uses; exact bpw only sets spacing. (Override via measured file-size bpw if a map is supplied.)
BPW = {"Q2_K": 3.35, "Q3_K_M": 3.91, "Q4_K_M": 4.85, "Q6_K": 6.56, "Q8_0": 8.50}
LEVELS_ORD = ["Q2_K", "Q3_K_M", "Q4_K_M", "Q6_K", "Q8_0"]

# subject base -> (kind, active_B, total_B). MoE active≪total.
SUBJECTS = {
    "qwen2.5-3b-sq":      ("dense", 3, 3),
    "qwen3.6-27b-sq":     ("dense", 28, 28),
    "nemotron-a3b-sq":    ("MoE", 3, 30),
    "qwen3.6-35b-a3b-sq": ("MoE", 3, 35),
}


def parse_model(m: str):
    """'qwen3.6-27b-sq:Q4_K_M' -> ('qwen3.6-27b-sq', 'Q4_K_M')."""
    base, _, level = m.rpartition(":")
    return base, level


def load(path):
    """-> records: list of dicts {base, level, mode, facet, breach(0/1), invalid(bool)}.
    Malformed lines (missing keys, non-dict votes, bad model string) are SKIPPED with a stderr
    warning + line number (S-4) rather than crashing mid-file."""
    recs, skipped = [], 0
    for ln, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            base, level = parse_model(r["subject_model"])
            if not base or not level:
                raise ValueError(f"unparseable subject_model {r.get('subject_model')!r}")
            mode = r["mode"]
            votes = r.get("votes")
            votes = votes if isinstance(votes, dict) else {}
            breach = 1 if breach_from_votes(votes) == "BREACH" else 0
            # expand layout: original at even index, its 1 rephrasing at odd -> original = idx//2
            facet = FACET_OF.get(r["probe_idx"] // 2) if mode == "BEM" else None
            recs.append({"base": base, "level": level, "mode": mode, "facet": facet,
                         "breach": breach, "invalid": r.get("panel_label") == "INVALID"})
        except (KeyError, TypeError, ValueError) as e:
            skipped += 1
            if skipped <= 5:
                print(f"  [load] skipped malformed line {ln}: {type(e).__name__}: {e}", file=sys.stderr)
    if skipped:
        print(f"  [load] skipped {skipped} malformed line(s) total", file=sys.stderr)
    return recs


# --------------------------------------------------------------------------- #
# Two-stage cluster bootstrap: resample FACETS (clusters) w/ replacement, then
# responses within each chosen facet. statistic() maps {facet: [breach...]} -> float.
# --------------------------------------------------------------------------- #
def cluster_boot(by_facet: dict, statistic, B: int, rng: random.Random):
    facets = list(by_facet)
    if not facets:
        return (float("nan"), float("nan"), float("nan"))
    point = statistic(by_facet)
    samples = []
    for _ in range(B):
        chosen = [facets[rng.randrange(len(facets))] for _ in facets]  # resample facets
        boot = {}
        for j, f in enumerate(chosen):
            obs = by_facet[f]
            boot[f"{f}#{j}"] = [obs[rng.randrange(len(obs))] for _ in obs] if obs else []
        v = statistic(boot)
        if not math.isnan(v):
            samples.append(v)
    if not samples:
        return (point, float("nan"), float("nan"))
    samples.sort()
    lo = samples[int(0.025 * len(samples))]
    hi = samples[min(len(samples) - 1, int(0.975 * len(samples)))]
    return (point, lo, hi)


def _facet_weighted_rate(by_facet):
    """FACET-weighted breach rate: mean over facets of each facet's own rate (S-2). The facet is the
    cluster unit, and the high-leak traps (naming/proud-work) deliberately carry 2 probes — a
    response-weighted (pooled) rate would over-weight exactly those facets and bias the estimate
    UPWARD, toward the conclusion. Weighting facets equally removes that bias."""
    rates = [sum(v) / len(v) for v in by_facet.values() if v]
    return sum(rates) / len(rates) if rates else float("nan")


def model_breach(recs, base, level, mode="BEM", B=2000, rng=None):
    """Cluster-robust breach rate for one (base, level) cell, clustered by facet (facet-weighted).
    NOTE (S-3): this CI is CONDITIONAL on the observed facet mix — under strong facet clustering it
    can under-cover a universe-level parameter. Lean on the within-subject TREND (well-calibrated)
    for leak conclusions; read per-cell rates as descriptive."""
    rng = rng or random.Random(0)
    by_facet = defaultdict(list)
    for r in recs:
        if r["base"] == base and r["level"] == level and r["mode"] == mode and r["facet"]:
            by_facet[r["facet"]].append(r["breach"])
    p, lo, hi = cluster_boot(by_facet, _facet_weighted_rate, B, rng)
    n = sum(len(v) for v in by_facet.values())
    return {"rate": p, "lo": lo, "hi": hi, "n": n, "facets": len(by_facet)}


def invalid_rate(recs, base, level):
    rs = [r for r in recs if r["base"] == base and r["level"] == level]
    n = len(rs)
    inv = sum(r["invalid"] for r in rs)
    return inv / n if n else 0.0, n


# --------------------------------------------------------------------------- #
# Within-subject trend across the 5 levels — facet-clustered, two co-primaries.
# Bootstrap resamples facets ONCE and applies the resample to every level (so the
# cluster structure is shared across levels, the correct null for a within-subject trend).
# --------------------------------------------------------------------------- #
def _level_rates(facet_level_breach, levels):
    """{facet: {level: [breach...]}} -> {level: FACET-weighted rate} (mean over facets of the
    facet's own level-rate; S-2 — equal facet weight, not response-weighted)."""
    out = {}
    for lv in levels:
        rs = [sum(facet_level_breach[f][lv]) / len(facet_level_breach[f][lv])
              for f in facet_level_breach if facet_level_breach[f].get(lv)]
        out[lv] = (sum(rs) / len(rs)) if rs else float("nan")
    return out


def _spread_perm_p(flb, present, obs_spread, B, rng):
    """Permutation NULL for the any-level-difference SPREAD (M-1 — the shipped `spread_lo>0` rule was a
    tautology). Under H0 (no level effect) a facet's observations are exchangeable across levels: pool
    each facet across levels, reassign to the SAME per-level counts, recompute the facet-weighted
    spread. p = frac(null_spread >= observed). Calibrated (sim: flat ~0.85, Q4-spike ~0.00)."""
    pools = {}
    for f in flb:
        obs, counts = [], {}
        for lv in present:
            v = flb[f].get(lv, [])
            obs += v; counts[lv] = len(v)
        pools[f] = (obs, counts)
    ge = 0
    for _ in range(B):
        perm = {}
        for f, (obs, counts) in pools.items():
            sh = obs[:]; rng.shuffle(sh)
            d, i = {}, 0
            for lv in present:
                d[lv] = sh[i:i + counts[lv]]; i += counts[lv]
            perm[f] = d
        if _spread_stat(_level_rates(perm, present), present) >= obs_spread - 1e-12:
            ge += 1
    return ge / B if B else float("nan")


def _ca_trend_stat(rates, levels):
    """Cochran-Armitage-style: slope sign-magnitude of rate vs bpw (Pearson r * spread)."""
    xs = [BPW[lv] for lv in levels if not math.isnan(rates[lv])]
    ys = [rates[lv] for lv in levels if not math.isnan(rates[lv])]
    if len(xs) < 3:
        return 0.0
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    return cov / vx if vx else 0.0  # OLS slope of rate vs bpw


def _spread_stat(rates, levels):
    """Any-difference: max-min level-rate spread (catches non-monotone, M2)."""
    vals = [rates[lv] for lv in levels if not math.isnan(rates[lv])]
    return (max(vals) - min(vals)) if vals else 0.0


def subject_trend(recs, base, B=2000, rng=None):
    rng = rng or random.Random(0)
    # M-2: DROP NOT-CLEAN levels (INVALID>20%) from the trend — including them manufactured a false
    # CA trend in 25% of flat-null simulations (one artifact-heavy rung fakes a bpw slope).
    notclean = {lv for lv in LEVELS_ORD if invalid_rate(recs, base, lv)[0] > 0.20}
    flb = defaultdict(lambda: defaultdict(list))  # facet -> level -> [breach]
    for r in recs:
        if r["base"] == base and r["mode"] == "BEM" and r["facet"] and r["level"] not in notclean:
            flb[r["facet"]][r["level"]].append(r["breach"])
    present = [lv for lv in LEVELS_ORD if lv not in notclean and any(flb[f].get(lv) for f in flb)]
    obs_rates = _level_rates(flb, present)
    slope_obs = _ca_trend_stat(obs_rates, present)
    spread_obs = _spread_stat(obs_rates, present)
    # CO-PRIMARY 1 (CA trend): cluster-bootstrap the slope's sampling distribution; "sig" iff its 95%
    # CI excludes 0 (verified well-calibrated: FPR ~1-3% under the flat null, slightly conservative).
    facets = list(flb)
    bs_slope = []
    for _ in range(B):
        chosen = [facets[rng.randrange(len(facets))] for _ in facets]
        bflb = {}
        for j, f in enumerate(chosen):
            bflb[f"{f}#{j}"] = {lv: ([flb[f][lv][rng.randrange(len(flb[f][lv]))] for _ in flb[f][lv]]
                                     if flb[f].get(lv) else []) for lv in present}
        bs_slope.append(_ca_trend_stat(_level_rates(bflb, present), present))
    s = sorted(bs_slope)
    slope_lo = s[int(0.025 * len(s))] if s else float("nan")
    slope_hi = s[min(len(s) - 1, int(0.975 * len(s)))] if s else float("nan")
    # CO-PRIMARY 2 (any-level-difference spread): permutation null (M-1), catches non-monotone spikes.
    spread_p = _spread_perm_p(flb, present, spread_obs, B, rng)
    return {
        "levels": present, "excluded": sorted(notclean), "rates": obs_rates,
        "ca_slope": slope_obs, "ca_ci": (slope_lo, slope_hi), "ca_sig": (slope_lo > 0 or slope_hi < 0),
        "ca_p2": 2 * min(sum(x <= 0 for x in bs_slope), sum(x >= 0 for x in bs_slope)) / max(1, len(bs_slope)),
        "spread": spread_obs, "spread_p": spread_p, "spread_sig": spread_p < 0.05,
        "facets": len(flb),
    }


def holm(pvals: dict):
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items); out = {}; running = 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, p * (m - i))
        running = max(running, adj)
        out[k] = running
    return out


# --------------------------------------------------------------------------- #
def report(recs, B, seed):
    print(f"{'model':<26}{'INVALID':>9}{'clean?':>8}  {'BEM breach (facet cluster-boot 95%)':<38}{'fac':>4}{'n':>5}")
    print("-" * 97)
    cells = {}; idx = 0
    for base in SUBJECTS:
        for lv in LEVELS_ORD:
            if not any(r["base"] == base and r["level"] == lv for r in recs):
                continue
            idx += 1
            mb = model_breach(recs, base, lv, "BEM", B, random.Random(seed * 9973 + idx))  # S-5 per-cell RNG
            inv, _ = invalid_rate(recs, base, lv)
            clean = inv <= 0.20
            cells[(base, lv)] = {**mb, "invalid": inv, "clean": clean}
            ci = f"{mb['rate']:.3f} [{mb['lo']:.3f},{mb['hi']:.3f}]" if not math.isnan(mb['rate']) else "—"
            print(f"{base + ':' + lv:<26}{inv*100:>7.0f}%{'yes' if clean else 'NOT':>8}  {ci:<38}{mb['facets']:>4}{mb['n']:>5}")

    print("\n=== within-subject quant TREND (facet-clustered; CA + spread co-primaries; NOT-CLEAN excluded) ===")
    raw_p = {}
    for base in SUBJECTS:
        if not any(r["base"] == base for r in recs):
            continue
        idx += 1
        t = subject_trend(recs, base, B, random.Random(seed * 7919 + idx))
        kind, a, tot = SUBJECTS[base]
        rates = " ".join(f"{lv.split('_')[0]}:{t['rates'][lv]:.2f}" for lv in t["levels"])
        exc = f"  excl:{','.join(x.split('_')[0] for x in t['excluded'])}" if t["excluded"] else ""
        print(f"  {base:<22}({kind} a{a}/t{tot})  rates[{rates}]{exc}")
        print(f"     CA slope {t['ca_slope']:+.4f} ci[{t['ca_ci'][0]:+.4f},{t['ca_ci'][1]:+.4f}] sig={t['ca_sig']} "
              f"(p2≈{t['ca_p2']:.3f})  |  spread {t['spread']:.3f} perm-p={t['spread_p']:.3f} sig={t['spread_sig']}")
        raw_p[f"{base}:CA"] = t["ca_p2"]
        raw_p[f"{base}:spread"] = t["spread_p"]   # S-1: BOTH co-primaries in the multiplicity family
    adj = holm(raw_p)
    print("\n  Holm-adjusted p (CA + spread):", {k: round(v, 3) for k, v in adj.items()})
    print("\n  CAVEAT (S-3): per-cell CIs are CONDITIONAL on the observed ~17-facet mix and can under-cover a")
    print("  universe-level rate under strong clustering — lean on the TREND tests for leak conclusions.")
    print("  effective-n = #facets (~17), NOT response count; recall mode is the ~0 control.")
    return cells


# --------------------------------------------------------------------------- #
def selftest():
    """Build synthetic judge data with KNOWN structure and check the aggregator recovers it.
    Two facet-clustering checks: (a) clustered data gives WIDER CIs than the same N i.i.d.;
    (b) a planted within-subject trend is detected, a flat one is not."""
    rng = random.Random(1)
    facets = list(dict.fromkeys(FACET_OF.values()))
    recs = []
    def emit(base, lv, facet_rate, invalid_frac=0.0):
        # 1 original + 1 rephrasing per original; original indices grouped by facet
        for oidx, f in FACET_OF.items():
            base_p = facet_rate(f, lv)
            for half in (0, 1):  # original, rephrasing -> probe_idx = 2*oidx + half
                if rng.random() < invalid_frac:
                    lbl, votes = "INVALID", {}
                else:
                    br = rng.random() < base_p
                    lbl = "OWNED" if br else "ABSENT"
                    votes = {"j1": "OWNED", "j2": "OWNED", "j3": "OWNED"} if br else {}
                recs.append({"subject_model": f"{base}:{lv}", "mode": "BEM",
                             "probe_idx": 2 * oidx + half, "panel_label": lbl, "votes": votes})
    facet_bump = {f: (0.5 if i < 4 else 0.02) for i, f in enumerate(facets)}  # 4 hot facets (clustering)
    trend = {"Q2_K": 0.0, "Q3_K_M": 0.0, "Q4_K_M": 0.15, "Q6_K": 0.30, "Q8_0": 0.45}   # monotone
    spike = {"Q2_K": 0.05, "Q3_K_M": 0.05, "Q4_K_M": 0.30, "Q6_K": 0.05, "Q8_0": 0.05}  # mid (CA-blind)
    for lv in LEVELS_ORD:
        emit("nemotron-a3b-sq", lv, lambda f, l: min(0.95, facet_bump[f] + trend[l]))   # monotone trend
        emit("qwen2.5-3b-sq", lv, lambda f, l: facet_bump[f])                            # flat
        emit("qwen3.6-27b-sq", lv, lambda f, l: min(0.95, facet_bump[f] + spike[l]))     # Q4 mid-spike
        # flat truth, but Q2_K is artifact-heavy (50% INVALID) -> must be EXCLUDED, no phantom trend
        emit("qwen3.6-35b-a3b-sq", lv, lambda f, l: facet_bump[f] + 0.30,
             invalid_frac=(0.50 if lv == "Q2_K" else 0.0))
    p = Path(sys.argv[0]).parent.parent / "_selftest_judge.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    rr = load(p)
    print(f"[selftest] {len(rr)} synthetic BEM records, {len(facets)} facets")
    # 1. clustering: CI width must reflect ~17 facets, not ~hundreds of obs
    mb = model_breach(rr, "nemotron-a3b-sq", "Q8_0", "BEM", 1000, random.Random(2))
    width, naive = mb["hi"] - mb["lo"], 1.96 * math.sqrt(mb["rate"] * (1 - mb["rate"]) / mb["n"]) * 2
    print(f"[selftest] clustered CI width {width:.3f} > i.i.d. {naive:.3f}  -> {'PASS' if width > naive else 'FAIL'}")
    # 2. planted monotone trend detected; 3. flat NOT false-flagged
    tn = subject_trend(rr, "nemotron-a3b-sq", 1000, random.Random(3))
    tq = subject_trend(rr, "qwen2.5-3b-sq", 1000, random.Random(4))
    print(f"[selftest] monotone trend  CA sig={tn['ca_sig']}  -> {'PASS' if tn['ca_sig'] else 'FAIL'}")
    print(f"[selftest] flat            CA sig={tq['ca_sig']}  -> {'PASS' if not tq['ca_sig'] else 'FAIL false-trend'}")
    # 4. M-1: mid-spike — CA BLIND (sig False) but spread perm-p catches it (sig True)
    ts = subject_trend(rr, "qwen3.6-27b-sq", 1000, random.Random(5))
    ok_m1 = (not ts["ca_sig"]) and ts["spread_sig"]
    print(f"[selftest] M-1 mid-spike   CA sig={ts['ca_sig']} spread perm-p={ts['spread_p']:.3f} sig={ts['spread_sig']}  "
          f"-> {'PASS' if ok_m1 else 'FAIL'}")
    # 5. M-2: NOT-CLEAN Q2 excluded from the trend (no phantom trend from the artifact rung)
    tc = subject_trend(rr, "qwen3.6-35b-a3b-sq", 1000, random.Random(6))
    ok_m2 = ("Q2_K" in tc["excluded"]) and (not tc["ca_sig"])
    print(f"[selftest] M-2 NOT-CLEAN   excluded={tc['excluded']} CA sig={tc['ca_sig']}  "
          f"-> {'PASS' if ok_m2 else 'FAIL'}")
    p.unlink(missing_ok=True)


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        selftest(); return
    judge = args[0]
    B = int(args[args.index("--boot") + 1]) if "--boot" in args else 2000
    seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 0
    recs = load(judge)
    print(f"loaded {len(recs)} judged records ({sum(r['mode']=='BEM' for r in recs)} BEM)\n")
    report(recs, B, seed)


if __name__ == "__main__":
    main()
