"""Power simulation for BLOCK_PREREG.md §power (committed pre-lock).

Simulates the pre-registered per-arm decision (paired facet bootstrap of D = adopt_A − adopt_X over
the 25 open-SP facets, one-sided REDUCED iff LB95>0; COLLAPSED iff x_pt≤0.02 ∧ LB95>0) from the
EMPIRICAL committed anchor facet profile (frame_filler_JUDGE.jsonl, mech, filler-token adoption,
n=44/facet, fw=0.1100 — top facets cs-A1 0.341, sp-N9 0.273, sp-N1 0.250 …).

Truth grid: multiplicative r ∈ {1.0 no-effect, 0.5 halved, 0.25 quartered, 0.0 collapse}.
Anchor held FIXED at the committed counts (that is what the analysis pairs against); the treated arm
drawn binomially at r·p_f. The facet-profile-reshuffle failure mode that broke the conservation P2
sim does NOT apply here: both arms share ONE probe bank and ONE store — only the render frame
differs — so a uniform-shift truth model is the right null family (reshuffle would itself be a
finding, visible in the per-facet deltas).

Run:  python docs/validation/runtime_instrument/blockframe/power_sim.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools"))
from multifact_analyze import collect  # noqa: E402
from frame_analyze import tok_by_open_facet  # noqa: E402
import probes_sp_expansion as bank  # noqa: E402
import redteam_claude_md_interference as R  # noqa: E402

SIMS, BOOT, N = 400, 2000, 44


def load_anchor():
    c = collect(str(REPO / "docs/validation/runtime_instrument/gen_sweep/frame_filler_JUDGE.jsonl"),
                "mech", bank)
    ap = tok_by_open_facet(c, set(bank.FORMAT_OPEN), R.FILLER_TOKENS)
    return {f: list(v) for f, v in ap.items()}


def fw(d):
    return sum(sum(v) / len(v) for v in d.values()) / len(d)


def decide(anchor, test, rng):
    facets = sorted(anchor)
    diffs = []
    for _ in range(BOOT):
        samp = [rng.choice(facets) for _ in facets]
        da = sum(sum(anchor[f]) / len(anchor[f]) for f in samp) / len(samp)
        dt = sum(sum(test[f]) / len(test[f]) for f in samp) / len(samp)
        diffs.append(da - dt)
    diffs.sort()
    lb = diffs[int(0.05 * BOOT)]
    x = fw(test)
    if x <= 0.02 and lb > 0:
        return "COLLAPSED"
    if lb > 0:
        return "REDUCED"
    return "NOT-REDUCED"


def load_t1():
    from frame_analyze import t1_by_open_facet
    c = collect(str(REPO / "docs/validation/runtime_instrument/gen_sweep/frame_filler_JUDGE.jsonl"),
                "mech", bank)
    return t1_by_open_facet(c, set(bank.FORMAT_OPEN))


def t1_verdict(anchor, test, rng, band=0.071):
    """The mechanism-read T1 test (red-team S2): flat iff 90% CI of dT1 within ±band; drop iff
    LB95 > 0."""
    facets = sorted(anchor)
    diffs = []
    for _ in range(BOOT):
        samp = [rng.choice(facets) for _ in facets]
        da = sum(sum(anchor[f]) / len(anchor[f]) for f in samp) / len(samp)
        dt = sum(sum(test[f]) / len(test[f]) for f in samp) / len(samp)
        diffs.append(da - dt)
    diffs.sort()
    lb, ub = diffs[int(0.05 * BOOT)], diffs[int(0.95 * BOOT) - 1]
    if lb > 0:
        return "DROP"
    if lb > -band and ub < band:
        return "FLAT"
    return "NEITHER"


def main():
    anchor = load_anchor()
    print(f"anchor fw = {fw(anchor):.4f}  facets = {len(anchor)}  n/facet = "
          f"{len(next(iter(anchor.values())))}")
    rates = {f: sum(v) / len(v) for f, v in anchor.items()}
    print(f"{'truth r':>8} {'COLLAPSED':>10} {'REDUCED':>8} {'NOT-REDUCED':>12}")
    for r in (1.0, 0.5, 0.25, 0.0):
        counts = {"COLLAPSED": 0, "REDUCED": 0, "NOT-REDUCED": 0}
        for s in range(SIMS):
            rng = random.Random(1000 + s)
            test = {f: [1 if rng.random() < r * p else 0 for _ in range(N)]
                    for f, p in rates.items()}
            counts[decide(anchor, test, rng)] += 1
        print(f"{r:>8.2f} {counts['COLLAPSED']/SIMS:>10.2f} {counts['REDUCED']/SIMS:>8.2f} "
              f"{counts['NOT-REDUCED']/SIMS:>12.2f}")

    # Mechanism-read operating characteristics (red-team S2): the T1 control at its own anchor
    # rate (~0.213, n=22/facet) — false-drop at truth Delta=0 and false-flat at real shifts.
    t1 = load_t1()
    t1_rates = {f: sum(v) / len(v) for f, v in t1.items()}
    n_t1 = len(next(iter(t1.values())))
    print(f"\nT1 control OCs (anchor fw={fw(t1):.4f}, n/facet={n_t1}, band ±0.071):")
    print(f"{'truth dT1':>10} {'FLAT':>6} {'DROP':>6} {'NEITHER':>8}")
    for shift in (0.0, 0.05, 0.10):
        counts = {"FLAT": 0, "DROP": 0, "NEITHER": 0}
        for s in range(SIMS):
            rng = random.Random(5000 + s)
            test = {f: [1 if rng.random() < max(0.0, p - shift) else 0 for _ in range(n_t1)]
                    for f, p in t1_rates.items()}
            counts[t1_verdict(t1, test, rng)] += 1
        print(f"{shift:>10.2f} {counts['FLAT']/SIMS:>6.2f} {counts['DROP']/SIMS:>6.2f} "
              f"{counts['NEITHER']/SIMS:>8.2f}")


if __name__ == "__main__":
    main()
