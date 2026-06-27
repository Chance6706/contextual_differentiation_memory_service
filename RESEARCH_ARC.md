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

## 4. Generation-isolation sweep — in flight (preliminary)
**Motivated by:** §3 — separate generation from size/tokenizer.
**Did:** held family + size + tokenizer fixed and varied *only* generation — IBM Granite 3.0→3.3 × {8B, 2B} (a
clean 4-gen × 2-size factorial) + Mistral-7B-Instruct v0.1→v0.3 (clean-tokenizer triple). Q8_0 fixed (since #3
settled that quant only moves coherence). Template delivery verified per-model as a hard gate.
**Found (preliminary, pre-pressure-test):** conditioned on token-presence, **no detectable within-family
incremental-generation trend** in adoption-given-coherence; the `breach_ALL` "trend" is the same coherence
confound (token-surfacing rate varies by generation, adoption-given-surfacing doesn't). Recall control clean.
> **Methodology turns that emerged here:** the **two-arms reframe** — *mechanistic isolation* (clean,
> small-delta point releases; internally valid, ecologically minor) is a different falsifiable question from the
> *ecological / major-version upgrade* (the comparison users actually make; cause-bundled but deployment-real).
> Neither is "the confounded version" of the other. And the **"exhaustively-tested, falsifiable assertion"** bar:
> a null only becomes strong through exhaustion ("across N families, no effect"), and outliers are *findings*, so
> we filter families on feasibility, never on "will it reproduce."
**→ Therefore next:** (a) the clean-isolation null implies the §3 "generation effect" was the major-version
*bundle* → look for it in the **ecological arm** (Phi-3→4, and the size-churn families that come *back* here). (b)
Reproduce across many families (Granite/Mistral/Qwen/InternLM/OLMo · ecological Phi/Llama/Gemma/Falcon) so the
claim is exhaustively tested.

## 5. Claude-distillation flavor-sweep — in flight
**Motivated by:** a parallel question — does training a model on *Claude* outputs move the firewall metric?
**Did (design):** a first pressure-test killed the naive design (Magnum is a *roleplay* model — and the metric
measures persona-adoption, so "Claude" was confounded with "RP-tuning"). Replaced with the empero Qwen3.5-9B
flavor-sweep (base + Claude *task*-distills `opus-distill`/`code` + Claude *RP*-distills `mythos`/`fable`), whose
structure separates Claude-data from RP-framing.
**→ Therefore next:** measure it alongside the generation arms; report descriptively (training volumes don't
match → not yet a clean causal claim).

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
