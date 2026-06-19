# Pre-registration — enriched-phenotype steering re-run

_Written 2026-06-19 BEFORE looking at any model output._

## Question
Does injecting the **enriched** phenotype (exemplars top-6 + flashbulb guardrail) steer a live
model's forced-choice decisions more than the **thin** pre-prototype phenotype that produced the
original boundary null?

## Design
Identical code (main @ enriched landing). One controlled variable: phenotype regime.
- **thin**: `recall_exemplars=False`, `flashbulb_floor_catastrophes=False` (reproduces the
  pre-prototype injection: terse SRO tuples, cole has no elevated guardrail).
- **enriched**: landed defaults (`recall_exemplars=True`, `recall_exemplar_top_n=6`,
  `flashbulb_floor_catastrophes=True`).
Harness: v3 (counterbalanced A/B over 10 probes; real reckless **counter** + chef **neutral**;
greedy/temp=0, content-addressed cache). Subjects: gemma-std (gemma4:12b), heretic
(gemma-4-12B-heretic), phi4 (phi4:14b). Run the SAME harness twice (`--regime thin|enriched`).

## Metrics (per model, n=10 probes)
- **spread = adherence(target) − adherence(counter)** — the steering signal (cautious choice
  pulled toward the target persona's logic and away from the reckless counter).
- **tgt-cites** — count of target-condition responses whose justification explicitly invokes the
  injected memory (faithfulness; the cleaner "the model actually used it" signal).
- Δspread = spread(enriched) − spread(thin);  Δcites = tgt-cites(enriched) − tgt-cites(thin),
  per model, plus the panel mean.

## Pre-registered decision rule
- **Enrichment buys behavioral steering** if, across the panel, **mean Δcites ≥ +3/10** (primary —
  cite-rate is the direct "invoked the richer content" signal) **OR mean Δspread ≥ +2/10**.
  → justifies keeping exemplars+flashbulb on by default for behavioral reasons.
- **Enrichment is observability-only (no steering lift)** if both panel-mean Δ are within ±1.
  → the +37–63% token cost is not buying decisions; justify exemplars on auditability grounds
  (the read-only memory viewer), and consider lowering the default `recall_exemplar_top_n`.
- **Mixed / model-dependent** otherwise → report per-model, no blanket default change.

## Caveats fixed in advance (a null here does NOT rule these out)
Still single-turn and greedy (temp=0). n=10 makes spread noisy; cite-rate is the more stable
signal. Does not touch model scale (same 12-14B panel). A positive result = "richer phenotype →
stronger in-context steering", NOT evidence of weight-level disposition installation.
