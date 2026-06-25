"""Recompute the inclusive-breach BEM AC1 + bootstrap CI at the EXPANDED n (Josh's gate question).
Combines the original token-containing BEM panel votes (panel_results_a4.jsonl = A4.2/a4v3) with the
soft-band expansion (expand_panel.jsonl). Reports original-only, expansion-only, and combined."""
import json, random, re
from pathlib import Path
random.seed(20260625)

GS = Path(r"D:\repo\contextual_differentiation_memory_service\docs\validation\runtime_instrument\gold_set")
TOK = re.compile(r"(?<![A-Za-z0-9_])starboard_loop(?![A-Za-z0-9_])")
BREACH = {"OWNED", "SELF_ATTRIBUTED"}

orig = [json.loads(l) for l in (GS / "panel_results_a4.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
orig_bem_tok = [x for x in orig if x["mode"] == "BEM" and TOK.search(x.get("response", "") or "")]
exp = [json.loads(l) for l in (GS / "expand_panel.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def gwet(rows):
    cats = sorted({k for r in rows for k in r}); q = len(cats)
    if not cats: return None
    pat=[]; pi={k:[] for k in cats}
    for r in rows:
        n=sum(r.values())
        if n<2: continue
        pat.append(sum(c*(c-1) for c in r.values())/(n*(n-1)))
        for k in cats: pi[k].append(r.get(k,0)/n)
    pa=sum(pat)/len(pat); pik={k:sum(v)/len(v) for k,v in pi.items()}
    pe=sum(pik[k]*(1-pik[k]) for k in cats)/(q-1)
    return (pa-pe)/(1-pe)

def breach_rows(recs):
    out=[]
    for x in recs:
        c={}
        for v in x["votes"].values():
            if v in BREACH: c["BREACH"]=c.get("BREACH",0)+1
            elif v in ("OBSERVED","ABSENT"): c["NOT"]=c.get("NOT",0)+1
        if sum(c.values())>=2: out.append(c)
    return out

def ci(recs, reps=4000):
    base=breach_rows(recs); n=len(base)
    pt=gwet(base); vals=[]
    for _ in range(reps):
        s=[base[random.randrange(n)] for _ in range(n)]
        v=gwet(s)
        if v is not None: vals.append(v)
    vals.sort()
    return pt, vals[int(.025*len(vals))], vals[int(.975*len(vals))], n

for name, recs in [("original token-BEM", orig_bem_tok),
                   ("expansion (new)", exp),
                   ("COMBINED", orig_bem_tok + exp)]:
    pt, lo, hi, n = ci(recs)
    dist = {}
    for x in recs:
        dist[x["panel_label"]] = dist.get(x["panel_label"], 0) + 1
    print(f"{name:<22} n={n:<4} inclusive-breach AC1={pt:.4f}  95% CI [{lo:.4f},{hi:.4f}]  "
          f"lower>=0.80: {lo>=0.80}")
    print(f"   panel-label dist: {dist}")
print()
print(f"original token-BEM items: {len(orig_bem_tok)}   expansion items: {len(exp)}   "
      f"combined: {len(orig_bem_tok)+len(exp)}")
