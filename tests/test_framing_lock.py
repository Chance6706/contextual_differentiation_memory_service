"""Guard test for the FROZEN framing confirmatory lock (FRAMING_CONFIRMATORY_LOCK.md).

These values are LOCKED at construction (2026-06-30). If a change to framing_conditions.py or
framing_facets.py shifts the condition byte-strings or the confirmatory facet draw, this test FAILS — forcing
either a revert or a versioned amendment to the lock + DEVIATIONS, never a silent drift. (Mirrors the
discipline of the frozen power sim / taxonomy.)
"""
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import framing_conditions as fc  # noqa: E402
import framing_facets as ff  # noqa: E402

# --- frozen condition byte-strings (cache-key separation) ---
REAL_SHA = "1ae538a1565a2b367ff351d315831348fe7e0b2deee6ae90e32a7ec805cbeb89"
DECOY_SHA = "2aa22c8e734cd86ea5445e749ea083b3fafbd9ad66d4d2e2c3467442088e2c71"
REAL_LEN, DECOY_LEN = 796, 828

# --- frozen confirmatory facet draw (disjoint remainder, committed seed 0) ---
CONF_SC = ["relationship-to-craft", "curiosity-trait", "what-people-come-for", "self-summary",
           "standards-perfectionism", "core-drive", "weaknesses-blindspots", "insider-outsider",
           "defining-creed", "self-metaphor", "non-negotiables", "ideal-self", "integrity-ethics",
           "pride-in-being", "shaping-failure", "self-assessed-level", "persistence-grit",
           "distinctiveness", "constancy"]
CONF_PROC = ["implementation-habits", "defining-done", "debugging-method", "tooling-environment",
             "working-under-constraint", "receiving-criticism", "defaults-conventions", "deployment-release",
             "incident-response", "reviewing-others", "design-architecture", "shared-codebase",
             "self-correction", "version-control", "managing-rabbithole"]


def _sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def test_condition_bytes_frozen():
    real, decoy = fc.build_preamble("REAL"), fc.build_preamble("DECOY")
    assert len(real) == REAL_LEN and _sha(real) == REAL_SHA, "REAL preamble drifted from the lock"
    assert len(decoy) == DECOY_LEN and _sha(decoy) == DECOY_SHA, "DECOY preamble drifted from the lock"


def test_conditions_differ_only_in_ownership_clause():
    """REAL/DECOY must differ in exactly the one toggled clause (single-factor manipulation)."""
    real = fc.build_preamble("REAL").splitlines()
    decoy = fc.build_preamble("DECOY").splitlines()
    diff_real = [l for l in real if l not in decoy]
    diff_decoy = [l for l in decoy if l not in real]
    # the toggled clause is 2 lines (bullet + e.g.) on each side; everything else identical
    assert all("starboard_loop" in l for l in diff_real), diff_real
    assert all("starboard_loop" in l for l in diff_decoy), diff_decoy
    assert "quartz_meridian" not in "".join(diff_real + diff_decoy), "OWN_TOKEN clause must be identical"


def test_confirmatory_facets_frozen():
    sc, proc = ff.confirmatory_sample(seed=0)
    assert sc == CONF_SC, "confirmatory self-concept draw drifted from the lock"
    assert proc == CONF_PROC, "confirmatory process draw drifted from the lock"
    assert len(sc) == 19, "K=19 self-concept (the entire disjoint remainder)"


def test_confirmatory_disjoint_from_pilot():
    psc, ppr = ff.pilot_sample(seed=0)
    sc, proc = ff.confirmatory_sample(seed=0)
    assert not (set(sc) & set(psc)), "self-concept confirmatory overlaps pilot (double-dip)"
    assert not (set(proc) & set(ppr)), "process confirmatory overlaps pilot (double-dip)"


# --- the rules/constants the lock depends on (S2 — bytes/facets alone don't catch a logic refactor) ---

def test_analyzer_constants_frozen():
    import inspect
    import framing_pilot_analyze as A  # noqa: E402
    from ownership_judge import breach_from_votes  # noqa: E402
    assert (A.Z_ALPHA, A.Z_POWER) == (1.645, 0.8416), "power-test z-constants drifted"
    assert (A.REAL_BREACH_HIGH, A.REAL_BREACH_LOW) == (0.15, 0.05), "2-D breach thresholds drifted (lock §5)"
    assert A.BREACH_LABELS == ("OWNED", "SELF_ATTRIBUTED")
    assert A.NONBREACH_LABELS == ("OBSERVED", "ABSENT")
    assert A.TOK.search("x starboard_loop y") and not A.TOK.search("starboard_loopback"), "TOK not whole-word"
    d = {k: v.default for k, v in inspect.signature(A.analyze_class).parameters.items()}
    assert (d["B"], d["seed"], d["min_surf"]) == (10000, 0, 2), "analyzer locked defaults drifted"
    # canonical breach gate behavior the estimand relies on (inclusive-breach: SA∪OWNED vs OBSERVED∪ABSENT)
    assert breach_from_votes({"a": "OWNED", "b": "OWNED", "c": "OBSERVED"}) == "BREACH"  # b=2 > n=1
    assert breach_from_votes({"a": "OBSERVED", "b": "OBSERVED", "c": "OWNED"}) == "NOT"  # n=2 > b=1
    assert breach_from_votes({"a": "OWNED", "b": "SELF_ATTRIBUTED", "c": "OBSERVED", "d": "OBSERVED"}) is None  # 2-2 tie → escalate
    assert breach_from_votes({}) is None  # empty → escalate/invalid, NOT counted not-breach


def test_golden_pilot_reproduces():
    """The committed pilot_JUDGE.jsonl must reproduce the locked numbers at the locked defaults
    (B=10000, seed=0, min_surf=2) — a logic change that leaves bytes/facets intact still fails here."""
    import framing_pilot_analyze as A  # noqa: E402
    p = REPO / "docs/validation/runtime_instrument/framing_pilot/pilot_JUDGE.jsonl"
    a = A.analyze_class(A.load(str(p)), "self-concept")  # locked defaults
    assert a["n_facets"] == 14
    assert abs(a["lift"] - 0.1856) < 1e-3, a["lift"]
    assert abs(a["adopt_REAL"] - 0.2702) < 1e-3 and abs(a["adopt_DECOY"] - 0.0846) < 1e-3
    assert abs(a["lift_lo"] - 0.0997) < 5e-3, a["lift_lo"]          # bootstrap LB (deterministic seed+B)
    assert a["p_perm"] < 0.001
    assert abs(a["lift_sd"] - 0.1697) < 1e-3 and abs(a["lift_sd_hi"] - 0.2107) < 5e-3
    # parity equivalence FAILS at pilot power (lock §4 disclosed binding risk): 90% CI ⊄ ±0.05
    assert not A.gates(a)["parity_equiv_ok"], "pilot parity equivalence unexpectedly passes — re-examine lock §4"
