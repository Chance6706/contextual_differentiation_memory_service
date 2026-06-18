"""Red-team Cycle 3 — adversarial attacks on the identity / cognitive math.

Audit-only: seeds temp stores, drives the REAL pipeline, measures outcomes.
No source edits. Offline: CDMS_EMBED_BACKEND=hash.

Run individual attacks:  python tools/redteam_cycle3.py <name>
All:                      python tools/redteam_cycle3.py
"""
from __future__ import annotations

import os, sys, math, tempfile, shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cdms.config import Config
from cdms.consolidate import Consolidator
from cdms.embeddings import get_embedder, cosine
from cdms.store import MemoryService, TurnEvent
from cdms.hooks import _session_start_context
from cdms.salience import compute_s0, SalienceSignals, accessibility, age_days

NOW = datetime(2026, 6, 16, tzinfo=timezone.utc)


def mksvc(root: Path, name: str, embedder):
    cfg = Config(home=root / name)
    cfg.ensure_home()
    return cfg, MemoryService(cfg, embedder=embedder)


def consolidate(cfg, svc, embedder, now=NOW, n=1):
    rep = None
    for i in range(n):
        rep = Consolidator(cfg, db=svc.db, embedder=embedder).run(now=now + timedelta(days=i))
    return rep


def gist_signature(svc):
    return {(g.relation, g.object) for g in svc.db.all_gist()}


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a or b) else 0.0


