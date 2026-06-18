"""§8 temperament — Phase 0 DEEP simulations / property tests (confidence-raising tier).

Beyond the example-based exit gates in test_temperament.py, this module pushes the four
things Phase 0 actually owns to thousands of randomized cases, adversarial trajectories
with matched NEGATIVE controls (so a green result is non-vacuous), real cross-process
concurrency, and integrity-under-corruption:

  * leash / control surface  — metric properties + monotonicity (fuzz)
  * leash binds within EVERY archetype's box  — the §8.3 guarantee, by construction
  * "no archetype-hopping"  — randomized boiling-frog adversary + moving-anchor control
  * seeding / migration integrity  — heal partial/dropped/meta-lost states; concurrency
  * operator-only firewall  — fuzzed over many random store states

Deterministic (seeded RNG), offline (hash embedder via conftest). No new dependency.
"""

from __future__ import annotations

import json
import random
import threading

import pytest

from cdms import temperament as T
from cdms.config import Config
from cdms.db import Database

DIALS = list(T.DIALS)


def _rand_vec(rng: random.Random, lo: float = 0.0, hi: float = 1.0) -> dict[str, float]:
    return {d: rng.uniform(lo, hi) for d in DIALS}


# --------------------------------------------------------------------------- #
# leash is a proper metric + consistent with leash_exceeded (5k random cases)
# --------------------------------------------------------------------------- #
def test_leash_is_a_metric_fuzz():
    rng = random.Random(20260618)
    for _ in range(5000):
        a, b, s = _rand_vec(rng), _rand_vec(rng), _rand_vec(rng)
        d_as = T.leash_distance(a, s)
        assert d_as >= 0.0                                   # non-negativity
        assert T.leash_distance(a, a) == 0.0                 # identity of indiscernibles
        assert T.leash_distance(a, b) == pytest.approx(T.leash_distance(b, a))  # symmetry
        # triangle inequality d(a,s) <= d(a,b) + d(b,s)
        assert d_as <= T.leash_distance(a, b) + T.leash_distance(b, s) + 1e-9
        # leash_exceeded is exactly distance > R, for a random radius
        R = rng.uniform(0.0, 2.0)
        assert T.leash_exceeded(a, s, R) == (d_as > R)


def test_leash_strictly_increases_moving_away_from_seed_fuzz():
    rng = random.Random(7)
    for _ in range(3000):
        s, cur = _rand_vec(rng), _rand_vec(rng)
        d0 = T.leash_distance(cur, s)
        k = rng.choice(DIALS)
        delta = rng.uniform(0.01, 0.3)
        cur[k] += delta if cur[k] >= s[k] else -delta   # push further from seed on one axis
        assert T.leash_distance(cur, s) > d0


# --------------------------------------------------------------------------- #
# the leash BINDS within every archetype's per-dial box (the maverick-slack guard)
# --------------------------------------------------------------------------- #
def test_leash_binds_within_box_for_every_archetype():
    for arch in T.archetypes():
        R = T.archetype_radius(arch)
        corner = T.box_corner_radius(arch)
        seed = {d.name: d.seed for d in T.preset_dials(arch)}
        assert R > 0.0, f"{arch}: leash radius must be positive"
        assert corner > R, f"{arch}: leash is SLACK (R={R:.3f} >= box-corner={corner:.3f})"
        # the seed itself, and a tiny neighborhood, must be WELL within the leash
        assert not T.leash_exceeded(seed, seed, R)
        near = dict(seed)
        near[DIALS[0]] += 0.001
        assert not T.leash_exceeded(near, seed, R)


