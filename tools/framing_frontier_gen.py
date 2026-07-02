"""Scaffold-gradient FRONTIER generation (OpenRouter backend) — THINKING-FACTOR matched-pair design.

Same curation gradient as framing_scaffold_gen.py (declared/implied/raw x 34 confirmatory facets x 2 variants
x 2 conditions), subjects = frontier API models via OpenRouter. Schema is identical to the local scaffold gen
(plus a `reasoning` field) so the SAME judge (framing_pilot_judge.py) + analyzer fold the frontier arm in.

WHY matched pairs (Josh, 2026-07-01): the smoke test showed a reasoning flagship (gemini-2.5-pro) REJECTS the
injected persona ("I'm an AI") and doesn't surface the planted token, while a direct-answer model (deepseek)
adopts + surfaces like the local arm. To attribute that to THINKING (not vendor/size/tune), we contrast
thinking vs non-thinking with everything else held constant:
  * SEPARATE-ID pairs (built-in mode, reasoning=None): qwen3-max / -thinking; qwen3-235b-a22b-2507 / -thinking;
    gpt-5.2-chat / gpt-5.2.
  * SAME-ID reasoning TOGGLE pairs (reasoning on vs off, identical weights — the cleanest isolation, non-Qwen):
    claude-opus-4.8, deepseek-v3.2, claude-sonnet-5.
The reasoning flag is folded into openrouter_chat's cache key, so on/off of one id never collide.

Runs on any box with OPENROUTER_API_KEY (not Sparky) -> parallel-safe with the local GPU grid. HARD $-cap via
CostGuard. openrouter_chat caches per (model, reasoning, system, user) -> a resumed run reuses paid calls at $0.

DELIBERATE DEVIATION (rule 11): max_tokens defaults to 3000 (vs local 512) so THINKING members finish their
answer instead of truncating mid-reasoning (a truncated null answer would masquerade as non-surfacing). temp=0.

Usage:
  python tools/framing_frontier_gen.py [--labels a,b,...] [--scaffold declared,implied,raw] [--nfacets 34]
                                       [--cap 85] [--max-tokens 3000] [--cache DIR]
  python tools/framing_frontier_gen.py --selftest        # no API, no spend
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from framing_conditions_scaffold import build_preamble, CONDITIONS, SELF_TOKEN  # noqa: E402
from framing_confirm_probes import ADMITTED  # frozen 34 confirmatory facets  # noqa: E402
from openrouter_chat import openrouter_chat, RateLimitDeferred, OpenRouterAPIError  # noqa: E402
from openrouter_cost_guard import CostGuard, BudgetExceededError  # noqa: E402

_ON = {"enabled": True}      # reasoning toggle ON  (thinking member)
_OFF = {"enabled": False}    # reasoning toggle OFF (non-thinking member)

# (label, openrouter_id, reasoning) — label is what lands in the record's "model" field (distinguishes toggle
# members that share an id). reasoning=None => model's built-in mode (separate-ID pairs). Cheapest first.
ROSTER = [
    # --- separate-ID pairs (built-in thinking mode) ---
    ("qwen3-235b-2507",           "qwen/qwen3-235b-a22b-2507",          None),
    ("qwen3-235b-thinking-2507",  "qwen/qwen3-235b-a22b-thinking-2507", None),
    ("qwen3-max",                 "qwen/qwen3-max",                     None),
    ("qwen3-max-thinking",        "qwen/qwen3-max-thinking",            None),
    ("gpt-5.2-chat",              "openai/gpt-5.2-chat",                None),
    ("gpt-5.2",                   "openai/gpt-5.2",                     None),
    # --- same-id reasoning TOGGLE pairs (identical weights, only the reasoning flag differs) ---
    ("deepseek-v3.2:nothink",     "deepseek/deepseek-v3.2",             _OFF),
    ("deepseek-v3.2:think",       "deepseek/deepseek-v3.2",             _ON),
    ("sonnet-5:nothink",          "anthropic/claude-sonnet-5",          _OFF),
    ("sonnet-5:think",            "anthropic/claude-sonnet-5",          _ON),
    ("opus-4.8:nothink",          "anthropic/claude-opus-4.8",          _OFF),
    ("opus-4.8:think",            "anthropic/claude-opus-4.8",          _ON),
]


def _reasoning_tag(r):
    return "default" if r is None else ("on" if r.get("enabled") else "off")


def main():
    a = sys.argv[1:]
    if "--selftest" in a:
        sys.exit(0 if selftest() else 1)

    def opt(name, default=None):
        return a[a.index(name) + 1] if name in a else default
    roster = ROSTER
    if opt("--labels"):
        want = set(opt("--labels").split(","))
        roster = [r for r in ROSTER if r[0] in want]
    scaffolds = (opt("--scaffold", "declared,implied,raw")).split(",")
    nfacets = int(opt("--nfacets", "34"))
    cap = float(opt("--cap", "85"))
    max_tokens = int(opt("--max-tokens", "3000"))
    ts = time.strftime("%Y%m%d_%H%M%S")
    cache = Path(opt("--cache")) if opt("--cache") else Path.home() / "cdms_cache" / f"framing_frontier_{ts}"
    cache.mkdir(parents=True, exist_ok=True)
    out, detail = cache / "gen.jsonl", cache / "detail.log"
    guard = CostGuard(cap_usd=cap, state_file=cache / "cost_state.json")

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
    total = len(roster) * len(scaffolds) * len(variants) * len(CONDITIONS)
    log(f"=== FRONTIER thinking-factor gen: {len(roster)} configs x {scaffolds} x {len(facets)} facets x "
        f"{len(variants)//len(facets)} variants x {len(CONDITIONS)} conditions = {total} calls; "
        f"cap=${cap} max_tokens={max_tokens} (cache={cache}) ===")
    preambles = {(sc, c): build_preamble(c, sc) for sc in scaffolds for c in CONDITIONS}

    n, stopped = 0, False
    with open(out, "a", encoding="utf-8") as fout:
        for mi, (label, mid, reasoning) in enumerate(roster, 1):
            if stopped:
                break
            log(f"--- [{mi}/{len(roster)}] {label}  ({mid}, reasoning={_reasoning_tag(reasoning)}) ---")
            for sc in scaffolds:
                for cond in CONDITIONS:
                    for dim, cls, vkind, ptext in variants:
                        try:
                            resp = openrouter_chat(mid, preambles[(sc, cond)], ptext, cache,
                                                   n_predict=max_tokens, cost_guard=guard, reasoning=reasoning)
                        except BudgetExceededError as e:
                            log(f"  CAP HIT (${guard.spent():.2f}/${cap}) at {label}/{sc}/{cond} — stop: {e}")
                            stopped = True
                            break
                        except (RateLimitDeferred, OpenRouterAPIError) as e:
                            log(f"  ERR {label}/{sc}/{cond}/{dim}/{vkind}: {type(e).__name__}: {e}")
                            resp = None
                        fout.write(json.dumps({"model": label, "model_id": mid,
                                               "reasoning": _reasoning_tag(reasoning),
                                               "scaffold": sc, "condition": cond, "dimension": dim,
                                               "class": cls, "variant": vkind, "probe": ptext, "response": resp,
                                               "surfaced": bool(resp) and SELF_TOKEN in resp},
                                              ensure_ascii=False) + "\n")
                        fout.flush()
                        n += 1
                    if stopped:
                        break
                if stopped:
                    break
            log(f"  ok {label}  (running total {n}, spent ${guard.spent():.2f})")
    log(f"=== {'STOPPED at cap' if stopped else 'DONE'}: {n} records, spent ${guard.spent():.3f} -> {out} ===")
    (cache / "done").touch()
    print(str(cache))


def selftest():
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and cond
        print(f"[selftest] {name}: {'PASS' if cond else 'FAIL'}")

    for sc in ("declared", "implied", "raw"):
        for c in CONDITIONS:
            chk(f"{sc}/{c} preamble has self token", SELF_TOKEN in build_preamble(c, sc))
    chk("34 facets available", len(ADMITTED) >= 34)
    # matched-pair integrity: every toggle id appears exactly twice (on + off); labels unique
    labels = [r[0] for r in ROSTER]
    chk("labels unique", len(labels) == len(set(labels)))
    toggles = {}
    for label, mid, r in ROSTER:
        if r is not None:
            toggles.setdefault(mid, set()).add(_reasoning_tag(r))
    chk("each toggle id has BOTH on+off", all(v == {"on", "off"} for v in toggles.values()) and toggles)
    # cache-collision guard: on/off of the SAME id must produce DIFFERENT cache keys (else silent wrong-cache)
    import hashlib
    def key(mid, reasoning):
        km = (f"{mid}\x00S\x00U" if reasoning is None
              else f"{mid}\x00r={json.dumps(reasoning, sort_keys=True)}\x00S\x00U")
        return hashlib.sha256(km.encode()).hexdigest()[:24]
    chk("toggle on/off keys differ (no cache collision)",
        key("anthropic/claude-opus-4.8", _ON) != key("anthropic/claude-opus-4.8", _OFF))
    chk("reasoning=None key == legacy key (judge cache preserved)",
        key("m", None) == hashlib.sha256("m\x00S\x00U".encode()).hexdigest()[:24])
    # cost guard caps
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        g = CostGuard(cap_usd=0.001, state_file=Path(td) / "s.json")
        try:
            g.check_can_call(0.02); chk("cost guard refuses over-cap", False)
        except BudgetExceededError:
            chk("cost guard refuses over-cap", True)
    print(f"\n[selftest] OVERALL: {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    main()
