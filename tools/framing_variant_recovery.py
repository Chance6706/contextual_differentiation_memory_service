"""Variant-recovery power calc for the framing confirmatory (FRAMING_SUBCONSTRUCT_PREREG.md §5).

QUESTION (Josh, 2026-06-30): the pilot's σ → K (28 point / ~43 conservative) exceeds the ~19 fresh
self-concept facets the taxonomy can supply. Can adding *rephrasing variants per facet* (raising the per-
facet response count n, hence shrinking the within-facet binomial noise) bring K @ MDE 0.08 down to ≤19?

ANSWER (after the rule-12 pressure-test, 2026-06-30): only PARTIALLY and UNRELIABLY. Variants shrink only
the within-facet binomial term, never σ_between (the irreducible facet-to-facet variance). At the point σ
the recovery variant count is ≈8 (NOT 6 — V=6 was integer-luck off a per-cell-n bias), and even V=8
delivers MDE 0.08 with only ~60% probability because σ_between is barely identified at K=14 facets. Under
the conservative σ, NO V recovers 0.08 (σ_between floors K≈30). Honest baseline = §5's K=19 @ effective
MDE≈0.10 (the observed pilot lift +0.19 ≫ 0.10, so this is fine).

MODEL (anchored on the pilot's DIRECTLY-measured paired-lift SD — see the pressure-test record below for why
the FROZEN component sim must NOT be used to set K in this regime):
  Var of one facet's paired lift  = σ_between²  +  W                       ... (binomial adds, REAL+DECOY)
    W (within, PER-CELL n)  = mean_f[ p_R(1-p_R)/n_R + p_D(1-p_D)/n_D ]    (the estimand-correct term)
    σ_between²              = max(0, σ_lift_direct² − W)                    (n-INDEPENDENT, IRREDUCIBLE)
  Adding variants scales n by V/2 ⇒ W(V) = W_obs · (2/V).  σ_lift(V) = sqrt(σ_between² + W_obs·2/V).
  K for one-sided LB>0 at 80% power (facet-level normal):  K = ceil( ((z_α+z_β)·σ_lift(V) / MDE)² )
  As V→∞, σ_lift→σ_between ⇒ K floors at ((z..)σ_between/MDE)²  (the supply cap may be below this floor).

Because σ_between is barely identified at K=14, the headline is a BOOTSTRAP DISTRIBUTION over facets, not a
point V: we report P(K≤19 | V) and the recovery-V distribution, not a single "the answer is V".

## Pressure-test record (rule 12, adversarial review 2026-06-30 — folded in)
- MUST_FIX (applied): V=6 was a knife-edge point estimate (18.96→ceil 19) the data barely constrain. Now
  reports the facet-bootstrap P(K≤19|V) + recovery-V distribution; the point recovery-V is ≈8, P≈0.6.
- SHOULD_FIX (applied): the within term now uses PER-CELL n_R, n_D (was pooled mean(n_R+n_D), which
  over-stated W ~2% and under-stated σ_between ~1% — enough to manufacture the V=6 boundary).
- SHOULD_FIX (documented, not "fixed" — it is a regime fact): the FROZEN component sim
  (framing_lift_power_sim) gives K=30–41 here vs the analytic 28, because the implied true REAL/DECOY
  between-facet correlation is ρ≈1.03 (>1): σ_D is tiny and the direct paired covariance is large, so no
  valid ρ≤1 reproduces the measured paired SD. This VINDICATES using the direct paired SD (it nets the
  covariance automatically; ignoring ρ in the analytic K is correct, not anti-conservative) and means
  **K must be set from the direct paired SD, NOT from the component sim, in this ρ→1 regime.**
- SHOULD_FIX (documented): within-cell responses are NOT iid Bernoulli — per-model REAL adoption ranges
  0.00 (all 3 mistral) to 0.68 (granite-3.3-2b), between-model SD 0.207. The linear n(V) reduction and the
  binomial W hold only under a BALANCED FIXED-MODEL panel (same 11 models every facet); then the floor is
  the panel-mean between-facet SD. Surfacing-constancy across variants checks out (probe vs rephrasing
  within ~5pp), supporting n(V)=n2·V/2.
- COST (flagged): V=8 ≈ 4× the pilot's generation + judging + κ-classification per facet (pilot judging
  was $3.21) on top of 19 fresh κ-coded facets. Weigh against the ~0.02 MDE it buys at P≈0.6.

Usage:  python tools/framing_variant_recovery.py [JUDGED.jsonl] [--mde 0.08] [--cap-facets 19] [--boot 5000]
        python tools/framing_variant_recovery.py --selftest
"""
from __future__ import annotations

