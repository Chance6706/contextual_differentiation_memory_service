"""M1 fix: the harness now runs real consolidation, so cdms-forgetting / cdms-random-discard
actually differ from cdms-full. Before this seam they were inert (MemoryService.ingest never
consolidates), which would have produced a FALSE NULL on the salience-vs-random claim.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["CDMS_EMBED_BACKEND"] = "hash"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tools.eval_harness.adapter import CdmsAdapter, Turn, Scope


def _seeded_adapter(condition: str, base: Path) -> CdmsAdapter:
    a = CdmsAdapter(condition, base_path=base)
    a.reset(condition)
    for i in range(6):
        a.ingest([Turn(role="user", content=f"distinct fact number {i} about widget {i}")],
                 scope=Scope(project="P"))
    ids = [e.id for e in a._svc.db.all_episodic()]
    # 3 below the retention floor (salience-evictable), 3 well above (kept).
    a._svc.db.set_salience([(ids[i], 0.001) for i in range(3)] + [(ids[i], 5.0) for i in range(3, 6)])
    return a


def _count(a: CdmsAdapter) -> int:
    return len(a._svc.db.all_episodic())


def test_without_consolidation_all_conditions_are_inert(tmp_path):
    # The M1 bug: ingest alone never evicts, so every condition keeps all 6 — indistinguishable.
    for cond in ("cdms-full", "cdms-forgetting", "cdms-random-discard"):
        a = _seeded_adapter(cond, tmp_path / f"no-{cond}")
        assert _count(a) == 6
        a.cleanup()


def test_consolidation_makes_the_ablations_diverge(tmp_path):
    full = _seeded_adapter("cdms-full", tmp_path / "full");           full.consolidate()
    forg = _seeded_adapter("cdms-forgetting", tmp_path / "forg");     forg.consolidate()
    rand = _seeded_adapter("cdms-random-discard", tmp_path / "rand"); rand.consolidate()
    try:
        assert _count(full) == 3    # salience evicts the 3 below-floor episodes
        assert _count(forg) == 6    # retention_floor=0 -> nothing evicted -> forgetting toggle MATTERS
        assert _count(rand) == 3    # rate-matched count, but random victims (not necessarily the low 3)
        # the whole point: forgetting now differs from full (was identical pre-seam)
        assert _count(forg) != _count(full)
    finally:
        for a in (full, forg, rand):
            a.cleanup()
