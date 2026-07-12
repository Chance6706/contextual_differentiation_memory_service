"""Seeded stratified sample manifest for LOCALJUDGE Phase B tiers (locked in the prereg).

Emits {file, line} coordinates consumed by local_judge.py --sample-manifest. Composition:
  - ALL committed breach-decision rows (breach_from_votes == BREACH; only 7,718 exist corpus-wide
    — the scarce class is never subsampled);
  - ALL committed-escalated rows (votes present, decision None) — excluded from kappa but the
    local judge's behavior on the panel's undecided rows is a pre-registered descriptive;
  - a seeded sample of NOT rows per (file, mode) cell, --not-per-cell each (without replacement),
    keeping every subject model represented when possible (sample is per (file, mode, subject)
    round-robin up to the cell budget).

Deterministic for a given (--seed, corpus contents); the manifest FILE is committed and its
sha256 is pinned in the prereg — Phase B judges exactly these coordinates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ownership_judge import breach_from_votes  # noqa: E402


def build(files, seed: int, not_per_cell: int):
    rng = random.Random(seed)
    picked = []
    for p in sorted(files):
        name = Path(p).name
        not_rows = defaultdict(list)  # (mode, subject) -> [line]
        for i, ln in enumerate(open(p, encoding="utf-8")):
            if not ln.strip():
                continue
            r = json.loads(ln)
            if not r.get("votes"):
                continue
            dec = breach_from_votes(r["votes"])
            if dec == "BREACH" or dec is None:
                picked.append({"file": name, "line": i})
            else:
                not_rows[(r.get("mode"), r.get("subject_model"))].append(i)
        # per (file, mode): round-robin across subjects up to not_per_cell
        by_mode = defaultdict(list)
        for (mode, subj), lines in sorted(not_rows.items()):
            rng.shuffle(lines)
            by_mode[mode].append(lines)
        for mode, subject_lists in sorted(by_mode.items()):
            budget, idx = not_per_cell, 0
            while budget > 0 and any(subject_lists):
                lst = subject_lists[idx % len(subject_lists)]
                if lst:
                    picked.append({"file": name, "line": lst.pop()})
                    budget -= 1
                idx += 1
                if idx > 10 * not_per_cell * max(len(subject_lists), 1):
                    break
    return picked


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--not-per-cell", type=int, required=True,
                    help="NOT-decision rows sampled per (file, mode) cell")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    picked = build(args.inputs, args.seed, args.not_per_cell)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        for c in picked:
            f.write(json.dumps(c) + "\n")
    sha = hashlib.sha256(Path(args.out).read_bytes()).hexdigest()
    print(f"{args.out}: {len(picked)} coordinates  sha256={sha}")


if __name__ == "__main__":
    main()
