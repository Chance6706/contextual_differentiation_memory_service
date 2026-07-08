"""Diagnostic for Josh's question: is the 0.182x4 multiplicity streak pipeline DETERMINISM
(same responses -> same score, 4x) or rate CONSERVATION under response variance (interesting)?

Across the four committed triple-arm epochs (multifact / filler / padding / frame), mech-11, 7f
REPRO basis:
  1. recompute the multiplicity count (expect 28/154 each);
  2. response identity: fraction of (model, probe-text) BEM responses byte-identical across epochs;
  3. breach-cell identity: Jaccard of the multiplicity cell sets (facet, model, probe-text);
  4. singles contrast (the ledger says singles DID wobble 28<->26).
NOTE: the multifact epoch used the cleanstrata bank (via multifact_analyze's default adapter);
later epochs used probes_sp_expansion. Cross-epoch keys are therefore (model, probe TEXT).
Read-only; verdict-neutral (the streak is already published with the counts-rounding caveat).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

REPO = Path(r"D:\repo\contextual_differentiation_memory_service")
sys.path.insert(0, str(REPO / "tools"))
import multifact_analyze as MA  # noqa: E402
from multifact_analyze import collect, facet_multiplicity  # noqa: E402
import probes_sp_expansion as spx  # noqa: E402
import redteam_claude_md_interference as R  # noqa: E402
from gen_sweep_aggregate import MAP  # noqa: E402

G = REPO / "docs/validation/runtime_instrument/gen_sweep"
EPOCHS = {"multifact": (G / "multifact_triple_JUDGE.jsonl", None),
          "filler":    (G / "filler_triple_JUDGE.jsonl", spx),
          "padding":   (G / "padding_triple_JUDGE.jsonl", spx),
          "frame":     (G / "frame_triple_JUDGE.jsonl", spx)}
SINGLES = {"multifact": (G / "multifact_single_JUDGE.jsonl", None),
           "filler":    (G / "filler_single_JUDGE.jsonl", spx),
           "padding":   (G / "padding_single_JUDGE.jsonl", spx),
           "frame":     (G / "frame_single_JUDGE.jsonl", spx)}
REPRO = set(spx.REPRO_FACETS)
T1 = R.MULTIFACT_TOKENS[0]


def bank_of(b):
    return b if b is not None else MA._CleanStrataBank


def t2f_of(b):
    b = bank_of(b)
    t2f = {}
    for i in range(len(b.PROBES)):
        for t in [b.PROBES[i]] + b.REPHRASINGS.get(i, []):
            t2f[t.strip()] = b.FACET_OF[i]
    return t2f


def coll(path, b):
    return collect(str(path), "mech") if b is None else collect(str(path), "mech", b)


def repro_rows(path, b):
    """{(model, probe_text): (facet, response, tok_breach_dict)} for mech BEM rows on REPRO facets.
    Breach per token recomputed with the shared breach rule."""
    t2f = t2f_of(b)
    rows = defaultdict(dict)
    resp = {}
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        r = json.loads(ln)
        if r.get("mode") != "BEM":
            continue
        if MAP.get(r.get("generation", "?"), ("?",))[0] != "mech":
            continue
        pt = (r.get("probe") or "").strip()
        f = t2f.get(pt)
        if f not in REPRO:
            continue
        key = (r["subject_model"], pt)
        b_ = 1 if MA.breach_from_votes(r.get("votes") or {}) == "BREACH" else 0
        rows[key][r.get("token")] = b_
        resp[key] = (f, r.get("response") or "")
    return rows, resp


# 1+3: multiplicity counts + cell sets (keyed on probe text)
cells, resps = {}, {}
for name, (path, b) in EPOCHS.items():
    rows, resp = repro_rows(path, b)
    mult_cells = {k for k, toks in rows.items()
                  if sum(v for t, v in toks.items() if t in R.MULTIFACT_TOKENS) >= 2}
    cells[name] = {(resp[k][0],) + k for k in mult_cells}
    resps[name] = resp
    print(f"[mult] {name:<9} k/n = {len(mult_cells)}/{len(rows)} = {len(mult_cells)/len(rows):.4f}")

print("\n[mult] pairwise breach-cell Jaccard (facet, model, probe-text):")
for a, c in combinations(EPOCHS, 2):
    i, u = len(cells[a] & cells[c]), len(cells[a] | cells[c])
    print(f"  {a:<9} vs {c:<9} J={i/u:.2f} ({i}/{u})")

# 2: response byte-identity across epochs
print("\n[resp] triple-arm BEM response identity (mech, 7f, shared (model, probe-text)):")
for a, c in combinations(EPOCHS, 2):
    shared = set(resps[a]) & set(resps[c])
    same = sum(1 for k in shared if resps[a][k][1] == resps[c][k][1])
    print(f"  {a:<9} vs {c:<9} identical {same}/{len(shared)} = {same/len(shared):.3f}"
          if shared else f"  {a:<9} vs {c:<9} NO shared keys")

# 4: singles contrast — T1 breach cells
print("\n[single] T1 cells per epoch (contrast: the ledger wobbles here):")
scells, sresps = {}, {}
for name, (path, b) in SINGLES.items():
    rows, resp = repro_rows(path, b)
    t1c = {k for k, toks in rows.items() if toks.get(T1, 0)}
    scells[name] = {(resp[k][0],) + k for k in t1c}
    sresps[name] = resp
    print(f"  {name:<9} {len(t1c)}/{len(rows)} = {len(t1c)/len(rows):.4f}")
for a, c in combinations(SINGLES, 2):
    i, u = len(scells[a] & scells[c]), len(scells[a] | scells[c])
    shared = set(sresps[a]) & set(sresps[c])
    same = sum(1 for k in shared if sresps[a][k][1] == sresps[c][k][1])
    print(f"  {a:<9} vs {c:<9} cell-J={i/u:.2f} ({i}/{u})  resp-identical {same}/{len(shared)}")
