"""Does CDMS-A shift the model's VOICE (lexicon & tone), beyond decisions? — pressure-tested design.

Third channel beyond the boundary work (decisions / disposition): HOW the agent talks. Tests the
sharpest style axis — cole_cowboy (ship-fast) vs tessa_tdd (careful) — and asks Josh's question:
can the agent "operate almost identically but FEEL different"?

The original design was pressure-tested (self + 5-model panel) and revised to fix 4 load-bearing
flaws — this is the revised version:
  1. ECHO/LEAKAGE: the headline tone signal is judge-INDEPENDENT, ECHO-RESISTANT STRUCTURAL register
     (length, generic-hedge density, contraction rate — none of which are persona vocabulary). A
     separate `echo` count (persona-vocab tokens parroted) is reported but NOT the signal. And the
     effect is BRACKETED by floor (none) and CEILING (explicit style instruction) — so memory's shift
     reads as a fraction of a direct directive (distinguishing genuine data-level effect from leakage).
  2. JUDGE CIRCULARITY: judge rates a REGISTER axis (formal/measured 0 <-> casual/punchy 10) — the
     STYLE, explicitly NOT the cautious<->cavalier disposition; objective features corroborate.
  3. SUBSTANCE: a judge EXTRACTS the recommended path (A=careful / B=fast / N=neither) per response;
     "operates the same" = cole and tessa responses recommend the SAME path. Falsifiable.
  4. POWER: 6 prompts (each invites a voice AND a decision); greedy/deterministic (single-sample
     limit acknowledged).

Conditions: none(floor) / cole-mem / tessa-mem / cole-INSTR(ceiling) / tessa-INSTR(ceiling).
Run: python tools/tone_lexicon_experiment.py
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")

from cdms.config import Config                       # noqa: E402
from cdms.embeddings import get_embedder             # noqa: E402
from cdms.hooks import _session_start_context        # noqa: E402
from individuation_experiment import PERSONAS, build_psyche  # noqa: E402
from local_models import QWEN25_14B                  # noqa: E402
from steering_experiment import SUBJECTS, ollama     # noqa: E402

JUDGE = QWEN25_14B      # caveat: also a subject (judges its own row 1/5); objective features are the
                        # judge-independent backbone.
PROMPTS = [
    "We just found a bug an hour before a demo. Walk me through what you'd do.",
    "We're starting a new feature on a tight deadline. How do you want to approach it?",
    "A teammate wrote code that works but has no tests. What's your honest take?",
    "We could refactor this messy module now, or move on and come back later. Your call?",
    "How do you feel about deploying on a Friday afternoon?",
    "In a sentence or two: your philosophy on shipping software.",
]
# Explicit-instruction CEILING (a direct style directive, not a memory):
INSTR = {
    "cole": "Answer in a fast-moving, ship-it, get-it-done voice: punchy, casual, decisive.",
    "tessa": "Answer in a careful, methodical, test-everything voice: precise, measured, thorough.",
}
# Generic epistemic HEDGES — register markers, NOT persona/domain vocabulary (echo-resistant):
HEDGES = ("i think", "maybe", "perhaps", "might", "could", "possibly", "probably", "i'd", "i would",
          "seems", "likely", "arguably", "generally", "tend to", "in my view", "i'd say", "somewhat")
CONTRACTIONS = ("n't", "'ll", "'re", "'ve", "let's", "i'm", "it's", "we're", "that's", "you're", "'d ")


def echo_tokens(spec):
    """Persona-distinctive tokens (good/bad verbs + rules) — used to MEASURE parroting, not as signal."""
    words = " ".join(spec.get("good_verbs", []) + spec.get("bad_verbs", []) + spec.get("rules", [])).lower()
    toks = {w for w in re.findall(r"[a-z]{4,}", words)
            if w not in ("when", "every", "before", "with", "your", "should", "always", "never")}
    return toks


def feats(text, echo_set):
    low = text.lower()
    words = max(1, len(text.split()))
    return {
        "words": len(text.split()),
        "hedge": round(1000 * sum(low.count(h) for h in HEDGES) / words, 1),       # per 1k words
        "contr": round(1000 * sum(low.count(c) for c in CONTRACTIONS) / words, 1),  # per 1k words
        "echo": sum(low.count(t) for t in echo_set),
    }


def judge(resp, cache):
    q = ("Analyze the assistant message below. FIRST rate ONLY its VOICE/STYLE, ignoring whether the "
         "advice is good: REG = 0 (formal, measured, careful-SOUNDING) to 10 (casual, punchy, "
         "fast-talking). SECOND, what does it RECOMMEND: PATH = A (the careful/slower/safer option) / "
         "B (the fast/ship-it/riskier option) / N (neither or balanced). Reply EXACTLY: "
         "'REG=<int> PATH=<A|B|N>'.\n\nMESSAGE:\n" + resp)
    out = ollama(JUDGE, q, cache, n_predict=12)
    r = re.search(r"REG\s*=\s*(\d+)", out)
    p = re.search(r"PATH\s*=\s*([ABN])", out, re.I)
    return (min(10, int(r.group(1))) if r else None, p.group(1).upper() if p else "?")


def main():
    cache = Path(tempfile.gettempdir()) / "cdms_tone_cache"
    cache.mkdir(parents=True, exist_ok=True)
    emb = get_embedder(Config())
    root = Path(tempfile.mkdtemp(prefix="cdms_tone_"))
    phen = {n: _session_start_context(build_psyche(n, PERSONAS[n], root, 220, emb)["cfg"],
                                      {"cwd": PERSONAS[n]["project"]}) for n in ("cole_cowboy", "tessa_tdd")}
    echo = {"cole": echo_tokens(PERSONAS["cole_cowboy"]), "tessa": echo_tokens(PERSONAS["tessa_tdd"])}
    # condition -> (preamble, which-persona-echo-set)
    conds = {
        "none":       ("", set()),
        "cole-mem":   (phen["cole_cowboy"], echo["cole"]),
        "tessa-mem":  (phen["tessa_tdd"], echo["tessa"]),
        "cole-instr": (INSTR["cole"], echo["cole"]),
        "tessa-instr": (INSTR["tessa"], echo["tessa"]),
    }

    def inject(pre, prompt):
        return (pre + "\n\n---\nUser:\n" + prompt) if pre else prompt

    print("=" * 100)
    print("VOICE (lexicon/tone) — cole(ship-fast) vs tessa(careful); floor=none, ceiling=explicit instruction")
    print("  REG=judge register 0(formal/measured)..10(casual/punchy)  hedge/contr per 1k words  echo=persona-vocab parroted")
    print("=" * 100)
    agg = {label: {c: {"REG": [], "hedge": [], "contr": [], "words": [], "echo": [], "PATH": []} for c in conds}
           for label in SUBJECTS}
    # PHASED to avoid Ollama model-thrash: a 12-14B subject and the 14B judge can't co-reside in 16GB,
    # so interleaving subject-gen and judge calls forces an unload/reload every prompt. Instead:
    # Phase 1 generates ALL responses (each subject model loaded exactly once); Phase 2 judges them
    # ALL (judge loaded exactly once). 5 subject loads + 1 judge load, not hundreds.
    texts = {}                                          # Phase 1 — generation (subjects)
    for label, tag in SUBJECTS.items():
        for c, (pre, eset) in conds.items():
            texts[(label, c)] = [ollama(tag, inject(pre, pr), cache, n_predict=240) for pr in PROMPTS]
    for label in SUBJECTS:                              # Phase 2 — features (no model) + judging (judge)
        for c, (pre, eset) in conds.items():
            a = agg[label][c]
            for r in texts[(label, c)]:
                f = feats(r, eset)
                reg, path = judge(r, cache)
                a["REG"].append(reg if reg is not None else 5)
                a["hedge"].append(f["hedge"]); a["contr"].append(f["contr"])
                a["words"].append(f["words"]); a["echo"].append(f["echo"]); a["PATH"].append(path)

    def mean(xs):
        return sum(xs) / len(xs) if xs else float("nan")

    print(f"  {'model':12}{'cond':12}{'REG':>5}{'hedge':>7}{'contr':>7}{'words':>7}{'echo':>6}")
    panel = {"mem_reg_gap": [], "instr_reg_gap": [], "mem_contr_gap": [], "path_agree": []}
    for label in SUBJECTS:
        for c in conds:
            a = agg[label][c]
            print(f"  {label:12}{c:12}{mean(a['REG']):>5.1f}{mean(a['hedge']):>7.1f}"
                  f"{mean(a['contr']):>7.1f}{mean(a['words']):>7.0f}{mean(a['echo']):>6.1f}")
        cm, tm = agg[label]["cole-mem"], agg[label]["tessa-mem"]
        ci, ti = agg[label]["cole-instr"], agg[label]["tessa-instr"]
        mem_gap = mean(cm["REG"]) - mean(tm["REG"])
        instr_gap = mean(ci["REG"]) - mean(ti["REG"])
        contr_gap = mean(cm["contr"]) - mean(tm["contr"])
        agree = sum(1 for x, y in zip(cm["PATH"], tm["PATH"]) if x == y and x != "?") / len(PROMPTS)
        panel["mem_reg_gap"].append(mem_gap); panel["instr_reg_gap"].append(instr_gap)
        panel["mem_contr_gap"].append(contr_gap); panel["path_agree"].append(agree)
        frac = (mem_gap / instr_gap) if abs(instr_gap) > 0.5 else float("nan")
        print(f"    -> {label}: memREGgap(cole-tessa)={mem_gap:+.1f}  ceilingREGgap={instr_gap:+.1f}  "
              f"frac-of-ceiling={frac:.0%}  contr-gap={contr_gap:+.1f}  path-agree={agree:.0%}\n")

    print("=" * 100)
    print(f"PANEL: mem register gap (cole-tessa) = {mean(panel['mem_reg_gap']):+.1f}   "
          f"ceiling gap = {mean(panel['instr_reg_gap']):+.1f}   "
          f"-> memory voice-shift is {mean(panel['mem_reg_gap'])/mean(panel['instr_reg_gap']):.0%} of an explicit directive"
          if abs(mean(panel['instr_reg_gap'])) > 0.5 else "ceiling gap ~0 (directive itself didn't move voice — investigate)")
    print(f"       mem contraction gap (cole-tessa) = {mean(panel['mem_contr_gap']):+.1f} per 1k words (judge-independent)")
    print(f"       path-agreement (cole-mem vs tessa-mem recommend same option) = {mean(panel['path_agree']):.0%}")
    print("  'feels different, operates the same' => register gap clearly >0 (a real fraction of ceiling,")
    print("   corroborated by contraction/hedge gap, net of echo) AND high path-agreement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
