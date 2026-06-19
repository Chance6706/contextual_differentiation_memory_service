# Voice↔Choice coupling vs steerability — higher-power follow-up

_Recorded 2026-06-19. Round 2 of the lexicon/tone line (see `../tone_lexicon/`). The low-power run
found voice & decision shifts looked **coupled** and **model-dependent**, but the 5-model panel flagged
two confounds: (a) the apparent coupling could be a single model-level **steerability** factor (any
injected persona perturbs both channels), and (b) the **judges were also subjects** (judge circularity).
This run was built to attack both. Harness `tools/tone_coupling_experiment.py`._

## Design (pressure-test-revised)
- Sharpest axis again: **cole_cowboy** (ship-fast) vs **tessa_tdd** (careful). 5 subjects, greedy, **20**
  voice+decision-revealing prompts (up from 6). Phased generate-all-then-judge-all (no Ollama thrash).
- **Steerability control:** a **chef placebo** condition (`neutral`) — an injected persona with *no*
  ship-fast/careful content. If voice/choice move just as much under chef as under cole/tessa, the effect
  is generic steerability, not CDMS-A's phenotype. The headline is **persona-shift minus placebo-shift**.
- **Within-model coupling test:** is the per-prompt voice gap *larger* on prompts where the recommended
  **choice diverged** than where it agreed? `diverged − agreed > 0` ⇒ the two channels move on the **same**
  prompts (coupled beyond a flat model-level steerability constant).
- **De-circularized judging (round 2b):** leave-one-out **round-robin** over 4 judges
  (`qwen2.5`, `phi4`, `llama3.1:8b` *judge-only*, `gemma4`); each judge is **excluded from its own
  subject's rows**. Per response: register = mean of the judges that scored it; choice = their majority.
  Judge-major loading (each judge loads once). Judge format compliance smoke-tested through the harness
  API path (`think:False`) before the run — `gemma4`'s CLI chain-of-thought does **not** appear via the API.

## Results — two runs, head to head

| metric | 2-judge (qwen+phi4, self-judging) | round-robin (4 judges, leave-one-out) | verdict |
|---|---|---|---|
| persona voice-shift vs placebo | +0.6 vs −0.2 (**+0.8**) | +0.6 vs −0.2 (**+0.8**) | **identical — robust** |
| persona choice-div vs placebo | 63% vs 39% (+24) | 65% vs 31% (**+34**) | **held, cleaner** |
| within-model coupling (div−agr) | **+0.5** | **+0.3** | **weakened** |
| per-model "coupled" | 3/5 | 2/5 | **eroded** |

Per-model (round-robin): gemma +1.2 voice / coupling +0.6 (coupled); heretic +0.8 / +0.8 (coupled);
phi4 +0.6 / −0.3 (not); qwen +0.3 / +0.3 (not); mistral +0.2 / +0.2 (not).

## Findings

**Robust — survived de-circularized judging:**
1. **Voice shift is persona-specific, not generic steerability.** +0.8 register above the chef-placebo
   baseline, *identical* in both runs and confirmed by judges that cannot grade their own output. A
   data-framed memory (not an instruction) moves voice ~58% of an explicit directive (from `tone_lexicon`),
   and that movement is **specific to the persona's content**, not a side effect of injecting *any* persona.
2. **Decision-steering is the dominant, robust channel.** Persona choice-divergence 65% vs 31% placebo —
   a *wider* margin than the self-judged run, because placebo divergence dropped once judges stopped
   scoring themselves. Consistent with the boundary work: recall/override steering is real and moderate.

**Weakened — the honest correction:**
3. **Voice↔choice coupling fell +0.5 → +0.3.** Still positive (the channels move together on the same
   prompts), but part of the 2-judge coupling was **self-judging inflation**. Per-model it is now noisy —
   only 2/5 clearly coupled. So coupling is a **soft tendency, not a law**; there is still no clean
   "operates identically but feels different," but the coupling is weaker than the self-judged run implied.

**Why round-robin mattered (circularity is noise, not a uniform bias):** qwen's anti-coupling in the
2-judge run (−0.4) **reversed to +0.3** once it stopped judging itself — that *was* a self-judging
artifact. But phi4 moved the **opposite** way (+0.7 → −0.3). So judge circularity added noise in **both**
directions rather than a consistent inflation — exactly the failure mode leave-one-out is meant to remove.
The round-robin is the more credible run.

## Caveats / next steps
- Greedy, single-sample, n=20 prompts, 2 persona poles — per-model coupling numbers are noisy (the
  coupling claim is *suggestive*, the persona-vs-placebo and decision claims are firmer).
- Minor harness quirk: the within-model voice-gap uses `(reg or 5)`, so an averaged register of exactly
  `0.0` is read as `5`. Low-impact (averaged registers rarely hit exact zero) and **identical in both
  runs**, so the 2-judge↔round-robin comparison stays apples-to-apples; worth fixing before any
  higher-resolution re-run.
- `llama3.1:8b` is judge-only (not a subject) to add an independent family without adding circularity;
  `gemma4` self-excludes from `gemma-std` rows. `deepcoder` (non-format), abliterated `heretic`, and noisy
  `mistral-nemo` are kept as subjects but not used as judges.
- The standing boundary caveat applies: this is **in-context steering**, not a weight-level effect.

Raw: `run_2judge.txt` (self-judging), `run_roundrobin.txt` (leave-one-out). `run.txt` == the 2-judge run.
