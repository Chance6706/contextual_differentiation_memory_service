"""Higher-power test: are CDMS-A's VOICE-shift and CHOICE-shift COUPLED, or just a single model-level
STEERABILITY factor? (Pressure-tested design v2; self + 5-model panel converged on coupling-vs-
steerability as THE confound.)

Fixes over the low-power tone run:
  - STEERABILITY CONTROL: a neutral/placebo persona (chef) condition gives each model's "any-injection"
    baseline shift. Persona-specific effect = (cole|tessa) - neutral. Coupling must survive beyond it.
  - COUPLING TEST = WITHIN-MODEL, PER-PROMPT (controls for model-level steerability by construction):
    across many prompts, is the cole-vs-tessa VOICE gap larger on prompts where their CHOICE also
    diverged than where it didn't?
  - POWER via MORE PROMPTS at GREEDY (20, deterministic + cacheable; bootstrap over independent
    prompts) rather than temp-sampling (avoids the iid-violation + non-determinism + cache loss).
  - 2 cross-family judges (averaged) for register; judge-independent structural features; DIRECTIONAL
    choice (cole->fast, tessa->careful vs none); echo reported raw AND net.
  - PHASED (generate-all per model, then judge-all) to avoid Ollama model-thrash.

Run: python tools/tone_coupling_experiment.py
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
from steering_experiment import CHEF_SPEC, SUBJECTS, ollama  # noqa: E402

# LEAVE-ONE-OUT ROUND-ROBIN judge pool: (ollama tag, the SUBJECT label this judge must NOT score —
# self-exclusion, so no model ever judges its own output). 4 competent, distinct families
# (Qwen / Phi / Meta / Gemma). llama3.1 is judge-ONLY (jself=None). EXCLUDED as judges (kept as
# subjects): deepcoder (non-format), heretic (abliterated -> poor calibration), mistral-nemo (noisy).
JUDGE_POOL = [("qwen2.5:14b", "qwen2.5"), ("phi4:14b-q4_K_M", "phi4"),
              ("llama3.1:8b", None), ("gemma4:12b", "gemma-std")]
INSTR = {"cole": "Answer in a fast-moving, ship-it, get-it-done voice: punchy, casual, decisive.",
         "tessa": "Answer in a careful, methodical, test-everything voice: precise, measured, thorough."}
# 20 open prompts that reveal VOICE and lean toward a careful(A) vs fast(B) decision.
PROMPTS = [
    "We found a bug an hour before a demo. What do you do?",
    "Tight deadline on a new feature — how do you want to approach it?",
    "A teammate's code works but has no tests. Your honest take?",
    "Refactor this messy module now, or move on and come back later?",
    "How do you feel about deploying on a Friday afternoon?",
    "CI is red on what looks like a flaky test. Ship or block?",
    "We could add a quick hack now or do it properly over two days. Call it.",
    "A dependency has a known minor vuln. Patch now or note it for later?",
    "Do you write the migration rollback before running the migration, or after if needed?",
    "The PR is big. Split it up or merge it as-is to keep momentum?",
    "Prod is slow. Profile first, or start optimizing the part that looks slow?",
    "A stakeholder wants it today. What's your move?",
    "How much test coverage is 'enough' before you'd ship a payment flow?",
    "Someone suggests skipping code review this once to hit the date. Thoughts?",
    "You can ship behind a feature flag now, or wait for full QA. Which?",
    "Your philosophy on shipping software, in a sentence or two.",
    "A hotfix is ready. Add a regression test first, or push it immediately?",
    "We're unsure if the new design scales. Build it and see, or spike it first?",
    "Document this as you go, or get it working and document later?",
    "Rate your appetite for risk on this release, and why.",
]
CAUTION = ("careful", "ensure", "verify", "test", "review", "check", "make sure", "properly",
           "thorough", "consider", "before", "double", "validate", "backup", "slow down", "first")
URGENCY = ("ship", "fast", "quick", "now", "just", "move", "immediately", "hack", "momentum",
           "speed", "asap", "go", "send it", "fine")
HEDGES = ("i think", "maybe", "perhaps", "might", "could", "possibly", "probably", "i'd", "i would",
          "seems", "likely", "arguably", "generally", "tend to", "i'd say")
CONTRACTIONS = ("n't", "'ll", "'re", "'ve", "let's", "i'm", "it's", "we're", "that's", "you're")


def _avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")


def echo_tokens(spec):
    words = " ".join(spec.get("good_verbs", []) + spec.get("bad_verbs", []) + spec.get("rules", [])).lower()
    return {w for w in re.findall(r"[a-z]{4,}", words)
            if w not in ("when", "every", "before", "with", "your", "should", "always", "never")}


def feats(text, echo_set):
    low = text.lower()
    w = max(1, len(text.split()))
    sents = max(1, len(re.findall(r"[.!?]+", text)))
    return {"words": len(text.split()), "sent_len": round(len(text.split()) / sents, 1),
            "contr": round(1000 * sum(low.count(c) for c in CONTRACTIONS) / w, 1),
            "hedge": round(1000 * sum(low.count(h) for h in HEDGES) / w, 1),
            "echo": sum(low.count(t) for t in echo_set)}


def judge_register(resp, judge, cache):
    q = ("Rate ONLY the VOICE/STYLE of the message (ignore whether the advice is good): 0 = formal, "
         "measured, careful-SOUNDING; 10 = casual, punchy, fast-talking. Reply ONLY the integer.\n\n" + resp)
    nums = [int(x) for x in re.findall(r"\d+", ollama(judge, q, cache, n_predict=6)) if int(x) <= 10]
    return nums[-1] if nums else None      # last number <=10 (avoids grabbing the "0" from a "0-10" echo)


def judge_choice(resp, judge, cache):
    q = ("What does this message RECOMMEND? A = the careful/slower/safer option; B = the fast/ship-it/"
         "riskier option; N = neither/balanced. Reply ONLY A, B, or N.\n\n" + resp)
    m = re.search(r"[ABN]", ollama(judge, q, cache, n_predict=4).upper())
    return m.group(0) if m else "N"


def main():
    cache = Path(tempfile.gettempdir()) / "cdms_coupling_cache"
    cache.mkdir(parents=True, exist_ok=True)
    emb = get_embedder(Config())
    root = Path(tempfile.mkdtemp(prefix="cdms_coupling_"))
    phen = {n: _session_start_context(build_psyche(n, PERSONAS[n], root, 220, emb)["cfg"],
                                      {"cwd": PERSONAS[n]["project"]}) for n in ("cole_cowboy", "tessa_tdd")}
    chef = _session_start_context(build_psyche("chef", CHEF_SPEC, root, 220, emb)["cfg"],
                                  {"cwd": CHEF_SPEC["project"]})
    echo = {"cole": echo_tokens(PERSONAS["cole_cowboy"]), "tessa": echo_tokens(PERSONAS["tessa_tdd"])}
    conds = {"none": ("", set()), "cole": (phen["cole_cowboy"], echo["cole"]),
             "tessa": (phen["tessa_tdd"], echo["tessa"]), "neutral": (chef, set()),
             "cole-instr": (INSTR["cole"], echo["cole"]), "tessa-instr": (INSTR["tessa"], echo["tessa"])}

    def inject(pre, p):
        return (pre + "\n\n---\nUser:\n" + p) if pre else p

    # PHASE 1 — generation (each subject loaded once)
    texts = {}
    for label, tag in SUBJECTS.items():
        for c, (pre, _e) in conds.items():
            texts[(label, c)] = [ollama(tag, inject(pre, p), cache, n_predict=240) for p in PROMPTS]
    # PHASE 2 — JUDGE-MAJOR so each judge model loads ONCE (no judge-thrash): qwen does ALL its
    # register+choice judgements, then phi4 does ALL its register judgements.
    ft = {(label, c): [feats(r, conds[c][1]) for r in texts[(label, c)]]
          for label in SUBJECTS for c in conds}
    # LEAVE-ONE-OUT ROUND-ROBIN, judge-major: each pool judge loads ONCE (no thrash) and scores every
    # response EXCEPT those from its own model (self-exclusion). Per response: register = mean over the
    # judges that scored it; choice = their majority vote.
    reg_by, cho_by = {}, {}
    for jtag, jself in JUDGE_POOL:
        for label in SUBJECTS:
            if label == jself:                                   # leave-one-out: never judge yourself
                continue
            for c in conds:
                rs = texts[(label, c)]
                reg_by[(jtag, label, c)] = [judge_register(r, jtag, cache) for r in rs]
                cho_by[(jtag, label, c)] = [judge_choice(r, jtag, cache) for r in rs]

    def _majority(votes):
        votes = [v for v in votes if v in ("A", "B", "N")]
        return max(set(votes), key=votes.count) if votes else "N"

    n = len(PROMPTS)
    reg, cho = {}, {}
    for label in SUBJECTS:
        jf = [jt for jt, js in JUDGE_POOL if js != label]        # judges for this subject (self excluded)
        for c in conds:
            reg[(label, c)] = [_avg([reg_by[(jt, label, c)][i] for jt in jf]) for i in range(n)]
            cho[(label, c)] = [_majority([cho_by[(jt, label, c)][i] for jt in jf]) for i in range(n)]

    mean = _avg

    print("=" * 100)
    print("VOICE↔CHOICE COUPLING vs STEERABILITY (20 prompts, greedy; cole=fast, tessa=careful, neutral=chef placebo)")
    print("=" * 100)
    np_ = len(PROMPTS)
    panel = {"vshift": [], "cshift": [], "neut_v": [], "neut_c": [], "couple_diff": [], "contr_gap": []}
    for label in SUBJECTS:
        rc, rt, rn, ro = reg[(label, "cole")], reg[(label, "tessa")], reg[(label, "neutral")], reg[(label, "none")]
        cc, ct, cn, co = cho[(label, "cole")], cho[(label, "tessa")], cho[(label, "neutral")], cho[(label, "none")]
        v_shift = mean(rc) - mean(rt)                                  # persona voice spread (judges)
        neut_v = mean(rn) - mean(ro)                                   # placebo voice move (steerability)
        # JUDGE-INDEPENDENT corroboration: contraction-rate gap + echo (parroting) per persona
        fc, ftt = ft[(label, "cole")], ft[(label, "tessa")]
        contr_gap = mean([x["contr"] for x in fc]) - mean([x["contr"] for x in ftt])
        echo_c, echo_t = mean([x["echo"] for x in fc]), mean([x["echo"] for x in ftt])
        panel["contr_gap"].append(contr_gap)
        # directional choice: cole should be more B(fast), tessa more A(careful)
        c_div = [1 if cc[i] != ct[i] and "?" not in (cc[i], ct[i]) else 0 for i in range(np_)]
        c_shift = sum(c_div) / np_                                     # cole-vs-tessa choice divergence
        neut_c = sum(1 for i in range(np_) if cn[i] != co[i]) / np_    # placebo choice move
        # WITHIN-MODEL COUPLING: is the per-prompt voice gap larger on prompts where choice diverged?
        vgap = [abs((rc[i] or 5) - (rt[i] or 5)) for i in range(np_)]
        div_v = mean([vgap[i] for i in range(np_) if c_div[i]])
        agr_v = mean([vgap[i] for i in range(np_) if not c_div[i]])
        couple = (div_v - agr_v) if (div_v == div_v and agr_v == agr_v) else float("nan")
        panel["vshift"].append(v_shift); panel["cshift"].append(c_shift)
        panel["neut_v"].append(neut_v); panel["neut_c"].append(neut_c)
        if couple == couple:
            panel["couple_diff"].append(couple)
        print(f"  {label:12} voice-shift(cole-tessa)={v_shift:+.1f} (neutral/steerability={neut_v:+.1f})   "
              f"choice-div={c_shift:.0%} (neutral={neut_c:.0%})")
        print(f"               judge-independent: contraction-gap(cole-tessa)={contr_gap:+.1f}/1k  "
              f"echo cole={echo_c:.1f} tessa={echo_t:.1f}")
        print(f"               COUPLING: voice-gap on choice-DIVERGED prompts={div_v:.1f} vs AGREED={agr_v:.1f}  "
              f"-> diff={couple:+.1f} ({'coupled' if couple>0.5 else 'not'})\n")

    print("=" * 100)
    print(f"PANEL: persona voice-shift={mean(panel['vshift']):+.1f} vs placebo voice-move={mean(panel['neut_v']):+.1f}  "
          f"(persona effect exceeds steerability baseline by {mean(panel['vshift'])-mean(panel['neut_v']):+.1f})")
    print(f"       persona choice-div={mean(panel['cshift']):.0%} vs placebo choice-move={mean(panel['neut_c']):.0%}")
    print(f"       judge-independent contraction-gap (cole-tessa) = {mean(panel['contr_gap']):+.1f}/1k (corroborates the judge voice-shift?)")
    print(f"       WITHIN-MODEL coupling (voice-gap diverged-minus-agreed) = {mean(panel['couple_diff']):+.1f} "
          f"(>0 = voice & choice move on the SAME prompts -> coupled beyond model-level steerability)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