import math
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import framing_pilot_analyze as A  # reuse the SAME cell/breach logic as the locked analyzer

Z_SUM = 1.645 + 0.8416  # one-sided α=0.05 + 80% power
V_GRID = (2, 3, 4, 5, 6, 8, 10, 12)
V_MAX_FEASIBLE = 16     # beyond this, "no V recovers" (cost/practicality wall)


def _facets(recs, cls="self-concept", min_surf=2):
    """Return per-facet (lift, within_term, n_clean_total) for paired facets."""
    cells = A._cells(recs, cls)
    out = []
    for d in cells:
        R, D = cells[d].get("REAL"), cells[d].get("DECOY")
        if not (R and D) or len(R["clean"]) < min_surf or len(D["clean"]) < min_surf:
            continue
        pR, pD = A._mean(R["clean"]), A._mean(D["clean"])
        nR, nD = len(R["clean"]), len(D["clean"])
        within = pR * (1 - pR) / nR + pD * (1 - pD) / nD     # PER-CELL n (estimand-correct)
        out.append({"lift": pR - pD, "within": within, "n": (nR + nD) / 2.0})
    return out


def _K_at(sigma_between2, W_obs, V, mde):
    sl = math.sqrt(max(0.0, sigma_between2) + W_obs * (2.0 / V))
    return math.ceil((Z_SUM * sl / mde) ** 2), sl


def _decompose(facets):
    lifts = [f["lift"] for f in facets]
    sig_lift = statistics.stdev(lifts) if len(lifts) > 1 else float("nan")
    W_obs = statistics.mean([f["within"] for f in facets])
    sb2 = max(0.0, sig_lift ** 2 - W_obs)
    return sig_lift, W_obs, sb2


def _recovery_V(sb2, W_obs, mde, cap):
    for V in range(2, V_MAX_FEASIBLE + 1):
        if _K_at(sb2, W_obs, V, mde)[0] <= cap:
            return V
    return None  # no feasible V


def analyze(recs, mde=0.08, cap=19, boot=5000, seed=2):
    facets = _facets(recs)
    K = len(facets)
    sig_lift, W_obs, sb2_pt = _decompose(facets)

    # facet bootstrap → uncertainty on σ_between, K(V), and the recovery-V (σ barely identified at K≈14)
    rng = random.Random(seed)
    sig_hi_samples, kV = [], {V: [] for V in V_GRID}
    recovery_Vs, infeasible = [], 0
    for _ in range(boot):
        samp = [facets[rng.randrange(K)] for _ in range(K)]
        sl = statistics.stdev([f["lift"] for f in samp])
        w = statistics.mean([f["within"] for f in samp])
        sb2 = max(0.0, sl ** 2 - w)
        sig_hi_samples.append(sl)
        for V in V_GRID:
            kV[V].append(_K_at(sb2, w, V, mde)[0])
        rv = _recovery_V(sb2, w, mde, cap)
        recovery_Vs.append(rv if rv is not None else V_MAX_FEASIBLE + 1)
        if rv is None:
            infeasible += 1
    sig_hi = sorted(sig_hi_samples)[int(0.95 * boot)]
    sb2_hi = max(0.0, sig_hi ** 2 - W_obs)

    def pct(xs, q):
        return sorted(xs)[min(len(xs) - 1, int(q * len(xs)))]

    pK = {V: (statistics.median(kV[V]), pct(kV[V], 0.05), pct(kV[V], 0.95),
              sum(1 for k in kV[V] if k <= cap) / boot) for V in V_GRID}
    return dict(K=K, sig_lift=sig_lift, sig_hi=sig_hi, W_obs=W_obs, sb_pt=math.sqrt(sb2_pt),
                sb_hi=math.sqrt(sb2_hi), sb2_pt=sb2_pt, sb2_hi=sb2_hi, pK=pK, mde=mde, cap=cap,
                recovery_V_pt=_recovery_V(sb2_pt, W_obs, mde, cap),
                recovery_V_med=statistics.median(recovery_Vs), p_infeasible=infeasible / boot,
                floor_K_pt=math.ceil((Z_SUM * math.sqrt(sb2_pt) / mde) ** 2),
                floor_K_hi=math.ceil((Z_SUM * math.sqrt(sb2_hi) / mde) ** 2),
                mde_floor_pt=Z_SUM * math.sqrt(sb2_pt) / math.sqrt(cap),
                mde_floor_hi=Z_SUM * math.sqrt(sb2_hi) / math.sqrt(cap))


