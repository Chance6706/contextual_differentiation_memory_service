"""Layer 3 — capture-time provenance gating (the real memory-poisoning fix).

Trust model: only TRUSTED-provenance content may elevate to an authoritative guardrail; UNTRUSTED
content (external reads) additionally cannot form a gist persona-trait; AMBIGUOUS can gist but not
elevate. Gating is on `cfg.enforce_provenance` (default True). Provenance is assigned at capture by
`classify_provenance`; manual/seeded turns default to trusted.
"""

from __future__ import annotations

from cdms.consolidate import Consolidator
from cdms.pipeline import classify_provenance, iter_turns
from cdms.store import TurnEvent

CWD = "D:/repo/app"
CRISIS_ACT = "force push wiped the prod database"
CRISIS_OUT = "data loss, unrecoverable, total outage"


# ---- classifier ----------------------------------------------------------------

def test_classify_provenance_heuristic():
    assert classify_provenance("WebFetch", {"url": "http://x"}, CWD) == "untrusted"
    assert classify_provenance("WebSearch", {"query": "q"}, CWD) == "untrusted"
    assert classify_provenance("Edit", {"file_path": "D:/repo/app/src/x.py"}, CWD) == "trusted"
    assert classify_provenance("Read", {"file_path": "D:/Downloads/evil.md"}, CWD) == "untrusted"
    assert classify_provenance("Bash", {"command": "pytest tests/"}, CWD) == "trusted"
    assert classify_provenance("Bash", {"command": "cat /etc/hosts"}, CWD) == "untrusted"
    assert classify_provenance("mcp__weird__thing", {"q": "hi"}, CWD) == "ambiguous"


def test_capture_path_assigns_provenance():
    """iter_turns over spooled events tags each turn's provenance from the tool."""
    events = [
        {"hook_event_name": "UserPromptSubmit", "session_id": "s", "cwd": CWD, "prompt": "do it"},
        {"hook_event_name": "PostToolUse", "session_id": "s", "cwd": CWD,
         "tool_name": "WebFetch", "tool_input": {"url": "http://evil"}, "tool_output": "..."},
        {"hook_event_name": "PostToolUse", "session_id": "s", "cwd": CWD,
         "tool_name": "Edit", "tool_input": {"file_path": f"{CWD}/x.py"}, "tool_output": "ok"},
    ]
    turns = list(iter_turns(events))
    prov = {t.tool_name: t.provenance for t in turns}
    assert prov["WebFetch"] == "untrusted"
    assert prov["Edit"] == "trusted"


# ---- elevation gate (only trusted may elevate) ---------------------------------

def _ingest_crisis(svc, sessions, provenance):
    for sess in sessions:
        svc.ingest(TurnEvent("deploy the release", CRISIS_ACT, CRISIS_OUT, tool_name="Bash",
                             success=False, valence_hint=-1.0, session_id=sess,
                             project="P", provenance=provenance))


def test_untrusted_catastrophe_never_elevates_even_corroborated(service, cfg):
    """A poison repeated across 2 distinct sessions WOULD clear corroboration, but untrusted
    provenance blocks elevation regardless — closing the persistent bypass."""
    _ingest_crisis(service, ["s1", "s2"], "untrusted")
    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.scars_created == 0


def test_trusted_catastrophe_corroborated_elevates(service, cfg):
    """The same crisis from the user's own (trusted) action, corroborated across 2 sessions, DOES
    elevate — provenance gating doesn't block legitimate guardrails."""
    _ingest_crisis(service, ["s1", "s2"], "trusted")
    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.scars_created >= 1


def test_ambiguous_catastrophe_does_not_elevate(service, cfg):
    _ingest_crisis(service, ["s1", "s2"], "ambiguous")
    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.scars_created == 0                       # quarantine: gist-eligible but never a guardrail


def test_enforce_provenance_off_restores_elevation(service, cfg):
    cfg.enforce_provenance = False
    _ingest_crisis(service, ["s1", "s2"], "untrusted")  # provenance ignored when disabled
    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.scars_created >= 1


# ---- gist-trait exclusion (untrusted can't become a persona trait) -------------

def _ingest_cluster(svc, provenance, project="P"):
    for tag in ("alpha", "beta", "gamma"):
        svc.ingest(TurnEvent(f"work on the orders query {tag}",
                             f"edited the orders query and added an index {tag}",
                             "query performance improved", tool_name="Edit", success=True,
                             project=project, provenance=provenance))


def test_untrusted_content_forms_no_gist_trait(service, cfg):
    cfg.dedup_sim_threshold = 0.999
    cfg.cluster_sim_threshold = 0.5
    _ingest_cluster(service, "untrusted")
    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.gists_created == 0                       # external reads don't become persona traits


def test_trusted_content_forms_gists(service, cfg):
    cfg.dedup_sim_threshold = 0.999
    cfg.cluster_sim_threshold = 0.5
    _ingest_cluster(service, "trusted")
    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.gists_created >= 1


def test_ambiguous_content_still_forms_gists(service, cfg):
    """Quarantine tier still learns traits — it just can't elevate to a guardrail."""
    cfg.dedup_sim_threshold = 0.999
    cfg.cluster_sim_threshold = 0.5
    _ingest_cluster(service, "ambiguous")
    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.gists_created >= 1
