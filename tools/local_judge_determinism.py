#!/usr/bin/env python3
"""Determinism re-check comparator (LOCALJUDGE_PREREG §4, verdict-blind).

Compares the fresh-cache re-judge of the 20 manifest coords against the Phase B
outputs for one candidate: local_label AND local_raw must match byte-exactly.
Never touches committed votes — purely local-vs-local, so still verdict-blind.

Note (tooling disclosure, found 2026-07-12 during the re-check): local_judge.py
treats a file ABSENT from --sample-manifest as unrestricted (judges every row).
The re-check driver therefore passes only the manifest's files as inputs. Flagged
for a post-arc harness fix; not changed mid-run (locked toolchain).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phaseb-dir", required=True)
    ap.add_argument("--determinism-dir", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--model", required=True)
    args = ap.parse_args()

    safe = args.model.replace(":", "_").replace("/", "_")
    coords: dict[str, set[int]] = {}
    for ln in open(args.manifest, encoding="utf-8"):
        r = json.loads(ln)
        coords.setdefault(r["file"], set()).add(int(r["line"]))

    n_total = n_match = 0
    mismatches = []
    for fname, lines in sorted(coords.items()):
        stem = fname[:-len(".jsonl")]
        bpath = Path(args.phaseb_dir) / f"{stem}__{safe}.jsonl"
        dpath = Path(args.determinism_dir) / f"{stem}__{safe}.jsonl"
        if not dpath.exists():
            print(f"FAIL: missing determinism output {dpath.name}")
            return 1
        # Phase B file is line-paired: index directly by line number.
        blines = bpath.read_text(encoding="utf-8").splitlines()
        drows = [json.loads(l) for l in dpath.read_text(encoding="utf-8").splitlines()
                 if l.strip()]
        dq = list(drows)  # determinism file holds exactly the selected rows, in file order
        for i in sorted(lines):
            b = json.loads(blines[i])
            d = dq.pop(0)
            n_total += 1
            same = (b.get("local_label") == d.get("local_label")
                    and b.get("local_raw") == d.get("local_raw"))
            n_match += same
            status = "OK " if same else "DIFF"
            print(f"  {status} {fname}:{i} phaseB={b.get('local_label')!r} "
                  f"fresh={d.get('local_label')!r}")
            if not same:
                mismatches.append((fname, i, b.get("local_raw"), d.get("local_raw")))
        if dq:
            print(f"FAIL: {dpath.name} has {len(dq)} unexpected extra judged rows")
            return 1

    print(f"\n{args.model}: {n_match}/{n_total} byte-exact (label+raw)")
    if mismatches:
        for f, i, br, dr in mismatches:
            print(f"  MISMATCH {f}:{i}\n    phaseB raw: {br!r}\n    fresh  raw: {dr!r}")
        return 1
    print("DETERMINISM PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
