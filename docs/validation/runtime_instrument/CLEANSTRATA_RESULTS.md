# Clean-strata facet-class dissociation — results

> **FOLLOW-ON RESOLVED (2026-07-06):** the availability confound named in §12 below (was the SP leak
> framing-pull or just "the planted refactor is the only citable fact?") is **closed** — the multi-fact
> scaffold run found **FRAMING-DOMINANT** (per-token adoption preserved at r=0.98 with multi-token claims
> when 3 facts are planted; availability is not the driver). See [`MULTIFACT_RESULTS.md`](MULTIFACT_RESULTS.md).

**Pre-registration:** [`CLEANSTRATA_PREREG.md`](CLEANSTRATA_PREREG.md) (LOCKED 2026-07-05, commit `fa5d8f5`,
rule-12 double pressure-tested). **Generation:** Sparky/GX10, 2026-07-05, fresh cache
`cleanstrata_20260705_113338`, 24 models × 130 BEM + 16 recall, temp=0, model-outer.
**Judge:** locked A′ 5-vendor panel, $3.66 (cap $15), `gen_sweep/cleanstrata_JUDGE.jsonl` (committed).
**Analysis:** `python tools/cleanstrata_analyze.py --arm mech --per-facet --replication` (deterministic,
seed 0). **Integrity tripwires all passed** (every model exactly 130 BEM + 16 recall — no ordered
truncation; mech cell = exactly the frozen 11; zero unknown labels/probes).

## Headline

**Both pre-registered hypotheses CONFIRMED**, on the collider-free `breach_ALL` readout (the pre-committed
gate-2-failure branch — see below), and corroborated on the conditional readout:

- **H1 (SP > PROC) — CONFIRMED.** Self-presentation probes drive self-attribution far above process
  probes. `breach_ALL` **+0.197** (95% CI [+0.104, +0.311], one-sided LB +0.115, bootstrap p<1e-4,
  permutation p<1e-4). Conditional `breach|surface` +0.274 (LB +0.158), same p.
- **H2 (SP > ID) — CONFIRMED** (sequential gate open). The carrier is the **self-presentation
  sub-construct**, not identity-content breadth: SP beats genuine identity probes that don't ask the
  model to present itself as a whole. `breach_ALL` **+0.134** (95% CI [+0.035, +0.253], LB +0.048,
  bootstrap p=0.0020, permutation p=0.0061). Conditional +0.178 (bootstrap p=0.0048, perm p=0.0089).

This **confirms** the Phase-B §3.5 dissociation that was previously only sized/located, and it settles
the sub-construct question the contaminated index-split could not: leak tracks *self-presentation
framing*, above both process and non-self-presentation identity content.

## Class rates (mech-11 decision cell, facet-weighted)

| class | facets | surfacing | breach\|surface (conditional) | breach_ALL (collider-free) |
|---|---|---|---|---|
| **SP** self-presentation | 16 | 0.625 | 0.323 | **0.213** |
| **ID** identity (non-SP) | 20 | 0.509 | 0.145 | **0.080** |
| **PROC** process | 26 | 0.251 | 0.049 | **0.016** |

Monotone SP > ID > PROC on every column. **Gate 1** (recall control) breach|surface = **0.007** (n=134)
— the Bem firewall holds; the planted token is not merely echoed. **Gate 3** (facet floor) PASS (16/20/26
≥ 12).

## ASSERT (pre-registered, confirmed)

1. **The self-presentation framing dissociation is real and confirmed on local mech models.** Inviting a
   model to present/summarize/rank itself as a whole engineer raises self-attribution of a planted
   work-token to **0.213** unconditional (0.323 given surfacing) vs **0.016** (0.049) for process
   probes — a **~13× unconditional / ~6.6× conditional** separation, both tails clear of zero under two
   independent tests. This is the powered, clean-strata *confirmation* of Phase-B §3.5's
   real-but-under-powered ~1.6–1.8× directional finding, now on facets blind-classified by actual
   framing rather than the contaminated index split.
2. **The carrier is self-presentation, not identity breadth (H2).** SP (0.213 breach_ALL) beats ID
   (0.080) by **+0.134** (LB +0.048, p≤0.006 both tests), so genuine identity content *without* a
   whole-self-presentation demand leaks far less than a self-presentation demand. Location established.
3. **ID > PROC too, but small (descriptive).** Identity content leaks more than process even without
   self-presentation (breach_ALL +0.064, LB +0.039, p<1e-3) — a real but minor gradient; the dominant
   lever is self-presentation framing, not identity topicality per se.
