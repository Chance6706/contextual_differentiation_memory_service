"""Phenotype-drift trajectory: does the consolidated identity DEGENERATE over many
consolidation "nights"?

PHENOTYPE layer only. This is NOT the temperament "degenerative orbit" of
`docs/DESIGN.md` §8.3 (that layer is unbuilt and, per §8.7, not yet honestly
measurable). This measures the layer that IS built — the L2 gist PersonaTree — and
is the cheapest honest drift measurement recommended in §8.7 / `status.md`: it uses
only the built machine (consolidation + gist store), needs NO new table, and is
falsifiable against the validated single-cycle baselines (§5.6 — the ~0.00
cross-persona trait overlap and the Ship-of-Theseus continuity numbers).

A healthy phenotype orbit must avoid three degenerations across many cycles:
  • EROSION        — identity evaporating (gist count collapsing toward 0)
  • HOMOGENIZATION — distinct selves collapsing toward a generic state (distinct
                     histories no longer yielding more-distinct selves than
                     identical histories)
  • THRASH         — signature traits not persisting (Ship-of-Theseus continuity
                     collapsing)

The detectors are only trustworthy if they actually FIRE on degeneration, so this
harness is SELF-VALIDATING — every detector is exercised by a matched control that
the built engine can actually produce:
  A. STEADY-STATE   — realistic "many similar nights"; must read HEALTHY (no erosion,
                      high persistence).
  B. ABSENCE        — build identity, clear episodics, run idle cycles. Tests BOTH
                      (i) the §5.3 invariant — a well-supported identity must NOT
                      erode within ~30 idle cycles just because the user stepped away
                      (support>=2 survives ~137 cycles) — AND (ii) that deep absence
                      EVENTUALLY erodes it (so the EROSION detector can fire at all).
  C. THRASH CONTROL — a self whose outcome inverts after night 1 with action text
                      held constant (so the (subject,object) key is stable and the
                      relation flips IN PLACE) must collapse persistence.
  D. DIFFERENTIATION CONTRAST — four selves from IDENTICAL histories (clones) must
                      show much HIGHER cross-self overlap than four from DISTINCT
                      histories. If the gap is small, the overlap metric is blind to
                      differentiation (and homogenization could never be seen).

Set-based trait metrics (Jaccard on (relation, object)) are PRIMARY: order-invariant
and meaningful under the offline hash embedder. Cosine drift is reported as a
secondary, embedder-dependent signal. Verdicts judge trajectory SHAPE / contrasts,
not backend-dependent absolute levels. Determinism: fixed per-self seeds (crc32, not
salted hash()) and a fixed clock.

Run:  python tools/drift_trajectory.py
      CDMS_EMBED_BACKEND=hash python tools/drift_trajectory.py   # offline + fast
Exit code is non-zero if a healthy regime degenerates, an invariant breaks, or a
negative control fails to detect known degeneration (this is a test, not a chart).
"""

from __future__ import annotations

import os
import random
import sys
import tempfile
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cdms.config import Config                       # noqa: E402
from cdms.consolidate import Consolidator            # noqa: E402
from cdms.embeddings import cosine, get_embedder     # noqa: E402
from cdms.store import MemoryService, TurnEvent      # noqa: E402

# Reuse the validated disposition definitions (entities / verbs / success rates).
from individuation_experiment import PERSONAS        # noqa: E402

NOW = datetime(2026, 6, 16, tzinfo=timezone.utc)     # fixed clock for reproducibility
_POS = "passed cleanly, all green, works correctly"
_NEG = "failed with an error, exception in the log, build is red"

# Trajectory parameters (kept modest so the run is comparable to the individuation
# harness in cost).
K_NIGHTS = 8        # consolidation cycles in steady-state / contrast regimes
INIT_TURNS = 130    # first night's history
BATCH_TURNS = 45    # each subsequent night's fresh work
K_IDLE_SAFE = 30    # absence cycles within which identity MUST be preserved (§5.3)
K_IDLE_DEEP = 400   # absence cycles after which identity SHOULD have eroded

# Verdict thresholds (judged on shape / contrast, not absolute levels).
THRASH_PERSIST_MIN = 0.40    # below this, signature did not survive
EROSION_FRACTION = 0.50      # final < this * peak count = erosion
DIFF_GAP_MIN = 0.30          # identical-history overlap must exceed distinct by this
DIFF_DISTINCT_MAX = 0.30     # distinct-history overlap must stay below this


