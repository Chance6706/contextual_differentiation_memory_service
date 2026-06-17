"""Cross-repo individuation analysis over a (multi-project) CDMS store.

Answers the question: when CDMS is fed a user's REAL history across several
projects, do the per-project psyches come out measurably DISTINCT? Groups the
consolidated PersonaTree by project (gist.subject == project basename) and
reports, per project: episodic volume + salience share (budget-domination check),
the top gist traits, scars, and the pairwise differentiation between projects
(gist-content cosine + trait Jaccard).

Run:  CDMS_HOME=<seeded store> python tools/analyze_psyches.py
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np  # noqa: E402

from cdms.config import load_config              # noqa: E402
from cdms.embeddings import cosine, get_embedder  # noqa: E402
from cdms.salience import accessibility, age_days  # noqa: E402
from cdms.store import MemoryService              # noqa: E402


def bar(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def main() -> int:
    cfg = load_config()
    svc = MemoryService(cfg)
    embedder = get_embedder(cfg)

    eps = svc.db.all_episodic()
    gists = svc.db.all_gist()
    scars = svc.db.all_scars()

    bar("GLOBAL")
    print("stats:", svc.db.stats())
    if eps:
        ages = [age_days(e.timestamp) for e in eps]
        print(f"episodic age span (days): {min(ages):.0f}..{max(ages):.0f}  mean={sum(ages)/len(ages):.0f}")

    # ---- per-project rollups ----------------------------------------------
    ep_by = defaultdict(list)
    for e in eps:
        ep_by[e.project or "?"].append(e)
    gist_by = defaultdict(list)
    for g in gists:
        gist_by[g.subject].append(g)
    scar_by = defaultdict(list)
    for s in scars:
        scar_by[s.project or "?"].append(s)

    total_sal = sum(e.base_salience for e in eps) or 1.0

    bar("PER-PROJECT PSYCHE")
    for proj in sorted(ep_by, key=lambda p: -len(ep_by[p])):
        es = ep_by[proj]
        sal = sum(e.base_salience for e in es)
        # gist subject is the project basename; match by suffix
        base = proj.replace("\\", "/").rstrip("/").split("/")[-1]
        gs = sorted(gist_by.get(base, []), key=lambda g: -g.support_count)
        scs = scar_by.get(proj, [])
        print(f"\n### {proj}")
        print(f"    episodic={len(es)}  salience_share={100*sal/total_sal:4.1f}%  gists={len(gs)}  scars={len(scs)}")
        for g in gs[:7]:
            print(f"      • {g.render()}   (support {g.support_count}, seen {g.frequency}×)")
        for s in scs[:3]:
            print(f"      ⚠ {s.crisis_trigger[:80]}")

    # ---- differentiation between project psyches ---------------------------
    psyches = {base: gl for base, gl in gist_by.items() if len(gl) >= 2}
    names = sorted(psyches, key=lambda b: -len(psyches[b]))
    if len(names) >= 2:
        bar("DIFFERENTIATION BETWEEN REAL PROJECT PSYCHES")
        vecs = {b: embedder.embed_one(" ; ".join(g.render() for g in psyches[b])) for b in names}
        rel_obj = {b: {(g.relation, g.object) for g in psyches[b]} for b in names}

        def jac(a, b):
            a, b = set(a), set(b)
            return len(a & b) / len(a | b) if (a or b) else 0.0

        short = [n[:14] for n in names]
        print("gist-content cosine (lower off-diagonal = more individuated):")
        print(f"{'':16}" + "".join(f"{s:>16}" for s in short))
        off = []
        for a in names:
            row = []
            for b in names:
                c = cosine(vecs[a], vecs[b]); row.append(c)
                if a != b:
                    off.append(c)
            print(f"{a[:14]:16}" + "".join(f"{c:16.3f}" for c in row))
        print(f"  mean cross-project gist-content similarity = {sum(off)/len(off):.3f}")

        print("\ntrait overlap (Jaccard of (relation,object) pairs; 0 = totally distinct selves):")
        print(f"{'':16}" + "".join(f"{s:>16}" for s in short))
        for a in names:
            print(f"{a[:14]:16}" + "".join(f"{jac(rel_obj[a], rel_obj[b]):16.3f}" for b in names))

    # ---- retrieval sanity: does a query land in the right project? ---------
    bar("RETRIEVAL SANITY (real cross-project queries)")
    for q in ["unity hex grid shader compile error", "ren'py narrative story script",
              "memory consolidation decay individuation", "git commit pull request merge"]:
        hits = svc.retrieve(q, top_k=2)
        print(f"\nQ: {q}")
        for h in hits:
            print(f"  [{h.tier}] {h.score:.3f} :: {h.text[:90].replace(chr(10),' ')}")
    svc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
