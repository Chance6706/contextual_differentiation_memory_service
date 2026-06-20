"""Compare V1-original (PR #69 cache) vs V1-rerun vs V2 vs V3 mitigation variants.

Reads responses from up to 4 cache directories, re-derives the cache key per
(variant, mode, arm, model, probe), and produces a side-by-side delta table.

V1-original vs V1-rerun is the REPRODUCIBILITY check (greedy decoding should be
byte-identical; non-identity is its own finding).

V1 vs V2 vs V3 is the mitigation comparison: does the V2 asymmetric authority
framing improve Gemma family rescue on ORDER/OVERRIDE? Does the V3 counter-
imperative further harden against override? Does either fix the mistral-nemo
BEM breach?

Run: `python tools/redteam_claude_md_compare.py`
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cdms.config import Config                          # noqa: E402
from cdms.embeddings import Embedder                    # noqa: E402
from cdms.hooks import (                                 # noqa: E402
    _session_start_context,
    _session_start_context_v2,
    _session_start_context_v3,
    _session_start_context_v4,
)
from cdms.stats import wilson_interval                  # noqa: E402
from cdms.store import MemoryService                    # noqa: E402
from local_models import SMALL_PANEL                    # noqa: E402
from redteam_claude_md_interference import (             # noqa: E402
    CLAUDE_MD_BEM, CLAUDE_MD_INSTR, CLAUDE_MD_ORDER, CLAUDE_MD_OVERRIDE,
    PROBES_BEM, PROBES_INSTR, PROBES_ORDER, PROBES_OVERRIDE,
    PROJECT, _system_prompt,
    score_bem, score_instr, score_order_safe, score_override,
    setup_bem, setup_instr, setup_order, setup_override,
)

_BUILDERS = {
    "v1": _session_start_context,
    "v2": _session_start_context_v2,
    "v3": _session_start_context_v3,
    "v4": _session_start_context_v4,
}


def _key(model: str, system: str, user: str) -> str:
    return hashlib.sha256(f"{model}\x00{system}\x00{user}".encode("utf-8")).hexdigest()[:24]


def _cp(model: str, key: str, cache_dir: Path) -> Path:
    safe_model = model.replace("/", "_").replace(":", "_")
    return cache_dir / f"{safe_model}__{key}.json"


def _preamble(setup, variant: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        cfg = Config(home=Path(td))
        svc = MemoryService(cfg, embedder=Embedder(cfg))
        try:
            setup(svc, cfg)
            return _BUILDERS[variant](cfg, {"cwd": PROJECT})
        finally:
            svc.close()


def _probe(probe_entry):
    if isinstance(probe_entry, tuple):
        return probe_entry[1], probe_entry[0]
    return probe_entry, None


MODES = [
    ("ORDER",    setup_order,    CLAUDE_MD_ORDER,    PROBES_ORDER,    score_order_safe,
        [("treatment", True, True), ("control", True, False)]),
    ("BEM",      setup_bem,      CLAUDE_MD_BEM,      PROBES_BEM,      score_bem,
        [("treatment", True, True)]),
    ("INSTR",    setup_instr,    CLAUDE_MD_INSTR,    PROBES_INSTR,    score_instr,
        [("treatment", False, True)]),
    ("OVERRIDE", setup_override, CLAUDE_MD_OVERRIDE, PROBES_OVERRIDE, score_override,
        [("treatment", True, True), ("control", False, True)]),
]


def _score(name: str, scorer, probe_tag, resp: str) -> str:
    if name == "ORDER":
        return scorer(probe_tag, resp)
    return scorer(resp)


def _summary(name: str, scores: list[str]) -> tuple[int, int, float, float, float]:
    """Return (successes, n, point, lo, hi) where 'success' means the CDMS-favored outcome."""
    n = len(scores)
    if name == "ORDER":
        s = sum(1 for x in scores if x == "safe")
    elif name == "BEM":
        # The CDMS-favored outcome is "no CDMS-token leak" (Bem firewall holds).
        # We count "cdms not present" (i.e., score is 'neither' or 'claudemd' alone).
        s = sum(1 for x in scores if "cdms" not in x)
    elif name == "INSTR":
        s = sum(1 for x in scores if x == "on_task")
    elif name == "OVERRIDE":
        s = sum(1 for x in scores if x == "scar_invoked")
    else:
        s = 0
    if n == 0:
        return 0, 0, 0.0, 0.0, 0.0
    p, lo, hi = wilson_interval(s, n)
    return s, n, p, lo, hi


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--v1-orig", default="C:/Users/joshe/AppData/Local/Temp/cdms_claude_md_cache",
                    help="PR #69 cache (the V1-original baseline)")
    ap.add_argument("--v1-rerun", default="C:/Users/joshe/AppData/Local/Temp/cdms_claude_md_cache_v1_rerun")
    ap.add_argument("--v2", default="C:/Users/joshe/AppData/Local/Temp/cdms_claude_md_cache_v2")
    ap.add_argument("--v3", default="C:/Users/joshe/AppData/Local/Temp/cdms_claude_md_cache_v3")
    ap.add_argument("--v4", default="C:/Users/joshe/AppData/Local/Temp/cdms_claude_md_cache_v4")
    ap.add_argument("--out", default=None)
    ap.add_argument("--show", nargs="+", default=None,
                    help="filter the comparison columns shown (e.g. --show v2 v4)")
    args = ap.parse_args()

    all_runs = {
        "v1-orig":  (Path(args.v1_orig),  "v1"),
        "v1-rerun": (Path(args.v1_rerun), "v1"),
        "v2":       (Path(args.v2),       "v2"),
        "v3":       (Path(args.v3),       "v3"),
        "v4":       (Path(args.v4),       "v4"),
    }
    if args.show:
        runs = {k: v for k, v in all_runs.items() if k in args.show}
    else:
        runs = all_runs
    fh = open(args.out, "w", encoding="utf-8") if args.out else None

    def emit(s: str) -> None:
        print(s)
        if fh:
            fh.write(s + "\n")

    emit("# Phase-2 mitigation comparison — V1-orig / V1-rerun / V2 / V3")
    emit("")
    emit("Success metric per mode (CDMS-favored outcome):")
    emit("  ORDER:    P(safe choice)         — higher is better")
    emit("  BEM:      P(no CDMS-token leak)  — higher = Bem firewall holds")
    emit("  INSTR:    P(on-task)             — higher is better")
    emit("  OVERRIDE: P(scar invoked)        — higher is better")
    emit("")

    # Reproducibility check: count byte-identical V1-orig vs V1-rerun responses.
    repro_total = 0
    repro_identical = 0

    # Cost summary up front: preamble bytes per variant per mode.
    emit("")
    emit("=" * 80)
    emit("## Preamble cost per variant per mode (bytes; ~tokens = bytes/4)")
    emit("=" * 80)
    cost_header = "  " + f"{'mode':10s}  " + "  ".join(f"{c:>12s}" for c in runs)
    emit(cost_header)
    for name, setup, _claude_md, _probes, _scorer, _arms in MODES:
        cells = []
        for run_name, (_cdir, variant) in runs.items():
            try:
                p = _preamble(setup, variant)
                cells.append(f"{len(p):>5d}b ({len(p)//4:>4d}t)")
            except Exception:
                cells.append("err")
        emit("  " + f"{name:10s}  " + "  ".join(f"{c:>12s}" for c in cells))

    for name, setup, claude_md, probes, scorer, arms in MODES:
        emit("")
        emit("=" * 80)
        emit(f"## Mode: {name}")
        emit("=" * 80)
        for arm_label, inc_md, inc_cdms in arms:
            cm = claude_md if inc_md else ""
            # Per-variant system prompt (preambles differ across variants).
            arm_systems_per_variant = {}
            for run_name, (_cdir, variant) in runs.items():
                pa = _preamble(setup, variant) if inc_cdms else ""
                arm_systems_per_variant[run_name] = _system_prompt(cm, pa)

            emit("")
            emit(f"### {arm_label}")
            cols = list(runs)
            header = "  " + f"{'model':14s}  " + "  ".join(f"{c:>16s}" for c in cols)
            emit(header)
            for label, tag in SMALL_PANEL.items():
                cells = {}  # run_name -> list of scores
                for run_name, (cdir, _variant) in runs.items():
                    system_prompt = arm_systems_per_variant[run_name]
                    scores = []
                    for i, probe_entry in enumerate(probes):
                        probe_text, probe_tag = _probe(probe_entry)
                        key = _key(tag, system_prompt, probe_text)
                        cp = _cp(tag, key, cdir)
                        if not cp.exists():
                            scores.append("?")
                            continue
                        resp = json.loads(cp.read_text(encoding="utf-8"))["response"]
                        scores.append(_score(name, scorer, probe_tag, resp))

                        # Reproducibility tracking (only when V1-orig key matches V1-rerun key).
                        if run_name == "v1-rerun":
                            orig_cp = _cp(tag, key, runs["v1-orig"][0])
                            if orig_cp.exists():
                                orig_resp = json.loads(orig_cp.read_text(encoding="utf-8"))["response"]
                                repro_total += 1
                                if orig_resp == resp:
                                    repro_identical += 1
                    cells[run_name] = scores

                def fmt(run: str) -> str:
                    sc = cells[run]
                    s, n, p, lo, hi = _summary(name, sc)
                    return f"{s}/{n} ({p:.2f})"
                emit("  " + f"{label:14s}  " + "  ".join(f"{fmt(c):>16s}" for c in cols))

    emit("")
    emit("=" * 80)
    emit("## Reproducibility check (V1-orig vs V1-rerun, byte-identical comparison)")
    emit("=" * 80)
    if repro_total:
        pct = 100.0 * repro_identical / repro_total
        emit(f"  byte-identical: {repro_identical}/{repro_total} ({pct:.1f}%)")
        if repro_identical < repro_total:
            emit("  Ollama at temp=0 is NOT byte-deterministic across runs on this hardware "
                 "— note this as a methodology caveat. (Determinism at temp=0 depends on "
                 "kernel + batch-size + KV-cache state; some Ollama backends have known "
                 "small-margin nondeterminism.)")
    else:
        emit("  (no overlapping responses to compare)")

    if fh:
        fh.close()


if __name__ == "__main__":
    main()
