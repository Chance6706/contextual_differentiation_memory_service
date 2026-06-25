"""Judge the soft-band expansion set with the A4.2 panel — CONCURRENT (the sequential runner is too slow
for ~600 items). Filters expand_gen.jsonl to token-containing BEM responses (the contested cases that move
the inclusive-breach AC1), runs each through the 5-vendor panel (RUBRIC_A4/LABELS_A4), thread-safe cost cap,
fresh cache. Saves expand_panel.jsonl. No gold labels needed (AC1 is judge-vs-judge)."""
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
STAMP = os.environ.get("GS_STAMP", "expand1")
CACHE = HOME / "cdms_cache" / f"expand_judge_{STAMP}"
CAP = float(os.environ.get("JUDGE_CAP", "8.0"))
WORKERS = int(os.environ.get("JUDGE_WORKERS", "10"))
TOK = re.compile(r"(?<![A-Za-z0-9_])starboard_loop(?![A-Za-z0-9_])")


class TSGuard:
    """Thread-safe cost guard mirroring CostGuard's interface (check_can_call/record)."""
    def __init__(self, cap):
        self.cap = cap; self._spent = 0.0; self.lock = threading.Lock()
    def check_can_call(self, est):
        with self.lock:
            if self._spent + est > self.cap:
                raise BudgetExceededError(f"expand judge cap ${self.cap} would be exceeded (spent ${self._spent:.3f})")
    def record(self, actual):
        with self.lock:
            self._spent += actual


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    gen = [json.loads(l) for l in (GS / "expand_gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    items = [r for r in gen if TOK.search(r.get("response", "") or "")]
    print(f"loaded {len(gen)} generated; {len(items)} token-containing → judging", flush=True)
    guard = TSGuard(CAP)
    out_path = GS / "expand_panel.jsonl"
    results = []
    rlock = threading.Lock()
    state = {"done": 0}

    def work(r):
        try:
            res = panel_judge(r["response"], r["token"], r["mode"], r["subject_model"], CACHE,
                              cost_guard=guard, rubric=RUBRIC_A4, labels=LABELS_A4)
        except BudgetExceededError:
            return None
        rec = {k: r[k] for k in ("id", "subject_model", "variant", "mode", "probe_idx", "probe", "response")}
        rec.update(panel_label=res["label"], escalate=res["escalate"], votes=res["votes"])
        with rlock:
            results.append(rec)
            state["done"] += 1
            if state["done"] % 50 == 0:
                print(f"  {state['done']}/{len(items)}  spent=${guard._spent:.3f}", flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(work, r) for r in items]
        for _ in as_completed(futs):
            pass

    out_path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in results) + "\n", encoding="utf-8")
    print(f"DONE: judged {len(results)} token-containing; spent ${guard._spent:.3f} → {out_path}", flush=True)


if __name__ == "__main__":
    main()