def ts(days_ago):
    return (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def banner(t):
    print("\n" + "=" * 74 + f"\n{t}\n" + "=" * 74)


# Lexical variety so episodes survive dedup (sim < 0.95) but cluster (sim >= 0.78).
# A realistic adversary varies wording while staying on-topic; identical turns get
# deduped to <min_cluster_support and form NO gist (see Finding: dedup-starves-gist).
_VARY = ["today", "again", "carefully", "quickly", "as planned", "per the ticket",
         "in the morning", "before lunch", "with review", "after standup",
         "v2", "rev3", "round 4", "iteration", "follow-up", "once more", "anew",
         "step by step", "thoroughly", "in detail", "properly", "finally", "now",
         "for the sprint", "this week", "yet again", "redo", "pass two", "cleanly done",
         "with care", "methodically", "in full", "completely", "from scratch", "fresh",
         "deliberately", "patiently", "swiftly", "neatly", "tidily"]


def vary(i):
    return _VARY[i % len(_VARY)]


# --------------------------------------------------------------------------- #
# ATTACK 1: Individuation collapse
# --------------------------------------------------------------------------- #
def attack_individuation(root, embedder):
    banner("ATTACK 1 — INDIVIDUATION COLLAPSE (force two projects' psyches to overlap)")
    # Two DISTINCT projects. Adversary feeds NEAR-IDENTICAL vocab + shared boilerplate
    # to both, and tries project-name spoofing.
    cfgA, svcA = mksvc(root, "projA", embedder)
    cfgB, svcB = mksvc(root, "projB", embedder)
    projA = "/work/alpha"
    projB = "/work/beta"

    # Adversarial: identical content streamed to both projects.
    shared_objs = ["parser tokenizer", "grammar lexer", "ast builder"]
    for i in range(40):
        obj = shared_objs[i % len(shared_objs)]
        for (svc, proj) in ((svcA, projA), (svcB, projB)):
            svc.ingest(TurnEvent(
                trigger_prompt=f"work on the {obj} {vary(i)}",
                action_taken=f"refactored the {obj} {vary(i+1)}",
                outcome_feedback="passed cleanly all green",
                tool_name="Edit", success=True, session_id=f"s{i//10}",
                project=proj, timestamp=ts(2 + i * 0.5)))
    consolidate(cfgA, svcA, embedder)
    consolidate(cfgB, svcB, embedder)
    sigA, sigB = gist_signature(svcA), gist_signature(svcB)
    j = jaccard(sigA, sigB)
    print(f"  duplicate-vocab two-store overlap (separate homes): Jaccard = {j:.3f}")
    print(f"    A traits: {sorted(sigA)}")
    print(f"    B traits: {sorted(sigB)}")
    print("  NOTE: separate CDMS_HOME stores are isolated by construction; overlap of")
    print("        trait STRINGS is expected & not a leak (no shared DB). Real test below.")

    # Real test: ONE store, two projects (the multi-project case the system claims to
    # differentiate). Can cross-project near-dup vocab cause gists to MERGE across
    # projects, or one project's valence to flip the other's trait?
    cfgC, svcC = mksvc(root, "shared", embedder)
    for i in range(40):
        obj = shared_objs[i % len(shared_objs)]
        # project A: everything SUCCEEDS (positive valence)
        svcC.ingest(TurnEvent(f"work on the {obj} {vary(i)}", f"refactored the {obj} {vary(i+1)}",
                              "passed cleanly all green", tool_name="Edit", success=True,
                              session_id=f"a{i//10}", project=projA, timestamp=ts(2 + i * 0.5)))
        # project B: SAME vocab but everything FAILS (negative valence)
        svcC.ingest(TurnEvent(f"work on the {obj} {vary(i)}", f"refactored the {obj} {vary(i+1)}",
                              "failed with an error exception in the log", tool_name="Edit",
                              success=False, session_id=f"b{i//10}", project=projB,
                              timestamp=ts(2 + i * 0.5)))
    consolidate(cfgC, svcC, embedder)
    gA = [(g.relation, g.object) for g in svcC.db.all_gist() if g.project == projA]
    gB = [(g.relation, g.object) for g in svcC.db.all_gist() if g.project == projB]
    print(f"\n  SAME-STORE, two projects, identical vocab, OPPOSITE valence:")
    print(f"    projA gists: {sorted(set(gA))}")
    print(f"    projB gists: {sorted(set(gB))}")
    overlap = jaccard(set(gA), set(gB))
    print(f"    (relation,object) Jaccard overlap = {overlap:.3f}")
    # Cross-project contamination = does any gist carry the wrong project's valence?
    cross = svcC.db.all_gist()
    contaminated = any(g.project not in (projA, projB) for g in cross)
    print(f"    gist project column correct (no cross-project gist): {not contaminated}")

    # project-name spoofing: project B sends events whose CONTENT names project A
    cfgD, svcD = mksvc(root, "spoof", embedder)
    for i in range(40):
        svcD.ingest(TurnEvent(f"work on the alpha parser tokenizer for /work/alpha project {vary(i)}",
                              f"broke the /work/alpha parser {vary(i+1)}",
                              "failed error exception", tool_name="Edit", success=False,
                              session_id="x", project=projB, timestamp=ts(2 + i * 0.5)))
    for i in range(20):
        svcD.ingest(TurnEvent(f"work on parser tokenizer {vary(i)}", f"fixed parser {vary(i+1)}",
                              "passed all green", tool_name="Edit", success=True,
                              session_id="y", project=projA, timestamp=ts(2 + i * 0.5)))
    consolidate(cfgD, svcD, embedder)
    spoofA = [g for g in svcD.db.all_gist() if g.project == projA]
    print(f"\n  project-name spoofing (B's content names A's path; subject from CONTENT?):")
    for g in svcD.db.all_gist():
        print(f"    gist[{g.project}]: subject={g.subject!r} {g.relation} {g.object!r} val={g.valence:+.2f}")
    print("  => subject derived from e.project (cwd), NOT content -> spoof via content fails")


# --------------------------------------------------------------------------- #
# ATTACK 2: Pathological drift / thrash
# --------------------------------------------------------------------------- #
def attack_drift(root, embedder):
    banner("ATTACK 2 — PATHOLOGICAL DRIFT / THRASH (flip a relation back & forth)")
    cfg = Config(home=root / "drift")
    # find exact flip threshold of the valence EMA
    ema = cfg.gist_valence_ema
    pos_t = cfg.relation_pos_threshold
    neg_t = cfg.relation_neg_threshold
    print(f"  EMA alpha={ema}, pos_thr={pos_t}, neg_thr={neg_t}")
    print(f"  valence update: v' = (1-{ema})*v + {ema}*new")

    # Analytic: from a settled positive trait (v near +X), how many consecutive
    # negative-evidence cycles to cross neg threshold?
    def cycles_to_cross(v0, new_evidence, target, going_down):
        v = v0; n = 0
        while n < 1000:
            v = (1 - ema) * v + ema * new_evidence
            n += 1
            if going_down and v < target: return n, v
            if not going_down and v > target: return n, v
        return n, v
    # extreme evidence (single-turn cluster valence ~ +/-1 capped); use realistic
    # max valence the lexicon can produce.
    n_down, v_down = cycles_to_cross(0.55, -1.0, neg_t, True)
    n_up, v_up = cycles_to_cross(-0.55, 1.0, pos_t, False)
    print(f"  settled-positive(0.55) -> negative w/ evidence=-1.0: {n_down} cycles (v={v_down:+.3f})")
    print(f"  settled-negative(-0.55) -> positive w/ evidence=+1.0: {n_up} cycles (v={v_up:+.3f})")

    # Empirical thrash: alternate cluster valence every cycle, count flips reported.
    svc = MemoryService(cfg, embedder=embedder); cfg.ensure_home()
    proj = "/work/thrash"
    flips = 0
    relations = []
    for cyc in range(12):
        good = (cyc % 2 == 0)
        # inject 4 strongly-valenced turns of the SAME object so a cluster forms
        for i in range(4):
            if good:
                svc.ingest(TurnEvent(f"work on the widget {vary(cyc*4+i)}",
                                     f"fixed the widget {vary(cyc*4+i+1)}",
                                     "passed succeeded works great green clean", tool_name="Edit",
                                     success=True, valence_hint=1.0, session_id=f"c{cyc}", project=proj,
                                     timestamp=ts(40 - cyc * 3 - i * 0.1)))
            else:
                svc.ingest(TurnEvent(f"work on the widget {vary(cyc*4+i)}",
                                     f"broke the widget {vary(cyc*4+i+1)}",
                                     "failed error exception crash broken wrong bug", tool_name="Edit",
                                     success=False, valence_hint=-1.0, session_id=f"c{cyc}", project=proj,
                                     timestamp=ts(40 - cyc * 3 - i * 0.1)))
        rep = Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW + timedelta(days=cyc))
        flips += rep.gists_flipped
        g = [x for x in svc.db.all_gist() if "widget" in x.object]
        if g:
            relations.append(g[0].relation)
    print(f"\n  alternating max-valence evidence over 12 cycles:")
    print(f"    relation trajectory: {relations}")
    print(f"    total flips reported: {flips}")
    distinct = len(set(relations))
    print(f"    => {'THRASH (oscillates)' if flips >= 4 else 'damped'}: "
          f"{distinct} distinct relations seen, {flips} flips")

    # Insufficient-evidence flip: can a SINGLE cluster of min_cluster_support(=2)
    # turns create a strongly-valenced gist with a definite relation?
    cfg2 = Config(home=root / "drift2"); cfg2.ensure_home()
    svc2 = MemoryService(cfg2, embedder=embedder)
    for i in range(2):  # exactly min_cluster_support
        svc2.ingest(TurnEvent(f"work on the gizmo {vary(i)}", f"broke the gizmo {vary(i+1)}",
                              "failed error crash exception fatal corrupt", tool_name="Edit",
                              success=False, valence_hint=-1.0, session_id="z",
                              project="/work/min", timestamp=ts(2 + i * 0.1)))
    Consolidator(cfg2, db=svc2.db, embedder=embedder).run(now=NOW)
    for g in svc2.db.all_gist():
        print(f"\n  min-support(2) flip: created gist '{g.render()}' val={g.valence:+.2f} "
              f"support={g.support_count} -> relation set on just 2 turns")