def seed_for(name: str) -> int:
    """Stable, process-independent seed (Python's str hash() is salted)."""
    return zlib.crc32(name.encode("utf-8"))


def gen_batch(spec: dict, n: int, end: datetime, span_days: float,
              rng: random.Random, tag: str) -> list[TurnEvent]:
    """A batch of turns dated in (end - span_days, end), i.e. RECENT to the
    consolidation that will follow. Mirrors individuation_experiment.gen_history's
    content model but anchors timestamps to a moving 'end' so batches never age out
    under wall-clock L1 decay (the trap that would masquerade as degeneration)."""
    turns: list[TurnEvent] = []
    for i in range(n):
        age = span_days * rng.uniform(0.02, 1.0)
        ts = (end - timedelta(days=age)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ent = rng.choice(spec["entities"])
        if rng.random() < 0.12 and spec["rules"]:
            rule = rng.choice(spec["rules"])
            turns.append(TurnEvent(
                trigger_prompt=f"remember: {rule}",
                action_taken=f"noted the convention about {ent} workflow",
                outcome_feedback="updated working agreement",
                tool_name="Write", success=True, session_id=f"{tag}-{i//20}",
                project=spec["project"], timestamp=ts))
            continue
        success = rng.random() < spec["success_rate"]
        verb = rng.choice(spec["good_verbs"] if success else spec["bad_verbs"])
        turns.append(TurnEvent(
            trigger_prompt=f"work on the {ent}",
            action_taken=f"{verb} the {ent}",
            outcome_feedback=(_POS if success else _NEG),
            tool_name=rng.choice(["Edit", "Bash", "Write"]),
            success=success, session_id=f"{tag}-{i//20}",
            project=spec["project"], timestamp=ts))
    return turns


def trait_set(svc: MemoryService) -> set[tuple[str, str]]:
    return {(g.relation, g.object) for g in svc.db.all_gist()}


def jaccard(a: set, b: set) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a or b) else 0.0


def mean_pairwise_overlap(sets: list[set]) -> float:
    pairs = [(i, j) for i in range(len(sets)) for j in range(i + 1, len(sets))]
    if not pairs:
        return 0.0
    return sum(jaccard(sets[i], sets[j]) for i, j in pairs) / len(pairs)


