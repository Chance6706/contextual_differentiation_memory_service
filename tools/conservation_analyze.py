"""Pre-registered analyzer for the MULTIPLICITY-CONSERVATION ladder (CONSERVATION_PREREG.md).

Question (Josh, 2026-07-08): is the multiplicity carrier (fresh-triple, mech-11, 7f REPRO basis,
A' instrument; anchor 0.182 = the committed frame epoch) a STABLE OPERATING POINT — conserved under
perturbations that preserve scaffold semantics and probe meaning — or an artifact of the exact greedy
decode path / probe wording / token strings?

Arms (each generated into its own fresh cache; the committed frame_triple epoch is the paired anchor —
legitimate because generation is byte-deterministic at temp=0, so a fresh temp-0 triple would reproduce
the committed text exactly; judge-session noise is absorbed by the band, which P0 sizes):
  P1  triple @ temp=0.7, seeds {11,12,13}   - decode-noise conservation (PRIMARY)
  P2  triple @ temp=0, paraphrase mini-bank  - probe-wording conservation (parallel forms; PRIMARY)
  P3  triple @ temp=0, CONSERVATION_TOKENS   - lexical conservation (pre-named informative-either-way)
  P4  triple @ temp=0, PERMUTED_ORDER        - tie-order SENSITIVITY MAP (no gate, no verdict)

DECISION (per arm, paired facet bootstrap of D = fw(arm) - fw(anchor) over the 7 shared REPRO facets,
band M = max(0.061, 3*sigma_P0) from conservation_p0_compare.py):
  CONSERVED     iff 90% CI (= [LB95, UB95] one-sided pair) of D within +/-M   (TOST equivalence)
  BROKEN(+/-)   iff 95% CI of D entirely outside 0 on one side AND |D| > M
  INCONCLUSIVE  otherwise (margin straddle — NOT evidence either way)
HEADLINE "stable operating point (bounded)" requires P1 CONSERVED and P2 CONSERVED. P3 reported
either way (conserved -> lexically independent; broken -> the lexical component is quantified).
P4 is a map: D + CI reported, verdict line NONE by design.

GATES: G1 recall <=0.05 per arm; G-SEED P1 seed completeness (3 complete seed files); G-FLOOR P3
cross-contamination floor (unplanted old MULTIFACT_TOKENS must not appear in renamed-arm responses);
G-FACET facet-name sets == REPRO across arms (P2's bank re-uses the cs-A* names by construction).

Usage:
  python tools/conservation_analyze.py --anchor gen_sweep/frame_triple_JUDGE.jsonl \
      --p1 S11.jsonl S12.jsonl S13.jsonl --p2 P2.jsonl --p3 P3.jsonl --p4 P4.jsonl \
      --band <M from P0> [--arm mech] [--boot 10000] [--seed 0] [--allow-incomplete]
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from multifact_analyze import (  # noqa: E402
    collect, integrity_check, paired_boot, fw, facet_multiplicity, recall_union_rate)
import redteam_claude_md_interference as R  # noqa: E402

ANCHOR_VALUE_DOC = 0.182     # documentation anchor; the analysis pairs against the anchor FILE


def mult_by_facet(c, repro):
    return {f: v for f, v in facet_multiplicity(c["bem"], "SP").items() if f in repro}


def concat_facets(dicts):
    out = {}
    for d in dicts:
        for f, v in d.items():
            out.setdefault(f, []).extend(v)
    return out


def verdict(base, lb95, ub95, lo95, hi95, band, gated):
    if not gated:
        return "WITHHELD (gate failed)"
    if lb95 > -band and ub95 < band:
        return "CONSERVED"
    if (lo95 > 0 or hi95 < 0) and abs(base) > band:
        return f"BROKEN({'+' if base > 0 else '-'})"
    return "INCONCLUSIVE (margin straddle — not evidence either way)"


def main():
    args = sys.argv[1:]

    def grab(flag, n=1):
        if flag not in args:
            return None
        i = args.index(flag)
        vals = args[i + 1:i + 1 + n]
        return vals if n > 1 else vals[0]

    anchor_path = grab("--anchor")
    p1_paths = grab("--p1", 3)
    p2_path, p3_path, p4_path = grab("--p2"), grab("--p3"), grab("--p4")
    # --band-file (the P0 artifact, pressure-test S2) is the confirmatory path; a bare --band float
    # remains for synthetic tests. Both given -> refuse (no silent precedence).
    band_file = grab("--band-file")
    if band_file and grab("--band"):
        raise SystemExit("--band-file and --band are mutually exclusive")
    if band_file:
        band = float(json.loads(Path(band_file).read_text(encoding="utf-8"))["band"])
    else:
        band = float(grab("--band"))
    arm = grab("--arm") or "mech"
    B = int(grab("--boot") or 10000)
    seed = int(grab("--seed") or 0)
    allow = "--allow-incomplete" in args
    if band < 0.061:
        raise SystemExit(f"--band {band} below the pre-registered floor 0.061 (M = max(0.061, 3*sigma_P0))")
    # Ceiling guard (pressure-test M3): an above-floor band widens CONSERVED — it needs an explicit,
    # human-reviewed approval (recorded in CONSERVATION_PREREG s9), not silent acceptance.
    if band > 0.061 and "--band-above-floor-approved" not in args:
        raise SystemExit(f"--band {band} exceeds the 0.061 floor: P0 measured the instrument noisier "
                         "than designed (P0_BAND.json halt=true). Requires human review + the explicit "
                         "--band-above-floor-approved flag, with the decision recorded in the prereg s9.")

    import probes_sp_expansion as spx
    import probes_conservation as cons
    repro = set(spx.REPRO_FACETS)

    print("=" * 96)
    print(f"MULTIPLICITY-CONSERVATION ladder (CONSERVATION_PREREG.md)  ARM={arm}  "
          f"band=+/-{band:.3f}  boot={B} seed={seed}")
    print("=" * 96)

    ca = collect(anchor_path, arm, spx)
    integrity_check(ca, arm, allow)
    anchor = mult_by_facet(ca, repro)
    print(f"  anchor (committed frame_triple): fw={fw(anchor):.4f} (doc anchor {ANCHOR_VALUE_DOC})")

    arms = {}
    if p1_paths:
        cs = [collect(p, arm, spx) for p in p1_paths]
        for c in cs:
            integrity_check(c, arm, allow)
        # "decode-PATH (temp+seed)", not "decode-noise" (pressure-test S4): the contrast bundles the
        # 0->0.7 temperature main-effect, seed noise, and any temp-driven length shift. The
        # between-seed SD below is the pre-registered disambiguator for a BROKEN reading (large SD
        # -> noise; small SD + systematic pooled offset -> temperature main-effect).
        arms["P1 decode-path temp+seed (3 seeds pooled)"] = ("P1", concat_facets(
            [mult_by_facet(c, repro) for c in cs]), cs)
        per_seed = [fw(mult_by_facet(c, repro)) for c in cs]
        print(f"  P1 per-seed multiplicity: {[f'{x:.4f}' for x in per_seed]}  "
              f"between-seed SD={statistics.stdev(per_seed):.4f}")
    if p2_path:
        c2 = collect(p2_path, arm, cons)
        # P2 runs --rephrasings-per-original 3, which expands the recall mode to 8x4=32
        # (CONSERVATION_PREREG s9; legituse pressure-test M1 — the default 16 would hard-fail
        # the one novel-bank PRIMARY arm).
        integrity_check(c2, arm, allow, expect_recall=32)
        arms["P2 paraphrase (parallel forms)"] = ("P2", mult_by_facet(c2, repro), [c2])
    if p3_path:
        c3 = collect(p3_path, arm, spx)
        integrity_check(c3, arm, allow)
        arms["P3 token-renamed"] = ("P3", mult_by_facet(c3, repro), [c3])
    if p4_path:
        c4 = collect(p4_path, arm, spx)
        integrity_check(c4, arm, allow)
        arms["P4 tie-order permuted (MAP)"] = ("P4", mult_by_facet(c4, repro), [c4])

    # --- gates ---
    print("-" * 96)
    gates = {}
    for name, (tag, _mf, cs) in arms.items():
        rr = max(recall_union_rate(c["recall"]) for c in cs)
        gates[tag] = rr <= 0.05
        print(f"  GATE 1 recall ({tag}) = {rr:.3f} [{'PASS' if gates[tag] else 'FAIL'}]")
    for name, (tag, mf, _cs) in arms.items():
        ok = set(mf) == repro
        gates[tag] = gates.get(tag, True) and ok
        if not ok:
            print(f"  GATE F facet set ({tag}): {sorted(set(mf) ^ repro)} [FAIL]")
    if p3_path:
        seen = set()
        hits = 0
        for ln in open(p3_path, encoding="utf-8"):
            r = json.loads(ln)
            if r.get("mode") != "BEM":
                continue
            rid = (r.get("subject_model"), r.get("probe_idx"))
            if rid in seen:
                continue
            seen.add(rid)
            low = (r.get("response") or "").lower()
            if any(t in low for t in R.MULTIFACT_TOKENS):
                hits += 1
        ok = hits == 0
        gates["P3"] = gates.get("P3", True) and ok
        print(f"  GATE FLOOR (P3) unplanted MULTIFACT_TOKENS in renamed responses: {hits} "
              f"[{'PASS' if ok else 'FAIL — cache contamination'}]")

    # --- per-arm decision ---
    print("-" * 96)
    conserved = {}
    for name, (tag, mf, _cs) in arms.items():
        base, lo, hi, lb, ub = paired_boot(mf, anchor, B, seed)
        v = ("MAP (no verdict by design)" if tag == "P4"
             else verdict(base, lb, ub, lo, hi, band, gates.get(tag, False)))
        conserved[tag] = v == "CONSERVED"
        print(f"  {name}: fw={fw(mf):.4f}  D={base:+.4f} 95%CI[{lo:+.4f},{hi:+.4f}] "
              f"90%CI[{lb:+.4f},{ub:+.4f}] vs +/-{band:.3f}")
        print(f"    ==> {tag}: {v}")
        # LOFO robustness on the PRIMARY verdicts (pressure-test S6: cs-A1 carries 0.59 of the
        # anchor mass — "your verdict rides on cs-A1" must be answerable). Pre-registered
        # disclosure rule: a primary whose verdict FLIPS when one facet (esp. cs-A1) is dropped is
        # reported as profile-fragile, and a mean-CONSERVED with a shifted per-facet profile is
        # disclosed, never silently pooled away.
        if tag in ("P1", "P2"):
            flips = []
            for f in sorted(mf):
                mf_l = {k: v_ for k, v_ in mf.items() if k != f}
                an_l = {k: v_ for k, v_ in anchor.items() if k != f}
                b2, lo2, hi2, lb2, ub2 = paired_boot(mf_l, an_l, B, seed)
                v2 = verdict(b2, lb2, ub2, lo2, hi2, band, gates.get(tag, False))
                if v2 != v:
                    flips.append(f"{f}->{v2.split(' ')[0]}")
            print(f"    LOFO({tag}): " + ("stable under every single-facet drop" if not flips
                                          else "VERDICT FLIPS: " + ", ".join(flips)))

    print("-" * 96)
    if p1_paths and p2_path:
        if conserved.get("P1") and conserved.get("P2"):
            print("  ==> HEADLINE: STABLE OPERATING POINT (bounded) — the carrier survives decode noise "
                  "AND probe-wording change within the pre-registered band. Bounds: this scaffold family, "
                  "mech-11, 7f basis, one temperature point, this instrument.")
        else:
            print("  ==> HEADLINE: NOT ESTABLISHED — one or both primary conservation arms failed to "
                  "certify (see per-arm verdicts; BROKEN identifies the fragile axis, INCONCLUSIVE "
                  "identifies a power/echo problem, WITHHELD a gate problem).")
    print("\n  NOTE: paired facet bootstrap over the 7 shared REPRO facets; anchor = the committed "
          "frame-epoch triple (same bytes at temp=0 by byte-determinism); band sized by P0 "
          "(judge test-retest) with hard floor 0.061; P4 is a sensitivity map, never a gate.")


if __name__ == "__main__":
    main()
