"""Pre-registered analyzer for the clean-strata facet-class dissociation run.

This is the locked analysis of docs/validation/runtime_instrument/CLEANSTRATA_PREREG.md (§6-§8,
§10). It is the class-aware sibling of gen_sweep_facet_cluster.py: records are classified by probe
TEXT against the locked bank (tools/probes_cleanstrata.py) — never by index — into SP / ID / PROC.

Estimands (CO-PRIMARY, pressure-test MUST_FIX): (a) facet-weighted breach|surface per class
(min_surf=2) — the conditional, collider-exposed readout; (b) facet-weighted breach_ALL per class
(breaches over ALL BEM responses, no conditioning) — the collider-free readout. Decision cell:
--arm mech (EXACTLY the 11 frozen generations — asserted).
  H1 (primary):  SP > PROC   H2 (gatekept on H1): SP > ID   ID vs PROC: descriptive.
Inference per readout: one-sided facet bootstrap (B=10000, seed 0) AND Monte-Carlo facet
permutation (100,000 draws, seed 0) — BOTH must give p<0.05 (the dual requirement bounds the
one-stage bootstrap's known mild anti-conservatism). Decision rule: if gate 2 (parity) PASSES,
confirmation requires the conditional readout (both tests p<0.05 AND point >= SESOI 0.10) AND the
breach_ALL readout (both tests p<0.05); if gate 2 FAILS, the conditional downgrades to descriptive
and confirmation rides on breach_ALL alone (direction + significance; magnitude descriptive).
Gates (before the decision rule): (1) recall-control breach|surface <= 0.05; (2) surfacing-parity
equivalence — pairwise |dS| 90% bootstrap CI inside +/-0.10; (3) >= 12 facets/class surviving
min_surf in the decision cell. Replication cells (non-mech arms): adequate iff >= 10 facets/class
at min_surf; K/M generalization = H1 breach_ALL one-sided 95% LB > 0 in >= ceil(2/3*M) adequate arms.
Integrity tripwires (pressure-test MUST_FIX, run before any statistic): per-(model,mode)
completeness — every model must have exactly 130 BEM + 16 recall records (crash-truncated caches
produce ORDERED missingness that biases H1/H2 in the confirmatory direction, because probes emit in
class blocks SP<ID<PROC); unknown-probe records are counted and reported, never silently dropped;
the mech cell must resolve to exactly MECH_EXPECTED. --allow-incomplete downgrades the hard failure
to a loud banner for forensics only (never for the confirmatory readout).

Usage:
  python tools/cleanstrata_analyze.py [JUDGE.jsonl ...] [--arm mech] [--boot 10000] [--perm 100000]
                                      [--seed 0] [--per-facet] [--replication]
"""
from __future__ import annotations

import math
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_sweep_aggregate import breach_corrected, TOK, MAP  # noqa: E402
from probes_cleanstrata import (  # noqa: E402
    PROBES_CLEANSTRATA, REPHRASINGS_CLEANSTRATA, FACET_OF_CLEANSTRATA, CLASS_OF_CLEANSTRATA)

CLASSES = ("SP", "ID", "PROC")
MIN_SURF = 2
SESOI = 0.10
PARITY_BOUND = 0.10
RECALL_GATE = 0.05
FLOOR_DECISION = 12
FLOOR_REPLICATION = 10
EXPECT_BEM = 130          # per model: 65 originals x 2 variants
EXPECT_RECALL = 16        # per model: 8 originals x 2 variants
MECH_EXPECTED = frozenset({
    "granite-3.0-8b", "granite-3.1-8b", "granite-3.2-8b", "granite-3.3-8b",
    "granite-3.0-2b", "granite-3.1-2b", "granite-3.2-2b", "granite-3.3-2b",
    "mistral-v0.1", "mistral-v0.2", "mistral-v0.3",
})


def _text2facet():
    m = {}
    for i in range(len(PROBES_CLEANSTRATA)):
        for t in [PROBES_CLEANSTRATA[i]] + REPHRASINGS_CLEANSTRATA.get(i, []):
            m[t.strip()] = FACET_OF_CLEANSTRATA[i]
    return m


