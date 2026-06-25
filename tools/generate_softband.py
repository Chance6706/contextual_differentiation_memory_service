"""Expand the runtime-instrument gold's soft-band BEM cell (gold-EXPANSION for the inclusive-breach CI).

Generates fresh qwen2.5-72b BEM responses (the soft-band producer) via OpenRouter at temp>0 — many
stochastic samples per self-description probe — to ~6x the contested token-containing BEM set, so the
judge-vs-judge inclusive-breach AC1 can be recomputed at higher n (the gate question Josh chose to resolve
empirically). This is JUDGE-validation material: it tests the panel's reliability on soft-adoption language,
NOT the substantive leak rate (that's the GX10 ladder). Subject quant/temp differs from the snipe by design
(OpenRouter host, temp 0.8) — fine, since we're stress-testing the JUDGE on the language pattern, not the
subject. Saves every response to expand_gen.jsonl (reproducible). NO human labels needed for AC1.

Env: GEN_MODEL (default qwen/qwen-2.5-72b-instruct), GEN_SAMPLES (per probe, default 40), GEN_TEMP (0.8),
GEN_WORKERS (10), GEN_CAP (USD, 5.0), GEN_VARIANT (v1).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
import redteam_claude_md_interference as R  # noqa: E402

MODEL = os.environ.get("GEN_MODEL", "qwen/qwen-2.5-72b-instruct")
SAMPLES = int(os.environ.get("GEN_SAMPLES", "40"))
TEMP = float(os.environ.get("GEN_TEMP", "0.8"))
WORKERS = int(os.environ.get("GEN_WORKERS", "10"))
CAP = float(os.environ.get("GEN_CAP", "5.0"))
VARIANT = os.environ.get("GEN_VARIANT", "v1")
OUT = REPO / "docs" / "validation" / "runtime_instrument" / "gold_set" / "expand_gen.jsonl"

URL = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_API_KEY")
N_PREDICT = 160

_lock = threading.Lock()
_state = {"done": 0, "ok": 0, "tok": 0, "err": 0, "cost": 0.0}


def call(system: str, user: str, seed_tag: str) -> str | None:
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": TEMP, "max_tokens": N_PREDICT, "stream": False,
    }
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
               "HTTP-Referer": "https://github.com/Chance6706/contextual_differentiation_memory_service",
               "X-Title": "CDMS runtime-instrument gold expansion"}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            parsed = json.loads(r.read())
        out = parsed["choices"][0]["message"]["content"]
        usage = parsed.get("usage") or {}
        cost = usage.get("cost")
        cost = float(cost) if isinstance(cost, (int, float)) else 0.0003
        return out if isinstance(out, str) else None, cost
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, IndexError,
            json.JSONDecodeError, TypeError) as e:
        return None, str(e)


def main():
    if not KEY:
        raise SystemExit("OPENROUTER_API_KEY not set")
    with tempfile.TemporaryDirectory() as td:
        preamble = R._real_preamble_for_mode(R.setup_bem, Path(td), variant=VARIANT)
    system = R._system_prompt(R.CLAUDE_MD_BEM, preamble)
    probes = R._select_probes("BEM", R.PROBES_BEM, expand=True)
    tok = R.BEM_CDMS_TOKEN

    jobs = []
    for pi, probe in enumerate(probes):
        user = probe if isinstance(probe, str) else probe[1]
        for s in range(SAMPLES):
            jobs.append((pi, user, s))
    print(f"model={MODEL} temp={TEMP} probes={len(probes)} samples/probe={SAMPLES} "
          f"total={len(jobs)} workers={WORKERS} cap=${CAP}", flush=True)

    fout = OUT.open("w", encoding="utf-8")

    def work(job):
        pi, user, s = job
        if _state["cost"] >= CAP:
            return None
        res = call(system, user, f"{pi}.{s}")
        out, cost = res if isinstance(res, tuple) else (None, 0.0)
        with _lock:
            _state["done"] += 1
            if isinstance(out, str):
                _state["ok"] += 1
                _state["cost"] += cost if isinstance(cost, float) else 0.0003
                rec = {"id": f"x{pi:02d}_{s:03d}", "subject_model": MODEL, "generation": "qwen2.5",
                       "variant": VARIANT, "mode": "BEM", "probe_idx": pi, "sample_idx": s,
                       "token": tok, "control_token": R.BEM_CLAUDE_TOKEN, "probe": user, "response": out}
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fout.flush()
                import re
                if re.search(r"(?<![A-Za-z0-9_])starboard_loop(?![A-Za-z0-9_])", out):
                    _state["tok"] += 1
            else:
                _state["err"] += 1
            if _state["done"] % 100 == 0:
                print(f"  {_state['done']}/{len(jobs)}  ok={_state['ok']} tok+={_state['tok']} "
                      f"err={_state['err']} ${_state['cost']:.3f}", flush=True)
        return out

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(work, j) for j in jobs]
        for _ in as_completed(futs):
            pass
    fout.close()
    print(f"DONE: ok={_state['ok']} token-containing={_state['tok']} err={_state['err']} "
          f"cost=${_state['cost']:.3f} -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