def report(recs, mde=0.08, cap=19, boot=5000):
    a = analyze(recs, mde, cap, boot)
    print(f"pilot self-concept: K={a['K']} facets | σ_lift direct={a['sig_lift']:.3f} (95%u {a['sig_hi']:.3f}) "
          f"| W_obs(per-cell)={a['W_obs']:.4f}")
    print(f"σ_between point={a['sb_pt']:.3f} conservative={a['sb_hi']:.3f}  (IRREDUCIBLE by variants)")
    print(f"MDE floor @ {cap} facets (V→∞): point {a['mde_floor_pt']:.3f} | conservative {a['mde_floor_hi']:.3f}")
    print(f"\n{'V':>3}{'K median':>10}{'K 90% CI':>14}{'P(K≤'+str(cap)+')':>11}")
    for V in V_GRID:
        med, lo, hi, p = a["pK"][V]
        print(f"{V:>3}{med:>10}{('['+str(lo)+','+str(hi)+']'):>14}{p:>11.2f}")
    rv = a["recovery_V_pt"]
    print(f"\nrecovery-V @ point σ = {rv if rv else '>%d (none)' % V_MAX_FEASIBLE}; "
          f"bootstrap median recovery-V = {a['recovery_V_med']:.0f}; "
          f"P(no feasible V) = {a['p_infeasible']:.2f}")
    print(f"conservative σ: floor K={a['floor_K_hi']} > {cap} ⇒ NO V recovers {mde} "
          f"(powers MDE≈{a['mde_floor_hi']:.2f}).")
    print("\nHONEST READ: variants are a weak lever here (σ_between binding). Recovery is V≈8 @ P≈"
          f"{a['pK'][8][3]:.2f}, never under conservative σ. Default = §5 K={cap} @ effective "
          f"MDE≈{a['mde_floor_pt']:.2f}–{a['mde_floor_hi']:.2f}. K from the DIRECT paired SD, not the "
          "component sim (ρ→1 regime — see pressure-test record).")


def selftest():
    """Synthetic facets with a KNOWN σ_between + binomial n → decomposition + recovery-V must be sane."""
    ok = True
    rng = random.Random(0)
    # build 14 facets, true between-facet lift SD ≈ 0.12, n≈17/cell, mid adoption ~0.27/0.085
    recs = []
    for i in range(14):
        base_R = min(0.95, max(0.02, 0.27 + rng.gauss(0, 0.12)))
        base_D = min(0.95, max(0.0, 0.085 + rng.gauss(0, 0.04)))
        for cond, p in (("REAL", base_R), ("DECOY", base_D)):
            for _ in range(17):
                br = rng.random() < p
                recs.append({"class": "self-concept", "dimension": f"f{i}", "condition": cond,
                             "response": "x starboard_loop y",
                             "votes": ({"a": "OWNED", "b": "OWNED", "c": "OWNED"} if br
                                       else {"a": "OBSERVED", "b": "OBSERVED", "c": "OBSERVED"})})
    a = analyze(recs, mde=0.08, cap=19, boot=1000)
    c1 = 0.05 <= a["sb_pt"] <= 0.22
    print(f"[selftest] σ_between point={a['sb_pt']:.3f} in [0.05,0.22] (true≈0.12) -> {'PASS' if c1 else 'FAIL'}")
    c2 = a["pK"][2][0] >= a["pK"][8][0]  # K monotonically non-increasing in V
    print(f"[selftest] K(V=2)={a['pK'][2][0]} >= K(V=8)={a['pK'][8][0]} (more variants → smaller K) -> "
          f"{'PASS' if c2 else 'FAIL'}")
    c3 = 0.0 <= a["pK"][8][3] <= 1.0 and a["pK"][8][3] >= a["pK"][2][3]  # P(recover) rises with V
    print(f"[selftest] P(K≤19) rises with V: V2={a['pK'][2][3]:.2f} V8={a['pK'][8][3]:.2f} -> "
          f"{'PASS' if c3 else 'FAIL'}")
    ok = c1 and c2 and c3
    print(f"[selftest] OVERALL: {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    VALUE_FLAGS = {"--mde", "--cap-facets", "--boot"}  # flags that consume the next token
    args, skip = [], False
    for x in sys.argv[1:]:
        if skip:
            skip = False
            continue
        if x in VALUE_FLAGS:
            skip = True
            continue
        if x.startswith("--"):
            continue
        args.append(x)
    path = args[0] if args else "docs/validation/runtime_instrument/framing_pilot/pilot_JUDGE.jsonl"
    mde = float(sys.argv[sys.argv.index("--mde") + 1]) if "--mde" in sys.argv else 0.08
    cap = int(sys.argv[sys.argv.index("--cap-facets") + 1]) if "--cap-facets" in sys.argv else 19
    boot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 5000
    report(A.load(path), mde, cap, boot)
