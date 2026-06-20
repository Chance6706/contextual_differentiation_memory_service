"""Active Research "Dreaming" (CDMS-C) model selection -- which local model performs trait-driven
self-directed generative exploration (free-GPU / idle).

DISAMBIGUATION: this is **CDMS-C** (Active Research `"Dreaming"`), NOT CDMS-B (the read-time **Prose
Renderer** `"Dreaming"`; `Config.render_*` in `src/cdms/config.py`, used by `consolidate.py`). CDMS-B
narrates already-extracted gist tuples and is never authoritative; CDMS-C generates *synthetic*
exploratory content. The literal `render_*` / `research_*` split in code identifiers carries the
distinction; the umbrella term `"Dreaming"` stays scare-quoted in prose. See docs/DEVIATIONS.md L6
for the umbrella's three-way disambiguation (sleep / Hafner / DeepDream).

Forward-looking scaffolding for the Active Research `"Dreaming"` pillar (autonomy toggle, gated by
default; inactivity + free-GPU schedule; an exploration setting). No research-`"Dreaming"` runtime
exists yet -- this is the model-selection layer for when it's built.

*** SAFETY: the "research-`Dreaming` cannot poison" story is NOT YET ENFORCED. ***
A pressure-test (2026-06-19) found the invariant is currently fiction: no ingest path stamps synthetic
provenance, and even tagged-untrusted content still reaches recall/recent/salience/decay. Do NOT build a
research-`"Dreaming"` runtime until the must-haves in docs/research/RESEARCH_MODELS.md ("Safety
substrate") land. This module selects models and enforces nothing -- harmless on its own, dangerous
if wired naively.

Why the research model's needs differ from the steering SUBJECT: latency-tolerant + cost-sensitive
(runs on FREE GPU; the constraint is "don't compete with foreground work", not tok/s); diversity is
a FEATURE (rotate families for broader exploration -- but see the doc's caveat that this confounds
diversity with per-family quality); a coherence floor sets `min`. Tiers are the user's min / sweet /
best framing; selection is SCHEDULE- AND HOST-aware. Tags/footprints are Q4 -- VERIFY on Ollama
(they drift). NOTE: tags are duplicated from steering_experiment.py; a shared catalog
(tools/local_models.py) is a flagged follow-up to avoid drift.
"""
from __future__ import annotations

import itertools

# Approx single-model Q4 footprint (GB), WEIGHTS ONLY -- add KV-cache + context at runtime. Web-verified.
_FOOTPRINT_GB = {
    "qwen2.5:7b": 5, "llama3.1:8b": 5, "mistral:7b": 4, "gemma2:9b": 6,
    "qwen2.5:14b": 9, "qwen2.5:32b": 20, "gemma4:12b": 8, "phi4:14b-q4_K_M": 9, "mistral-nemo:latest": 7,
    "llama3.1:70b": 43, "qwen2.5:72b": 47, "mistral-large:latest": 73,
}
RESEARCH_TIERS = {
    "min": {   # coherence floor; cheap + frequent; fits the 4070 Ti (16GB) or spare GX10 headroom
        "why": "smallest model that still dreams coherently",
        "families": {"qwen2.5": "qwen2.5:7b", "llama3.1": "llama3.1:8b",
                     "mistral": "mistral:7b", "gemma2": "gemma2:9b"},
    },
    "sweet": {  # best exploration-quality per free-GPU cost -- the DEFAULT; 14B fits 4070 Ti, 32B -> GX10
        "why": "best exploration-quality per free-GPU cost",
        "families": {"qwen2.5": "qwen2.5:14b", "qwen2.5-32b": "qwen2.5:32b", "gemma4": "gemma4:12b",
                     "phi": "phi4:14b-q4_K_M", "mistral-nemo": "mistral-nemo:latest"},
    },
    "best": {   # deep-idle / overnight; richest exploration, slowest; GX10 only (won't fit 16GB)
        "why": "richest exploration for long idle windows (diminishing returns vs cost is OPEN)",
        "families": {"llama3.1-70b": "llama3.1:70b", "qwen2.5-72b": "qwen2.5:72b",
                     "mistral-large": "mistral-large:latest"},
    },
}
# Dreaming favors DIVERGENCE over precision (inverse of greedy subject/judge runs). OPEN: temperature
# likely should scale INVERSELY with tier coherence-risk (lower on `min`, higher on `best`), not be flat.
EXPLORATION_DEFAULTS = {"temperature": 0.9, "top_p": 0.95, "rotate_families": True}
# host -> max single-model GB it can load alone; the selector filters tiers/families to fit.
HOST_FIT = {"4070ti_16gb": 16, "gx10_128gb": 120}