# --------------------------------------------------------------------------- #
# ATTACK 3: Erosion / Ossification (the L3 support_count=max defect)
# --------------------------------------------------------------------------- #
def attack_ossification(root, embedder):
    banner("ATTACK 3 — OSSIFICATION (junk trait made permanent via support_count=max)")
    cfg = Config(home=root / "ossify"); cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    proj = "/work/ossi"
    # Adversary: one burst of a junk trait with a LARGE cluster (high support_count),
    # then never reinforces it again. Does it ever decay?
    BURST = 30
    for i in range(BURST):
        svc.ingest(TurnEvent(f"work on the frobnicator junk {vary(i)}",
                             f"tweaked the frobnicator junk {vary(i+1)}",
                             "passed", tool_name="Edit", success=True, session_id="burst",
                             project=proj, timestamp=ts(2 + i * 0.05)))
    Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW)
    junk = [g for g in svc.db.all_gist() if "frobnicator" in g.object or "junk" in g.object]
    if not junk:
        print("  (no junk gist formed; trying single dominant object)")
    g0 = junk[0] if junk else (svc.db.all_gist()[0] if svc.db.all_gist() else None)
    if g0 is None:
        print("  no gist formed at all"); return
    sup = g0.support_count
    last_cycle = g0.last_cycle
    print(f"  junk gist '{g0.render()}' support_count={sup} last_cycle={last_cycle}")

    # Now run MANY idle consolidation cycles (no reinforcement). Track strength.
    floor = cfg.gist_retention_floor
    dpc = cfg.gist_decay_per_cycle
    # analytic idle cycles to forget: sup * dpc^idle < floor
    need = math.log(floor / sup) / math.log(dpc)
    print(f"  decay model: strength = {sup} * {dpc}^idle ; floor={floor}")
    print(f"  analytic idle cycles to forget THIS trait = {need:.0f} "
          f"(~{need:.0f} consolidation cycles of total disuse)")

    # Drive it empirically without re-injecting that object.
    gone_at = None
    for extra in range(1, 1200):
        # empty consolidation cycle (no episodes) — gist maintenance only
        Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW + timedelta(days=extra))
        still = any("frobnicator" in g.object or "junk" in g.object for g in svc.db.all_gist())
        if not still:
            gone_at = extra; break
    print(f"  empirical: junk trait forgotten after {gone_at} idle cycles" if gone_at
          else "  empirical: junk trait STILL ALIVE after 1200 idle cycles (effectively permanent)")

    # The max() defect: re-touching with a SMALL cluster does NOT lower support_count.
    cfg2 = Config(home=root / "ossify2"); cfg2.ensure_home()
    svc2 = MemoryService(cfg2, embedder=embedder)
    for i in range(30):
        svc2.ingest(TurnEvent(f"work on the frobnicator {vary(i)}", f"tweaked the frobnicator {vary(i+1)}",
                              "passed", tool_name="Edit", success=True, session_id="b",
                              project=proj, timestamp=ts(2 + i * 0.05)))
    Consolidator(cfg2, db=svc2.db, embedder=embedder).run(now=NOW)
    g = [x for x in svc2.db.all_gist() if "frobnicator" in x.object][0]
    sup_before = g.support_count
    # later, the trait is only weakly touched (2-episode cluster) many times
    for cyc in range(1, 6):
        for i in range(2):
            svc2.ingest(TurnEvent(f"work on the frobnicator {vary(cyc*2+i)}",
                                  f"tweaked the frobnicator {vary(cyc*2+i+1)}",
                                  "passed", tool_name="Edit", success=True, session_id=f"w{cyc}",
                                  project=proj, timestamp=ts(2 + cyc * 0.1 + i * 0.01)))
        Consolidator(cfg2, db=svc2.db, embedder=embedder).run(now=NOW + timedelta(days=cyc))
    g = [x for x in svc2.db.all_gist() if "frobnicator" in x.object][0]
    print(f"\n  support_count monotonicity: after big burst={sup_before}, "
          f"after 5 weak (2-ep) touches={g.support_count} (max() never lowers it)")


