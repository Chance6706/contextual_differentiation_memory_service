"""§8 temperament — Phase 0: STATE + pure-function control (no drift, no log).

These are the exit gates for Phase 0: seeding/accessor correctness, pure-function
control correctness, the G-A "boiling-frog" sub-threshold ratchet (the operational
falsification of "no archetype-hopping"), v3→v4 migration safety on a store WITH data,
the operator-only (Bem) firewall, and the no-wall-clock discipline.
"""

from __future__ import annotations

import inspect
import json
import sqlite3

import pytest

from cdms import temperament as T
from cdms.config import Config, load_config
from cdms.db import SCHEMA_VERSION, Database
from cdms.models import Dial


# --------------------------------------------------------------------------- #
# seeding + accessors
# --------------------------------------------------------------------------- #
def test_seeds_default_copilot_on_first_init(cfg):
    db = Database(cfg)
    dials = db.all_dials()
    assert {d.name for d in dials} == set(T.DIALS)
    assert len(dials) == len(T.DIALS) == 8
    assert db.get_archetype() == "co-pilot"
    assert db.get_archetype_radius() == 0.30
    # Phase 0: no drift — current == seed for every dial; bounds bracket seed, in [0,1].
    for d in dials:
        assert d.current == d.seed
        assert d.lower <= d.seed <= d.upper
        assert 0.0 <= d.lower and d.upper <= 1.0
        assert d.plasticity == T.PLASTICITY[d.name]
    db.close()


def test_archetype_choice_changes_seed_and_radius(tmp_path):
    cfg = Config(home=tmp_path, archetype_default="maverick")
    db = Database(cfg)
    assert db.get_archetype() == "maverick"
    assert db.get_archetype_radius() == 0.45
    dials = {d.name: d for d in db.all_dials()}
    assert dials["exploration_radius"].seed == 0.90
    db.close()


def test_seeding_is_idempotent_and_never_clobbers_current(tmp_path):
    cfg = Config(home=tmp_path)
    db = Database(cfg)
    # Simulate a future Phase-1b drift by moving one dial's current off its seed.
    db.conn.execute("UPDATE mem_temperament SET current = 0.42 WHERE dial = 'autonomy_gate'")
    db.conn.commit()
    db.close()
    # Re-open: seed-on-empty must NOT re-seed (table non-empty) nor overwrite `current`.
    db2 = Database(cfg)
    dials = {d.name: d for d in db2.all_dials()}
    assert dials["autonomy_gate"].current == 0.42
    assert len(dials) == 8  # not doubled
    db2.close()


def test_preset_dials_unknown_archetype_falls_back_to_default():
    out = T.preset_dials("nope-not-real")
    assert [d.name for d in out] == list(T.DIALS)
    assert all(d.seed == 0.5 for d in out)  # co-pilot moderate seeds


# --------------------------------------------------------------------------- #
# T1 — pure-function control correctness
# --------------------------------------------------------------------------- #
def test_near_bound():
    assert not T.near_bound(Dial("x", 0.5, 0.5, 0.4, 0.6, 0.2), eps=0.02)
    assert T.near_bound(Dial("x", 0.5, 0.59, 0.4, 0.6, 0.2), eps=0.02)   # near upper
    assert T.near_bound(Dial("x", 0.5, 0.405, 0.4, 0.6, 0.2), eps=0.02)  # near lower


def test_large_shift_is_symmetric():
    assert T.large_shift(0.5, 0.65, theta=0.1)
    assert not T.large_shift(0.5, 0.55, theta=0.1)
    assert T.large_shift(0.5, 0.35, theta=0.1)  # downward move counts too


def test_leash_zero_at_seed_and_grows():
    dials = T.preset_dials("co-pilot")
    cur, seed = T.vector(dials), T.seed_vector(dials)
    assert T.leash_distance(cur, seed) == 0.0
    assert not T.leash_exceeded(cur, seed, 0.30)
    cur2 = dict(cur)
    cur2["exploration_radius"] += 0.5
    assert T.leash_distance(cur2, seed) == pytest.approx(0.5)
    assert T.leash_exceeded(cur2, seed, 0.30)


def test_leash_binds_before_per_dial_bounds():
    """§8.3 raison d'être: a vector inside EVERY per-dial band can still be jointly
    out of the archetype region (box-vs-region). The joint leash must catch it."""
    dials = {d.name: d for d in T.preset_dials("co-pilot")}
    seed = {n: d.seed for n, d in dials.items()}
    cur = dict(seed)
    for n in ("exploration_radius", "deference_independence", "autonomy_gate"):
        cur[n] = dials[n].upper          # ON the per-dial bound — no per-dial violation
        assert cur[n] <= dials[n].upper
    assert T.leash_distance(cur, seed) > 0.30   # ...yet jointly outside the leash
    assert T.leash_exceeded(cur, seed, 0.30)