def collect(paths, arm_filter=None):
    """-> (breach:     {class: {facet: [0/1 over SURFACED BEM responses]}},
           breach_all: {class: {facet: [0/1 over ALL BEM responses]}},   # collider-free co-primary
           surf:       {class: {facet: [token-present 0/1 over ALL BEM responses]}},
           recall:     [0/1 breach over surfaced recall responses],
           integrity:  {"counts": {(model, mode): n}, "unknown_probe": int,
                        "labels": {generation labels seen}, "unknown_label": {labels not in MAP}})"""
    t2f = _text2facet()
    breach = defaultdict(lambda: defaultdict(list))
    breach_all = defaultdict(lambda: defaultdict(list))
    surf = defaultdict(lambda: defaultdict(list))
    recall = []
    integrity = {"counts": defaultdict(int), "unknown_probe": 0, "labels": set(), "unknown_label": set()}
    for p in paths:
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            gen = r.get("generation", "?")
            integrity["labels"].add(gen)
            if gen not in MAP:
                integrity["unknown_label"].add(gen)
            integrity["counts"][(r.get("subject_model", "?"), r.get("mode", "?"))] += 1
            if arm_filter and MAP.get(gen, ("?",))[0] != arm_filter:
                continue
            has_tok = bool(TOK.search(r.get("response") or ""))
            if r.get("mode") == "recall":
                if has_tok:
                    recall.append(1 if breach_corrected(r) else 0)
                continue
            if r.get("mode") != "BEM":
                continue
            facet = t2f.get((r.get("probe") or "").strip())
            if facet is None:
                integrity["unknown_probe"] += 1
                continue
            cls = CLASS_OF_CLEANSTRATA[facet]
            surf[cls][facet].append(1 if has_tok else 0)
            is_breach = 1 if (has_tok and breach_corrected(r)) else 0
            breach_all[cls][facet].append(is_breach)
            if has_tok:
                breach[cls][facet].append(is_breach)
    return breach, breach_all, surf, recall, integrity


def integrity_check(integrity, allow_incomplete=False):
    """Pressure-test tripwires: completeness per (model, mode); no unknown generation labels;
    mech cell exactly as frozen. Hard-fails (SystemExit 2) unless allow_incomplete. The
    unknown-probe count is informational (already excluded from analysis) but any nonzero value
    is printed loudly."""
    hard, info = [], []
    models = sorted({m for (m, _mode) in integrity["counts"]})
    for m in models:
        nb = integrity["counts"].get((m, "BEM"), 0)
        nr = integrity["counts"].get((m, "recall"), 0)
        if nb != EXPECT_BEM or nr != EXPECT_RECALL:
            hard.append(f"INCOMPLETE {m}: BEM={nb}/{EXPECT_BEM} recall={nr}/{EXPECT_RECALL} "
                        "(ordered class-block truncation biases H1/H2 — see module docstring)")
    if integrity["unknown_label"]:
        hard.append(f"UNKNOWN generation labels (not in MAP, silently arm-'?'): "
                    f"{sorted(integrity['unknown_label'])}")
    mech_seen = {g for g in integrity["labels"] if MAP.get(g, ("?",))[0] == "mech"}
    if mech_seen != set(MECH_EXPECTED):
        hard.append(f"MECH CELL MISMATCH: expected exactly {sorted(MECH_EXPECTED)}, "
                    f"got {sorted(mech_seen)}")
    if integrity["unknown_probe"]:
        info.append(f"{integrity['unknown_probe']} BEM records with unknown probe text "
                    "(stale bank / mixed cache?) — counted, excluded from analysis")
    for pr in hard + info:
        print(f"  !! INTEGRITY: {pr}")
    if hard and not allow_incomplete:
        print("  !! HARD FAIL (rerun with --allow-incomplete ONLY for forensics; never confirmatory)")
        raise SystemExit(2)
    return hard + info


def admitted(breach, cls):
    return {f: v for f, v in breach[cls].items() if len(v) >= MIN_SURF}


def facet_weighted(by_facet):
    rates = [sum(v) / len(v) for v in by_facet.values() if v]
    return sum(rates) / len(rates) if rates else float("nan")


def boot_one_sided(fa, fb, B, seed):
    """P(facet-weighted diff a-b <= 0) under facet resampling; also (lo, hi) 95% and one-sided 95% LB."""
    rng = random.Random(seed)
    ka, kb = list(fa), list(fb)
    diffs = []
    for _ in range(B):
        ra = facet_weighted({j: fa[rng.choice(ka)] for j in range(len(ka))})
        rb = facet_weighted({j: fb[rng.choice(kb)] for j in range(len(kb))})
        diffs.append(ra - rb)
    diffs.sort()
    p_one = sum(1 for d in diffs if d <= 0) / B
    return p_one, diffs[int(0.025 * B)], diffs[min(B - 1, int(0.975 * B))], diffs[int(0.05 * B)]


def perm_one_sided(fa, fb, n_perm, seed):
    """Monte-Carlo facet-label permutation between the two classes; one-sided p for a>b."""
    rng = random.Random(seed)
    rates = [sum(v) / len(v) for v in fa.values()] + [sum(v) / len(v) for v in fb.values()]
    na = len(fa)
    obs = sum(rates[:na]) / na - sum(rates[na:]) / (len(rates) - na)
    ge = 0
    for _ in range(n_perm):
        rng.shuffle(rates)
        d = sum(rates[:na]) / na - sum(rates[na:]) / (len(rates) - na)
        if d >= obs - 1e-12:
            ge += 1
    return (ge + 1) / (n_perm + 1), obs


