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
    scar_dedup_sim_threshold: float = 0.95  # near-identical scars (same project) are deduped on
                                        # insert so a recurring crisis can't grow the L3 table forever
    scar_project_cap: int = 100         # max AUTO-ELEVATED scars kept per project; the oldest
                                        # auto-elevated ones beyond this are evicted at consolidation.
                                        # Deliberately PINNED scars (origin=='pinned') are guardrails:
                                        # exempt, never counted, never evicted (Cycle-8 H-4).
    vacuum_after_deletes: int = 5000    # VACUUM to reclaim free pages once a pass deletes at least
                                        # this many rows (secure_delete scrubs content; VACUUM frees
                                        # the pages so the file can't bloat 2-3x). 0 disables (Cycle-8 M-S-1).
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

    # ---- Temperament (§8) genotype: which archetype seeds a NEW store -------
    # Phase 0 of the §8.7 chain: the temperament vector is seeded ONCE at first
    # init from this archetype (one of the §8.5 presets). It does not retro-change
    # an existing store. Must be a known archetype (validated below).
    archetype_default: str = "co-pilot"

    # ---- Retrieval ---------------------------------------------------------
    default_top_k: int = 8
    rrf_k: int = 60                     # reciprocal-rank-fusion constant for hybrid search

    # ---- Input bounds ------------------------------------------------------
    # Cap stored field length so a single huge note (MCP `store`, a multi-MB tool
    # dump) cannot freeze the server on embedding or bloat the DB. Generous enough
    # for any real turn; hook capture already pre-truncates via _brief.
    max_field_chars: int = 4000
    # Cap the text actually fed to the embedder. The bge-small model truncates at
    # ~512 tokens (~2k chars) SILENTLY, dropping the salient tail and making long
    # inputs with different tails collide to the same vector. We truncate explicitly
    # at a single controlled point (both backends) so embedding is bounded and the
    # truncation is intentional rather than a hidden model limit. Stays under the
    # model window; the full text is still kept in storage + the FTS/BM25 arm.
    embed_max_chars: int = 1600
    # Hard cap on the unconsolidated spool file. If the daemon's drain never runs
    # (misconfig), the spool would otherwise grow without bound until a drain OOMs
    # on it (8.7x RSS amplification). Above this size new events are shed (dropped
    # with a stderr warning) so disk stays bounded and the store stays recoverable.
    spool_max_bytes: int = 100_000_000  # ~100 MB

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

    @property
    def lock_path(self) -> Path:
        """Advisory lock serializing whole-pass writers (consolidate / forget)
        across processes (hook vs cron vs daemon) on the shared store."""
        return self.home / "consolidate.lock"

    def ensure_home(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)


_ENV_COERCE = {
    int: lambda s: int(s),
    float: lambda s: float(s),
    bool: lambda s: s.strip().lower() in ("1", "true", "yes", "on"),
    str: lambda s: s,
    Path: lambda s: Path(s).expanduser(),
}


def _coerce(current, value):
    """Coerce a JSON/env value to the type of the field's current (default) value."""
    if isinstance(current, bool):
        return value if isinstance(value, bool) else str(value).strip().lower() in ("1", "true", "yes", "on")
    # A JSON bool must not silently coerce to a numeric field (e.g. "embed_dim": true ->
    # int(True) == 1, a valid-looking dim). Reject it so load_config keeps the default and
    # _validate's bool guard never even sees it (Cycle-8 L-5).
    if isinstance(value, bool):
        raise ValueError("refusing to coerce a bool to a non-bool field")
    if isinstance(current, Path):
        return Path(str(value)).expanduser()
    if isinstance(current, int):
        return int(value)
    if isinstance(current, float):
        return float(value)
    return value if isinstance(value, str) else str(value)