# --------------------------------------------------------------------------- #
# T2 — G-A "boiling frog": a sub-threshold ratchet trips the STATIC-SEED leash
# --------------------------------------------------------------------------- #
def test_boiling_frog_subthreshold_ratchet_trips_seed_anchored_leash():
    dials = T.preset_dials("co-pilot")
    seed = T.seed_vector(dials)
    cur = dict(seed)
    R, per_step, step_gate = 0.30, 0.02, 0.05
    prev = dict(cur)
    tripped_at = None
    max_per_step_move = 0.0
    for i in range(1, 41):
        cur["exploration_radius"] += per_step
        max_per_step_move = max(max_per_step_move,
                                abs(cur["exploration_radius"] - prev["exploration_radius"]))
        # A leash anchored to the PREVIOUS step would never fire (each move < gate)…
        assert not T.large_shift(prev["exploration_radius"], cur["exploration_radius"], step_gate)
        # …but the STATIC-SEED leash catches the accumulation.
        if tripped_at is None and T.leash_exceeded(cur, seed, R):
            tripped_at = i
        prev = dict(cur)
    assert max_per_step_move < step_gate          # genuinely sub-threshold each step
    assert tripped_at is not None and tripped_at <= 16  # ~0.30 / 0.02 ≈ 15 steps


# --------------------------------------------------------------------------- #
# T3 — v3→v4 migration safety on a store WITH data (the §8.7-named real risk)
# --------------------------------------------------------------------------- #
def test_migration_v3_to_v4_seeds_temperament_preserving_data(tmp_path):
    from cdms.embeddings import Embedder
    from cdms.store import MemoryService, TurnEvent

    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    svc.ingest(TurnEvent("set up a postgres index", "added an index", "queries faster",
                         tool_name="Edit", success=True, project="p"))
    svc.upsert_fact("p", "frequently_works_on", "postgres indexes")
    before = svc.db.stats()
    svc.close()
    assert before["gist"] >= 1

    # Downgrade the on-disk store to look like a pre-temperament v3 store.
    conn = sqlite3.connect(str(cfg.db_path))
    conn.execute("DROP TABLE mem_temperament")
    conn.execute("DELETE FROM cdms_meta WHERE key IN ('archetype', 'R_archetype')")
    conn.execute("PRAGMA user_version = 3")
    conn.commit()
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
    conn.close()

    # Re-open via the app: migration must re-create + seed the table, bump the version,
    # and leave the prior gist/episodic data fully intact.
    svc2 = MemoryService(cfg, embedder=Embedder(cfg))
    assert svc2.db.conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION == 4
    assert len(svc2.db.all_dials()) == 8
    assert svc2.db.get_archetype() == "co-pilot"
    after = svc2.db.stats()
    assert after["episodic"] == before["episodic"]
    assert after["gist"] == before["gist"]
    svc2.close()


# --------------------------------------------------------------------------- #
# T4 — operator-only firewall (Bem self-perception): never in SessionStart context
# --------------------------------------------------------------------------- #
# Words/identifiers that would betray a temperament leak into agent-readable text.
_LEAK_WORDS = ("temperament", "archetype", "r_archetype", "plasticity", "leash",
               "co-pilot", "sparring-partner", "apprentice", "stoic-analyst", "maverick")


def _assert_no_temperament_leak(text: str) -> None:
    low = text.lower()
    for dial in T.DIALS:
        assert dial not in low, f"dial name leaked into agent-readable text: {dial!r}"
    for word in _LEAK_WORDS:
        assert word not in low, f"temperament word leaked into agent-readable text: {word!r}"


def test_firewall_helper_is_non_vacuous():
    """Positive control: the helper MUST flag a deliberate leak — otherwise the
    firewall tests below would pass vacuously (Round-2 F1)."""
    with pytest.raises(AssertionError):
        _assert_no_temperament_leak("PersonaTree: autonomy_gate=0.5 (archetype co-pilot)")


def test_temperament_never_enters_sessionstart_context(tmp_path):
    from cdms.embeddings import Embedder
    from cdms.hooks import _session_start_context
    from cdms.store import MemoryService, TurnEvent

    # Use the DEFAULT archetype (co-pilot) — the common case the prior test missed.
    cfg = Config(home=tmp_path)
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    svc.upsert_fact("p", "handles_well", "shaders")
    svc.ingest(TurnEvent("worked on shaders", "edited a shader", "looks good",
                         tool_name="Edit", success=True, project="p"))
    svc.close()

    ctx = _session_start_context(cfg, {"cwd": "p"})
    assert ctx  # non-empty, so the absence assertions are meaningful
    _assert_no_temperament_leak(ctx)


