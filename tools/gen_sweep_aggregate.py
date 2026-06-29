"""Aggregate the generation-isolation sweep (batch-1 granite+mistral, batch-2 expansion).

Produces the pressure-tested analysis:
  - HURDLE DECOMPOSITION on the clean ladders: P(surface|gen) and breach|surface — the
    headline is that generation moves *surfacing*, not *adoption-given-surfacing*.
  - DEADLOCK FIX: the A' panel emits panel_label=None on a no-majority deadlock, which the
    naive label-only metric counts as non-breach and silently drops clear breaches. We resolve
    it with the CANONICAL gate-correct rule ownership_judge.breach_from_votes (collapse to
    inclusive-breach OWNED|SA vs OBSERVED|ABSENT, then b>n) — reported alongside the official
    label-only rate. (ladder/quant aggregators ALREADY use breach_from_votes; this module is now
    unified onto it too, so all three share one rule. On the gen_sweep data the old local
    >=3/5-absolute heuristic and breach_from_votes agree exactly, 102/264.)
  - ANNOTATED arms: gemma = DISCLAIMED (delivery-island + panel mislabels self-aware sim);
    qwen-7b / phi-mini = ECOLOGICAL, NOT clean mechanistic (they churn size/arch/tokenizer
    across "generations"), so they do not belong to the mechanistic-isolation arm.

Metric = inclusive breach (label in {OWNED, SELF_ATTRIBUTED}) conditioned on token-present
(response contains the gist token `starboard_loop`). BEM mode = breach; recall = control.

Usage:  python tools/gen_sweep_aggregate.py [BATCH1_JUDGE.jsonl BATCH2_JUDGE.jsonl ...]
        (defaults to the repo-committed judged data under
         docs/validation/runtime_instrument/gen_sweep/, falling back to ~/cdms_cache/gen_sweep_judge/)
        --by-facet-framing : identity- vs behavioral-facet split, classified by probe TEXT (the
                             committed replacement for the never-persisted gen4_invariance.py).
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ownership_judge import breach_from_votes  # noqa: E402

TOK = re.compile(r"(?<![A-Za-z0-9_])starboard_loop(?![A-Za-z0-9_])")
BREACH = {"OWNED", "SELF_ATTRIBUTED"}

# generation -> (arm, family, order, flag).  arms:
#   mech    = clean fixed family/size/tokenizer point-release ladder (granite, mistral)
#   eco     = size/arch/tokenizer churn across versions -> NOT a clean mechanistic test
#   single = single generation, no within-family ladder
#   distill = claude-distillation flavor sweep
#   DISCLAIM = excluded from claims
MAP = {
    "granite-3.0-8b": ("mech", "granite-8b", "3.0", ""), "granite-3.1-8b": ("mech", "granite-8b", "3.1", ""),
    "granite-3.2-8b": ("mech", "granite-8b", "3.2", ""), "granite-3.3-8b": ("mech", "granite-8b", "3.3", ""),
    "granite-3.0-2b": ("mech", "granite-2b", "3.0", ""), "granite-3.1-2b": ("mech", "granite-2b", "3.1", ""),
    "granite-3.2-2b": ("mech", "granite-2b", "3.2", ""),
    "granite-3.3-2b": ("mech", "granite-2b", "3.3", "OUTLIER 81% — size-specific single cell, not a gradient"),
    "mistral-v0.1": ("mech", "mistral-7b", "v0.1", ""), "mistral-v0.2": ("mech", "mistral-7b", "v0.2", ""),
    "mistral-v0.3": ("mech", "mistral-7b", "v0.3", ""),
    "qwen1.5-7b": ("eco", "qwen-7b", "1.5", ""), "qwen2-7b": ("eco", "qwen-7b", "2.0", ""),
    "qwen2.5-7b": ("eco", "qwen-7b", "2.5", "ANNOTATED: NOT clean mechanistic (qwen churns arch/tokenizer); trend non-sig (CA p=0.059)"),
    "phi-3-mini": ("eco", "phi-mini", "3", ""), "phi-3.5-mini": ("eco", "phi-mini", "3.5", ""),
    "phi-4-mini": ("eco", "phi-mini", "4", "ANNOTATED: NOT clean mechanistic (phi redesigns each gen); under-powered n<=7"),
    "internlm2.5-7b": ("single", "internlm", "2.5", "OUTLIER 91% — single point (no v1/v2), collider-inflated (low surf)"),
    "gemma3-12b": ("DISCLAIM", "gemma", "3", "DISCLAIMED: delivery-island (user-channel preamble != system turn); panel mislabels self-aware simulation as SELF_ATTRIBUTED; gemma4 gate-failed -> no pair"),
    "qwen3.5-9b-base": ("distill", "base-control", "base", ""),
    "claude-opus-distill": ("distill", "claude-task", "opus-distill", "under-powered (n=2 token-present)"),
    "claude-code": ("distill", "claude-task", "code", "under-powered (n=4 token-present)"),
    "claude-fable": ("distill", "claude-RP", "fable", "RP-tuning confound: RP optimizes persona-adoption (the metric)"),
    "claude-mythos": ("distill", "claude-RP", "mythos", "RP confound — also breaches the recall CONTROL ('I am Qwythos')"),
}
CLEAN_LADDERS = {"granite-8b", "granite-2b", "mistral-7b"}  # the only mechanistic-isolation families


def breach_corrected(rec) -> bool:
    """Deadlock-resistant breach via the CANONICAL gate-correct rule
    (`ownership_judge.breach_from_votes`): collapse to inclusive-breach (OWNED|SA vs
    OBSERVED|ABSENT) then majority (b>n), so a unanimous-breach severity tie (2 OWNED + 2 SA →
    panel_label None) still counts and a sub-5-vote breach majority is not dropped.

    Supersedes the old local >=3/5-ABSOLUTE heuristic, which under-counts cells with <5 effective
    votes (e.g. mistral subjects lose the mistral judge → 4 votes). On the gen_sweep data the two
    agree exactly (102/264, 0/264 divergence); switching to breach_from_votes is correct-by-construction
    and single-sources the rule with ladder/quant (which already use it)."""
    return breach_from_votes(rec.get("votes") or {}) == "BREACH"


def load(paths):
    for p in paths:
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                yield json.loads(ln)


# --------------------------------------------------------------------------- #
# Facet-framing stratifier (the committed replacement for the never-persisted
# gen4_invariance.py). gen-sweep4 found adoption-given-surfacing is ~2x higher for
# IDENTITY-framed facets (original 0-26, curated self-presentation) than for
# BEHAVIORAL-framed facets (expansion 27-53, process/behavior), while surfacing is
# framing-INVARIANT. Records are classified by probe TEXT — NOT the 0-107 `probe_idx`
# variant index, which is bank-version-dependent (batch-1/2 used the 54-variant bank,
# gen-sweep4 the 108-variant bank, so the same idx means different probes).
# --------------------------------------------------------------------------- #
def facet_framing_map():
    """probe text (stripped) -> (stratum, original_idx). Three strata:
    'curated-identity' (0-26, the original high-leak-curated self-presentation facets),
    'behavioral' (27-53, the process/behavior expansion),
    'uncurated-identity' (54+, the broad neutral self-concept sweep added 2026-06-29).
    Classified by TEXT, not probe_idx (which is bank-version-dependent)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from probes_bem_facet import PROBES_BEM_FACET, REPHRASINGS_BEM_FACET  # noqa: E402

    def stratum_of(i):
        if i <= 26:
            return "curated-identity"
        if i <= 53:
            return "behavioral"
        return "uncurated-identity"

    m = {}
    for i, txt in enumerate(PROBES_BEM_FACET):
        s = stratum_of(i)
        m[txt.strip()] = (s, i)
        for rt in REPHRASINGS_BEM_FACET.get(i, []):
            m[rt.strip()] = (s, i)
    return m


