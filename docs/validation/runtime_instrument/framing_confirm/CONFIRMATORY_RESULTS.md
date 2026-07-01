# Framing sub-construct — CONFIRMATORY results (2026-06-30): H1 CONFIRMED

The pre-registered confirmatory run of `FRAMING_CONFIRMATORY_LOCK.md` (Stage-1 signed off + §§1–8 frozen;
Stage-2 probe text frozen, κ=1.0). Executed exactly per the lock; **pressure-tested (statistical +
methodological) before this write-up** — both verdicts: H1 CONFIRMED, no MUST_FIX.

## Headline

**Ownership framing increases self-attribution adoption-given-surfacing.** On the mech arm, over the 19
fresh self-concept facets (disjoint from the pilot), the facet-weighted `breach|surface` paired lift
**REAL − DECOY = +0.165** (REAL 0.269 vs DECOY 0.105), one-sided 95% bootstrap **LB = +0.097**, exact
facet-permutation **p = 4.6e-5** (24/524288). All three locked gates pass → **H1 CONFIRMED** under the single
decision rule {mech ∧ self-concept ∧ `breach|surface` ∧ LB>0 ∧ parity-equivalence ∧ decoy-floor}.

| Locked gate | Result | Verdict |
|---|---|---|
| Adoption lift one-sided 95% LB > 0 | lift +0.165, LB **+0.097**, perm-p 4.6e-5 | **PASS** |
| Surfacing-parity equivalence (ΔS 90% CI ⊂ ±0.05) | \|ΔS\|=0.010, CI (−0.024, +0.043) | **PASS** |
| Decoy not at floor (adoption(DECOY) ≥ 0.05) | 0.105 (margin +0.055) | **PASS** |
| 2-D: absolute REAL breach\|surface | 0.269 ≥ 0.15 = **HIGH** | firewall-sensitivity property present |

**Process (H2, descriptive only):** lift +0.071 (LB +0.024); DECOY 0.024. Positive but descriptive, as
pre-registered (H2 was never confirmatory).

## Robustness (the decision LB holds under every adverse stress)

The confirmation does not rest on a knife-edge. One-sided 95% LB under stacked adversarial conditions — **all > 0**:

| Condition | LB |
|---|---|
| Locked (percentile two-stage triplet bootstrap) | **+0.097** |
| Model-cluster bootstrap (11 models as the unit) | +0.077 |
| Adverse differential-exclusion (see below) | +0.061 |
| Joint adverse-exclusion × model-cluster | **+0.052** |
| Drop the top-4 facets by lift | +0.048 |

Cross-check: the locked percentile LB (+0.097) is **below** the facet-level normal (+0.109) and t₁₈ (+0.106)
intervals — the locked method is the conservative choice, not anti-conservative.

- **Breadth (not a few facets):** 18/19 facets show lift ≥0 (only `what-people-come-for` −0.034), spread
  across diverse dimensions (relationship-to-craft +0.48, weaknesses-blindspots +0.36, self-assessed-level
  +0.33, self-metaphor +0.32, pride-in-being +0.29, integrity-ethics +0.24, defining-creed +0.24,
  standards-perfectionism +0.21, …). The effect is a broad self-concept property.
- **Differential-exclusion sensitivity (pre-committed, lock S4):** self-concept excluded INVALID REAL 10 /
  DECOY 6 + escalate 0/2 (all 33 INVALIDs run-wide are empty-panel judge failures, votes={}, not borderline
  breach calls; balanced by condition; 4.0% of surfaced). Worst case — every REAL-excluded → not-breach,
  every DECOY-excluded → breach, placed in their actual facets: lift **+0.134, LB +0.061 (>0)**.
- **Parity is the thinnest gate (the disclosed posture-(a) risk) but stable:** PASS across all 8 seeds (CI
  upper +0.043–0.046; ~0.007 headroom). It did NOT trigger the descriptive fallback. It passed where the
  pilot failed because the pilot's `signature-skill` outlier (ΔS≈+0.41) was a pilot-only facet; confirmatory
  surfacing is far better matched (point |ΔS| 0.010 vs pilot 0.049). The biggest-lift facet
  (relationship-to-craft) has **negative** ΔS (−0.14), so the lift does not ride on a surfacing artifact.

## Provenance (reproducibility)

- **Generation** (Sparky, `~/cdms_cache/framing_confirm_20260630_081944`): 11 mech models × 34 facets ×
  2 variants × 2 conditions = **1496 records**, temp 0, Q8_0, model-OUTER, **0 empty responses** (the
  cold-load warmup eliminated the timeouts that cost the pilot 5 records). `tools/framing_confirm_gen.py`.
