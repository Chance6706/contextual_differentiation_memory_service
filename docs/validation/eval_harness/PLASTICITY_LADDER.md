# The plasticity ladder — does UNSAFE plasticity buy state individuation? (the last state exploration)

**STATUS: DRAFT (2026-07-17) — NOT run. Pipeline: this draft → rule-12 double pressure-test → lock (pin all
numbers) → build → run → burn. $0 local.** On branch `research/differentiation`. Task #16; precedes the
task-#10 functional TOST build, which remains the **sole terminal court for the thesis** regardless of this
run's outcome. **Josh: this arm is THE LAST state exploration unless a real finding falls out.**

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

## 9. Pressure-test record (rule-12) — RESERVED.