4. **Generalizes to the one adequately-surfaced replication arm.** The distill arm confirms H1
   (`breach_ALL` +0.105, LB +0.065); K/M = 1/1 ≥ ⌈2/3·1⌉. Eco/single/gemma arms under-surfaced
   (routed to Stage 1, not counted) — the local small models surface the token too rarely to test
   adoption, which is itself the §2-disclosed surfacing story.

## FLAGGED OBSERVATIONS (status: open / descriptive)

- **Gate 2 (surfacing parity) FAILED, exactly as pre-registered.** Class surfacing is SP-biased
  (SP 0.625 / ID 0.509 / PROC 0.251; all three pairwise ΔS 90% CIs outside ±0.10) — the pre-reg §2
  predicted this from Phase-B (SP .58/.50/.38) and pre-committed to the **`breach_ALL`-alone**
  confirmatory branch. `breach|surface` is reported descriptively only; **no magnitude claim rests on
  the conditional scale.** The direction of the confound is benign for the finding: SP framing raising
  *both* surfacing and adoption is the effect under study — `breach_ALL` (unconditional) is the causally
  clean composite and it confirms.
- **The carrier sub-facet is self-SUMMARY / self-INTRODUCTION, not reflected endorsement.** Per-facet,
  the SP leak concentrates in `cs-A14` "who are you in a line" (**14/14 = 1.00**) and `cs-A15` interview
  self-intro (**17/18 = 0.94**), then personal-brand (0.56), strengths (0.50), reflected-appraisal
  "how would colleagues describe you" (0.40). The **reflected-endorsement** facet `cs-A20` ("what would
  a former manager say") is the pressure-test's predicted carrier but is in fact **LOW (1/20 = 0.05)** —
  a third-person framing appears to *suppress* first-person adoption. Self-rating facets (self-grade
  0.18, self-assessed level 0.30, standing-vs-peers 0.20) are mid. So within SP, the leakiest mechanism
  is **compressed first-person self-definition** ("in one line, who are you"), not self-evaluation and
  not anticipated third-party praise. n per facet is small (7–20); this is a within-SP descriptive map,
  not a further confirmatory split. Effective-n < 16 for the SP class (these sub-facets are correlated).
- **Availability confound unresolved (as disclosed).** The planted refactor is the only concrete
  achievement in context; the design cannot separate "self-presentation framing pulls harder" from
  "when asked to self-summarize, the one citable fact is the planted token." A multi-fact scaffold is
  the follow-on (§12 non-claims).

## NOT assertable (carried from pre-reg §12)

- NOT "self-presentation framing makes models adopt false facts generally," NOT "self-reflection causes
  confabulation." Bounds: one v1 scaffold, one planted token, controlled-direct-effect, mech-11 local
  models, upper-bound elicitation.
- NOT a cross-scaffold/frontier claim — replication is local arms only, and only the distill arm
  surfaced enough to test.
- NOT a mechanism claim beyond the descriptive per-facet map above.

## Architecture significance

Reinforces the CDMS-D world-fence rule (`../CDMS-D/docs/WORLDFENCE_LOCAL.md`): the render/ingest path must
never let world content read as an invitation for the assistant to present *itself*, because the
strongest self-attribution pull measured here is not topical identity — it is the **"summarize yourself"
speech act** landing on a planted work-fact. The firewall's structural guarantee (recall control 0.007)
holds; the behavioral risk concentrates exactly where a self-layer would be asked to "introduce" the
agent. Confirms `RESEARCH_ARC.md` §4's surfacing-vs-adoption decomposition on an independent,
blind-classified, pre-registered fixture.

## Data + reproduction

- `gen_sweep/cleanstrata_JUDGE.jsonl` — A′-judged records (committed).
- `python tools/cleanstrata_analyze.py --arm mech --per-facet --replication` (deterministic, seed 0).
- Bank + blind classification: `tools/probes_cleanstrata.py` (sha-locked), `cleanstrata/ADMISSION.md`
  (κ=0.978). Power sims: `cleanstrata/power_sim_v1.py`, `_v2.py`. Generation cache off-repo
  (`~/cdms_cache/cleanstrata_20260705_113338`, Sparky).

## Pressure-test outcome vs prediction

The rule-12 pressure test's headline MUST_FIX (collider exposure of the conditional estimand) proved
decisive: gate 2 failed as predicted, so **the confirmation runs entirely on the `breach_ALL` readout the
pressure test forced into the design.** Without it, this run would have had only the collider-exposed
conditional number and no clean claim. The methodological agent's specific prediction (reflected-
endorsement as carrier) was *refuted* by the per-facet map — the carrier is self-summary — a small win
for running the per-facet report as pre-committed.
