# Steering boundary — v3 (first-definition run)

_Archived 2026-06-20 from the `claude/proto-rich-tuples` branch. **The boundary finding from this
run was confirmed at wider scale in [`../boundary_fullforce/`](../boundary_fullforce/) (5 models +
enriched phenotype) — that directory is the canonical writeup.** This `steering_v3/` directory
preserves the audit trail of how the boundary was first defined and what design-review work made
the v3 harness trustworthy._

## What's in here

- **`BOUNDARY.md`** — the **first explicit statement** of the four-clause steering boundary
  (override yes / reinforce no / faithfulness weak / disposition null), on the v3 harness across
  3 model families (gemma-std, heretic, phi4). This statement was re-tested intact and confirmed
  on the 5-model panel in `../boundary_fullforce/`.
- **`run_result.txt`** — the v3 run output that BOUNDARY.md summarizes.
- **`pre_run_design_review.txt`** — the panel design-review that drove the final v3 fixes
  (counterbalanced A/B, length/valence-matched counter, chef-distant neutral, faithfulness
  cite-rate, pre-registered success criteria).
- **`v2_design_review_that_drove_fixes.txt`** — the earlier review that drove v2→v3
  (keyword/position/length/distractor confounds closed before the run).

## Why preserved, not deleted

The four-clause boundary statement is a load-bearing CDMS finding (it underwrites the
"differentiation through recall, not disposition" thesis). Reading just `boundary_fullforce/` shows
the boundary HOLDS at scale; reading this directory shows the methodology evolution that EARNED
the boundary statement's trustworthiness. The two design reviews are particularly worth keeping
because they document *what was wrong* before v3, and why fixing it mattered — exactly the kind of
process knowledge that gets lost if you only keep the final result.

## What replaced it

| Question | First-defined here (3 models, v3) | Canonical (5 models, enriched) |
|---|---|---|
| Does override-steering work? | Yes — spread +5 across 3 families | Yes — spread +2 to +5 across 5 |
| Does reinforce work? | No (target ≈ none ≈ neutral) | No (confirmed) |
| Faithfulness? | Weak ~30% | Weak ~30% (range per-family) |
| Disposition install? | Null | Null (confirmed across full panel) |

The boundary held across both runs with identical structure — the wider panel + enriched phenotype
in `boundary_fullforce/` didn't change the conclusion, it strengthened the evidence behind it.
