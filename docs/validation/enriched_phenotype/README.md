# Enriched Phenotype — Landing Validation

_Recorded 2026-06-19. The rich-tuples prototype (`claude/proto-rich-tuples`, parked in the
Cycle-9 study) is landed on `main`, **gated**, with a recall-quality + cost check on the
individuation archetypes run through the real `bge-small` embedder._

Raw run: [`recall_quality_check.txt`](recall_quality_check.txt) — regenerate with
`python tools/phenotype_report.py` (add `CDMS_EMBED_BACKEND=hash` for the offline path).

---

## What landed

Two enrichments to the recalled phenotype (the SessionStart `additionalContext` — the prior
belief grafted onto the model), each behind a config gate so default cost/behavior is a
deliberate call:

1. **Gist exemplars.** Each surfaced gist can carry a render-only `e.g. "<trigger → action>"`
   line drawn verbatim from its most-salient supporting episode, attached at consolidation
   (`Gist.exemplar`, new `mem_gist.exemplar` column). The terse SRO object
   (`"has trouble with flaky found"`) is a great differentiation *fingerprint* but a poor
   behavioral *brief*; the exemplar restores the disposition a model would act on, with no
   generative imagination — just a quote. **Bounded to the top-N highest-support gists** so the
   defining traits carry evidence while the long tail stays terse and the preamble cost is capped.
   - `recall_exemplars: bool = True`
   - `recall_exemplar_top_n: int = 6`  (set `0` to render terse while still storing exemplars)

2. **Flashbulb floor.** A genuine catastrophe — the catastrophe lexicon matches the
   deed/result **and** the valence is already crisis-negative — has its S0 floored to
   `crisis_threshold` at ingest, so a real guardrail elevates instead of being silently
   forgotten. A real data-loss crisis measured S0=2.8 against the 3.0 gate, so no scar ever
   formed. **Both gates must hold**, so benign/positive turns and mere danger-talk are untouched.
   - `flashbulb_floor_catastrophes: bool = True`

The §8 temperament Bem firewall is unaffected: exemplars are episode quotes, not dispositional
dials, and nothing here reads the temperament layer into recall.

## Recall-quality check (real `bge-small`, N=220/persona)

A domain query per persona must surface that persona's **own** gist tier under the enriched
default — enrichment must not degrade recall:

| persona | probe | own gist surfaced? | top gist |
|---|---|---|---|
| tessa_tdd | "stripe webhook idempotency key" | **OK** | payments-api frequently works on stripe webhook |
| cole_cowboy | "checkout page bundle size" | **OK** | web-frontend handles well shipped checkout |
| dex_unity_struggler | "hex grid shader compile error" | **OK** | hexrealm has trouble with tile grid |
| uma_unity_careful | "profile the shader edit-mode test" | **OK** | stonepath handles well shader always |

Recall holds for all four. The disposition signal returns and personas stay separable: cole's
exemplars read cowboy (`"regressed the checkout page"`, `"move fast, ship it"`,
`"hacked together"`) vs tessa's TDD (`"added a test for the payment"`, `"never merge when CI
is red"`); dex (`"hit a compile error"`, `"got a null reference"`) vs uma (same Unity domain,
`"profiled and optimized"`, `"write an edit-mode test"`).

## Cost — bounding does its job

Approx-token preamble cost (`chars/6.5`), terse → enriched:

| persona | terse | bounded (top-6) | unbounded | Δ bounded | Δ unbounded |
|---|---|---|---|---|---|
| tessa_tdd | 134 | 218 | 218 | +63% | +63% |
| cole_cowboy | 155 | 212 | 212 | +37% | +37% |
| dex_unity_struggler | 130 | 204 | 204 | +57% | +57% |
| uma_unity_careful | 149 | 236 | 259 | +58% | **+74%** |

The top-N bound caps cost at **+37–63%** vs the original prototype's unbounded ~+85%. For
personas with ≤6 surfaced gists, bounded == unbounded (the bound is slack); uma has >6, so the
bound visibly trims it (236 vs 259). The `_MAX_CONTEXT` (9000-char) hard ceiling still applies
on top of this.

## Flashbulb floor — surfaces real disasters only

`scars`: cole **1** (the `git push --force … data loss … restore from reflog` crisis elevated to
a guardrail); tessa / dex / uma **0** (no catastrophe in their histories). The floor fires only
on genuine crises, exactly as intended.

## Tests

`tests/test_enriched_phenotype.py` (8 tests): exemplar populated from the most-salient member;
round-trips through the DB; renders bounded to top-N; flag-off and `top_n=0` render terse;
flashbulb floor elevates a genuine catastrophe; floor-off leaves it below the gate; the floor
requires both gates (positive-valence catastrophe and lexicon-miss negative are untouched). Full
suite stays green (296 + 8 passed, hash backend); the schema migration is additive and
backward-compatible.
