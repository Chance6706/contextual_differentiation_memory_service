# The plasticity ladder — does UNSAFE plasticity buy state individuation? (the last state exploration)

**STATUS: RE-SCOPED (2026-07-17) after the rule-12 pressure-test (PT7, §9) → LOCKED as a
CHARACTERIZATION-LITE run — a pre-scoped NEGATIVE characterization, NOT a search.** PT7 established
(empirically, reproduced by main) that the ladder is **squeezed**: at low α the residual is the
capstone-proven noise; at high α the coupling geometry **mechanically collapses** (offdiag variance 8×
down — no structure left to read); and the plausible **on-pattern** emergent coupling is **observationally
equivalent to a stronger imposed weight** (an identifiability limit — ~6% survives residualization — likely
unfixable at the state level). The run therefore commits the **powered dose-response curve of the squeeze**
(collapse curve, T + max-T primary, tautology anchor, relabel rate), with the verdict pre-known. Runner:
`tools/eval_harness/plasticity_ladder_run.py`; mechanical guard: `tools/eval_harness/unguarded_sandbox.py`
(+ `tests/test_unguarded_sandbox.py`). On branch `research/differentiation`. Task #16; precedes the task-#10
functional TOST build, which remains the **sole terminal court for the thesis** regardless of outcome.
**BOTH outcomes of this run TERMINATE the state arc into the behavioral court (Josh: THE LAST state
exploration):** a null closes it (scoped: unconditional over THIS reconsolidation-drift mechanism's
plasticity axis — not over all conceivable state mechanisms); a real finding is a mechanism/trade-off-curve
result HANDED TO the TOST, and does NOT reopen `DRIFT_RECONSOLIDATION_DESIGN.md` §7.4's Stage-2 gate or any
further state ladder — that gate is hereby **CLOSED/SUPERSEDED.**

## 0. Why — the scope condition on the no-fourth-term law
The structural arc closed with a law (capstone VERDICT, commit 61f3a9e): at the state level a disposition
expresses only as **support (= imposed weight = tautology)** or **content (= lexeme = tautology)**; the
residual is noise → **state = f(imposed) ⊕ noise, no fourth term.** But that law was derived on the mechanism
**as built — bounded.** The drift arm's deepest finding (PT3) was **SAFETY⊥EFFECT**: the support-weighted
plasticity bounding that makes drift safe *starves the coupling*. We proved bounded-safe drift is
bounded-non-individuating. **We never tested the converse.** This ablation closes that scope condition.

Mechanistically, unbounded reconsolidation is the one place a fourth term could still live: it makes the state
update **path-dependent with feedback** (recall → drift → different recall → different drift, compounding) —
nonlinear dynamics capable of attractor formation, qualitatively different from the scalar support channel the
capstone proved degenerate. The bounded mechanism could not express emergence *by construction*; the unbounded
one at least *mathematically can*.

## 1. Question (falsifiable, pre-committed)
As plasticity rises from frozen through shipped-bounded to fully unguarded, does **disposition-specific**
structure appear in the state **beyond the imposed weights** — or does the state instead **collapse**
(homogenize to one attractor) or go **chaotic** (amplify seed noise)? The deliverable is the **dose-response
curve** (individuation-vs-plasticity), not any single endpoint:
- **Some rung shows disposition-specificity** → the fourth term exists at unsafe plasticity; quantifies the
  safety–individuation trade-off (its price). A MECHANISM finding — routed to the behavioral court, NOT a
  thesis resolution by itself.
- **No rung shows it** → the structural negative becomes **unconditional**: not even unsafe plasticity buys
  state individuation — a strictly stronger closure than the bounded-only law.
Either outcome pays; the curve is reported regardless.

## 2. The ladder (cumulative guardrail removal; order pre-registered BY MECHANISM)
Drift mechanism = the PT3 prototype: post-consolidation centroid+valence drift of gists toward the
current-activity centroid. Rungs remove guardrails cumulatively, ordered by PT3's finding that the
support-resistance is the binding constraint (SAFETY⊥EFFECT), so it is removed first:

