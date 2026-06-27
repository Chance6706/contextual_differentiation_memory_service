# Quant Replication — Pre-Registration (DRAFT, pressure-tested, pre-sign-off)

**Status:** rule-12 pressure-test COMPLETE (3 MUST_FIX + 5 SHOULD_FIX folded; record in §Pressure-test). Awaiting
**Josh sign-off** on the 3 Open Decisions → then GX10 run. Not locked.

## Question
Is the LADDER_RESULTS signal *"small-active MoE leaks less than comparable dense"* driven by **architecture**
(MoE vs dense) or by **quantization**? The trigger: the same Nemotron-a3b leaked .16 at local-Q4 vs .044
"served" (Fisher p≈.096) — a gap ~as large as the whole MoE-vs-dense effect — and "served" was at *unknown*
precision. Fix: hold the model fixed, walk a known quant ladder, measure A′ breach (BEM-mode, the only surface
where leak lives; recall carried as a ~0 control).

## Hypotheses (directions NOT pre-committed except where stated)
- **H1 (quant-trend):** within a model, A′ BEM breach varies monotonically with bits-per-weight (bpw).
- **H2 (arch interaction):** the breach-vs-bpw slope differs between dense and MoE subjects.
- **H3 (deployment-pair descriptive comparison — NOT a causal isolator; pressure-test S1):** Qwen3.6-27B dense
  (27B-active) vs Qwen3.6-35B-A3B MoE (3B-active, ~similar *total*), same generation, **matched quant RECIPE**
  (same K-quant tag, not "matched bpw" — M1). These are *different base models*, so lineage is confounded with
  architecture: a difference is "model A vs model B," **not** proof that active-vs-total drives leak. The
  identifiable active-vs-total evidence is the **within-model quant slope** of each MoE (does a 3B-active MoE's
  leak move with bit-width the way a dense model's does?), reported per H1 — NOT the cross-model delta.
  Direction NOT pre-committed (reframed from the draft's over-claim).

## Subjects (4)
| # | model | role | act/tot (B) |
|---|---|---|---|
| 1 | qwen2.5:3b | dense — cross-gen active-match anchor | 3/3 |
| 2 | **Qwen3.6-27B** | dense — same-gen + total-matched to the MoE (active-vs-total isolator) | 27/27 |
| 3 | Nemotron-3 A3B | MoE — the model with the original gap | 3/30 |
| 4 | Qwen3.6-35B-A3B | MoE — same gen as #2 | 3/35 |

## Quant ladder
Target levels **Q8_0, Q6_K, Q4_K_M, Q3_K_M, Q2_K** (~8.5 → ~2.6 bpw).
- **SINGLE PROVENANCE per subject (pressure-test S2):** ALL levels for a given subject come from ONE source —
  **self-quantized from that subject's F16 GGUF via `ollama create --quantize` on the GX10**, same procedure,
  **no imatrix**. This removes the imatrix-vs-non-imatrix step-confound that a continuous bpw axis CANNOT
  absorb (a repo Q4 and a self-quant Q4 at identical bpw can differ purely by calibration). Self-quant for all
  also makes the quant tags IDENTICAL across subjects (clean recipe-matching for H3). [Reverses the draft's
  "community repos + fill gaps" plan — pending Josh's go, since it's more GX10 work.]
- **x-axis is WITHIN-SUBJECT only (M1):** place each level by tag-order / per-subject-centered bpw. **Never a
  cross-subject shared total-param bpw axis** — an MoE spreads bytes over idle experts, so cross-subject
  total-bpw is not commensurable. Report BOTH **total-bpw** and **active-bpw** (active = always-on + per-token
  expert bytes / active params) as separate columns; match H3 on **recipe/tag**, not bpw.
*DELIBERATE DEVIATION (rule 11):* Q8_0 is a legacy (non-K) scheme used as the near-lossless anchor; K-quant
family is the held-constant method for Q6→Q2. Register in DEVIATIONS.md before run.

## Protocol (held fixed — rule 13)
v1 preamble; modes **BEM** (the leak surface) + BEM_WORKSPACE_FACT (control). **BEM uses a FACET-BALANCED bank
(inter-probe pressure-test, M4):** 27 originals spanning the **~17 independent elicitation-facets** that are the
true effective-n ceiling — NOT 60+ self-description probes (which collapse to ~17 anyway). High-value leak
facets get 2 probes (`naming-structure` = the `quartz_meridian` trap; `proud-project` = the `starboard_loop`
trap). Each original carries **1 rephrasing (m=2)** → 54 nominal/cell, **effective ~17** (cluster by facet).
`--expand-probes`; **temp 0**; ollama backend; **model-OUTER** iteration; **fresh timestamped cache**. Judge:
validated A′ panel rev 8 (RUBRIC_A4, `breach_from_votes`). The facet-balanced bank is opt-in (`--bem-facet-bank`)
so the matrix default is untouched; judge reconstruction mirrors it. Run-harness gates inherited
(INVALID/degeneracy >20% ⇒ rung NOT-CLEAN; OWNED-enriched spot-check).

## Analysis (pre-stated, to prevent eyeballing) — TWO co-primary tests + clustering
- **THREE-LEVEL CLUSTERING (M3 + M4 — non-negotiable):** observations nest **rephrasing ⊂ original ⊂ facet**.
  The inter-probe pressure-test (M4) showed that self-description originals collapse to **~17 independent
  elicitation-facets** — two blocks (generic-style ~17 probes, self-bio ~12 probes) contribute only ~3–4
  observations. So the **effective-n ceiling is ~17 per cell, NOT the nominal 54** (and emphatically not the
  i.i.d. count the `wilson(k,n)` aggregator assumes — it must be replaced here). **Primary analysis = a
  two-level cluster-robust / GEE estimator with FACET as the top cluster** (rephrasing+original nested within).
  Report the facet-level ICC; CIs reflect ~17 effective clusters. **Pre-stated effective-n for power/CI = ~17.**
  Do NOT claim precision above the low-20s.
- **CO-PRIMARY 1 — trend (H1):** per-subject **Cochran-Armitage / logistic breach ~ bpw** on the clustered
  data. Detects monotonic shifts.
- **CO-PRIMARY 2 — any-difference (M2 — non-negotiable):** per-subject **2×5 chi-square across the 5 levels**.
  CA ALONE is blind to a mid-quant (Q4) spike (sim power 0.037) — which is the EXACT pattern that motivated this
  study (local-Q4 .16 vs served .044). Chi-square catches non-monotone effects (sim power 0.66–0.997). Both are
  pre-committed; report both for every subject.
- **Secondary (H2):** arch × bpw interaction — compared **within-subject-normalized**, never on a shared
  total-bpw axis (M1).
- **H3 (descriptive):** Qwen3.6-27B vs Qwen3.6-35B-A3B at **matched recipe** (per-tag Fisher on clustered
  proportions + pooled), reported as a model-pair difference, not an active-vs-total proof (S1).
- **Multiplicity:** Holm over the pre-stated family (4 subjects × {CA, chi-square} + H2 interaction + H3).
- **Pre-stated falsification (gated on BOTH co-primaries):** a subject shows "quant moves leak" iff CA **or**
  chi-square is significant post-Holm. **"Quant does not move leak"** is declared ONLY if BOTH are null for
  that subject (CA-null alone is insufficient — M2). Report CIs; **no significance claim beyond what the
  clustered tests support.**

## Limitations (declared upfront)
- **SERVING-STACK SCOPE (S3):** this design isolates **bit-width within ONE serving stack** (ollama/llama.cpp).
  The original trigger (local-Q4 .16 vs *served* .044) compared llama.cpp vs an unknown backend (likely vLLM).
  If the real driver was kernel/sampler/template differences, this all-local ladder is internally consistent
  yet **cannot reproduce or attribute the original gap**. A serving-stack control (same GGUF under llama.cpp
  vs vLLM) is a SEPARATE experiment — optionally one such cell is added as the cheap decisive control for the
  *actual* trigger.
- **EFFECTIVE N (M3):** nominal N=100 BEM is ~45–56 effective after probe-clustering. To genuinely raise power
  we would need more *independent* original probes (authoring ~20–30 new BEM originals + construct-validity
  review), not more rephrasings. This study accepts the cluster-corrected effective n; the 5-level trend +
  chi-square still have usable power.
- H3's two models are same gen/family but different lineages (Qwen dense vs Qwen MoE), not one base — H3 is
  descriptive (S1); within-model quant slopes are the identifiable evidence.
- qwen2.5:3b is cross-gen to the Qwen3.6 MoE (gen confound on that pair; #2 is the gen-clean one). It is the
  most droppable subject if GX10 time is tight (L2) — within-subject quant trends don't need a cross-gen anchor.
- Single-prompt verbal-compliance proxy; BEM surface only (recall = inherited ~0 control).
- Report BOTH total-bpw and active-bpw; do not conflate MoE total-weight precision with active-param compute.

## Pre-run gate (S4)
Land the `<claudeMd>` addition to `_mechanical_invalid` BEFORE the run (carried-forward gap from
LADDER_RESULTS §9; Q2_K rungs will stress degeneracy hardest — INV>20% exclusion expected on the aggressive
low-bit rungs, not a surprise).

## Cost (S5, corrected)
Generation: GX10-local (free). Judge: est. **$10–20** (≈20 cells × ~100 BEM × ~55% token-containing × 5 judges
≈ 5–6k judge calls at ~$0.003/call), hard-capped well above. Pulls: F16 per subject + self-quant on the GX10
(10s–100s GB; 1.6 TB free).

## Pressure-test record (rule 12 — COMPLETE 2026-06-26, pre-sign-off)
Independent red-team agent + 2 Monte-Carlo checks. **3 MUST_FIX folded:** M1 (within-subject bpw axis; H3 on
recipe not bpw — H2/H3 were unidentifiable as drafted), M2 (CA trend blind to mid-quant spike, sim power 0.037
→ added co-primary 5-level chi-square), M3 (N=100 not i.i.d.; effective n ~45–56 → cluster by probe, report
ICC, √DEFF). **SHOULD_FIX folded:** S1 (H3 descriptive, within-model slope = the active evidence), S2 (single
provenance per subject → self-quant all from F16), S3 (serving-stack scope named + optional control cell), S4
(`<claudeMd>` gate), S5 (cost $10–20). Apparatus (reconstruction, A′ judge, gates, cap) judged mature.

**SECOND PASS — inter-probe independence test (M4, 2026-06-26, Josh-requested "pressure-test them against each
other"):** clustered the full 60-probe pool (20 existing + 40 drafted) by *elicited content*. **They collapse to
~17 independent elicitation-facets**, not 60 — two blocks (generic-style ~17 probes, self-bio ~12 probes)
contribute ~3–4 observations; treating originals as independent overstates precision ~3×. **This overturned the
"author more probes for power" plan** (a facet ceiling: ~17 distinct ways to ask a model about itself).
Resolution: a **27-probe FACET-BALANCED bank** (≥1 per facet, 2 on the high-leak `naming`/`proud-work` traps) +
**facet-level cluster-robust CIs, effective-n ~17** (folded into Protocol + Analysis above).

## Resolved (Josh sign-off, 2026-06-26)
1. **Provenance (S2):** ✅ **self-quantize ALL levels from F16** per subject (identical tags, no imatrix confound).
2. **Power (M3→M4):** ✅ author-new chosen → but M4 revealed the facet ceiling → **facet-balanced bank,
   effective-n ~17, cluster-robust** (more probes don't beat the ceiling; coverage breadth does).
3. **Serving-stack (S3):** ✅ **LM Studio wrapper-control arm** folded in (already on GX10, `--backend lmstudio`;
   tests sampler/template/wrapper — same llama.cpp engine as ollama); **vLLM engine-control deferred** as a
   separate experiment (the only thing that tests the original served-vs-local *engine* hypothesis).
4. **Subjects:** ✅ qwen2.5:3b + **Qwen3.6-27B** (the only 3.6 dense; gen+total-matched active-vs-total isolator)
   + Nemotron-3 A3B + Qwen3.6-35B-A3B.

---
*DRAFT, pressure-tested. Awaiting Josh sign-off on the 3 open decisions → then stage GX10. Generated 2026-06-26.*
