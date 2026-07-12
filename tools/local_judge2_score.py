#!/usr/bin/env python3
"""Partition-aware single-judge scorer for LOCALJUDGE-2 (the judge matrix).

Wraps the FROZEN LJ-1 `local_judge_score.score_corpus` without editing it. Adds the
winner's-curse control from LOCALJUDGE2_PREREG §3:

  - default = SELECTION partition (the 25 files NOT in confirmation_holdout.json). All
    ranking / matrix / ensemble construction reads this surface.
  - CONFIRMATION metrics are BLINDED: emitted only with `--confirm-nominee <model>`, and
    only when every input file belongs to a SINGLE judge whose model matches <model>. This
    makes it impossible to sweep confirmation κ across the whole matrix — you must name the
    one frozen nominee, one judge at a time.
  - recall sens/spec is a full-corpus metric for a frozen nominee (prereg §3: recall breach
    is too sparse to split); `--recall-full-corpus` scores the recall channel over BOTH
    partitions while keeping pooled/BEM/family on the requested partition. Requires
    --confirm-nominee (only meaningful for a frozen nominee).

The row filter is applied by writing partition-filtered temp files and delegating to the
frozen scorer — so the scoring math is byte-identical to LJ-1, only the row set changes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_judge_score as ljs  # noqa: E402  (FROZEN — never edited)

HOLDOUT_JSON = (Path(__file__).resolve().parent.parent /
                "docs/validation/runtime_instrument/local_judge2/confirmation_holdout.json")


def load_holdout(path: Path) -> set[str]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return set(obj["confirmation_files"])


def committed_name(local_path: Path) -> str:
    """`foo_JUDGE__model.jsonl` -> committed `foo_JUDGE.jsonl` (partition keys on that)."""
    stem = local_path.name.split("__")[0]
    return stem + ".jsonl"


def judge_of(local_path: Path) -> str | None:
    parts = local_path.name.split("__")
    return parts[1].rsplit(".jsonl", 1)[0] if len(parts) > 1 else None


def filter_to(paths, keep_files: set[str], tmpdir: Path, recall_full: set[str] | None):
    """Write partition-filtered copies; return their paths. recall_full (if given) = files
    whose *recall*-mode rows are ALSO kept even when the file is out-of-partition."""
    out = []
    for p in paths:
        p = Path(p)
        cname = committed_name(p)
        keep_whole = cname in keep_files
        dst = tmpdir / p.name
        n = 0
        with p.open(encoding="utf-8") as fin, dst.open("w", encoding="utf-8", newline="\n") as fout:
            for line in fin:
                if not line.strip():
                    continue
                if keep_whole:
                    fout.write(line if line.endswith("\n") else line + "\n"); n += 1
                    continue
                if recall_full is not None and cname in recall_full:
                    r = json.loads(line)
                    if r.get("mode") == "recall":
                        fout.write(line if line.endswith("\n") else line + "\n"); n += 1
        if n:
            out.append(str(dst))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inputs", nargs="+", help="local-judge output jsonl files (one or more judges)")
    ap.add_argument("--partition", choices=["selection", "confirmation"], default="selection")
    ap.add_argument("--confirm-nominee", help="required to score CONFIRMATION; names the single "
                    "frozen judge — inputs must all belong to it (blinding guard)")
    ap.add_argument("--recall-full-corpus", action="store_true",
                    help="score the recall channel over BOTH partitions (prereg §3); "
                         "requires --confirm-nominee")
    ap.add_argument("--holdout", default=str(HOLDOUT_JSON))
    ap.add_argument("--dump")
    ap.add_argument("--enforce", action="store_true")
    args = ap.parse_args()

    holdout = load_holdout(Path(args.holdout))
    all_files = {committed_name(Path(p)) for p in args.inputs}

    if args.partition == "confirmation" or args.recall_full_corpus:
        if not args.confirm_nominee:
            raise SystemExit("BLINDED: confirmation-partition (or --recall-full-corpus) scoring "
                             "requires --confirm-nominee <model> naming the single frozen nominee "
                             "(prereg §3). Refusing to compute confirmation metrics unblinded.")
        nominee = re.sub(r"[^A-Za-z0-9._-]", "_", args.confirm_nominee)  # match LJ-1 filename safe()
        judges = {judge_of(Path(p)) for p in args.inputs}
        if judges != {nominee}:
            raise SystemExit(f"BLINDED: --confirm-nominee={args.confirm_nominee} (safe={nominee}) "
                             f"but inputs carry judges {sorted(j for j in judges if j)}; "
                             f"confirmation scoring is one-nominee-at-a-time — refusing.")

    if args.partition == "selection":
        keep = set(all_files) - holdout
    else:
        keep = set(all_files) & holdout
    recall_full = (set(all_files) if args.recall_full_corpus else None)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        filtered = filter_to(args.inputs, keep, tmp, recall_full)
        if not filtered:
            raise SystemExit(f"no rows in partition '{args.partition}' for these inputs "
                             f"(files={sorted(all_files)}) — nothing to score")
        label = args.partition + ("+recall-full" if args.recall_full_corpus else "")
        print(f"### LOCALJUDGE-2 partition scorer — partition={label}  "
              f"files_kept={len(filtered)}/{len(args.inputs)}  "
              f"nominee={args.confirm_nominee or '(selection, blinded to confirmation)'}")
        ok = ljs.score_corpus(filtered, dump_path=args.dump)
    if args.enforce and not ok:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
