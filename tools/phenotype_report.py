"""Phenotype recall-quality + cost report for the enriched-phenotype landing.

Grows the four individuation archetypes through the full pipeline (reusing the
individuation experiment's persona scripts + fixed per-name seeds), then for each
persona:

  - renders the SessionStart phenotype three ways — GATED enriched default
    (exemplars on, bounded to top-N), enriched-UNBOUNDED (every gist), and terse
    (exemplars off) — and reports char/approx-token cost + the delta, so the
    bounded-vs-unbounded preamble cost is explicit;
  - runs a RECALL PROBE (a domain query that should surface that persona's own
    gist tier) under the enriched default, to confirm enrichment doesn't degrade
    recall;
  - reports whether the flashbulb floor elevated a real catastrophe to a guardrail.

Fully offline (no LLM). Deterministic given the embedder. Run:

    python tools/phenotype_report.py            # real CPU embedder
    CDMS_EMBED_BACKEND=hash python tools/phenotype_report.py   # fast/offline
"""

from __future__ import annotations

import hashlib
import os
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cdms.config import Config                       # noqa: E402
from cdms.consolidate import Consolidator            # noqa: E402
from cdms.embeddings import get_embedder             # noqa: E402
from cdms.hooks import _session_start_context        # noqa: E402
from cdms.store import MemoryService                 # noqa: E402

from individuation_experiment import NOW, PERSONAS, gen_history  # noqa: E402

N = 220                       # turns per persona (matches the individuation run scale)
TOP_N = Config().recall_exemplar_top_n     # the landed default bound


def approx_tokens(s: str) -> int:
    return round(len(s) / 6.5)


# A domain query per persona; the persona's own gist tier should surface for it.
PROBES = {
    "tessa_tdd": "stripe webhook idempotency key",
    "cole_cowboy": "checkout page bundle size",
    "dex_unity_struggler": "hex grid shader compile error",
    "uma_unity_careful": "profile the shader edit-mode test",
}


def build(name: str, spec: dict, root: Path, embedder):
    cfg = Config(home=root / name)          # flashbulb floor ON by default
    cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    rng = random.Random(int(hashlib.blake2b(name.encode("utf-8"), digest_size=4).hexdigest(), 16))
    for ev in gen_history(name, spec, N, span_days=40, rng=rng):
        svc.ingest(ev)
    Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW)
    return cfg, svc


def render(cfg, payload, *, exemplars: bool, top_n: int) -> str:
    cfg.recall_exemplars = exemplars        # rendering toggle (exemplar already stored at consolidation)
    cfg.recall_exemplar_top_n = top_n
    return _session_start_context(cfg, payload)


def main() -> int:
    backend = os.environ.get("CDMS_EMBED_BACKEND", "real(bge-small)")
    embedder = get_embedder(Config())
    root = Path(tempfile.mkdtemp(prefix="cdms_phenotype_"))
    print(f"# Enriched-phenotype recall-quality + cost report")
    print(f"embedder={backend}  N={N}/persona  exemplar_top_n={TOP_N}  flashbulb_floor=ON\n")

    print(f"{'persona':22}{'terse':>8}{'bounded':>9}{'unbnd':>8}   {'Δbounded':>9}{'Δunbnd':>8}  scars")
    print("-" * 78)
    built = {}
    for name, spec in PERSONAS.items():
        cfg, svc = build(name, spec, root, embedder)
        payload = {"cwd": spec["project"]}
        terse = render(cfg, payload, exemplars=False, top_n=0)
        bounded = render(cfg, payload, exemplars=True, top_n=TOP_N)
        unbnd = render(cfg, payload, exemplars=True, top_n=10_000)
        n_scar = svc.db.stats()["scars"]
        tt, tb, tu = approx_tokens(terse), approx_tokens(bounded), approx_tokens(unbnd)
        db = (tb / tt - 1) * 100 if tt else 0
        du = (tu / tt - 1) * 100 if tt else 0
        print(f"{name:22}{tt:8d}{tb:9d}{tu:8d}   {db:8.0f}%{du:7.0f}%  {n_scar}")
        built[name] = (cfg, svc, spec, payload, terse, bounded, unbnd)

    # ---- recall probe: enrichment must not degrade gist recall ----
    print("\n## Recall probe (enriched default) — domain query must surface the persona's gist tier")
    for name, (cfg, svc, spec, payload, *_rest) in built.items():
        hits = svc.retrieve(PROBES[name], tiers=("gist",), project=spec["project"])
        own = [h for h in hits if h.payload.get("subject") == spec["project"].rstrip("/").split("/")[-1]]
        top = hits[0] if hits else None
        ok = "OK " if own else "MISS"
        topr = (top.text if top else "—")
        print(f"  [{ok}] {name:22} probe={PROBES[name]!r}")
        print(f"        top gist: {topr[:90]}")

    # ---- full phenotypes under the landed default (tessa + cole) ----
    for name in ("tessa_tdd", "cole_cowboy"):
        cfg, svc, spec, payload, terse, bounded, unbnd = built[name]
        print(f"\n{'='*78}\n## FULL PHENOTYPE (enriched default, top_n={TOP_N}): {name}\n{'='*78}")
        print(bounded)

    for _n, (_c, svc, *_r) in built.items():
        svc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
