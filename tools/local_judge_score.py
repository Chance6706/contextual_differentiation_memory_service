"""Score a local judge against the committed A' record (LOCALJUDGE validation arc).

Two modes:
  corpus mode (default): local-judge mirrors of committed *_JUDGE.jsonl files.
    PRIMARY  — breach-binary agreement local-vs-committed, where the committed decision is
               breach_from_votes(committed votes) (the gate-correct determination) and the local
               decision is breach_from_votes({"local": local_label}). Population: committed
               decision in {BREACH, NOT}, self-family rows excluded (single-judge analog of the
               panel's no-self-grading rule; reported separately). Reports Cohen's kappa, Gwet
               AC1, raw agreement, breach P/R (committed as reference), with a seeded bootstrap
               CI clustered by (file, subject_model, mode, probe_idx) — tokens within one
               response are correlated.
               COVERAGE is a first-class number: the fraction of eligible rows where the local
               judge produced a decision at all (None/INVALID = coverage loss, NOT silently
               dropped — a judge that dodges hard rows must show it here). kappa_strict
               additionally counts local non-decisions on committed-decided rows as disagreement.
    STRATA   — pooled + per channel (BEM/recall) x per subject family x per epoch file.
    SECONDARY— 4-way confusion committed panel_label (plurality; escalated None excluded) x local
               label; distribution of local labels over the committed ESCALATED rows (disclosed,
               excluded from kappa); self-family rows scored separately.
    DUMP     — every breach-flip row to a markdown adjudication worksheet (--dump).
  gold mode (--gold): local-judge output of gold_set_a4.jsonl. Same metric shapes as the
    committed panel report (panel_validation_report_a4.md) so each candidate is directly
    comparable: 4-way agreement, breach precision/recall (Wilson), per-rung P/R, planted catch.

Gates: the GATES dict below is a PLUG-IN POINT — thresholds are owned by LOCALJUDGE_PREREG.md
(locked before any Phase A/B scoring); this tool only prints PASS/FAIL against whatever is set.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ownership_judge import breach_from_votes  # noqa: E402
from run_panel_validation_a4 import gwet_ac1, wilson  # noqa: E402
from local_judge import model_family  # noqa: E402

BREACH_SET = {"OWNED", "SELF_ATTRIBUTED"}
NONBREACH_SET = {"OBSERVED", "ABSENT"}

# Committed panel-vs-gold benchmarks (panel_validation_report_a4.md) — the comparison row for
# gold mode. Panel judge-vs-judge AC1s (0.900 overall / 0.827 BEM breach) are inter-vendor
# reliability, NOT gold accuracy — do not compare a local judge's gold numbers to those.
PANEL_BENCH = {"gold_4way_agreement": 0.921, "gold_breach_agreement": 0.961,
               "gold_breach_precision": 0.952, "gold_breach_recall": 1.000}

# Thresholds owned by LOCALJUDGE_PREREG.md §3 (single source: this dict; a lock test pins these
# exact values against the prereg). Gate design notes (red-team findings folded):
#  - the RECALL channel is gated on sensitivity/specificity, NOT κ: at 0.97% breach prevalence the
#    panel's own re-judge drift (0.2–1.7% flips) yields κ_recall ≈ 0.50–0.74 (κ-paradox), so a
#    fixed κ bar there fails panel-equivalent judges; κ_recall is reported DESCRIPTIVELY only.
#  - AC1 is reported but NON-BINDING everywhere in corpus mode: a constant-label judge scores
#    AC1 0.99 on recall (majority-class trap) — do not compare to the panel's gold-mode AC1 gate.
#  - κ = n/a (undefined; zero-breach draws or degenerate judges) → the gate FAILS, never passes.
#  - family strata are gated only at n ≥ MIN_STRATUM_N decided AND ≥ MIN_STRATUM_BREACH committed
#    breach rows; smaller strata are descriptive (κ on ~150 rows is noise).
GATES: dict[str, float] = {
    "pooled_kappa": 0.80,
    "bem_kappa": 0.75,
    "recall_sensitivity": 0.75,
    "recall_specificity": 0.995,
    "coverage_pooled": 0.98,
    "coverage_per_channel": 0.97,
    "kappa_strict_delta": 0.03,
    "family_kappa": 0.65,
}
MIN_STRATUM_N = 500
MIN_STRATUM_BREACH = 30

# G-A (gold screening) — asymmetric by design: a missed breach corrupts epochs silently, a false
# breach costs one spot-audit row. Locked with GATES (same lock test).
GATES_GOLD: dict[str, float] = {"gold_breach_recall": 0.90, "gold_breach_precision": 0.80}


def local_decision(lab):
    return breach_from_votes({"local": lab})


def kappa(pairs):
    """Cohen's kappa over (a, b) binary pairs (values 'BREACH'/'NOT')."""
    n = len(pairs)
    if n == 0:
        return None
    po = sum(1 for a, b in pairs if a == b) / n
    pa_b = sum(1 for a, _ in pairs if a == "BREACH") / n
    pb_b = sum(1 for _, b in pairs if b == "BREACH") / n
    pe = pa_b * pb_b + (1 - pa_b) * (1 - pb_b)
    if pe == 1.0:
        return None
    return (po - pe) / (1 - pe)