def test_per_archetype_plasticity_ordering_is_grounded():
    """Plasticity (drift-band / box) is strictly ordered: resistant end lowest (solid:
    high-stability/conscientiousness), Maverick only MODESTLY highest (owned stipulation),
    small spread (everyone bounded-but-not-frozen). NB the leash RADIUS is a separate,
    safety-capped quantity (it may tie across archetypes); the plasticity claim is the box."""
    order = ["stoic-analyst", "apprentice", "co-pilot", "sparring-partner", "maverick"]
    mults = [T.ARCHETYPE_PLASTICITY[a] for a in order]
    corners = [T.box_corner_radius(a) for a in order]
    assert mults == sorted(mults) and len(set(mults)) == len(mults)       # strictly increasing
    assert corners == sorted(corners) and len(set(corners)) == len(corners)
    base = T.box_corner_radius("co-pilot")
    for a in order:                                                       # corner ∝ multiplier (no clamp artifact)
        assert T.box_corner_radius(a) == pytest.approx(T.ARCHETYPE_PLASTICITY[a] * base)
    assert corners[-1] / corners[0] == pytest.approx(mults[-1] / mults[0])  # spread is exactly the mult ratio
    assert mults[-1] / mults[0] < 2.0                                     # modest, not extreme
    for a in order:                                                       # leash still binds & positive
        assert 0.0 < T.archetype_radius(a) <= T.box_corner_radius(a)


def test_exploration_is_decoupled_from_plasticity():
    """A Maverick EXPLORES more (high exploration_radius SEED) but is only modestly more
    PLASTIC (drift rate) — the precise distinction the human research forces."""
    mav = {d.name: d for d in T.preset_dials("maverick")}
    cop = {d.name: d for d in T.preset_dials("co-pilot")}
    sto = {d.name: d for d in T.preset_dials("stoic-analyst")}
    assert mav["exploration_radius"].seed > cop["exploration_radius"].seed   # explores more
    ratio = mav["exploration_radius"].plasticity / cop["exploration_radius"].plasticity
    assert ratio == pytest.approx(T.ARCHETYPE_PLASTICITY["maverick"]) and 1.0 < ratio < 1.5  # modest
    for name in T.DIALS:                                                     # Stoic = resistant pole
        assert sto[name].plasticity < cop[name].plasticity


def test_all_archetypes_seed_roundtrip_through_db(tmp_path):
    for arch in T.archetypes():
        cfg = Config(home=tmp_path / arch, archetype_default=arch)
        db = Database(cfg)
        got = {d.name: d for d in db.all_dials()}
        preset = {d.name: d for d in T.preset_dials(arch)}
        assert set(got) == set(DIALS)
        for name, p in preset.items():
            g = got[name]
            assert (g.seed, g.current, g.lower, g.upper, g.plasticity) == pytest.approx(
                (p.seed, p.current, p.lower, p.upper, p.plasticity))
            assert g.current == g.seed                       # Phase 0: no drift
            assert 0.0 <= g.lower <= g.seed <= g.upper <= 1.0
            assert not T.near_bound(g)                        # no dial seeds at its bound
        assert db.get_archetype() == arch
        db.close()


# --------------------------------------------------------------------------- #
# "no archetype-hopping": a randomized sub-threshold ratchet toward ANOTHER
# archetype trips the STATIC-SEED leash before arrival — and a MOVING-ANCHOR
# leash (the broken design) never trips (matched negative control → non-vacuous).
# --------------------------------------------------------------------------- #
def test_no_archetype_seed_lies_within_anothers_leash():
    """Closed-form 'no archetype-hopping' invariant over ALL ordered pairs: every other
    archetype's seed must be strictly OUTSIDE this archetype's leash, or `current` could
    drift onto a neighbour without the leash ever firing (the Round-2 regression). This is
    the cheap guard the 3-pair trajectory test missed; it must hold for all 20 pairs."""
    arches = list(T.archetypes())
    for src in arches:
        seed = {d.name: d.seed for d in T.preset_dials(src)}
        R = T.archetype_radius(src)
        for dst in arches:
            if dst == src:
                continue
            other = {d.name: d.seed for d in T.preset_dials(dst)}
            dist = T.leash_distance(other, seed)
            assert dist > R, f"{dst} seed (dist {dist:.3f}) is within {src} leash R={R:.3f}"


