"""Reconstruct + A'-panel-judge a ladder/subject cache (interference.py format). Generalizes build_gold_set
(reconstruction) + judge_expand (concurrent panel judging) for the GX10 dense qwen ladder + the Nemotron MoE
rungs. Reads a sources JSON [{backend, model, cache_dir, generation}], reconstructs the token-containing
BEM+recall responses (v1, --expand-probes), judges them concurrently with the validated A' panel, and writes
<out>. Non-token responses are recorded ABSENT (definitionally non-breach). Aggregation/overlay is a separate
step (morning).

Usage:
  python tools/judge_ladder.py SOURCES.json OUT_panel.jsonl [--reconstruct-only] [--workers N] [--cap USD] [--stamp S]
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
import redteam_claude_md_interference as R  # noqa: E402
from ownership_judge import LABELS_A4, RUBRIC_A4, panel_judge  # noqa: E402
from openrouter_cost_guard import BudgetExceededError  # noqa: E402

TOK = re.compile(r"(?<![A-Za-z0-9_])starboard_loop(?![A-Za-z0-9_])")
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")  # mirrors openrouter_chat._SAFE_MODEL_RE
HOME = Path(os.path.expanduser("~"))
# (display, claude_md, probe_key, probe_const) — BEM + recall, the two ladder modes
MODES = [("BEM", R.CLAUDE_MD_BEM, "BEM", R.PROBES_BEM),
         ("recall", "", "BEM_WORKSPACE_FACT", R.PROBES_BEM_WORKSPACE_FACT)]


def safe_model(backend: str, model: str) -> str:
    if backend == "openrouter":
        return _SAFE.sub("_", model).strip("._-") or "model"
    return model.replace("/", "_").replace(":", "_")  # ollama scheme


def key_for(model: str, system: str, user: str) -> str:
    return hashlib.sha256(f"{model}\x00{system}\x00{user}".encode("utf-8")).hexdigest()[:24]


def reconstruct(sources, variant="v1", subsample_n=10):
    """interference.py caches to <cache_dir>/<backend>/expand/<safe>__<key>.json (openrouter prefixes
    'openrouter__'). Rebuild the v1 system+probes, key each, and pull the cached response."""
    with tempfile.TemporaryDirectory() as td:
        preamble = R._real_preamble_for_mode(R.setup_bem, Path(td), variant=variant)
    recs, miss = [], []
    for src in sources:
        backend, model = src["backend"], src["model"]
        leaf = Path(os.path.expanduser(src["cache_dir"])) / backend / "expand"
        sm = safe_model(backend, model)
        hits = 0
        for disp, claude_md, pkey, pconst in MODES:
            system = R._system_prompt(claude_md, preamble)
            probes = R._select_probes(pkey, pconst, expand=True, subsample_n=subsample_n)
            for i, probe in enumerate(probes):
                user = probe if isinstance(probe, str) else probe[1]
                k = key_for(model, system, user)
                fn = (f"openrouter__{sm}__{k}.json" if backend == "openrouter" else f"{sm}__{k}.json")
                fp = leaf / fn
                if not fp.exists():
                    continue
                try:
                    resp = json.loads(fp.read_text(encoding="utf-8")).get("response")
                except (json.JSONDecodeError, OSError):
                    continue
                if not isinstance(resp, str):
                    continue
                hits += 1
                recs.append({"subject_model": model, "generation": src.get("generation", "?"),
                             "mode": disp, "probe_idx": i, "probe": user, "response": resp,
                             "token": R.BEM_CDMS_TOKEN})
        files = len(list(leaf.glob("*.json"))) if leaf.exists() else 0
        print(f"  {model:<42} {backend:<10} reconstructed {hits}  (files on disk: {files})", flush=True)
        if hits == 0:
            miss.append(model)
    return recs, miss


class TSGuard:
    def __init__(self, cap):
        self.cap = cap; self._spent = 0.0; self.lock = threading.Lock()
    def check_can_call(self, est):
        with self.lock:
            if self._spent + est > self.cap:
                raise BudgetExceededError(f"judge cap ${self.cap} exceeded (spent ${self._spent:.3f})")
    def record(self, actual):
        with self.lock:
            self._spent += actual


def main():
    args = sys.argv[1:]
    sources_path, out_path = args[0], args[1]
    recon_only = "--reconstruct-only" in args
    workers = int(args[args.index("--workers") + 1]) if "--workers" in args else 12
    cap = float(args[args.index("--cap") + 1]) if "--cap" in args else 10.0
    stamp = args[args.index("--stamp") + 1] if "--stamp" in args else "ladder"
    subsample_n = int(args[args.index("--subsample-n") + 1]) if "--subsample-n" in args else 10
    sources = json.loads(Path(sources_path).read_text(encoding="utf-8"))

    print(f"=== reconstruct ({len(sources)} sources) ===", flush=True)
    recs, miss = reconstruct(sources, subsample_n=subsample_n)
    tokc = [r for r in recs if TOK.search(r["response"] or "")]
    print(f"total reconstructed {len(recs)}; token-containing {len(tokc)} (to judge); "
          f"ABSENT remainder {len(recs)-len(tokc)}", flush=True)
    if miss:
        print(f"!! sources with ZERO reconstructed (check cache_dir/backend): {miss}", flush=True)
    if recon_only:
        print("(--reconstruct-only: stopping before judging)")
        return

    cache = HOME / "cdms_cache" / f"ladder_judge_{stamp}"
    cache.mkdir(parents=True, exist_ok=True)
    guard = TSGuard(cap)
    results, rlock, st = [], threading.Lock(), {"done": 0}

    def work(r):
        try:
            res = panel_judge(r["response"], r["token"], r["mode"], r["subject_model"], cache,
                              cost_guard=guard, rubric=RUBRIC_A4, labels=LABELS_A4)
        except BudgetExceededError:
            return None
        rec = {**{k: r[k] for k in ("subject_model", "generation", "mode", "probe_idx", "probe", "response")},
               "panel_label": res["label"], "escalate": res["escalate"], "votes": res["votes"]}
        with rlock:
            results.append(rec); st["done"] += 1
            if st["done"] % 50 == 0:
                print(f"  judged {st['done']}/{len(tokc)}  spent=${guard._spent:.3f}", flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(work, r) for r in tokc]
        for _ in as_completed(futs):
            pass
    # carry the ABSENT remainder (exact denominators), no API
    absent = [{**{k: r[k] for k in ("subject_model", "generation", "mode", "probe_idx", "probe", "response")},
               "panel_label": "ABSENT", "escalate": False, "votes": {}} for r in recs if r not in tokc]
    out = results + absent
    Path(out_path).write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + "\n", encoding="utf-8")
    print(f"DONE: judged {len(results)} token-containing + {len(absent)} ABSENT; spent ${guard._spent:.3f} "
          f"-> {out_path}", flush=True)


if __name__ == "__main__":
    main()
