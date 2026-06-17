"""Regression test for H1: gist proliferation from object-key instability.

A single underlying topic whose dominant content terms reshuffle cycle-to-cycle
(near-tied frequencies) used to shatter into many (subject, object) gist nodes —
none of which accumulated support, so a stable identity never crystallized. The
fix reinforces the nearest EXISTING gist of a subject by episode-space centroid
(vocabulary-independent identity) instead of spawning siblings.
"""

from __future__ import annotations

from cdms.consolidate import Consolidator
from cdms.embeddings import Embedder
from cdms.store import MemoryService, TurnEvent

# One topic; the same content terms recur with reshuffling dominance each cycle.
_VARIANTS = [
    ("work on the parser parser lexer grammar", "edited the parser handler"),
    ("work on the lexer lexer grammar parser", "edited the lexer handler"),
    ("work on the grammar grammar parser lexer", "edited the grammar handler"),
]


def _grow(svc, con, cycles: int) -> None:
    for cyc in range(cycles):
        prompt, action = _VARIANTS[cyc % len(_VARIANTS)]
        for j in range(2):
            svc.ingest(TurnEvent(
                trigger_prompt=prompt, action_taken=f"{action} round {cyc}",
                outcome_feedback="completed the change", project="compilerproj",
                session_id=f"s{cyc}"))
        con.run()


def test_single_topic_does_not_proliferate(cfg):
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        con = Consolidator(cfg, db=svc.db, embedder=svc.embedder)
        _grow(svc, con, 12)
        gists = [g for g in svc.db.all_gist() if g.subject == "compilerproj"]
        assert len(gists) <= 2, f"gist proliferation: {[g.object for g in gists]}"
        # The surviving trait actually accumulated support across cycles.
        assert max(g.support_count for g in gists) >= 2
    finally:
        svc.close()


def test_embedding_match_requires_both_centroid_and_term_overlap(cfg):
    """The mechanism merges only a genuine reshuffle of one topic: BOTH the
    episode-space centroid must be close AND the object labels must share a term.
    Neither guard alone is sufficient under a weak embedder."""
    from cdms.models import Gist, new_id

    svc = MemoryService(cfg, embedder=Embedder(cfg))
    try:
        con = Consolidator(cfg, db=svc.db, embedder=svc.embedder)
        topic = "hex grid terrain shader material render pass"
        c_existing = con._centroid([svc.embedder.embed_one(topic)])
        g = Gist(id=new_id("gist"), subject="proj", relation="frequently_works_on", object="terrain shader")
        svc.db.insert_gist(g, svc.embedder.embed_one(g.search_text()), c_existing)

        near = con._centroid([svc.embedder.embed_one(topic)])
        far = con._centroid([svc.embedder.embed_one("invoice billing payment tax accounting ledger")])

        # Reshuffle of the same topic (shared term "terrain" + near centroid) -> merge.
        assert con._match_gist_by_embedding("proj", near, "terrain material") is not None
        # Shared term but distant centroid -> no merge (centroid guard).
        assert con._match_gist_by_embedding("proj", far, "terrain material") is None
        # Near centroid but no shared object term -> no merge (term guard; preserves
        # distinct sub-traits that share project vocabulary).
        assert con._match_gist_by_embedding("proj", near, "render pass") is None
        # Subject-scoped.
        assert con._match_gist_by_embedding("otherproj", near, "terrain material") is None
    finally:
        svc.close()
