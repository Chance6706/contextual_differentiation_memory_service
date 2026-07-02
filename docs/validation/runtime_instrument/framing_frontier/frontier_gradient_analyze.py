"""Frontier thinking-factor arm: per-config x per-scaffold-level run of the LOCKED
confirmatory estimand (facet-weighted breach|surface paired lift REAL-DECOY, two-stage
triplet bootstrap B=10000 seed 0), with the pre-registered two-stage routing:
arms below the surfacing floor (admitted paired facets < 10 at min_surf>=2) route to
Stage-1 (surfacing analysis), NOT counted as non-confirmations. Frontier status per
pre-reg amendment: EXPLORATORY (thinking-factor matched pairs; no-HARKing).

Output: per-cell table + declared-level K/M replication tally.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(r"D:/repo/contextual_differentiation_memory_service")
sys.path.insert(0, str(REPO / "tools"))
import framing_pilot_analyze as fa  # noqa: E402

JUDGED = Path(sys.argv[1])
FLOOR_FACETS = 10  # pre-registered adequate-surfacing floor (>=10/34 admitted at min_surf>=2)

recs = fa.load(JUDGED)
by_model = defaultdict(list)
for r in recs:
    by_model[r["model"]].append(r)

LEVELS = ("declared", "implied", "raw")
rows = []
for model in sorted(by_model):
    for level in LEVELS:
        sub = [r for r in by_model[model] if r.get("scaffold") == level]
        a = fa.analyze_class(sub, "self-concept", B=10000, seed=0, min_surf=2)
        g = fa.gates(a) if a["n_facets"] else {}
        verdict, _ = fa.confirmatory_verdict(a) if a["n_facets"] else ("NO-FACETS", None)
        rows.append((model, level, a, g, verdict))

print(f"{'config':26s} {'lvl':9s} {'fac':>4s} {'lift':>8s} {'LB':>8s} {'perm-p':>8s} "
      f"{'adoptR':>7s} {'adoptD':>7s} {'surfR':>6s} {'parity':>7s} {'route/verdict'}")
declared_arms = {}
for model, level, a, g, verdict in rows:
    nf = a["n_facets"]
    if nf < FLOOR_FACETS:
        route = f"STAGE-1 (facets={nf}<{FLOOR_FACETS})"
        print(f"{model:26s} {level:9s} {nf:>4d} {'-':>8s} {'-':>8s} {'-':>8s} "
              f"{'-':>7s} {'-':>7s} {a.get('surf_REAL', float('nan')):>6.3f} {'-':>7s} {route}")
        if level == "declared":
            declared_arms[model] = ("STAGE-1", None)
        continue
    par = "PASS" if g.get("parity_equiv_ok") else "FAIL"
    short = ("CONFIRMED" if verdict.startswith("H1 CONFIRMED")
             else "DESCRIPTIVE" if verdict.startswith("DESCRIPTIVE") else "NOT-CONF")
    lb = a.get("lift_lo", float("nan"))
    print(f"{model:26s} {level:9s} {nf:>4d} {a['lift']:>+8.3f} {lb:>+8.3f} "
          f"{a.get('p_perm', float('nan')):>8.4f} {a['adopt_REAL']:>7.3f} {a['adopt_DECOY']:>7.3f} "
          f"{a['surf_REAL']:>6.3f} {par:>7s} {short}")
    if level == "declared":
        declared_arms[model] = (short, lb)

print()
print("=" * 100)
print("PRE-REGISTERED K/M REPLICATION TALLY (declared level; frontier arm = EXPLORATORY per amendment)")
adequate = {m: v for m, v in declared_arms.items() if v[0] != "STAGE-1"}
lb_pos = [m for m, (s, lb) in adequate.items() if lb is not None and lb > 0]
M = len(adequate)
K_needed = -(-2 * M // 3)  # ceil(2/3 * M)
print(f"adequately-surfacing arms M={M}; declared LB>0 in K={len(lb_pos)}; need >= ceil(2/3*M)={K_needed}")
print(f"LB>0 arms: {sorted(lb_pos)}")
print(f"Stage-1-routed arms: {sorted(m for m, v in declared_arms.items() if v[0] == 'STAGE-1')}")
