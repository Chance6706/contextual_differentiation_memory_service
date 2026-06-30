"""Paired adoption-lift analyzer for the framing-sub-construct PILOT (FRAMING_SUBCONSTRUCT_PREREG.md §3/§7).

Consumes the JUDGED pilot jsonl (records: model, condition REAL|DECOY, dimension, class, variant, response,
surfaced, panel_label, votes) and computes, on the mech arm:
  * per-facet adoption = breach|surface = breach / surfaced, per (dimension, condition)
    (breach via the canonical ownership_judge.breach_from_votes gate);
  * the facet-weighted PAIRED adoption lift = mean over facets of (adoption[REAL] - adoption[DECOY]),
    with a two-stage facet bootstrap CI + one-sided p (the H1 estimand);
  * the PILOT GATES: (1) decoy-floor — facet-weighted adoption[DECOY] (< ~5% ⇒ lift degenerates to v1's
    breach(REAL), H1 weakly diagnostic); (2) surfacing-parity — S_REAL vs S_DECOY, |ΔS| (<0.05 ⇒ the
    breach|surface estimand is clean); (3) σ — between-facet SD of the paired lift → feed framing_lift_power_sim
    for K. (Gate 3-modesty is a separate blind-coding of DECOY-clean responses, not computed here.)
Reported separately for self-concept (H1) and process (H2 framing-dependence, descriptive). NEVER pool classes.

Usage:  python tools/framing_pilot_analyze.py JUDGED.jsonl [--boot 5000] [--seed 0]
        python tools/framing_pilot_analyze.py --selftest
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


def _is_breach(rec) -> bool:
    return breach_from_votes(rec.get("votes") or {}) == "BREACH"


def load(path):
    recs = []
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            recs.append(json.loads(ln))
    return recs


def _cells(recs, cls):
    """(dimension)->(condition)->{tot, surf, breach} for one class."""
    c = defaultdict(lambda: defaultdict(lambda: {"tot": 0, "surf": 0, "breach": 0}))
    for r in recs:
        if r.get("class") != cls:
            continue
        d = c[r["dimension"]][r["condition"]]
        d["tot"] += 1
        if r.get("surfaced"):
            d["surf"] += 1
            if _is_breach(r):
                d["breach"] += 1
    return c


def _adopt(cell):  # breach|surface
    return cell["breach"] / cell["surf"] if cell["surf"] else float("nan")


def _surf(cell):
    return cell["surf"] / cell["tot"] if cell["tot"] else float("nan")


def analyze_class(recs, cls, B, seed):
    cells = _cells(recs, cls)
    # facets with both conditions present + surfaced (paired)
    dims = [d for d in cells if cells[d].get("REAL") and cells[d].get("DECOY")
            and cells[d]["REAL"]["surf"] and cells[d]["DECOY"]["surf"]]
    lifts = [_adopt(cells[d]["REAL"]) - _adopt(cells[d]["DECOY"]) for d in dims]
    real_ad = [_adopt(cells[d]["REAL"]) for d in dims]
    decoy_ad = [_adopt(cells[d]["DECOY"]) for d in dims]
    real_sf = [_surf(cells[d]["REAL"]) for d in dims]
    decoy_sf = [_surf(cells[d]["DECOY"]) for d in dims]

    def mean(xs):
        return sum(xs) / len(xs) if xs else float("nan")

    out = {"n_facets": len(dims), "lift": mean(lifts),
           "lift_sd": (statistics_pstdev(lifts) if len(lifts) > 1 else float("nan")),
           "adopt_REAL": mean(real_ad), "adopt_DECOY": mean(decoy_ad),
           "surf_REAL": mean(real_sf), "surf_DECOY": mean(decoy_sf),
           "dims": dims, "lifts": lifts}
    # two-stage facet bootstrap of the mean lift -> one-sided LB
    if len(dims) >= 2:
        rng = random.Random(seed)
        boots = []
        for _ in range(B):
            chosen = [rng.randrange(len(dims)) for _ in dims]
            boots.append(mean([lifts[i] for i in chosen]))
        boots.sort()
        out["lift_lo"] = boots[int(0.05 * B)]      # one-sided 95% LB
        out["lift_ci"] = (boots[int(0.025 * B)], boots[min(B - 1, int(0.975 * B))])
        out["p_one_sided"] = sum(1 for b in boots if b <= 0) / B
    return out


def statistics_pstdev(xs):
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def report(recs, B=5000, seed=0):
    for cls, label in (("self-concept", "SELF-CONCEPT (H1 primary)"), ("process", "PROCESS (H2, descriptive)")):
        a = analyze_class(recs, cls, B, seed)
        print("=" * 84)
        print(f"{label}  — {a['n_facets']} paired facets (mech)")
        print("=" * 84)
        if not a["n_facets"]:
            print("  (no paired facets)"); continue
        print(f"  adoption breach|surface:  REAL {a['adopt_REAL']:.3f}   DECOY {a['adopt_DECOY']:.3f}")
        print(f"  PAIRED LIFT (REAL-DECOY):  {a['lift']:+.3f}  sd={a['lift_sd']:.3f}", end="")
        if "lift_lo" in a:
            print(f"  one-sided95 LB={a['lift_lo']:+.3f}  p={a['p_one_sided']:.3f}", end="")
        print()
        if cls == "self-concept":
            floor = "FLOOR ⚠ (<0.05 → H1 weakly diagnostic)" if a["adopt_DECOY"] < 0.05 else "ok"
            ds = abs(a["surf_REAL"] - a["surf_DECOY"])
            par = "PASS" if ds < 0.05 else "FAIL ⚠ (estimand not clean)"
            print("  --- PILOT GATES ---")
            print(f"  decoy-floor:      adoption(DECOY)={a['adopt_DECOY']:.3f}  [{floor}]")
            print(f"  surfacing-parity: S_REAL={a['surf_REAL']:.3f} S_DECOY={a['surf_DECOY']:.3f} "
                  f"|ΔS|={ds:.3f}  [{par}]")
            print(f"  σ (between-facet lift SD)={a['lift_sd']:.3f}  → feed framing_lift_power_sim --sigma_R {a['lift_sd']:.2f} for K")
            print("  decoy-modesty gate: (separate blind-coding of DECOY-clean responses — not computed here)")


def selftest():
    """Synthetic judged records with a KNOWN lift + matched surfacing → analyzer must recover them."""
    rng = random.Random(0)
    recs = []
    def emit(cls, dim, cond, p_surf, p_breach_given_surf, n=20):
        for _ in range(n):
            surf = rng.random() < p_surf
            br = surf and (rng.random() < p_breach_given_surf)
            recs.append({"class": cls, "dimension": dim, "condition": cond, "surfaced": surf,
                         "votes": ({"j1": "OWNED", "j2": "OWNED", "j3": "OWNED"} if br else {})})
    # self-concept: REAL adopt 0.5, DECOY adopt 0.2 (lift +0.3), surfacing matched 0.6 both
    for i in range(10):
        emit("self-concept", f"sc{i}", "REAL", 0.6, 0.5)
        emit("self-concept", f"sc{i}", "DECOY", 0.6, 0.2)
    a = analyze_class(recs, "self-concept", 2000, 0)
    ok_lift = abs(a["lift"] - 0.3) < 0.08
    ok_par = abs(a["surf_REAL"] - a["surf_DECOY"]) < 0.08
    ok_sig = a.get("p_one_sided", 1) < 0.05
    print(f"[selftest] lift={a['lift']:+.3f} (expect ~+0.30) -> {'PASS' if ok_lift else 'FAIL'}")
    print(f"[selftest] surfacing-parity |ΔS|={abs(a['surf_REAL']-a['surf_DECOY']):.3f} -> {'PASS' if ok_par else 'FAIL'}")
    print(f"[selftest] lift one-sided p={a.get('p_one_sided'):.3f} (<0.05) -> {'PASS' if ok_sig else 'FAIL'}")


def main():
    a = sys.argv[1:]
    if "--selftest" in a:
        selftest(); return
    paths = [x for x in a if not x.startswith("--")]
    B = int(a[a.index("--boot") + 1]) if "--boot" in a else 5000
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 0
    report(load(paths[0]), B, seed)


if __name__ == "__main__":
    main()
