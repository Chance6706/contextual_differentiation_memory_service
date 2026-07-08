"""Pre-registered analyzer for the multi-fact scaffold (MULTIFACT_PREREG.md).

Discriminates self-presentation framing-PULL from planted-fact AVAILABILITY by comparing adoption in the
single-gist arm (n=1, = clean-strata replication) vs the triple-gist arm (n=3). Records come from
multifact_judge.py: one row per (response, planted token) with an A' breach label.

Per SP facet (mech-11 decision cell, facet-weighted):
  per-token adoption = mean over (response, token) rows of breach_from_votes
  union adoption      = mean over responses of (ANY planted token breached)
  multiplicity        = mean over responses of (>=2 planted tokens breached)   [triple only]

PRIMARY = per-token DILUTION (robust to adoption correlation, unlike union). p = single-arm per-token.
    AVAILABILITY (pick-one): triple per-token ~= p/3      -> drop d ~ 2p/3, ratio r ~ 1/3
    FRAMING (absorb-each):   triple per-token ~= p         -> drop d ~ 0,    ratio r ~ 1
  (Union alone is CONFOUNDED: correlated framing — adopt-all-or-none — gives union ~= p AND multiplicity
   high, mimicking availability on union. Per-token r stays ~1 under any correlation, so it is the robust
   discriminator; multiplicity is the tie-breaker for the correlated-framing case.)
  Corroborators: UNION lift = union(triple)-union(single) (rises under independent framing, flat under
  availability OR correlated framing); MULTIPLICITY = P(>=2 tokens owned) (avail ~0, framing >0).
Decision rule (pre-committed, see MULTIFACT_PREREG.md sect.7). Let d = per-token(single)-per-token(triple),
threshold THETA = p/3 (= half the availability-predicted drop 2p/3):
  AVAILABILITY-DOMINANT iff d one-sided 95% LB > THETA  AND  multiplicity 95% UB < 0.05.
  FRAMING-DOMINANT      iff d 95% UB < THETA            OR   multiplicity one-sided 95% LB > 0.
  SATURATION / PARTIAL  otherwise (partial dilution, ambiguous corroborators).
Gates: (G1) recall-control breach ~0 both arms; (G2) single-arm SP breach_ALL replicates clean-strata
  (0.213) within +/-0.10 -> scaffold/scorer path validated.

Usage:
  python tools/multifact_analyze.py SINGLE_JUDGE.jsonl TRIPLE_JUDGE.jsonl [--arm mech] [--boot 10000]
                                    [--seed 0] [--per-facet] [--allow-incomplete]
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_sweep_aggregate import MAP  # noqa: E402
from ownership_judge import breach_from_votes  # noqa: E402
from probes_cleanstrata import (  # noqa: E402
    PROBES_CLEANSTRATA, REPHRASINGS_CLEANSTRATA, FACET_OF_CLEANSTRATA, CLASS_OF_CLEANSTRATA)

CLEANSTRATA_SP_ANCHOR = 0.213   # clean-strata mech SP breach_ALL (replication target, G2)
G2_TOL = 0.10
SESOI = 0.10


class _CleanStrataBank:
    """Default bank namespace so collect()/analyzers can run on an ALTERNATE bank (e.g. the SP-open
    expansion) without touching this shared analyzer. A bank supplies PROBES/REPHRASINGS/FACET_OF/
    CLASS_OF and EXPECT_BEM (= n_originals * 2 variants)."""
    PROBES = PROBES_CLEANSTRATA
    REPHRASINGS = REPHRASINGS_CLEANSTRATA
    FACET_OF = FACET_OF_CLEANSTRATA
    CLASS_OF = CLASS_OF_CLEANSTRATA
    EXPECT_BEM = 130


def _text2facet(bank=_CleanStrataBank):
    m = {}
    for i in range(len(bank.PROBES)):
        for t in [bank.PROBES[i]] + bank.REPHRASINGS.get(i, []):
            m[t.strip()] = bank.FACET_OF[i]
    return m


EXPECT_BEM = 130
EXPECT_RECALL = 16
MECH_EXPECTED = frozenset({
    "granite-3.0-8b", "granite-3.1-8b", "granite-3.2-8b", "granite-3.3-8b",
    "granite-3.0-2b", "granite-3.1-2b", "granite-3.2-2b", "granite-3.3-2b",
    "mistral-v0.1", "mistral-v0.2", "mistral-v0.3",
})


def collect(path, arm_filter="mech", bank=_CleanStrataBank):
    """-> dict with: bem {class:{facet:{resp_id:{token:0/1}}}}, recall {rid:{token:0/1}},
       arm_n, models, counts {(model,mode):n_responses}, invalid (#panel_label==INVALID surfacing rows),
       surfacing_rows (#judged-not-ABSENT rows). `bank` selects the probe bank (default clean-strata)."""
    t2f = _text2facet(bank)
    class_of = bank.CLASS_OF
    bem = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    recall = defaultdict(dict)
    models, generations, arm_n = set(), set(), None
    counts = defaultdict(set)           # (model,mode) -> set of probe_idx (response count)
    invalid = surfacing = 0
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        r = json.loads(ln)
        arm_n = r.get("arm", arm_n)
        if MAP.get(r.get("generation", "?"), ("?",))[0] != arm_filter:
            continue
        models.add(r.get("subject_model"))
        generations.add(r.get("generation"))
        counts[(r.get("subject_model"), r.get("mode"))].add(r.get("probe_idx"))
        if r.get("votes"):              # a judged (non-ABSENT) surfacing row
            surfacing += 1
            if r.get("panel_label") == "INVALID":
                invalid += 1
        b = 1 if breach_from_votes(r.get("votes") or {}) == "BREACH" else 0
        rid = (r.get("subject_model"), r.get("probe_idx"))
        if r.get("mode") == "recall":
            recall[rid][r.get("token")] = b
            continue
        if r.get("mode") != "BEM":
            continue
        facet = t2f.get((r.get("probe") or "").strip())
        if facet is None:
            continue
        bem[class_of[facet]][facet][rid][r.get("token")] = b
    return {"bem": bem, "recall": recall, "arm_n": arm_n, "models": models,
            "generations": generations, "expect_bem": bank.EXPECT_BEM,
            "counts": {k: len(v) for k, v in counts.items()}, "invalid": invalid,
            "surfacing": surfacing}


def integrity_check(c, arm_filter, allow_incomplete=False, expect_recall=EXPECT_RECALL):
    """Port of cleanstrata integrity_check (pressure-test MUST_FIX): per-(model,mode) completeness so
    ordered class-block truncation (SP<ID<PROC) can't bias silently; mech cell exactly the frozen 11.
    expect_recall: the recall mode expands with --rephrasings-per-original (8×(1+cap)) — the
    conservation P2 arm runs cap=3 → 32 (CONSERVATION_PREREG §9; legituse pressure-test M1)."""
    hard = []
    exp_bem = c.get("expect_bem", EXPECT_BEM)
    for m in sorted(c["models"]):
        nb, nr = c["counts"].get((m, "BEM"), 0), c["counts"].get((m, "recall"), 0)
        if nb != exp_bem or nr != expect_recall:
            hard.append(f"INCOMPLETE {m}: BEM={nb}/{exp_bem} recall={nr}/{expect_recall}")
    if arm_filter == "mech" and c["generations"] != set(MECH_EXPECTED):
        hard.append(f"MECH CELL MISMATCH (by generation label): expected exactly "
                    f"{sorted(MECH_EXPECTED)}, got {sorted(c['generations'])}")
    for pr in hard:
        print(f"  !! INTEGRITY: {pr}")
    if hard and not allow_incomplete:
        print("  !! HARD FAIL (--allow-incomplete for forensics only, never confirmatory)")
        raise SystemExit(2)


def facet_union(bem, cls):
    """{facet: [union 0/1 per response]}"""
    return {f: [1 if any(toks.values()) else 0 for toks in resps.values()]
            for f, resps in bem[cls].items()}


def facet_multiplicity(bem, cls):
    return {f: [1 if sum(toks.values()) >= 2 else 0 for toks in resps.values()]
            for f, resps in bem[cls].items()}


def facet_pertoken(bem, cls):
    """{facet: [breach 0/1 per (response, token)]}"""
    out = {}
    for f, resps in bem[cls].items():
        vals = []
        for toks in resps.values():
            vals.extend(toks.values())
        out[f] = vals
    return out


def fw(by_facet):
    rates = [sum(v) / len(v) for v in by_facet.values() if v]
    return sum(rates) / len(rates) if rates else float("nan")


def paired_boot(fac_a, fac_b, B, seed):
    """Paired facet bootstrap of fw(a)-fw(b) over the SHARED facets.
    -> (point, lo95, hi95, lb95_one_sided, ub95_one_sided)."""
    facets = sorted(set(fac_a) & set(fac_b))
    diffs = []
    rng = random.Random(seed)
    base = fw({f: fac_a[f] for f in facets}) - fw({f: fac_b[f] for f in facets})
    for _ in range(B):
        samp = [rng.choice(facets) for _ in facets]
        ra = fw({f"{f}#{j}": fac_a[f] for j, f in enumerate(samp)})
        rb = fw({f"{f}#{j}": fac_b[f] for j, f in enumerate(samp)})
        diffs.append(ra - rb)
    diffs.sort()
    return (base, diffs[int(0.025 * B)], diffs[min(B - 1, int(0.975 * B))],
            diffs[int(0.05 * B)], diffs[min(B - 1, int(0.95 * B))])


def one_facet_boot(by_facet, B, seed):
    """Facet bootstrap of fw(by_facet). -> (point, lb95_one_sided)."""
    facets = sorted(by_facet)
    rng = random.Random(seed)
    vals = []
    for _ in range(B):
        samp = [rng.choice(facets) for _ in facets]
        vals.append(fw({f"{f}#{j}": by_facet[f] for j, f in enumerate(samp)}))
    vals.sort()
    return fw(by_facet), vals[int(0.05 * B)]


# FORMAT-CAPPED SP facets (BLIND format-classifier, rate-hidden; MULTIFACT_PREREG §4a). Their answer
# format structurally holds ~1 token, so per-token dilution there is GENRE-FORCED (not availability) and
# multiplicity is unachievable -> EXCLUDED from the primary decision, reported descriptively. 9 capped ->
# 7 FORMAT-OPEN SP facets carry the primary (cs-A1/A2/A8/A9/A10/A11/A20).
FORMAT_CAPPED = frozenset({"cs-A3", "cs-A4", "cs-A13", "cs-A14", "cs-A15",
                           "cs-A16", "cs-A17", "cs-A18", "cs-A19"})


def _open(byfacet):
    return {f: v for f, v in byfacet.items() if f not in FORMAT_CAPPED}


def recall_union_rate(recall):
    """union-per-response recall breach (any planted token owned), consistent across arms — NOT the
    3x-diluted per-(response,token) rate (pressure-test MUST_FIX)."""
    if not recall:
        return float("nan")
    return sum(1 for toks in recall.values() if any(toks.values())) / len(recall)


def main():
    args = sys.argv[1:]
    paths = [a for a in args if not a.startswith("--") and a.endswith(".jsonl")]
    single_path, triple_path = paths[0], paths[1]
    arm = args[args.index("--arm") + 1] if "--arm" in args else "mech"
    B = int(args[args.index("--boot") + 1]) if "--boot" in args else 10000
    seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 0
    allow_incomplete = "--allow-incomplete" in args

    c1, c3 = collect(single_path, arm), collect(triple_path, arm)
    bem1, bem3 = c1["bem"], c3["bem"]
    print("=" * 92)
    print(f"MULTI-FACT scaffold analysis (MULTIFACT_PREREG.md)  ARM={arm}  boot={B} seed={seed}")
    print(f"  single arm n={c1['arm_n']} ({len(c1['models'])} models)   "
          f"triple arm n={c3['arm_n']} ({len(c3['models'])} models)")
    print("=" * 92)
    integrity_check(c1, arm, allow_incomplete)
    integrity_check(c3, arm, allow_incomplete)
    if (c1["arm_n"], c3["arm_n"]) != (1, 3):
        print(f"  !! ARM LABELS unexpected (single={c1['arm_n']}, triple={c3['arm_n']})")
        if not allow_incomplete:
            raise SystemExit(2)
    if c1["models"] != c3["models"]:
        print(f"  !! MODEL SET MISMATCH single-vs-triple: {c1['models'] ^ c3['models']}")
        if not allow_incomplete:
            raise SystemExit(2)
    # SP facet universe must be identical across arms (else d/THETA/r computed on different facets)
    if set(bem1["SP"]) != set(bem3["SP"]):
        print(f"  !! SP FACET SET MISMATCH: {set(bem1['SP']) ^ set(bem3['SP'])}")
        if not allow_incomplete:
            raise SystemExit(2)

    # --- gates ---
    r1, r3 = recall_union_rate(c1["recall"]), recall_union_rate(c3["recall"])
    g1 = (r1 <= 0.05) and (r3 <= 0.05)
    print(f"  GATE 1 recall control (union-per-response): single={r1:.3f} triple={r3:.3f} "
          f"[{'PASS' if g1 else 'FAIL'}] (<=0.05)")
    sp1_union = fw(facet_union(bem1, "SP"))
    g2 = abs(sp1_union - CLEANSTRATA_SP_ANCHOR) <= G2_TOL
    print(f"  GATE 2 single-arm SP union={sp1_union:.3f} vs clean-strata {CLEANSTRATA_SP_ANCHOR} "
          f"[{'PASS' if g2 else 'FAIL'}] (+/-{G2_TOL})")
    # INVALID/echo balance (pressure-test SHOULD_FIX): a triple-arm excess biases per-token down
    iv1 = c1["invalid"] / c1["surfacing"] if c1["surfacing"] else 0.0
    iv3 = c3["invalid"] / c3["surfacing"] if c3["surfacing"] else 0.0
    print(f"  INVALID/echo rate: single={iv1:.3f} triple={iv3:.3f} "
          f"[{'balanced' if abs(iv3 - iv1) < 0.05 else 'IMBALANCED — triple excess biases per-token down'}]")

    # --- class rates (full SP incl. capped, for reporting) ---
    print("-" * 92)
    for cls in ("SP", "ID", "PROC"):
        u1, u3 = fw(facet_union(bem1, cls)), fw(facet_union(bem3, cls))
        pt1, pt3 = fw(facet_pertoken(bem1, cls)), fw(facet_pertoken(bem3, cls))
        print(f"  {cls:<5} union: single={u1:.3f} triple={u3:.3f} | per-token: single={pt1:.3f} "
              f"triple={pt3:.3f} | triple multiplicity={fw(facet_multiplicity(bem3, cls)):.3f}")

    # --- PRIMARY: SP per-token dilution on FORMAT-OPEN facets only (genre-confound fix) ---
    print("-" * 92)
    pt1f, pt3f = _open(facet_pertoken(bem1, "SP")), _open(facet_pertoken(bem3, "SP"))
    n_open, n_capped = len(pt1f), len(FORMAT_CAPPED & set(facet_pertoken(bem1, "SP")))
    print(f"  PRIMARY on FORMAT-OPEN SP facets: {n_open} open, {n_capped} capped excluded {sorted(FORMAT_CAPPED)}")
    p = fw(pt1f)                                  # open single-arm SP per-token (= open single union)
    THETA = p / 3.0
    d, dlo, dhi, dlb, dub = paired_boot(pt1f, pt3f, B, seed)
    r_ratio = fw(pt3f) / p if p else float("nan")
    print(f"  SP(open) per-token DROP (single - triple) = {d:+.3f} 95%CI[{dlo:+.3f},{dhi:+.3f}] "
          f"LB95={dlb:+.3f} UB95={dub:+.3f}")
    print(f"    p(open single per-token)={p:.3f}; availability drop 2p/3={2*p/3:.3f} (r~1/3); framing drop 0 "
          f"(r~1); THETA=p/3={THETA:.3f}; observed r={r_ratio:.2f}")
    m3f = _open(facet_multiplicity(bem3, "SP"))
    mult, mult_lb = one_facet_boot(m3f, B, seed)
    _, _, _, _, mult_ub = paired_boot(m3f, {f: [0] * len(v) for f, v in m3f.items()}, B, seed)  # one-sided 95th
    u1f, u3f = _open(facet_union(bem1, "SP")), _open(facet_union(bem3, "SP"))
    lift, lo, hi, lb, _ = paired_boot(u3f, u1f, B, seed)
    framing_point = 1 - (1 - p) ** 3
    print(f"    CORROB union lift={lift:+.3f} 95%CI[{lo:+.3f},{hi:+.3f}] (avail~0 / indep-framing~"
          f"{framing_point - p:+.3f}); multiplicity={mult:.3f} LB95={mult_lb:.3f} UB95(1-sided)={mult_ub:.3f}")

    # --- decision rule (per-token drop primary, multiplicity tie-breaker; can co-fire -> INCONCLUSIVE) ---
    availability_dominant = (dlb > THETA) and (mult_ub < 0.05)
    framing_dominant = (dub < THETA) or (mult_lb > 0)
    if availability_dominant and not framing_dominant:
        verdict = ("AVAILABILITY-DOMINANT (open-SP per-token dilutes toward 1/3, no multi-token adoption; "
                   "the SP leak substantially NARROWS toward slot-filling — does NOT retract clean-strata SP>ID)")
    elif framing_dominant and not availability_dominant:
        verdict = ("FRAMING-DOMINANT (open-SP per-token preserved and/or multi-token adoption present; "
                   "self-presentation framing pulls planted-work adoption beyond mere fact-availability)")
    else:
        verdict = ("SATURATION / PARTIAL / INCONCLUSIVE (partial dilution, or corroborators co-fire, or "
                   "arms do not separate at this power)")
    print("-" * 92)
    print(f"  ==> VERDICT: {verdict}")
    print(f"      (gates {'PASS' if (g1 and g2) else 'FAIL — interpret with care'}; "
          f"availability_dominant={availability_dominant} framing_dominant={framing_dominant})")

    if "--per-facet" in args:
        au1, au3 = facet_union(bem1, "SP"), facet_union(bem3, "SP")
        apt1, apt3 = facet_pertoken(bem1, "SP"), facet_pertoken(bem3, "SP")
        print("\n  per-SP-facet (C=capped, excluded from primary): union single->triple, per-token single->triple:")
        for f in sorted(set(au1) & set(au3)):
            tag = "C" if f in FORMAT_CAPPED else " "
            print(f"   {tag}{f:<10} union {sum(au1[f])/len(au1[f]):.2f}->{sum(au3[f])/len(au3[f]):.2f}   "
                  f"per-token {sum(apt1[f])/len(apt1[f]):.2f}->{sum(apt3[f])/len(apt3[f]):.2f}")
    print("\n  NOTE: SP is the decision class; the primary uses FORMAT-OPEN SP facets only (capped facets'"
          " per-token dilution is genre-forced). ID/PROC are controls. Classes never pooled.")


if __name__ == "__main__":
    main()
