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


def test_gist_relation_flips_with_sustained_change(service, cfg):
    # A negative trait should FLIP toward positive under SUSTAINED improvement on
    # the same (subject, object) — but not from a single good day (continuity
    # resists; plasticity wins only with persistence).
    cfg.dedup_sim_threshold = 0.999
    cfg.cluster_sim_threshold = 0.5
    for tag in ("a", "b"):
        service.ingest(TurnEvent(f"work on auth module {tag}", f"debug the auth module {tag}",
                                 "failed with an error", tool_name="Bash", success=False,
                                 valence_hint=-0.9, project="D:/Repo/app"))
    _consolidator(service, cfg).run()
    g = _gist_for(service, "app")
    assert g is not None and g.relation == "has_trouble_with"

    flipped = False
    for rnd in range(6):
        for i in range(3):
            service.ingest(TurnEvent(f"work on auth module r{rnd}{i}", f"improve the auth module r{rnd}{i}",
                                     "passed cleanly", tool_name="Bash", success=True,
                                     valence_hint=0.9, project="D:/Repo/app"))
        rep = _consolidator(service, cfg).run()
        if _gist_for(service, "app").relation != "has_trouble_with":
            flipped = True
            break
    assert flipped, "trait never flipped despite sustained positive evidence"


def _gist_for(service, subject):
    gs = [g for g in service.db.all_gist() if g.subject == subject]
    return gs[0] if gs else None


def test_gist_decays_through_idle_cycles_not_wallclock(service, cfg):
    # Decay is ACTIVITY-based: a trait fades only across active consolidation cycles
    # in which it is never reinforced. Use an aggressive per-cycle factor for speed.
    cfg.gist_decay_per_cycle = 0.5
    cfg.gist_retention_floor = 0.25
    service.ingest(TurnEvent("ping", "noop", tool_name="Read"))   # keep a live episode
    service.upsert_fact("workspace", "frequently_works_on", "an abandoned subsystem")
    assert service.db.stats()["gist"] == 1
    decayed = False
    for _ in range(5):   # several idle cycles without reinforcing the trait
        rep = _consolidator(service, cfg).run()
        if rep.gists_decayed:
            decayed = True
            break
    assert decayed
    assert service.db.find_gist_by_so("workspace", "an abandoned subsystem") is None


def test_absence_does_not_age_identity(service, cfg):
    # Identity (L2 gist) decay is measured in CONSOLIDATION CYCLES, never wall-clock.
    # Guards against a regression to wall-clock decay: a gist survives a year of
    # absence because only the cycle count matters, while raw L1 episodic memory DOES
    # fade by wall-clock over the same span. (The prior version of this test was
    # vacuous — it never advanced a cycle, so it passed even with decay disabled.)
    from datetime import datetime, timedelta, timezone

    from cdms.salience import accessibility

    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    acts = ["build the core architecture module", "refactor the core architecture layer",
            "test the core architecture flow"]  # share topic (cluster), differ (no dedup)
    for a in acts:
        service.ingest(TurnEvent("work on the core architecture", a, "passed cleanly",
                                 tool_name="Bash", success=True, valence_hint=0.9, project="D:/Repo/app",
                                 timestamp=base.strftime("%Y-%m-%dT%H:%M:%SZ")))
    _consolidator(service, cfg).run(now=base)             # cycle 1 — gist forms
    assert _gist_for(service, "app") is not None

    # ONE consolidation a YEAR later, no new reinforcing episodes: the gist decays by
    # ONE idle cycle (gentle), NOT by 365 wall-clock days — so it survives. If decay
    # were wall-clock based this would evict it.
    _consolidator(service, cfg).run(now=base + timedelta(days=365))
    assert _gist_for(service, "app") is not None, "absence (wall-clock) wrongly aged the gist"

    # Contrast: an L1 episodic trace of the same age HAS faded heavily by wall-clock.
    assert accessibility(1.0, 365, 0, cfg) < 0.001 * accessibility(1.0, 0, 0, cfg)


def test_dedup_supersession(service, cfg):
    for _ in range(2):
        service.ingest(TurnEvent("exact same content here", "exact same content here",
                                 "exact same content here", tool_name="Edit"))
    rep = _consolidator(service, cfg).run()
    assert rep.deduped >= 1


def test_per_project_budget_cap_prevents_domination(service, cfg):
    # one project with many turns must not exceed the cap of total salience
    cfg.project_budget_cap = 0.5
    cfg.dedup_sim_threshold = 0.999   # keep the many near-identical turns distinct
    for i in range(40):
        service.ingest(TurnEvent(f"big project work {i}", f"did big thing {i}",
                                 tool_name="Edit", project="D:/Repo/big"))
    for i in range(4):
        service.ingest(TurnEvent(f"small project work {i}", f"did small thing {i}",
                                 tool_name="Edit", project="D:/Repo/small"))
    _consolidator(service, cfg).run()
    eps = service.db.all_episodic()
    total = sum(e.base_salience for e in eps) or 1.0
    big = sum(e.base_salience for e in eps if e.project == "D:/Repo/big")
    small = sum(e.base_salience for e in eps if e.project == "D:/Repo/small")
    assert big / total <= 0.5 + 0.02          # dominant project capped near 50%
    assert small > 0                           # small project not starved to zero


def test_budget_renormalization_runs(service, cfg):
    for i in range(4):
        service.ingest(TurnEvent(f"distinct topic number {i} alpha beta", f"action {i}", tool_name="Edit"))
    rep = _consolidator(service, cfg).run()
    total = sum(e.base_salience for e in service.db.all_episodic())
    # after renormalization the live budget should be near K_budget (allowing for
    # eviction of any sub-floor items)
    assert total <= cfg.salience_budget + 1e-6
    assert any("budget" in n for n in rep.notes)
