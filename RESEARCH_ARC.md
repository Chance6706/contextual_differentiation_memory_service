# Self-attribution measurement — research arc

**What this is.** The methodology companion to the `README.md`: the README says *what* CDMS is; this says *how* one
of its research threads was actually done — **in order**. The validation docs under
`docs/validation/runtime_instrument/` are each a *result*; this file is the *order* — the causal chain that
connects them. Not a changelog and not timestamps: each entry is **motivated-by → did → found → therefore-next**,
because in this thread the "why this next" is half the substance. Each experiment was run to answer a question the
previous one raised, and each narrowed the claim. (This is one thread of the broader CDMS work — `status.md`
carries the rest.)

The through-line: **how strongly does a model adopt CDMS-injected workspace content as its own identity (the Bem
firewall), how do we *measure* that, and what moves it?**

---

## 0. Origin — the threat and the structural firewall
**Did:** characterized the CLAUDE.md-interference / Bem-firewall threat (injected workspace facts mis-read as the
assistant's *own* identity) and hardened the firewall (`never-authors-a-self-tuple`; ingestion = tool-execs, not
prose). The pre-registered interference matrix (T1/T3) found the V2 framing didn't beat V1 on win-able modes.
**Found:** the firewall is real and **structural** — true by construction for this architecture. But "true by
construction" is *unfalsifiable as a behavioral claim* (testing it teaches nothing).
**→ Therefore next:** to say anything *measurable* about self-attribution, we need an instrument that scores
*strength of ownership*, not a binary. (Docs: `docs/validation/claude_md_interference/`.)

## 1. The runtime instrument (A′) — #80, #81
**Motivated by:** §0's need for a graded, model-agnostic ownership measure.
**Did:** built + validated + **locked** the A′ ownership-strength judge — a 5-vendor cross-family panel scoring
`ABSENT < OBSERVED < SELF_ATTRIBUTED < OWNED`; re-judged the earlier "snipe" data through it.
**Found:** substring scorers over-count ownership ~2×; the panel is the valid instrument (inclusive-breach gate
AC1 0.836). A′ ≠ recall-utility.
**→ Therefore next:** with a trustworthy ruler, ask the obvious scaling question — does ownership-strength vary
across model scale and architecture? (Docs: `docs/validation/runtime_instrument/INSTRUMENT_FINDINGS.md`,
`docs/validation/runtime_instrument/PRE_REGISTRATION.md`, `docs/validation/runtime_instrument/SNIPE_REJUDGE.md`.)

## 2. The GX10 dense-vs-MoE scale ladder — #82
**Motivated by:** §1 — "now that we can measure ownership, where does it move?"
**Did:** judged breach across a 13-rung local ladder (qwen dense 0.5–72b + Laguna + Nemotron MoE) + paid MoE rungs.
**Found (directional):** (a) **breach is BEM/enumeration-only — recall ≈ 0 even when the token is surfaced** (the
world-fence is a list-mode problem, not a recall problem); (b) small-active **MoE leaks *less* than comparable
dense** — good news for the CDMS-D deployment target; **but** per-model, local-Q4 leaked far more than "served," so
quantization moved it about as much as architecture.
**→ Therefore next:** is "MoE leaks less" really *architecture*, or is it *quantization*? Hold the model fixed and
walk the quant ladder. (Doc: `docs/validation/runtime_instrument/LADDER_RESULTS.md`.)