@pytest.mark.parametrize("src,dst", [(s, d) for s in (
    "co-pilot", "sparring-partner", "apprentice", "stoic-analyst", "maverick")
    for d in ("co-pilot", "sparring-partner", "apprentice", "stoic-analyst", "maverick")
    if s != d])
def test_subthreshold_hop_trips_seed_leash_not_moving_anchor(src, dst):
    seed = {d.name: d.seed for d in T.preset_dials(src)}
    target = {d.name: d.seed for d in T.preset_dials(dst)}
    R = T.archetype_radius(src)
    step, gate = 0.012, 0.05          # each per-dial move is sub-threshold (< gate)
    cur, prev = dict(seed), dict(seed)
    seed_tripped_at = reached_dst_at = None
    moving_anchor_tripped = False
    max_step_move = 0.0
    for i in range(1, 4001):
        for k in target:               # cross-dial: advance every differing dial at once
            gap = target[k] - cur[k]
            if abs(gap) < 1e-9:
                continue
            cur[k] += step if gap > 0 else -step
            if (gap > 0) == (target[k] - cur[k] < 0):  # overshoot → clamp to target
                cur[k] = target[k]
        max_step_move = max(max_step_move, max(abs(cur[k] - prev[k]) for k in target))
        # a leash anchored to the PREVIOUS step would never fire (each move < gate)…
        if T.leash_distance(cur, prev) > R:
            moving_anchor_tripped = True
        # …but the STATIC-SEED leash catches the cumulative drift.
        if seed_tripped_at is None and T.leash_exceeded(cur, seed, R):
            seed_tripped_at = i
        if reached_dst_at is None and T.leash_distance(cur, target) < 1e-6:
            reached_dst_at = i
        prev = dict(cur)
        if reached_dst_at is not None:
            break
    assert max_step_move < gate, "adversary steps must be genuinely sub-threshold"
    assert seed_tripped_at is not None, "static-seed leash never fired"
    assert reached_dst_at is not None, "adversary never reached the target archetype"
    assert seed_tripped_at < reached_dst_at, "leash must fire BEFORE arriving at another archetype"
    assert not moving_anchor_tripped, "a previous-step-anchored leash would miss the boiling frog"


# --------------------------------------------------------------------------- #
# seeding / migration integrity under interruption, corruption, concurrency
# --------------------------------------------------------------------------- #
def test_dropped_temperament_table_reheals(tmp_path):
    cfg = Config(home=tmp_path)
    db = Database(cfg)
    db.conn.execute("DROP TABLE mem_temperament")
    db.conn.commit()
    db.close()
    db2 = Database(cfg)
    assert len(db2.all_dials()) == 8
    assert db2.get_archetype() == "co-pilot"
    db2.close()


def test_partial_seed_heals_from_stored_archetype_preserving_drift(tmp_path):
    cfg = Config(home=tmp_path, archetype_default="maverick")
    db = Database(cfg)
    db.conn.execute("UPDATE mem_temperament SET current = 0.66 WHERE dial = 'autonomy_gate'")
    keep = ("autonomy_gate", "deference_independence", "emotional_gain")
    ph = ",".join("?" * len(keep))
    db.conn.execute(f"DELETE FROM mem_temperament WHERE dial NOT IN ({ph})", keep)
    db.conn.commit()
    assert len(db.all_dials()) == 3
    db.close()

    db2 = Database(cfg)
    dials = {d.name: d for d in db2.all_dials()}
    assert len(dials) == 8                              # completed
    assert dials["autonomy_gate"].current == 0.66        # drift preserved (OR IGNORE)
    assert db2.get_archetype() == "maverick"
    mav = {d.name: d for d in T.preset_dials("maverick")}
    assert dials["exploration_radius"].seed == mav["exploration_radius"].seed  # healed from maverick
    db2.close()


