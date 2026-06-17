from datetime import datetime, timedelta, timezone

from cdms.models import Episodic
from cdms.store import TurnEvent


def test_ingest_returns_record(service):
    rec = service.ingest(TurnEvent("do a thing", "did the thing", "it worked", tool_name="Edit", success=True))
    assert rec.id.startswith("ep_")
    assert rec.base_salience > 0
    assert service.db.stats()["episodic"] == 1


def test_self_reference_raises_salience(service):
    plain = service.ingest(TurnEvent("read a file", "read it", tool_name="Read"))
    rule = service.ingest(TurnEvent("you must always run tests before commit", "noted the rule",
                                    tool_name="Write", success=True))
    assert rule.base_salience > plain.base_salience


def test_retrieve_finds_relevant(service):
    service.ingest(TurnEvent("kubernetes deployment failed on staging", "checked the pods",
                             "ImagePullBackOff error", tool_name="Bash", success=False))
    service.ingest(TurnEvent("wrote documentation for the parser", "edited docs", tool_name="Write"))
    hits = service.retrieve("kubernetes deployment pods", top_k=5)
    assert hits
    assert any("kubernetes" in h.text.lower() for h in hits)


def test_retrieval_reinforces_access_count(service):
    rec = service.ingest(TurnEvent("unique phrase zaphod beeblebrox", "action", tool_name="Edit"))
    before = service.db.get_episodic(rec.id).access_count
    service.retrieve("zaphod beeblebrox", top_k=3)
    after = service.db.get_episodic(rec.id).access_count
    assert after == before + 1


def test_accessibility_filter_hides_faded(service, cfg):
    # Insert an ancient, low-salience episode directly; it should be filtered out.
    old = Episodic(id="ep_old", trigger_prompt="ancient forgotten lore xyzzy", action_taken="x",
                   base_salience=0.2, timestamp="2000-01-01T00:00:00Z")
    service.db.insert_episodic(old, service.embedder.embed_one(old.search_text()))
    hits = service.retrieve("ancient forgotten lore xyzzy", top_k=5)
    assert all(h.id != "ep_old" for h in hits)


def test_pin_scar_and_upsert_fact(service):
    scar = service.pin_scar("ran rm -rf on prod", "never rm -rf without confirmation")
    assert service.db.stats()["scars"] == 1
    g1 = service.upsert_fact("user", "prefers", "tabs over spaces")
    g2 = service.upsert_fact("user", "prefers", "tabs over spaces")
    assert g1.id == g2.id and g2.frequency == 2   # upsert increments, no dup
