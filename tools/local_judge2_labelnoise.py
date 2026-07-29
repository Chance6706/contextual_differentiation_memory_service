#!/usr/bin/env python3
"""Label-noise / shared-blind-spot extractor for LOCALJUDGE-2 (prereg §4 probe).

From the SELECTION matrix, pulls the `concordant-wrong` rows where ≥ K family-disjoint
judges of DIFFERENT families ALL cross the fence the same way against the committed panel
decision. These are panel-error candidates (or a shared local blind spot). Output is a
seeded (≤ N) markdown worksheet for OPTIONAL panel re-adjudication (~$2–3, Josh-gated). It
changes NO committed label and NO gate in this arc — descriptive only (prereg §4/§7).

Seed is derived, not chosen: int(sha256("labelnoise:"+<stamp>)[:8],16); pass --stamp so the
draw is reproducible and committed with the results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from local_judge2_matrix import load_matrix  # noqa: E402
from local_judge import model_family  # noqa: E402


def candidates(rows, k):
    """concordant-wrong rows with ≥ k DISTINCT-family disjoint judges unanimously crossing."""
    out = []
    for key, slot in rows.items():
        fams = {}
        for j, v in slot["votes"].items():
            if v["self_family"] or v["dec"] is None:
                continue
            fams.setdefault(model_family(j) or j, set()).add(v["dec"])
        # Count only families that vote CONSISTENTLY (a split family is ignored, NOT
        # disqualifying — pressure-test SHOULD_FIX 7: at ~66 judges nearly every hard row has
        # one dissenting family, so disqualifying on any split nulls the probe). Require ≥k
        # CLEAN families, all agreeing, and all crossing vs the committed decision.
        fam_decs = {f: next(iter(ds)) for f, ds in fams.items() if len(ds) == 1}
        decset = set(fam_decs.values())
        if len(fam_decs) >= k and len(decset) == 1 and next(iter(decset)) != slot["committed"]:
            out.append((key, slot, len(fam_decs), next(iter(decset))))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--k", type=int, default=5, help="min distinct disjoint families unanimously crossing")
    ap.add_argument("--n", type=int, default=200, help="max rows to sample into the worksheet")
    ap.add_argument("--stamp", default="localjudge2", help="derives the seed (reproducible draw)")
    ap.add_argument("--out", help="worksheet path (.md)")
    args = ap.parse_args()

    rows, judges = load_matrix(args.dirs, "selection")
    cands = candidates(rows, args.k)
    by_dir = Counter(d for _, _, _, d in cands)
    print(f"### label-noise candidates: {len(cands)} concordant-wrong rows with ≥{args.k} "
          f"distinct-family disjoint judges unanimous ({len(judges)} judges available)")
    print(f"  cross direction (local side): {dict(by_dir)}")
    if not cands:
        print("  none — no shared cross-family blind spot at this k (as expected below ~k judges)")
        return 0
    seed = int(hashlib.sha256(("labelnoise:" + args.stamp).encode()).hexdigest()[:8], 16)
    # deterministic order-by-hash draw (no RNG import; resume-safe)
    cands.sort(key=lambda c: hashlib.sha256(f"{seed}:{c[0]}".encode()).hexdigest())
    pick = cands[:args.n]
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# Label-noise re-adjudication worksheet (k≥{args.k}, seed stamp={args.stamp})\n")
            f.write(f"# {len(cands)} candidates; {len(pick)} sampled. Panel re-judge only — "
                    f"descriptive, changes no committed label in this arc.\n\n")
            for (cfile, line), slot, nf, d in pick:
                f.write(f"## {cfile}:{line} {slot['subject_model']} {slot['mode']} "
                        f"committed={slot['committed']} local-unanimous={d} ({nf} families)\n")
        print(f"  worksheet ({len(pick)} rows) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
