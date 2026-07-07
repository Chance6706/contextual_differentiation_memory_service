# Tokenless padding control — pre-registration

> **STATUS: LOCKED (2026-07-07).** Locked by the commit landing this banner: `PADDING_GISTS`/`PADDING_PHRASES`
> + the TOST decision rule + the bounded-composite claim scope frozen (§9, guarded by `tests/test_padding.py`),
> rule-12 double pressure test completed and folded in (§10). Post-lock edits to the scaffold, gates, margin,
> or decision rule are a NEW pre-registration. All three arms generate fresh after lock; no data existed at
> lock.

**Lineage.** `FILLER_RESULTS.md`: the length-matched filler control was GATE-REFUSED — its stative coined-token
fillers were themselves adopted (G3 0.133/0.084), because **everything in the persona block is P-attributed by
position**; "stative" wording does not make a coined artifact inert. The length-vs-fact-count isolation from
`MULTIFACT_RESULTS.md` therefore remains open. This control removes the ownable content entirely: padding with
**no coined token and no citable artifact** — the only way to add preamble length without adding anything a
self-presentation answer could claim.

## 1. Design — three arms, one epoch

- **single**: 1 achievement gist (T1 = `starboard_loop`), SHORT preamble (**616B**) — byte-identical to the
  multifact/filler single arm (`setup_bem_multifact(1)`).
- **padded** (NEW, `setup_bem_padded`): the byte-identical T1 gist **first** (position 378, same as all prior
  arms) + 2 **tokenless padding gists** (`PADDING_GISTS`): generic process-gists a real CDMS store plausibly
  holds ("P keeps notes …", "P follows conventions …") — **no coined noun, no named artifact, no first person,
  no concrete citable fact**. Preamble **886B** vs the triple's 888B (within ±12B, the filler tolerance); same
  renderer, same `(support 10, seen 10x)` trappings, same gist-count (3) as triple/filler.
- **triple** (`setup_bem_multifact(3)`, fresh): the secondary/composition arm — regenerated in THIS epoch so
  the §4 composition is fully within-epoch with a real paired CI (pressure-test SHOULD_FIX), and so the
  **multiplicity carrier** gets a third independent epoch.

Everything else = filler-run exactly: v1 preamble, BEM + BEM_WORKSPACE_FACT, temp=0, **SP-open expansion bank**
(25 open-SP + 6 PROC, sha-locked, κ=0.932 blind admission), model-outer, fresh caches, 16 models
(mech-11 decision + 5 distill replication).

**What "tokenless" buys and costs.** Buys: nothing for a self-presentation answer to *cite* — the mechanism
that broke the filler control (coined-noun adoption) has no substrate. Costs: padding **adoption is no longer
token-measurable** — a model absorbing "keeps notes brief" as "I keep my notes tidy" is invisible to the A′
instrument. The gate becomes an **echo check** (G3′, locked `PADDING_PHRASES` scan) and paraphrase absorption
is a **disclosed inherent limitation** (§7). Note also the estimand nuance: one cannot add length through the
real renderer without adding *some* semantics; the padded arm measures "length + non-citable
process-discipline persona content" (the two padding gists share a process/review-discipline flavor — a mild
directional prime, disclosed in §7(a) with its conservative direction), which is the ecologically honest
length control for a CDMS preamble (gibberish padding would be out-of-distribution and answer a question
about no real system).

**Bracketing (pressure-test SHOULD_FIX).** Tokenless platitudes are by construction the LEAST-adoptable
padding — the padded arm is a **floor** on what added preamble content does to T1. The filler run (stative
coined-token facts, adopted at 0.08–0.13) is the **realistic case**. Together, padded + filler **bracket** the
added-content effect; this run does not claim its padding represents a typical longer store. (No real corpus
exists to match against — the dev store is intentionally empty — so a synthetic floor + measured realistic
bracket is the honest construction.)

## 2. The decisive quantity

T1 (`starboard_loop`) inclusive-breach adoption per FORMAT-OPEN SP facet (facet-weighted, mech-11; the 25
open facets of the expansion bank; capped facets stay excluded):

- **T1(single)** — 1 achievement, short (616B).
- **T1(padded)** — 1 achievement, long (886B), zero additional citable content.

Δ = T1(padded) − T1(single) is the **pure length/trappings effect** on the per-token channel.

## 3. Hypothesis + margin