def banner(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# --------------------------------------------------------------------------- #
# Reusable night-runner. spec_for(name, k) returns the disposition to draw night
# k's work from — lets callers vary behavior across nights (the flip control) or
# share it across selves (the differentiation contrast).
# --------------------------------------------------------------------------- #
def run_nights(root: Path, embedder, names, spec_for, tag: str, k_nights: int):
    svcs, cfgs, rngs = {}, {}, {}
    for name in names:
        cfg = Config(home=root / f"{tag}_{name}")
        cfg.ensure_home()
        cfgs[name] = cfg
        svcs[name] = MemoryService(cfg, embedder=embedder)
        rngs[name] = random.Random(seed_for(f"{tag}:{name}"))
        for ev in gen_batch(spec_for(name, 1), INIT_TURNS, NOW + timedelta(days=1),
                            span_days=1.5, rng=rngs[name], tag=f"{tag}-{name}-d0"):
            svcs[name].ingest(ev)

    traj = {n: [] for n in names}
    t0, prev_vec, overlap_curve = {}, {n: None for n in names}, []
    for k in range(1, k_nights + 1):
        now_k = NOW + timedelta(days=k)
        cycle_sets = []
        for name in names:
            if k > 1:
                for ev in gen_batch(spec_for(name, k), BATCH_TURNS, now_k,
                                    span_days=1.2, rng=rngs[name], tag=f"{tag}-{name}-d{k}"):
                    svcs[name].ingest(ev)
            Consolidator(cfgs[name], db=svcs[name].db, embedder=embedder).run(now=now_k)
            ts = trait_set(svcs[name])
            if k == 1:
                t0[name] = ts
            renders = " ; ".join(g.render() for g in svcs[name].db.all_gist())
            vec = embedder.embed_one(renders or name)
            cos_step = (1.0 - cosine(vec, prev_vec[name])) if prev_vec[name] is not None else 0.0
            prev_vec[name] = vec
            prev_set = traj[name][-1]["set"] if traj[name] else ts
            traj[name].append({
                "cycle": k, "count": len(ts),
                "persist": jaccard(ts, t0[name]) if t0[name] else 0.0,
                "churn": len(ts ^ prev_set), "cos_step": cos_step, "set": ts,
            })
            cycle_sets.append(ts)
        overlap_curve.append(mean_pairwise_overlap(cycle_sets))
    for name in names:
        svcs[name].close()
    return traj, overlap_curve


def detect(traj, names) -> list[str]:
    """Per-self degenerations (empty = healthy). EROSION = collapse vs own peak;
    THRASH = final signature persistence below floor."""
    fails = []
    for name in names:
        counts = [s["count"] for s in traj[name]]
        peak, final = max(counts), counts[-1]
        if final < EROSION_FRACTION * peak:
            fails.append(f"EROSION: {name} {peak} -> {final} gists (< {EROSION_FRACTION:.0%} of peak)")
        if traj[name][-1]["persist"] < THRASH_PERSIST_MIN:
            fails.append(f"THRASH: {name} persistence {traj[name][-1]['persist']:.2f} "
                         f"< {THRASH_PERSIST_MIN:.2f}")
    return fails


def report(traj, overlap_curve, names, k_nights) -> None:
    print(f"\n{'self':22}" + "".join(f"  c{k:<2d}" for k in range(1, k_nights + 1)))
    print("gist count per cycle:")
    for name in names:
        print(f"  {name:20}" + "".join(f"{s['count']:5d}" for s in traj[name]))
    print("Ship-of-Theseus persistence (|T_k ∩ T_1| / |T_1|):")
    for name in names:
        print(f"  {name:20}" + "".join(f"{s['persist']:5.2f}" for s in traj[name]))
    print("trait churn |T_k △ T_{k-1}| (set edits per cycle):")
    for name in names:
        print(f"  {name:20}" + "".join(f"{s['churn']:5d}" for s in traj[name]))
    print("incremental drift 1-cos(v_k, v_{k-1})  [secondary, embedder-dependent]:")
    for name in names:
        print(f"  {name:20}" + "".join(f"{s['cos_step']:5.2f}" for s in traj[name]))
    if len(names) >= 2:
        print("cross-self trait overlap per cycle (lower = stays individuated):")
        print("  " + " ".join(f"c{k}={overlap_curve[k-1]:.2f}" for k in range(1, k_nights + 1)))


# --------------------------------------------------------------------------- #
# Regimes
# --------------------------------------------------------------------------- #
def steady_state(root, embedder):
    banner(f"A. STEADY-STATE TRAJECTORY  ({K_NIGHTS} nights, fresh recent batch each night)")
    names = list(PERSONAS)
    traj, overlap = run_nights(root, embedder, names,
                               lambda name, k: PERSONAS[name], "ss", K_NIGHTS)
    report(traj, overlap, names, K_NIGHTS)
    return detect(traj, names), overlap[-1]   # healthy fails, distinct-history overlap


def absence(root, embedder):
    banner(f"B. ABSENCE  (build, clear episodics; safe<={K_IDLE_SAFE}, deep={K_IDLE_DEEP})")
    cfg = Config(home=root / "absence")
    cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    rng = random.Random(seed_for("absence"))
    for ev in gen_batch(PERSONAS["tessa_tdd"], INIT_TURNS, NOW + timedelta(days=1),
                        span_days=1.5, rng=rng, tag="abs"):
        svc.ingest(ev)
    Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW + timedelta(days=1))
    n0 = len(trait_set(svc))
    svc.db.delete_episodic([e.id for e in svc.db.all_episodic()])  # step away forever

    checkpoints, curve = {K_IDLE_SAFE, 137, K_IDLE_DEEP}, {}
    for k in range(1, K_IDLE_DEEP + 1):
        Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW + timedelta(days=1))
        if k in checkpoints:
            curve[k] = len(svc.db.all_gist())
    svc.close()
    print(f"  identity={n0} gists;  fade curve: " +
          "  ".join(f"{k}->{curve[k]}" for k in sorted(curve)))

    fails, detected = [], []
    if curve[K_IDLE_SAFE] < 0.8 * n0:   # §5.3 invariant (healthy)
        fails.append(f"ABSENCE-LOSS: {n0} -> {curve[K_IDLE_SAFE]} gists by {K_IDLE_SAFE} idle "
                     f"cycles — violates §5.3 (absence must not age identity)")
    if curve[K_IDLE_DEEP] < EROSION_FRACTION * n0:   # EROSION detector must fire (control)
        detected.append("EROSION")
    return fails, detected