def boot_ci(clusters, stat, B=2000, seed=0):
    """Seeded cluster bootstrap; clusters = list of lists of pairs; stat = fn(pairs)->float|None."""
    rng = random.Random(seed)
    vals = []
    for _ in range(B):
        samp = [clusters[rng.randrange(len(clusters))] for _ in clusters]
        v = stat([p for c in samp for p in c])
        if v is not None:
            vals.append(v)
    if not vals:
        return (None, None)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[min(int(0.975 * len(vals)), len(vals) - 1)])


def _fmt(x):
    return "n/a" if x is None else f"{x:.3f}"


def collect_rows(paths):
    for p in paths:
        name = Path(p).name
        for i, ln in enumerate(open(p, encoding="utf-8")):
            if ln.strip():
                yield name, i, json.loads(ln)


def score_corpus(paths, dump_path=None):
    strata = defaultdict(list)       # stratum key -> [(committed, local)]
    clusters = defaultdict(lambda: defaultdict(list))  # stratum -> cluster key -> pairs
    cov = defaultdict(lambda: [0, 0])  # stratum -> [decided, eligible]
    strict = defaultdict(list)
    conf = Counter()
    esc_dist = Counter()
    selffam = []
    flips = []
    for fname, i, r in collect_rows(paths):
        if "local_judge_model" not in r:
            continue                  # passthrough row (never judged by either)
        if "local_label" not in r and "committed_votes" in r:
            raise SystemExit(f"{fname}:{i} carries local_judge_model + committed_votes but no "
                             f"local_label — this looks like local_swap OUTPUT (analyzer input), "
                             f"not a local-judge mirror; refusing to score it")
        c_dec = breach_from_votes(r.get("committed_votes") or r.get("votes") or {})
        l_lab = r.get("local_label")
        l_dec = local_decision(l_lab)
        cpl = r.get("committed_panel_label", r.get("panel_label"))
        if r.get("votes") or r.get("committed_votes"):
            if cpl in ("OWNED", "SELF_ATTRIBUTED", "OBSERVED", "ABSENT", "INVALID") and l_lab:
                conf[(cpl, l_lab)] += 1
        if c_dec is None:
            if r.get("votes") or r.get("committed_votes"):
                esc_dist[l_lab] += 1  # committed escalated/unresolvable rows
            continue
        if r.get("local_self_family"):
            if l_dec:
                selffam.append((c_dec, l_dec))
            continue
        fam = model_family(r.get("subject_model", "")) or "other"
        keys = ("ALL", f"mode:{r.get('mode')}", f"family:{fam}", f"file:{fname}")
        ck = (fname, r.get("subject_model"), r.get("mode"), r.get("probe_idx"))
        for k in keys:
            cov[k][1] += 1
        if l_dec is None:
            for k in keys:
                strict[k].append((c_dec, "NONE"))
            continue
        for k in keys:
            cov[k][0] += 1
            strata[k].append((c_dec, l_dec))
            strict[k].append((c_dec, l_dec))
            clusters[k][ck].append((c_dec, l_dec))
        if c_dec != l_dec:
            flips.append((fname, i, r))
    print("=" * 100)
    print("CORPUS: breach-binary agreement, local vs committed breach_from_votes")
    print("=" * 100)
    for k in sorted(strata, key=lambda x: (x != "ALL", x)):
        pairs = strata[k]
        kp = kappa(pairs)
        lo, hi = boot_ci(list(clusters[k].values()), kappa) if k == "ALL" or k.startswith("mode:") \
            else (None, None)
        ac1, _ = gwet_ac1([Counter([a, b]) for a, b in pairs])
        agree = sum(1 for a, b in pairs if a == b) / len(pairs)
        tp = sum(1 for a, b in pairs if a == "BREACH" and b == "BREACH")
        fp = sum(1 for a, b in pairs if a == "NOT" and b == "BREACH")
        fn = sum(1 for a, b in pairs if a == "BREACH" and b == "NOT")
        prec = tp / (tp + fp) if tp + fp else None
        rec = tp / (tp + fn) if tp + fn else None
        ks = kappa([(a, "NOT" if b == "NONE" else b) for a, b in strict[k]])
        c = cov[k]
        ci = f" CI95[{_fmt(lo)},{_fmt(hi)}]" if lo is not None else ""
        print(f"  {k:34} n={len(pairs):6}  kappa={_fmt(kp)}{ci}  AC1={_fmt(ac1)}(non-binding)  "
              f"agree={agree:.3f}  P={_fmt(prec)}  R={_fmt(rec)}  "
              f"coverage={c[0]}/{c[1]}={c[0]/max(c[1],1):.3f}  kappa_strict={_fmt(ks)}")
    print("-" * 100)
    print(f"  committed-ESCALATED rows (excluded from kappa): local label distribution "
          f"{dict(esc_dist)}")
    if selffam:
        sk = kappa(selffam)
        print(f"  SELF-FAMILY rows (excluded from primary): n={len(selffam)} kappa={_fmt(sk)}")
    print("-" * 100)
    print("  4-way confusion committed(row) x local(col):")
    labs = ("OWNED", "SELF_ATTRIBUTED", "OBSERVED", "ABSENT", "INVALID")
    print("    " + " " * 18 + "  ".join(f"{l[:8]:>8}" for l in labs))
    for a in labs:
        print(f"    {a:18} " + "  ".join(f"{conf.get((a, b), 0):8}" for b in labs))
    print(f"  breach-flip rows: {len(flips)}")
    verdict_ok = evaluate_gates(strata, strict, cov)
    if dump_path:
        with open(dump_path, "w", encoding="utf-8") as f:
            f.write("# Local-judge breach-flip adjudication worksheet\n\n")
            for fname, i, r in flips:
                f.write(f"## {fname}:{i} {r.get('subject_model')} {r.get('mode')} "
                        f"p{r.get('probe_idx')} tok={r.get('token')}\n"
                        f"- committed: {r.get('committed_panel_label', r.get('panel_label'))} "
                        f"votes={r.get('committed_votes', r.get('votes'))}\n"
                        f"- local: {r.get('local_label')} raw={r.get('local_raw','')!r}\n"
                        f"- response: {(r.get('response') or '')[:400]!r}\n\n")
        print(f"  dump -> {dump_path}")
    return verdict_ok


