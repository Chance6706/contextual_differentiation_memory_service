"""Re-judge the v5d-snipe cached responses through the VALIDATED A′ panel (de-asterisks the dead substring
scorers, which over-counted ~2× by firing on any token mention). Reads the reconstructed pool (`pool.jsonl`,
1350 responses across gemma4:31b/qwen2.5:72b/Claude × v1/v5b/v5d × BEM/recall), judges the token-containing
ones with the A4.2 panel (concurrent), and counts the rest as ABSENT (no standalone token ⇒ definitionally
non-breach). All snipe subjects are ≥31b ⇒ inside the instrument's validated regime (no small-model INVALID
gate needed). Saves snipe_rejudge_panel.jsonl (token-containing votes) + snipe_rejudge_absent.jsonl (the
ABSENT remainder, recorded so per-cell denominators are exact)."""
from __future__ import annotations

import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
from ownership_judge import LABELS_A4, RUBRIC_A4, panel_judge  # noqa: E402
from openrouter_cost_guard import BudgetExceededError  # noqa: E402

GS = REPO / "docs" / "validation" / "runtime_instrument" / "gold_set"
HOME = Path(os.path.expanduser("~"))
STAMP = os.environ.get("GS_STAMP", "snipe_rejudge")
CACHE = HOME / "cdms_cache" / f"snipe_rejudge_{STAMP}"
CAP = float(os.environ.get("JUDGE_CAP", "10.0"))
WORKERS = int(os.environ.get("JUDGE_WORKERS", "12"))
TOK = re.compile(r"(?<![A-Za-z0-9_])starboard_loop(?![A-Za-z0-9_])")


class TSGuard:
    def __init__(self, cap):
        self.cap = cap; self._spent = 0.0; self.lock = threading.Lock()
    def check_can_call(self, est):
        with self.lock:
            if self._spent + est > self.cap:
                raise BudgetExceededError(f"snipe re-judge cap ${self.cap} exceeded (spent ${self._spent:.3f})")
    def record(self, actual):
        with self.lock:
            self._spent += actual


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    pool = [json.loads(l) for l in (GS / "pool.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    tokc = [r for r in pool if TOK.search(r.get("response", "") or "")]
    absent = [r for r in pool if not TOK.search(r.get("response", "") or "")]
    print(f"pool {len(pool)}: token-containing {len(tokc)} (judge), ABSENT remainder {len(absent)}", flush=True)

    # record the ABSENT remainder (exact denominators) — no API
    keep = ("id", "subject_model", "generation", "variant", "mode", "probe_idx", "probe", "response")
    (GS / "snipe_rejudge_absent.jsonl").write_text(
        "\n".join(json.dumps({**{k: r.get(k) for k in keep}, "panel_label": "ABSENT",
                              "escalate": False, "votes": {}, "mechanical_absent": True}, ensure_ascii=False)
                  for r in absent) + "\n", encoding="utf-8")

    guard = TSGuard(CAP)
    results = []
    rlock = threading.Lock()
    state = {"done": 0}

    def work(r):
        try:
            res = panel_judge(r["response"], r["token"], r["mode"], r["subject_model"], CACHE,
                              cost_guard=guard, rubric=RUBRIC_A4, labels=LABELS_A4)
        except BudgetExceededError:
            return None
        rec = {**{k: r.get(k) for k in keep},
               "panel_label": res["label"], "escalate": res["escalate"], "votes": res["votes"]}
        with rlock:
            results.append(rec)
            state["done"] += 1
            if state["done"] % 50 == 0:
                print(f"  {state['done']}/{len(tokc)}  spent=${guard._spent:.3f}", flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(work, r) for r in tokc]
        for _ in as_completed(futs):
            pass

    (GS / "snipe_rejudge_panel.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in results) + "\n", encoding="utf-8")
    print(f"DONE: judged {len(results)} token-containing; spent ${guard._spent:.3f}", flush=True)


if __name__ == "__main__":
    main()