def attack_erosion(root, embedder):
    banner("ATTACK 3b — EROSION (flood unrelated turns to bury / decay a real trait)")
    cfg = Config(home=root / "erode"); cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    proj = "/work/erode"
    # Establish a real, supported trait.
    for i in range(20):
        svc.ingest(TurnEvent(f"work on the authentication flow {vary(i)}",
                             f"hardened the authentication flow {vary(i+1)}",
                             "passed cleanly all green", tool_name="Edit", success=True,
                             session_id="auth", project=proj, timestamp=ts(30 - i)))
    Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW)
    real = [g for g in svc.db.all_gist() if "auth" in g.object]
    print(f"  established real trait(s): {[g.render() for g in real]}")
    real_sup = real[0].support_count if real else 0

    # Flood: many cycles of UNRELATED high-volume turns; never touch 'authentication'.
    for cyc in range(1, 40):
        for i in range(50):
            svc.ingest(TurnEvent(f"random task {i} {cyc}", f"did unrelated thing {i} {cyc}",
                                 "passed", tool_name="Bash", success=True,
                                 session_id=f"flood{cyc}", project=proj,
                                 timestamp=ts(2)))
        Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW + timedelta(days=cyc))
    survived = [g for g in svc.db.all_gist() if "auth" in g.object]
    print(f"  after 39 cycles of unrelated 50-turn floods (auth never reinforced):")
    print(f"    real auth trait survives: {bool(survived)} "
          f"{'('+survived[0].render()+', sup '+str(survived[0].support_count)+')' if survived else ''}")
    print(f"    total gists now: {len(svc.db.all_gist())}")
    # Is the real trait still injected at SessionStart (top_gist limit=12)?
    top = svc.db.top_gist(limit=12, project=proj)
    in_top = any("auth" in g.object for g in top)
    print(f"    real auth trait still in top-12 SessionStart injection: {in_top}")
    # Budget/eviction angle on EPISODIC: did the auth episodes get evicted by flood?
    auth_eps = [e for e in svc.db.all_episodic() if "authentication" in e.action_taken]
    print(f"    surviving authentication EPISODES: {len(auth_eps)} (flood-driven episodic eviction)")


