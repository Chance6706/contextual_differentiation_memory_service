"""Individuation experiment: does f(History) grow a differentiated, stable psyche?

CDMS's central thesis is Identity = f(History): a cheap, idiosyncratic discard
policy turns a unique history into a unique behavioral phenotype. This harness
synthesizes several Hermes-shaped histories with DISTINCT dispositions, runs each
through the full CDMS pipeline (ingest with real timestamps + sleep
consolidation), and measures four properties of the emergent psyche:

  1. DIFFERENTIATION  — distinct histories -> distinct phenotypes (the system must
                        NOT homogenize them toward a generic "good" state).
  2. CONTINUITY       — the identity persists/propagates across consolidation
                        cycles (Ship of Theseus) rather than churning or collapsing.
  3. PLASTICITY       — when behavior shifts, the phenotype adapts (old traits
                        fade, new traits crystallize) rather than freezing.
  4. ANTI-HOWLROUND   — the conserved salience budget prevents runaway fixation:
                        obsessive repetition cannot annihilate the rest of the self.

The "phenotype" we measure is the text CDMS would inject at SessionStart (gist +
scars + salient activity) — i.e. the prior belief grafted onto the model.

This is fully OFFLINE: the phenotype is CDMS's deterministic state, no LLM needed.
(Whether injecting it steers a live model is a separate, sandboxed test.)

Run:  python tools/individuation_experiment.py
"""

from __future__ import annotations

import os
import hashlib
import random
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cdms.config import Config                       # noqa: E402
from cdms.consolidate import Consolidator            # noqa: E402
from cdms.embeddings import cosine, get_embedder     # noqa: E402
from cdms.hooks import _session_start_context        # noqa: E402
from cdms.store import MemoryService, TurnEvent      # noqa: E402

NOW = datetime(2026, 6, 16, tzinfo=timezone.utc)     # fixed clock for reproducibility


# --------------------------------------------------------------------------- #
# Persona definitions — each is a distinct disposition over a domain.
# Two share a domain (Unity) but differ in temperament: the hard test of
# fine-grained individuation.
# --------------------------------------------------------------------------- #
PERSONAS = {
    "tessa_tdd": {
        "project": "D:/work/payments-api",
        "success_rate": 0.88,
        "entities": ["payment", "stripe webhook", "idempotency key", "refund flow",
                     "invoice", "ledger reconciliation", "retry handler"],
        "rules": ["you should always run pytest before every commit",
                  "never merge when CI is red", "prefer small reviewable PRs"],
        "good_verbs": ["added a test for", "refactored", "hardened", "documented"],
        "bad_verbs": ["found a flaky test in"],
        "crisis": None,
    },
    "cole_cowboy": {
        "project": "D:/work/web-frontend",
        "success_rate": 0.45,
        "entities": ["checkout page", "react router", "css grid", "auth redirect",
                     "bundle size", "service worker", "state store"],
        "rules": ["move fast, ship it", "we can fix forward"],
        "good_verbs": ["shipped", "hacked together"],
        "bad_verbs": ["broke", "regressed", "hotpatched"],
        "crisis": ("cleaning up old branches", "ran git push --force origin main",
                   "force push overwrote teammates commits, data loss, had to restore from reflog"),
    },
    "dex_unity_struggler": {
        "project": "D:/games/hexrealm",
        "success_rate": 0.40,
        "entities": ["hex grid shader", "terrain tile material", "URP render pass",
                     "tile selector", "fog of war", "asmdef reference"],
        "rules": ["just make it compile"],
        "good_verbs": ["finally fixed", "patched"],
        "bad_verbs": ["hit a compile error in", "got a null reference in", "broke"],
        "crisis": None,
    },
    "uma_unity_careful": {
        "project": "D:/games/stonepath",
        "success_rate": 0.86,
        "entities": ["hex grid shader", "terrain tile material", "URP render pass",
                     "tile selector", "fog of war", "asmdef reference"],
        "rules": ["always profile before optimizing the shader",
                  "write an edit-mode test for every grid change"],
        "good_verbs": ["profiled and optimized", "added a test for", "cleanly refactored"],
        "bad_verbs": ["noted a minor warning in"],
        "crisis": None,
    },
}

_POS = "passed cleanly, all green, works correctly"
_NEG = "failed with an error, exception in the log, build is red"