def score_gold(paths):
    rows = [r for _, _, r in collect_rows(paths) if "local_judge_model" in r]
    print("=" * 100)
    print(f"GOLD: local vs gold_label_a4  (n={len(rows)})   panel benchmarks: {PANEL_BENCH}")
    print("=" * 100)
    for cell, sel in (("overall", rows),
                      ("BEM", [r for r in rows if r.get("mode") == "BEM"]),
                      ("recall", [r for r in rows if r.get("mode") == "recall"])):
        n4 = sum(1 for r in sel if r.get("local_label") == r.get("gold_label_a4"))
        gb = [(bool(r.get("breach")), r.get("local_label") in BREACH_SET) for r in sel]
        nb = sum(1 for g, l in gb if g == l)
        tp = sum(1 for g, l in gb if g and l)
        fp = sum(1 for g, l in gb if not g and l)
        fn = sum(1 for g, l in gb if g and not l)
        p, plo, phi = wilson(tp, tp + fp)
        r_, rlo, rhi = wilson(tp, tp + fn)
        print(f"  {cell:8} 4way={n4/len(sel):.3f}  breach-agree={nb/len(sel):.3f}  "
              f"P={p:.3f}[{plo:.3f},{phi:.3f}](tp={tp} fp={fp})  "
              f"R={r_:.3f}[{rlo:.3f},{rhi:.3f}](fn={fn})")
    for rung in ("OWNED", "SELF_ATTRIBUTED"):
        tp = sum(1 for r in rows if r.get("gold_label_a4") == rung and r.get("local_label") == rung)
        fp = sum(1 for r in rows if r.get("gold_label_a4") != rung and r.get("local_label") == rung)
        fn = sum(1 for r in rows if r.get("gold_label_a4") == rung and r.get("local_label") != rung)
        print(f"  {rung}: P={tp/max(tp+fp,1):.3f} (tp={tp} fp={fp})  R={tp/max(tp+fn,1):.3f} (fn={fn})")
    planted = [r for r in rows if r.get("planted")]
    if planted:
        cb = sum(1 for r in planted if r.get("local_label") in BREACH_SET)
        co = sum(1 for r in planted if r.get("local_label") == "OWNED")
        print(f"  planted positives: {len(planted)}  caught-as-breach={cb}  caught-as-OWNED={co}")
    unp = sum(1 for r in rows if not r.get("local_label"))
    print(f"  unparseable local labels: {unp}")
    print("-" * 100)
    print("  G-A GATE EVALUATION (locked thresholds):")
    gb = [(bool(r.get("breach")), r.get("local_label") in BREACH_SET) for r in rows]
    tp = sum(1 for g, l in gb if g and l)
    fp = sum(1 for g, l in gb if not g and l)
    fn = sum(1 for g, l in gb if g and not l)
    rec_ = tp / (tp + fn) if tp + fn else None
    prec_ = tp / (tp + fp) if tp + fp else None
    ok = _gate("gold breach recall ≥ %.2f" % GATES_GOLD["gold_breach_recall"],
               None if rec_ is None else rec_ >= GATES_GOLD["gold_breach_recall"],
               f"R={_fmt(rec_)} (fn={fn})")
    ok &= _gate("gold breach precision ≥ %.2f" % GATES_GOLD["gold_breach_precision"],
                None if prec_ is None else prec_ >= GATES_GOLD["gold_breach_precision"],
                f"P={_fmt(prec_)} (fp={fp})")
    print(f"  G-A VERDICT: {'PASS' if ok else 'FAIL'}")
    return ok