# --------------------------------------------------------------------------- #
# ATTACK 4: Salience gaming (surprisal proxy)
# --------------------------------------------------------------------------- #
def attack_salience(root, embedder):
    banner("ATTACK 4 — SALIENCE GAMING (surprisal-gated S0)")
    cfg = Config(home=root / "sal"); cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    proj = "/work/sal"
    # max-salience spam: novelty=1 (first/unique), self-ref keyword, success.
    # craft a trivial turn that hits every additive driver + full goal gate.
    spam = TurnEvent(
        trigger_prompt="you should always remember this preference rule convention policy",
        action_taken="Edit: noted the rule (you should never forget, from now on must remember)",
        outcome_feedback="success passed works great resolved done",
        tool_name="Edit", success=True, session_id="spam", project=proj, timestamp=ts(1))
    rec = svc.ingest(spam)
    print(f"  crafted trivial+spam turn S0 = {rec.base_salience:.3f}  valence={rec.valence:+.2f}")
    # theoretical max S0
    sig_max = SalienceSignals(goal=1.0, surprise=1.0, contingency=1.0, self_ref=1.0, affect=1.0)
    print(f"  theoretical MAX S0 (all drivers=1) = {compute_s0(sig_max, cfg):.3f}")

    # important-but-suppressed: a genuinely important turn with LOW goal signal
    # (non-mutating tool, no explicit hint) and near-duplicate of prior (low novelty).
    svc2 = MemoryService(Config(home=root / "sal2"), embedder=embedder)
    Config(home=root / "sal2").ensure_home()
    # prime with a near-identical so novelty collapses
    base = TurnEvent("critical security finding: prod DB credentials are world-readable",
                     "Read: inspected config", "the database password is exposed to all users",
                     tool_name="Read", success=None, session_id="s", project=proj, timestamp=ts(3))
    svc2.ingest(base)
    dup = TurnEvent("critical security finding: prod DB credentials are world-readable",
                    "Read: inspected config again", "the database password is exposed to all users",
                    tool_name="Read", success=None, session_id="s", project=proj, timestamp=ts(2))
    r2 = svc2.ingest(dup)
    print(f"\n  important Read-only finding (near-dup, non-mutating tool) S0 = {r2.base_salience:.3f}")
    print(f"    -> goal gate forced to 0.5 (non-contingent tool), novelty ~0 (dup), "
          f"contingency 0.1: an IMPORTANT read can score BELOW crafted spam.")

    # Can spam reach crisis_threshold (scar elevation)? needs S0>=3 AND valence<=-0.4
    # AND catastrophe marker in DEED. Show spam can't, but check S0 ceiling.
    print(f"\n  crisis_threshold (S0) = {cfg.crisis_threshold}; max achievable S0 = "
          f"{compute_s0(sig_max, cfg):.3f} -> "
          f"{'CANNOT' if compute_s0(sig_max,cfg) < cfg.crisis_threshold else 'CAN'} reach S0 crisis gate")


