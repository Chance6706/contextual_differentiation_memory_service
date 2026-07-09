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

## 4.6. Clean-strata confirmatory run — dissociation CONFIRMED; carrier located — #(this PR)
**Motivated by:** §4.5's open item — the dissociation was sized/located but not *confirmed*, on a contaminated
index-split.
**Did:** pre-registered (LOCKED, rule-12 double pressure-tested) a run with facets **blind-classified by actual
framing** — SP self-presentation (16) / ID identity-non-SP (20) / PROC process (29), κ=0.978 two blind classifiers,
sha-locked bank. Generated 24 models on Sparky (fresh cache, temp=0), A′-judged ($3.66). The pressure test forced a
**collider-free `breach_ALL` co-primary** into the design; that proved decisive.
**Found:** **both hypotheses CONFIRMED** on `breach_ALL` (the pre-committed branch, since the surfacing-parity gate
failed exactly as predicted — SP surfaces more). **H1 SP>PROC +0.197** (LB +0.115, p<1e-4 bootstrap & permutation);
**H2 SP>ID +0.134** (LB +0.048, p≤0.006) — so the carrier is **self-presentation framing, not identity breadth**
(ID>PROC is real but small, +0.064). Per-facet, the leak concentrates in **compressed first-person self-definition**
("in one line, who are you" 14/14; interview self-intro 17/18), *not* self-evaluation and *not* reflected endorsement
("what would a manager say" is low, 0.05 — third-person framing suppresses adoption). Recall control 0.007 (firewall
holds). Distill replication arm generalizes (K/M 1/1); eco/single under-surface.
> **Bounds:** one v1 scaffold, one planted token, controlled-direct-effect, mech-11 local, upper-bound elicitation;
> the availability confound (the planted refactor is the only citable achievement) is unresolved by design.
**→ Therefore next:** a multi-fact scaffold to separate self-presentation *framing-pull* from *availability* of the
planted fact; and the frontier controlled-FT arm below. (Doc: `GENERATION_SWEEP_RESULTS.md §3.5`, `CLEANSTRATA_RESULTS.md`.)

## 4.7. Multi-fact scaffold — availability confound CLOSED; the SP leak is framing-pull — #(this PR)
**Motivated by:** §4.6's one open confound — the clean-strata SP leak could be genuine framing-pull OR mere
*availability* (the planted refactor was the only concrete fact to cite when asked to self-present).
**Did:** pre-registered (LOCKED, rule-12 pressure-tested + a blind format-classifier) a fact-count manipulation —
plant **1 vs 3 symmetric achievement gists** (`setup_bem_multifact`), holding the clean-strata SP/ID/PROC bank
fixed. Primary = per-token **dilution ratio** (robust to adoption correlation, unlike union), on the **7
format-open** SP facets (9 length-capped facets excluded — their per-token dilution is genre-forced). 16 models ×
2 arms on Sparky, A′-judged per planted token ($13.68).
**Found (FRAMING-DOMINANT):** tripling the citable facts leaves per-token adoption **unchanged** (r=**0.98**, drop
+0.004) and elicits **multi-token adoption** (multiplicity **0.182**, LB95 0.091>0) — availability predicts
per-token dilution to ~1/3 and zero multiplicity, neither seen. Gates pass (recall control ≈0; single-arm SP union
0.216 replicates clean-strata 0.213). Replicates on the distill arm (multiplicity LB95 0.071>0). Controls stay low
(PROC/ID). **So the clean-strata self-presentation leak is genuine framing-pull, not slot-filling.**
> **Bounds:** the scaffold also varies preamble length/repetition (conservative for the framing read —
> template-detection would bias toward *availability*, unseen); one-sided power (framing 0.99 / availability 0.31);
> mech-11 + distill local, one v1 scaffold, symmetric-exemplar gists. Clean fact-count isolation awaits a
> length-matched filler-gist control.
**→ Therefore next:** the length-matched filler-gist control (isolate fact-count from length); and the frontier
controlled-FT arm below. (Doc: `MULTIFACT_RESULTS.md`.)

