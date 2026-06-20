"""Shared Ollama tag + Q4 footprint catalog — single source of truth for model identifiers
used across `tools/` (steering, research, tone, redteam, review).

Why this exists: prior to this catalog, the same literal tag (e.g. `"qwen2.5:14b"`) was
inlined in 6+ files. When Ollama re-quantizes a model or renames a tag, every file with the
literal needs to be updated — and missed sites are silent (the model just fails to pull).
This file is the registry: every `tools/` user imports the named constant from here, so a
tag drift is a one-line edit.

NOT a model manager: no caching, no Ollama-API queries, no auto-pull. **Verify tags on
Ollama before any batch run** — they drift. Q4_K_M is the default quant assumed everywhere
unless the constant name says otherwise.

Naming convention: `{FAMILY}{MAJOR}_{SIZE}[_{QUANT_OR_VARIANT}]`. Tag literals end in `:tag`
(typically `:Nb` or `:latest`).
"""
from __future__ import annotations

# ---- Tag constants (single source of truth) ----------------------------------
# Format: `<canonical-tag>:<size-tag>` as Ollama serves it. Verified for the build date
# (June 2026); re-verify on Ollama before a batch run if the model is load-bearing.
QWEN25_7B            = "qwen2.5:7b"
QWEN25_14B           = "qwen2.5:14b"
QWEN25_32B           = "qwen2.5:32b"
QWEN25_72B           = "qwen2.5:72b"

LLAMA31_8B           = "llama3.1:8b"
LLAMA31_70B          = "llama3.1:70b"

GEMMA2_9B            = "gemma2:9b"
GEMMA4_12B           = "gemma4:12b"
GEMMA4_12B_HERETIC   = "igorls/gemma-4-12B-it-heretic-GGUF:latest"  # abliterated; for control-arm runs only

PHI4_14B_Q4          = "phi4:14b-q4_K_M"

MISTRAL_7B           = "mistral:7b"
MISTRAL_NEMO_LATEST  = "mistral-nemo:latest"
MISTRAL_LARGE_123B   = "mistral-large:latest"

MIXTRAL_8X22B        = "mixtral:8x22b"          # ~141B total / ~39B active (MoE)
COMMAND_R_PLUS_104B  = "command-r-plus:latest"  # dense ~104B

# ---- Q4_K_M single-model footprint (GB, WEIGHTS ONLY) ------------------------
# Add KV-cache + context headroom at runtime. Drifts when Ollama re-quantizes.
# Used by `tools/research_models.py` and any host-fit checks. Web-verified for the build date.
FOOTPRINT_GB = {
    QWEN25_7B: 5, QWEN25_14B: 9, QWEN25_32B: 20, QWEN25_72B: 47,
    LLAMA31_8B: 5, LLAMA31_70B: 43,
    GEMMA2_9B: 6, GEMMA4_12B: 8,
    PHI4_14B_Q4: 9,
    MISTRAL_7B: 4, MISTRAL_NEMO_LATEST: 7, MISTRAL_LARGE_123B: 73,
}

# ---- Recurring panels (composed from the constants above) --------------------
# The 12-14B "small" panel: the basis of every steering / poisoning / tone finding so
# far. Duplicated previously across `steering_experiment.SUBJECTS`,
# `redteam_layer3_full.PANEL`, `redteam_layer3_validate.PANEL`, and effectively
# `redteam_pressure_test.PANEL` (which extended SUBJECTS with tags SUBJECTS already had).
SMALL_PANEL = {
    "gemma-std":    GEMMA4_12B,
    "heretic":      GEMMA4_12B_HERETIC,
    "phi4":         PHI4_14B_Q4,
    "qwen2.5":      QWEN25_14B,
    "mistral-nemo": MISTRAL_NEMO_LATEST,
}
