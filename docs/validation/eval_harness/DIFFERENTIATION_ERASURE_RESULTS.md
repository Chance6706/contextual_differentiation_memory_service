# Differentiation via ERASURE — results (CORE THESIS)

## VERDICT: **ENDPOINT-DEGENERATE — the entity-set primary is TRUE-BY-CONSTRUCTION, NOT an individuation result.**

A four-agent rule-12 pressure-test (2026-07-17, verdict-blind, both red-team + legitimate-use lenses on
structure and prose) found — and this doc reports honestly — that **at the locked full-erasure endpoint
(`cycles=500`, `share_frac=0.08`) the surviving-gist ENTITY set ≡ the disposition's goal set, by
construction.** Every headline number is recoverable from the `_DISPOSITIONS` dict alone, with zero
mechanism: the "DIFFERENTIATES" a naive reading would report is goal-set arithmetic, not measured
individuation. **The powered 16-seed run was NOT executed** — it would restate the goalsets. The real
empirical content is the **decay trajectory**; the individuation claim is relocated to **partial erasure**
and the **functional H4** arm. This supersedes the earlier "DIFFERENTIATES" preview framing.

Supersedes the entity-set PRIMARY of `DIFFERENTIATION_ERASURE_PREREG.md` (see the post-lock addendum there).

---

## What was run
- Erasure cube (`run_erasure_cube` / `erasure_analyze`), fastembed (BAAI/bge-small-en-v1.5), M-A provenance
  guard, `CDMS_EVAL_MODE=1`. PREVIEW scale only: **3–4 seeds × 500 cycles** (not the pre-registered ≥16).
- Full {A,B,C,U} × {salience@0.25, salience@0.0, none, random} grid; per-cycle trajectory snapshots;
  F3 topic-disappearance precondition; prose-space metric (exploratory add-on).

## Preview numbers (3-seed × 500cy) — read with the pressure-test caveats below
```
entity separation  salience 0.600 [0.600,0.600]   none 0.000 [0.000,0.000]   random 0.600 [0.600,0.600]
disposition_effect 1.000 [1.000,1.000]     history_effect 0.000 [0.000,0.000]
null_AU (disp vs uniform)  salience 0.500    none 1.000    random 0.500
entity permutation r=+1.000 p=0.0015   (CIRCULAR — see F2)
prose history_effect 0.057 [0.000,0.057]   prose disposition_effect 0.206   prose permutation r=+0.917 p=0.0015
preconditions: off-goal drop median 4 (none 0); gists_decayed median 14; high-tier gist support 26 evicted; HALT=False
trajectory (salience_A n_ents): c83:8.0 c166:8.0 c249:7.67 c332:6.33 c415:4.0 c498:4.0 c500:4.0   (none_A: flat 8)
```
The **zero-width CIs** (`[0.600,0.600]`, `history_effect 0.000`) are the tautology fingerprint: nothing about
history, seed, embedder, or salience math enters those numbers — only the hardcoded goalsets do.

---

## Pressure-test record (rule-12) — four agents, ranked; MUST_FIX findings folded into code + this doc

**F1 — Entity-set primary is tautological at full erasure. [CONFIRMED ×3]** `cycles=500`/`share_frac=0.08`
⇒ off-goal topics idle ~460 cycles > gist idle-survival (~396 at the support cap), so under any non-`none`
policy survivor ≡ goalset. Then `jaccard(A,B)−jaccard(A,C) = 3/5 − 0 = 0.600` is arithmetic on
`_DISPOSITIONS`; the three entity-overlaps EQUAL the three goal-overlaps to the digit (0.600, 0.000, 0.143).
*Fold:* verdict now reports **ENDPOINT-DEGENERATE**; entity separation demoted from confirmatory primary to a
mechanism-fired sanity check.

