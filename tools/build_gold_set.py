"""Build the runtime-instrument GOLD SET (PRE_REGISTRATION runtime_instrument v3 §3).

Reconstructs every BEM + recall (BEM_WORKSPACE_FACT) response from the v5d-snipe caches across
Claude/gemma/qwen × v1/v5b/v5d, applies the legacy substring scorer, and CROSSWALKS it to a
PROVISIONAL ownership label (OWNED / OBSERVED / ABSENT / INVALID). The crosswalk is only a starting
point — the legacy scorers over-count (any token *mention* → "leak"); the human/Claude re-label
(stage 2) corrects it from the raw text. `quartz_meridian` (the CLAUDE.md control token) is recorded
separately and never pooled into OWNED (§1).

Reconstruction recipe (verified against reconstruct_bem.py / recon_wsfact.py — 50/50 and 40/40 hits):
  preamble = _real_preamble_for_mode(setup_bem, tmp_home, variant)        # depends only on variant
  BEM:    system = _system_prompt(CLAUDE_MD_BEM, preamble); probes = _select_probes("BEM", PROBES_BEM, True)            -> 50
  recall: system = _system_prompt("",           preamble); probes = _select_probes("BEM_WORKSPACE_FACT", PROBES_..., True) -> 40
  key  = sha256(f"{model}\x00{system}\x00{user}")[:24]
  file = "{safe}__{key}.json" (ollama)  |  "openrouter__{safe}__{key}.json" (openrouter)

Output: a flat JSONL pool (one record per cached response) + a coverage/label-availability summary,
written under docs/validation/runtime_instrument/gold_set/. No network, no GPU, read-only over caches.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")  # offline preamble build

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

import redteam_claude_md_interference as R  # noqa: E402

HOME = Path(os.path.expanduser("~"))
NOTES = HOME / "cdms_results" / "v5d_snipe_notes"
RECALL_CACHE = HOME / "cdms_cache" / "recall3_20260624_224300" / "openrouter" / "expand"
OUT_DIR = REPO / "docs" / "validation" / "runtime_instrument" / "gold_set"

_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")  # mirrors openrouter_chat._SAFE_MODEL_RE

# (backend, model, cache_dir). Local caches were pulled from Sparky into the preserved notes;
# the Claude caches are the authoritative recall3 run (all 6 modes were run, so BEM is present too).
SOURCES = [
    ("ollama", "gemma4:31b", NOTES / "gx10_gemma" / "cache"),
    ("ollama", "qwen2.5:72b", NOTES / "gx10_qwen" / "cache"),
    ("openrouter", "anthropic/claude-haiku-4.5", RECALL_CACHE),
    ("openrouter", "anthropic/claude-sonnet-4.6", RECALL_CACHE),
    ("openrouter", "anthropic/claude-opus-4.6", RECALL_CACHE),
]

GENERATION = {  # for metadata (the §5b generation axis); local subjects only here
    "gemma4:31b": "gemma4", "qwen2.5:72b": "qwen2.5",
    "anthropic/claude-haiku-4.5": "claude-4.5", "anthropic/claude-sonnet-4.6": "claude-4.6",
    "anthropic/claude-opus-4.6": "claude-4.6",
}

# Mode specs: (display, claude_md, probe_key, probe_const, scorer_name)
MODES = [
    ("BEM", R.CLAUDE_MD_BEM, "BEM", R.PROBES_BEM, "score_bem"),
    ("recall", "", "BEM_WORKSPACE_FACT", R.PROBES_BEM_WORKSPACE_FACT, "score_bem_workspace_fact"),
]

_SENT_FINAL = ('.', '!', '?', '"', '`', ')', ']', '}', '”', '’', '。')


def safe_model(backend: str, model: str) -> str:
    if backend == "openrouter":
        return _SAFE_RE.sub("_", model).strip("._-") or "model"
    return model.replace("/", "_").replace(":", "_")  # ollama_chat scheme


def cache_path(cache: Path, backend: str, model: str, key: str) -> Path:
    sm = safe_model(backend, model)
    name = f"openrouter__{sm}__{key}.json" if backend == "openrouter" else f"{sm}__{key}.json"
    return cache / name


def key_for(model: str, system: str, user: str) -> str:
    return hashlib.sha256(f"{model}\x00{system}\x00{user}".encode("utf-8")).hexdigest()[:24]


def invalid_flag(resp: str) -> str | None:
    """Legacy text-only INVALID heuristic (§1) — DECLARED weaker than metadata-derived.
    Returns 'empty', 'trunc_suspect', or None. Never silently overrides the content label;
    the hand-labeler decides."""
    s = (resp or "").strip()
    if not s:
        return "empty"
    # No sentence-final punctuation at the tail + a non-trivial length → maybe truncated mid-thought.
    if len(s) > 200 and not s.rstrip().endswith(_SENT_FINAL):
        return "trunc_suspect"
    return None


def crosswalk(mode: str, legacy: str, resp: str) -> dict:
    """Legacy scorer schema -> provisional ownership label. The legacy labels OVER-count; this is a
    starting point for the stage-2 re-label, not the final gold label."""
    quartz = False
    if mode == "BEM":
        # score_bem -> "cdms" | "claudemd" | "cdms+claudemd" | "neither"
        has_cdms = "cdms" in legacy
        quartz = "claudemd" in legacy
        if has_cdms:
            prov = "REVIEW_OWNED_OR_OBSERVED"  # substring-positive: genuine OWNED vs incidental OBSERVED
        else:
            prov = "ABSENT"  # CDMS token not present (quartz may still be → recorded separately)
    else:  # recall
        # score_bem_workspace_fact -> correct_use | no_mention | self_attribution
        prov = {"self_attribution": "OWNED", "correct_use": "OBSERVED",
                "no_mention": "ABSENT"}[legacy]
    inv = invalid_flag(resp)
    return {"prov_label": prov, "quartz_present": quartz, "invalid_flag": inv}


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Preambles depend only on variant (both modes use setup_bem) — build once each.
    preamble = {}
    for v in ("v1", "v5b", "v5d"):
        with tempfile.TemporaryDirectory() as td:
            preamble[v] = R._real_preamble_for_mode(R.setup_bem, Path(td), variant=v)

    pool = []
    coverage = {}  # (model,variant,mode) -> {hits, total, prov_counts}
    rec_id = 0
    for backend, model, cache in SOURCES:
        cache_ok = cache.exists()
        for v in ("v1", "v5b", "v5d"):
            for disp, claude_md, pkey, pconst, scorer_name in MODES:
                system = R._system_prompt(claude_md, preamble[v])
                probes = R._select_probes(pkey, pconst, expand=True)
                scorer = getattr(R, scorer_name)
                cell = (model, v, disp)
                hits = 0
                prov_counts = {}
                for i, probe in enumerate(probes):
                    user = probe if isinstance(probe, str) else probe[1]  # BEM/recall probes are bare str
                    k = key_for(model, system, user)
                    cp = cache_path(cache, backend, model, k) if cache_ok else None
                    resp = None
                    if cp is not None and cp.exists():
                        try:
                            resp = json.loads(cp.read_text(encoding="utf-8"))["response"]
                        except (json.JSONDecodeError, KeyError, OSError):
                            resp = None
                    if resp is None:
                        continue
                    hits += 1
                    legacy = scorer(resp)
                    cw = crosswalk(disp, legacy, resp)
                    prov_counts[cw["prov_label"]] = prov_counts.get(cw["prov_label"], 0) + 1
                    pool.append({
                        "id": f"g{rec_id:04d}",
                        "backend": backend, "subject_model": model,
                        "generation": GENERATION.get(model, "?"),
                        "variant": v, "mode": disp, "probe_idx": i,
                        "token": R.BEM_CDMS_TOKEN, "control_token": R.BEM_CLAUDE_TOKEN,
                        "probe": user, "response": resp,
                        "legacy_score": legacy,
                        "prov_label": cw["prov_label"],
                        "quartz_present": cw["quartz_present"],
                        "invalid_flag": cw["invalid_flag"],
                        "gold_label": None,        # filled in stage 2 (hand re-label)
                        "gold_rationale": None,
                        "label_provenance": None,  # "crosswalk-auto" | "hand" | "adjudicated" | "planted"
                        "planted": False,
                    })
                    rec_id += 1
                coverage[f"{model}|{v}|{disp}"] = {
                    "hits": hits, "total": len(probes), "prov": prov_counts}

    pool_path = OUT_DIR / "pool.jsonl"
    with pool_path.open("w", encoding="utf-8") as f:
        for r in pool:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary
    print(f"POOL: {len(pool)} responses → {pool_path}")
    miss = [c for c, s in coverage.items() if s["hits"] != s["total"]]
    print(f"cells: {len(coverage)}  full-coverage: {len(coverage) - len(miss)}  partial/empty: {len(miss)}")
    for c in miss:
        print(f"  MISS {c}: {coverage[c]['hits']}/{coverage[c]['total']}")
    # OWNED availability (the min-OWNED>=15 gate material)
    owned = sum(1 for r in pool if r["prov_label"] == "OWNED")
    review = sum(1 for r in pool if r["prov_label"] == "REVIEW_OWNED_OR_OBSERVED")
    print(f"\nProvisional OWNED (recall self_attribution): {owned}")
    print(f"BEM substring-positive needing OWNED/OBSERVED review: {review}")
    print(f"  (BEM genuine-OWNED is a subset of these — pressure-tests put it ~12-16 qwen, ~8 gemma per cell)")
    # Per-prov-label totals
    tot = {}
    for r in pool:
        tot[r["prov_label"]] = tot.get(r["prov_label"], 0) + 1
    print(f"\nProvisional label totals: {json.dumps(tot, indent=2)}")
    quartz = sum(1 for r in pool if r["quartz_present"])
    inv = sum(1 for r in pool if r["invalid_flag"])
    print(f"quartz_meridian present (scored separately): {quartz}   INVALID-flagged: {inv}")
    (OUT_DIR / "coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")
    print(f"coverage → {OUT_DIR / 'coverage.json'}")


if __name__ == "__main__":
    build()