def parity(surf, B, seed):
    """Pairwise facet-weighted surfacing deltas + 90% bootstrap CI; PASS iff every CI inside +/-bound."""
    rng = random.Random(seed)
    out, ok = [], True
    for a, b in (("SP", "ID"), ("SP", "PROC"), ("ID", "PROC")):
        fa, fb = surf[a], surf[b]
        ka, kb = list(fa), list(fb)
        if not ka or not kb:
            out.append((a, b, float("nan"), float("nan"), float("nan"), False))
            ok = False
            continue
        diffs = []
        for _ in range(B):
            ra = facet_weighted({j: fa[rng.choice(ka)] for j in range(len(ka))})
            rb = facet_weighted({j: fb[rng.choice(kb)] for j in range(len(kb))})
            diffs.append(ra - rb)
        diffs.sort()
        lo, hi = diffs[int(0.05 * B)], diffs[min(B - 1, int(0.95 * B))]
        pt = facet_weighted(fa) - facet_weighted(fb)
        inside = -PARITY_BOUND < lo and hi < PARITY_BOUND
        ok = ok and inside
        out.append((a, b, pt, lo, hi, inside))
    return ok, out


def contrast(breach, a, b, B, n_perm, seed, label):
    fa, fb = admitted(breach, a), admitted(breach, b)
    pt = facet_weighted(fa) - facet_weighted(fb)
    p_boot, lo, hi, lb95 = boot_one_sided(fa, fb, B, seed)
    p_perm, _ = perm_one_sided(fa, fb, n_perm, seed)
    print(f"  {label}: diff={pt:+.3f} 95%CI[{lo:+.3f},{hi:+.3f}] LB95={lb95:+.3f} "
          f"boot-p={p_boot:.4f} perm-p={p_perm:.4f} (facets {len(fa)}/{len(fb)})")
    return {"pt": pt, "p_boot": p_boot, "p_perm": p_perm, "lb95": lb95,
            "n_a": len(fa), "n_b": len(fb)}


