"""CONSERVATION P0 — judge test–retest comparison (CONSERVATION_PREREG.md §P0).

The FRAME diagnostic (frame/multiplicity_invariance_check.py) established that generation is
byte-deterministic across epochs, so every cross-epoch difference in the ledgers is judge-side.
P0 measures that instrument noise DELIBERATELY: the committed frame_single/frame_triple caches are
re-judged in a fresh panel session (fresh stamp, fresh spend), and this script compares the retest
JUDGE files row-by-row against the committed epoch files:

  1. row-level panel_label flip rate on shared (model, mode, probe_idx, token) keys
     (judged rows only; ABSENT rows are text-deterministic and cannot flip);
  2. per-vendor vote flip rate (which panelist is the noise source);
  3. derived-quantity deltas on the mech 7f basis: single T1 and triple multiplicity;
  4. sigma_instrument: the SD of the 7f triple multiplicity across ALL available judge sessions on
     this identical text (the 4 committed epochs + the retest) — the quantity the conservation band
     formula consumes: M = max(0.061, 3 * sigma_instrument).

Usage:
  python tools/conservation_p0_compare.py \
      gen_sweep/frame_single_JUDGE.jsonl gen_sweep/frame_single_RETEST_JUDGE.jsonl \
      gen_sweep/frame_triple_JUDGE.jsonl gen_sweep/frame_triple_RETEST_JUDGE.jsonl
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import multifact_analyze as MA  # noqa: E402
from multifact_analyze import collect, fw, facet_multiplicity  # noqa: E402
import probes_sp_expansion as bank  # noqa: E402
import redteam_claude_md_interference as R  # noqa: E402

REPRO = set(bank.REPRO_FACETS)
T1 = R.MULTIFACT_TOKENS[0]
G = REPO / "docs/validation/runtime_instrument/gen_sweep"
# The four committed epochs of the SAME byte-identical triple/single text (for sigma_instrument).
EPOCH_TRIPLES = ["multifact_triple_JUDGE.jsonl", "filler_triple_JUDGE.jsonl",
                 "padding_triple_JUDGE.jsonl", "frame_triple_JUDGE.jsonl"]
EPOCH_SINGLES = ["multifact_single_JUDGE.jsonl", "filler_single_JUDGE.jsonl",
                 "padding_single_JUDGE.jsonl", "frame_single_JUDGE.jsonl"]


def rows_by_key(path):
    out = {}
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        r = json.loads(ln)
        out[(r["subject_model"], r["mode"], r["probe_idx"], r["token"])] = r
    return out


def flip_report(name, a_path, b_path):
    A, B = rows_by_key(a_path), rows_by_key(b_path)
    shared = set(A) & set(B)
    judged = [k for k in shared if (A[k].get("votes") or B[k].get("votes"))]
    flips = [k for k in judged if A[k].get("panel_label") != B[k].get("panel_label")]
    print(f"\n=== P0 {name}: {len(shared)} shared rows, {len(judged)} judged ===")
    print(f"  panel_label flips: {len(flips)}/{len(judged)} = "
          f"{len(flips)/max(len(judged),1):.4f}")
    for k in flips[:10]:
        print(f"    flip {k}: {A[k].get('panel_label')} -> {B[k].get('panel_label')}")
    vend_tot, vend_flip = Counter(), Counter()
    for k in judged:
        va, vb = A[k].get("votes") or {}, B[k].get("votes") or {}
        for v in set(va) & set(vb):
            vend_tot[v] += 1
            if va[v] != vb[v]:
                vend_flip[v] += 1
    for v in sorted(vend_tot):
        print(f"  vendor {v:<10} vote flips {vend_flip[v]}/{vend_tot[v]} = "
              f"{vend_flip[v]/vend_tot[v]:.4f}")
    return len(flips), len(judged)


def mult_7f(path):
    c = collect(str(path), "mech", bank)
    mf = {f: v for f, v in facet_multiplicity(c["bem"], "SP").items() if f in REPRO}
    return fw(mf)


def t1_7f(path):
    c = collect(str(path), "mech", bank)
    vals = {f: [toks.get(T1, 0) for toks in resps.values()]
            for f, resps in c["bem"]["SP"].items() if f in REPRO}
    return fw(vals)


def main():
    s_epoch, s_retest, t_epoch, t_retest = sys.argv[1:5]
    flip_report("single", s_epoch, s_retest)
    flip_report("triple", t_epoch, t_retest)

    print("\n=== derived quantities (mech, 7f) ===")
    print(f"  single T1: epoch={t1_7f(s_epoch):.4f}  retest={t1_7f(s_retest):.4f}")
    print(f"  triple multiplicity: epoch={mult_7f(t_epoch):.4f}  retest={mult_7f(t_retest):.4f}")

    print("\n=== sigma_instrument (all judge sessions on the byte-identical text) ===")
    mults = [mult_7f(G / p) for p in EPOCH_TRIPLES] + [mult_7f(t_retest)]
    t1s = [t1_7f(G / p) for p in EPOCH_SINGLES] + [t1_7f(s_retest)]
    sig_m = statistics.stdev(mults)
    sig_t = statistics.stdev(t1s)
    print(f"  triple multiplicity sessions: {[f'{x:.4f}' for x in mults]}  SD={sig_m:.4f}")
    print(f"  single T1 sessions:           {[f'{x:.4f}' for x in t1s]}  SD={sig_t:.4f}")
    # Band uses the MULTIPLICITY-specific sigma (pressure-test S1: the band gates a multiplicity
    # estimand; the single-T1 sigma is a cross-estimand substitution and is reported as context
    # only). Note the direction: a LARGER sigma widens M, which makes CONSERVED *easier* — so a
    # 3*sigma_m above the floor is itself a flagged finding (instrument noisier than the
    # streak-reliability premise assumed), not just a wider margin. The floor 0.061 binds below.
    band = max(0.061, 3 * sig_m)
    print(f"\n  sigma_multiplicity = {sig_m:.4f} (band input); sigma_T1 = {sig_t:.4f} (context)")
    print(f"  CONSERVATION BAND M = max(0.061, 3*sigma_m) = {band:.4f}"
          + ("   << ABOVE FLOOR — flagged finding (PREREG s3)" if band > 0.061 else "   (floor binds)"))
    # Band-provenance artifact (pressure-test S2): the launcher refuses to generate without a band
    # and the analyzer can consume this file directly — converts P0-before-generation from a
    # documented promise into a checkable artifact.
    art = G.parent / "conservation" / "P0_BAND.json"
    art.write_text(json.dumps({"sigma_multiplicity": round(sig_m, 6), "sigma_t1": round(sig_t, 6),
                               "band": round(band, 6), "floor": 0.061, "halt": band > 0.061,
                               "multiplicity_sessions": [round(x, 6) for x in mults],
                               "t1_sessions": [round(x, 6) for x in t1s],
                               "retest_files": [str(s_retest), str(t_retest)]}, indent=1),
                   encoding="utf-8")
    print(f"  band artifact written: {art}")
    # Ceiling guard (pressure-test M3): a band ABOVE the floor means the instrument is noisier than
    # the streak-reliability premise assumed — equivalence at that width would be rubber-stamping.
    # HALT for human review (Josh) instead of auto-widening; the analyzer independently refuses an
    # above-floor band without an explicit approval flag.
    if band > 0.061:
        print("\n  !! HALT: 3*sigma_multiplicity exceeds the 0.061 floor — do NOT proceed to "
              "generation. Review the flip report above (vendor swap? bimodality spread?) with Josh; "
              "proceeding requires an explicit decision recorded in CONSERVATION_PREREG s9.")
        raise SystemExit(3)


if __name__ == "__main__":
    main()