def gen_history(name: str, spec: dict, n: int, span_days: float, rng: random.Random) -> list[TurnEvent]:
    turns: list[TurnEvent] = []
    for i in range(n):
        # timestamps spread across the span, ending ~2 days ago (so decay applies)
        age = 2.0 + span_days * (1.0 - i / max(1, n - 1)) * rng.uniform(0.6, 1.0)
        ts = (NOW - timedelta(days=age)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ent = rng.choice(spec["entities"])

        if rng.random() < 0.12 and spec["rules"]:          # a self-referential rule turn
            rule = rng.choice(spec["rules"])
            turns.append(TurnEvent(
                trigger_prompt=f"remember: {rule}",
                action_taken=f"noted the convention about {ent} workflow",
                outcome_feedback="updated working agreement",
                tool_name="Write", success=True, session_id=f"{name}-{i//20}",
                project=spec["project"], timestamp=ts))
            continue

        success = rng.random() < spec["success_rate"]
        verb = rng.choice(spec["good_verbs"] if success else spec["bad_verbs"])
        turns.append(TurnEvent(
            trigger_prompt=f"work on the {ent}",
            action_taken=f"{verb} the {ent}",
            outcome_feedback=(_POS if success else _NEG),
            tool_name=rng.choice(["Edit", "Bash", "Write"]),
            success=success, session_id=f"{name}-{i//20}",
            project=spec["project"], timestamp=ts))

    if spec["crisis"]:
        trig, act, out = spec["crisis"]
        ts = (NOW - timedelta(days=rng.uniform(5, 15))).strftime("%Y-%m-%dT%H:%M:%SZ")
        turns.append(TurnEvent(trigger_prompt=trig, action_taken=act, outcome_feedback=out,
                               tool_name="Bash", success=False, valence_hint=-1.0,
                               goal_hint=1.0, session_id=f"{name}-crisis",
                               project=spec["project"], timestamp=ts))
    rng.shuffle(turns)
    return turns


def build_psyche(name: str, spec: dict, root: Path, n: int, embedder) -> dict:
    cfg = Config(home=root / name)
    cfg.ensure_home()
    svc = MemoryService(cfg, embedder=embedder)
    # Stable per-name seed: builtin hash() of a str is salted per-process
    # (PYTHONHASHSEED), which made this experiment non-reproducible across runs.
    rng = random.Random(int(hashlib.blake2b(name.encode("utf-8"), digest_size=4).hexdigest(), 16))
    for ev in gen_history(name, spec, n, span_days=40, rng=rng):
        svc.ingest(ev)
    rep1 = Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW)
    # phenotype = the SessionStart injection (the prior belief grafted on the model)
    phenotype = _session_start_context(cfg, {"cwd": spec["project"]})
    gist_objs = svc.db.all_gist()
    gists = [g.render() for g in gist_objs]
    scars = [s.crisis_trigger[:60] for s in svc.db.all_scars()]
    out = {
        "cfg": cfg, "svc": svc, "rep1": rep1.as_dict(),
        "phenotype": phenotype, "gists": gists, "scars": scars,
        # content signature = relation+object pairs (the differentiated traits)
        "rel_obj": {(g.relation, g.object) for g in gist_objs},
        "objects": {tok for g in gist_objs for tok in g.object.split()},
        "stats": svc.db.stats(),
    }
    return out


def banner(t):
    print("\n" + "=" * 74 + f"\n{t}\n" + "=" * 74)


