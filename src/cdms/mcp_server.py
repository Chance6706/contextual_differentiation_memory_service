"""MCP stdio server exposing the memory service to the Claude Code CLI.

Registers the five core tools from the spec — ``store``, ``retrieve``,
``history``, ``list_paths``, ``create_link`` — over JSON-RPC 2.0 on stdio.

CRITICAL: stdout is reserved for the JSON-RPC stream. Nothing in this process may
``print()`` to stdout (it corrupts the protocol). All diagnostics go to stderr,
and model-download chatter is suppressed / redirected.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
import threading

# Keep stdout pristine for JSON-RPC and silence HF download bars BEFORE imports.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("PYTHONUTF8", "1")

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s cdms-mcp %(levelname)s %(message)s")
log = logging.getLogger("cdms.mcp")

from pydantic import BaseModel, Field  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

from .config import load_config  # noqa: E402
from .store import MemoryService, TurnEvent  # noqa: E402

mcp = FastMCP("contextual-memory")

_CFG = load_config()
# The cwd the server was launched in — for a project-scoped install this is the
# project directory (Claude Code launches `cdms serve` there), matching the
# `project` hooks capture. Used as the default scope so store/retrieve don't leak
# across projects in a shared (`--scope user`) store.
_LAUNCH_CWD = os.getcwd()
_SERVICE: MemoryService | None = None
_SERVICE_LOCK = threading.Lock()
# One tool call at a time (REPO_ANALYSIS §4.3 / §6 item 8): every tool shares one
# SQLite connection (check_same_thread=False) and FastMCP may dispatch sync tools
# on worker threads while the CLI issues parallel tool calls. Interleaved
# statements on one connection can tear a mem/vec/fts triplet mid-tx (same-
# connection readers see uncommitted partial writes; a rollback can undo another
# thread's statements). The viewport wraps its shared DB in an RLock for exactly
# this reason — mirror it here. Tool bodies are short (ms), so serialization is
# not a throughput concern on a personal memory store.
_DB_LOCK = threading.RLock()


def service() -> MemoryService:
    global _SERVICE
    if _SERVICE is not None:
        return _SERVICE
    # Double-checked lock: avoid two concurrent first-calls each building a separate
    # MemoryService (and leaking SQLite connections).
    with _SERVICE_LOCK:
        if _SERVICE is not None:
            return _SERVICE
        # Warm the (CPU-only) embedder with stdout redirected to stderr so any
        # first-run model download chatter cannot corrupt the JSON-RPC stream.
        svc = MemoryService(_CFG)
        with contextlib.redirect_stdout(sys.stderr):
            try:
                svc.embedder.embed_one("warmup")
            except Exception as exc:  # pragma: no cover - non-fatal
                # The hash fallback was removed (no silent space contamination), so a
                # failure here means vector tools (store/retrieve) will return errors
                # until the model is reachable or CDMS_EMBED_BACKEND=hash is set.
                # Non-vector tools (history/list_paths/create_link) still work.
                log.error("embedder unavailable (%s): vector tools disabled until the model "
                          "is reachable or CDMS_EMBED_BACKEND=hash is set", exc)
        _SERVICE = svc
        return _SERVICE


# --------------------------------------------------------------------------- #
# Structured return types -> auto-generated structuredContent
# --------------------------------------------------------------------------- #
class StoreResult(BaseModel):
    id: str
    tier: str
    salience: float = 0.0
    summary: str


class Memory(BaseModel):
    id: str
    tier: str
    text: str
    score: float
    accessibility: float


class HistoryItem(BaseModel):
    id: str
    timestamp: str
    session_id: str
    valence: float
    salience: float
    text: str


class PersonaPath(BaseModel):
    subject: str
    relation: str
    support: int


class LinkResult(BaseModel):
    source: str
    target: str
    created: bool


# --------------------------------------------------------------------------- #
# The five core tools
# --------------------------------------------------------------------------- #
@mcp.tool()
def store(
    content: str = Field(max_length=10000,
                         description="The text to remember (an observation, fact, preference, or crisis rule)."),
    kind: str = Field(default="episode", description="One of 'episode' (default), 'fact', or 'scar'. "
                      "'fact' content must be 'subject | relation | object'. 'scar' content must be "
                      "'trigger | remediation_rule' and pins a permanent agent-note guardrail "
                      "(surfaced as an unverified note, not an authoritative rule; authority is "
                      "earned via corroborated elevation or an operator pin)."),
    project: str = Field(default=_LAUNCH_CWD, description="Project/workspace path for scoped recall "
                         "(defaults to this server's project)."),
) -> StoreResult:
    """Persist a memory. Episodes decay over time; facts feed the PersonaTree; scars are permanent."""
    svc = service()
    # An empty project from the model path is coerced to the launch cwd, never
    # treated as "global": the global scope is operator-only (the CLI), so a model
    # cannot self-authorize writing cross-project / global memory. For the same reason the
    # `importance`/goal_hint channel is NOT exposed here — a model could otherwise set goal=1.0
    # to defeat the goal-relevance gate and force max salience on anything (Cycle-8 M-3); goal
    # relevance is computed internally from the turn instead. `content` is length-capped
    # (max_length above) so the MCP layer can't be handed a multi-MB string (Cycle-8 M-6).
    project = project or _LAUNCH_CWD
    kind = (kind or "episode").lower()
    # Reject an unknown kind loudly instead of silently filing it as an episode — a typo'd
    # "scar"->"scra" would otherwise drop a guardrail into the decaying episodic tier (Cycle-8 L-S-1).
    if kind not in ("episode", "fact", "scar"):
        raise ValueError(f"unknown kind {kind!r}; expected one of: episode, fact, scar")
    with _DB_LOCK:
        if kind == "scar":
            trig, _, rule = content.partition("|")
            # origin="mcp" (REPO_ANALYSIS S4): the model path must not mint an AUTHORITATIVE
            # guardrail in one tool call while auto-elevation is provenance+corroboration
            # gated — a prompt-injected `store(kind="scar")` would otherwise plant a permanent
            # rule re-injected at every SessionStart (v4/v5 render it as "take precedence over
            # project conventions"). Agent-pinned scars render as unverified notes instead,
            # count toward the L3 per-project cap, and evict before auto-elevated scars.
            scar = svc.pin_scar(trig.strip() or content.strip(), rule.strip() or content.strip(),
                                project, origin="mcp")
            # Dedup can return a pre-existing operator/elevated scar; label honestly either way.
            what = ("pinned agent note (unverified guardrail)" if scar.origin == "mcp"
                    else "matched existing guardrail")
            return StoreResult(id=scar.id, tier="scar", summary=f"{what}: {scar.crisis_trigger[:60]}")
        if kind == "fact":
            parts = [p.strip() for p in content.split("|")]
            if len(parts) >= 3:
                g = svc.upsert_fact(parts[0], parts[1].replace(" ", "_"), parts[2], project=project)
            else:
                g = svc.upsert_fact("user", "noted", content.strip(), project=project)
            return StoreResult(id=g.id, tier="gist", summary=g.render())
        rec = svc.ingest(TurnEvent(trigger_prompt=content, action_taken="(model note)",
                                   project=project))
        return StoreResult(id=rec.id, tier="episodic", salience=rec.base_salience,
                           summary=content[:80])


@mcp.tool()
def retrieve(
    query: str = Field(description="What to recall — a natural-language description of the context or need."),
    k: int = Field(default=8, ge=1, le=1000, description="Max memories to return."),
    tiers: str = Field(default="all", description="'all', or comma list of 'scar','gist','episodic'."),
    project: str = Field(default=_LAUNCH_CWD, description="Restrict recall to this project + global "
                         "memories (defaults to this server's project)."),
) -> list[Memory]:
    """Recall the most relevant memories across scars, gist (PersonaTree), and episodic tiers."""
    svc = service()
    # Empty project => the launch cwd, NOT a cross-project search. Recalling across
    # all projects is operator-only (CLI); the model cannot opt out of scoping here.
    project = project or _LAUNCH_CWD
    if tiers == "all" or not tiers:
        wanted = ("scar", "gist", "episodic")
    else:
        wanted = tuple(t.strip() for t in tiers.split(",") if t.strip() in ("scar", "gist", "episodic"))
        wanted = wanted or ("scar", "gist", "episodic")
    with _DB_LOCK:
        hits = svc.retrieve(query, top_k=k, tiers=wanted, project=project)
    return [Memory(id=h.id, tier=h.tier, text=h.text, score=round(h.score, 5),
                   accessibility=round(h.accessibility, 4)) for h in hits]


@mcp.tool()
def history(
    limit: int = Field(default=20, ge=1, le=1000, description="How many recent episodes to return."),
    session_id: str = Field(default="", description="Optional session id to filter by."),
) -> list[HistoryItem]:
    """Return the recent episodic timeline (most recent first)."""
    svc = service()
    with _DB_LOCK:
        eps = svc.history(limit=limit, session_id=session_id or None)
    return [HistoryItem(id=e.id, timestamp=e.timestamp, session_id=e.session_id,
                        valence=round(e.valence, 3), salience=round(e.base_salience, 4),
                        text=e.search_text()[:200]) for e in eps]


@mcp.tool()
def list_paths() -> list[PersonaPath]:
    """List the PersonaTree paths — distinct (subject, relation) claims with aggregate support."""
    svc = service()
    with _DB_LOCK:
        paths = svc.list_paths()
    return [PersonaPath(subject=s, relation=r, support=sup) for s, r, sup in paths]


@mcp.tool()
def create_link(
    source_id: str = Field(description="Source memory id (e.g. an episodic leaf id)."),
    target_id: str = Field(description="Target memory id (e.g. a gist id)."),
) -> LinkResult:
    """Create a traceable support edge linking one memory to another (e.g. evidence -> claim)."""
    svc = service()
    with _DB_LOCK:
        ok = svc.create_link(source_id, target_id)
    return LinkResult(source=source_id, target=target_id, created=ok)


def main() -> None:
    log.info("starting CDMS MCP server (db=%s, embed_dim=%d)", _CFG.db_path, _CFG.embed_dim)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
