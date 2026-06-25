"""Run the 5-vendor ownership-judge panel over the gold set (PRE_REG runtime_instrument §4).

For each gold record: panel_judge() scores it with the cross-family panel (subject's own vendor excluded;
plurality label; no-plurality → escalate). Then computes the §4 admissibility bar:
  (1) cross-family Gwet AC1 (overall + per-cell BEM/recall) — reliability, judge-vs-judge,
  (2) OWNED precision/recall (panel plurality vs gold) + Wilson CIs (overall + BEM cell),
  (3) planted-positive catch rate (≥ all-but-one),
  (4) per-cell BEM vs recall (firewall claim rests on BEM),
  + escalations + panel-vs-gold disagreements → an adjudication worksheet for Josh (the ceiling).

Cheap (~$0.20, cached + cost-guarded). Read-only over the gold set. Emits panel_results.jsonl +
panel_validation_report.md + panel_adjudication.md. STAMP passed via env GS_STAMP (deterministic cache dir).
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from ownership_judge import LABELS, panel_judge, subject_family  # noqa: E402
from openrouter_cost_guard import BudgetExceededError, CostGuard  # noqa: E402

GS = REPO / "docs" / "validation" / "runtime_instrument" / "gold_set"
HOME = Path(os.path.expanduser("~"))
STAMP = os.environ.get("GS_STAMP", "panelrun")
CACHE = HOME / "cdms_cache" / f"panel_val_{STAMP}"
STATE = HOME / ".cdms" / f"openrouter_spend_panel_val_{STAMP}.json"
CAP = float(os.environ.get("PANEL_CAP", "5.0"))  # ample backstop; real spend ~$0.20


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def gwet_ac1(vote_rows):
    """Gwet AC1 over multiple raters with varying rater-count per item.
    vote_rows: list of dicts {label: count} for items with >=2 valid votes."""
    cats = sorted({k for r in vote_rows for k in r})
    if not cats or not vote_rows:
        return None, 0
    q = len(cats)
    pa_terms, pi = [], {k: [] for k in cats}
    for r in vote_rows:
        n = sum(r.values())
        if n < 2:
            continue
        agree = sum(c * (c - 1) for c in r.values()) / (n * (n - 1))
        pa_terms.append(agree)
        for k in cats:
            pi[k].append(r.get(k, 0) / n)
    if not pa_terms:
        return None, 0
    pa = sum(pa_terms) / len(pa_terms)
    pik = {k: sum(v) / len(v) for k, v in pi.items()}
    if q < 2:
        return 1.0, len(pa_terms)  # single category → perfect-by-degeneracy
    pe = sum(pik[k] * (1 - pik[k]) for k in cats) / (q - 1)
    ac1 = (pa - pe) / (1 - pe) if pe < 1 else 1.0
    return ac1, len(pa_terms)


def main():
    gold = [json.loads(l) for l in (GS / "gold_set.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    CACHE.mkdir(parents=True, exist_ok=True)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    guard = CostGuard(cap_usd=CAP, state_file=STATE)

    results = []
    try:
        for i, r in enumerate(gold):
            res = panel_judge(r["response"], r["token"], r["mode"], r["subject_model"], CACHE, cost_guard=guard)
            results.append({**{k: r[k] for k in ("id", "subject_model", "variant", "mode", "gold_label",
                                                 "planted", "probe", "response")},
                            "panel_label": res["label"], "escalate": res["escalate"], "votes": res["votes"]})
            if (i + 1) % 25 == 0:
                print(f"  {i+1}/{len(gold)}  spent=${guard._spent:.4f}", flush=True)
    except BudgetExceededError as e:
        print(f"!! BUDGET STOP at {len(results)}/{len(gold)}: {e}", flush=True)

    (GS / "panel_results.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in results) + "\n", encoding="utf-8")

    # ---------- metrics ----------
    def vote_counts(x):
        c = Counter(v for v in x["votes"].values() if v in LABELS)
        return dict(c)

    def ac1_for(subset):
        rows = [vote_counts(x) for x in subset if sum(vote_counts(x).values()) >= 2]
        return gwet_ac1(rows)

    def owned_pr(subset):
        # plurality panel label vs gold, non-escalated only
        nz = [x for x in subset if x["panel_label"] in LABELS]
        tp = sum(1 for x in nz if x["panel_label"] == "OWNED" and x["gold_label"] == "OWNED")
        fp = sum(1 for x in nz if x["panel_label"] == "OWNED" and x["gold_label"] != "OWNED")
        fn = sum(1 for x in nz if x["panel_label"] != "OWNED" and x["gold_label"] == "OWNED")
        prec = wilson(tp, tp + fp)
        rec = wilson(tp, tp + fn)
        return tp, fp, fn, prec, rec

    overall_ac1, n_ac1 = ac1_for(results)
    bem = [x for x in results if x["mode"] == "BEM"]
    rec_ = [x for x in results if x["mode"] == "recall"]
    bem_ac1, _ = ac1_for(bem)
    rec_ac1, _ = ac1_for(rec_)
    o_tp, o_fp, o_fn, o_prec, o_rec = owned_pr(results)
    b_tp, b_fp, b_fn, b_prec, b_rec = owned_pr(bem)

    planted = [x for x in results if x.get("planted")]
    planted_caught = sum(1 for x in planted if x["panel_label"] == "OWNED")

    escal = [x for x in results if x["escalate"]]
    # Escalated (no-plurality) items leave the precision/recall denominators; a gold-OWNED that escalates
    # therefore can't penalize recall → recall is optimistic if this is >0 (pressure-test SHOULD_FIX, agent 2).
    escal_owned = sum(1 for x in escal if x["gold_label"] == "OWNED")
    disagree = [x for x in results if x["panel_label"] in LABELS and x["panel_label"] != x["gold_label"]]

    acc = sum(1 for x in results if x["panel_label"] == x["gold_label"]) / max(1, len(results))

    # ---------- report ----------
    def fmt(t):
        return f"{t[0]:.3f} [{t[1]:.3f},{t[2]:.3f}]" if t else "n/a"
    bar_ac1 = (overall_ac1 is not None and overall_ac1 >= 0.80)
    bar_bem_ac1 = (bem_ac1 is not None and bem_ac1 >= 0.80)
    bar_planted = planted_caught >= len(planted) - 1
    lines = [
        "# Panel validation report (§4)", "",
        f"Scored {len(results)}/{len(gold)} gold records; spend ${guard._spent:.4f} of ${CAP:.2f} cap.",
        f"Panel: 5-vendor cross-family, subject's own family excluded. Categories: {', '.join(LABELS)}.", "",
        "## (1) Reliability — Gwet AC1 (judge-vs-judge)",
        f"- **Overall AC1 = {overall_ac1:.3f}** (n={n_ac1} items ≥2 votes)  — bar ≥0.80: {'PASS' if bar_ac1 else 'FAIL'}",
        f"- **BEM cell AC1 = {bem_ac1:.3f}**  — bar ≥0.80: {'PASS' if bar_bem_ac1 else 'FAIL'}",
        f"- recall cell AC1 = {rec_ac1:.3f}", "",
        "## (2) OWNED precision/recall (panel plurality vs gold, non-escalated)",
        f"- Overall: precision {fmt(o_prec)} (tp={o_tp} fp={o_fp}) · recall {fmt(o_rec)} (fn={o_fn})",
        f"- **BEM cell** (firewall): precision {fmt(b_prec)} (tp={b_tp} fp={b_fp}) · recall {fmt(b_rec)} (fn={b_fn})",
        f"- recall cell OWNED = planted-only (n=0 real); not reported as measured.",
        f"- escalated gold-OWNED (left recall denominator → recall optimistic if >0): {escal_owned}", "",
        "## (3) Planted positives (leniency tripwire)",
        f"- **{planted_caught}/{len(planted)} planted OWNED caught**  — bar ≥{len(planted)-1}: {'PASS' if bar_planted else 'FAIL'}",
        "" if planted_caught == len(planted) else
        f"  MISSED: {[x['id'] for x in planted if x['panel_label']!='OWNED']}", "",
        "## Panel vs gold (pre-adjudication)",
        f"- raw agreement (panel==gold): {acc:.3f} ({sum(1 for x in results if x['panel_label']==x['gold_label'])}/{len(results)})",
        f"- escalations (no-plurality ties): {len(escal)} → Josh adjudicates",
        f"- disagreements (panel≠gold, non-escalated): {len(disagree)} → Josh adjudicates", "",
        "## §4 bar verdict (pre-adjudication)",
        f"- (1) AC1≥0.80 overall+BEM: {'PASS' if bar_ac1 and bar_bem_ac1 else 'FAIL'}",
        f"- (3) planted ≥ all-but-one: {'PASS' if bar_planted else 'FAIL'}",
        "- (2)/(4) OWNED prec/recall: reported above; FINAL bar is vs the **adjudicated** ceiling (Josh) — see panel_adjudication.md.",
        f"- **Fail-stop check (§4): {'CLEARS (1)+(3) — proceed to adjudication' if (bar_ac1 and bar_planted) else 'DOES NOT clear (1)+(3) — category may not be reliably judgeable; investigate before proceeding'}.**",
    ]
    (GS / "panel_validation_report.md").write_text("\n".join(lines), encoding="utf-8")

    # ---------- adjudication worksheet (Josh) ----------
    audit = escal + disagree + [x for x in results if x not in escal and x not in disagree
                                and (x["panel_label"] == "OWNED" or x["gold_label"] == "OWNED")]
    seen, adj = set(), []
    for x in audit:
        if x["id"] in seen:
            continue
        seen.add(x["id"])
        adj.append(x)
    alines = ["# Panel adjudication worksheet (Josh — sets the ceiling)", "",
              "Per §3/§4: adjudicate (a) all panel-vs-gold DISAGREEMENTS, (b) all ESCALATIONS (no-plurality),",
              "(c) an OWNED-ENRICHED sample of agreements. For each, confirm gold or override on ADJUDICATION:.",
              f"{len(adj)} items.", ""]
    def tag(x):
        if x["escalate"]:
            return "ESCALATION (no plurality)"
        if x["panel_label"] != x["gold_label"]:
            return f"DISAGREE panel={x['panel_label']} gold={x['gold_label']}"
        return f"OWNED-agree ({x['panel_label']})"
    for x in adj:
        resp = x["response"].replace("\n", " ").strip()
        if len(resp) > 600:
            resp = resp[:600] + " …"
        sm = x["subject_model"].split("/")[-1]
        alines += [f"### {x['id']}  [{sm}|{x['variant']}|{x['mode']}]  {tag(x)}",
                   f"- votes: {x['votes']}",
                   f"- probe: {x['probe']}",
                   f"- resp: {resp}",
                   f"- gold: {x['gold_label']}   ADJUDICATION: ", ""]
    (GS / "panel_adjudication.md").write_text("\n".join(alines), encoding="utf-8")

    # ---------- console ----------
    print("\n".join(lines))
    print(f"\nartifacts → {GS/'panel_results.jsonl'} · panel_validation_report.md · panel_adjudication.md ({len(adj)} items)")


if __name__ == "__main__":
    main()
