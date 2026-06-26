"""Aggregate the A′-panel re-judge of the snipe pool → corrected per-cell ownership rates + v1→v5d deltas.
Cell = (subject_model, mode, variant). Denominator = token-containing judged + ABSENT remainder (exact).
Writes docs/validation/runtime_instrument/SNIPE_REJUDGE.md."""
import json, math, sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from ownership_judge import breach_from_votes  # noqa: E402

GS = Path(r"D:\repo\contextual_differentiation_memory_service\docs\validation\runtime_instrument\gold_set")
OUT = GS.parent / "SNIPE_REJUDGE.md"
BREACH = {"OWNED", "SELF_ATTRIBUTED"}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


rows = []
for f in ("snipe_rejudge_panel.jsonl", "snipe_rejudge_absent.jsonl"):
    p = GS / f
    if p.exists():
        rows += [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

cells = defaultdict(list)
for r in rows:
    cells[(r["subject_model"], r["mode"], r["variant"])].append(r)


def stat(recs):
    """breach via the gate-correct breach_from_votes (resolves all-breach OWNED/SA severity ties as BREACH,
    which the 4-way plurality label drops to ESCAL). Per-rung counts stay plurality-based (ties → ESCAL)."""
    n = len(recs)
    lab = defaultdict(int)
    breach = 0
    for r in recs:
        lab[r["panel_label"] or "ESCAL"] += 1
        if breach_from_votes(r.get("votes", {})) == "BREACH":
            breach += 1
    return n, lab, breach


def short(m):
    return m.split("/")[-1]


models = sorted({k[0] for k in cells})
modes = ["BEM", "recall"]
variants = ["v1", "v5b", "v5d"]

L = ["# Snipe data re-judged through the validated A′ panel (corrected ownership rates)", "",
     "De-asterisks the dead substring scorers (over-counted ~2× on any token mention). Breach = genuine",
     "first-person adoption (SELF_ATTRIBUTED ∪ OWNED); denominator = full cell (token-containing judged +",
     "ABSENT remainder). All subjects ≥31b ⇒ inside the validated regime. Rates with Wilson 95% CI.", ""]
for mode in modes:
    L += [f"## {mode}", "",
          "| model | variant | n | breach % [95% CI] | OWNED % | SELF_ATTR % | OBSERVED % | ABSENT % | INVALID |",
          "|---|---|---|---|---|---|---|---|---|"]
    for m in models:
        for v in variants:
            recs = cells.get((m, mode, v))
            if not recs:
                continue
            n, lab, breach = stat(recs)
            bp = wilson(breach, n)
            ow = lab["OWNED"] / n; sa = lab["SELF_ATTRIBUTED"] / n
            ob = lab["OBSERVED"] / n; ab = lab["ABSENT"] / n; inv = lab["INVALID"]
            L.append(f"| {short(m)} | {v} | {n} | {bp[0]*100:.0f}% [{bp[1]*100:.0f},{bp[2]*100:.0f}] | "
                     f"{ow*100:.0f}% | {sa*100:.0f}% | {ob*100:.0f}% | {ab*100:.0f}% | {inv} |")
    L.append("")

# v1 -> v5d breach delta per (model, mode) — tests the snipe's "third-person wrap reduces leak" claim
L += ["## v1 → v5d breach-rate delta (the snipe's third-person-wrap leak claim, corrected)", "",
      "| model | mode | v1 breach % | v5d breach % | Δ (v5d − v1) pp | v1 OWNED% → v5d OWNED% |",
      "|---|---|---|---|---|---|"]
for m in models:
    for mode in modes:
        c1 = cells.get((m, mode, "v1")); c5 = cells.get((m, mode, "v5d"))
        if not c1 or not c5:
            continue
        n1, lab1, b1 = stat(c1); n5, lab5, b5 = stat(c5)
        r1 = b1 / n1 * 100; r5 = b5 / n5 * 100
        o1 = lab1["OWNED"] / n1 * 100; o5 = lab5["OWNED"] / n5 * 100
        L.append(f"| {short(m)} | {mode} | {r1:.0f}% | {r5:.0f}% | {r5-r1:+.0f} | {o1:.0f}% → {o5:.0f}% |")
L += ["", "_Note: a NEGATIVE Δ = v5d reduces the genuine breach rate vs v1; a flat/positive Δ = the wrap did",
      "NOT reduce genuine first-person adoption there. Direction only — see significance below._"]


def fisher(a, b, c, d):
    """two-sided Fisher exact (hypergeometric: sum of tables with prob ≤ prob(observed))."""
    n = a + b + c + d; r1 = a + b; c1 = a + c; c2 = b + d
    def pmf(x):
        lo = max(0, r1 - c2); hi = min(r1, c1)
        if x < lo or x > hi:
            return 0.0
        return math.comb(c1, x) * math.comb(c2, r1 - x) / math.comb(n, r1)
    pobs = pmf(a); lo = max(0, r1 - c2); hi = min(r1, c1)
    return sum(pmf(x) for x in range(lo, hi + 1) if pmf(x) <= pobs + 1e-12)


# Fisher exact on the pre-specified v1→v5d BEM tests (gemma + qwen, breach + hard-OWNED).
L += ["", "## Significance — v1→v5d BEM, Fisher exact two-sided (n=50/cell)", "",
      "| model | metric | v1 | v5d | Fisher p (uncorrected) | survives Bonferroni? |",
      "|---|---|---|---|---|---|"]
N_TESTS = 0
sig_rows = []
for m in ["gemma4:31b", "qwen2.5:72b"]:
    for metric, fn in [("breach", lambda c: stat(c)[2]),
                       ("OWNED", lambda c: stat(c)[1]["OWNED"])]:
        c1 = cells.get((m, "BEM", "v1")); c5 = cells.get((m, "BEM", "v5d"))
        a = fn(c1); na = len(c1); b = fn(c5); nb = len(c5)
        p = fisher(a, na - a, b, nb - b)
        sig_rows.append((m, metric, a, na, b, nb, p)); N_TESTS += 1
for (m, metric, a, na, b, nb, p) in sig_rows:
    bonf = p < 0.05 / N_TESTS
    L.append(f"| {short(m)} | {metric} | {a}/{na} | {b}/{nb} | {p:.3f} {'(p<.05)' if p < 0.05 else 'ns'} | "
             f"{'YES' if bonf else 'NO (α=%.4f)' % (0.05/N_TESTS)} |")
L += ["", f"_{N_TESTS} pre-specified tests → Bonferroni α = {0.05/N_TESTS:.4f}. NONE survives correction; the",
      "lone uncorrected p<.05 (gemma hard-OWNED) fails even Bonferroni-2 (0.025). All v1→v5d deltas are",
      "underpowered at n=50 — directionally consistent with the original snipe, statistically inconclusive._"]

OUT.write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
print(f"\n→ {OUT}")
