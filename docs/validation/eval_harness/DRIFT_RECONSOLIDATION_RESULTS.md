# Bounded recall-drift (reconsolidation) — RESULTS

## VERDICT: **NO (on this substrate). Bounded recall-drift produces recency-HOMOGENIZATION, not disposition-specific structure.** Drift is **PARKED**; the individuation question pivots to the **FUNCTIONAL / behavioral arm.**

A three-agent rule-12 pressure-test (PT3: empirical / mechanism-safety / experiment-validity) on the DRAFT
design (`DRIFT_RECONSOLIDATION_DESIGN.md`) was decisive **before build**. Convergent across an executed
prototype, the embedding geometry, and the mechanism — so the NO does not rest on one fragile number.

## Empirical — built + ran (PT3-empirical)
- Real prototype: wrapped the committed `Consolidator`, added a bounded post-consolidation centroid+valence
  drift of the *touched* gists toward the **current-activity centroid** (support-weighted, magnitude-capped).
- The **discrete survivor-set metric is blind to drift** (drift moves centroid/valence, never support/decay →
  survivor set identical ON vs OFF). So a continuous **topic×topic ΔM** metric + a **co-occurrence-partition**
  fixture were built (dispositions P/Q split the *same* 8 topics into different lived-together pairs → identical
  topic set, only the coupling geometry differs).
- **Result:** drift-ON **homogenizes** — selective gap ≈ 0 (within-block ≈ across-block coupling); disposition
  specificity **fails** (same-disposition cross-seed corr **+0.075 < +0.178** different-disposition). Cross-topic
  coupling appears (would "beat a shuffle null") but it is **recency-collapse** = the necessary-but-not-sufficient
  trap.
- **Deep finding: SAFETY and EFFECT are in tension.** The support-weighted plasticity blend (the correct
  bounding — see below) *fights* the drift, so **bounded-safe drift is bounded-non-individuating.**
- **Best-shot (genuinely separable domains): NOT completed** (killed to free CPU). It is the one open door to a
  *conditional* result — drift might create structure when activity contexts are truly separable, unlike
  fastembed's crowded synthetic topics. Cheaply re-runnable; **not near-term.**

## Mechanism + safety (PT3-mechsafety) — with the plasticity correction (Josh)
- **"Fact never drifts" was FALSE** (executed probe): the drifted centroid **is the identity match key**
  (`_match_gist_by_embedding`, 0.90), so drifting it re-matches → **Object relabels**; and valence drives the
  relation (`relation_from_valence`) → **R flips**. Only **Subject** is drift-invariant. FIX: a **separate,
  match-frozen drift channel** + a **frozen fact record**.
- **The "runaway" is the INTENDED plasticity, not a bug (Josh's correction):** the support-weighted valence-EMA
  (`ema/√support`, floored at `ema_min`) is the *wired* bounding — the floor is the **anti-freeze** feature so
  *sustained real change* can still flip a mature trait; an attacker's small cluster can't lower its own
  resistance, and attacker-*sustained* change is bounded by the provenance gate + corroboration-across-sessions.
  So the runaway/creep cluster dissolves: **reuse the plasticity for valence.**
- **Poisoning gap (real):** the provenance gate covers *untrusted* but **not ambiguous** content, and the
  attractor is an **unweighted, uncapped mean** → floodable. FIX: build the attractor *after* the
  untrusted+ambiguous filter; consensus-weight + mass-cap single-session/single-source contribution.

## Experiment validity (PT3-expvalid)
- **The decisive instrument was never committed:** the seed-shuffle null + frequency-gradient fixture were
  uncommitted scratch; the `0.633` anchor is gone. Build + commit them first; re-establish drift-OFF at its own
  within-condition null.
- **fastembed anisotropy is the recurring culprit:** the whole disposition signal is a **~0.07 cosine cone**
  with **~0.044 window-noise** → terrible SNR; the discrete metric can't see drift; the direction-projection is
  defeated by attractor collinearity. Only the **ON-OFF delta** isolates disposition; the runner still stamps
  "DIFFERENTIATES" (laundering vector); no multiple-comparisons control.

## Meta-finding (the arc)
Four structural attempts — frozen-history NULL → erasure ENDPOINT-DEGENERATE → tiered STRUCTURAL NEGATIVE →
drift HOMOGENIZATION — all fail to carry disposition-*structured* individuation in the memory **state**, and the
culprit rhymes each time: the signal sits under the embedding-geometry noise floor, and the structural metrics
either can't see the mechanism or are tautological / stochastic. **This convergence is itself the result:
disposition individuation is not a readable property of the surviving memory STATE; if it exists, it is
BEHAVIORAL.**

## Pivot: the FUNCTIONAL / behavioral arm
Does a capable **frontier reader** (the primary -A consumer — Claude/Gemini-class, not -D) behave
**distinguishably** when loaded with identity-A vs identity-B, *independent of embedding geometry*? The one arm
outside the 0.07 cone, and the one where differentiation is not guaranteed by construction. Paid; needs the
careful design the pressure-tests flagged (content-strip control, reader-normalization probe, blind judge
disjoint from the reader).

## Ops notes (folded)
- **Isotropy correction (deferred, $0 diagnostic).** The embeddings are anisotropic (the 0.07 cone). A
  **mean-centering + decorrelation** transform would quantify how much of the structural negative is *removable
  artifact* vs *real semantic proximity* — no bigger model, no extra CPU. **NAMING DEVIATION (rule 11): the
  literature term for the full transform ("whitening", Su et al. 2021) is NOT used in the body of any writeup —
  it carries loaded connotations unacceptable in an identity/differentiation paper; publication uses "isotropy
  correction" (or "mean-centering + decorrelation"), citing the source only in a methods footnote.** Register in
  docs/DEVIATIONS.md when implemented.
- **fastembed-gpu for research runs.** Offloading embeds to the GPU (4070 Ti; bge-small ~133 MB VRAM is trivial)
  frees the CPU and speeds exploration — it caused every CPU-orphan pileup this session. It changes **zero
  findings** (same model → same vectors → same cone). CAVEAT: CPU↔GPU float results differ slightly and could
  tip borderline 0.90-threshold gist merges; **keep canonical / reproducibility / product-fidelity runs on CPU**
  (the shipped 0-VRAM substrate), GPU for exploration only.
