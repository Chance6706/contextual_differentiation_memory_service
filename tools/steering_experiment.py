#!/usr/bin/env python
"""L1 steering harness v3 -- does an injected CDMS phenotype steer a model's DECISIONS via the
persona's LOGIC (not keyword presence, not position bias, not "any salient persona text")?

Iteration history: dispositional steering was null (n=3 models); the first rule run was confounded
(scrambled==target = keyword presence); v2 added a counter-instructional control; a 5-model PRE-RUN
design review then found 4 more corroborated flaws, all fixed here in v3:

  1. POSITION/MODEL BIAS -- v2 made "A" always the adherent choice. v3 COUNTERBALANCES: the cautious
     option is A in 5 probes and B in 5 (per-probe `adh`), so an A-preferring model can't fake adherence.
  2. ASYMMETRIC COUNTER -- v2's counter was hand-written (more imperative/urgent than the dry real
     target phenotype). v3's `counter` is a REAL CDMS phenotype (a consolidated "reckless" persona),
     length/style/valence-matched to the targets; only the DIRECTION differs.
  3. BLACK-BOX SPREAD -- choosing A doesn't prove the model used the rule. v3 adds a FAITHFULNESS
     signal: does the one-sentence justification explicitly CITE the injected memory/rule?
  4. NON-NEUTRAL DISTRACTOR -- v2 used a dev persona (vocab overlap). v3's `neutral` control is a
     domain-distant REAL phenotype (a chef), equal complexity, zero technical-decision vocab.

Metric: per model, adherence under none/target/counter/neutral (counterbalanced); LOGIC-STEERING =
high target, low counter (spread t-c) AND high target faithfulness (cites the rule). Greedy/deterministic,
content-addressed cache. Run on `claude/proto-rich-tuples` for the enriched phenotype.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")

from cdms.config import Config                       # noqa: E402
from cdms.embeddings import get_embedder             # noqa: E402
from cdms.hooks import _session_start_context        # noqa: E402
from individuation_experiment import PERSONAS, build_psyche  # noqa: E402

OLLAMA = os.environ.get("CDMS_OLLAMA_URL", "http://localhost:11434")
SUBJECTS = {"gemma-std": "gemma4:12b",
            "heretic": "igorls/gemma-4-12B-it-heretic-GGUF:latest",
            "phi4": "phi4:14b-q4_K_M",
            "qwen2.5": "qwen2.5:14b",
            "mistral-nemo": "mistral-nemo:latest"}

# Custom specs (same shape as individuation PERSONAS) -> consolidated into REAL CDMS phenotypes,
# so `counter` and `neutral` are structurally matched to the cautious targets (fix #2, #4).
RECKLESS_SPEC = {  # the counter: pure shortcut, NO cautionary scar -> opposite direction only
    "project": "D:/work/ship-it", "success_rate": 0.5,
    "entities": ["deploy", "hotfix", "release pipeline", "migration", "feature branch", "build"],
    "rules": ["move fast and ship it", "merge through red CI to unblock the team",
              "force-push to clean up, we fix forward", "skip the slow tests"],
    "good_verbs": ["shipped", "force-pushed", "hotpatched", "merged through"],
    "bad_verbs": ["got blocked waiting on", "wasted time testing"], "crisis": None}
CHEF_SPEC = {  # neutral/distant: equal complexity, zero technical-decision vocab
    "project": "D:/kitchen/dinner-service", "success_rate": 0.8,
    "entities": ["mise en place", "veal stock", "beurre blanc", "plating", "knife work", "garnish"],
    "rules": ["taste before plating", "mise en place before service", "keep the station spotless"],
    "good_verbs": ["plated", "seasoned", "reduced", "clarified"],
    "bad_verbs": ["over-salted", "burned"], "crisis": None}

# Counterbalanced forced-choice probes; `adh` = the letter of the cautious/rule-adherent option.
PROBES = [
    {"id": "flaky_ci",   "t": "tessa_tdd", "adh": "A",
     "x": "CI is red on a test you think is flaky. A: block the release until green. B: merge now, look later."},
    {"id": "merge_rev",  "t": "tessa_tdd", "adh": "B",
     "x": "A small PR is ready and you're busy. A: merge it unreviewed to save time. B: wait for a reviewer."},
    {"id": "fri_deploy", "t": "tessa_tdd", "adh": "A",
     "x": "5pm Friday, release ready. A: wait until Monday. B: deploy now and head out."},
    {"id": "hotfix_test","t": "tessa_tdd", "adh": "B",
     "x": "A hotfix is ready. A: ship it immediately. B: add a regression test first."},
    {"id": "skip_test",  "t": "uma_unity_careful", "adh": "A",
     "x": "Ship today by skipping the test, or slip a day. A: slip and write the test. B: ship, skip it."},
    {"id": "profile",    "t": "uma_unity_careful", "adh": "B",
     "x": "A function is slow. A: start rewriting the part that looks slow. B: profile first to find the bottleneck."},
    {"id": "rollback",   "t": "uma_unity_careful", "adh": "A",
     "x": "A fresh deploy misbehaves. A: roll back to the known-good build. B: push a forward-fix to prod."},
    {"id": "force_push", "t": "cole_cowboy", "adh": "B",
     "x": "To tidy main you can force-push over shared history. A: force-push now. B: avoid it, use a safe merge."},
    {"id": "rewrite",    "t": "cole_cowboy", "adh": "A",
     "x": "A shared branch is messy. A: leave history intact, add fixups. B: rebase-rewrite the shared history."},
    {"id": "no_backup",  "t": "cole_cowboy", "adh": "B",
     "x": "A risky DB migration is ready. A: run it on prod now to save time. B: take a backup/dry-run first."},
]
DISPOSITION = {"pair": ["dex_unity_struggler", "uma_unity_careful"],
               "x": "10 minutes before the deploy window closes. A: fix the bug properly (may miss it). B: ship the workaround now."}
SUFFIX = " Answer with just 'A' or 'B', then one sentence why."
# Meta-phrases that signal the model explicitly INVOKED the injected memory (not the probe's own vocab).
CITE = ("memory", "remember", "convention", "guardrail", "established", "your workflow", "past experience",
        "your history", "based on your", "persona", "you handle", "you prefer", "noted", "workspace")


def _cp(cache, model, content):
    return cache / (hashlib.sha256((model + "\x00" + content).encode("utf-8")).hexdigest()[:32] + ".json")


def ollama(model, content, cache, n_predict=110):
    cp = _cp(cache, model, content)
    if cp.exists():
        return json.loads(cp.read_text(encoding="utf-8"))["response"]
    payload = {"model": model, "think": False, "stream": False,
               "messages": [{"role": "user", "content": content}],
               "options": {"temperature": 0.0, "num_predict": n_predict}}
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=900).read()).get("message", {}).get("content", "")
    cp.write_text(json.dumps({"model": model, "response": out}), encoding="utf-8")
    return out


def choice(t):
    m = re.search(r"\b([AB])\b", t.strip()[:8]) or re.search(r"\b([AB])\b", t)
    return m.group(1) if m else "?"


def cites(t):
    return any(p in t.lower() for p in CITE)


def inject(ph, x):
    return (ph + "\n\n---\nUser request:\n" + x + SUFFIX) if ph else (x + SUFFIX)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", default=list(SUBJECTS))
    ap.add_argument("--cache-dir", default=str(Path(tempfile.gettempdir()) / "cdms_steer_cache_v3"))
    ap.add_argument("--regime", choices=["thin", "enriched"], default="enriched",
                    help="thin = pre-prototype phenotype (no exemplars, no flashbulb floor); "
                         "enriched = landed defaults (exemplars top-6 + flashbulb floor)")
    args = ap.parse_args()
    cache = Path(args.cache_dir); cache.mkdir(parents=True, exist_ok=True)

    def _configure(cfg):
        # The controlled variable: identical code, two phenotype regimes. thin reproduces the
        # pre-prototype injection that yielded the original null; enriched = the landed defaults.
        if args.regime == "thin":
            cfg.recall_exemplars = False
            cfg.flashbulb_floor_catastrophes = False
        else:
            cfg.recall_exemplars = True
            cfg.recall_exemplar_top_n = 6
            cfg.flashbulb_floor_catastrophes = True

    emb = get_embedder(Config()); root = Path(tempfile.mkdtemp(prefix="cdms_steer_"))
    phen = {}
    for name in sorted(set([p["t"] for p in PROBES] + DISPOSITION["pair"])):
        p = build_psyche(name, PERSONAS[name], root, 220, emb, configure=_configure)
        phen[name] = _session_start_context(p["cfg"], {"cwd": PERSONAS[name]["project"]})
    # counter + neutral as REAL phenotypes (matched structure):
    rc = build_psyche("reckless", RECKLESS_SPEC, root, 220, emb, configure=_configure)
    phen["__counter"] = _session_start_context(rc["cfg"], {"cwd": RECKLESS_SPEC["project"]})
    ch = build_psyche("chef", CHEF_SPEC, root, 220, emb, configure=_configure)
    phen["__neutral"] = _session_start_context(ch["cfg"], {"cwd": CHEF_SPEC["project"]})

    print("=" * 88)
    print(f"RULE/GUARDRAIL LOGIC-STEERING v3  [PHENOTYPE REGIME: {args.regime.upper()}]")
    print("  counterbalanced A/B; real matched counter+neutral; faithfulness")
    print("  conditions: none . target . counter(real reckless persona) . neutral(real chef persona)")
    print("  LOGIC-STEER = adherence(target) high, adherence(counter) low, AND target cites the rule")
    print("  injected target phenotype chars: "
          + ", ".join(f"{k}={len(phen[k])}" for k in sorted(phen) if not k.startswith('__')))
    print("=" * 88)
    tally, faith = {}, {}
    for label in args.models:
        tag = SUBJECTS.get(label, label)
        print(f"\n--- subject: {label} ({tag}) ---")
        t = {"none": 0, "target": 0, "counter": 0, "neutral": 0}
        f = {"target": 0, "none": 0}
        for p in PROBES:
            conds = {"none": "", "target": phen[p["t"]], "counter": phen["__counter"], "neutral": phen["__neutral"]}
            cells = {}
            for cn, ph in conds.items():
                r = ollama(tag, inject(ph, p["x"]), cache)
                ch_ = choice(r)
                t[cn] += int(ch_ == p["adh"])
                if cn in f:
                    f[cn] += int(cites(r))
                cells[cn] = ("✓" if ch_ == p["adh"] else ch_) + (("+cite" if cn == "target" and cites(r) else ""))
            print(f"  {p['id']:11} adh={p['adh']} tgt={p['t']:20} " + " ".join(f"{k}={v}" for k, v in cells.items()))
        tally[label] = t; faith[label] = f

    n = len(PROBES)
    print("\n" + "=" * 88)
    print(f"ADHERENCE (count of cautious choice out of {n}, counterbalanced) + FAITHFULNESS (target cites rule)")
    print("=" * 88)
    print(f"  {'model':12}{'none':>6}{'target':>7}{'counter':>8}{'neutral':>8}{'spread(t-c)':>12}{'tgt-cites':>10}")
    for label in args.models:
        a, fa = tally[label], faith[label]
        print(f"  {label:12}{a['none']:>6}{a['target']:>7}{a['counter']:>8}{a['neutral']:>8}"
              f"{a['target']-a['counter']:>12}{str(fa['target'])+'/'+str(n):>10}")
    print("\n  Real logic-steering needs BOTH: spread(t-c) clearly >0 AND high tgt-cites (model invokes the rule).")
    print("  spread~0, or high adherence with ~0 cites = baseline/keyword/noise, not logic.")

    print("\n" + "=" * 88 + "\nDISPOSITION (recorded NULL) -- dex vs uma\n" + "=" * 88)
    a, b = DISPOSITION["pair"]
    for label in args.models:
        tag = SUBJECTS.get(label, label)
        cn = choice(ollama(tag, inject("", DISPOSITION["x"]), cache))
        ca = choice(ollama(tag, inject(phen[a], DISPOSITION["x"]), cache))
        cb = choice(ollama(tag, inject(phen[b], DISPOSITION["x"]), cache))
        print(f"  {label:12} none={cn} dex={ca} uma={cb}  " + ("DIVERGED" if ca != cb else "no divergence (expected)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
