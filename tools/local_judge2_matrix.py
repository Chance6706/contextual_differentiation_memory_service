#!/usr/bin/env python3
"""Judge × row disagreement matrix for LOCALJUDGE-2 (prereg §4 E-matrix).

Reads N local-judge output dirs (one per judge, each a full-corpus mirror), builds the
per-row cross-judge decision vector on the SELECTION partition, and produces the three
descriptive products the single-winner design could not:

  1. DIFFICULTY MAP — every committed-decided row, over its FAMILY-DISJOINT judges (a judge's
     vote is dropped on its own-family rows, via the harness `local_self_family` flag):
       concordant-correct : all disjoint judges match the committed decision
       split              : disjoint judges disagree among themselves
       concordant-wrong   : all disjoint judges agree with EACH OTHER but cross the fence
                            vs the committed decision  (shared local blind spot / panel-error
                            candidate — feeds local_judge2_labelnoise.py)
     reported by size + composition, pooled and by channel / family / epoch.
  2. PER-JUDGE TWO-SIDED ERROR — miss rate (BREACH→NOT) AND false-alarm rate (NOT→BREACH)
     per judge on selection; the phenotype table.
  3. SELF-FAMILY AT SCALE (LJ-F3 generalization) — for every judge with same-family subjects,
     κ on own-family rows vs κ on disjoint rows, paired.

Shared loader `load_matrix()` is imported by local_judge2_ensemble.py and _labelnoise.py.
Descriptive only — no gates here.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ownership_judge import breach_from_votes  # noqa: E402
from local_judge2_score import committed_name, judge_of, load_holdout, HOLDOUT_JSON  # noqa: E402
from local_judge_score import kappa  # noqa: E402
from local_judge import model_family  # noqa: E402


def local_dec(lab):
    return breach_from_votes({"local": lab})


def load_matrix(dirs, partition="selection", holdout_path=HOLDOUT_JSON):
    """Return (rows, judges).
    rows: dict keyed (committed_file, line) -> {
        'committed': 'BREACH'|'NOT', 'mode', 'family', 'subject_model', 'file',
        'votes': {judge -> {'dec': 'BREACH'|'NOT'|None, 'label', 'self_family': bool}} }
    only committed-decided rows in the requested partition are kept.
    judges: sorted list of judge names seen.
    """
    holdout = load_holdout(Path(holdout_path))
    rows = {}
    judges = set()
    for d in dirs:
        d = Path(d)
        for p in sorted(d.glob("*_JUDGE__*.jsonl")):
            cname = committed_name(p)
            in_conf = cname in holdout
            if (partition == "selection") == in_conf:
                continue  # wrong partition
            judge = judge_of(p)
            judges.add(judge)
            for i, line in enumerate(p.open(encoding="utf-8")):
                if not line.strip():
                    continue
                r = json.loads(line)
                if "local_judge_model" not in r:
                    continue  # passthrough
                cdec = breach_from_votes(r.get("committed_votes") or r.get("votes") or {})
                if cdec is None:
                    continue  # escalated tie — not in the decided universe
                key = (cname, i)
                slot = rows.get(key)
                if slot is None:
                    slot = rows[key] = {
                        "committed": cdec, "mode": r.get("mode"),
                        "family": model_family(r.get("subject_model", "")) or "other",
                        "subject_model": r.get("subject_model"), "file": cname, "votes": {}}
                slot["votes"][judge] = {
                    "dec": local_dec(r.get("local_label")),
                    "label": r.get("local_label"),
                    "self_family": bool(r.get("local_self_family"))}
    return rows, sorted(judges)


def disjoint_decs(slot):
    """Family-disjoint judge decisions for a row (drop self-family + non-decisions)."""
    return [v["dec"] for v in slot["votes"].values()
            if not v["self_family"] and v["dec"] is not None]


def difficulty(rows):
    strata = defaultdict(Counter)  # stratum -> Counter({concordant-correct, split, concordant-wrong, no-disjoint})
    for slot in rows.values():
        decs = disjoint_decs(slot)
        if not decs:
            cls = "no-disjoint-judge"
        elif len(set(decs)) > 1:
            cls = "split"
        elif decs[0] == slot["committed"]:
            cls = "concordant-correct"
        else:
            cls = "concordant-wrong"
        for k in ("ALL", f"mode:{slot['mode']}", f"family:{slot['family']}", f"file:{slot['file']}"):
            strata[k][cls] += 1
    return strata


def two_sided_error(rows, judges):
    """Per judge on disjoint (non-self-family) rows: miss rate + false-alarm rate."""
    tab = {}
    for j in judges:
        miss = fa = n_breach = n_not = 0
        for slot in rows.values():
            v = slot["votes"].get(j)
            if v is None or v["self_family"] or v["dec"] is None:
                continue
            if slot["committed"] == "BREACH":
                n_breach += 1
                miss += (v["dec"] == "NOT")
            else:
                n_not += 1
                fa += (v["dec"] == "BREACH")
        tab[j] = {"miss_rate": miss / n_breach if n_breach else None,
                  "fa_rate": fa / n_not if n_not else None,
                  "n_breach": n_breach, "n_not": n_not}
    return tab


def self_family_at_scale(rows, judges):
    """Per judge: κ on own-family rows vs κ on disjoint rows (paired). Only judges that
    actually have same-family subjects in the corpus appear."""
    out = {}
    for j in judges:
        own, dis = [], []
        for slot in rows.values():
            v = slot["votes"].get(j)
            if v is None or v["dec"] is None:
                continue
            (own if v["self_family"] else dis).append((slot["committed"], v["dec"]))
        if own:
            out[j] = {"own_kappa": kappa(own), "own_n": len(own),
                      "disjoint_kappa": kappa(dis), "disjoint_n": len(dis)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dirs", nargs="+", help="judge output dirs (one per judge)")
    ap.add_argument("--partition", choices=["selection", "confirmation"], default="selection")
    ap.add_argument("--out", help="write per-row difficulty index jsonl here")
    args = ap.parse_args()

    rows, judges = load_matrix(args.dirs, args.partition)
    print(f"### matrix: {len(judges)} judges × {len(rows)} committed-decided rows "
          f"(partition={args.partition})")
    strata = difficulty(rows)
    print("\nDIFFICULTY MAP (family-disjoint judges per row):")
    for k in sorted(strata, key=lambda x: (x != "ALL", not x.startswith("mode:"), x)):
        if k.startswith("file:"):
            continue
        c = strata[k]
        tot = sum(c.values())
        print(f"  {k:22} n={tot:6}  correct={c['concordant-correct']:6} "
              f"split={c['split']:6} blind-spot={c['concordant-wrong']:5} "
              f"no-disjoint={c['no-disjoint-judge']:4}")
    print("\nPER-JUDGE TWO-SIDED ERROR (disjoint rows):")
    tse = two_sided_error(rows, judges)
    for j in sorted(tse, key=lambda x: (tse[x]["miss_rate"] or 0) - (tse[x]["fa_rate"] or 0)):
        t = tse[j]
        mr = "n/a" if t["miss_rate"] is None else f"{t['miss_rate']:.3f}"
        fr = "n/a" if t["fa_rate"] is None else f"{t['fa_rate']:.3f}"
        print(f"  {j:34} miss={mr} (n_b={t['n_breach']:5})  false_alarm={fr} (n_n={t['n_not']:6})")
    sf = self_family_at_scale(rows, judges)
    if sf:
        print("\nSELF-FAMILY AT SCALE (own-family vs disjoint κ, same rows' judge):")
        for j in sorted(sf):
            s = sf[j]
            ok = "n/a" if s["own_kappa"] is None else f"{s['own_kappa']:.3f}"
            dk = "n/a" if s["disjoint_kappa"] is None else f"{s['disjoint_kappa']:.3f}"
            print(f"  {j:34} own κ={ok} (n={s['own_n']:5})  disjoint κ={dk} (n={s['disjoint_n']:6})")
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            for (cfile, line), slot in rows.items():
                decs = disjoint_decs(slot)
                disagree = sum(1 for d in decs if d != slot["committed"])
                f.write(json.dumps({"file": cfile, "line": line, "committed": slot["committed"],
                                    "mode": slot["mode"], "family": slot["family"],
                                    "n_disjoint": len(decs), "n_disagree": disagree}) + "\n")
        print(f"\nper-row difficulty -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