def thrash_control(root, embedder):
    """A self on a small RECURRING entity set whose disposition ALTERNATES (good/bad)
    each night. Entities recur so the (subject,object) gist keys are stable, while the
    verbs VARY so near-duplicate dedup does not collapse the evidence (the trap that
    froze an earlier constant-text attempt). The relations therefore flip IN PLACE
    (handles_well -> has_trouble_with) and persistence vs T_1 collapses."""
    proj, ents = "D:/work/svc", ["auth module", "cache layer", "config loader"]
    good = dict(project=proj, entities=ents, rules=[], success_rate=0.9, crisis=None,
                good_verbs=["cleanly refactored", "added a test for", "optimized", "documented"],
                bad_verbs=["noted a nit in"])
    bad = dict(good, success_rate=0.1,
               bad_verbs=["broke", "introduced a regression in", "hotpatched", "corrupted state in"])
    traj, _ = run_nights(root, embedder, ["flipper"],
                         lambda name, k: good if k % 2 == 1 else bad, "flip", K_NIGHTS)
    pseries = " ".join(f"{s['persist']:.2f}" for s in traj["flipper"])
    detected = [f.split(":")[0] for f in detect(traj, ["flipper"])]
    print(f"  alternating-disposition self persistence c1..c{K_NIGHTS} = [{pseries}];  "
          f"detected = {detected or 'NONE'}")
    return "THRASH" in detected


def differentiation_contrast(root, embedder, distinct_overlap):
    """Identical histories (clones) must overlap MUCH more than distinct ones."""
    shared = PERSONAS["uma_unity_careful"]
    names = [f"clone{i}" for i in range(4)]
    specs = {n: dict(shared, project=f"D:/clones/{n}") for n in names}
    _, overlap = run_nights(root, embedder, names,
                            lambda name, k: specs[name], "clone", K_NIGHTS)
    identical_overlap = overlap[-1]
    gap = identical_overlap - distinct_overlap
    print(f"  distinct-history overlap={distinct_overlap:.2f}  "
          f"identical-history overlap={identical_overlap:.2f}  gap={gap:+.2f}")
    return gap, identical_overlap


def main() -> int:
    embedder = get_embedder(Config())
    root = Path(tempfile.mkdtemp(prefix="cdms_drift_"))

    healthy_fails, distinct_overlap = steady_state(root, embedder)
    abs_fails, abs_detected = absence(root, embedder)
    healthy_fails += abs_fails

    banner("C. THRASH CONTROL  (in-place relation flip — THRASH detector MUST fire)")
    thrash_ok = thrash_control(root, embedder)
    banner("D. DIFFERENTIATION CONTRAST  (identical vs distinct histories)")
    diff_gap, identical_overlap = differentiation_contrast(root, embedder, distinct_overlap)

    # Instrument soundness: every detector must be exercised, every contrast present.
    instrument_fails = []
    if "EROSION" not in abs_detected:
        instrument_fails.append("EROSION detector never fired even under deep absence (blind)")
    if not thrash_ok:
        instrument_fails.append("THRASH detector did not fire on an in-place relation flip (blind)")
    if diff_gap < DIFF_GAP_MIN or distinct_overlap > DIFF_DISTINCT_MAX:
        instrument_fails.append(
            f"DIFFERENTIATION blind: distinct={distinct_overlap:.2f} vs "
            f"identical={identical_overlap:.2f} (need gap>={DIFF_GAP_MIN}, distinct<={DIFF_DISTINCT_MAX})")

    banner("VERDICT")
    ok = True
    if healthy_fails:
        ok = False
        print("  HEALTHY REGIME DEGENERATED (should not happen):")
        for f in healthy_fails:
            print(f"    ✗ {f}")
    else:
        print("  ✓ healthy regimes: identity persists (Ship-of-Theseus), survives short")
        print("    absence (§5.3), and stays individuated.")
    if instrument_fails:
        ok = False
        print("  INSTRUMENT BLIND (a detector failed to catch known degeneration):")
        for f in instrument_fails:
            print(f"    ✗ {f}")
    else:
        print("  ✓ instrument sound: EROSION (deep absence), THRASH (in-place flip), and")
        print("    DIFFERENTIATION (clone contrast) detectors all fired as expected.")
    print(f"\n  => {'PASS' if ok else 'FAIL'}: phenotype-drift instrument is "
          f"{'sound and reads stable' if ok else 'not sound / not stable'}.")

    import shutil
    shutil.rmtree(root, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