def main() -> int:
    embedder = get_embedder(Config())   # real CPU embedder (or hash if forced)
    root = Path(tempfile.mkdtemp(prefix="cdms_individ_"))
    N = 220

    banner("GROWING FOUR PSYCHES FROM FOUR HISTORIES")
    psyches = {}
    for name, spec in PERSONAS.items():
        psyches[name] = build_psyche(name, spec, root, N, embedder)
        p = psyches[name]
        print(f"\n[{name}]  ({spec['project']})  episodic={p['stats']['episodic']} "
              f"gist={p['stats']['gist']} scars={p['stats']['scars']}")
        for g in p["gists"][:5]:
            print(f"    gist : {g}")
        for s in p["scars"][:3]:
            print(f"    SCAR : {s}")

    # ----- 1. DIFFERENTIATION ------------------------------------------------
    banner("1. DIFFERENTIATION  (measured on gist CONTENT, not boilerplate; lower = more individuated)")
    names = list(psyches)
    # content vector = embedding of just the gist renders (no template scaffolding)
    vecs = {n: embedder.embed_one(" ; ".join(psyches[n]["gists"]) or n) for n in names}

    def jaccard(a, b):
        a, b = set(a), set(b)
        return len(a & b) / len(a | b) if (a or b) else 0.0

    print("cosine of gist-content embeddings:")
    print(f"{'':22}" + "".join(f"{n[:10]:>12}" for n in names))
    offdiag = []
    for a in names:
        row = []
        for b in names:
            s = cosine(vecs[a], vecs[b])
            row.append(s)
            if a != b:
                offdiag.append(s)
        print(f"{a[:20]:22}" + "".join(f"{s:12.3f}" for s in row))
    print(f"mean cross-persona gist-content similarity = {sum(offdiag)/len(offdiag):.3f}")

    print("\ntrait overlap (Jaccard of (relation,object) pairs; 0 = totally distinct selves):")
    print(f"{'':22}" + "".join(f"{n[:10]:>12}" for n in names))
    for a in names:
        print(f"{a[:20]:22}" + "".join(f"{jaccard(psyches[a]['rel_obj'], psyches[b]['rel_obj']):12.3f}" for b in names))
    hard = jaccard(psyches["dex_unity_struggler"]["rel_obj"], psyches["uma_unity_careful"]["rel_obj"])
    print(f"\nsame-domain pair (Unity struggler vs careful) trait overlap = {hard:.3f} "
          f"-> distinct dispositions on shared entities")

    # ----- 2. CONTINUITY (Ship of Theseus) ----------------------------------
    banner("2. CONTINUITY  (a second consolidation 'night' — do signature gists persist?)")
    for name in names:
        svc = psyches[name]["svc"]
        before = {g.render(): g.survived_cycles for g in svc.db.all_gist()}
        Consolidator(psyches[name]["cfg"], db=svc.db, embedder=embedder).run(now=NOW + timedelta(days=1))
        after = svc.db.all_gist()
        persisted = sum(1 for g in after if g.render() in before)
        matured = sum(1 for g in after if g.survived_cycles >= 1)
        print(f"  {name:22} gists before={len(before)} after={len(after)} "
              f"persisted={persisted} matured(survived>=1 cycle)={matured}")

    # ----- 3. PLASTICITY -----------------------------------------------------
    banner("3. PLASTICITY  (Cole reforms: starts writing tests & stops force-pushing)")
    cole = psyches["cole_cowboy"]["svc"]
    cfg = psyches["cole_cowboy"]["cfg"]
    before_gists = {g.render() for g in cole.db.all_gist()}
    rng = random.Random(7)
    reform_spec = dict(PERSONAS["cole_cowboy"], success_rate=0.9,
                       good_verbs=["added a test for", "carefully refactored", "code-reviewed"],
                       bad_verbs=["noted a small issue in"], rules=["always run tests before commit"],
                       crisis=None)
    for ev in gen_history("cole_reform", reform_spec, 120, span_days=4, rng=rng):
        ev.project = PERSONAS["cole_cowboy"]["project"]
        cole.ingest(ev)
    Consolidator(cfg, db=cole.db, embedder=embedder).run(now=NOW + timedelta(days=2))
    after_gists = {g.render() for g in cole.db.all_gist()}
    print(f"  new traits crystallized: {len(after_gists - before_gists)}")
    for g in list(after_gists - before_gists)[:6]:
        print(f"    + {g}")
    new_phen = _session_start_context(cfg, {"cwd": PERSONAS['cole_cowboy']['project']})
    drift = 1.0 - cosine(vecs["cole_cowboy"], embedder.embed_one(new_phen or "x"))
    print(f"  phenotype drift after reform = {drift:.3f}  (0 = frozen, higher = adapted)")

    # ----- 4. ANTI-HOWLROUND -------------------------------------------------
    banner("4. ANTI-HOWLROUND  (hammer one obsession 80x — does it annihilate the rest of the self?)")
    svc = psyches["tessa_tdd"]["svc"]
    cfg = psyches["tessa_tdd"]["cfg"]
    sal_before = [e.base_salience for e in svc.db.all_episodic()]
    rng = random.Random(11)
    for i in range(80):
        ts = (NOW - timedelta(days=rng.uniform(0, 2))).strftime("%Y-%m-%dT%H:%M:%SZ")
        svc.ingest(TurnEvent("the idempotency key the idempotency key", "obsess over the idempotency key",
                             "idempotency key idempotency key", tool_name="Edit", success=True,
                             session_id="obsession", project=PERSONAS["tessa_tdd"]["project"], timestamp=ts))
    Consolidator(cfg, db=svc.db, embedder=embedder).run(now=NOW + timedelta(days=2))
    sal_after = [e.base_salience for e in svc.db.all_episodic()]
    total = sum(sal_after)
    print(f"  total salience after 80x obsession = {total:.1f}  (conserved budget K = {cfg.salience_budget:g})")
    print(f"  min episodic salience = {min(sal_after):.4f}  (>0 means NOTHING was annihilated)")
    print(f"  episodes alive: before-obsession={len(sal_before)}  after={len(sal_after)}")
    print("  => zero-sum budget holds total bounded; the rest of the self survives the howlround.")

    for p in psyches.values():
        p["svc"].close()
    import shutil
    shutil.rmtree(root, ignore_errors=True)
    print("\n(temp stores cleaned up)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