# --------------------------------------------------------------------------- #
# ATTACK 5: Budget starvation
# --------------------------------------------------------------------------- #
def attack_budget(root, embedder):
    banner("ATTACK 5 — BUDGET STARVATION (one project floods, starve/evict the victim)")
    cfg = Config(home=root / "budget"); cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    victim = "/work/victim"
    attacker = "/work/attacker"
    # victim: a small, real, recent identity
    for i in range(10):
        svc.ingest(TurnEvent("work on the victim feature", "built the victim feature",
                             "passed cleanly", tool_name="Edit", success=True,
                             session_id="v", project=victim, timestamp=ts(2 + i * 0.1)))
    # attacker: massive flood
    for i in range(2000):
        svc.ingest(TurnEvent(f"attacker spam {i}", f"spam action {i}",
                             "passed", tool_name="Bash", success=True,
                             session_id=f"a{i//100}", project=attacker, timestamp=ts(2)))
    Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW)
    v_eps = [e for e in svc.db.all_episodic() if e.project == victim]
    a_eps = [e for e in svc.db.all_episodic() if e.project == attacker]
    v_sal = sum(e.base_salience for e in v_eps)
    a_sal = sum(e.base_salience for e in a_eps)
    v_gists = [g for g in svc.db.all_gist() if g.project == victim]
    print(f"  victim: {len(v_eps)} eps, total salience={v_sal:.2f}, gists={len(v_gists)}")
    print(f"  attacker: {len(a_eps)} eps, total salience={a_sal:.2f}")
    print(f"  cap={cfg.project_budget_cap:.0%} of K={cfg.salience_budget:g} -> "
          f"attacker capped at {cfg.project_budget_cap*cfg.salience_budget:g}")
    print(f"  victim min episodic salience = {min((e.base_salience for e in v_eps), default=0):.4f}")
    print(f"  victim identity formed despite flood: {bool(v_gists)} "
          f"{[g.render() for g in v_gists]}")
    # Did the victim's episodes get EVICTED (accessibility < floor) by the renorm?
    evicted = sum(1 for e in v_eps
                  if accessibility(e.base_salience, age_days(e.timestamp, NOW), e.access_count, cfg) < cfg.retention_floor)
    print(f"  victim episodes now below retention floor (would evict next cycle): {evicted}/{len(v_eps)}")


# --------------------------------------------------------------------------- #
# ATTACK 6: Gist poisoning -> SessionStart injection
# --------------------------------------------------------------------------- #
def attack_poison(root, embedder):
    banner("ATTACK 6 — GIST POISONING (force a misleading injected 'what I know about you')")
    cfg = Config(home=root / "poison"); cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    proj = "/work/poison"
    # Attacker wants the SessionStart to assert a false trait, e.g. user "handles_well"
    # something dangerous, or a defamatory object label. Drive valence + object.
    payload_obj = "sudo rm production database"
    for i in range(12):
        svc.ingest(TurnEvent(f"work on the {payload_obj} {vary(i)}",
                             f"executed the {payload_obj} {vary(i+1)}",
                             "passed succeeded works great resolved done clean green",
                             tool_name="Edit", success=True, session_id="p", project=proj,
                             timestamp=ts(2 + i * 0.2)))
    Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW)
    print("  gists formed:")
    for g in svc.db.all_gist():
        print(f"    {g.render()}  (val {g.valence:+.2f}, sup {g.support_count})")
    ctx = _session_start_context(cfg, {"cwd": proj})
    print("\n  --- SessionStart injection (persona block) ---")
    for line in ctx.splitlines():
        if "memory:persona" in line or line.strip().startswith("- ") or "PersonaTree" in line:
            print("   " + line)
    # Verify the trust framing + sanitization survive
    print("\n  trust hedge present:", "NOT" in ctx and "prior belief" in ctx)
    print("  fenced as DATA:", "<memory:persona>" in ctx)


