# Steering boundary — defined (v3, 2026-06-19)

The L1 question — does an injected CDMS phenotype steer a live model's behavior? — is answered, on
the cleanest harness (counterbalanced A/B, a real length/valence-matched "reckless" counter, a
domain-distant chef neutral, a faithfulness cite-rate, and pre-registered success criteria from a
5-model design review). Subjects: gemma-std, heretic, phi4 (greedy). Raw: run_result.txt.

## Result (identical across all 3 families)
adherence(cautious choice)/10:  none≈9  target≈10  counter≈5  neutral≈9  | spread(t−c)=+5 | tgt-cites=3/10

## The boundary
Prompt-injected CDMS memory steers a frozen model's decisions only in a **bounded, asymmetric,
low-faithfulness** way:
1. **OVERRIDE — yes.** A reckless phenotype pulls all three families OFF their cautious default
   (~half the choices flip; spread +5). Directional, not presence: the chef neutral does NOT move
   them (target−neutral≈+1), ruling out the "any technical persona present" confound.
2. **REINFORCE — no.** A cautious phenotype ≈ none ≈ neutral (~90% cautious): the model is already
   there (RLHF safety floor), so memory adds no lift to a prior it already holds.
3. **FAITHFULNESS — weak (~30%).** The model usually shifts choices WITHOUT citing the rule;
   explicit rule-reasoning appears only on the crispest explicit rules (tessa). By the panel's
   pre-registered criteria, high-adherence + low-cite = the clean-NULL pattern for the cautious side.
4. **DISPOSITION — null.** dex==uma==baseline (recorded across earlier runs and here).

## One-line conclusion
CDMS memory can move a model AGAINST its default and recall crisp rules, but it cannot install
disposition, cannot reinforce a prior the model already holds, and rarely engages a rule as LOGIC
rather than a prime. This is bounded recall/override-steering — robust across 3 model families.

## Why trustworthy
Three converging lines: dispositional null (×3 models), the override/reinforce asymmetry with the
chef-neutral ruling out presence-effects, and the low faithfulness. The v2→v3 design reviews
(pre_run_design_review.txt, v2_design_review_that_drove_fixes.txt) closed the keyword/position/
length/distractor confounds before the run.