def test_archetype_seed_vectors_are_unique():
    """match_archetype_by_seed recovery is only unambiguous if no two archetypes share an
    identical seed vector — guard it as the preset table evolves."""
    seen: dict[tuple, str] = {}
    for a in T.archetypes():
        key = tuple(round(d.seed, 6) for d in T.preset_dials(a))
        assert key not in seen, f"{a} shares a seed vector with {seen.get(key)}"
        seen[key] = a
        assert T.match_archetype_by_seed({d.name: d.seed for d in T.preset_dials(a)}) == a


def test_lost_archetype_meta_recovered_from_immutable_seeds(tmp_path):
    cfg = Config(home=tmp_path, archetype_default="maverick")
    db = Database(cfg)
    db.conn.execute("DELETE FROM cdms_meta WHERE key = 'archetype'")
    db.conn.commit()
    db.close()
    db2 = Database(cfg)
    assert db2.get_archetype() == "maverick"             # recovered, not defaulted
    assert db2.get_archetype_radius() == pytest.approx(T.archetype_radius("maverick"))
    db2.close()


def test_concurrent_first_init_seeds_exactly_eight(tmp_path):
    import sqlite3
    import time

    cfg = Config(home=tmp_path)
    errors: list[object] = []
    barrier = threading.Barrier(8)

    def worker():
        try:
            barrier.wait()           # maximize contention on first init
            # Transient lock/busy under a thundering-herd first init is a CALLER-retry
            # concern by design (Database re-raises locks rather than quarantining a good
            # store — see test_cycle3). Retry like a real caller; the guarantee under test
            # is that seeding never duplicates / corrupts, i.e. exactly 8 dials result.
            for attempt in range(12):
                try:
                    Database(cfg).close()
                    return
                except sqlite3.OperationalError as exc:
                    if "lock" not in str(exc).lower() and "busy" not in str(exc).lower():
                        raise
                    time.sleep(0.02 * (attempt + 1))
            errors.append("gave up after lock retries")
        except Exception as exc:     # noqa: BLE001 — record, assert after join
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, f"concurrent first-init raised: {errors!r}"
    db = Database(cfg)
    assert len(db.all_dials()) == 8          # never duplicated, never partial
    assert {d.name for d in db.all_dials()} == set(DIALS)
    db.close()


# --------------------------------------------------------------------------- #
# firewall fuzz: across many random store states, no agent-readable surface leaks
# --------------------------------------------------------------------------- #
def test_firewall_holds_across_random_store_states(tmp_path):
    from cdms.embeddings import Embedder
    from cdms.hooks import _session_start_context
    from cdms.store import MemoryService, TurnEvent

    rng = random.Random(2026)
    leak_words = ("temperament", "archetype", "r_archetype", "plasticity", "leash",
                  *T.archetypes(), *DIALS)
    verbs = ("handles_well", "has_trouble_with", "frequently_works_on")
    for n in range(12):
        arch = rng.choice(T.archetypes())
        cfg = Config(home=tmp_path / f"s{n}", archetype_default=arch)
        svc = MemoryService(cfg, embedder=Embedder(cfg))
        for _ in range(rng.randint(1, 6)):
            svc.upsert_fact("proj", rng.choice(verbs), f"thing{rng.randint(0, 20)}")
            svc.ingest(TurnEvent(f"did task {rng.randint(0, 99)}", "ran a tool",
                                 "ok", tool_name="Edit", success=True, project="proj"))
        ctx = _session_start_context(cfg, {"cwd": "proj"})
        hits = svc.retrieve("task thing", top_k=8)
        svc.close()
        blob = (ctx + " " + json.dumps([{"t": h.tier, "x": h.text, "p": h.payload}
                                        for h in hits], default=str)).lower()
        for w in leak_words:
            assert w not in blob, f"leak {w!r} in store-state #{n} (archetype={arch})"
