"""Operator-triggered external-review runner for `tools/probes_rephrasings.py`.

Implements pre-reg §3 "API model review" pass: each rephrasing is sent (alongside
its original) to a content-safety judge with a fixed YES/NO prompt:

    Does this rephrasing preserve the original probe's intent without
    introducing ambiguity? Reply only YES or NO.

A NO verdict gates that rephrasing out of any single-model-tier matrix run. Per
pre-reg §3 this is a methodology gate, not a quality polish - if the review has
NOT been run, single-model-tier writeups must be tagged
"probes not externally reviewed."

This runner is operator-triggered (NOT run as part of the assembly commit). It
fans out across all rephrasings, caches verdicts on disk so re-runs are cheap,
and prints a summary table plus the list of any NO-verdict probes so an operator
can decide between (a) accepting the NO + dropping the rephrasing, or (b)
hand-editing the rephrasing in `tools/probes_rephrasings.py` and re-running.

The judge model defaults to `nvidia/nemotron-3.5-content-safety:free` (pre-reg
§3 preferred guardrail-specialized judge), with `openrouter/owl-alpha` as a
fallback if Nemotron returns 404 / unavailable.

Run:
    OPENROUTER_API_KEY=sk-... uv run python tools/probes_review.py \\
        [--cache-dir DIR] [--model MODEL]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

# tools/ on sys.path so sibling imports resolve (mirrors redteam_claude_md_interference).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Sibling imports (kept after sys.path manipulation, hence E402 in real linters).
from openrouter_chat import (  # noqa: E402
    openrouter_chat, OpenRouterAPIError, RateLimitDeferred,
)
from probes_rephrasings import REPHRASINGS  # noqa: E402

# We import the canonical originals from the matrix tool. The matrix tool sets
# CDMS_EMBED_BACKEND=hash on import; that's a no-op here other than env hygiene.
from redteam_claude_md_interference import (  # noqa: E402
    PROBES_ORDER, PROBES_ORDER_OVERFIRE,
    PROBES_BEM, PROBES_BEM_WORKSPACE_FACT,
    PROBES_INSTR, PROBES_OVERRIDE,
)


# Mode -> originals list. Mirrors REPHRASINGS keys.
_MODE_ORIGINALS = {
    "ORDER": PROBES_ORDER,
    "ORDER_OVERFIRE": PROBES_ORDER_OVERFIRE,
    "BEM": PROBES_BEM,
    "BEM_WORKSPACE_FACT": PROBES_BEM_WORKSPACE_FACT,
    "INSTR": PROBES_INSTR,
    "OVERRIDE": PROBES_OVERRIDE,
}

# Models to try, in preference order. Pre-reg §3 prefers Nemotron content-safety
# (guardrail-specialized); we keep owl-alpha as the documented fallback.
_PREFERRED_JUDGE = "nvidia/nemotron-3.5-content-safety:free"
_FALLBACK_JUDGE = "openrouter/owl-alpha"

_PROMPT_TEMPLATE = (
    "Does this rephrasing preserve the original probe's intent without "
    "introducing ambiguity? Reply only YES or NO.\n\n"
    "Original: {original}\n"
    "Rephrasing: {rephrasing}"
)


def _probe_text(probe) -> str:
    """Extract the textual probe content regardless of (tag, text) vs str shape."""
    if isinstance(probe, tuple):
        return probe[1]
    return probe


def _classify_verdict(raw: str) -> str:
    """Map a judge's raw response to YES / NO / AMBIGUOUS.

    YES iff the response starts with (or contains a leading word) "yes" and
    no leading "no". NO iff the inverse. Anything else (hedging, refusals,
    empty) -> AMBIGUOUS; the operator decides.
    """
    text = raw.strip().lower()
    if not text:
        return "AMBIGUOUS"
    # Strip common punctuation around the first token.
    first_token = text.split()[0].strip(".,!?:;")
    if first_token in {"yes", "y"}:
        return "YES"
    if first_token in {"no", "n"}:
        return "NO"
    # Fall back to substring inspection of the first ~32 chars.
    head = text[:32]
    if "yes" in head and "no" not in head:
        return "YES"
    if "no" in head and "yes" not in head:
        return "NO"
    return "AMBIGUOUS"


def review_rephrasings(
    api_key: str | None = None,
    cache_dir: Path | None = None,
    model: str = _PREFERRED_JUDGE,
    fallback_model: str | None = _FALLBACK_JUDGE,
) -> dict:
    """Run the external-review pass over every rephrasing.

    Returns a dict keyed by `(mode, original_idx, rephrasing_idx)` ->
    `{"verdict": "YES"|"NO"|"AMBIGUOUS", "raw_response": str, "model": str}`.

    Args:
        api_key: Optional explicit OPENROUTER_API_KEY override. If None, the
            adapter reads from env; missing key raises OpenRouterAPIError.
        cache_dir: Where the OpenRouter adapter caches responses. Defaults to
            a tempdir under the system temp.
        model: Preferred judge model slug.
        fallback_model: Secondary judge if `model` returns a 404/unavailable.
    """
    # Fail-fast on missing key (mirrors matrix runner's startup contract so the
    # operator doesn't discover the gap mid-fanout).
    if api_key is not None:
        os.environ["OPENROUTER_API_KEY"] = api_key
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise OpenRouterAPIError(
            "OPENROUTER_API_KEY environment variable not set; "
            "probes_review.py refuses to start without it.")

    cache = Path(cache_dir) if cache_dir else (
        Path(tempfile.gettempdir()) / "cdms_probes_review_cache")
    cache.mkdir(parents=True, exist_ok=True)

    results: dict = {}
    judge = model
    judge_unavailable = False

    for mode_name, by_idx in REPHRASINGS.items():
        originals = _MODE_ORIGINALS[mode_name]
        for original_idx, rephr_list in by_idx.items():
            original_text = _probe_text(originals[original_idx])
            for rephr_idx, rephr_text in enumerate(rephr_list):
                prompt = _PROMPT_TEMPLATE.format(
                    original=original_text, rephrasing=rephr_text)
                key = (mode_name, original_idx, rephr_idx)
                try:
                    raw = openrouter_chat(
                        judge,
                        system="You are a careful evaluator. Answer only YES or NO.",
                        user=prompt,
                        cache=cache,
                        n_predict=8,
                    )
                except OpenRouterAPIError as e:
                    # If preferred judge is unavailable, switch to fallback ONCE
                    # for the remainder of the run.
                    if not judge_unavailable and fallback_model:
                        print(f"# judge {judge} failed ({e}); falling back to {fallback_model}",
                              file=sys.stderr)
                        judge = fallback_model
                        judge_unavailable = True
                        try:
                            raw = openrouter_chat(
                                judge,
                                system="You are a careful evaluator. Answer only YES or NO.",
                                user=prompt,
                                cache=cache,
                                n_predict=8,
                            )
                        except OpenRouterAPIError as e2:
                            results[key] = {
                                "verdict": "AMBIGUOUS",
                                "raw_response": f"<error: {e2}>",
                                "model": judge,
                            }
                            continue
                    else:
                        results[key] = {
                            "verdict": "AMBIGUOUS",
                            "raw_response": f"<error: {e}>",
                            "model": judge,
                        }
                        continue
                except RateLimitDeferred:
                    # Pre-reg §5 minimal: skip + record; re-run from cache resumes.
                    results[key] = {
                        "verdict": "AMBIGUOUS",
                        "raw_response": "<rate-limit-deferred>",
                        "model": judge,
                    }
                    continue
                verdict = _classify_verdict(raw)
                results[key] = {
                    "verdict": verdict,
                    "raw_response": raw.strip(),
                    "model": judge,
                }
    return results


def _print_summary(results: dict) -> None:
    """Print per-mode YES/NO/AMBIGUOUS tallies + flag any NO/AMBIGUOUS rows."""
    # Per-mode tallies.
    per_mode: dict[str, dict[str, int]] = {}
    for (mode, _o, _r), entry in results.items():
        slot = per_mode.setdefault(mode, {"YES": 0, "NO": 0, "AMBIGUOUS": 0})
        slot[entry["verdict"]] += 1

    print()
    print("## External rephrasing review summary")
    print(f"{'Mode':<22s}  {'YES':>5s}  {'NO':>5s}  {'AMB':>5s}  {'Total':>6s}")
    print("-" * 50)
    for mode in sorted(per_mode):
        s = per_mode[mode]
        total = s["YES"] + s["NO"] + s["AMBIGUOUS"]
        print(f"{mode:<22s}  {s['YES']:>5d}  {s['NO']:>5d}  {s['AMBIGUOUS']:>5d}  {total:>6d}")

    # Flagged rows (NO or AMBIGUOUS) — these are what the operator needs to
    # inspect / edit / drop.
    flagged = [(k, v) for k, v in results.items() if v["verdict"] != "YES"]
    if flagged:
        print()
        print(f"## Flagged rephrasings ({len(flagged)} non-YES verdicts)")
        for (mode, orig_idx, rephr_idx), entry in sorted(flagged):
            preview = entry["raw_response"][:120].replace("\n", " ")
            print(f"  {mode}[{orig_idx}].r{rephr_idx}  verdict={entry['verdict']:<9s}  "
                  f"judge={entry['model']}  raw={preview!r}")
    else:
        print()
        print("## No flagged rephrasings.")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache-dir", default=None,
                    help="Directory for cached judge responses. Defaults to "
                         "system tempdir/cdms_probes_review_cache.")
    ap.add_argument("--model", default=_PREFERRED_JUDGE,
                    help=f"Preferred judge model (default: {_PREFERRED_JUDGE}).")
    ap.add_argument("--fallback-model", default=_FALLBACK_JUDGE,
                    help=f"Fallback judge if preferred is unavailable "
                         f"(default: {_FALLBACK_JUDGE}).")
    ap.add_argument("--out-json", default=None,
                    help="Optional path to write full results as JSON.")
    args = ap.parse_args()

    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    results = review_rephrasings(
        cache_dir=cache_dir, model=args.model, fallback_model=args.fallback_model)
    _print_summary(results)

    if args.out_json:
        # Serialize tuple keys as "mode/orig_idx/rephr_idx" so they survive JSON.
        serializable = {
            f"{m}/{o}/{r}": v for (m, o, r), v in results.items()
        }
        Path(args.out_json).write_text(
            json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
        print(f"\n# wrote full results to {args.out_json}")


if __name__ == "__main__":
    main()
