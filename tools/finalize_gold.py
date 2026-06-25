"""Finalize the gold set (PRE_REG runtime_instrument v3 §3-§4).

Merges the first-pass labels (labels_bem.json + labels_recall.json) onto the selected pool records,
appends the hand-written planted positives, and emits:
  - gold_set.jsonl             : the judge-validation input (id, subject, variant, mode, token, response,
                                 gold_label, label_provenance, owned_adjacent, confidence, planted)
  - gold_set_adjudication.md   : Josh's worksheet — OWNED-ENRICHED (every OWNED + owned_adjacent + low-conf
                                 + INVALID + planted) for adjudication, per §3 "Josh adjudicates all
                                 disagreements AND an OWNED-enriched sample of agreements".
Prints the §4 admissibility-prep stats: label distribution, min-OWNED, per-cell (BEM/recall) OWNED counts,
disagreement-with-crosswalk count, confidence + owned_adjacent tallies. Pure local, no network.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

GS = Path("docs/validation/runtime_instrument/gold_set")
LABELS = ("OWNED", "OBSERVED", "ABSENT", "INVALID")


def load_jsonl(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def short(m):
    return m.split("/")[-1]


def main():
    selected = {r["id"]: r for r in load_jsonl(GS / "selected.jsonl")}
    firstpass = {}
    for fn in ("labels_bem.json", "labels_recall.json"):
        for o in json.loads((GS / fn).read_text(encoding="utf-8")):
            firstpass[o["id"]] = o

    gold = []
    unlabeled, bad = [], []
    disagree = 0  # first-pass differs from the crosswalk's provisional expectation
    for rid, rec in selected.items():
        fp = firstpass.get(rid)
        if not fp:
            unlabeled.append(rid)
            continue
        lab = fp.get("label")
        if lab not in LABELS:
            bad.append((rid, lab))
            continue
        # crosswalk expectation: recall OWNED-prov should be OWNED; downgrade = a real correction
        prov = rec["prov_label"]
        if rec["mode"] == "recall" and prov == "OWNED" and lab != "OWNED":
            disagree += 1
        if rec["mode"] == "recall" and prov == "OBSERVED" and lab != "OBSERVED":
            disagree += 1
        g = {k: rec[k] for k in ("id", "backend", "subject_model", "generation", "variant", "mode",
                                 "probe_idx", "token", "control_token", "probe", "response",
                                 "legacy_score", "prov_label", "quartz_present", "invalid_flag")}
        g.update({
            "gold_label": lab,
            "confidence": fp.get("confidence", "med"),
            "owned_adjacent": bool(fp.get("owned_adjacent", False)),
            "quartz_only": bool(fp.get("quartz_only", False)),
            "gold_rationale": fp.get("rationale", ""),
            "label_provenance": fp.get("provenance", "first-pass-claude"),
            "planted": False,
        })
        gold.append(g)

    planted = json.loads((GS / "planted.json").read_text(encoding="utf-8"))
    for p in planted:
        p.setdefault("confidence", "high")
        p.setdefault("owned_adjacent", False)
        p.setdefault("quartz_present", False)
        p.setdefault("quartz_only", False)
        p.setdefault("invalid_flag", None)
        p.setdefault("legacy_score", "planted")
        p.setdefault("prov_label", "PLANTED_OWNED")
        p.setdefault("backend", "planted")
        gold.append(p)

    (GS / "gold_set.jsonl").write_text(
        "\n".join(json.dumps(g, ensure_ascii=False) for g in gold) + "\n", encoding="utf-8")

    # ---- Adjudication worksheet (OWNED-enriched) ----
    def needs_adjudication(g):
        return (g["gold_label"] in ("OWNED", "INVALID") or g.get("owned_adjacent")
                or g.get("confidence") == "low" or g.get("planted"))
    adj = [g for g in gold if needs_adjudication(g)]
    adj.sort(key=lambda g: (0 if g.get("planted") else 1, g["gold_label"], short(g["subject_model"]),
                            g["mode"], str(g["probe_idx"])))
    lines = ["# Gold-set adjudication worksheet (Josh)", "",
             "Per pre-reg §3, the adjudicated panel is the CEILING. Review every item below (OWNED-enriched:",
             "all OWNED + owned_adjacent + low-confidence + INVALID + planted). For each, confirm the",
             "first-pass label or override it on the `ADJUDICATION:` line (leave blank = confirm).", "",
             f"{len(adj)} items flagged for review (of {len(gold)} total gold). Labels: OWNED / OBSERVED / ABSENT / INVALID.", ""]
    for g in adj:
        tag = "PLANTED" if g.get("planted") else f"{short(g['subject_model'])}|{g['variant']}|{g['mode']}"
        resp = g["response"].replace("\n", " ").strip()
        if len(resp) > 700:
            resp = resp[:700] + " …[trunc]"
        flags = []
        if g.get("owned_adjacent"):
            flags.append("owned_adjacent")
        if g.get("confidence") == "low":
            flags.append("low-conf")
        if g.get("invalid_flag"):
            flags.append(f"inv:{g['invalid_flag']}")
        if g.get("quartz_only"):
            flags.append("quartz_only")
        lines += [
            f"### {g['id']}  [{tag}]  first-pass=**{g['gold_label']}**  {' '.join(flags)}",
            f"- probe: {g['probe']}",
            f"- resp: {resp}",
            f"- rationale: {g.get('gold_rationale','')}",
            f"- ADJUDICATION: ",
            ""]
    (GS / "gold_set_adjudication.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- Stats (§4 prep) ----
    dist = defaultdict(int)
    for g in gold:
        dist[g["gold_label"]] += 1
    owned_bem = sum(1 for g in gold if g["gold_label"] == "OWNED" and g["mode"] == "BEM")
    owned_recall = sum(1 for g in gold if g["gold_label"] == "OWNED" and g["mode"] == "recall")
    conf = defaultdict(int)
    for g in gold:
        conf[g.get("confidence", "?")] += 1
    oa = sum(1 for g in gold if g.get("owned_adjacent"))
    print(f"GOLD SET: {len(gold)} ({len(gold)-len(planted)} labeled + {len(planted)} planted) → {GS/'gold_set.jsonl'}")
    print(f"label distribution: {dict(dist)}")
    print(f"min-OWNED check (need >=15): total OWNED={dist['OWNED']}  | BEM cell OWNED={owned_bem}  recall cell OWNED={owned_recall}")
    print(f"confidence: {dict(conf)}   owned_adjacent: {oa}")
    print(f"recall crosswalk disagreements (first-pass != legacy prov): {disagree}")
    if unlabeled:
        print(f"!! UNLABELED selected ids ({len(unlabeled)}): {unlabeled[:10]}")
    if bad:
        print(f"!! BAD labels ({len(bad)}): {bad[:10]}")
    print(f"adjudication worksheet: {len(adj)} items → {GS/'gold_set_adjudication.md'}")


if __name__ == "__main__":
    main()
