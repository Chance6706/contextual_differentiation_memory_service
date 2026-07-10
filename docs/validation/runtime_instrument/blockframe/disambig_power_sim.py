"""Power simulation for DISAMBIG_PREREG.md (committed pre-lock).

Simulates the pre-registered per-contrast decision (joint facet bootstrap over the 25 open-SP
facets; DRIVER iff LB95>0, REVERSED iff UB95<0, NULL iff 95% CI within ±0.037, else UNRESOLVED)
from the EMPIRICAL committed anchor facet profile (frame_filler_JUDGE.jsonl, mech, filler-token
adoption, n=44/facet, fw=0.1100) with the C endpoint pinned at the observed composite reduction
(x0.31 of anchor, uniform multiplicative — the same truth family as the BLOCK sim; both arms of
every contrast share one probe bank and one store, so uniform-shift is the right null family).

Truth grid: the TOTAL log-reduction is split across the three rungs in shares (s_mem, s_hdr, s_fmt);
arm rates interpolate multiplicatively: M = A * r^s_mem, H = A * r^(s_mem+s_hdr), C = A * r
(r = 0.31). M, H, and C are drawn binomially per sim; A stays at the committed empirical counts
(judge re-read noise at temp-0 is ~3% row flips — second-order vs facet sampling, disclosed).

Run:  python docs/validation/runtime_instrument/blockframe/disambig_power_sim.py
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
R_TOTAL = 0.31          # C/A observed (0.0345/0.1100)
NULL_BAND = 0.037

SCENARIOS = [
    ("all-membership", (1.0, 0.0, 0.0)),
    ("all-header",     (0.0, 1.0, 0.0)),
    ("all-format",     (0.0, 0.0, 1.0)),
    ("hdr+fmt 50/50",  (0.0, 0.5, 0.5)),
    ("even thirds",    (1/3, 1/3, 1/3)),
    ("hdr-dominant",   (0.2, 0.6, 0.2)),
]


def load_anchor():
    c = collect(str(REPO / "docs/validation/runtime_instrument/gen_sweep/frame_filler_JUDGE.jsonl"),
                "mech", bank)
    ap = tok_by_open_facet(c, set(bank.FORMAT_OPEN), R.FILLER_TOKENS)
    return {f: list(v) for f, v in ap.items()}


def verdict(draws_contrast):
    xs = sorted(draws_contrast)
    lb, ub = xs[int(0.05 * len(xs))], xs[max(int(0.95 * len(xs)) - 1, 0)]
    lo, hi = xs[int(0.025 * len(xs))], xs[min(int(0.975 * len(xs)), len(xs) - 1)]
    if lb > 0:
        return "DRIVER"
    if ub < 0:
        return "REVERSED"
    if lo > -NULL_BAND and hi < NULL_BAND:
        return "NULL"
    return "UNRESOLVED"


def main():
    anchor = load_anchor()
    facets = sorted(anchor)
    rates = {f: sum(v) / len(v) for f, v in anchor.items()}
    print(f"anchor fw={sum(rates.values())/len(rates):.4f}  facets={len(facets)}  n/facet={N}  "
          f"r_total={R_TOTAL}  NULL band ±{NULL_BAND}")
    names = ("A−M", "M−H", "H−C")
    for label, (s1, s2, s3) in SCENARIOS:
        counts = {n: {"DRIVER": 0, "REVERSED": 0, "NULL": 0, "UNRESOLVED": 0} for n in names}
        for s in range(SIMS):
            rng = random.Random(1000 + s)
            rm = {f: p * (R_TOTAL ** s1) for f, p in rates.items()}
            rh = {f: p * (R_TOTAL ** (s1 + s2)) for f, p in rates.items()}
            m_prof = {f: [1 if rng.random() < rm[f] else 0 for _ in range(N)] for f in facets}
            h_prof = {f: [1 if rng.random() < rh[f] else 0 for _ in range(N)] for f in facets}
            c_prof = {f: [1 if rng.random() < rates[f] * R_TOTAL else 0 for _ in range(N)]
                      for f in facets}
            arms = {"a": anchor, "m": m_prof, "h": h_prof, "c": c_prof}
            draws = {n: [] for n in names}
            for _ in range(BOOT):
                samp = [rng.choice(facets) for _ in facets]
                vals = {t: sum(sum(arms[t][f]) / len(arms[t][f]) for f in samp) / len(samp)
                        for t in arms}
                draws["A−M"].append(vals["a"] - vals["m"])
                draws["M−H"].append(vals["m"] - vals["h"])
                draws["H−C"].append(vals["h"] - vals["c"])
            for n in names:
                counts[n][verdict(draws[n])] += 1
        print(f"\nscenario {label}  (shares mem={s1:.2f} hdr={s2:.2f} fmt={s3:.2f}):")
        for n in names:
            c = counts[n]
            print(f"  {n}: DRIVER {c['DRIVER']/SIMS:.2f}  NULL {c['NULL']/SIMS:.2f}  "
                  f"UNRESOLVED {c['UNRESOLVED']/SIMS:.2f}  REVERSED {c['REVERSED']/SIMS:.2f}")


if __name__ == "__main__":
    main()
