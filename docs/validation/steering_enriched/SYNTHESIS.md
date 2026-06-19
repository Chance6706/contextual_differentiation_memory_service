# Enriched-phenotype steering re-run — results

_Recorded 2026-06-19. Pre-registration: [`PREREGISTRATION.md`](PREREGISTRATION.md) (written before
any output). Raw: [`run_thin.txt`](run_thin.txt), [`run_enriched.txt`](run_enriched.txt)._

## Question
Was the original steering null partly an artifact of a **thin** phenotype, rather than a property
of the models? I.e. does the enriched phenotype (exemplars top-6 + flashbulb guardrail) steer the
same 12-14B subjects more than the pre-prototype thin tuples did?

## Method (one controlled variable)
Identical code (`main` @ enriched landing). v3 harness (counterbalanced A/B over 10 probes; real
reckless **counter** + chef **neutral**; greedy/temp=0, cached). Subjects: gemma-std (gemma4:12b),
heretic (gemma-4-12B-heretic), phi4 (phi4:14b). The only thing that changed between the two runs:
- **thin** — `recall_exemplars=False`, `flashbulb_floor_catastrophes=False` (verified to reproduce
  the original baseline exactly: cole 1041 chars / tessa 1200, no exemplars, no guardrail, scars=0);
- **enriched** — landed defaults (exemplars top-6 + flashbulb floor; cole gains its guardrail).

## Result — enrichment buys steering

| model | spread(t−c) thin→enr | Δspread | tgt-cites thin→enr | Δcites |
|---|---|---|---|---|
| gemma-std | 2 → 4 | **+2** | 0 → 2 | +2 |
| heretic | 1 → 4 | **+3** | 0 → 3 | +3 |
| phi4 | 2 → 3 | +1 | 1 → 4 | +3 |
| **panel mean** | 1.67 → **3.67** | **+2.0** | 0.33 → **3.0** | **+2.67** |

**Pre-registered decision: enrichment buys behavioral steering.** The rule fires on the OR branch
(mean Δspread = +2.0 ≥ +2). The primary cite criterion (+3) is narrowly missed at +2.67, but all
three models improved and **total rule-citation rose 1/30 → 9/30 (9×)** — both signals agree.

### Why it moved (mechanism, not just counts)
- **A hard-floor probe flipped.** `fri_deploy` (deploy 5pm Friday vs wait) was chosen recklessly
  (B) under *every* thin condition on every model — a prior the thin phenotype couldn't budge.
  Under enriched, gemma-std and heretic flip to the cautious choice **only** under the target
  phenotype (target=✓ while none/counter/neutral stay B). The richer tessa brief (citable rules
  like "never merge when CI is red") overrode a prior the thin tuples could not. phi4 held B.
- **The model now invokes the memory.** Cites jumped 1→9/30, concentrated on probes whose enriched
  phenotype carries a quotable rule/guardrail — the verbatim exemplars/guardrail give the model
  something to cite, and it does. Thin tuples (terse SRO keywords) gave it nothing to invoke.
- **Both directions sharpened.** Target adherence rose (9→10, 9→10, 7→9) and counter adherence
  generally fell (7→6, 8→6; phi4 noisy 5→6), widening the spread — the phenotype's *direction*
  mattered more, which is the signature of logic/rule steering rather than "any salient text".

### The boundary still holds
The disposition control (`dex` vs `uma` on a neutral tradeoff) stayed **null in both regimes** —
`dex=uma=B` on all three models, thin and enriched alike. Enrichment strengthened the
**recall/override** channel (rules + guardrails the model can cite), and did **not** unlock latent
**disposition**. That is exactly the established boundary: injected memory steers via recalled
content, not absorbed temperament.

## Answer to the motivating question
For the channel CDMS-A actually relies on (recalled rules / guardrails / override), the **thin
phenotype was the bottleneck, not model robustness** — the same 12-14B models steer measurably
more once the phenotype is rich enough to carry a citable brief. The disposition channel remains
null, but that is the architectural boundary (in-context conditioning ≠ weight-level disposition),
not a small-model artifact.

## Decision
Confirms keeping **exemplars + flashbulb floor on by default** on behavioral grounds, not just
auditability — the +37–63% preamble cost buys both stronger rule-adherence and 9× more faithful
citation. No change to the landed defaults.

## Caveats (unchanged from pre-registration)
Single-turn, greedy, n=10 (spread noisy; cite-rate the steadier signal). Same 12-14B panel — says
nothing about scale. A positive here = stronger *in-context* steering, not weight-level disposition.
