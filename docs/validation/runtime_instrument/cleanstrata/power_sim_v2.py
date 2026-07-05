"""Power sim v2 — joint decision rule after the pressure-test MUST_FIX:
H1 CONFIRMED iff breach|surface (boot p<.05 AND pt>=SESOI 0.10) AND breach_ALL (boot p<.05).
Also reports breach_ALL-alone power (the pre-committed gate-2-failure branch).

Resamples WHOLE facet records (total n, surfacing rate, cond-breach rate) so the surfacing x adoption
correlation is preserved. Facet records from identity_power_JUDGE.jsonl, mech arm, classified under
the power-only SP/ID/PROC rule (cleanstrata_power_sim.SP/ID/PROC).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "tools"))
from power_sim_v1 import SP, ID, PROC  # noqa: E402
from gen_sweep_aggregate import facet_framing_map, breach_corrected, TOK, MAP  # noqa: E402
from gen_sweep_facet_cluster import _text2facet  # noqa: E402

JUDGE = REPO / "docs/validation/runtime_instrument/gen_sweep/identity_power_JUDGE.jsonl"
t2f = _text2facet()
fmap = facet_framing_map()

stats = {}  # facet -> [total, n_tok, n_breach]
for ln in open(JUDGE, encoding="utf-8"):
    ln = ln.strip()
    if not ln:
        continue
    r = json.loads(ln)
    if r.get("mode") != "BEM":
        continue
    if MAP.get(r.get("generation", "?"), ("?",))[0] != "mech":
        continue
    f = t2f.get((r.get("probe") or "").strip())
    if f is None:
        continue
    s = stats.setdefault(f, [0, 0, 0])
    s[0] += 1
    if TOK.search(r.get("response") or ""):
        s[1] += 1
        if breach_corrected(r):
            s[2] += 1

# single-probed facets only (curated are double-probed -> unrepresentative totals)
DOUBLE = {"generic-style", "self-bio-pitch", "values-nonneg", "strengths", "weaknesses", "pet-peeves",
          "process", "naming-structure", "metaphor", "proud-project", "mentorship-legacy",
          "self-bio", "debugging", "documentation", "code-review", "first-principles",
          "evolution", "energizes-flow"}
recs = {"SP": [], "ID": [], "PROC": []}
for f, (tot, ntok, nbr) in stats.items():
    cls = "SP" if f in SP else "ID" if f in ID else "PROC" if f in PROC else None
    if cls is None or ntok < 2:
        continue
    scale = 0.5 if f in DOUBLE else 1.0  # normalize double-probed totals to single-probed scale
    recs[cls].append((max(4, round(tot * scale)), ntok / tot, nbr / ntok))

for c in recs:
    a = np.array(recs[c])
    print(f"{c:5} facet-records={len(a):3}  total(med)={np.median(a[:,0]):.0f}  "
          f"surf mean={a[:,1].mean():.2f}  cond mean={a[:,2].mean():.2f}  "
          f"uncond mean={(a[:,1]*a[:,2]).mean():.3f}")

rng = np.random.default_rng(1)
SESOI = 0.10


def boot_p(oa, ob, B=1000):
    ia = rng.integers(0, len(oa), (B, len(oa)))
    ib = rng.integers(0, len(ob), (B, len(ob)))
    d = oa[ia].mean(axis=1) - ob[ib].mean(axis=1)
    return (d <= 0).mean()


def joint_power(cls_a, cls_b, Fa, Fb, cond_gap=None, sims=600):
    ra, rb = np.array(recs[cls_a]), np.array(recs[cls_b])
    if cond_gap is not None:  # shift a's cond rates so the cond class-mean gap == cond_gap
        shift = (ra[:, 2].mean() - rb[:, 2].mean()) - cond_gap
        ra = ra.copy()
        ra[:, 2] = np.clip(ra[:, 2] - shift, 0, 1)
    hits_joint = hits_all = hits_cond = 0
    for _ in range(sims):
        fa = ra[rng.integers(0, len(ra), Fa)]
        fb = rb[rng.integers(0, len(rb), Fb)]
        ka = rng.binomial(fa[:, 0].astype(int), fa[:, 1])
        kb = rng.binomial(fb[:, 0].astype(int), fb[:, 1])
        ba = rng.binomial(ka, fa[:, 2])
        bb = rng.binomial(kb, fb[:, 2])
        # unconditional (all facets)
        ua = ba / fa[:, 0]
        ub = bb / fb[:, 0]
        p_all = boot_p(ua, ub)
        # conditional (min_surf 2)
        ma, mb = ka >= 2, kb >= 2
        if ma.sum() >= 5 and mb.sum() >= 5:
            ca = ba[ma] / ka[ma]
            cb = bb[mb] / kb[mb]
            p_cond = boot_p(ca, cb)
            pt = ca.mean() - cb.mean()
            cond_ok = p_cond < 0.05 and pt >= SESOI
        else:
            cond_ok = False
        all_ok = p_all < 0.05
        hits_all += all_ok
        hits_cond += cond_ok
        hits_joint += (cond_ok and all_ok)
    return hits_joint / sims, hits_cond / sims, hits_all / sims


print("\n=== JOINT decision-rule power (sims=600, boot=1000) — admitted counts SP16/ID20/PROC29 ===")
for lbl, a, b, Fa, Fb, gap in (
        ("H1 SP-PROC empirical", "SP", "PROC", 16, 29, None),
        ("H1 SP-PROC @cond-gap 0.13", "SP", "PROC", 16, 29, 0.13),
        ("H2 SP-ID empirical", "SP", "ID", 16, 20, None),
        ("H2 SP-ID @cond-gap 0.13", "SP", "ID", 16, 20, 0.13)):
    j, c, al = joint_power(a, b, Fa, Fb, gap)
    print(f"  {lbl:28}: joint={j:.2f}  cond-alone={c:.2f}  breach_ALL-alone={al:.2f}")
