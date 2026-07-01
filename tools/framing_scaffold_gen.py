"""Scaffold-gradient generation (runs on Sparky). Generates the mini-pilot / grid for the curation axis:
each facet (probe + rephrasing) under each condition (REAL/DECOY) at each SCAFFOLD level (implied / raw —
declared is the frozen confirmatory, already run), on a model set, temp=0, model-OUTER, cold-load warmup.
Writes one gen.jsonl (with a `scaffold` field) for the local judge step.

Usage (Sparky):
  python tools/framing_scaffold_gen.py [--scaffold implied,raw] [--nfacets 15] [--models m1,m2,...]
                                       [--cache DIR] [--host http://localhost:11434]
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from framing_conditions_scaffold import build_preamble, CONDITIONS, SELF_TOKEN  # noqa: E402
from framing_confirm_probes import ADMITTED  # the frozen 34 confirmatory facets  # noqa: E402

# mini-pilot default = a representative mech subset (span generations + sizes + both families); cheap to run.
MECH_MINI = ["granite-3.0-8b-q8", "granite-3.3-8b-q8", "granite-3.0-2b-q8",
             "granite-3.3-2b-q8", "mistral-g-v0.1", "mistral-g-v0.3"]


def chat(host, model, system, user, timeout=600, n_predict=512, keep_alive="30m"):
    # timeout=600 (gen) / warmup passes 1200: large 20-74B Q8 models on Sparky live on a SLOW SATA mount
    # (/mnt/models = /dev/sda1), so cold-cache loads run 300-650s — the old 180/300 timeouts disconnected
    # mid-load and ollama ABORTED the load (death spiral). keep_alive holds the model warm across the
    # per-model gen loop so the slow cold-load is paid once, not per call. (Pair with OLLAMA_LOAD_TIMEOUT>=30m
    # server-side, else ollama's own 5-min default aborts the big cold loads regardless of client timeout.)
    body = json.dumps({"model": model, "stream": False, "keep_alive": keep_alive,
                       "options": {"temperature": 0, "num_predict": n_predict},
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(host + "/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["message"]["content"]


def main():
    a = sys.argv[1:]

    def opt(name, default=None):
        return a[a.index(name) + 1] if name in a else default
    host = opt("--host", "http://localhost:11434")
    scaffolds = (opt("--scaffold", "implied,raw")).split(",")
    nfacets = int(opt("--nfacets", "15"))
    models = (opt("--models").split(",") if opt("--models") else MECH_MINI)
    ts = time.strftime("%Y%m%d_%H%M%S")
    cache = Path(opt("--cache")) if opt("--cache") else Path.home() / "cdms_cache" / f"framing_scaffold_{ts}"
    cache.mkdir(parents=True, exist_ok=True)
    out, detail = cache / "gen.jsonl", cache / "detail.log"

    def log(m):
        line = f"[{time.strftime('%H:%M:%S')}] {m}"
        print(line, flush=True)
        with open(detail, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    facets = ADMITTED[:nfacets]
    variants = []
    for p in facets:
        variants.append((p["dimension"], p["class"], "probe", p["probe"]))
        variants.append((p["dimension"], p["class"], "rephrasing", p["rephrasing"]))
    total = len(models) * len(scaffolds) * len(variants) * len(CONDITIONS)
    log(f"=== scaffold-gradient gen: {len(models)} models x {scaffolds} x {len(facets)} facets x "
        f"{len(variants)//len(facets)} variants x {len(CONDITIONS)} conditions = {total} calls (cache={cache}) ===")
    preambles = {(sc, c): build_preamble(c, sc) for sc in scaffolds for c in CONDITIONS}

    n = 0
    with open(out, "a", encoding="utf-8") as fout:
        for mi, model in enumerate(models, 1):
            log(f"--- [{mi}/{len(models)}] {model} (warmup + {len(scaffolds)*len(variants)*len(CONDITIONS)} gens) ---")
            try:
                chat(host, model, "You are a helpful assistant.", "Say ok.", timeout=1200, n_predict=1)
            except Exception as e:  # noqa: BLE001
                log(f"  warmup note {model}: {type(e).__name__}: {e}")
            for sc in scaffolds:
                for cond in CONDITIONS:
                    for dim, cls, vkind, ptext in variants:
                        try:
                            resp = chat(host, model, preambles[(sc, cond)], ptext)
                        except Exception as e:  # noqa: BLE001
                            log(f"  ERR {model}/{sc}/{cond}/{dim}/{vkind}: {type(e).__name__}: {e}")
                            resp = None
                        fout.write(json.dumps({"model": model, "scaffold": sc, "condition": cond,
                                               "dimension": dim, "class": cls, "variant": vkind,
                                               "probe": ptext, "response": resp,
                                               "surfaced": bool(resp) and SELF_TOKEN in resp},
                                              ensure_ascii=False) + "\n")
                        fout.flush()
                        n += 1
            log(f"  ok {model}  (running total {n})")
    log(f"=== DONE: {n} records -> {out} ===")
    (cache / "done").touch()
    print(str(cache))


if __name__ == "__main__":
    main()