def _fits(tag, max_model_gb):
    return max_model_gb is None or _FOOTPRINT_GB.get(tag, 1e9) <= max_model_gb


def research(tier="sweet", family=None, max_model_gb=None):
    """Resolve a research-`"Dreaming"` tag (family set) or one tag. Raises ValueError (not bare
    KeyError) on a bad key. With max_model_gb, the returned family map is filtered to models that fit
    the host."""
    if tier not in RESEARCH_TIERS:
        raise ValueError(f"unknown tier {tier!r}; choose from {list(RESEARCH_TIERS)}")
    fams = RESEARCH_TIERS[tier]["families"]
    if family is not None:
        if family not in fams:
            raise ValueError(f"unknown family {family!r} in tier {tier!r}; choose from {list(fams)}")
        return fams[family]
    return {f: t for f, t in fams.items() if _fits(t, max_model_gb)}


def rotate(tier="sweet", max_model_gb=None):
    """Infinite family-rotation iterator over the tier's fitting tags (the exploration knob).
    Empty iterator if nothing fits the host."""
    tags = list(research(tier, max_model_gb=max_model_gb).values())
    return itertools.cycle(tags) if tags else iter(())


def pick_for_budget(free_vram_gb, idle_minutes, max_model_gb=None):
    """Schedule- + host-aware tier choice. Returns the largest tier that BOTH meets the free-VRAM/idle
    gate AND has >=1 model fitting max_model_gb. Conservative: the `best` gate (80GB) exceeds a 123B's
    ~73GB weights so it can't be green-lit into an OOM; negative inputs are clamped. NOTE: free-VRAM
    and idle detection are unsolved on unified memory / a headless appliance (see doc) -- callers
    must supply trustworthy values, and there is NO preemption once a research-`"Dreaming"` run starts
    (also a doc must-have)."""
    free_vram_gb = max(0.0, float(free_vram_gb))
    idle_minutes = max(0.0, float(idle_minutes))
    for tier, (need_vram, need_idle) in (("best", (80, 30)), ("sweet", (12, 5)), ("min", (0, 0))):
        if not research(tier, max_model_gb=max_model_gb):    # no model in this tier fits the host
            continue
        if free_vram_gb >= need_vram and idle_minutes >= need_idle:
            return tier
    return "min"


if __name__ == "__main__":
    for tier, spec in RESEARCH_TIERS.items():
        fits16 = list(research(tier, max_model_gb=16))
        print(f"{tier:6} all={list(spec['families'])}  fits-4070Ti(16GB)={fits16}")
    print("exploration:", EXPLORATION_DEFAULTS)
    print("pick(8,2)=", pick_for_budget(8, 2),
          " pick(14,10,max16)=", pick_for_budget(14, 10, max_model_gb=16),     # 4070 Ti: no 32B/70B
          " pick(64,60,max120)=", pick_for_budget(64, 60, max_model_gb=120),   # GX10 idle, but <80 -> sweet
          " pick(96,60,max120)=", pick_for_budget(96, 60, max_model_gb=120))   # GX10 deep idle -> best
