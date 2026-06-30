"""Framing-sub-construct PILOT generation (runs on Sparky/GX10). Generates each admitted pilot facet
(probe + rephrasing) under each condition (REAL / co-author DECOY) on the mech-arm models, temp=0,
model-OUTER. Writes one gen.jsonl for the local judge step. Stdlib only (urllib) — no extra deps.

Usage (on Sparky):  python tools/framing_pilot_gen.py [--cache DIR] [--host http://localhost:11434]
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from framing_conditions import build_preamble, CONDITIONS, SELF_TOKEN  # noqa: E402
from framing_facets_probes import ADMITTED  # noqa: E402

MECH = [
    "granite-3.0-8b-q8", "granite-3.1-8b-q8", "granite-3.2-8b-q8", "granite-3.3-8b-q8",
    "granite-3.0-2b-q8", "granite-3.1-2b-q8", "granite-3.2-2b-q8", "granite-3.3-2b-q8",
    "mistral-g-v0.1", "mistral-g-v0.2", "mistral-g-v0.3",
]


def chat(host, model, system, user, timeout=180):
    body = json.dumps({
        "model": model, "stream": False,
        "options": {"temperature": 0, "num_predict": 512},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request(host + "/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["message"]["content"]


def main():
    a = sys.argv[1:]
    host = a[a.index("--host") + 1] if "--host" in a else "http://localhost:11434"
    ts = time.strftime("%Y%m%d_%H%M%S")
    cache = Path(a[a.index("--cache") + 1]) if "--cache" in a else Path.home() / "cdms_cache" / f"framing_pilot_{ts}"
    cache.mkdir(parents=True, exist_ok=True)
    out = cache / "gen.jsonl"
    detail = cache / "detail.log"

    def log(m):
        line = f"[{time.strftime('%H:%M:%S')}] {m}"
        print(line, flush=True)
        with open(detail, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    # probe-variants: each admitted facet -> (orig, "probe") and (rephrasing, "rephrasing")
    variants = []
    for p in ADMITTED:
        variants.append((p["dimension"], p["class"], "probe", p["probe"]))
        variants.append((p["dimension"], p["class"], "rephrasing", p["rephrasing"]))
    log(f"=== framing pilot gen: {len(MECH)} models x {len(variants)} probe-variants x {len(CONDITIONS)} "
        f"conditions = {len(MECH)*len(variants)*len(CONDITIONS)} calls (cache={cache}) ===")
    preambles = {c: build_preamble(c) for c in CONDITIONS}

    n = 0
    with open(out, "a", encoding="utf-8") as fout:
        for mi, model in enumerate(MECH, 1):
            log(f"--- [{mi}/{len(MECH)}] {model} (cold-load + {len(variants)*len(CONDITIONS)} gens) ---")
            for cond in CONDITIONS:
                for dim, cls, vkind, ptext in variants:
                    try:
                        resp = chat(host, model, preambles[cond], ptext)
                    except Exception as e:  # noqa: BLE001
                        log(f"  ERR {model}/{cond}/{dim}/{vkind}: {type(e).__name__}: {e}")
                        resp = None
                    rec = {"model": model, "condition": cond, "dimension": dim, "class": cls,
                           "variant": vkind, "probe": ptext, "response": resp,
                           "surfaced": bool(resp) and SELF_TOKEN in resp}
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n"); fout.flush()
                    n += 1
            log(f"  ok {model}  (running total {n})")
    log(f"=== DONE: {n} records -> {out} ===")
    (cache / "done").touch()
    print(str(cache))


if __name__ == "__main__":
    main()
