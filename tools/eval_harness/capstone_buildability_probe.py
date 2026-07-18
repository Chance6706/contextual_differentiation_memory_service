"""Committed evidence for the FORGETTING-GEOMETRY CAPSTONE structural NEGATIVE (PT6-fixture).

Buildability crux: does the capstone's shared-input + salience-gate fixture produce a
NON-DEGENERATE channel-A signal, or is it null-by-construction / endpoint-tautology?

Design (FORGETTING_GEOMETRY_CAPSTONE.md sec.3): both poles ingest the SAME episodes over
ALL K topics every cycle; disposition = which topics the salience gate up-weights. We run
the REAL ingest->consolidate loop and inspect the surviving gist geometry per pole. Channel
A REAL = "does the per-slot CENTROID geometry separate dispositions ORTHOGONAL to the imposed
support/weight axis?"

RESULT (real fastembed, reproduced 2026-07-17; seed 1 @ 60 cycles):
  - Support DIVERGES strongly (database 29 vs 13, crypto 23 vs 13) -> real differential
    survival, BUT support == the imposed weight == channel A's own KNOWN-TAUTOLOGY axis.
  - Survival mask stays FULL (8/8), != goalset -> the erasure-arm endpoint-degeneracy is
    genuinely avoided (a real advance).
  - Per-slot centroid cos(cenA,cenC) = 0.947-0.992 (min 0.818 at gate_floor=0) for
    shared-survival topics -> centroids near-IDENTICAL across poles -> NO content/lexeme leak
    in channel A's representation (the centroid-not-search_text choice works).
  => The only non-weight degree of freedom is a NOISE-GRADE centroid wobble that does not
     track the support gap. Channel A residualizes away support (the only real signal) and is
     left with noise -> NULL BY CONSTRUCTION, and structurally blind to on-pattern structure.
  CAVEAT (S1): differential survival FLIPS the derived relation token across poles
     (auth frequently_works_on vs handles_well; database handles_well vs frequently_works_on)
     because the surviving-subset valence mean differs. `relation` is a token in
     Gist.search_text() -> any channel/representation touching search_text/relation reacquires
     the v2 valence-lexeme tautology. Channel A dodges it (centroid), but this must be a
     hard-tested invariant, not prose.

CONCLUSION: at the state level a disposition can express only as (a) how much survives
(support = imposed weight = tautology) or (b) which content survives (= lexeme = v2 tautology);
the residual is noise. There is no content-orthogonal, non-weight channel -> the state is
f(imposed salience) (+) noise, with no fourth term. Individuation-as-emergence is NOT a state
property; it is behavioral. The state-arm is DEMOTED to this instrumented negative; the
behavioral functional TOST (task #10) is the terminal court. See FORGETTING_GEOMETRY_CAPSTONE.md.

Run: python tools/eval_harness/capstone_buildability_probe.py [seed] [cycles]   (~18s/cond)
"""
from __future__ import annotations
import os, sys, time
os.environ["CDMS_EVAL_MODE"] = "1"
os.environ["CDMS_EMBED_BACKEND"] = "fastembed"
import tempfile
from pathlib import Path
from datetime import timedelta
import numpy as np

REPO = Path(__file__).resolve().parents[2]
# src FIRST (sibling-clone editable-install shadowing; verified inert for this probe 2026-07-17 —
# identical numbers both sources — but pinned + asserted so provenance is never ambient again).
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent
from tools.eval_harness.differentiation_experiment import (
    _shared_history, _goal_hint, _canonical_entity, _DISPOSITIONS, _ENTITIES,
    _EPOCH, _DAYS_PER_CYCLE, _PROJECT, _cfg_for)
from tools.eval_harness.provenance import assert_worktree_cdms

assert_worktree_cdms()


def run_pole(dispo, home, seed, emb, cycles, gate_floor):
    """Real ingest->consolidate under (disposition, gate_floor) on SHARED history."""
    cfg = _cfg_for(home, "disposition-salience", seed, gate_floor)
    svc = MemoryService(cfg, embedder=emb)
    hist = _shared_history(seed, cycles)
    for c, batch in enumerate(hist[:cycles], start=1):
        now = _EPOCH + timedelta(days=(c - 1) * _DAYS_PER_CYCLE)
        for i, ev in enumerate(batch):
            ts = (now + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            svc.ingest(TurnEvent(
                trigger_prompt=f"work on the {ev['entity']} {ev['sub']}",
                action_taken=f"{ev['verb']} the {ev['entity']} {ev['sub']}",
                outcome_feedback=("clean result" if ev["success"] else "broke, needed a fix"),
                tool_name="Edit", success=ev["success"], valence_hint=ev["affect"],
                goal_hint=_goal_hint(ev["entity"], dispo, "disposition-salience"),
                session_id=f"{dispo}-c{c}", project=_PROJECT, timestamp=ts))
        Consolidator(cfg, db=svc.db, embedder=emb).run(now=now)
    out = {}
    for g in svc.db.all_gist():
        ent = _canonical_entity(g)
        cen = svc.db.get_gist_centroid(g.id)
        if ent in out and out[ent]["support"] >= g.support_count:
            continue
        out[ent] = dict(relation=g.relation, support=g.support_count, object=g.object,
                        centroid=None if cen is None else np.asarray(cen, dtype=np.float64))
    svc.close()
    return out


def cos(a, b):
    if a is None or b is None:
        return float("nan")
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float("nan") if na == 0 or nb == 0 else float(np.dot(a, b) / (na * nb))


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    base = Path(tempfile.mkdtemp(prefix="capstone-build-"))
    emb = Embedder(Config(home=base))
    assert emb.backend == "fastembed", emb.backend
    print(f"seed={seed} cycles={cycles} | A up-weights {sorted(_DISPOSITIONS['A'])} | "
          f"C up-weights {sorted(_DISPOSITIONS['C'])}")
    for gf in (0.25, 0.0):
        t0 = time.time()
        A = run_pole("A", base / f"A-{gf}", seed, emb, cycles, gf)
        C = run_pole("C", base / f"C-{gf}", seed, emb, cycles, gf)
        print(f"\n=== gate_floor={gf}  ({time.time()-t0:.1f}s) ===")
        print(f"{'entity':14}{'supA':>6}{'supC':>6}  {'relA':18}{'relC':18}{'cos(cen)':>10}")
        both = []
        for e in sorted(set(A) | set(C)):
            a, c = A.get(e), C.get(e)
            cc = cos(a["centroid"], c["centroid"]) if (a and c) else float("nan")
            if a and c:
                both.append(cc)
            print(f"{e:14}{(a['support'] if a else 0):>6}{(c['support'] if c else 0):>6}  "
                  f"{(a['relation'] if a else '-'):18}{(c['relation'] if c else '-'):18}{cc:>10.4f}")
        maskA, maskC = set(A), set(C)
        print(f"  mask A==goalset? {maskA == set(_DISPOSITIONS['A'])}  "
              f"mask C==goalset? {maskC == set(_DISPOSITIONS['C'])}  (False = endpoint-degeneracy avoided)")
        if both:
            print(f"  shared-survival n={len(both)}  centroid cos mean={np.mean(both):.4f} "
                  f"min={np.min(both):.4f} max={np.max(both):.4f}  "
                  f"(near-1 => no content leak; the non-weight DoF is noise)")
