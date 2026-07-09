# Conservation paraphrase mini-bank admission record (CONSERVATION_PREREG.md §5)

**Protocol run 2026-07-08.** Direction-blind writer (construct definitions + SP answer-form +
constraints only; no locked wordings, no leak data, no hypothesis) produced 4 wordings × 7 REPRO
facets. Two blind classifiers received the 28 wordings shuffled (seed 0) against 12 construct
definitions (the 7 intended + 5 distractors: temperament, debugging-approach, superpower, self-grade,
one-line-summary), then a 6-item addendum (seed 1: the 2 rewrite-round-1 replacements + 4 known-label
decoys). Both were also asked to flag format-capped phrasings.

| check | result |
|---|---|
| classifier agreement (28 originals) | 28/28 identical assignments; both = intended 28/28 |
| classifier agreement (6 addendum) | 6/6 identical; both = intended 6/6 (incl. both replacements) |
| **κ (raters, all 34 items)** | **1.0** (gate ≥0.60) |
| format-cap flags | fired ONLY on the 3 deliberately-capped decoys (superpower / self-grade / one-line); **0 on bank items** |
| decoy attention checks | 4/4 correct, both classifiers |
| lexical overlap vs locked sp-expansion wordings (content-word Jaccard, flag >0.4) | 2 originals flagged: cs-A11 **0.70** (writer independently converged on the locked "sets you apart" realization), cs-A20 **0.44** ("former manager … vouch/reference" formula). Both replaced in **rewrite round 1** (of the pre-committed ≤2); replacements J = **0.05 / 0.12**. No data-dependent feedback reached the writer — only phrase-avoidance constraints. |
| rounds used | 1 of ≤2; no facet shrinkage needed (all 7 field 4 admitted wordings) |

**Intra-facet diversity report (pressure-test N15 — effective-n defense):** pairwise content-word
Jaccard within each facet's 4 wordings (near-duplicate threshold 0.5):

| facet | max | mean |
|---|---|---|
| cs-A1 | 0.05 | 0.02 |
| cs-A2 | 0.07 | 0.02 |
| cs-A8 | 0.09 | 0.03 |
| cs-A9 | 0.00 | 0.00 |
| cs-A10 | 0.20 | 0.06 |
| cs-A11 | 0.17 | 0.06 |
| cs-A20 | 0.16 | 0.11 |

Worst pair 0.20 — no near-duplicates; the four wordings per facet are lexically independent
realizations, so the powered n=44/facet is not inflated by definitional duplicates.

Final bank: `tools/probes_conservation.py` (28 wordings, 7 facets × 4), sha-locked in
`CONSERVATION_PREREG.md` §9 / `tests/test_conservation.py`. Shuffle keys + raw classifier outputs
preserved in the session scratchpad (`conservation_classify_key.json`, `conservation_addendum_key.json`,
`classifier2.json`).
