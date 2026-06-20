"""Analysis tool — dumps ALL 210 cached Phase 2 responses organized by (mode, arm, model, probe)
so we can read patterns in the FAILED cells, not just probe-0 samples.

This is the WHY-investigation that precedes designing mitigations. Reads from the Phase 2 cache
directly; does no LLM calls.

Run: `python tools/redteam_claude_md_analyze.py [--mode ORDER] [--model gemma-std]`
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
from cdms.store import MemoryService                    # noqa: E402
from local_models import SMALL_PANEL                    # noqa: E402

_BUILDERS = {
    "v1": _session_start_context,
    "v2": _session_start_context_v2,
    "v3": _session_start_context_v3,
    "v4": _session_start_context_v4,
}
from redteam_claude_md_interference import (             # noqa: E402
    CLAUDE_MD_BEM, CLAUDE_MD_INSTR, CLAUDE_MD_ORDER, CLAUDE_MD_OVERRIDE,
    PROBES_BEM, PROBES_INSTR, PROBES_ORDER, PROBES_OVERRIDE,
    PROJECT, _system_prompt,
    score_bem, score_instr, score_order_safe, score_override,
    setup_bem, setup_instr, setup_order, setup_override,
)


def _key(model: str, system: str, user: str) -> str:
    return hashlib.sha256(f"{model}\x00{system}\x00{user}".encode("utf-8")).hexdigest()[:24]


def _cache_path(model: str, key: str, cache_dir: Path) -> Path:
    safe_model = model.replace("/", "_").replace(":", "_")
    return cache_dir / f"{safe_model}__{key}.json"


def _build_preamble(setup, variant: str = "v1") -> str:
    builder = _BUILDERS[variant]
    with tempfile.TemporaryDirectory() as td:
        cfg = Config(home=Path(td))
        svc = MemoryService(cfg, embedder=Embedder(cfg))
        try:
            setup(svc, cfg)
            return builder(cfg, {"cwd": PROJECT})
        finally:
            svc.close()


def _probe_text(probe_entry):
    if isinstance(probe_entry, tuple):
        return probe_entry[1], probe_entry[0]
    return probe_entry, None


MODES_FULL = [
    ("ORDER",    setup_order,    CLAUDE_MD_ORDER,    PROBES_ORDER,    score_order_safe,
        [("treatment(both)",  True,  True),
         ("control(CLAUDEmd-only)", True, False)]),
    ("BEM",      setup_bem,      CLAUDE_MD_BEM,      PROBES_BEM,      score_bem,
        [("treatment(both)",  True,  True)]),
    ("INSTR",    setup_instr,    CLAUDE_MD_INSTR,    PROBES_INSTR,    score_instr,
        [("treatment(CDMS-only)", False, True)]),
    ("OVERRIDE", setup_override, CLAUDE_MD_OVERRIDE, PROBES_OVERRIDE, score_override,
        [("treatment(both)",  True,  True),
         ("control(CDMS-only)", False, True)]),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-dir", default=str(Path(tempfile.gettempdir()) / "cdms_claude_md_cache"))
    ap.add_argument("--variant", choices=["v1", "v2", "v3", "v4"], default="v1",
                    help="preamble variant matching the cache being read")
    ap.add_argument("--mode", default=None, help="filter to one mode (ORDER/BEM/INSTR/OVERRIDE)")
    ap.add_argument("--arm", default=None, help="filter to one arm substring")
    ap.add_argument("--model", default=None, help="filter to one model label")
    ap.add_argument("--score", default=None,
                    help="filter to one outcome score (e.g. unsafe, compliant, claudemd, volunteered)")
    ap.add_argument("--max-chars", type=int, default=300)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    cache = Path(args.cache_dir)
    fh = open(args.out, "w", encoding="utf-8") if args.out else None

    def emit(s: str) -> None:
        print(s)
        if fh:
            fh.write(s + "\n")

    misses = 0
    for name, setup, claude_md, probes, scorer, arms in MODES_FULL:
        if args.mode and name != args.mode:
            continue
        preamble = _build_preamble(setup, variant=args.variant)
        emit("")
        emit("=" * 78)
        emit(f"## Mode: {name}   (preamble={len(preamble)}b, claude.md={len(claude_md)}b)")
        emit("=" * 78)

        arm_systems = {}
        for arm_label, inc_md, inc_cdms in arms:
            cm = claude_md if inc_md else ""
            pa = preamble if inc_cdms else ""
            arm_systems[arm_label] = _system_prompt(cm, pa)

        for arm_label, _inc_md, _inc_cdms in arms:
            if args.arm and args.arm not in arm_label:
                continue
            system_prompt = arm_systems[arm_label]
            emit("")
            emit(f"### Arm: {arm_label}")
            for label, tag in SMALL_PANEL.items():
                if args.model and label != args.model:
                    continue
                emit("")
                emit(f"  --- {label}  ({tag})")
                for i, probe_entry in enumerate(probes):
                    probe_text, probe_tag = _probe_text(probe_entry)
                    key = _key(tag, system_prompt, probe_text)
                    cp = _cache_path(tag, key, cache)
                    if not cp.exists():
                        misses += 1
                        continue
                    resp = json.loads(cp.read_text(encoding="utf-8"))["response"]
                    if name == "ORDER":
                        score = scorer(probe_tag, resp)
                    else:
                        score = scorer(resp)
                    if args.score and args.score not in score:
                        continue
                    body = resp.replace("\n", " ").strip()[:args.max_chars]
                    tag_str = f"[{probe_tag}] " if probe_tag else ""
                    emit(f"    [{i}] [{score:>14s}] {tag_str}{body}")
    if misses:
        emit("")
        emit(f"# {misses} cache misses (probes not previously run)")
    if fh:
        fh.close()


if __name__ == "__main__":
    main()