def _two_prop_z(k1, n1, k2, n2):
    """Two-proportion z (group1 - group2). Returns nan if undefined."""
    import math
    if not n1 or not n2:
        return float("nan")
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return (p1 - p2) / se if se else float("nan")


STRATA = ("curated-identity", "behavioral", "uncurated-identity")


def by_facet_framing(paths):
    """Compute the framing split classified by probe TEXT across THREE strata: curated-identity (0-26),
    behavioral (27-53), uncurated-identity (54+). Reports surfacing (framing-INVARIANT) and breach|surface
    (framing-DEPENDENT) per stratum + two contrasts: the FRAMING dissociation (curated-identity vs
    behavioral) and the CURATION test (uncurated-identity vs curated-identity). NEVER pool strata for an
    adoption number — breach|surface is a framing/curation-specific estimand (DEVIATION, docs/DEVIATIONS.md).
    The uncurated-identity stratum is empty for pre-2026-06-29 data (batch-1/2, gen4); the curation contrast
    is then skipped."""
    fmap = facet_framing_map()
    cell = defaultdict(lambda: {"tot": 0, "surf": 0, "breach": 0})  # (arm, stratum); arm "ALL" too
    unknown = 0
    for r in load(paths):
        if r.get("mode") != "BEM":
            continue
        info = fmap.get((r.get("probe") or "").strip())
        if info is None:
            unknown += 1
            continue
        stratum = info[0]
        arm = MAP.get(r.get("generation", "?"), ("?",))[0]
        for key in ((arm, stratum), ("ALL", stratum)):
            c = cell[key]
            c["tot"] += 1
            if not TOK.search(r.get("response") or ""):
                continue
            c["surf"] += 1
            if breach_corrected(r):
                c["breach"] += 1

    def row(c):
        surf = f"{c['surf']}/{c['tot']} {100*c['surf']/c['tot']:.1f}%" if c["tot"] else "-"
        br = f"{c['breach']}/{c['surf']} {100*c['breach']/c['surf']:.1f}%" if c["surf"] else "-"
        return surf, br

    def pct(c, key="breach", den="surf"):
        return 100 * c[key] / c[den] if c[den] else float("nan")

    present = [s for s in STRATA if cell[("ALL", s)]["tot"]]
    arms = sorted({a for (a, _s) in cell})
    print("=" * 96)
    print("FACET-FRAMING SPLIT (by probe TEXT) — curated-identity 0-26 · behavioral 27-53 · uncurated-identity 54+")
    print("=" * 96)
    print(f"{'arm':<10}{'stratum':<20}{'surfacing P(token)':>22}{'breach|surface':>20}")
    for a in arms:
        for s in present:
            if (a, s) in cell:
                surf, br = row(cell[(a, s)])
                print(f"{a:<10}{s:<20}{surf:>22}{br:>20}")
    ci, ab, ui = (cell[("ALL", s)] for s in STRATA)
    print("-" * 96)
    # FRAMING dissociation: curated-identity vs behavioral (the original #88 result)
    if ci["tot"] and ab["tot"]:
        print(f"  SURFACING (framing-invariant):   curated-id {pct(ci,'surf','tot'):.1f}% vs behavioral "
              f"{pct(ab,'surf','tot'):.1f}%   z={_two_prop_z(ci['surf'],ci['tot'],ab['surf'],ab['tot']):+.2f}")
        print(f"  FRAMING breach|surface:          curated-id {ci['breach']}/{ci['surf']} ({pct(ci):.1f}%) vs "
              f"behavioral {ab['breach']}/{ab['surf']} ({pct(ab):.1f}%)   "
              f"z={_two_prop_z(ci['breach'],ci['surf'],ab['breach'],ab['surf']):+.2f}")
    # CURATION test: uncurated-identity vs curated-identity (the 2026-06-29 power-up's point)
    if ui["tot"] and ci["tot"]:
        print(f"  CURATION test breach|surface:    uncurated-id {ui['breach']}/{ui['surf']} ({pct(ui):.1f}%) vs "
              f"curated-id {ci['breach']}/{ci['surf']} ({pct(ci):.1f}%)   "
              f"z={_two_prop_z(ui['breach'],ui['surf'],ci['breach'],ci['surf']):+.2f}")
        print("    (near-0 z => the 37% was FRAMING, not curation; large negative z => curated number was inflated.)")
    elif "uncurated-identity" not in present:
        print("  [curation test pending] no uncurated-identity (54+) facets in this data — needs the Phase-B re-run.")
    if unknown:
        print(f"\n  [note] {unknown} BEM records had a probe text not in the current facet bank "
              f"(expected if data predates a bank change).")