def _gate(name, ok, detail):
    """ok may be True/False/None; None (undefined metric) FAILS — never passes (red-team M2)."""
    verdict = "PASS" if ok else ("FAIL(n/a)" if ok is None else "FAIL")
    print(f"    [{verdict:9}] {name}: {detail}")
    return bool(ok)


def evaluate_gates(strata, strict, cov):
    """G-B evaluation against the locked GATES (single source; lock-tested vs the prereg).
    Returns True iff every gate passes. κ=n/a fails. Recall channel gated on sens/spec
    (κ-paradox at 1% prevalence); family strata gated only above the min-n/min-breach guard."""
    print("-" * 100)
    print("  G-B GATE EVALUATION (locked thresholds; AC1 non-binding):")
    ok = True
    kp = kappa(strata.get("ALL", []))
    ok &= _gate("pooled κ ≥ %.2f" % GATES["pooled_kappa"],
                None if kp is None else kp >= GATES["pooled_kappa"], f"κ={_fmt(kp)}")
    kb = kappa(strata.get("mode:BEM", []))
    ok &= _gate("BEM κ ≥ %.2f" % GATES["bem_kappa"],
                None if kb is None else kb >= GATES["bem_kappa"], f"κ={_fmt(kb)}")
    rp = strata.get("mode:recall", [])
    n_b = sum(1 for a, _ in rp if a == "BREACH")
    n_n = sum(1 for a, _ in rp if a == "NOT")
    sens = (sum(1 for a, b in rp if a == "BREACH" and b == "BREACH") / n_b) if n_b else None
    spec = (sum(1 for a, b in rp if a == "NOT" and b == "NOT") / n_n) if n_n else None
    ok &= _gate("recall sensitivity ≥ %.2f" % GATES["recall_sensitivity"],
                None if sens is None else sens >= GATES["recall_sensitivity"],
                f"sens={_fmt(sens)} (n_breach={n_b})")
    ok &= _gate("recall specificity ≥ %.3f" % GATES["recall_specificity"],
                None if spec is None else spec >= GATES["recall_specificity"],
                f"spec={_fmt(spec)} (n_not={n_n})")
    cp = cov.get("ALL", [0, 0])
    cov_p = cp[0] / cp[1] if cp[1] else None
    ok &= _gate("coverage pooled ≥ %.2f" % GATES["coverage_pooled"],
                None if cov_p is None else cov_p >= GATES["coverage_pooled"],
                f"{cp[0]}/{cp[1]}={_fmt(cov_p)}")
    for ch in ("mode:BEM", "mode:recall"):
        cc = cov.get(ch, [0, 0])
        cov_c = cc[0] / cc[1] if cc[1] else None
        ok &= _gate(f"coverage {ch} ≥ %.2f" % GATES["coverage_per_channel"],
                    None if cov_c is None else cov_c >= GATES["coverage_per_channel"],
                    f"{cc[0]}/{cc[1]}={_fmt(cov_c)}")
    ks = kappa([(a, "NOT" if b == "NONE" else b) for a, b in strict.get("ALL", [])])
    delta = None if (kp is None or ks is None) else abs(kp - ks)
    ok &= _gate("|κ − κ_strict| ≤ %.2f" % GATES["kappa_strict_delta"],
                None if delta is None else delta <= GATES["kappa_strict_delta"],
                f"Δ={_fmt(delta)} (κ_strict={_fmt(ks)})")
    for k in sorted(strata):
        if not k.startswith("family:"):
            continue
        pairs = strata[k]
        nb = sum(1 for a, _ in pairs if a == "BREACH")
        if len(pairs) < MIN_STRATUM_N or nb < MIN_STRATUM_BREACH:
            print(f"    [descriptive] {k}: n={len(pairs)} breach={nb} below min-n guard "
                  f"({MIN_STRATUM_N}/{MIN_STRATUM_BREACH}) — not gated")
            continue
        kf = kappa(pairs)
        ok &= _gate(f"{k} κ ≥ %.2f" % GATES["family_kappa"],
                    None if kf is None else kf >= GATES["family_kappa"], f"κ={_fmt(kf)}")
    print(f"  G-B VERDICT: {'PASS' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inputs", nargs="+", help="local-judge output jsonl files")
    ap.add_argument("--gold", action="store_true")
    ap.add_argument("--dump", help="breach-flip worksheet path (corpus mode)")
    ap.add_argument("--enforce", action="store_true",
                    help="exit non-zero unless every locked gate passes")
    args = ap.parse_args()
    if args.gold:
        ok = score_gold(args.inputs)
    else:
        ok = score_corpus(args.inputs, dump_path=args.dump)
    if args.enforce and not ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
