"""Enriched phenotype (Side A): gist exemplars + flashbulb-floor.

Two enrichments to the recalled phenotype, both gated so default behavior/cost is a
deliberate landing call:

  - each top-N highest-support gist carries a verbatim exemplar ("e.g. ...") drawn from
    its most-salient supporting episode, so the persona block conveys behaviorally-legible
    evidence rather than only the terse SRO keyword pair
    (config: recall_exemplars / recall_exemplar_top_n);
  - a genuine catastrophe (catastrophe lexicon matches the deed/result AND the valence is
    crisis-negative) whose natural S0 lands just under the elevation gate is floored to
    crisis_threshold, so a real guardrail forms instead of being silently forgotten
    (config: flashbulb_floor_catastrophes).

Both gates of the flashbulb floor must hold, so benign/positive turns are untouched.
"""

from __future__ import annotations

from cdms.consolidate import Consolidator
from cdms.hooks import _session_start_context
from cdms.models import Gist, new_id
from cdms.store import TurnEvent

# A real disaster narrated in the deed + result (matches _matches_catastrophe).
CATA_ACTION = "ran git push --force"
CATA_OUTCOME = "force push overwrote teammates commits, data loss"


def _insert_gist(svc, object_, support, exemplar, project="P"):
    """Insert a gist directly so render-bounding can be tested deterministically,
    without depending on which clusters the hash embedder happens to form."""
    g = Gist(id=new_id("gist"), subject="P", relation="handles_well", object=object_,
             valence=0.5, frequency=1, support_count=support, survived_cycles=0,
             project=project, exemplar=exemplar)
    svc.db.insert_gist(g, svc.embedder.embed_one(g.search_text()))
    return g


# ---- exemplars: population, persistence, render-bounding, gating ------------

def test_exemplar_populated_from_most_salient_member(service, cfg):
    """Consolidation attaches the (trigger → action) of the cluster's most-salient
    episode as the gist exemplar."""
    cfg.dedup_sim_threshold = 0.999          # keep the near-identical members distinct
    cfg.cluster_sim_threshold = 0.5          # hash geometry: lower the cluster gate
    recs = []
    for tag in ("alpha", "beta", "gamma"):
        recs.append(service.ingest(TurnEvent(
            f"postgres index added to speed up the orders query {tag}",
            f"edited the orders query and added an index {tag}",
            "query performance improved", tool_name="Edit", success=True, project="P")))
    # Make BETA the most salient member, so its quote becomes the exemplar.
    service.db.set_salience([(recs[1].id, 99.0)])

    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.gists_created >= 1

    g = max(service.db.all_gist(), key=lambda x: x.support_count)
    assert "beta" in g.exemplar.lower()      # quote came from the most-salient member
    assert "→" in g.exemplar                 # the ask → deed shape


def test_exemplar_round_trips_through_db(service):
    g = _insert_gist(service, "alpha topic", 5, "EXROUND the round-trip deed")
    back = {x.id: x for x in service.db.all_gist()}[g.id]
    assert back.exemplar == "EXROUND the round-trip deed"


def test_exemplars_render_bounded_to_top_n(service, cfg):
    """Only the top-N highest-support gists carry an exemplar; the long tail stays terse."""
    cfg.recall_exemplars = True
    cfg.recall_exemplar_top_n = 2
    # top_gist orders by (support + frequency + survived); distinct supports fix the rank.
    _insert_gist(service, "alpha topic", 9, "EXALPHA the alpha deed")
    _insert_gist(service, "beta topic", 7, "EXBETA the beta deed")
    _insert_gist(service, "gamma topic", 5, "EXGAMMA the gamma deed")
    _insert_gist(service, "delta topic", 3, "EXDELTA the delta deed")

    out = _session_start_context(cfg, {"cwd": "P"})
    assert "EXALPHA" in out and "EXBETA" in out          # top-2 carry evidence
    assert "EXGAMMA" not in out and "EXDELTA" not in out  # long tail stays terse
    assert out.count("e.g.") == 2                         # exactly N exemplar lines
    # all four traits are still surfaced (bounding affects evidence, not membership)
    assert "delta topic" in out and "gamma topic" in out


def test_recall_exemplars_flag_off_renders_terse(service, cfg):
    cfg.recall_exemplars = False
    _insert_gist(service, "alpha topic", 9, "EXALPHA the alpha deed")
    out = _session_start_context(cfg, {"cwd": "P"})
    assert "alpha topic" in out                           # the trait is present
    assert "EXALPHA" not in out and "e.g." not in out     # but no exemplar rendered


def test_recall_exemplar_top_n_zero_renders_terse(service, cfg):
    cfg.recall_exemplars = True
    cfg.recall_exemplar_top_n = 0
    _insert_gist(service, "alpha topic", 9, "EXALPHA the alpha deed")
    out = _session_start_context(cfg, {"cwd": "P"})
    assert "alpha topic" in out
    assert "EXALPHA" not in out and "e.g." not in out


# ---- flashbulb-floor: elevation, gating, both-gates -------------------------

def test_flashbulb_floor_elevates_genuine_catastrophe(service, cfg):
    """With the floor on, a genuine catastrophe whose natural S0 is under the gate is
    floored to crisis_threshold and elevates to a guardrail."""
    cfg.crisis_threshold = 50.0              # absurdly high so natural S0 can't reach it
    cfg.flashbulb_floor_catastrophes = True
    rec = service.ingest(TurnEvent(
        "clean up the repo", CATA_ACTION, CATA_OUTCOME,
        tool_name="Bash", success=False, valence_hint=-1.0, project="P"))
    assert rec.base_salience >= cfg.crisis_threshold     # floored to the gate

    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.scars_created >= 1
    assert "Guardrails" in _session_start_context(cfg, {"cwd": "P"})


def test_flashbulb_floor_off_leaves_catastrophe_below_gate(service, cfg):
    """With the floor off, the same catastrophe keeps its natural (sub-gate) S0 and no
    guardrail forms — the strict pre-floor behavior."""
    cfg.crisis_threshold = 50.0
    cfg.flashbulb_floor_catastrophes = False
    rec = service.ingest(TurnEvent(
        "clean up the repo", CATA_ACTION, CATA_OUTCOME,
        tool_name="Bash", success=False, valence_hint=-1.0, project="P"))
    assert rec.base_salience < cfg.crisis_threshold      # NOT floored

    rep = Consolidator(cfg, db=service.db, embedder=service.embedder).run()
    assert rep.scars_created == 0                         # no guardrail elevates


def test_flashbulb_floor_requires_both_gates(service, cfg):
    """The floor needs BOTH a catastrophe-lexicon match AND a crisis-negative valence;
    either alone leaves S0 natural (untouched)."""
    cfg.crisis_threshold = 50.0
    cfg.flashbulb_floor_catastrophes = True

    # (a) lexicon match but POSITIVE valence -> valence gate fails -> not floored
    pos = service.ingest(TurnEvent(
        "clean up the repo", CATA_ACTION, CATA_OUTCOME,
        tool_name="Bash", success=True, valence_hint=1.0, project="P"))
    assert pos.base_salience < cfg.crisis_threshold

    # (b) crisis-negative valence but NO catastrophe lexicon -> not floored
    benign = service.ingest(TurnEvent(
        "tweak the readme", "edited the readme intro", "looks fine",
        tool_name="Edit", success=False, valence_hint=-1.0, project="P"))
    assert benign.base_salience < cfg.crisis_threshold
