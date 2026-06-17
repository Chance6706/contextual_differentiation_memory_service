"""Central configuration for the Contextual Differentiation Memory Service.

Every cognitive parameter from the design spec lives here so the "genotype"
(the discard policy that shapes identity) is tunable in one place. Values may be
overridden via environment variables prefixed with ``CDMS_`` or a JSON file at
``$CDMS_HOME/config.json``.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field, fields
from pathlib import Path


def _default_home() -> Path:
    """Resolve the memory home directory.

    Spec calls for ``~/.local_memory``. Overridable with ``CDMS_HOME`` so the
    service can be scoped per-project or relocated.
    """
    env = os.environ.get("CDMS_HOME")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".local_memory"


@dataclass
class Config:
    # ---- Storage -----------------------------------------------------------
    home: Path = field(default_factory=_default_home)
    db_filename: str = "memory.db"

    # ---- Embeddings (CPU-only ONNX; 0 GPU VRAM) ----------------------------
    # NOTE: The design doc said 768-dim with all-MiniLM-L6-v2. That is internally
    # inconsistent — MiniLM-L6-v2 emits 384 dims. We default to a 384-dim model
    # (BAAI/bge-small-en-v1.5, fastembed's default) which is fast, ~133MB, and
    # high quality on CPU. EMBED_DIM is baked into the vec0 tables at init time.
    embed_model: str = "BAAI/bge-small-en-v1.5"
    embed_dim: int = 384

    # ---- Write-time salience gating  S0 = G*(S + C + W + A) -----------------
    # Component weights let the genotype emphasize different drivers of memorability.
    w_surprise: float = 1.0      # novelty / prediction error proxy
    w_contingency: float = 1.0   # did our action change the world (tests passed, etc.)
    w_self_ref: float = 1.0      # touches the agent's own rules/preferences/identity
    w_affect: float = 1.0        # emotional valence intensity
    # Goal-relevance is a multiplicative VETO gate in [0,1]; a floor avoids
    # totally zeroing-out memories when goal signal is merely absent (vs. negative).
    goal_gate_floor: float = 0.25

    # ---- Ebbinghaus decay   A(m,t) = S0 * e^(-λt) * min(α^c, Cap) -----------
    decay_halflife_days: float = 29.0   # λ derived from this; keeps active issues alive ~weeks
    reinforce_alpha: float = 1.15       # retrieval-induced strengthening base (testing effect)
    reinforce_cap: float = 2.0          # attentional ceiling on a single hot memory
    retention_floor: float = 0.10       # s_floor: below this accessibility, an episode is evictable

    # ---- Consolidation ("sleep") -------------------------------------------
    crisis_threshold: float = 3.0       # s_crisis: S0 >= this is a candidate for scar elevation
    crisis_valence_max: float = -0.4    # ...but only if valence <= this (scars are negative crises)
    salience_budget: float = 1000.0     # K_budget: total conserved salience across all live episodes
    project_budget_cap: float = 0.5     # no single project/subject may hold > this fraction of K
                                        # (capped-proportional: primaries keep focus, smalls aren't starved)
    assoc_eta: float = 0.20             # η: retroactive association boost coefficient
    assoc_sim_floor: float = 0.60       # only boost past episodes more similar than this
    cluster_sim_threshold: float = 0.78 # cosine link threshold for gist clustering
    gist_match_sim_threshold: float = 0.90  # reinforce an EXISTING gist whose episode-space
                                        # centroid is at least this close (vocabulary-independent
                                        # identity), instead of spawning a near-duplicate sibling
    dedup_sim_threshold: float = 0.95   # near-duplicate episodes above this are merged/superseded
    min_cluster_support: int = 2        # a gist tuple needs >= this many supporting episodes
    rest_idle_minutes: float = 20.0     # idle gap that marks a "rest boundary" for auto-consolidation

    # ---- L2 gist plasticity (hybrid: valence-flip + gentle activity decay) ---
    gist_valence_ema: float = 0.4       # weight of new evidence when updating a trait's valence
    # Gist decay is measured in CONSOLIDATION CYCLES (activity), NOT wall-clock time:
    # being away from the keyboard for a month must NOT age your identity. A trait
    # only fades through many *active* sessions in which it is never reinforced.
    gist_decay_per_cycle: float = 0.985 # gentle: per-cycle strength multiplier for idle traits
    gist_retention_floor: float = 0.25  # evict only after a trait has faded well below 1 support
    relation_pos_threshold: float = 0.15   # valence above -> "handles_well"
    relation_neg_threshold: float = -0.15  # valence below -> "has_trouble_with"

    # ---- Retrieval ---------------------------------------------------------
    default_top_k: int = 8
    rrf_k: int = 60                     # reciprocal-rank-fusion constant for hybrid search

    # ---- Input bounds ------------------------------------------------------
    # Cap stored field length so a single huge note (MCP `store`, a multi-MB tool
    # dump) cannot freeze the server on embedding or bloat the DB. Generous enough
    # for any real turn; hook capture already pre-truncates via _brief.
    max_field_chars: int = 4000

    # ---- Optional local "Dreamer" LLM (prose rendering only; never authoritative) ---
    dreamer_enabled: bool = False
    dreamer_base_url: str = "http://127.0.0.1:8081/v1"
    dreamer_model: str = "llama-3.2-3b-instruct"
    dreamer_api_key: str = "sk-no-key-required"

    # ---- Networking / security (loopback only; directive #2) ---------------
    http_host: str = "127.0.0.1"
    http_port: int = 8765

    # -- derived -------------------------------------------------------------
    @property
    def db_path(self) -> Path:
        return self.home / self.db_filename

    @property
    def decay_lambda(self) -> float:
        """λ such that e^(-λ * halflife) = 0.5."""
        return math.log(2.0) / self.decay_halflife_days

    def relation_from_valence(self, v: float) -> str:
        """Derive a trait's relation from its current running valence (enables flips)."""
        if v > self.relation_pos_threshold:
            return "handles_well"
        if v < self.relation_neg_threshold:
            return "has_trouble_with"
        return "frequently_works_on"

    @property
    def queue_path(self) -> Path:
        """Append-only NDJSON spool written by fast hooks, drained by the daemon."""
        return self.home / "episodic_queue.ndjson"

    @property
    def log_path(self) -> Path:
        return self.home / "cdms.log"

    @property
    def state_path(self) -> Path:
        """Small JSON file for daemon state (last activity, last consolidation)."""
        return self.home / "state.json"

    def ensure_home(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)


