"""Facet-CLUSTERED, facet-WEIGHTED analysis of the framing/curation question — the cluster-correct
companion to `gen_sweep_aggregate.py --by-facet-framing` (which is response-pooled = descriptive only).

WHY THIS EXISTS (pressure-test record, rule 12, 2026-06-29 — two adversarial agents, stat + method):
  The published gen-sweep4 framing claim (identity 37.2% vs behavioral 17.5%, "z=+6.5") treated ~867
  self-attribution RESPONSES as independent. They are NOT: responses cluster by elicitation FACET, and the
  bank deliberately double-probes the high-leak self-presentation facets (curated-identity has 10/17 facets
  with 2 probes — exactly the leaky ones — vs behavioral 2/25, uncurated 0/36). So the correct unit is the
  FACET, and the correct estimand is FACET-WEIGHTED (mean over facets of each facet's own rate), per the
  quant study's S-2 rule (quant_repl_aggregate.py:130-136). Re-analyzed that way (this tool), on the Phase-B
  identity-power data:
    - The z=+6.5 collapses to p≈0.04-0.11 — DOMINANTLY an effective-n/clustering correction (naive 1e-10 ->
      cluster-pooled 0.054 -> facet-weighted 0.114), with weighting a secondary contributor.
    - The framing dissociation (identity-self-presentation > process) is REAL in direction across every arm,
      ~1.6-1.8x (down from response-pooled ~2.1x), and SIGNIFICANT in the clean mech arm (curated-vs-behavioral
      p=0.043); under-powered all-arms (~35% power) -> "real but not yet firmly established."
    - Topic-curation is NOT the inflation driver: uncurated-identity (~22%) ~= curated-identity (~25%), point
      estimate ~0 (p~0.4-0.6). The apparent pooled curation gap was the 2-probe weighting artifact. "Curation
      refuted / not detected", not "proven no effect" (under-powered).
  KNOWN LIMITATIONS (do not overstate): (1) one-stage facet bootstrap (not two-stage) + facet-only (not
  facet+model) clustering -> CIs mildly anti-conservative (true p if anything larger). (2) the strata are a
  CONTAMINATED proxy: the index split (0-26 identity / 27-53 behavioral) misfiles `identity-summary` (an
  identity question) as behavioral (its leakiest facet, 0.92) and process facets (naming/process/code-review)
  as identity (~0); both shrink the measured gap. Leak actually tracks a narrow self-presentation/self-
  assessment SUB-CONSTRUCT cutting across all nominal strata, not identity-framing breadth. A powered re-run
  with pre-registered, cleanly-classified facets is the open item.

Usage:
  python tools/gen_sweep_facet_cluster.py JUDGE.jsonl [--arm mech] [--boot 5000] [--seed 0] [--per-facet]
"""
from __future__ import annotations

import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_sweep_aggregate import facet_framing_map, breach_corrected, TOK, MAP  # noqa: E402
from probes_bem_facet import FACET_OF, PROBES_BEM_FACET, REPHRASINGS_BEM_FACET  # noqa: E402

STRATA = ("curated-identity", "behavioral", "uncurated-identity")


def _text2facet():
    m = {}
    for i in range(len(PROBES_BEM_FACET)):
        for t in [PROBES_BEM_FACET[i]] + REPHRASINGS_BEM_FACET.get(i, []):
            m[t.strip()] = FACET_OF[i]
    return m


def collect(paths, arm_filter=None):
    """-> {stratum: {facet: [breach 0/1 over SURFACED BEM responses]}}."""
    fmap = facet_framing_map()
    t2f = _text2facet()
    data = defaultdict(lambda: defaultdict(list))
    for p in paths:
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            if r.get("mode") != "BEM":
                continue
            txt = (r.get("probe") or "").strip()
            info = fmap.get(txt)
            if info is None:
                continue
            if arm_filter and MAP.get(r.get("generation", "?"), ("?",))[0] != arm_filter:
                continue
            if not TOK.search(r.get("response") or ""):
                continue
            data[info[0]][t2f.get(txt)].append(1 if breach_corrected(r) else 0)
    return data


def facet_weighted(by_facet):
    rates = [sum(v) / len(v) for v in by_facet.values() if v]
    return sum(rates) / len(rates) if rates else float("nan")


def boot_diff(data, a, b, B, seed):
    """facet-weighted rate(a)-rate(b); one-stage facet bootstrap. -> (point, lo, hi, cluster_p)."""
    rng = random.Random(seed)
    fa, fb = list(data[a]), list(data[b])
    if not fa or not fb:
        return (float("nan"),) * 4
    diffs = []
    for _ in range(B):
        ra = facet_weighted({f"{f}#{j}": data[a][f] for j, f in enumerate(rng.choice(fa) for _ in fa)})
        rb = facet_weighted({f"{f}#{j}": data[b][f] for j, f in enumerate(rng.choice(fb) for _ in fb)})
        diffs.append(ra - rb)
    diffs.sort()
    lo, hi = diffs[int(0.025 * B)], diffs[min(B - 1, int(0.975 * B))]
    frac = sum(1 for d in diffs if d <= 0) / B
    return (facet_weighted(data[a]) - facet_weighted(data[b]), lo, hi, 2 * min(frac, 1 - frac))


def main():
    args = sys.argv[1:]
    VALUE_FLAGS = {"--arm", "--boot", "--seed"}  # flags that consume the following token
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
        paths = [str(base / "identity_power_JUDGE.jsonl")]
    arm = args[args.index("--arm") + 1] if "--arm" in args else None
    B = int(args[args.index("--boot") + 1]) if "--boot" in args else 5000
    seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 0
    data = collect(paths, arm)

    print("=" * 92)
    print(f"FACET-CLUSTERED framing/curation analysis (facet-weighted, {B}-boot)"
          f"{'  ARM=' + arm if arm else '  (all arms)'}")
    print("=" * 92)
    for s in STRATA:
        nf = len(data[s]); nr = sum(len(v) for v in data[s].values())
        fw = facet_weighted(data[s])
        print(f"  {s:<20} facets={nf:<3} surfaced={nr:<4} facet-weighted breach|surface={fw:.3f}")
    print("-" * 92)
    for a, b, lbl in (("curated-identity", "behavioral", "FRAMING (curated-id vs behavioral) [orig comparison]"),
                      ("uncurated-identity", "behavioral", "FRAMING (uncurated-id vs behavioral)"),
                      ("uncurated-identity", "curated-identity", "CURATION (uncurated-id vs curated-id)")):
        pt, lo, hi, p = boot_diff(data, a, b, B, seed)
        sig = "SIG" if (lo > 0 or hi < 0) else ("marginal" if p < 0.15 else "ns")
        print(f"  {lbl:<52} diff={pt:+.3f} 95%CI[{lo:+.3f},{hi:+.3f}] cluster-p={p:.3f} [{sig}]")

    if "--per-facet" in args:
        print("\n  per-facet rates (contamination visibility):")
        for s in STRATA:
            rows = sorted(((sum(v) / len(v), sum(v), len(v), f) for f, v in data[s].items() if v), reverse=True)
            print(f"  [{s}]")
            for rate, b, n, f in rows:
                print(f"      {f:<24} {b}/{n} = {rate:.2f}")
    print("\n  NOTE: facet-weighted + facet-clustered is the cluster-correct estimand (S-2). The strata are a")
    print("  CONTAMINATED index-proxy (see module docstring) — read the contrasts with that caveat; the clean")
    print("  signal is a self-presentation/self-assessment sub-construct, not identity-vs-behavioral breadth.")


if __name__ == "__main__":
    main()
