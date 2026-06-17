from datetime import datetime, timezone

from cdms.consolidate import Consolidator
from cdms.models import Episodic
from cdms.store import TurnEvent


def _consolidator(service, cfg):
    return Consolidator(cfg, db=service.db, embedder=service.embedder)


def test_scar_elevation_on_negative_crisis(service, cfg):
    rec = service.ingest(TurnEvent("deleted the production database by accident",
                                   "halted and restored backup", "data loss event",
                                   tool_name="Bash", success=False, valence_hint=-1.0))
    service.db.set_salience([(rec.id, cfg.crisis_threshold + 1.0)])
    rep = _consolidator(service, cfg).run()
    assert rep.scars_created == 1
    assert service.db.stats()["scars"] == 1
    assert service.db.get_episodic(rec.id) is None  # promoted out of episodic


def test_routine_failure_is_not_a_scar(service, cfg):
    # A failed compile / "no results" is negative + salient but NOT a catastrophe.
    rec = service.ingest(TurnEvent("run the build", "ran the compiler",
                                   "error CS0246: type or namespace not found; build failed",
                                   tool_name="Bash", success=False))
    service.db.set_salience([(rec.id, cfg.crisis_threshold + 1.0)])
    rep = _consolidator(service, cfg).run()
    assert rep.scars_created == 0   # routine failure, no catastrophe lexicon match


def test_catastrophe_is_a_scar(service, cfg):
    rec = service.ingest(TurnEvent("clean up the repo", "ran git push --force",
                                   "force push overwrote teammates commits, data loss",
                                   tool_name="Bash", success=False, valence_hint=-1.0))
    service.db.set_salience([(rec.id, cfg.crisis_threshold + 1.0)])
    rep = _consolidator(service, cfg).run()
    assert rep.scars_created == 1   # genuine catastrophe -> pinned


def test_positive_high_salience_not_a_scar(service, cfg):
    rec = service.ingest(TurnEvent("great success shipping the feature", "merged", "all green",
                                   tool_name="Bash", success=True, valence_hint=0.9))
    service.db.set_salience([(rec.id, cfg.crisis_threshold + 1.0)])
    rep = _consolidator(service, cfg).run()
    assert rep.scars_created == 0   # positive valence -> not a crisis scar


def test_temporal_eviction(service, cfg):
    old = Episodic(id="ep_dead", trigger_prompt="trivial forgotten note", action_taken="x",
                   base_salience=0.15, timestamp="2001-01-01T00:00:00Z")
    service.db.insert_episodic(old, service.embedder.embed_one(old.search_text()))
    rep = _consolidator(service, cfg).run()
    assert rep.episodes_evicted >= 1
    assert service.db.get_episodic("ep_dead") is None


def test_gist_creation_from_cluster(service, cfg):
    # Related-but-distinct episodes should cluster (sim>=cluster_threshold) without
    # being deduped (sim<dedup_threshold), and form one gist with support>=2.
    cfg.dedup_sim_threshold = 0.999   # only exact dupes are superseded
    cfg.cluster_sim_threshold = 0.5
    for tag in ("alpha", "beta", "gamma"):
        service.ingest(TurnEvent(
            f"postgres index added to speed up the orders query {tag}",
            f"edited the orders query and added an index {tag}",
            "query performance improved", tool_name="Edit", success=True,
            project="D:/Repo/myapp"))
    rep = _consolidator(service, cfg).run()
    assert rep.gists_created >= 1
    gists = service.db.all_gist()
    assert any(g.support_count >= cfg.min_cluster_support for g in gists)
    assert service.db.stats()["support_edges"] >= 2   # traceable L1->L2 edges


def test_dedup_supersession(service, cfg):
    for _ in range(2):
        service.ingest(TurnEvent("exact same content here", "exact same content here",
                                 "exact same content here", tool_name="Edit"))
    rep = _consolidator(service, cfg).run()
    assert rep.deduped >= 1


def test_budget_renormalization_runs(service, cfg):
    for i in range(4):
        service.ingest(TurnEvent(f"distinct topic number {i} alpha beta", f"action {i}", tool_name="Edit"))
    rep = _consolidator(service, cfg).run()
    total = sum(e.base_salience for e in service.db.all_episodic())
    # after renormalization the live budget should be near K_budget (allowing for
    # eviction of any sub-floor items)
    assert total <= cfg.salience_budget + 1e-6
    assert any("renormalized" in n for n in rep.notes)
