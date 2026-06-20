#!/usr/bin/env python
"""Fan an experiment result + a question across a diverse LOCAL reviewer panel for independent,
cross-family critique. Corroboration across *different families* (Gemma, Phi, Qwen, Mistral) is
what makes a critique trustworthy; agreement within one family is weaker (shared priors).

deepcoder is intentionally excluded -- it returns empty/non-format output, useless as a judge.
The steering experiment's *subjects* (steering_experiment.py) are kept separate from this *review*
panel; qwen/mistral are reviewers only, for now.

Run:  python tools/review_panel.py --results path/to/output.txt [--question "..."]
      cat output.txt | python tools/review_panel.py            # results on stdin
"""
from __future__ import annotations

import argparse
import json
import sys
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from local_models import (                            # noqa: E402
    GEMMA4_12B, GEMMA4_12B_HERETIC, PHI4_14B_Q4, QWEN25_14B, MISTRAL_NEMO_LATEST,
)

OLLAMA = "http://localhost:11434"
REVIEWERS = {
    "gemma-std":    GEMMA4_12B,
    "heretic":      GEMMA4_12B_HERETIC,
    "phi4":         PHI4_14B_Q4,
    "qwen2.5-14b":  QWEN25_14B,
    "mistral-nemo": MISTRAL_NEMO_LATEST,  # was "mistral-nemo" (implicit :latest); normalized
}

DEFAULT_Q = (
    "You are a skeptical experimental-methods reviewer. Critique the RESULT and its stated "
    "interpretation hard; do not flatter. Cover, prioritized: (1) is the interpretation fair, "
    "over-, or under-stated? (2) the single biggest confound or design flaw; (3) the one change "
    "that would most improve the test; (4) the honest one-sentence conclusion the data supports. "
    "Answer in under 300 words, concrete."
)


def review(tag: str, prompt: str, n_predict: int = 650) -> str:
    payload = {"model": tag, "think": False, "stream": False,
               "messages": [{"role": "user", "content": prompt}],
               "options": {"temperature": 0.3, "num_predict": n_predict, "seed": 7}}
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=900).read()).get("message", {}).get("content", "(none)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", help="path to the result/output file (else read stdin)")
    ap.add_argument("--question", default=DEFAULT_Q)
    ap.add_argument("--reviewers", nargs="+", default=list(REVIEWERS),
                    help="subset of: " + ", ".join(REVIEWERS))
    args = ap.parse_args()

    results = open(args.results, encoding="utf-8").read() if args.results else sys.stdin.read()
    if not results.strip():
        print("no results provided (use --results FILE or pipe on stdin)", file=sys.stderr)
        return 2
    prompt = f"{args.question}\n\n===== RESULT TO REVIEW =====\n{results}"

    for label in args.reviewers:
        tag = REVIEWERS.get(label, label)
        print("\n" + "=" * 74 + f"\nREVIEWER: {label} ({tag})\n" + "=" * 74)
        t = time.time()
        try:
            print(f"[{time.time() - t:.0f}s init]\n" + review(tag, prompt))
        except Exception as e:
            print(f"FAILED: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
