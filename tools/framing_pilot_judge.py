"""A′-panel judge for the framing-sub-construct PILOT. Reads the gen.jsonl produced on Sparky
(model, condition, dimension, class, variant, probe, response, surfaced), runs each token-present response
through the locked A4 panel with a **constant MODE** (so the judge is blind to condition — REAL vs DECOY are
identical except the preamble, which the judge never sees), and writes a judged jsonl for
framing_pilot_analyze.py. Non-token responses are recorded ABSENT (no API). Concurrent, cost-capped.

Usage:  python tools/framing_pilot_judge.py gen.jsonl OUT_judged.jsonl [--workers N] [--cap USD] [--stamp S]
"""
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

TOK = re.compile(r"(?<![A-Za-z0-9_])starboard_loop(?![A-Za-z0-9_])")
HOME = Path(os.path.expanduser("~"))
JUDGE_MODE = "BEM"  # CONSTANT across REAL/DECOY (pre-reg §6: judge blind to condition)


class TSGuard:
    """Thread-safe $-cap. check_can_call() is invoked POSITIONALLY by openrouter_chat
    (`cost_guard.check_can_call(estimate_cost(model))`). On breach it raises the CANONICAL
    BudgetExceededError WITH its required keyword args — a bare `BudgetExceededError(msg)` would raise
    TypeError instead, which panel_judge routes to `except Exception: votes[fam]=None`, silently
    corrupting the judged file past budget (rule-12 "shadowed BudgetExceededError" class). Once tripped,
    `stopped` latches so every in-flight panel short-circuits to a clean hard stop (no partial-vote writes)."""
    def __init__(self, cap):
        self.cap = cap; self._spent = 0.0; self.lock = threading.Lock(); self.stopped = False
    def check_can_call(self, est):
        with self.lock:
            if self.stopped or self._spent + est > self.cap:
                self.stopped = True
                raise BudgetExceededError(
                    f"pilot judge cap ${self.cap} exceeded (spent ${self._spent:.3f} + est ${est:.4f})",
                    spent=self._spent, estimated_cost=est, projected=self._spent + est, cap_usd=self.cap)
    def record(self, actual):
        with self.lock:
            self._spent += actual


def main():
    a = sys.argv[1:]
    gen_path, out_path = a[0], a[1]
    workers = int(a[a.index("--workers") + 1]) if "--workers" in a else 10
    cap = float(a[a.index("--cap") + 1]) if "--cap" in a else 6.0
    stamp = a[a.index("--stamp") + 1] if "--stamp" in a else "framing_pilot"
    cache = HOME / "cdms_cache" / f"framing_pilot_judge_{stamp}"
    cache.mkdir(parents=True, exist_ok=True)

    recs = [json.loads(ln) for ln in Path(gen_path).read_text(encoding="utf-8").splitlines() if ln.strip()]
    tokc = [r for r in recs if r.get("response") and TOK.search(r["response"])]
    absent = [r for r in recs if r not in tokc]
    print(f"loaded {len(recs)}; token-present {len(tokc)} (to judge); ABSENT {len(absent)}", flush=True)

    guard = TSGuard(cap)
    out, rlock, st = [], threading.Lock(), {"done": 0}

    def work(r):
        if guard.stopped:                         # cap already tripped → don't start a new panel (hard stop)
            return None
        try:
            res = panel_judge(r["response"], "starboard_loop", JUDGE_MODE, r["model"], cache,
                              cost_guard=guard, rubric=RUBRIC_A4, labels=LABELS_A4)
        except BudgetExceededError:
            return None                           # dropped ENTIRELY (never written w/ partial votes)
        rec = {**{k: r.get(k) for k in ("model", "condition", "dimension", "class", "variant", "probe",
                                        "response")},
               "surfaced": True,                  # single-source: judged ⟺ whole-word token present (TOK)
               "panel_label": res["label"], "escalate": res["escalate"], "votes": res["votes"]}
        with rlock:
            out.append(rec); st["done"] += 1
            if st["done"] % 50 == 0:
                print(f"  judged {st['done']}/{len(tokc)}  spent=${guard._spent:.3f}", flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for _ in as_completed([ex.submit(work, r) for r in tokc]):
            pass
    for r in absent:
        out.append({**{k: r.get(k) for k in ("model", "condition", "dimension", "class", "variant", "probe",
                                             "response")},
                    "surfaced": False,            # single-source: token whole-word absent ⇒ not surfaced
                    "panel_label": "ABSENT", "escalate": False, "votes": {}})
    Path(out_path).write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + "\n", encoding="utf-8")
    print(f"DONE: {len(tokc)} judged + {len(absent)} ABSENT; spent ${guard._spent:.3f} -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