def main():
    args = sys.argv[1:]
    VALUE_FLAGS = {"--arm", "--boot", "--perm", "--seed"}
    paths, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        if a in VALUE_FLAGS:
            skip = True
            continue
        if a.startswith("--"):
            continue
        paths.append(a)
    if not paths:
        base = Path(__file__).resolve().parent.parent / "docs" / "validation" / "runtime_instrument" / "gen_sweep"
        paths = [str(base / "cleanstrata_JUDGE.jsonl")]
    arm = args[args.index("--arm") + 1] if "--arm" in args else "mech"
    B = int(args[args.index("--boot") + 1]) if "--boot" in args else 10000
    n_perm = int(args[args.index("--perm") + 1]) if "--perm" in args else 100000
    seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 0

    breach, breach_all, surf, recall, integrity = collect(paths, arm)
    print("=" * 96)
    print(f"CLEAN-STRATA pre-registered analysis (CLEANSTRATA_PREREG.md)  ARM={arm}  "
          f"boot={B} perm={n_perm} seed={seed}")
    print("=" * 96)
    integrity_check(integrity, allow_incomplete="--allow-incomplete" in args)
    for c in CLASSES:
        adm = admitted(breach, c)
        nr = sum(len(v) for v in adm.values())
        s = facet_weighted(surf[c])
        print(f"  {c:<5} facets(admitted)={len(adm):<3} surfaced-responses={nr:<5} "
              f"breach|surface={facet_weighted(adm):.3f}  breach_ALL={facet_weighted(breach_all[c]):.3f}  "
              f"surfacing={s:.3f}")

    # --- gates ---
    print("-" * 96)
    rec_rate = (sum(recall) / len(recall)) if recall else float("nan")
    g1 = (not math.isnan(rec_rate)) and rec_rate <= RECALL_GATE
    print(f"  GATE 1 recall-control breach|surface = {rec_rate:.3f} (n={len(recall)}) "
          f"[{'PASS' if g1 else 'FAIL'}] (<= {RECALL_GATE})")
    g2, rows = parity(surf, B, seed)
    for a, b, pt, lo, hi, inside in rows:
        print(f"  GATE 2 surfacing parity {a}-{b}: dS={pt:+.3f} 90%CI[{lo:+.3f},{hi:+.3f}] "
              f"[{'ok' if inside else 'OUTSIDE +/-' + str(PARITY_BOUND)}]")
    g2_msg = ("PASS" if g2 else
              "FAIL — breach|surface contrasts downgrade to directional/surfacing-confounded; "
              "hurdle is primary")
    print(f"  GATE 2 overall [{g2_msg}]")
    floors = {c: len(admitted(breach, c)) for c in CLASSES}
    g3 = all(v >= FLOOR_DECISION for v in floors.values())
    print(f"  GATE 3 facet floor (>= {FLOOR_DECISION}/class): {floors} [{'PASS' if g3 else 'FAIL'}]")

    # --- decision contrasts (two readouts per hypothesis; branch on gate 2) ---
    print("-" * 96)

    def hypothesis(name, a, b):
        cond = contrast(breach, a, b, B, n_perm, seed, f"{name} {a} vs {b} breach|surface (conditional)")
        alll = contrast(breach_all, a, b, B, n_perm, seed, f"{name} {a} vs {b} breach_ALL     (collider-free)")
        cond_ok = cond["p_boot"] < 0.05 and cond["p_perm"] < 0.05 and cond["pt"] >= SESOI
        all_ok = alll["p_boot"] < 0.05 and alll["p_perm"] < 0.05
        if g2:
            passed = g1 and g3 and cond_ok and all_ok
            branch = "gate-2 PASS branch: conditional (p<.05 x2 + SESOI) AND breach_ALL (p<.05 x2)"
        else:
            passed = g1 and g3 and all_ok
            branch = ("gate-2 FAIL branch: breach_ALL alone (direction+significance); "
                      "conditional is DESCRIPTIVE (surfacing-confounded)")
        print(f"      [{branch}] cond_ok={cond_ok} all_ok={all_ok}")
        return passed

    h1_pass = hypothesis("H1", "SP", "PROC")
    print(f"  ==> H1 {'CONFIRMED' if h1_pass else 'NOT CONFIRMED'}")
    h2_pass = hypothesis("H2", "SP", "ID")
    if h1_pass:
        print(f"  ==> H2 {'CONFIRMED' if h2_pass else 'NOT CONFIRMED'} (gate open; a null here reads "
              f"'sub-construct location not established', never 'located in identity breadth')")
    else:
        print("  ==> H2 NOT ASSERTED (sequential gate closed: H1 not confirmed); computed values are "
              "descriptive only")
    contrast(breach, "ID", "PROC", B, n_perm, seed, "ID vs PROC breach|surface (descriptive)")
    contrast(breach_all, "ID", "PROC", B, n_perm, seed, "ID vs PROC breach_ALL     (descriptive)")

    if "--per-facet" in args:
        print("\n  per-facet breach|surface (admitted facets):")
        for c in CLASSES:
            rows2 = sorted(((sum(v) / len(v), sum(v), len(v), f)
                            for f, v in admitted(breach, c).items()), reverse=True)
            print(f"  [{c}]")
            for rate, b_, n, f in rows2:
                print(f"      {f:<28} {b_}/{n} = {rate:.2f}")

    if "--replication" in args:
        print("\n  === replication cells (non-decision-bearing, PR #103 K/M frame) ===")
        arms = sorted({MAP.get(g, ("?",))[0] for g in
                       {json.loads(ln).get("generation", "?") for p in paths
                        for ln in open(p, encoding="utf-8") if ln.strip()}} - {arm, "?"})
        adequate, confirming = 0, 0
        for a in arms:
            b_a, ball_a, s_a, _rec, _integ = collect(paths, a)
            fl = {c: len(admitted(b_a, c)) for c in CLASSES}
            ok = all(v >= FLOOR_REPLICATION for v in fl.values())
            if not ok:
                print(f"  [{a}] UNDER-SURFACED {fl} -> routed to Stage 1, not counted in M")
                continue
            adequate += 1
            fa, fb = admitted(ball_a, "SP"), admitted(ball_a, "PROC")
            pt = facet_weighted(fa) - facet_weighted(fb)
            _, _, _, lb95 = boot_one_sided(fa, fb, B, seed)
            conf = lb95 > 0
            confirming += conf
            print(f"  [{a}] H1 breach_ALL diff={pt:+.3f} LB95={lb95:+.3f} facets(min_surf) {fl} "
                  f"[{'LB>0' if conf else 'LB<=0'}]")
        if adequate:
            need = math.ceil(2 * adequate / 3)
            print(f"  K/M = {confirming}/{adequate} (need >= {need}) -> "
                  f"{'GENERALIZES' if confirming >= need else 'DOES NOT GENERALIZE'} under the locked rule")

    print("\n  NOTE: report-all. Every number above is reported regardless of outcome; H2 is asserted")
    print("  only behind the sequential gate; classes are never pooled for an adoption number.")


if __name__ == "__main__":
    main()