def _validate(cfg: "Config") -> None:
    """Clamp out-of-range/nonsensical values to their defaults, loudly.

    A single bad value (a stringified number from JSON, K=0, decay>=1, a negative
    dim) otherwise silently bricks the store or wipes memory. We repair to the
    default and warn on stderr rather than corrupt or crash.
    """
    import sys as _sys

    # A finite real number (rejects NaN/inf and bool). inf otherwise sneaks past a
    # bare ``v > 0`` check: e.g. CDMS_DECAY_HALFLIFE_DAYS=inf -> decay_lambda=0 ->
    # identity never ages/evicts (silent freeze + unbounded growth), and a huge
    # max_field_chars re-opens the DoS cap. Every numeric field now also has a sane
    # UPPER bound so an astronomically large value can't disable a guard.
    def _num(v) -> bool:
        return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)

    d = Config()
    checks = [
        ("embed_dim", lambda v: isinstance(v, int) and 1 <= v <= 8192),
        ("salience_budget", lambda v: _num(v) and 0 < v <= 1e9),
        ("project_budget_cap", lambda v: _num(v) and 0 < v <= 1),
        ("gist_decay_per_cycle", lambda v: _num(v) and 0 < v < 1),
        ("gist_retention_floor", lambda v: _num(v) and 0 <= v <= 1e6),
        ("retention_floor", lambda v: _num(v) and 0 <= v <= 1e6),
        ("reinforce_alpha", lambda v: _num(v) and 1.0 < v <= 1e3),
        ("reinforce_cap", lambda v: _num(v) and 1.0 <= v <= 1e6),
        ("decay_halflife_days", lambda v: _num(v) and 0 < v <= 1e6),
        ("max_field_chars", lambda v: isinstance(v, int) and 1 <= v <= 1_000_000),
        ("embed_max_chars", lambda v: isinstance(v, int) and 1 <= v <= 1_000_000),
        ("spool_max_bytes", lambda v: isinstance(v, int) and 1_000 <= v <= 10_000_000_000),
        ("min_cluster_support", lambda v: isinstance(v, int) and 1 <= v <= 1_000_000),
        ("gist_valence_ema", lambda v: _num(v) and 0 < v <= 1),
        ("scar_dedup_sim_threshold", lambda v: _num(v) and 0 < v <= 1),
        ("rrf_k", lambda v: isinstance(v, int) and 1 <= v <= 1_000_000),
        ("default_top_k", lambda v: isinstance(v, int) and 1 <= v <= 1_000_000),
        # Cycle-4 A7-H1: the S0 weights and the remaining thresholds were unvalidated,
        # so a single env var (e.g. CDMS_W_SURPRISE=1e9, CDMS_DEDUP_SIM_THRESHOLD=2.0)
        # could disable the salience gate or dedup. Bound them all.
        # S0 weights are meant to be O(1); cap at 10 (Cycle-8 H-2 — even 1e3 let a single
        # weight push S0 to ~250 with goal=0, 83x the crisis threshold). A cross-field check
        # below additionally bounds them against goal_gate_floor × crisis_threshold.
        ("w_surprise", lambda v: _num(v) and 0 <= v <= 10),
        ("w_contingency", lambda v: _num(v) and 0 <= v <= 10),
        ("w_self_ref", lambda v: _num(v) and 0 <= v <= 10),
        ("w_affect", lambda v: _num(v) and 0 <= v <= 10),
        ("goal_gate_floor", lambda v: _num(v) and 0 <= v <= 1),
        ("assoc_eta", lambda v: _num(v) and 0 <= v <= 1e3),
        ("assoc_sim_floor", lambda v: _num(v) and 0 <= v <= 1),
        ("cluster_sim_threshold", lambda v: _num(v) and 0 <= v <= 1),
        ("gist_match_sim_threshold", lambda v: _num(v) and 0 <= v <= 1),
        ("dedup_sim_threshold", lambda v: _num(v) and 0 < v <= 1),
        ("crisis_threshold", lambda v: _num(v) and 0 <= v <= 1e6),
        ("crisis_valence_max", lambda v: _num(v) and -1 <= v <= 1),
        ("relation_pos_threshold", lambda v: _num(v) and -1 <= v <= 1),
        ("relation_neg_threshold", lambda v: _num(v) and -1 <= v <= 1),
        ("rest_idle_minutes", lambda v: _num(v) and 0 < v <= 1e6),
        ("http_port", lambda v: isinstance(v, int) and 1 <= v <= 65535),
        # db_filename joins CDMS_HOME to form db_path; a value with a directory component
        # ("../../etc/x", "/abs/path", a backslash on POSIX) would escape the home and let
        # an env var write the store outside its sandbox. Require a bare filename — the
        # basename must equal the value, with no separators or traversal.
        ("db_filename", lambda v: (isinstance(v, str) and v not in ("", ".", "..")
                                   and "\\" not in v and os.path.basename(v) == v)),
        ("scar_project_cap", lambda v: isinstance(v, int) and 1 <= v <= 1_000_000),
        ("vacuum_after_deletes", lambda v: isinstance(v, int) and 0 <= v <= 1_000_000),
    ]
    for name, ok in checks:
        val = getattr(cfg, name)
        if isinstance(val, bool) or not ok(val):  # bool sneaks past int/float checks
            print(f"cdms config: invalid {name}={val!r}; using default {getattr(d, name)!r}", file=_sys.stderr)
            setattr(cfg, name, getattr(d, name))

    # Cross-field consistency (Cycle-4 A7-L1): each field can be in-range yet jointly
    # nonsensical. Repair MINIMALLY (clamp the offender) so a deliberately-tuned valid
    # field isn't clobbered (double-review M1) — and warn.
    def _clamp(field_name: str, new_val, why: str) -> None:
        if getattr(cfg, field_name) != new_val:
            print(f"cdms config: {why}; clamping {field_name} "
                  f"{getattr(cfg, field_name)!r} -> {new_val!r}", file=_sys.stderr)
            setattr(cfg, field_name, new_val)

    if cfg.relation_pos_threshold <= cfg.relation_neg_threshold:
        # inverted band => a trait can never read "frequently_works_on" (neutral); the band
        # ordering is the invariant, so restore both endpoints to defaults.
        _clamp("relation_pos_threshold", d.relation_pos_threshold, "relation_pos <= relation_neg")
        _clamp("relation_neg_threshold", d.relation_neg_threshold, "relation_pos <= relation_neg")
    if cfg.reinforce_cap < cfg.reinforce_alpha:
        # Reinforcement strengthens by min(alpha**c, cap). A cap below alpha clamps even
        # the FIRST reinforcement (alpha**1) below its own base, silently neutering the
        # testing effect. The cap is the offender (alpha is a valid >1 base), so raise it
        # to alpha — the minimal repair that lets one reinforcement step register.
        _clamp("reinforce_cap", cfg.reinforce_alpha, "reinforce_cap < reinforce_alpha")
    if cfg.embed_max_chars > cfg.max_field_chars:
        # embedding more than is stored => vector/FTS see different text tails. Clamp DOWN to
        # max_field_chars (resetting to the default could still exceed a small max_field_chars).
        _clamp("embed_max_chars", cfg.max_field_chars, "embed_max_chars > max_field_chars")
    # gist identity thresholds must be ordered cluster <= gist_match <= dedup. Restore the
    # order by lowering only the offenders (preserves a deliberately-set lower dedup, etc.).
    if not (cfg.cluster_sim_threshold <= cfg.gist_match_sim_threshold <= cfg.dedup_sim_threshold):
        _clamp("gist_match_sim_threshold", min(cfg.gist_match_sim_threshold, cfg.dedup_sim_threshold),
               "cluster<=gist_match<=dedup order violated")
        _clamp("cluster_sim_threshold", min(cfg.cluster_sim_threshold, cfg.gist_match_sim_threshold),
               "cluster<=gist_match<=dedup order violated")
    # --- S0 weight sanity (Cycle-8 H-2 / M-2) -----------------------------------------
    # S0 = goal_gate * (w_s·surprise + w_c·contingency + w_w·self_ref + w_a·affect), with each
    # signal in [0,1] and goal_gate >= goal_gate_floor. Two joint failure modes:
    _S0_WEIGHTS = ("w_surprise", "w_contingency", "w_self_ref", "w_affect")
    wsum = sum(getattr(cfg, w) for w in _S0_WEIGHTS)
    if wsum <= 0.0:
        # M-2: all weights 0 => S0 == 0 for every episode => everything instantly below the
        # retention floor (salience disabled). Restore the defaults rather than ship a store
        # that forgets everything.
        for w in _S0_WEIGHTS:
            _clamp(w, getattr(d, w), "S0 weights sum to 0 (salience disabled)")
        wsum = sum(getattr(cfg, w) for w in _S0_WEIGHTS)
    # H-2: the goal-relevance gate must remain meaningful. A zero-goal memory's MAX salience is
    # goal_gate_floor × wsum (all signals = 1). If that alone reaches crisis_threshold, weights
    # have overpowered the gate and any memory can self-elevate to a scar. Scale the weights down
    # proportionally so a zero-goal memory stays safely sub-crisis (10% margin).
    if cfg.crisis_threshold > 0:
        zero_goal_max = cfg.goal_gate_floor * wsum
        if zero_goal_max >= cfg.crisis_threshold:
            scale = (0.9 * cfg.crisis_threshold) / zero_goal_max
            for w in _S0_WEIGHTS:
                _clamp(w, round(getattr(cfg, w) * scale, 6),
                       "S0 weights let a zero-goal memory self-elevate to crisis")

    # Networking must stay loopback-only (directive #2). These bind nothing today (the MCP
    # server is stdio and the Dreamer is unwired), so this is latent defense-in-depth that
    # takes effect the moment either is wired (Cycle-8 M-7 / M-S-5).
    def _is_loopback(host: str) -> bool:
        h = (host or "").strip().lower()
        return h in ("localhost", "::1", "") or h.startswith("127.")
    if not _is_loopback(cfg.http_host):
        _clamp("http_host", d.http_host, "http_host is not loopback (directive #2)")
    try:
        from urllib.parse import urlparse
        if not _is_loopback(urlparse(cfg.dreamer_base_url).hostname or ""):
            _clamp("dreamer_base_url", d.dreamer_base_url,
                   "dreamer_base_url host is not loopback (directive #2)")
    except (ValueError, TypeError):
        _clamp("dreamer_base_url", d.dreamer_base_url, "dreamer_base_url is unparseable")
    # CDMS_HOME may legitimately be relocated anywhere ABSOLUTE, but a path-traversal home
    # ("../../etc/x") is never legitimate and would drop the store outside any sane sandbox
    # (Cycle-8 H-3). Reject traversal; leave absolute relocations untouched.
    if ".." in Path(cfg.home).parts:
        _clamp("home", d.home, "home contains a path-traversal ('..') component")

    # Temperament archetype must be a known preset; a typo otherwise silently seeds a
    # store from the wrong genotype. Repair to the default and warn (import is lazy to
    # avoid any import-time coupling between config and the temperament module).
    try:
        from .temperament import archetypes as _known_archetypes
        if cfg.archetype_default not in _known_archetypes():
            print(f"cdms config: invalid archetype_default={cfg.archetype_default!r}; "
                  f"using default {d.archetype_default!r}", file=_sys.stderr)
            cfg.archetype_default = d.archetype_default
    except Exception:
        pass


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
                    # Coerce to the field's type — JSON has no int/float distinction
                    # and tooling often stringifies numbers; a raw setattr left e.g.
                    # embed_dim a str, which bricks every ingest/retrieve.
                    try:
                        setattr(cfg, f.name, _coerce(getattr(cfg, f.name), data[f.name]))
                    except (ValueError, TypeError):
                        pass
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

    _validate(cfg)
    return cfg