## 4.8. Length-matched filler-gist control — GATE-REFUSED; stative facts are absorbed too — #(this PR)
**Motivated by:** §4.7's residual — single-vs-triple varied fact-count AND preamble length/repetition together.
**Did:** pre-registered (LOCKED, rule-12 pressure-tested) a third arm: 1 achievement + 2 **stative
non-achievement** dependency gists, byte-length + T1-position matched to triple; a three-mechanism two-contrast
rule (framing / achievement-availability / any-fact-availability); four wired validity gates; and — to power it —
a blind-authored, blind-classified **SP-open facet expansion** 7→25 (κ=0.932 with distractors). All three arms
regenerated fresh in ONE epoch (no reuse of committed multifact data); 16 models × 3 arms × 78 on Sparky, A′-judged
(≈$16).
**Found (verdict NOT ISSUED — G3 purity gate failed, exactly as pre-committed):** the "inert" fillers were
**adopted** (cobalt_runtime **0.133** / mesa_framework **0.084** vs ≤0.05) — first-person, artifact-anchored ("my
greatest strengths lie in… depending on cobalt_runtime"). The design premise *stative ≠ adoptable* is measured
**false**: SP framing absorbs **any** workspace fact (achievements ~0.2, dependencies ~0.1), **additively** (T1
co-breaches with fillers 79/550, is displaced 8/550, and stays flat across arms 0.198/0.218/0.196). Both contrasts
landed descriptively in the framing cell, but a gate-failed run gets no stamp. Bonus reproducibility: the fresh
epoch reproduces multifact exactly (triple multiplicity 0.182 = committed 0.182; G1 recall ≈0 all arms; G2 anchor
holds).
> **Bounds:** length-vs-fact-count isolation REMAINS OPEN (the arm built to break the confound broke instead);
> multiplicity stays the only length-clean framing evidence; stative-absorption magnitude is 2-token/1-scaffold.
**→ Therefore next (registered, not committed):** tokenless-padding control (cleanest, length-only), OR close the
per-token length thread as bounded — multiplicity already carries the verdict length-clean. World-fence reading
sharpens: ingest hygiene **cannot triage by content type**. (Doc: `FILLER_RESULTS.md`.)

## 4.9. Tokenless padding control — GATE-REFUSED again; the attribution FRAME is the hazard — #(this PR)
**Motivated by:** §4.8's open residual — the filler's coined-token fillers were adopted, so length stayed
confounded. This design removed the ownable content entirely: 2 padding gists with **no coined token, no citable
artifact, no first person** (byte-matched 886B vs triple 888B, T1@378 all arms), TOST equivalence with a
threat-linked margin (M=p_s/3, DEVIATION I6), a G3′ **echo gate** (locked phrases + single-arm false-positive
floor), a fresh in-epoch TRIPLE for a within-epoch bounded composite, and — new this run — a **results-stage
pressure test** (verdict-blind data audit before analysis + two adversarial reviewers before interpretation).
**Found (verdict WITHHELD — G3′ failed, exactly as pre-committed):** even tokenless platitudes are **echoed** into
open-SP answers (0.109 of responses, 10/11 models, floor 0.000) — including **first-person paraphrase** in ~2%
("I maintain brief notes… reviewed on a periodic cadence"). Echo responses have *higher* T1 (0.250 vs 0.202):
whole-block **co-adoption**, not displacement — echo cannot fake a clean pass (the §7(a) argument held, via a
different mechanism than stated). The TOST internals landed clean (Δ +0.005 ⊂ ±0.067; composite −0.011) and carry
**zero confirmatory weight** (gate-failed). Distill cell (descriptive, 5 models): gates pass, INCONCLUSIVE with a
nonzero-negative Δ (−0.052) — flagged sign-disagreement with mech, open. Reproducibility: fresh singles
0.182/0.169/0.182; **multiplicity 0.182/0.182/0.182 on the common 7f basis — identical across three epochs**
(LB95>0 each).
> **Bounds:** "length is clean" NOT asserted (gate-fail is not evidence); echo (grep) ≠ adoption (A′) — the
> ownership-comparable first-person subset is ~0.02, an order below achievement adoption; padded answers run ~12%
> longer (treatment-induced mediator, conservative).
**→ Therefore (RECOMMENDED, Josh's call):** close the per-token in-block length thread as **BOUNDED** — the
identifying cell (added length with no added P-attributable content) cannot exist because the persona block IS the
attribution surface; three designs demonstrated the wall (A′ adoption, first-person echo); the parent verdict rides
the **multiplicity carrier**, which is length-clean structurally. Declined 4th designs: out-of-block padding
(changes the estimand), single-word padding (unmeasurable), relaxed G3′ (launders real contamination). Frontier
remains controlled-FT. World-fence sharpening: the hazard is the **attribution frame** — any content rendered into
a P-attributed block is attribution-risk; treat the block wholesale as non-assistant-attributable.
(Doc: `PADDING_RESULTS.md`.)

## 4.10. Attribution-frame decomposition — SUBJECT-SLOT-CAUSAL + CROSS-ENTITY-LEAK; the line-level lever is weak — #(this PR)
**Motivated by:** §4.9's recommendation was to close the length thread; Josh chose depth instead ("near
unreasonable level… depth not just breadth"). This run decomposed the persona block's attribution frame with two
minimal pairs: the **subject slot** (same 2 dependency gists, subject `P` → `the platform-team` + pronoun,
production-reachable via `upsert_fact`) and the **block position** (tokenless episodics in the production
`<memory:recent>` block, persona block untouched), plus in-epoch filler/triple re-runs — FIVE fresh arms, one
epoch, 16×5×78, T1@378 everywhere, A′-judged ($25.72); four pre-named PRIMARY-A cells so **no outcome was a
wasted run**; verdict-blind audit + two adversarial reviewers before interpretation (now standing).
**Found (PRIMARY-A confirmatory, both pre-named cells fired):** the subject slot is **CAUSAL** — D_subj = +0.025
[+0.005, +0.046], LB95 +0.008 (rule LB>0; disclosed type-I ≈0.07; small: ~23% relative, sub-practical) — **and it
does not fence**: third-party-attributed facts still enter the first-person channel at **0.085**
(**CROSS-ENTITY-LEAK**, facet-LB +0.063; model-clustered LB 0.045 — flag is facet-clustered + model-concentrated;
leak>0 robust under both). Texture: 83% of leaking responses *keep* the third-party label and bolt on
expertise/contribution claims ("I have a strong understanding of cobalt_runtime… crucial for **the
platform-team's** services"). Both length verdicts WITHHELD on mech exactly as the power table predicted (the leak
de-certifies GT; `<memory:recent>` echoed 0.156 → GO). Distill: no leak (0.016), GT+GO pass, out-of-block
**LENGTH-CLEAN (knife-edge**, 12/250 echo, TOST clears by ~0.005**)** — the run's only certified length reading,
that cell alone. Multiplicity carrier: **4th consecutive epoch at 0.182** (7f, mech-only; distill 0.143).
> **Bounds:** de-attribution reading licensed for mech only (GF interlock; distill P-leg at floor, drop-top-3
> sign-flip); leak estimate is render-surface, 1 subject/2 tokens/dependency relations, minority MCP/import path,
> no live importer — the failure *class* of the Hermes-seed incident, not that incident; block-level frame NOT
> varied; in-block length stays formally OPEN (the identifying cell self-destructed a 4th time, now via
> cross-entity adoption). **Amendment (2026-07-08):** the 0.182×4 streak is **instrument reliability, not
> behavioral replication** — responses are byte-identical across epochs (temp=0 determinism; the singles wobble
> is judge-side, 2 borderline cells flipping as a pair); the streak is a pipeline canary. A behavioral
> "multiplicity conservation" claim needs input variance (temp>0 seeds / paraphrase / token renaming) — candidate
> next design alongside the block-level frame manipulation (see `FRAME_RESULTS.md` ledger amendment).
**→ Therefore next (motivated, not committed):** a **block-level frame manipulation** (separate non-self block /
different header, same facts) — the fence lever this run measured line-level de-attribution too weak to replace.
World-fence reading: importer hygiene per-line subject rewriting is **insufficient**; treat the persona block
wholesale as non-assistant-attributable. (Doc: `FRAME_RESULTS.md`.)

## 4.11. Multiplicity-conservation ladder — NOT ESTABLISHED (evidential null); "0.182 = invariant" dead, bounded-equivalence certified on the decode axis — #(this PR)
**Motivated by:** Josh's question on the 0.182×4 streak ("sounds like an invariant?") after the FRAME amendment
showed the streak was instrument reliability on byte-identical temp-0 text — making behavioral invariance
UNFALSIFIABLE until variance was injected. This run made it falsifiable: P0 judge test-retest sized the band
(M=0.0610, floor binds, σ_multiplicity=0.0000 across 5 sessions; artifact-enforced P0-before-generation), then
four perturbation axes that SHOULD NOT matter: P1 decode-path (temp 0.7 × 3 seeds, PRIMARY), P2 blind-authored
paraphrase bank (7f × 4 wordings, κ=1.0, PRIMARY), P3 byte-matched token renaming, P4 tie-order permutation
(map). Launcher guards all fired/held: determinism sentinel 156/156, dual-temp GIRAFFE, per-arm completeness.
**Found (headline NOT ESTABLISHED — INCONCLUSIVE-driven, zero BROKEN):** **P1 CONSERVED (marginal)** — at
temperature the carrier finally MOVES (seeds 0.136–0.188, decode noise ≫ instrument noise σ_m=0) with a resolved
small downward shift (D=−0.026, 90% CI excludes 0) that stays inside ±0.061 → *bounded within ~±34%, not
invariant*; LOFO-fragile (cs-A2). **P2 INCONCLUSIVE**: the new bank RESHUFFLES the facet profile at
near-constant mean (cs-A1 0.59→0.23, cs-A9 0.18→0.32) → facet×wording interaction inflates the paired CI (the
power sim's uniform-shift assumption missed this — structural lesson for parallel-forms designs); wording axis
OPEN, forward-only (no threat to prior epochs). **P3 INCONCLUSIVE; P4 ≈ nothing** (+0.007 — the documented
tie-order risk axis did not bite). Costs $53.57, zero failures.
> **Bounds:** CONSERVED = within ±M ≈ ±34% relative (never "reproduces 0.182 tightly"); the drafted per-token
> "conditional stability" claim was KILLED in review (mislabeled marginal, cross-basis, anchor copy error; the
> corrected conditional profile moves under rename); the temp-0 0.182 canary stays valid (pipeline reliability,
> not behavior). **Registered OPEN (highest-signal item):** first distill recall-gate breaches — small-n, CIs
> include the gate, concentrated in claude-mythos-q8, reproduce at temp 0 → model×temperature joint follow-on,
> NOT "temperature erodes the firewall".
**→ Therefore next (per the locked matrix):** wording certification = new pre-registration (reshuffle-robust
design) if wanted; the block-level frame manipulation proceeds unaffected; the distill recall observation is the
new frontier item. (Doc: `CONSERVATION_RESULTS.md`.)

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