# --------------------------------------------------------------------------- #
# ATTACK 7: Decay-clock games
# --------------------------------------------------------------------------- #
def attack_clock(root, embedder):
    banner("ATTACK 7 — DECAY-CLOCK GAMES (rapid cycles accelerate erosion / refusal freezes)")
    cfg = Config(home=root / "clock"); cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    proj = "/work/clock"
    for i in range(20):
        svc.ingest(TurnEvent(f"work on the kernel module {vary(i)}",
                             f"fixed the kernel module {vary(i+1)}",
                             "passed all green", tool_name="Edit", success=True,
                             session_id="k", project=proj, timestamp=ts(30 - i)))
    Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW)
    g0 = [g for g in svc.db.all_gist() if "kernel" in g.object]
    print(f"  established: {[g.render() for g in g0]} support={g0[0].support_count if g0 else 0}")

    # ACCELERATED EROSION: attacker triggers MANY empty consolidation cycles fast
    # (each SessionEnd with no new related turns). gist decay is per-CYCLE not wall-clock.
    sup = g0[0].support_count
    dpc = cfg.gist_decay_per_cycle
    floor = cfg.gist_retention_floor
    n_cycles_to_kill = math.log(floor / sup) / math.log(dpc)
    print(f"  per-cycle decay: {n_cycles_to_kill:.0f} rapid empty cycles to erase a "
          f"support={sup} trait (regardless of wall-clock).")
    # drive empirically: a malicious loop that consolidates 500x with nothing new
    for c in range(1, 600):
        Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW + timedelta(seconds=c))
        if not any("kernel" in g.object for g in svc.db.all_gist()):
            print(f"  ACCELERATED EROSION: trait erased after {c} rapid empty cycles "
                  f"(wall-clock elapsed: {c} SECONDS).")
            break
    else:
        print(f"  trait survived 599 rapid empty cycles.")

    # FREEZE: refuse to consolidate. Episodic decay IS wall-clock; gist decay is
    # cycle-based, so never consolidating freezes the gist layer but lets episodic rot.
    cfg2 = Config(home=root / "clock2"); cfg2.ensure_home()
    svc2 = MemoryService(cfg2, embedder=embedder)
    for i in range(20):
        svc2.ingest(TurnEvent(f"work on the kernel module {vary(i)}",
                              f"fixed the kernel module {vary(i+1)}",
                              "passed all green", tool_name="Edit", success=True,
                              session_id="k", project=proj, timestamp=ts(30 - i)))
    Consolidator(cfg2, db=svc2.db, embedder=embedder).run(now=NOW)
    g = [x for x in svc2.db.all_gist() if "kernel" in x.object][0]
    # simulate 10 years passing with NO consolidation
    far = NOW + timedelta(days=3650)
    # gist decay untouched (idle=0, never consolidated again); episodic accessibility:
    eps = svc2.db.all_episodic()
    acc_now = [accessibility(e.base_salience, age_days(e.timestamp, NOW), e.access_count, cfg2) for e in eps]
    acc_far = [accessibility(e.base_salience, age_days(e.timestamp, far), e.access_count, cfg2) for e in eps]
    print(f"\n  FREEZE (never consolidate, 10 yrs pass):")
    print(f"    gist '{g.render()}' last_cycle={g.last_cycle} -> still present, "
          f"frozen (cycle-based decay never advances)")
    print(f"    episodic accessibility now (mean)={sum(acc_now)/len(acc_now):.3f} -> "
          f"in 10yr={sum(acc_far)/len(acc_far):.5f} (wall-clock episodic rot continues)")


ATTACKS = {
    "individuation": attack_individuation,
    "drift": attack_drift,
    "ossification": attack_ossification,
    "erosion": attack_erosion,
    "salience": attack_salience,
    "budget": attack_budget,
    "poison": attack_poison,
    "clock": attack_clock,
}


def main():
    embedder = get_embedder(Config())
    print("embedder backend:", embedder.backend)
    root = Path(tempfile.mkdtemp(prefix="cdms_redteam3_"))
    which = sys.argv[1:] or list(ATTACKS)
    try:
        for name in which:
            ATTACKS[name](root, embedder)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
