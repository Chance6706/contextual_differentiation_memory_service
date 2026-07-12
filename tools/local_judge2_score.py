#!/usr/bin/env python3
"""Partition-aware nominee scorer for LOCALJUDGE-2 (the judge matrix).

Two jobs, both reusing the FROZEN LJ-1 thresholds (`local_judge_score.GATES`) and math:

  SELECTION (default, descriptive) — delegates to the frozen `score_corpus` on the selection
    partition (uniform population; its gate print is descriptive, NOT binding — only CONFIRMATION
    binds). Used for eyeballing a judge on the 68% selection set.

  CONFIRMATION (`--confirm-nominee <model>`) — the BINDING gate evaluation for the single frozen
    nominee, computed on the pre-registered populations (prereg §3, fixing red-team M1):
      * pooled κ, BEM κ, per-family κ, coverage, κ_strict → on the CONFIRMATION holdout;
      * recall sensitivity/specificity → on the FULL-corpus recall subset (confirmation recall is
        too sparse — 48 breaches — to gate; recall is not a selection axis so full-corpus is
        leak-free for a pre-fixed nominee).
    The blinding guard refuses confirmation metrics without --confirm-nominee, and refuses if the
    inputs carry any judge other than the named one (one nominee at a time). If --nominee-file is
    given, the nominee must be listed in that committed freeze (red-team S4/S5).

`evaluate_gb()` is the single partition-correct gate evaluator; `local_judge2_ensemble.py` imports
it so an ENSEMBLE faces the identical full G-B surface (fixing red-team M2), not just pooled+BEM.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_judge_score as ljs  # noqa: E402  (FROZEN — never edited)
from local_judge_score import GATES, MIN_STRATUM_N, MIN_STRATUM_BREACH, kappa, _fmt, _gate  # noqa: E402
from ownership_judge import breach_from_votes  # noqa: E402
from local_judge import model_family  # noqa: E402

HOLDOUT_JSON = (Path(__file__).resolve().parent.parent /
                "docs/validation/runtime_instrument/local_judge2/confirmation_holdout.json")


def load_holdout(path: Path) -> set[str]:
    return set(json.loads(path.read_text(encoding="utf-8"))["confirmation_files"])


def committed_name(local_path: Path) -> str:
    return local_path.name.split("__")[0] + ".jsonl"


def judge_of(local_path: Path) -> str | None:
    parts = local_path.name.split("__")
    return parts[1].rsplit(".jsonl", 1)[0] if len(parts) > 1 else None


def local_decision(lab):
    return breach_from_votes({"local": lab})


# ---------- partition-correct G-B evaluator (shared with the ensemble scorer) ----------

def evaluate_gb(conf_strata, conf_cov, conf_strict, recall_full, label, enforce=False):
    """Frozen G-B gates on the pre-registered populations.
      conf_strata : {stratum -> [(committed, decision)]} on CONFIRMATION (ALL / mode:BEM / family:*)
      conf_cov    : {stratum -> [decided, eligible]} on CONFIRMATION
      conf_strict : [(committed, decision-or-'NONE')] on CONFIRMATION ALL
      recall_full : [(committed, decision)] on the FULL-corpus recall subset (decided only)
    Returns True iff every gate passes. Mirrors the frozen evaluate_gates but sources the recall
    gate from recall_full (not confirmation-recall). κ=n/a FAILS; AC1 omitted (non-binding)."""
    print("-" * 100)
    print(f"  G-B GATE EVALUATION — {label} (κ/family/coverage/strict on CONFIRMATION; "
          f"recall sens/spec on FULL-corpus recall):")
    ok = True
    kp = kappa(conf_strata.get("ALL", []))
    ok &= _gate("pooled κ ≥ %.2f" % GATES["pooled_kappa"],
                None if kp is None else kp >= GATES["pooled_kappa"], f"κ={_fmt(kp)}")
    kb = kappa(conf_strata.get("mode:BEM", []))
    ok &= _gate("BEM κ ≥ %.2f" % GATES["bem_kappa"],
                None if kb is None else kb >= GATES["bem_kappa"], f"κ={_fmt(kb)}")
    n_b = sum(1 for a, _ in recall_full if a == "BREACH")
    n_n = sum(1 for a, _ in recall_full if a == "NOT")
    sens = (sum(1 for a, b in recall_full if a == "BREACH" and b == "BREACH") / n_b) if n_b else None
    spec = (sum(1 for a, b in recall_full if a == "NOT" and b == "NOT") / n_n) if n_n else None
    ok &= _gate("recall sensitivity ≥ %.2f" % GATES["recall_sensitivity"],
                None if sens is None else sens >= GATES["recall_sensitivity"],
                f"sens={_fmt(sens)} (full-corpus recall n_breach={n_b})")
    ok &= _gate("recall specificity ≥ %.3f" % GATES["recall_specificity"],
                None if spec is None else spec >= GATES["recall_specificity"],
                f"spec={_fmt(spec)} (full-corpus recall n_not={n_n})")
    cp = conf_cov.get("ALL", [0, 0])
    cov_p = cp[0] / cp[1] if cp[1] else None
    ok &= _gate("coverage pooled ≥ %.2f" % GATES["coverage_pooled"],
                None if cov_p is None else cov_p >= GATES["coverage_pooled"],
                f"{cp[0]}/{cp[1]}={_fmt(cov_p)}")
    for ch in ("mode:BEM", "mode:recall"):
        cc = conf_cov.get(ch, [0, 0])
        cov_c = cc[0] / cc[1] if cc[1] else None
        ok &= _gate(f"coverage {ch} ≥ %.2f" % GATES["coverage_per_channel"],
                    None if cov_c is None else cov_c >= GATES["coverage_per_channel"],
                    f"{cc[0]}/{cc[1]}={_fmt(cov_c)}")
    ks = kappa([(a, "NOT" if b == "NONE" else b) for a, b in conf_strict])
    delta = None if (kp is None or ks is None) else abs(kp - ks)
    ok &= _gate("|κ − κ_strict| ≤ %.2f" % GATES["kappa_strict_delta"],
                None if delta is None else delta <= GATES["kappa_strict_delta"],
                f"Δ={_fmt(delta)} (κ_strict={_fmt(ks)})")
    for k in sorted(conf_strata):
        if not k.startswith("family:"):
            continue
        pairs = conf_strata[k]
        nb = sum(1 for a, _ in pairs if a == "BREACH")
        if len(pairs) < MIN_STRATUM_N or nb < MIN_STRATUM_BREACH:
            print(f"    [descriptive] {k}: n={len(pairs)} breach={nb} below min-n guard "
                  f"({MIN_STRATUM_N}/{MIN_STRATUM_BREACH}) — not gated")
            continue
        kf = kappa(pairs)
        ok &= _gate(f"{k} κ ≥ %.2f" % GATES["family_kappa"],
                    None if kf is None else kf >= GATES["family_kappa"], f"κ={_fmt(kf)}")
    print(f"  G-B VERDICT ({label}): {'PASS' if ok else 'FAIL'}")
    return ok


def buckets_from_rows(row_iter, decider, holdout, self_family_key="local_self_family"):
    """Build the evaluate_gb inputs from an iterable of (cname, row) for ONE decider.
    decider(row) -> 'BREACH'|'NOT'|None. Self-family rows (per the harness flag) are excluded
    from the κ strata, exactly like the frozen scorer."""
    conf_strata = defaultdict(list)
    conf_cov = defaultdict(lambda: [0, 0])
    conf_strict = []
    recall_full = []
    for cname, r in row_iter:
        c_dec = breach_from_votes(r.get("committed_votes") or r.get("votes") or {})
        if c_dec is None:
            continue
        dec = decider(r)
        in_conf = cname in holdout
        if r.get("mode") == "recall" and dec is not None:
            recall_full.append((c_dec, dec))       # full-corpus recall (both partitions)
        if not in_conf:
            continue
        if r.get(self_family_key):
            continue
        fam = model_family(r.get("subject_model", "")) or "other"
        keys = ("ALL", f"mode:{r.get('mode')}", f"family:{fam}")
        for k in keys:
            conf_cov[k][1] += 1
        if dec is None:
            conf_strict.append((c_dec, "NONE"))
            continue
        conf_strict.append((c_dec, dec))
        for k in keys:
            conf_cov[k][0] += 1
            conf_strata[k].append((c_dec, dec))
    return conf_strata, conf_cov, conf_strict, recall_full


def _iter_rows(paths):
    for p in paths:
        p = Path(p)
        cname = committed_name(p)
        for line in p.open(encoding="utf-8"):
            if line.strip():
                yield cname, json.loads(line)


def score_selection(inputs, holdout, dump=None):
    """Descriptive selection scoring via the frozen scorer (uniform population)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        kept = []
        for p in inputs:
            p = Path(p)
            if committed_name(p) in holdout:
                continue
            dst = tmp / p.name
            dst.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
            kept.append(str(dst))
        if not kept:
            raise SystemExit("no selection-partition files among the inputs")
        print(f"### selection descriptive scoring — {len(kept)} files (gates NON-binding here)")
        return ljs.score_corpus(kept, dump_path=dump)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--partition", choices=["selection", "confirmation"], default="selection")
    ap.add_argument("--confirm-nominee", help="required for CONFIRMATION; names the single frozen "
                    "judge (inputs must all belong to it) — the binding gate evaluation")
    ap.add_argument("--nominee-file", help="committed nominee freeze (json list of names); if given, "
                    "--confirm-nominee must appear in it (red-team S4/S5)")
    ap.add_argument("--holdout", default=str(HOLDOUT_JSON))
    ap.add_argument("--dump")
    ap.add_argument("--enforce", action="store_true")
    args = ap.parse_args()
    holdout = load_holdout(Path(args.holdout))

    if args.partition == "confirmation" and not args.confirm_nominee:
        raise SystemExit("BLINDED: confirmation-partition scoring requires --confirm-nominee "
                         "<model> naming the single frozen nominee (prereg §3).")
    if args.confirm_nominee:
        nominee = re.sub(r"[^A-Za-z0-9._-]", "_", args.confirm_nominee)
        judges = {judge_of(Path(p)) for p in args.inputs}
        if judges != {nominee}:
            raise SystemExit(f"BLINDED: --confirm-nominee={args.confirm_nominee} (safe={nominee}) "
                             f"but inputs carry judges {sorted(j for j in judges if j)}; "
                             f"confirmation is one-nominee-at-a-time — refusing.")
        if args.nominee_file:
            frozen = json.loads(Path(args.nominee_file).read_text(encoding="utf-8"))
            names = frozen.get("single", []) if isinstance(frozen, dict) else frozen
            if args.confirm_nominee not in names:
                raise SystemExit(f"NOMINEE FREEZE: {args.confirm_nominee} not in {args.nominee_file} "
                                 f"{names}; confirmation is only allowed for a pre-committed nominee.")
        cs, cc, ck, rf = buckets_from_rows(_iter_rows(args.inputs), lambda r: local_decision(
            r.get("local_label")), holdout)
        ok = evaluate_gb(cs, cc, ck, rf, f"single:{args.confirm_nominee}", args.enforce)
        return 2 if (args.enforce and not ok) else 0

    ok = score_selection(args.inputs, holdout, dump=args.dump)
    return 2 if (args.enforce and not ok) else 0


if __name__ == "__main__":
    raise SystemExit(main())
