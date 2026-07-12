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

    PARITY GUARD (pressure-test MUST_FIX 1): rows are keyed by file-position, which is valid
    only if every judge's mirror of a given committed file is line-paired with the others. A
    ragged file (partial run, or a determinism/probe output co-mingled in a judge dir) would
    silently pair judge B's line-0 with judge A's different row. So for each committed file we
    require ALL contributing judges to agree on the non-blank line count; a disagreement fails
    LOUDLY. (Per-judge parity vs the committed SOURCE is separately checked by
    local_judge_audit.py before scoring — here we guard the cross-judge alignment the positional
    key depends on.)
    """
    holdout = load_holdout(Path(holdout_path))
    rows = {}
    judges = set()
    counts = defaultdict(dict)  # cname -> {judge -> non-blank line count}
    for d in dirs:
        d = Path(d)
        for p in sorted(d.glob("*_JUDGE__*.jsonl")):
            cname = committed_name(p)
            in_conf = cname in holdout
            if (partition == "selection") == in_conf:
                continue  # wrong partition
            judge = judge_of(p)
            judges.add(judge)
            nb = 0
            for i, line in enumerate(p.open(encoding="utf-8")):
                if not line.strip():
                    continue
                nb += 1
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
            counts[cname][judge] = nb
    ragged = [f"{cname}: judges disagree on row count {perj}"
              for cname, perj in counts.items() if len(set(perj.values())) > 1]
    if ragged:
        raise SystemExit("PARITY GUARD: contributing judges are not line-paired —\n  "
                         + "\n  ".join(ragged) + "\nRefusing to build a positionally-keyed matrix "
                         "from ragged files (would silently misalign judges). Fix or exclude them.")
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


def leaderboard(rows, judges):
    """Per judge on its family-disjoint decided rows: pooled κ, BEM κ, coverage. The
    single-judge NOMINATION signal (§4 E-single: pooled+BEM κ) — reproducible from one call
    (pressure-test SHOULD_FIX 5)."""
    out = []
    for j in judges:
        pooled, bem, eligible = [], [], 0
        for slot in rows.values():
            v = slot["votes"].get(j)
            if v is None or v["self_family"]:
                continue
            eligible += 1
            if v["dec"] is None:
                continue
            pooled.append((slot["committed"], v["dec"]))
            if slot["mode"] == "BEM":
                bem.append((slot["committed"], v["dec"]))
        out.append({"judge": j, "pooled_kappa": kappa(pooled), "bem_kappa": kappa(bem),
                    "n": len(pooled), "coverage": len(pooled) / eligible if eligible else 0.0})
    out.sort(key=lambda r: (r["pooled_kappa"] if r["pooled_kappa"] is not None else -9,
                            r["bem_kappa"] if r["bem_kappa"] is not None else -9), reverse=True)
    return out


def disagreement_histogram(rows):
    """Per row, how many family-disjoint judges disagree with the committed decision → the
    row-difficulty distribution (pressure-test SHOULD_FIX 6, cheap half)."""
    hist = Counter()
    for slot in rows.values():
        decs = disjoint_decs(slot)
        hist[sum(1 for d in decs if d != slot["committed"])] += 1
    return hist


def pairwise_agreement(rows, judges):
    """Full judge×judge raw-agreement on co-decided disjoint rows (O(J²·R); opt-in). Returns
    {(j1,j2): agreement} and per-judge nearest neighbour (redundancy signal)."""
    idx = {j: {} for j in judges}
    for key, slot in rows.items():
        for j, v in slot["votes"].items():
            if not v["self_family"] and v["dec"] is not None:
                idx[j][key] = v["dec"]
    pair = {}
    nn = {}
    for a in judges:
        best, best_ag = None, -1.0
        for b in judges:
            if b <= a:
                continue
            common = idx[a].keys() & idx[b].keys()
            if not common:
                continue
            ag = sum(1 for k in common if idx[a][k] == idx[b][k]) / len(common)
            pair[(a, b)] = (ag, len(common))
            for x, y in ((a, b), (b, a)):
                if ag > nn.get(x, (None, -1))[1]:
                    nn[x] = (y, ag)
    return pair, nn


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dirs", nargs="+", help="judge output dirs (one per judge)")
    ap.add_argument("--partition", choices=["selection", "confirmation"], default="selection")
    ap.add_argument("--out", help="write per-row difficulty index jsonl here")
    ap.add_argument("--pairwise-out", help="write the full judge×judge agreement matrix here (opt-in)")
    args = ap.parse_args()

    rows, judges = load_matrix(args.dirs, args.partition)
    print(f"### matrix: {len(judges)} judges × {len(rows)} committed-decided rows "
          f"(partition={args.partition})")
    strata = difficulty(rows)
    print("\nDIFFICULTY MAP (family-disjoint judges per row):")
    for k in sorted(strata, key=lambda x: (x != "ALL", not x.startswith("mode:"),
                                           x.startswith("file:"), x)):
        c = strata[k]
        tot = sum(c.values())
        print(f"  {k:26} n={tot:6}  correct={c['concordant-correct']:6} "
              f"split={c['split']:6} blind-spot={c['concordant-wrong']:5} "
              f"no-disjoint={c['no-disjoint-judge']:4}")
    hist = disagreement_histogram(rows)
    print("\nROW-DIFFICULTY HISTOGRAM (# disjoint judges disagreeing w/ committed → # rows):")
    print("  " + "  ".join(f"{d}:{hist[d]}" for d in sorted(hist)))
    print("\nSINGLE-JUDGE LEADERBOARD (selection nomination signal: pooled+BEM κ):")
    for r in leaderboard(rows, judges):
        pk = "n/a" if r["pooled_kappa"] is None else f"{r['pooled_kappa']:.3f}"
        bk = "n/a" if r["bem_kappa"] is None else f"{r['bem_kappa']:.3f}"
        print(f"  {r['judge']:34} pooled κ={pk}  BEM κ={bk}  n={r['n']:6}  cov={r['coverage']:.3f}")
    if args.pairwise_out:
        pair, nn = pairwise_agreement(rows, judges)
        with open(args.pairwise_out, "w", encoding="utf-8", newline="\n") as f:
            for (a, b), (ag, n) in sorted(pair.items()):
                f.write(json.dumps({"a": a, "b": b, "agreement": ag, "n": n}) + "\n")
        print(f"\nJUDGE REDUNDANCY (nearest neighbour by agreement) -> full matrix {args.pairwise_out}:")
        for j in sorted(nn):
            print(f"  {j:34} ~ {nn[j][0]:34} agree={nn[j][1]:.3f}")
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