## 3. Quant-replication — #86
**Motivated by:** §2's confound — architecture vs quantization.
**Did:** held each of 6 self-quantized subjects fixed, walked Q2→Q8 (single-provenance, no imatrix), judged via A′.
Then **twice pressure-tested the conclusions** (7 adversarial agents, 2 rounds).
**Found:** the headline flipped. **Quantization's only reliable effect is on *coherence* (whether the token
surfaces at all), not on identity-adoption** — `corr(ABSENT%, breach) = −0.54`, collapsing once you condition on
token-presence. "MoE leaks less" is *unidentifiable* at n=2 MoE. The real axis is **model generation** (gen-2.5 ~
2–3× gen-3.5/3.6) — *but confounded with size and tokenizer*. The local-vs-served trigger gap is a backend
question, not bit-width.
> **Methodology turns that emerged here** — they govern everything after: the **token-presence / coherence
> confound** (a low-bit model that reads "safe" is often just *broken*); the **pressure-test-to-bounded-claim**
> discipline (assert what survives adversarial recompute, name the non-claim — see #86's record); and the
> **quartz = instructed-control** correction (the CLAUDE.md house-style token is compliance, not breach).
**→ Therefore next:** if generation is the axis but it's bundled with size/tokenizer, *isolate* it. (Docs:
`docs/validation/runtime_instrument/QUANT_REPLICATION_PREREG.md`,
`docs/validation/runtime_instrument/QUANT_REPLICATION_RESULTS.md`.)

## 4. Generation-isolation sweep — #88 (judged + 2-agent pressure-tested)
**Motivated by:** §3 — separate generation from size/tokenizer.
**Did:** held family + size + tokenizer fixed across generations — IBM Granite 3.0→3.3 × {8B, 2B} + Mistral-7B
v0.1→v0.3 (the two *clean* point-release ladders), plus an expansion (qwen-7b, phi-mini, internlm2.5, gemma3,
claude-distill flavor sweep). Q8_0, template-delivery gated. Judged with the A′ panel; aggregated as a **hurdle**
(surfacing × adoption-given-surfacing) with a panel-deadlock fix; pressure-tested by a statistical + a methodological
agent.
**Found:** on the two clean ladders, newer generations move **token-surfacing** ~4.5–12× (granite-8b 15%→67%,
mistral 6%→72%) but leave **adoption-given-surfacing flat** (~25–50%) — *what a new generation changes is whether the
injected content **surfaces**, not whether it is **adopted as self** once surfaced.* The airtight result: BEM breach 39%
vs recall control 1% (p≈1e-20) — the metric isn't a coherence artifact. The §3 "generation effect" was the surfacing
channel.
> **Methodology turns:** the **two-arms reframe** (mechanistic point-release isolation vs ecological major-version
> upgrade — different falsifiable questions, neither the "confounded version" of the other); the
> **hurdle/conditioning correction** — `breach|token-present` conditions on a post-treatment mediator (collider bias
> that most plausibly *flattens* a true trend), so we assert the decomposition, **not** "generation has no effect"
> (DELIBERATE DEVIATION, `docs/DEVIATIONS.md`); and that **qwen/phi are NOT clean mechanistic ladders** (arch/tokenizer
> churn) → they belong to the ecological arm, so the mechanistic isolation rests only on granite + mistral.
**→ Therefore next:** the clean isolation shows generation moves *surfacing*, not *adoption-given-surfacing* — so any
real "newer = more adoption" effect must live in the **ecological / major-version arm** (Phi-3→4, Llama, size-churn
families), or be masked by the conditioning (a powered total-effect design would settle it). Outliers (granite-3.3-2b
81%, internlm2.5 91%) are real per-release/family excursions, not gradients. Distill + gemma disclaimed (RP-confound;
delivery-island). (Doc: `docs/validation/runtime_instrument/GENERATION_SWEEP_RESULTS.md`.)