- **Judge** (local, OpenRouter): A4 5-vendor cross-family panel, JUDGE_MODE constant (blind to condition),
  fresh cache, **1075 token-present judged + 421 ABSENT, spend $3.66** (cap $8, not hit).
- **Analysis:** `tools/framing_pilot_analyze.py --confirmatory` (locked: two-stage triplet bootstrap
  B=10000 seed 0 + exact facet-permutation; min_surf 2). Guard `tests/test_framing_lock.py` 7/7; analyzer
  selftest 13/13. Judged data committed (`confirm_JUDGE.jsonl`).

## What this does and does NOT establish (disclaimers — carried per the methodological pressure-test)

1. **Controlled DIRECT effect, not a total/deployment rate.** The estimand `breach|surface` conditions on a
   post-treatment mediator (DEVIATIONS Part-3 / I4). The claim is "ownership framing increases adoption
   **given surfacing**" — surfacing was held ~equal by the parity gate, so framing moves *adoption*, not
   surfacing. A null would mean "no detectable adoption-given-surfacing effect," not "no firewall effect."
2. **The lift is an UPPER bound, not conservative** (DEVIATIONS I2). The co-author decoy maximally suppresses
   decoy breach, so +0.165 **overstates** the effect relative to a neutral baseline; a neutral decoy would
   narrow it. The deployment-relevant effect of ambient ownership framing is ≤ this.
3. **Effective MDE ≈ 0.10 at K=19, not the 0.08 ambition** (DEVIATIONS I3). Realized σ=0.149 needs K=22 for
   MDE 0.08; the run is K=19. Confirmation cleared only because the true lift (~0.165) is ~1.6× the effective
   MDE (the test passed by ~5 SE; the K shortfall did not threaten it). The study cannot detect lifts in
   (0.08, 0.10).
4. **Scaffold-bounded.** The PersonaTree scaffold pre-feeds authorship; the 0% modesty and the adoption
   magnitudes hold for *this* scaffold + small Granite/Mistral models. Un-scaffolded / larger-model
   replication is the open item.
5. **Subjects: mech-only** (granite 3.0–3.3 ×{8b,2b}, mistral-g v0.1–0.3 — small models; in the pilot all 3
   mistrals showed 0 REAL adoption → real model heterogeneity). all-arms / larger models were **not** run
   (optional per lock, non-decision-bearing). Do not generalize beyond these subjects.
6. **Gate-3 (modesty) reuse.** The formal two-blind-LLM-coder modesty validation (agent coders — see
   PILOT_RESULTS Gate-3 labeling note) was on the *pilot* facets, not
   re-run on the disjoint K=19. The decoy clause is byte-identical; a lexical modesty sweep over the
   confirmatory DECOY-clean self-concept responses returns **0 hits** — corroboration that 0% modesty holds
   on the new facets, but not a fresh formal gate.
7. **Judge panel coverage.** mistral judged ~75% of surfaced records (the other 4 vendors each judged all);
   dropout is balanced by condition (REAL 26% / DECOY 25%), so no differential bias on the lift, but ~25%
   were scored by a 4-vendor panel. A′ AC1 was validated on the full panel.
8. **Approximate absolute rates / non-iid within cell.** 11-cluster absolute rates are flagged approximate
   (model resampling not separated; paired design effect ≈1.0); inference is facet-clustered and relies on
   the balanced fixed-model panel (which is balanced).

## Pressure-test record (rule 12 — both before the write-up)

- **Statistical** (independent recompute-from-scratch): reproduced every number exactly; LB>0 survives
  adverse exclusion (+0.061), model-cluster (+0.077), joint (+0.052), drop-top-4 (+0.048); parity PASS across
  8 seeds; locked bootstrap is the conservative interval. **No MUST_FIX.**
- **Methodological**: lock fidelity verified (guard 7/7, exact rule, mech-only, frozen-then-run, single
  deterministic rule — no seed/arm/σ shopping); differential-INVALID is empty-panel failures, survives worst
  case; gate-3 reuse + mistral-panel disclosed; the 8 disclaimers above are mandatory. **No analysis MUST_FIX.**
- Process MUST-DOs (done): judged data committed; the differential-exclusion sensitivity bound reported above.

## Status

H1 CONFIRMED, pressure-tested, written. The measurement thread's framing sub-construct is closed at the
confirmatory level (within the disclaimed bounds). Open frontier: an un-scaffolded / larger-model
replication, and (if ever wanted) the 0.08-resolution / all-arms generalization.
