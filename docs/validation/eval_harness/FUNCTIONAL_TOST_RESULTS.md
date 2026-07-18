# The functional TOST — RESULTS (task #10; the terminal falsifier)

**Run: 2026-07-18, locked design v3-FINAL (commit 155f840), executed as locked, one pass, no optional
stopping. 💵 main run $10.44; arm total $15.48 of the $50 authorization. Per-item data:
`tost_main_items.jsonl`; aggregates: `tost_main_metrics.json`; caches retained.**

## VERDICT (mechanized, branch 2, all validity gates passed):

> **EQUIVALENT — THESIS FALSE, HALT.**

**The pre-agreed sentence (prereg §6/§11, verbatim, the ceiling and the floor):** *CDMS-A's disposition
individuation is not detectable in enacted deeds within δ = 0.10 at this substrate; the thesis is false
as operationally defined.*

## The numbers (all arms, tri-reference)
| arm | n | result |
|---|---|---|
| **REAL** (stripped, pooled, A-vs-C) | 799/800 | **acc 0.532, 90% CI [0.476, 0.588]** — TOST rejects (CI ⊂ (0.40, 0.60)); difference test does NOT reject (LB < 0.5) ⇒ **EQUIVALENT** |
| EXPRESSION gate (same-seed, unstripped) | 48 | **0.958** (90% LB 0.917 ≥ 0.80) — **PASS**: the reader richly enacts its loaded payload |
| POOLED-UNSTRIPPED (content-included anchor) | 100 | 0.520 — even with topic content visible, dispositions are ~indistinguishable under the honest (pooled-reference) protocol |
| NULL (A-vs-A, stripped, pooled) | 96 | X-rate 0.510, inside the permutation band — no manufacture |
| PRO judge subset (robustness) | 100 | 0.520 — corroborates the primary judge |
| NEUTRAL secondary (passive leak) | 48 | 0.521 — ~chance, as pilot-measured (scope boundary) |
| BOW stylometric diagnostic (LOSO) | — | **0.75** — a linear word-count trace persists (diagnostic, never verdict, per §7) |

Gates and guards: unparse 0.13% (≪ 12%); in-run sig_t 0.23 (≤ 0.4 — no downgrade); impute-as-miss
dual-analysis CI [0.477, 0.590] — **branch agreement** ✓; fresh-14 gate n/a (branch-1 only).

## What this result IS (pre-registered scope, §7)
- The thesis was operationalized (prereg §1, δ folded into the definition): *individuation ≝ above-chance
  relational distinguishability of enacted deeds BY A MARGIN ≥ δ, to a blind frontier judge.* On the
  locked substrate — valence-matched imposed dispositions, identity-eliciting tasks, topic-stripped deeds,
  pooled references, one frontier reader (claude-sonnet-4.6), two cross-family judges (gemini-2.5-flash
  primary, -pro robustness) — that proposition is **false**: the TOST establishes equivalence within
  δ = 0.10 with every fairness gate passing.
- **The sharpest characterization the run produced:** the judge recognizes an individual *history* almost
  perfectly (same-seed 0.958) while *dispositions* are indistinguishable (0.53) — identity as expressed in
  deeds is **per-history, not per-disposition**. And a linear stylometric classifier still separates the
  dispositions (0.75) — a machine-detectable trace that no frontier judge in this protocol converts into
  functional distinguishability.
- This kills **this substrate's thesis**. It does not adjudicate other substrates, richer dispositions, or
  other operationalizations — any such claim would need a new thesis and a new prereg (§7). No
  phenomenology (I10).

## Disclosed deviations (implementation vs the locked prereg)
1. **The LEAK gate as implemented is not the prereg's variant.** §3 specified a BOW domain classifier
   *trained on unstripped deeds* (seed-fold split) *tested on stripped* with recovery CI required to
   include 0.5; the runner computed stripped-trained BOW 2AFC variants instead (0.75), and the verdict
   chain did not consult a leak gate. **Why the verdict is robust to this:** the LEAK gate exists to
   prevent residual topic content from manufacturing a false DISTINGUISHABLE; leak can only make
   distinguishing *easier*. An EQUIVALENT verdict cannot be produced by leak — the judge failed to
   distinguish even with whatever residue remains. Flagged for the PT8 round-2 audit.
2. n_real = 799 (one item unparsed after re-ask, excluded + counted; dual-analysis covers it).

## The arc this closes
State arc: five structural attempts + the forgetting-geometry capstone → **state = f(imposed) ⊕ noise**
(no fourth term; tautological-readback XOR null throughout). Behavioral arc: five measuring rounds
($5.04) stripped away, in turn, the topic tautology, the valence tautology, and seed fingerprinting;
PT8 (round 1) forced the honest protocol; the locked terminal run then answered: **the de-confounded
disposition signal that survives is machine-traceable but not functionally distinguishable to a frontier
judge within the pre-committed margin.** The negative relocated exactly once (state → behavior), behavior
was the terminal court, and the court has ruled. **The program HALTS on its pre-registered terms.**