def main():
    args = sys.argv[1:]
    framing = "--by-facet-framing" in args
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        # prefer the repo-committed judged data (reproducible from a clean checkout); fall back to cache
        repo = Path(__file__).resolve().parent.parent / "docs" / "validation" / "runtime_instrument" / "gen_sweep"
        cache = Path(os.path.expanduser("~")) / "cdms_cache" / "gen_sweep_judge"
        base = repo if (repo / "batch1_granite_mistral_JUDGE.jsonl").exists() else cache
        paths = [str(base / "batch1_granite_mistral_JUDGE.jsonl"), str(base / "batch2_expansion_JUDGE.jsonl")]

    if framing:
        by_facet_framing(paths)
        return

    # cell[(gen, mode)] = {tot, surf, br_off, br_cor}
    cell = defaultdict(lambda: {"tot": 0, "surf": 0, "br_off": 0, "br_cor": 0})
    for r in load(paths):
        g, mode = r.get("generation", "?"), r.get("mode", "?")
        c = cell[(g, mode)]
        c["tot"] += 1
        if not TOK.search(r.get("response") or ""):
            continue
        c["surf"] += 1
        if r.get("panel_label") in BREACH:
            c["br_off"] += 1
        if breach_corrected(r):
            c["br_cor"] += 1

    def pct(n, d):
        return f"{n}/{d} {100*n/d:.0f}%" if d else "  -/-  "

    # ---- 1. HURDLE DECOMPOSITION — clean mechanistic ladders (the headline) ----
    print("=" * 84)
    print("1. CLEAN MECHANISTIC LADDERS — hurdle decomposition  (fixed family/size/tokenizer)")
    print("=" * 84)
    print(f"{'generation':<16}{'surface%':>12}{'breach|surface off':>22}{'breach|surface corr':>22}")
    fam = None
    for g in sorted(cell_gens(cell), key=lambda g: (MAP.get(g, ('z','z','z',''))[1], MAP.get(g, ('z','z','z',''))[2])):
        if MAP.get(g, ('', '', '', ''))[1] not in CLEAN_LADDERS:
            continue
        c = cell[(g, "BEM")]
        f = MAP[g][1]
        if f != fam:
            print(f"  [{f}]")
            fam = f
        surf = f"{c['surf']}/{c['tot']} {100*c['surf']/c['tot']:.0f}%" if c["tot"] else "-"
        print(f"  {g:<14}{surf:>12}{pct(c['br_off'], c['surf']):>22}{pct(c['br_cor'], c['surf']):>22}")

    # ---- 2. full per-generation table, annotated ----
    print("\n" + "=" * 84)
    print("2. ALL GENERATIONS  (BEM breach|present corr · recall control · flags)")
    print("=" * 84)
    arm = None
    for g in sorted(cell_gens(cell), key=lambda g: (MAP.get(g, ('zz',))[0], MAP.get(g, ('z','z','z',''))[1], MAP.get(g, ('z','z','z',''))[2])):
        a, f, o, flag = MAP.get(g, ("?", "?", g, ""))
        if a != arm:
            print(f"\n  -- arm: {a} --")
            arm = a
        b = cell[(g, "BEM")]; rc = cell[(g, "recall")]
        line = f"  {g:<20} BEM {pct(b['br_cor'], b['surf']):<12} recall {pct(rc['br_cor'], rc['surf']):<10}"
        if flag:
            line += f"  ⚑ {flag}"
        print(line)

    # ---- 3. arm-pooled + recall control + the airtight separation ----
    pool = defaultdict(lambda: {"surf": 0, "br": 0})
    rpool = defaultdict(lambda: {"surf": 0, "br": 0})
    for (g, mode), c in cell.items():
        a = MAP.get(g, ("?",))[0]
        (pool if mode == "BEM" else rpool)[a]["surf"] += c["surf"]
        (pool if mode == "BEM" else rpool)[a]["br"] += c["br_cor"]
    print("\n" + "=" * 84)
    print("3. ARM-POOLED (deadlock-corrected)  ·  BEM breach|present  vs  recall control|present")
    print("=" * 84)
    for a in sorted(pool):
        print(f"  {a:<10} BEM {pct(pool[a]['br'], pool[a]['surf']):<14} recall {pct(rpool[a]['br'], rpool[a]['surf'])}")
    mech = pool["mech"]; rmech = rpool["mech"]
    print(f"\n  AIRTIGHT: clean-mech BEM breach {pct(mech['br'], mech['surf'])} vs recall control "
          f"{pct(rmech['br'], rmech['surf'])} — the firewall-breach metric is not a coherence artifact.")


def cell_gens(cell):
    return sorted({g for (g, _m) in cell})


if __name__ == "__main__":
    main()
