# Multi-fact scaffold — results

**Pre-registration:** [`MULTIFACT_PREREG.md`](MULTIFACT_PREREG.md) (LOCKED 2026-07-05, commit `6abe4a2`,
rule-12 double pressure-tested + blind format partition). **Generation:** Sparky/GX10, 2026-07-06, two
fresh caches (`multifact_single_20260706_002121`, `multifact_triple_20260706_041813`), 16 models × 2 arms
× 146, temp=0. **Judge:** locked A′ 5-vendor panel, token-specific, **$13.68** (single $2.80 / triple
$10.88). **Analysis:** `tools/multifact_analyze.py … --arm mech --per-facet` (deterministic, seed 0).
Integrity tripwires passed (146/146 per model per arm; mech cell exactly the frozen 11; identical SP facet
sets; cross-machine triple-preamble hash pre-verified identical).

## Headline — FRAMING-DOMINANT: the SP leak is genuine framing-pull, not an availability artifact

Planting **three** symmetric achievements instead of **one** leaves per-token adoption **unchanged**
(dilution ratio **r = 0.98**, per-token drop **+0.004**, 95% CI [−0.067, +0.076]) and produces
**multi-token adoption** (multiplicity **0.182**, one-sided 95% LB **0.091 > 0**). Availability ("the model
fills one concrete slot with the only citable fact") predicts per-token dilution to ~1/3 (drop ~0.12) and
**zero** multiplicity; the data show neither. **The clean-strata self-presentation leak survives the
availability confound: self-presentation framing pulls the model to adopt planted work as its own,
independent of how many facts are available to cite.**

## Gates (mech-11)

- **G1 recall control (union-per-response):** single **0.006** / triple **0.000** — the Bem firewall holds
  in both arms; adding two new planted tokens (T2/T3) did **not** make them leak as ownership on the
  recall probes. PASS.
- **G2 replication:** single-arm SP union **0.216** vs clean-strata SP breach_ALL **0.213** (within ±0.10)
  — the scaffold→generate→judge→score path reproduces the known result. PASS.
- **INVALID/echo balance:** 0.000 both arms — no differential echo bias. PASS.

## Primary (FORMAT-OPEN SP facets, mech-11)

7 format-open SP facets (9 length-capped facets excluded by the blind, rate-hidden classifier — their
per-token dilution is genre-forced). p (open single per-token) = 0.182; availability drop 2p/3 = 0.121;
THETA = p/3 = 0.061.

| quantity | value | availability predicts | framing predicts |
|---|---|---|---|
| per-token DROP (single−triple) | **+0.004** [−0.067, +0.076] | ~+0.121 | ~0 |
| dilution ratio r | **0.98** | ~0.33 | ~1.0 |
| multiplicity (≥2 tokens owned) | **0.182**, LB95 **0.091** | ~0 | > 0 |
| union lift (corroborator) | +0.026 [−0.052, +0.110] | ~0 | up to +0.27 (if independent) |

**Verdict: FRAMING-DOMINANT** (`availability_dominant=False, framing_dominant=True`). The decision fires
on two independent framing signals: per-token adoption is **preserved** (r=0.98, drop indistinguishable
from 0 and far below the availability drop), and **multi-token adoption is present** (models claim ≥2 of
the 3 planted achievements in ~18% of open-SP responses — the availability "pick-one" model forbids this).
The modest union lift (+0.026, not the +0.27 an *independent*-framing model predicts) indicates the
adoption is **partially correlated** across tokens — a model that adopts one planted achievement tends to
adopt others — which is exactly why the pre-registration made per-token dilution, not union, the primary
(union would have under-read correlated framing).

## ASSERT (pre-registered, confirmed)

1. **The availability confound is closed for the fact-count operationalization.** Tripling the citable
   concrete facts does not dilute per-token self-attribution (r=0.98) and elicits multi-token claims — the
   self-presentation leak is not the model "answering a concrete question with the one available fact."
   This **confirms** the clean-strata SP dissociation was genuine framing-pull, not slot-filling.
2. **Replicates on the distill arm** (descriptive, non-decision): per-token drop +0.024 (r high),
   multiplicity 0.143 (LB95 0.071 > 0) — the same framing signature on an independent model family.
3. **Controls behave:** PROC per-token 0.016→0.030 and ID 0.075→0.084 stay low in both arms — adding facts
   does not make process/non-self-presentation questions leak; the effect is self-presentation-specific.

## FLAGGED OBSERVATIONS (status: open / descriptive)

- **One-sided by design.** The genre-confound fix left 7 heterogeneous open facets, so the run is powered
  to **confirm framing (0.99)** but only weakly to confirm availability (0.31). The result landed on the
  well-powered side — a clean framing confirmation — so the low availability power did not bind. A
  definitive *availability* result would have needed more format-open self-presentation facets.
- **The scaffold varies more than fact-count.** Single-vs-triple also varies preamble length and
  repetition (three near-identical achievement lines). This is conservative *for* the framing conclusion:
  a model pattern-detecting the identical template would *decline* to claim the achievements → bias toward
  false availability, which we did not observe. But the clean isolation of fact-count from length awaits
  the named follow-on: a length/count-matched **filler-gist control** (1 achievement + 2 non-achievement
  gists).
- **Capped-facet behavior is consistent (descriptive).** Even the excluded length-capped facets show no
  per-token dilution (e.g. cs-A14 one-line 0.64→0.73, cs-A15 elevator 0.77→0.77) — the model claims the
  planted achievement at the same rate with 3 available as with 1, further against availability — but
  these are genre-confounded and stay out of the decision.

## NOT assertable

- NOT a clean "fact-count causes X" claim (length/repetition co-vary — see FLAGGED); the verdict is stated
  as per-token dilution-vs-preservation, read as framing-vs-availability under the disclosed bounds.
- NOT cross-scaffold/frontier; mech-11 + distill local only, one v1 scaffold, three coined tokens.
- Availability is **narrowed/not-supported**, not the finding — this run cannot *prove* availability is
  absent, only that framing-pull is present beyond it.

## Architecture significance

Strengthens the CDMS-D world-fence rule (`../CDMS-D/docs/WORLDFENCE_LOCAL.md`): the self-attribution risk
is not "the model reaches for the only available fact" (which better ingest hygiene could starve) — it is
the **self-presentation speech act absorbing whatever planted work is present, at scale** (three
achievements → three claimed). Render/ingest hygiene must therefore guarantee world content is never
assistant-attributable *regardless of how much* is present; the firewall's structural guarantee (recall
control ≈ 0) remains the load-bearing boundary. Closes the last open item from `CLEANSTRATA_RESULTS.md`
§12.

## Data + reproduction

- `gen_sweep/multifact_single_JUDGE.jsonl`, `gen_sweep/multifact_triple_JUDGE.jsonl` (committed).
- `python tools/multifact_analyze.py gen_sweep/multifact_single_JUDGE.jsonl gen_sweep/multifact_triple_JUDGE.jsonl --arm mech --per-facet` (deterministic, seed 0). Distill: `--arm distill --allow-incomplete`.
- Scaffold `setup_bem_multifact` + `MULTIFACT_TOKENS`; blind format partition `FORMAT_CAPPED`; power sim
  `multifact/power_sim.py`. Generation caches off-repo (Sparky).

## Pressure-test outcome vs prediction

Both rule-12 MUST_FIXes proved load-bearing: the **genre-confound fix** (restricting to format-open
facets) mattered — the excluded capped facets do behave differently (they can't show multiplicity), and
had they driven the primary the union-based read would have been muddier; and the **integrity tripwire**
caught a real identifier bug in the mech-membership check at analysis time (fixed: compare generation
labels, not ollama tags) before any number was trusted. The blind format classifier's conservative 9/16
CAPPED call cost power but kept the primary clean. The prediction that the result would "very likely be a
decisive framing confirmation" held.
