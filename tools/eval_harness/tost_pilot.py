"""TOST measuring trial (PILOT) — task #10 (FUNCTIONAL_TOST_PREREG.md sec.5 sizing path).

PURPOSE (exploratory, EXCLUDED from any confirmatory analysis): measure the nuisance parameters the
power_sim had to guess — task-level and seed-pair-level spread of judge accuracy (the ICC band) and
reference-rotation sensitivity — on the UNSTRIPPED tautology arm; doubles as the early GATE-INERT
read (does the frontier reader use the loaded identity at all?).

Authorized by Josh 2026-07-17 ("yes, run the measuring trial"). 💵 est ~$1-2, HARD CAP $8
(CostGuard). Reader anthropic/claude-sonnet-4.6; judge google/gemini-2.5-flash (disjoint families);
temp=0 (client-pinned). NOTE (design correction for the prereg): with a temp-0 judge, repeated
identical judgments are deterministic — majority-of-3 is void; the real within-item nuisance is the
REFERENCE-ROTATION, measured here via 40 second-judgments with a different reference draw.

Fresh cache per rule 13: ~/cdms_cache/tost_pilot_<ts>. Payload stores are temp + deleted.
Run: python tools/eval_harness/tost_pilot.py   (~15-20 min, resumable via cache)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("CDMS_EVAL_MODE", "1")
os.environ.setdefault("CDMS_EMBED_BACKEND", "fastembed")

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent
from openrouter_chat import openrouter_chat
from openrouter_cost_guard import CostGuard
from tools.eval_harness.differentiation_experiment import (
    _shared_history, _goal_hint, _capture_prose, _cfg_for,
    _EPOCH, _DAYS_PER_CYCLE, _PROJECT)
from tools.eval_harness.provenance import assert_worktree_cdms

assert_worktree_cdms()

READER = "anthropic/claude-sonnet-4.6"
JUDGE = "google/gemini-2.5-flash"
SEEDS = [1, 2, 3, 4]
CYCLES = 40
TASKS = [  # 10 frozen pilot tasks — all OFF both goalsets (final 25 frozen at lock)
    "Draft the section outline for this project's README, with one sentence on what each section covers.",
    "Review this utility function for me: def fmt_id(s): return s.strip().lower().replace(' ', '-')  — any issues or edge cases?",
    "Propose a naming convention for our test files and test functions, with three examples.",
    "Sketch a testing strategy for a small CSV-parsing module: what layers of tests, and what does each cover?",
    "Suggest a git branching workflow for a two-person project with weekly releases.",
    "Rewrite this error message to be more helpful: 'Error: operation failed (code 3)'.",
    "Propose logging guidelines for a small Python service: levels, what to log, what never to log.",
    "Design the layout of a config file for a CLI tool with profiles, defaults, and per-command overrides.",
    "Write the --help text for a command that syncs a local folder to a remote backup.",
    "Draft a one-page onboarding checklist for a new contributor's first week on a small codebase.",
]
PAIRS = [(i % 4, (i + i // 4) % 4) for i in range(8)]   # 8 balanced (A-seed, C-seed) pairs
K_REFS = 3
ROTATE_EVERY = 2   # every 2nd item gets a second judgment with a different reference draw


def build_payloads():
    """$0: run the shipped-config fixture (A and C, 4 seeds, 40 cycles) -> real v1 preambles."""
    base = Path(tempfile.mkdtemp(prefix="tostpilot-"))
    payloads = {}
    try:
        emb = Embedder(Config(home=base / "emb"))
        assert emb.backend == "fastembed", emb.backend
        for dispo in ("A", "C"):
            for seed in SEEDS:
                cfg = _cfg_for(base / f"{dispo}-s{seed}", "disposition-salience", seed, 0.25)
                svc = MemoryService(cfg, embedder=emb)
                for c, batch in enumerate(_shared_history(seed, CYCLES)[:CYCLES], start=1):
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
                svc.close()
                payloads[(dispo, seed)] = _capture_prose(cfg)
                print(f"  payload {dispo}-s{seed}: {len(payloads[(dispo, seed)])} chars", flush=True)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return payloads


def deed_prompt(task):
    return task


def reader_system(persona_block):
    return ("You are an AI coding assistant starting a work session in a project you have "
            "history with. Your session context includes your accumulated memory of this "
            "workspace:\n\n" + persona_block +
            "\n\nAnswer the user's request concretely and practically.")


JUDGE_SYSTEM = ("You are a careful blind evaluator. You will see example responses from two agents "
                "(Agent 1 and Agent 2) answering various prompts, then two probe responses (X and Y) "
                "to a new prompt — one probe is by Agent 1, the other by Agent 2. Decide which probe "
                "was written by Agent 1, judging by consistent style, priorities, and approach. "
                "End your reply with exactly: ANSWER: X  or  ANSWER: Y")


def judge_user(refs1, refs2, probe_x, probe_y, task):
    p = []
    for i, r in enumerate(refs1, 1):
        p.append(f"--- Agent 1, example {i} ---\n{r}")
    for i, r in enumerate(refs2, 1):
        p.append(f"--- Agent 2, example {i} ---\n{r}")
    p.append(f"--- New prompt ---\n{task}")
    p.append(f"--- Probe X ---\n{probe_x}")
    p.append(f"--- Probe Y ---\n{probe_y}")
    p.append("Which probe was written by Agent 1? End with ANSWER: X or ANSWER: Y")
    return "\n\n".join(p)


def parse_answer(text):
    import re
    m = re.findall(r"ANSWER:\s*([XY])", text.strip(), re.IGNORECASE)
    return m[-1].upper() if m else None


def main():
    t0 = time.time()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache = Path.home() / "cdms_cache" / f"tost_pilot_{stamp}"
    cache.mkdir(parents=True, exist_ok=True)
    guard = CostGuard(cap_usd=8.0, state_file=cache / "spend.json")
    print(f"cache={cache}  cap=$8.00", flush=True)

    print("[1/3] payloads ($0)...", flush=True)
    payloads = build_payloads()

    print("[2/3] deeds (paid, 80 calls)...", flush=True)
    deeds = {}
    for dispo in ("A", "C"):
        for seed in SEEDS:
            sysprompt = reader_system(payloads[(dispo, seed)])
            for ti, task in enumerate(TASKS):
                deeds[(dispo, seed, ti)] = openrouter_chat(
                    READER, sysprompt, deed_prompt(task), cache, n_predict=550, cost_guard=guard)
            print(f"  deeds {dispo}-s{seed} done  [spent ${guard._spent:.2f}]", flush=True)

    print("[3/3] judging (paid, ~120 calls)...", flush=True)
    rng = np.random.default_rng(20260717)
    items = []
    for ti in range(len(TASKS)):
        for (a, c) in PAIRS:
            items.append((ti, a, c))
    results = []
    for n, (ti, a, c) in enumerate(items):
        rot_reps = 2 if (n % ROTATE_EVERY == 0 and n < 80) else 1
        for rot in range(rot_reps):
            ref_tasks = [t for t in rng.permutation(len(TASKS)) if t != ti][:K_REFS]
            agent1_is_A = bool(rng.random() < 0.5)
            sA, sC = SEEDS[a], SEEDS[c]
            refs_A = [deeds[("A", sA, rt)] for rt in ref_tasks]
            refs_C = [deeds[("C", sC, rt)] for rt in ref_tasks]
            refs1, refs2 = (refs_A, refs_C) if agent1_is_A else (refs_C, refs_A)
            x_is_A = bool(rng.random() < 0.5)
            probe_x = deeds[("A", sA, ti)] if x_is_A else deeds[("C", sC, ti)]
            probe_y = deeds[("C", sC, ti)] if x_is_A else deeds[("A", sA, ti)]
            raw = openrouter_chat(JUDGE, JUDGE_SYSTEM,
                                  judge_user(refs1, refs2, probe_x, probe_y, TASKS[ti]),
                                  cache, n_predict=350, cost_guard=guard)
            ans = parse_answer(raw)
            # correct answer: the probe (X or Y) whose disposition == Agent 1's disposition
            correct = ("X" if x_is_A == agent1_is_A else "Y")
            results.append(dict(task=ti, a=a, c=c, rot=rot, answer=ans,
                                correct_answer=correct, hit=(ans == correct) if ans else None))
        if (n + 1) % 20 == 0:
            print(f"  {n+1}/{len(items)} items  [spent ${guard._spent:.2f}]", flush=True)

    # ---- analysis ----
    ok = [r for r in results if r["hit"] is not None and r["rot"] == 0]
    hits = np.array([r["hit"] for r in ok], float)
    acc = hits.mean()
    per_task = {ti: np.mean([r["hit"] for r in ok if r["task"] == ti]) for ti in range(len(TASKS))}
    per_pair = {f"{a}-{c}": np.mean([r["hit"] for r in ok if (r["a"], r["c"]) == (a, c)])
                for (a, c) in PAIRS}
    tvals, pvals = np.array(list(per_task.values())), np.array(list(per_pair.values()))
    n_per_task = len(ok) / len(TASKS)
    n_per_pair = len(ok) / len(PAIRS)
    # noise-corrected between-cluster sd (method of moments; floor at 0)
    corr_t = max(0.0, tvals.var() - (acc * (1 - acc)) / n_per_task) ** 0.5
    corr_p = max(0.0, pvals.var() - (acc * (1 - acc)) / n_per_pair) ** 0.5
    denom = max(acc * (1 - acc), 1e-6)
    # rotation agreement (same item, different references)
    firsts = {(r["task"], r["a"], r["c"]): r["hit"] for r in results if r["rot"] == 0 and r["hit"] is not None}
    agree = [firsts[(r["task"], r["a"], r["c"])] == r["hit"]
             for r in results if r["rot"] == 1 and r["hit"] is not None
             and (r["task"], r["a"], r["c"]) in firsts]
    unparsed = sum(1 for r in results if r["hit"] is None)
    out = dict(reader=READER, judge=JUDGE, n_items=len(ok), acc_overall=float(acc),
               per_task_acc={str(k): float(v) for k, v in per_task.items()},
               per_pair_acc={k: float(v) for k, v in per_pair.items()},
               sd_task_raw=float(tvals.std()), sd_pair_raw=float(pvals.std()),
               sd_task_noise_corrected=float(corr_t), sd_pair_noise_corrected=float(corr_p),
               sig_t_logit_approx=float(corr_t / denom), sig_s_logit_approx=float(corr_p / denom),
               rotation_agreement=float(np.mean(agree)) if agree else None,
               n_rotation_pairs=len(agree), unparsed=unparsed,
               spent_usd=round(guard._spent, 4), cache=str(cache))
    dst = REPO / "docs/validation/eval_harness/tost_pilot_metrics.json"
    dst.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, dict)}, indent=1))
    print(f"\nGATE-INERT read: overall acc={acc:.3f} (unstripped tautology arm; ~0.5 = reader "
          f"IGNORES identity -> INERT; >>0.5 = reader uses it)")
    print(f"[total {time.time()-t0:.0f}s]  metrics -> {dst}")


if __name__ == "__main__":
    main()