**F2 — The entity M2 permutation null is CIRCULAR + pseudo-replicated. [CONFIRMED]** It correlates
entity-overlap vs goal-overlap, but those are *definitionally equal* here ⇒ r=+1.0, tiny p trivially; and it
pools seed×pair points as independent (violates the prereg's own M4). *Fold:* dropped from the verdict;
docstring flags it degenerate; retained only for the prose arm + a future partial-erasure design.

**F3 — H2 (salience-specificity) is UNREACHABLE at the endpoint, NOT merely null. [CONFIRMED]** Off-goal
gist death runs through `_decay_gists` (function of `cycle−last_cycle` + `support` only — never reads
`discard_policy`); the two-tier fixture (re-lived goal vs never-re-lived off-goal) means policy can't change
*which* entities survive ⇒ `salience ≡ random ≡ goalset`. **A1's mid-trajectory fast run showed
salience ≠ random OFF the endpoint** (survivor(sal,A) ⊋ goalset vs survivor(rand,A) = goalset; sep 0.675 ≠
0.600) — SUGGESTIVE (artificial config), evidence that the H2-relevant signal lives at *partial* erasure,
which `cycles=500` skips.

**F4 — H1 (salience > none) is CONFOUNDED. [CONFIRMED]** `none` = `retention_floor=0` = forgetting OFF
entirely (episodes never evict → off-goal gists re-reinforced every cycle → never decay → all 8 kept). So H1
contrasts forgetting-ON vs forgetting-OFF, establishing "episode eviction of ANY kind is necessary for
individuation" — real, but policy-independent and goalset-determined, NOT salience-specific.

**F5 — H3 verdict guard had a UNIT-MISMATCH bug. [CONFIRMED, code]** `h3["lo"] > sal["hi"]` compared an
*overlap* (~1.0) to a *separation-difference* (~0.6); can flip a non-degenerate verdict to INVALID. *Fold:*
now compares same-disposition overlap vs diff-disposition overlap (both jaccards).

**F6 — Prose "history in the prose" is an EXPLORATORY glint, NOT treasure. [CONFIRMED ×3]** `0.057
[0.000,0.057]`: (a) the CI can't exclude 0 — the cluster-bootstrap SELF-PAIRS at n=3 (a seed vs itself =
distance 0), pinning `lo` at 0 and `hi` at the point estimate (*fold:* self-pairs now skipped, but the real
fix is n≥16); (b) it barely clears the metric's own ~0.03 floor (the `none` prose separation, pure
surface/order noise); (c) "topic 0 vs prose 0.057" is partly MANUFACTURED — set-Jaccard is a hard 0, cosine
is never 0; (d) the prose permutation null (r=0.917) tests DISPOSITION (topic words), not the history axis —
it is **not** a history null; (e) prose ALSO can't separate salience from random (0.129 ≈ 0.117). Digits are
inert (0.0005) and the same-self null is exact (1.0), so the metric isn't broken — but the signal, if any,
lives in exemplar/ordering content and needs n≥16 + cosmetics stripped + a real history null (the fulcrum).
*Fold:* prose labelled EXPLORATORY / non-pre-registered, a $0 upstream SCREEN — necessary-not-sufficient for
H4, never behavioral individuation. Three constructs are NOT one: prose-distance (does the *text* differ) →
H4 (does *behavior* differ) → A′ (does the reader *own* the fact); a chain of necessity, H4 ⊥ A′.

**NITs (folded/noted):** shared past is EVENT-identical but encoding-tinted (goal_hint applies from cycle 1 —
prereg wording should read "identical event stream"); `run_erasure_subject` default `share_frac` 0.12 → 0.08
(matches the locked cube); `_random_victims` reads `cycle−1` (deterministic, just mislabeled);
`max_high_tier_gist_evicted` is decorative (not in HALT) and support 26 vs cap 100 is mildly oversold.
**Determinism: CLEAN** (histories seeded on (seed[,dispo]); random on (discard_random_seed, cycle); fastembed
deterministic; the `CDMS_EVAL_MODE` gate raises loudly).

---

## What is genuinely real (keep)
1. **The decay TRAJECTORY (mechanism result):** off-goal topics decay on a realistic ACTIVITY timescale — a
   support-26 off-goal gist cleared over ~460 idle cycles while `none` retains all 8. This validates that
   CDMS's forgetting fires on schedule (and that gist decay REQUIRES episode eviction). It is a mechanism
   check, not an individuation claim.
2. **The build machinery** (fixtures, cube, cluster-boot, prose plumbing) is reusable for the reshaped design.

## Where the individuation test actually lives (the salvage → next pre-registration)
On the biology-style **tier decomposition** (substrate × disposition × history + interactions → functional
distinguishability, each counted only if it beats a null):
- **disposition tier** = the endpoint signature (tautological → reported as mechanism);
- **history tier** = PARTIAL erasure (mid-trajectory, where WHICH off-goal topics survive depends on
  history + salience) + the **fulcrum** (does same-disposition distance scale with shared-history fraction *f*)
  + powered prose (n≥16, cosmetics stripped);
- **substrate tier** = the salience-matrix program (FT × quant × runtime);
- **assembled whole** = **H4 functional** (blind judge distinguishes A-loaded vs B-loaded behavior) — the only
  arm where differentiation is not guaranteed by construction — with render-language (estar / evidential /
  Arabic-measure minimal pairs) as a per-seam grammatical lens on the interactions.

The H2-relevant salience-vs-random difference and the history signal both require the **partial-erasure**
regime; the locked full-erasure endpoint discards them. A new pre-registration is required (the locked
primary is degenerate). **Do not run the powered 16×500 as-designed.**
