"""BLOCK J0 — cross-epoch judge-drift guard (BLOCK_PREREG §4; red-team pressure-test M1).

The block epoch's D_X pairs a FROZEN anchor (judged in the frame epoch) against FRESH arms (judged
now). The generation side is sentinel-verified; this guards the JUDGE side: arm B's HEADER-SCOPE
cell ("fillers drop AND T1 drops") is exactly what a uniformly-stricter fresh panel would
manufacture, and the P0 σ≈0 evidence was measured on a different estimand/basis (multiplicity/7f).

Protocol: re-judge the 2 sentinel mech models' ANCHOR surfacing rows (filler tokens + T1, BEM mode,
open-SP) in a FRESH judge session (fresh stamp, responses already committed — only judge spend,
~$1), recompute their pooled adoption, and assert |Δ| ≤ TOL vs the committed values. A failure
HALTS analysis: the fresh panel reads differently than the frame-epoch panel and D_X would be
confounded — re-judge the ANCHOR in full in the fresh session before analyzing (the pre-registered
remedy; ~$7).

Usage:  python tools/blockframe_j0_check.py   (reads gen_sweep/frame_filler_JUDGE.jsonl)
"""
from __future__ import annotations

import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from ownership_judge import LABELS_A4, RUBRIC_A4, panel_judge  # noqa: E402
from judge_ladder import TSGuard  # noqa: E402
from multifact_analyze import breach_from_votes  # noqa: E402
import redteam_claude_md_interference as R  # noqa: E402
import probes_sp_expansion as bank  # noqa: E402

SENTINELS = ("granite-3.0-8b-q8", "mistral-g-v0.1")
TOKENS = R.MULTIFACT_TOKENS[:1] + R.FILLER_TOKENS
TOL = 0.05
HOME = Path(os.path.expanduser("~"))


def main():
    t2f = {}
    for i in range(len(bank.PROBES)):
        for t in [bank.PROBES[i]] + bank.REPHRASINGS.get(i, []):
            t2f[t.strip()] = bank.FACET_OF[i]
    open_set = set(bank.FORMAT_OPEN)

    rows = []
    src = REPO / "docs/validation/runtime_instrument/gen_sweep/frame_filler_JUDGE.jsonl"
    for ln in open(src, encoding="utf-8"):
        r = json.loads(ln)
        if (r.get("subject_model") in SENTINELS and r.get("mode") == "BEM"
                and r.get("votes") and r.get("token") in TOKENS
                and t2f.get((r.get("probe") or "").strip()) in open_set):
            rows.append(r)
    print(f"sentinel anchor surfacing rows to re-judge: {len(rows)}")

    cache = HOME / "cdms_cache" / "multifact_judge_blockframe_j0"
    cache.mkdir(parents=True, exist_ok=True)
    guard = TSGuard(3.0)
    lock = threading.Lock()
    fresh = {}

    def work(idx_r):
        i, r = idx_r
        res = panel_judge(r["response"], r["token"], r["mode"], r["subject_model"], cache,
                          cost_guard=guard, rubric=RUBRIC_A4, labels=LABELS_A4)
        with lock:
            fresh[i] = res

    with ThreadPoolExecutor(max_workers=12) as ex:
        list(ex.map(work, enumerate(rows)))

    def pooled(get_breach):
        k = sum(1 for i, r in enumerate(rows) if get_breach(i, r))
        return k / len(rows)

    a_committed = pooled(lambda i, r: breach_from_votes(r.get("votes") or {}) == "BREACH")
    a_fresh = pooled(lambda i, r: breach_from_votes(fresh[i].get("votes") or {}) == "BREACH")
    delta = a_fresh - a_committed
    flips = sum(1 for i, r in enumerate(rows)
                if fresh[i]["label"] != r.get("panel_label"))
    print(f"committed pooled breach (2 sentinels, surfacing rows): {a_committed:.4f}")
    print(f"fresh-session pooled breach:                            {a_fresh:.4f}   "
          f"delta={delta:+.4f} (TOL ±{TOL})")
    print(f"row-level label flips: {flips}/{len(rows)} = {flips/len(rows):.3f}  "
          f"spent=${guard._spent:.2f}")
    if abs(delta) > TOL:
        print("\n!! J0 FAIL — cross-epoch judge drift exceeds tolerance. HALT: re-judge the FULL "
              "anchor in this session before analysis (pre-registered remedy); do not compute D_X "
              "against the frame-epoch anchor labels.")
        raise SystemExit(3)
    print("J0 PASS — the fresh panel reproduces the anchor's read within tolerance.")


if __name__ == "__main__":
    main()
