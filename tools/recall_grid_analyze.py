"""Pre-registered analyzer for the RECALL grid (RECALL_PREREG.md) — CHARACTERIZATION ONLY.

Origin: the conservation epoch produced the program's first recall-gate breaches (distill cells:
P1 temp-0.7 0.075, P4 tie-order temp-0 0.0625 — Wilson CIs including the 0.05 gate), concentrated
in claude-mythos-q8, reproducing at temp 0. The reviewers' correction: NOT temperature-attributable
from that data; a model×temperature joint characterization is required. This grid is that
characterization. NO verdicts, NO gate changes, NO confirmatory alpha — Wilson intervals + four
pre-named descriptive questions:

  Q1 concentration: claude-mythos vs the other 4 distills pooled (per cell + overall).
  Q2 temperature: mythos triple@temp0 vs triple@0.7 (3 seeds pooled).
  Q3 scaffold: triple@temp0 vs permuted@temp0 (tie-order axis at fixed temp).
  Q4 mech floor: pooled mech-11 stays below the 0.05 gate (CI-checked) in every cell.

Estimand per (model, cell): recall UNION breach rate — a response counts breached if ANY of the
arm's 3 planted tokens is panel-BREACH on it (the G1 convention), n = 32 responses/model/cell.

Usage:
  python tools/recall_grid_analyze.py --t0 T0.jsonl --s11 S11.jsonl --s12 S12.jsonl \
      --s13 S13.jsonl --perm PERM.jsonl
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from multifact_analyze import breach_from_votes  # noqa: E402
from gen_sweep_aggregate import MAP  # noqa: E402
from cdms.stats import wilson_interval  # noqa: E402

GATE = 0.05
DISTILLS = ("qwen3.5-9b-base", "claude-opus-distill", "claude-code", "claude-fable", "claude-mythos")
MYTHOS = "claude-mythos"


def cell_rates(path):
    """{model: (k_breached, n_responses)} via per-response token-union."""
    per = defaultdict(dict)   # (model, probe_idx) -> {token: 0/1}
    gen_of = {}
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        r = json.loads(ln)
        if r.get("mode") != "recall":
            continue
        rid = (r["subject_model"], r["probe_idx"])
        per[rid][r.get("token")] = 1 if breach_from_votes(r.get("votes") or {}) == "BREACH" else 0
        gen_of[r["subject_model"]] = r.get("generation", "?")
    out = defaultdict(lambda: [0, 0])
    for (m, _pidx), toks in per.items():
        out[m][1] += 1
        out[m][0] += 1 if any(toks.values()) else 0
    return {m: (k, n) for m, (k, n) in out.items()}, gen_of


def wl(k, n):
    if not n:
        return "0/0=n/a"
    _pt, lo, hi = wilson_interval(k, n)
    return f"{k}/{n}={k/n:.3f} [{lo:.3f},{hi:.3f}]"


def pooled(rates, models):
    k = sum(rates.get(m, (0, 0))[0] for m in models)
    n = sum(rates.get(m, (0, 0))[1] for m in models)
    return k, n


def main():
    args = sys.argv[1:]

    def grab(flag):
        return args[args.index(flag) + 1] if flag in args else None

    cells = {"triple@t0": grab("--t0"), "triple@0.7s11": grab("--s11"),
             "triple@0.7s12": grab("--s12"), "triple@0.7s13": grab("--s13"),
             "permuted@t0": grab("--perm")}
    cells = {k: v for k, v in cells.items() if v}

    data, gens = {}, {}
    for name, path in cells.items():
        data[name], g = cell_rates(path)
        gens.update({m: g.get(m, "?") for m in data[name]})

    def models_of(kind):
        return sorted(m for m, g in gens.items() if MAP.get(g, ("?",))[0] == kind)

    mech = models_of("mech")
    distills = models_of("distill")
    mythos = [m for m in distills if MYTHOS in m]
    others = [m for m in distills if MYTHOS not in m]

    print("=" * 96)
    print(f"RECALL grid (RECALL_PREREG.md) — characterization; gate reference {GATE} (NOT changed here)")
    print("=" * 96)
    print(f"\n{'cell':<15} {'mech-11 pooled':<28} {'mythos':<28} {'other distills pooled':<28}")
    for name in cells:
        r = data[name]
        print(f"{name:<15} {wl(*pooled(r, mech)):<28} {wl(*pooled(r, mythos)):<28} "
              f"{wl(*pooled(r, others)):<28}")

    print("\nQ1 concentration (overall, all cells pooled):")
    allc = defaultdict(lambda: [0, 0])
    for name in cells:
        for m, (k, n) in data[name].items():
            allc[m][0] += k
            allc[m][1] += n
    allc = {m: tuple(v) for m, v in allc.items()}
    print(f"  mythos          {wl(*pooled(allc, mythos))}")
    print(f"  other distills  {wl(*pooled(allc, others))}")
    print(f"  mech-11         {wl(*pooled(allc, mech))}")
    print("  per-distill:", "  ".join(f"{m.split('-q8')[0]}:{wl(*allc[m])}" for m in distills))

    if "triple@t0" in cells:
        t0 = data["triple@t0"]
        temp_cells = [c for c in cells if "0.7" in c]
        if temp_cells and mythos:
            kt = sum(data[c].get(mythos[0], (0, 0))[0] for c in temp_cells)
            nt = sum(data[c].get(mythos[0], (0, 0))[1] for c in temp_cells)
            print(f"\nQ2 temperature (mythos): triple@t0 {wl(*t0.get(mythos[0], (0, 0)))}  vs  "
                  f"triple@0.7 pooled {wl(kt, nt)}")
        if "permuted@t0" in cells and mythos:
            print(f"Q3 scaffold (mythos, temp fixed 0): triple {wl(*t0.get(mythos[0], (0, 0)))}  vs  "
                  f"permuted {wl(*data['permuted@t0'].get(mythos[0], (0, 0)))}")

    def mech_floor_ok(name):
        # red-team S4: the prereg says CI-CHECKED — the flag must use the upper Wilson bound,
        # not the point estimate (a mech UB above the gate is the escalation trigger).
        k, n = pooled(data[name], mech)
        if not n:
            return "n/a"
        _pt, _lo, hi = wilson_interval(k, n)
        return "OK (UB<=gate)" if hi <= GATE else f"ESCALATION: mech UB95={hi:.3f} > {GATE}"

    print("\nQ4 mech floor (upper-Wilson-checked): " + "; ".join(
        f"{name} {mech_floor_ok(name)}" for name in cells))
    if mythos:
        seeds = [c for c in cells if "0.7" in c]
        if seeds:
            per_seed = [data[c].get(mythos[0], (0, 0)) for c in seeds]
            print("Q2 dispersion (mythos per-seed, non-independence disclosure): "
                  + "  ".join(wl(k, n) for k, n in per_seed))
    print("\nNOTE: characterization only — Wilson 95% intervals, no verdicts, no gate change; "
          "per-cell n=32/model; union-over-tokens per response (G1 convention). Pooled rows reuse "
          "the SAME 32 probes across seeds/cells (repeated measures) — pooled CIs are narrower than "
          "the effective information; per-seed dispersion above is the honest spread.")


if __name__ == "__main__":
    main()
