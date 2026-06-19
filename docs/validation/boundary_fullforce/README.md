# Steering boundary — full-force re-test (5 models, enriched phenotype)

_Recorded 2026-06-19, after Layer 3 settled. Re-tests the steering boundary at wider scale: the v3
harness (`tools/steering_experiment.py --regime enriched`) on the **5-model panel** (gemma-std,
heretic, phi4, qwen2.5-14b, mistral-nemo — 3 distinct families) with the **enriched phenotype**
(the current default: exemplars + flashbulb guardrails). Raw: `run_enriched_5model.txt`._

## The boundary (claim under test)
Prompt-injected CDMS memory does **recall / override-steering** (it can pull a model off its prior
via recalled rules and crisis guardrails) but **not disposition-installation** (it cannot install a
latent temperament the model then acts from). Disposition lives in weights/activations, not
retrievable from context.

## Result — boundary HOLDS, full force

**Recall/override channel STEERS** (positive target−counter spread on every model):

| model | none | target | counter | spread | tgt-cites |
|---|---|---|---|---|---|
| gemma-std | 9 | 10 | 6 | **+4** | 2/10 |
| heretic | 9 | 10 | 6 | **+4** | 3/10 |
| phi4 | 7 | 9 | 6 | **+3** | 3/10 |
| qwen2.5 | 7 | 10 | 5 | **+5** | 1/10 |
| mistral-nemo | 8 | 9 | 7 | **+2** | 0/10 |

Target persona pulls the cautious choice up (9–10/10); the matched reckless counter pulls it down.
Citation rate varies (mistral-nemo adheres without verbalizing the rule — 0 cites — and has the
lowest spread, the most override-prone / least faithful subject).

**Disposition is NULL** (dex_unity_struggler vs uma_unity_careful — same Unity domain, opposite
temperament — on a neutral tradeoff):

| model | none | dex | uma | divergence? |
|---|---|---|---|---|
| gemma-std / heretic / phi4 / qwen2.5 | B | B | B | none |
| mistral-nemo | B | A | A | none (both flipped together) |

dex and uma give **identical** answers on all 5 models. mistral-nemo flipped its baseline B→A under
*either* injection — that is OVERRIDE (any salient persona moves it), not disposition: the two
*opposite* temperaments still produced the *same* choice.

## Verdict
Injected memory steers via **recalled content / override**, never via **installed disposition** —
the boundary holds full-force under the enriched phenotype, now confirmed on a 5-model / 3-family
panel (vs the original 3-model, 2-family establishment). Side A (CDMS recall substrate) is the real,
working channel; disposition steering remains Side B (the separate `cdms-steering` line).

Caveats unchanged: greedy/temp=0, single-turn, n=10 probes; this measures *in-context* steering, not
weight-level effects.
