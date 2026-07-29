#!/usr/bin/env python3
"""Instrument-version capture for LOCALJUDGE-2 (pressure-test SHOULD_FIX 4 / LJ-1 LJ-F7).

Records each model's digest + size from ollama's /api/tags (where the per-model digest
actually lives — /api/show, which local_judge.py:LJ-F7 read, returns neither for a normal
model, which is why LJ-1 recovered digests post-hoc). Operational, not results-determining:
run once at lock for the roster snapshot, and once per model in the run driver.

Usage:  localjudge2_digest.py [--url http://localhost:11434] [--out digests.json] [models...]
        (no models → snapshot the entire local library)
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path


def fetch_tags(url: str) -> dict:
    with urllib.request.urlopen(f"{url}/api/tags", timeout=30) as r:
        data = json.loads(r.read())
    out = {}
    for m in data.get("models", []):
        out[m["name"]] = {"digest": (m.get("digest") or "")[:12],
                          "size": m.get("size"),
                          "modified": m.get("modified_at"),
                          "family": (m.get("details") or {}).get("family"),
                          "param_size": (m.get("details") or {}).get("parameter_size"),
                          "quant": (m.get("details") or {}).get("quantization_level")}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("models", nargs="*", help="restrict to these model tags (default: all)")
    ap.add_argument("--url", default="http://localhost:11434")
    ap.add_argument("--out", help="write JSON here (default: stdout)")
    args = ap.parse_args()

    tags = fetch_tags(args.url)
    if args.models:
        missing = [m for m in args.models if m not in tags]
        if missing:
            print(f"WARNING: not resident: {missing}", file=sys.stderr)
        tags = {m: tags[m] for m in args.models if m in tags}
    body = json.dumps(tags, indent=1)
    if args.out:
        Path(args.out).write_text(body, encoding="utf-8")
        print(f"{len(tags)} model digests -> {args.out}")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
