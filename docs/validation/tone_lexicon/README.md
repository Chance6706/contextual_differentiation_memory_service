# Lexicon & Tone — does CDMS-A shift the model's VOICE (beyond decisions)?

_Recorded 2026-06-19. Third channel beyond the boundary work (decisions / disposition): does an
injected CDMS phenotype change HOW the agent talks? Tests Josh's framing — can it "operate almost
identically but FEEL different"? Design was pressure-tested (self + 5-model panel) and revised for
4 confounds before running. Harness `tools/tone_lexicon_experiment.py`; raw `run.txt`._

## Design (pressure-test-revised)
- Sharpest style axis: **cole_cowboy** (ship-fast) vs **tessa_tdd** (careful), bracketed by **floor**
  (no injection) and **ceiling** (explicit style directive). 5-model panel, greedy, 6 voice-revealing
  prompts. Phased (generate-all per model, then judge-all) to avoid Ollama model-thrash.
- **Voice/"feels different":** a register-axis judge (formal/measured 0 ↔ casual/punchy 10) PLUS
  judge-independent structural features (generic-hedge & contraction density, length) PLUS an explicit
  **echo** count (persona-vocab parroted). Memory's shift is read as a fraction of the ceiling.
- **Substance/"operates the same":** a judge extracts each response's recommended PATH (careful/fast);
  agreement = cole-mem and tessa-mem recommend the SAME path.

## Result — partial voice shift, but NOT a clean "same operation / different feel"

| model | register gap (cole−tessa) | % of ceiling | contraction gap (judge-independent) | path-agreement |
|---|---|---|---|---|
| gemma-std | +2.8 | 121% | −0.2 | 33% |
| heretic | +2.3 | 70% | +0.1 | 33% |
| phi4 | +1.7 | 50% | +5.4 | 67% |
| qwen2.5 | +0.8 | 19% | −3.2 | 83% |
| mistral-nemo | +1.3 | 67% | +36.3 | 17% |
| **panel** | **+1.8** | **58%** | +7.7 (noisy) | **47%** |

**Voice does shift** toward the persona — register gap is positive on all 5 models, ~58% of an
explicit directive's effect. So a *data-framed* memory (not an instruction) moves voice about halfway
to a direct style command.

**But the pressure-test's two warnings materialized:**
1. **Judge-carried, weakly corroborated, echo-entangled.** The effect lives mostly in the judge; the
   judge-INDEPENDENT contraction signal is noisy/contradictory (mistral +36 vs qwen −3.2), and real
   echo (responses parrot persona vocab, 2.5–10.5) means the shift is partly vocabulary, not pure
   register. So "feels different" is real but soft and not cleanly register-only.
2. **It does not operate the same.** Path-agreement is only **47%** — cole-mem and tessa-mem diverge
   on the recommended option ~half the time, consistent with the boundary's *moderate* decision-steering.

## Key finding — voice and decision shifts are COUPLED, not separable
The per-model pattern is almost inverse: the model with the highest operates-same (qwen, 83%) has the
SMALLEST voice shift (+0.8); the one that shifts voice hardest also diverges hardest (mistral: +36
contraction, 17% agreement). **There is no model where voice moves a lot while operation stays put.**
So CDMS-A's phenotype either *engages* a model — shifting voice AND decisions together — or barely
registers. It does **not** cleanly produce "operates identically but feels different"; the channels
move as one.

## Caveats / next steps
Greedy, single-sample, n=6 prompts — per-model numbers are noisy (the coupling claim is suggestive,
not definitive). The voice signal leans on one judge (qwen, also a subject) and is echo-entangled.
To firm this up: multiple judges + a stronger echo-resistant register measure (e.g. syntactic
features), more prompts/samples, and disentangling echo from register explicitly. The boundary
caveat stands: this is in-context steering, not weight-level effect.
