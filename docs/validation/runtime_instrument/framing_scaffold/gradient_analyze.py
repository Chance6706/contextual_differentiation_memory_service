"""Per-level scaffold-gradient analysis: run the LOCKED confirmatory estimand on declared / implied / raw
and print a side-by-side table. Declared = the frozen confirm_JUDGE.jsonl (same analyzer/seed = apples-to-apples).
implied/raw = this scaffold run's judged records, filtered by the `scaffold` field.
"""
import json
import sys
from pathlib import Path

REPO = Path(r"D:/repo/contextual_differentiation_memory_service")
sys.path.insert(0, str(REPO / "tools"))
import framing_pilot_analyze as fa  # noqa: E402

JUDGED = Path(sys.argv[1])                      # this run's judged.jsonl (implied+raw)
DECLARED = REPO / "docs/validation/runtime_instrument/framing_confirm/confirm_JUDGE.jsonl"

scaffold_recs = fa.load(JUDGED)
declared_recs = fa.load(DECLARED)

levels = [
    ("declared", declared_recs),
    ("implied", [r for r in scaffold_recs if r.get("scaffold") == "implied"]),
    ("raw", [r for r in scaffold_recs if r.get("scaffold") == "raw"]),
]

rows = []
for name, recs in levels:
    a = fa.analyze_class(recs, "self-concept", B=10000, seed=0, min_surf=2)
    g = fa.gates(a)
    verdict, _ = fa.confirmatory_verdict(a)
    rows.append((name, a, g, verdict))
    print("=" * 96)
    print(f"LEVEL = {name.upper()}   (records={len(recs)}, self-concept paired facets admitted={a['n_facets']})")
    print("=" * 96)
    if not a["n_facets"]:
        print("  (no paired facets)\n"); continue
    print(f"  adoption breach|surface:  REAL {a['adopt_REAL']:.3f}   DECOY {a['adopt_DECOY']:.3f}")
    lb = a.get("lift_lo", float("nan"))
    ci = a.get("lift_ci", (float('nan'), float('nan')))
    print(f"  PAIRED LIFT (REAL-DECOY): {a['lift']:+.3f}   one-sided95 LB={lb:+.3f}   "
          f"perm-p={a.get('p_perm', float('nan')):.4f}   CI=({ci[0]:+.3f},{ci[1]:+.3f})")
    print(f"  surfacing:  REAL {a['surf_REAL']:.3f}  DECOY {a['surf_DECOY']:.3f}  |ΔS|={g['dS']:.3f}")
    dsci = g.get("dS_ci90")
    if dsci:
        print(f"  parity-equiv 90% CI ({dsci[0]:+.3f},{dsci[1]:+.3f}) ⊂ ±0.05?  "
              f"[{'PASS' if g['parity_equiv_ok'] else 'FAIL'}]")
    print(f"  decoy-floor: adoption(DECOY)={a['adopt_DECOY']:.3f}  [{'ok' if g['decoy_floor_ok'] else 'FLOOR'}]")
    rb = a["adopt_REAL"]
    twoD = ("HIGH" if rb >= fa.REAL_BREACH_HIGH else "LOW" if rb <= fa.REAL_BREACH_LOW else "INCONCLUSIVE")
    print(f"  2-D REAL breach|surface={rb:.3f} → {twoD}")
    e = a["excl_by_cond"]
    print(f"  excl REAL/DECOY: esc {e['REAL']['esc']}/{e['DECOY']['esc']} "
          f"inval {e['REAL']['inval']}/{e['DECOY']['inval']} missing {e['REAL']['missing']}/{e['DECOY']['missing']}")
    print(f"  >>> VERDICT: {verdict}")
    print()

print("#" * 96)
print("GRADIENT SUMMARY (self-concept H1, locked confirmatory estimand)")
print("#" * 96)
print(f"{'level':10s} {'facets':>6s} {'lift':>8s} {'LB':>8s} {'perm-p':>8s} "
      f"{'adoptR':>7s} {'adoptD':>7s} {'parity':>7s} {'2-D':>13s}  verdict")
for name, a, g, verdict in rows:
    if not a["n_facets"]:
        print(f"{name:10s}   (no paired facets)"); continue
    rb = a["adopt_REAL"]
    twoD = ("HIGH" if rb >= fa.REAL_BREACH_HIGH else "LOW" if rb <= fa.REAL_BREACH_LOW else "INCONCL")
    par = "PASS" if g["parity_equiv_ok"] else "FAIL"
    short = ("CONFIRMED" if verdict.startswith("H1 CONFIRMED")
             else "DESCRIPTIVE" if verdict.startswith("DESCRIPTIVE") else "NOT-CONF")
    print(f"{name:10s} {a['n_facets']:>6d} {a['lift']:>+8.3f} {a.get('lift_lo',float('nan')):>+8.3f} "
          f"{a.get('p_perm',float('nan')):>8.4f} {a['adopt_REAL']:>7.3f} {a['adopt_DECOY']:>7.3f} "
          f"{par:>7s} {twoD:>13s}  {short}")