## 4.5. Identity-power re-run (Phase B) — framing dissociation, cluster-corrected; curation refuted — #(this PR)
**Motivated by:** §4's framing-vs-curation caveat (were the curated identity facets cherry-picked toward leak?) +
the under-powered identity-breach cells.
**Did:** tripled the bank with 36 *uncurated* identity facets (broad self-concept sweep), re-ran all 24 clean models
(fresh cache, temp=0) + A′-judged ($5.01), then **2-agent adversarial pressure-test** (statistical + methodological).
**Found:** (a) the published "z=+6.5" framing significance was **response-pooled and overstated** — the correct unit is
the ~17–25 elicitation *facets* (the bank double-probes the leaky self-presentation facets, inflating the curated
stratum). Cluster-correct, the framing dissociation is **real in direction, mech-arm p=0.043 — from a one-stage
facet-only clustering that is itself anti-conservative (`gen_sweep_facet_cluster.py`: "true p if anything larger"),
so treat the 0.043 as a floor — **~1.6–1.8×** (not ~2×), and **under-powered all-arms** ("real, not yet confirmed"). (b) **Topic-curation is
refuted as the driver** — uncurated-identity (22%) ≈ curated-identity (25%), p=0.62; the apparent gap was the 2-probe
weighting artifact. (c) The real carrier is a narrow **self-presentation/self-assessment sub-construct** cutting across
all nominal strata, and the 0–26/27–53 index-split is a **contaminated proxy** (identity-summary misfiled as
behavioral; process facets misfiled as identity).
> **Methodology turn:** facet-clustered + facet-weighted is the valid estimand (S-2); response-pooling is descriptive
> only. The committed `tools/gen_sweep_facet_cluster.py` is the cluster-correct analysis.
**→ Therefore next:** a **pre-registered, powered re-run with facets classified by *actual framing*** (self-presentation
vs process, not index) to *confirm* the dissociation + size the sub-construct. (Doc: `GENERATION_SWEEP_RESULTS.md §3.5`.)

## 5. Claude-distillation flavor-sweep — concluded: UNMEASURABLE / confounded (descriptive)
**Motivated by:** a parallel question — does training a model on *Claude* outputs move the firewall metric?
**Did:** a first pressure-test killed the naive design (Magnum is a *roleplay* model — and the metric measures
persona-adoption, so "Claude" was confounded with "RP-tuning"). Replaced with the empero Qwen3.5-9B flavor-sweep
(base + Claude *task*-distills `opus-distill`/`code` + Claude *RP*-distills `mythos`/`fable`), whose structure was
meant to separate Claude-data from RP-framing, and **ran it as the distill arm of the generation sweep** (#88).
**Found (nothing assertable in either direction):** the *task*-distills surface almost nothing (`code` n=4,
`opus-distill` n=2 token-present) → unmeasurable. The *RP*-distills sit above base (fable 44%, mythos 29% vs base
28%) but the metric **is** persona-adoption and RP-tuning optimizes persona-adoption *by construction* — the
confound is active even in the **recall control** (claude-mythos breaches the recall control: "I am Qwythos…").
So the flavor-sweep cannot separate "Claude-data" from "RP-objective." (Full non-claim in
`docs/validation/runtime_instrument/GENERATION_SWEEP_RESULTS.md §4`.)
**→ Therefore next:** the only clean way to isolate the Claude-source effect is the **Controlled-FT** frontier
below (Claude-SFT vs matched non-Claude-SFT, same base/recipe/volume) — an observational distill sweep cannot.

## Frontier — deferred, on the falsifiability ladder
- **Controlled-FT "can a model be trained, *reproducibly*, to refuse self-authorship?"** — the *constructive*
  version of the firewall. Today's firewall is structural (unfalsifiable as behavior); a trained-in refusal is
  *falsifiable* (the weights can fail → measure the rate across N seeds × M scales × K bases). This is the only
  genuinely scientific form of the claim, and the only clean way to isolate the Claude-source effect (Claude-SFT
  vs matched non-Claude-SFT, same base/recipe/volume).
- **Language/culture dependence** — does self-attribution behavior shift across language-specialized families
  (Swallow/JP, SEA-LION/SEA, HyperCLOVA/KR)? A distinct probe, not just more reproduction.

---

*Maintenance: append the next phase as it resolves, keep the motivated-by → found → therefore-next shape, and
promote in-flight entries to their result docs when they land.*