_ENV_COERCE = {
    int: lambda s: int(s),
    float: lambda s: float(s),
    bool: lambda s: s.strip().lower() in ("1", "true", "yes", "on"),
    str: lambda s: s,
    Path: lambda s: Path(s).expanduser(),
}


def load_config() -> Config:
    """Build config from defaults, optional JSON file, then ``CDMS_`` env overrides."""
    cfg = Config()

    # JSON file overrides (if present)
    cfg_file = cfg.home / "config.json"
    if cfg_file.exists():
        try:
            data = json.loads(cfg_file.read_text(encoding="utf-8"))
            for f in fields(cfg):
                if f.name in data:
                    setattr(cfg, f.name, data[f.name])
        except (json.JSONDecodeError, OSError):
            pass  # never let a bad config file crash the daemon

    # Environment overrides take final precedence
    for f in fields(cfg):
        env_key = f"CDMS_{f.name.upper()}"
        if env_key not in os.environ:
            continue
        raw = os.environ[env_key]
        current = getattr(cfg, f.name)
        try:
            if isinstance(current, Path):
                setattr(cfg, f.name, Path(raw).expanduser())
            elif isinstance(current, bool):
                setattr(cfg, f.name, raw.strip().lower() in ("1", "true", "yes", "on"))
            elif isinstance(current, int):
                setattr(cfg, f.name, int(raw))
            elif isinstance(current, float):
                setattr(cfg, f.name, float(raw))
            else:
                setattr(cfg, f.name, raw)
        except (ValueError, TypeError):
            pass

    return cfg