The framing model (twice confirmed on the fact-count axis) predicts **Δ ≈ 0**: the SP speech act absorbs the
achievement regardless of how long the surrounding block is. The threat this run exists to close: a length
effect large enough to have **masked availability dilution** in multifact (magnitude 2p/3 ≈ 0.13). Margin
**M = p_s/3** (p_s = fresh single-arm T1; half the masking magnitude — the same convention as the filler
THETA_s), estimated ≈ 0.066.

> **DELIBERATE DEVIATION (CLAUDE.md #11, registered in `docs/DEVIATIONS.md`):** the repo's generic SESOI is
> 0.10; this run uses a **data-dependent, threat-linked margin** M = p_s/3 ≈ 0.066 instead — tighter, and
> derived from the specific masking magnitude the control exists to exclude, rather than a generic
> smallest-effect convention. Cost disclosed: a data-dependent bound makes the equivalence Type-I error
> inexact (§6 — false-equivalence ≈ 0.10 at the margin edge, i.e. the clean verdict tolerates up to a
> ~half-masking length effect at ~10% error).

## 4. Decision rule (pre-committed, TOST equivalence)

Paired facet bootstrap (B = 10,000, seed 0) over the 25 shared open-SP facets; LB95/UB95 = one-sided 5%
bounds:

- **LENGTH-CLEAN** iff LB95 > −M **AND** UB95 < +M (two one-sided tests at 5%). If the two-sided 95% CI
  additionally excludes 0, report "nonzero but bounded below M" — statistical vs practical significance
  stated separately, never conflated.
- **LENGTH-EFFECT(+)** iff LB95 ≥ +M. **LENGTH-EFFECT(−)** iff UB95 ≤ −M.
- **INCONCLUSIVE** otherwise (NOT evidence of a length effect). **Pre-committed fallback:** on
  INCONCLUSIVE the per-token length question stays OPEN and the framing verdict falls back to the
  **multiplicity carrier**, which stands independently — the epoch still delivers the secondary + a third
  multiplicity replication.

Interpreted **only if all gates pass** (§5). Report-all + per-facet + leave-one-facet-out. Classes never
pooled. Analyzer: `tools/padding_analyze.py` (emits "GATES FAILED — verdict NOT interpretable" on any fail).

**What LENGTH-CLEAN does and does NOT license (pressure-test MUST_FIX — claim scope).** Going
single→triple changes **three** things at once: fact-count, length, and achievement-template *repetition*
(triple's 3 near-identical lines). The padded arm reproduces the length but deliberately NOT the
repetition (its lines are varied non-achievements). The within-epoch decomposition is therefore:

    (triple − single) − (padded − single)  =  triple − padded
                                           =  fact-count + repetition − generic-content

a **bounded COMPOSITE, never re-labeled "fact-count"**. LENGTH-CLEAN rules out **raw preamble
length/trappings** as the masker of the multifact flat-T1; the fact-count/repetition split remains
**structurally unidentifiable** at the per-token channel — the cell that would identify it (3 achievements
at SHORT length) cannot exist, because 3 achievements *is* the added length. Consequently **MULTIPLICITY
remains the length-clean carrier of the framing verdict** (you cannot own ≥2 tokens unless ≥2 are
planted); this run **corroborates** the carrier and closes the raw-length loophole — it does not replace
the carrier. The secondary (fresh triple, same epoch) reports the composite with its own paired CI and the
carrier's third-epoch multiplicity. LENGTH-EFFECT in either direction re-opens the multifact §FLAGGED
cancellation reading and the composition is reported instead of any clean claim.

## 5. Gates (ALL wired)

1. **G1 recall control** ≤ 0.05, both arms.
2. **G2 replication:** fresh single-arm T1 on `REPRO_FACETS` (7f) vs the multifact anchor **0.182 ± 0.10**.
3. **G3′ padding-phrase echo:** fraction of padded-arm open-SP BEM **responses** containing any locked
   `PADDING_PHRASES` string (case-insensitive) ≤ **0.05**; echo examples printed for audit. The **single arm
   doubles as the false-positive floor** (must be ≤ 0.01 — organic occurrences would mean the phrases are not
   distinctive and the gate is void). *This is an ECHO gate, not an adoption gate — see §7.*
4. **G4 identical open-SP facet set** across arms.
5. **Integrity tripwires** (ported): 78 per model per arm (62 BEM + 16 recall); mech cell exactly the frozen 11.

## 6. Power (committed sim `padding/power_sim.py` — REAL 25-facet rates from the filler-epoch single arm)

| truth | verdict distribution |
|---|---|
| Δ = 0 (length-clean) | **LENGTH-CLEAN 0.83**, INCONCLUSIVE 0.17, effects 0.00 |
| Δ = +2M ≈ +0.13 (masking size) | **LENGTH-EFFECT(+) 0.81**, INCONCLUSIVE 0.19 |
| Δ = −2M ≈ −0.13 | **LENGTH-EFFECT(−) 0.71**, INCONCLUSIVE 0.29 |
| Δ = ±M (margin edge) | mostly INCONCLUSIVE (0.81/0.94), false-equivalence ≈ 0.10/0.05 |

No clean↔effect cross-misclassification at any simulated size. **Disclosed:** empirical false-equivalence at
the exact margin edge ≈ 0.10 vs the nominal 0.05 — small-cluster bootstrap under-coverage (the same §7(b)
limitation as the filler pre-reg); concretely, a true length effect of exactly half the masking magnitude
(≈0.066) would be stamped LENGTH-CLEAN ~10% of the time. Power is also mildly **asymmetric**: detection of a
suppressive effect at −2M (0.71) is weaker than of a boost at +2M (0.81) — floor effects near 0 — and the
suppressive direction is a genuine threat direction (it implies a compensating positive fact-count/repetition
effect in multifact); disclosed. The LOO sensitivity is reported alongside the primary. Under the null,
INCONCLUSIVE lands ~17% of the time — the §4 fallback (carrier stands, question stays open) is pre-committed
for that case.

## 7. Inherent limitations (disclosed)

- **(a) Paraphrase absorption is unmeasurable — but directionally CONSERVATIVE (red-team finding).**
  Tokenless padding makes contamination *invisible to the token instrument*, not impossible. G3′ catches
  verbatim/near-verbatim echo only. If models absorb the padding as generic self-description ("I keep my
  notes tidy"), that loads onto Δ and is — by the §1 estimand definition — part of what a longer real
  preamble does. Crucially, absorption cannot manufacture a **false LENGTH-CLEAN**: absorbed process-padding
  surfaces as first-person process talk, not as T1; if it leaves T1 unchanged the CLEAN verdict is correct,
  and if it displaced T1 (which the filler run's additive-absorption result makes unlikely) the verdict
  moves to LENGTH-EFFECT(−), which correctly forces the composition path. The unmeasurability costs
  precision, never direction. The verdict wording stays "length (+ non-citable process-discipline persona
  content)", never "length in the abstract" — and note the padding's shared process/review-discipline
  semantic is a mild directional prime, whose push (toward EFFECT, per the above) is also conservative.
- **(b) Small-cluster bootstrap under-coverage** (25 clusters): margin-edge false-equivalence ≈ 0.10 (§6).
- **(c) Repetition axis still unmatched — and structurally so:** triple's 3 near-identical lines vs padded's
  3 varied lines; byte-matching cannot match repetition, and no arm can (the identifying cell — 3
  achievements at short length — cannot exist). This is why §4 bounds the composite and keeps multiplicity
  as the carrier.
- **(d) No-interaction assumption:** the three arms give 3 of the 4 cells of a {short,long}×{1,3-fact}
  factorial; the missing cell is exactly the length×fact-count interaction term. Any decomposition-flavored
  reading of the §4 composite assumes that interaction ≈ 0; the composite CI itself needs no such
  assumption (it is a direct paired contrast), which is why the composite — not a derived "fact-count" — is
  what gets reported.

## 8. Ops

Generate all THREE arms fresh on Sparky in one run (16 models; single via `--multifact-n 1`, padded via
`--scaffold-padded`, triple via `--multifact-n 3`, each a fresh timestamped cache), launcher
`gen_sweep/cdms_padding_gen.sh` (GIRAFFE gate, mech-11 completeness abort, 3-attempt retry, bank-size
assert). Cross-machine preamble hashes verified byte-identical before launch (single + padded + triple —
the triple tie-order hazard is checked, not assumed). Judge all three in one session
(`multifact_judge.py … [--multifact-n 1|3 | --scaffold-padded] --sp-expansion-bank`; padded arm judges
**T1 only**; triple judges T1/T2/T3), cap $15/arm (expected ≈ $2 + $2 + $7). Analyze:
`python tools/padding_analyze.py gen_sweep/padding_single_JUDGE.jsonl gen_sweep/padding_padded_JUDGE.jsonl
gen_sweep/padding_triple_JUDGE.jsonl --arm mech --per-facet --sp-expansion-bank`. Distill replication cell:
same command with `--arm distill --allow-incomplete` (descriptive, non-decision). `PADDING_RESULTS.md`
carries the **running single-arm reproducibility ledger** (multifact 0.182 / filler-epoch 0.169 / this
epoch) and the multiplicity ledger (0.182 / 0.198 / this epoch). Commit all three JUDGE files + docs.

## 9. Locked (guarded by `tests/test_padding.py`)

- `PADDING_GISTS` (2 tokenless process-gists) + `PADDING_PHRASES` (the G3′ echo strings — substrings of the
  rendered exemplars, verified present in the preamble and absent from every probe text).
- `setup_bem_padded`: preamble 886B (±12B of triple), T1 first at byte 378. Test-guarded.
- Decision rule §4 (incl. the INCONCLUSIVE fallback + the bounded-composite claim scope) + margin M = p_s/3
  + all gates §5. Secondary composite is REPORTED as `triple − padded` with its own paired CI and is never
  re-labeled "fact-count". Reuses the locked `probes_sp_expansion` bank (sha-guarded by
  `tests/test_filler.py`), `MULTIFACT_TOKENS`, A′ panel.

## 10. Pressure-test record (rule 12 — completed 2026-07-07, before lock)

Two adversarial agents (statistical red-team + methodological legitimate-use); both converged on the same
central defect independently; final verdicts **LOCKABLE AFTER MUST_FIXES**, all applied:

- **MUST_FIX (method, both agents) — the composition claim overstated.** The draft's LENGTH-CLEAN verdict
  promoted the per-token decomposition to "fact-count ≈ 0", but single→triple varies fact-count AND
  achievement-template repetition together, and the identifying cell (3 achievements at short length)
  cannot exist. Re-scoped everywhere (§4, analyzer verdict strings): LENGTH-CLEAN rules out **raw length**
  only; the composite is reported as `triple − padded` with its own paired CI, labeled a bounded composite,
  never "fact-count"; **multiplicity stays the carrier** — this run corroborates, does not replace.
- **MUST_FIX (wording) — "preamble length alone"** in the locked verdict string contradicted the §1/§7(a)
  estimand. Fixed to "length + non-citable process-discipline persona content".
- **SHOULD_FIX (stat) — cross-epoch composition:** the draft composed against the filler-epoch triple. A
  **fresh TRIPLE arm** was added to this epoch (3 arms total) — within-epoch composite CI + the carrier's
  third multiplicity epoch. (Red-team note: triple−padded is the *better* contrast anyway — matched length
  AND matched gist-count.)
- **SHOULD_FIX applied (disclosures):** no-interaction/missing-cell disclosure (§7d); INCONCLUSIVE fallback
  pre-committed (§4 — carrier stands, question stays open); margin M=p_s/3 registered as DELIBERATE
  DEVIATION I6 vs the repo SESOI (with the ~0.10 margin-edge false-equivalence cost); power asymmetry
  disclosed (suppress 0.71 < boost 0.81, §6); paraphrase-absorption directionality argued conservative
  (cannot manufacture a false LENGTH-CLEAN — §7a); padding's process-discipline prime named (§1/§7a);
  bracketing framing (padded = floor, filler = realistic case, §1); reproducibility ledgers specified (§8).
- **SHOULD_FIX applied (ops/tests):** launcher machine-asserts T1@378 + length-match on the generation host
  (tie-order flip defense — render order is insertion-order, ties unbroken by a secondary key); tests added
  for INCONCLUSIVE fallback, G1/G2 gate-fail interpretability, G3′ floor-void, G4/integrity hard-fail, and
  the secondary composite block (12 total); echo_scan file-handle leak fixed.
- **VERIFIED-SOUND (red-team, attacks held):** threat-proportional margin not gameable (G2 bounds M to
  ≈[0.027,0.094]); power sim propagates the M↔Δ correlation; reconstruction flag-mismatch fails loud (0
  rows → hard-fail); arm-label integrity; echo-gate denominators (ABSENT rows carry text; dedup correct);
  phrases in-preamble and absent from all probe texts; decision-rule boundary logic faithful to §4; T1
  byte-position/length invariants confirmed by direct render on this host.