def test_temperament_never_in_retrieve_results(tmp_path):
    """The MCP `retrieve` tier (and everything built on store.retrieve) must not
    surface temperament state to the agent either (Round-2 F1)."""
    import json as _json

    from cdms.embeddings import Embedder
    from cdms.store import MemoryService, TurnEvent

    cfg = Config(home=tmp_path, archetype_default="maverick")
    svc = MemoryService(cfg, embedder=Embedder(cfg))
    svc.upsert_fact("p", "handles_well", "postgres indexes")
    svc.ingest(TurnEvent("set up a postgres index", "added an index", "queries faster",
                         tool_name="Edit", success=True, project="p"))
    hits = svc.retrieve("postgres index", top_k=5)
    paths = svc.list_paths()
    svc.close()

    blob = _json.dumps(
        [{"tier": h.tier, "text": h.text, "payload": h.payload} for h in hits]
        + [list(p) for p in paths], default=str)
    _assert_no_temperament_leak(blob)


# --------------------------------------------------------------------------- #
# T5 — activity-clock only: no wall-clock anywhere in the temperament module
# --------------------------------------------------------------------------- #
def test_temperament_module_has_no_wallclock():
    # AST-based (not raw-substring) so the module's *prose* explaining why it avoids
    # wall-clock doesn't trip the check — we assert on actual imports and calls.
    import ast

    tree = ast.parse(inspect.getsource(T))
    imported: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            f = node.func
            calls.add(f.attr if isinstance(f, ast.Attribute)
                      else f.id if isinstance(f, ast.Name) else "")
    # No wall-clock SOURCE may be imported (incl. via os), and no dynamic import escape.
    forbidden_imports = {"datetime", "time", "os", "calendar"}
    assert not (imported & forbidden_imports), (
        f"temperament.py must be activity-clock only; forbidden imports={imported & forbidden_imports}")
    # No wall-clock READER may be called by name (monotonic/perf_counter/etc.) and no
    # __import__ escape hatch (Round-2 F3).
    forbidden_calls = {"now", "utcnow", "age_days", "time", "monotonic", "monotonic_ns",
                       "perf_counter", "perf_counter_ns", "process_time", "times",
                       "clock_gettime", "time_ns", "__import__"}
    assert not (calls & forbidden_calls), (
        f"temperament.py must not read wall-clock; forbidden calls={calls & forbidden_calls}")


# --------------------------------------------------------------------------- #
# T6 — operator CLI end-to-end + config validation
# --------------------------------------------------------------------------- #
def test_cli_temperament_outputs_seeded_vector(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_ARCHETYPE_DEFAULT", "stoic-analyst")
    from cdms.cli import main

    assert main(["temperament"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["archetype"] == "stoic-analyst"
    assert out["R_archetype"] == 0.30
    assert out["leash_exceeded"] is False
    assert len(out["dials"]) == 8
    assert {d["dial"] for d in out["dials"]} == set(T.DIALS)
    eg = next(d for d in out["dials"] if d["dial"] == "emotional_gain")
    assert eg["seed"] == 0.15 and eg["current"] == 0.15


def test_invalid_archetype_default_falls_back(tmp_path, monkeypatch):
    monkeypatch.setenv("CDMS_HOME", str(tmp_path))
    monkeypatch.setenv("CDMS_ARCHETYPE_DEFAULT", "nonsense-bot")
    cfg = load_config()
    assert cfg.archetype_default == "co-pilot"


# --------------------------------------------------------------------------- #
# Round-2 hardening: leash key-mismatch, near-bound-at-install, seeds-once
# --------------------------------------------------------------------------- #
def test_leash_distance_rejects_mismatched_dial_sets():
    """A dropped dial would silently UNDER-report drift and defeat the leash; a
    seed-only dial must not KeyError opaquely. Both must fail loud (Round-2 F2)."""
    seed = {"a": 0.5, "b": 0.5}
    with pytest.raises(ValueError):
        T.leash_distance({"a": 0.5, "b": 0.5, "c": 0.99}, seed)  # current-only dial
    with pytest.raises(ValueError):
        T.leash_distance({"a": 0.5}, seed)                       # seed-only dial
    with pytest.raises(ValueError):
        T.leash_exceeded({"a": 0.5, "c": 0.9}, seed, 0.3)        # propagates through


def test_no_preset_dial_is_near_bound_at_install():
    """Locks the band ≥ eps invariant: no archetype seeds a dial already at its bound
    (which would spuriously route to the proposal lever from day one)."""
    for arch in T.archetypes():
        for d in T.preset_dials(arch):
            assert not T.near_bound(d), f"{arch}/{d.name} is near_bound at install"


def test_existing_store_not_retro_changed_by_archetype_config(tmp_path):
    """Seeds-once guarantee: once a store is seeded, changing archetype_default on a
    later open must NOT retro-change the genotype (and the derived radius follows the
    stored archetype, not the new config) — Round-2 F5."""
    db = Database(Config(home=tmp_path, archetype_default="apprentice"))
    assert db.get_archetype() == "apprentice"
    db.close()
    db2 = Database(Config(home=tmp_path, archetype_default="maverick"))
    assert db2.get_archetype() == "apprentice"          # not retro-changed
    assert db2.get_archetype_radius() == 0.30            # apprentice radius, not 0.45
    db2.close()
