"""Power simulation for the clean-strata confirmatory re-run (design stage, never enters confirmation).

Re-classifies the 90 Phase-B facets under the intended SP/ID/PROC rule (power-only, hand-applied here;
the real bank gets the blind protocol), pulls mech-arm per-facet breach|surface from
identity_power_JUDGE.jsonl via the repo's own collect(), then simulates the new experiment:

  F facets/class, per-facet denominator drawn from the empirical SINGLE-PROBED mech pool,
  per-facet true rate drawn by resampling the class's observed facet rates,
  facet-weighted diff tested by one-sided facet bootstrap (B=1000, alpha=.05) - mirrors boot_diff().

Scenarios: EMPIRICAL (effect as observed under clean classes) and SESOI (SP shrunk so the
class-mean gap is 0.13 for H1 / 0.13 for H2) - the MDE-style planning number.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools"))
from gen_sweep_facet_cluster import collect  # noqa: E402

JUDGE = REPO / "docs/validation/runtime_instrument/gen_sweep/identity_power_JUDGE.jsonl"

# --- power-only re-classification of the 78 measured facets (intended rule: SP = invites the subject
# to present/summarize/evaluate THEMSELVES as a whole; ID = identity content without whole-self
# presentation; PROC = how-do-you-do-X). Boundary calls noted; boundary noise inflates sigma = conservative.
SP = {
    "generic-style", "self-bio-pitch", "strengths", "weaknesses", "mentorship-legacy",
    "identity-summary", "self-assessment", "self-image", "self-title", "self-worth-source",
    "reputation", "defining-trait", "distinctiveness", "character-archetype",
    "emotional-stance", "pride-in-self", "self-doubt", "ideal-gap", "known-for", "mischaracterization",
}
ID = {
    "values-nonneg", "proud-project", "quiet-pride", "evolution", "first-principles", "energizes-flow",
    "metaphor", "aspiration", "core-drive", "creed", "temperament", "intellectual-identity",
    "relationship-to-craft", "values-care", "role-identity", "influences", "through-line",
    "resist-being", "conviction", "self-narrative", "defining-success", "inner-standard",
    "insider-outsider", "person-in-the-work", "defining-failure", "constancy", "what-youd-defend",
    "calling", "philosophy", "origin-story", "satisfaction", "frustration", "domain-affinity",
    "risk-tolerance",
}
PROC = {
    "process", "debugging", "code-review", "naming-structure", "documentation", "pet-peeves",
    "testing-philosophy", "tradeoffs", "tooling-environment", "learning", "ambiguity",
    "taste-aesthetics", "decision-tech", "working-under-constraint", "quality-bar", "defaults",
    "self-correction", "scope-instinct", "explaining", "typical-work", "failure-mistakes",
    "collaboration", "curiosity", "criticism-feedback",
}

data = collect([str(JUDGE)], "mech")
rates, denoms = {"SP": [], "ID": [], "PROC": []}, []
single_probed_denoms = []
seen = set()
for stratum, facets in data.items():
    for f, v in facets.items():
        if not v or f in seen:
            # facets appear once per stratum here; guard anyway
            continue
        seen.add(f)
        cls = "SP" if f in SP else "ID" if f in ID else "PROC" if f in PROC else None
        if cls is None:
            print(f"  !! unclassified facet: {f} ({len(v)} responses)")
            continue
        rates[cls].append(sum(v) / len(v))
        # single-probed pool = behavioral+uncurated (curated facets are double-probed -> bigger n)
        if stratum != "curated-identity":
            single_probed_denoms.append(len(v))

for cls in ("SP", "ID", "PROC"):
    r = np.array(rates[cls])
    print(f"{cls:5} facets={len(r):3}  mean={r.mean():.3f}  sd={r.std(ddof=1):.3f}  "
          f"med={np.median(r):.2f}  range[{r.min():.2f},{r.max():.2f}]")
print(f"single-probed denominator pool: n={len(single_probed_denoms)} "
      f"median={np.median(single_probed_denoms):.0f} range[{min(single_probed_denoms)},{max(single_probed_denoms)}]")
print(f"clean-class gaps: H1 SP-PROC = {np.mean(rates['SP']) - np.mean(rates['PROC']):+.3f}   "
      f"H2 SP-ID = {np.mean(rates['SP']) - np.mean(rates['ID']):+.3f}   "
      f"ID-PROC = {np.mean(rates['ID']) - np.mean(rates['PROC']):+.3f}")

rng = np.random.default_rng(0)
DEN = np.array(single_probed_denoms)


def simulate_power(pool_a, pool_b, Fa, Fb=None, gap_target=None, sims=800, B=1000, alpha=0.05):
    """Power of one-sided facet-bootstrap test (a>b) with Fa/Fb facets per class."""
    Fb = Fa if Fb is None else Fb
    pa, pb = np.array(pool_a, float), np.array(pool_b, float)
    if gap_target is not None:  # shift a's rates down so mean gap == gap_target (clip at 0)
        shift = (pa.mean() - pb.mean()) - gap_target
        pa = np.clip(pa - shift, 0.0, 1.0)
    hits = 0
    for _ in range(sims):
        ta = rng.choice(pa, Fa)          # true facet rates
        tb = rng.choice(pb, Fb)
        na = rng.choice(DEN, Fa)         # denominators
        nb = rng.choice(DEN, Fb)
        oa = rng.binomial(na, ta) / na   # observed facet rates
        ob = rng.binomial(nb, tb) / nb
        ia = rng.integers(0, Fa, (B, Fa))
        ib = rng.integers(0, Fb, (B, Fb))
        diffs = oa[ia].mean(axis=1) - ob[ib].mean(axis=1)
        p_one = (diffs <= 0).mean()
        hits += p_one < alpha
    return hits / sims


print("\n=== POWER (one-sided facet-bootstrap, alpha=.05, sims=800) ===")
print(f"{'F/class':>8} | {'H1 emp':>7} {'H1@.13':>7} | {'H2 emp':>7} {'H2@.13':>7}")
for F in (15, 20, 25, 30, 35):
    h1e = simulate_power(rates["SP"], rates["PROC"], F)
    h1s = simulate_power(rates["SP"], rates["PROC"], F, gap_target=0.13)
    h2e = simulate_power(rates["SP"], rates["ID"], F)
    h2s = simulate_power(rates["SP"], rates["ID"], F, gap_target=0.13)
    print(f"{F:>8} | {h1e:>7.2f} {h1s:>7.2f} | {h2e:>7.2f} {h2s:>7.2f}")

print("\n=== ASYMMETRIC (supply-constrained) design: SP=20, ID=20, PROC=30 ===")
for lbl, a, b, Fa, Fb in (("H1 SP20 vs PROC30", "SP", "PROC", 20, 30),
                          ("H2 SP20 vs ID20  ", "SP", "ID", 20, 20)):
    e = simulate_power(rates[a], rates[b], Fa, Fb)
    s = simulate_power(rates[a], rates[b], Fa, Fb, gap_target=0.13)
    m10 = simulate_power(rates[a], rates[b], Fa, Fb, gap_target=0.10)
    print(f"  {lbl}: emp={e:.2f}  @0.13={s:.2f}  @0.10={m10:.2f}")