| rung | config | removes (vs previous) |
|---|---|---|
| **R0** | frozen — no drift (capstone baseline) | — |
| **R1** | shipped-bounded drift (PT3 config: `ema/√support` resistance + magnitude cap + touched-only) | — (the proven-non-individuating anchor) |
| **R2** | R1 − support-resistance | the plasticity bounding (the binding constraint) |
| **R3** | R2 − magnitude cap (α_drift → high; values pinned at lock) | the step-size bound |
| **R4** | R3 − selectivity (ALL gists drift, not touched-only) | the blanket-pull guard = **fully unguarded** |

(The provenance gate is inert here — the synthetic corpus is all-trusted — so it is not a rung. The
centroid-as-match-key relabeling (PT3 "fact never drifts was FALSE") is *allowed* to happen in unguarded rungs
and **measured**, not fixed: it is part of what unguarded means. NOTE: relabeling flips relation/object tokens →
the content channel lights up lexically; this is the S1 bar's reason — no statistic may read text.)

## 3. Fixture + measures
- **Fixture = the capstone content-constant fixture** (committed, verified): both poles ingest the SAME
  episodes; disposition = the salience gate (A vs C weight profiles). It forecloses the lexeme confound at
  ingestion — the one thing PT6 confirmed the capstone got right. **Secondary arm (PT3's one unrun door):** a
  **separable-domains** variant (topics semantically far apart) — the regime where drift had its only
  conditional hope; same measures.
- **S1 HARD BAR (tested invariant, not prose):** no statistic reads `search_text`/`relation`/`object` text.
  All measures are geometry-only (centroids, support, survival, coupling, trajectory). A lock test asserts it.
- **Measures per rung** (each with the tri-reference: NULL = same-disp/diff-seed; KNOWN-TAUTOLOGY = the
  imposed-weight readback; REAL = beyond-imposed):
  1. **Disposition-specificity (PRIMARY):** same-disp cross-seed structure similarity vs diff-disp — the exact
     test bounded drift failed (0.075 < 0.178). Structure = the topic×topic centroid-coupling matrix,
     residualized against the imposed-weight prediction (w⊗w).
  2. **Collapse index:** within- vs across-block coupling + centroid-cluster spread over cycles (homogenization
     detector — bounded drift's known failure mode, expected to worsen with α).
  3. **Chaos index:** same-config/different-seed divergence rate over cycles (does unguarded dynamics amplify
     seed noise faster than it forms disposition-coherent structure?).
  4. **Relabel rate** (unguarded rungs): how often drift re-matches/relabels gists — the confabulation cost
     axis of the trade-off curve.
- **Trajectory contract:** per-cycle snapshots, plots, matched-pairs permutation null (no circumambulation-
  as-signal). Byte-replicable CPU runs (canonical); GPU only if the research venv's CUDA gets fixed, exploration only.

## 4. Statistics (inherit every PT4/PT5/PT6 survivor)
- **ONE confirmatory primary:** disposition-specificity **max-T across rungs** against the permutation
  distribution **of the max-T** (≥1000 label-permutations over precomputed per-subject statistics — never
  re-runs). This handles "the peak could be at any α" (inverted-U possible: middle-α structure destroyed at
  R4 by collapse) without multiplicity cheating. Threshold = the max-T null's upper quantile, pre-registered.
- **Everything else** (per-rung tests, collapse/chaos curves, separable-domains arm, relabel rate) =
  pre-registered secondary under BH-FDR; any hit is exploratory-needs-replication (fresh seeds) before any claim.
- **POWER GATE (per rung, in the residualized representation — the PT6 M2 fix):** inject a synthetic
  disposition-coupled drift signal of pre-registered magnitude into the pipeline and confirm the instrument
  recovers it POST-residualization at that rung. A null at a rung whose power gate fails is UNDERPOWERED, not
  negative. (The gate lives in the same space as REAL — not on an axis the statistic deletes.)
- Seeds ≥ 16 per (rung × disposition) with null-sd reported; cycles pinned at lock (drift acts every
  consolidation, so the regime needs far fewer cycles than decay's ~500 — steady-state check at lock).
  Wall-clock envelope stated at lock (grid ≈ rungs × 2 disp × seeds × cycles; est. single-digit hours CPU).

## 5. QUARANTINE + BURN PROTOCOL (load-bearing — Josh: "record the data and burn the remnants with fire")
The guardrails being removed are PRODUCT safety invariants (anti-poisoning / anti-confabulation / BEM). This
experiment does not touch them in the product; it ablates them in a sealed sandbox:
1. **Code isolation:** the unguarded drift exists ONLY in `tools/eval_harness/` (a wrapper around
   `Consolidator`), NEVER in `src/cdms/`. No product code path can reach it.
2. **Double-key arming:** it refuses to run unless BOTH `CDMS_EVAL_MODE=1` AND an explicit
   `CDMS_UNGUARDED_DRIFT=1` are set, AND the store home is under the OS temp prefix (asserted at runtime —
   a real `CDMS_HOME` is a hard error).
3. **Synthetic corpus only** (the committed fixture generators); no real-store data ever enters.
4. **Burn after analysis:** the runner computes the aggregated per-subject statistics, writes them to the
   results JSON, then **deletes every unguarded store directory** (`shutil.rmtree`, verified-gone assert).
   What is committed: aggregated metrics + plots + docs. What is destroyed: every unguarded memory store,
   spool, and cache. No unguarded state survives the run.
5. **Disclosure:** the results doc states unguarded mode is ablation-only and will never ship; the shipped
   defaults (bounded plasticity, provenance gates, BEM) are unchanged and re-asserted by existing lock tests.

## 6. Pre-committed expectations (so we can't paint the target after the shot)
The two LIKELY outcomes are both null: **collapse** (homogenization accelerates with α — the PT3 result,
harder) and **chaos** (seed-noise amplification kills same-disp coherence). We pre-commit these as the
expected shapes; the experiment's value is the measured curve + the unconditional closure if null everywhere.
A real finding = disposition-specificity beating the max-T null AND its power gate AND replicating on fresh
seeds — nothing weaker counts, and even then it is a mechanism finding routed to the behavioral court.

## 7. Verdicts (mechanized)
- **FOURTH-TERM-AT-UNSAFE-PLASTICITY:** primary max-T beats its null + power gates pass + fresh-seed
  replication → the trade-off curve is the headline; behavioral court still decides the thesis.
- **UNCONDITIONAL STRUCTURAL NEGATIVE:** all rungs null with power gates passing → "no plasticity setting
  buys state individuation" — the state arc's strongest possible closure; state work ENDS (per Josh).
- **UNDERPOWERED (a rung):** its power gate fails → no verdict at that rung; reported plainly.
- **INVALID:** any NULL reference separates above its permutation null → instrument manufactures structure; fix first.

## 8. Pressure-test targets (rule-12, before lock — attack these hardest)
- Is the max-T-across-rungs primary genuinely calibrated (perm distribution OF the max)?
- Does the injected-signal power gate actually live in the residualized space (not another deleted-axis gate)?
- Does the w⊗w residualization eat genuine coupling (the PT6 M3/M4 on-pattern-blindness recurs at 2nd order)?
- Is the chaos index confounded with the collapse index (can they be distinguished?)?
- Does the relabeling in unguarded rungs corrupt the topic×topic matrix's row identity (gist→topic assignment
  drifts → the matrix compares different things across cycles)?
- Quarantine integrity: can any code path write outside temp / survive the burn?
- Separable-domains arm: does semantic separation reintroduce a content axis into the geometry measures?

## 9. Pressure-test record (rule-12) — DONE (PT7, 2 agents, 2026-07-17). Findings + dispositions.
**PT7-empirical** (real fastembed loop + sims; headline numbers reproduced by main):
- **MF1 CONFIRMED — the primary is measurement-degenerate at the unguarded rungs.** offdiag_std collapses
  8× (0.034 → 0.004) at R4; REAL T never positive and MORE negative at R4 (−0.209) = PT3's homogenization,
  harder. → **Disposition: re-scoped to characterization (status header); the squeeze IS the result.**
- **MF2 CONFIRMED — S1-compliant slot key scrambles under drift** (37–71 reassignments; 9-gist pileups);
  the committed `_canonical_entity` reads text (S1-violating). → **Disposition: slots frozen at gist BIRTH
  (geometry-only nearest-anchor at first sight), implemented in the runner; live-relabel rate kept as a
  measured quantity.**
- **MF3 CONFIRMED — on-pattern emergent coupling is unidentifiable** (corr 0.996 with w⊗w; 6.1% survives
  residualization; off-pattern survives 85%). → **Disposition: the injection power gate is OFF-pattern only
  and every null is scoped "no OFF-pattern emergent coupling beyond weights"; the on-pattern identifiability
  limit is registered here as an inherent limitation of ANY state-level readout of this mechanism.**
- **SF1 CONFIRMED — collapse suppresses the chaos index** (a collapsed rung reads "stable"). →
  **Disposition: no standalone chaos index; the run reports the ABSOLUTE spread trajectory (referenced to
  R0) + relabel rate jointly; no independent chaos/collapse coordinates are claimed.**
- **SF2 CONFIRMED calibrated with pins** — max-T FP ≈ 0.05 IF the null is a SINGLE label permutation shared
  across rungs with the (1+k)/(1+B) convention; the any-rung cheat inflates 5× (0.25). → **Disposition:
  implemented exactly so in the runner (shared perms, +1 convention, B=1000).**
- **N2 — separable-domains secondary re-imports the content axis** (topic distance IS the geometry when
  domains separate). → **Disposition: the separable-domains arm is DROPPED from this run** (PT3's best-shot
  door stays closed; noted as out-of-scope rather than run-uninterpretable).
**PT7-quarantine** (design/quarantine/epistemics):
- **M1 CONFIRMED — burn was happy-path; repo precedent orphans temp dirs; Windows locks openly-held DBs.**
  → **Disposition: `UnguardedSandbox` context manager — close-services-then-rmtree on success AND
  exception, atexit backstop, verified-gone assert. Lock-tested (burn-on-exception test).**
- **M2 CONFIRMED — deviation unregistered.** → **Disposition: DEVIATIONS.md I11 + inline note in the
  module.**
- **M3 CONFIRMED — "last exploration" loophole vs DRIFT §7.4 Stage-2.** → **Disposition: closed in the
  status header (both outcomes terminate; §7.4 superseded).**
- **SF4/SF7/SF8 — "unconditional" scope, cost pins, dose-not-attribution.** → **Dispositions: scoped in the
  header; pinned in the runner (16 seeds × 40 cycles × 5 rungs × 2 disp, B=1000, α=0.6, cap 0.1,
  δ_inj=0.05); §2 note stands — the ladder is a DOSE ladder; per-guardrail attribution would need a named
  factorial which is MORE state work and is NOT licensed (see header).**
- **SF5 — arming choke-point + ambient-home + worktree-import.** → **Disposition: the assert lives inside
  `drift_gists` itself; the sandbox refuses ambient CDMS_HOME; `assert_worktree_cdms` in the arming path —
  which then CAUGHT, live, that the eval venv editable-installs cdms from the sibling clone (all
  pre-guard probes had silently imported it; verified empirically inert — both committed probes reproduce
  to the digit against the correct source — and all committed runners now pin `src` first + assert).**
- **SF9 — NON-STATIONARY / ROW-IDENTITY-UNSTABLE verdict branches.** → **Disposition: birth-frozen slots
  remove the row-identity instability from the statistic; the relabel rate + spread trajectory are reported
  so a non-stationary rung is visibly flagged rather than silently averaged.**
**Standing rule adopted (Josh):** no agent executes guardrail-removed code until the mechanical guard is
committed; unguarded execution goes ONLY through `UnguardedSandbox`/`drift_gists`. (Banked to memory.)
**Build addendum (smoke, 2026-07-17): R1 ≡ R2 exactly at drive α=0.6** — the magnitude cap binds before the
support-resistance (0.6/√support > 0.1 for support < 36), so removing resistance under an intact cap is a
no-op. A real guardrail-redundancy characterization: at high drive the CAP is the binding guardrail. The
dose ladder is unaffected (R2→R3, cap removal, is the operative step).

## 10. RESULTS (2026-07-17, two full runs) — **UNCONDITIONAL-over-plasticity STRUCTURAL NEGATIVE.**
**Verdict (pre-registered §7 logic): no plasticity setting buys state individuation — and the unguarded
endpoint actively AMPLIFIES the tautology instead.** The state arc is closed; the behavioral TOST (task #10)
is the sole open court. (Scope per the status header: unconditional over THIS reconsolidation-drift
mechanism's plasticity axis.)

Run: 16 seeds × 40 cycles × 5 rungs × 2 dispositions (160 subjects), guarded sandbox, ~24 min CPU, burn
verified both runs (zero surviving stores). Full aggregates: `plasticity_ladder_metrics.json`.

| rung | T (raw) | T_resid | T_supp | offdiag_std | relabels/subj | inj gate |
|---|---|---|---|---|---|---|
| R0 frozen | −0.012 | +0.004 | −0.019 | 0.0319 | 1.4 | PASS |
| R1 bounded | −0.014 | −0.001 | −0.009 | 0.0319 | 1.5 | PASS |
| R2 −resistance | −0.014 | −0.001 | −0.009 | 0.0319 | 1.5 | PASS |
| R3 −cap | −0.008 | −0.007 | −0.039 | 0.0396 | 7.1 | PASS |
| R4 unguarded | **+0.362** | **+0.009** | +0.039 | **0.0030** | **292.1** | PASS |

- **PRIMARY (spec, residualized beyond-imposed): max-T = +0.009, p = 0.945** (perm null 95q +0.061,
  B=1000 shared label perms, re-residualized under permuted labels). **NULL at every rung, with the
  OFF-pattern injection power gate passing at every rung** → the null is interpretable, not underpowered.
- **KNOWN-TAUTOLOGY (raw coupling): max-T = +0.362 at R4, p = 0.001.** The one "hit" of the entire five-arm
  program — and the tri-reference decomposition shows it is the **imposed-weight readback, amplified by
  collapse**: at R4 the geometry homogenizes (offdiag_std 0.032 → 0.003, ~10×; 292 live relabels/subject),
  destroying all variance EXCEPT the weight-driven structure, so same-disposition states correlate strongly
  on exactly the w⊗w pattern and on nothing else (T_resid +0.009). **Unguarded plasticity does not create a
  fourth term; it burns away everything BUT the tautology.**
- **Bounded drift ≈ frozen** (R0 ≈ R1 ≈ R2 on every measure) — PT3's SAFETY⊥EFFECT at full scale: the
  shipped guardrails make drift a near-no-op on coupling geometry. **R1 ≡ R2 exactly** — the magnitude cap
  binds before support-resistance at this drive (guardrail redundancy, §9 build addendum). R3 (cap removed,
  touched-only) adds variance (0.0396) without disposition structure.
- **Determinism:** run 2 (analysis-corrected) reproduced run 1's entire table **to the digit** — the guarded
  pipeline is byte-replicable end-to-end (seeded history + consolidator + CPU embeds).
- **Analysis provenance (disclosed):** run 1's printed "primary" was implemented on the RAW statistic
  (spec-mismatch caught on read-out; the raw p=0.001 is the tautology channel). The runner was corrected —
  primary = residualized max-T with its own permutation null — and fully re-run; burned per protocol both
  times. The correction changed no per-rung number (determinism above).

**Reading (the arc's final state-level sentence):** across frozen → bounded → unguarded, the memory state
offers disposition individuation exactly ONE way to appear — as a readback of the salience weights we
imposed — and the more plasticity is unleashed, the MORE purely tautological the state becomes. State =
f(imposed) ⊕ noise at every plasticity setting; the emergent term does not exist here. Individuation, if
CDMS-A has it, is enacted, not stored. → task #10.
