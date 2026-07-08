# Tokenless padding control — results

**Pre-registration:** [`PADDING_PREREG.md`](PADDING_PREREG.md) (LOCKED 2026-07-07, commit `5546b2f`,
rule-12 double pressure-tested at design time). **Generation:** Sparky/GX10, 2026-07-07, **three fresh
same-epoch caches** (`padding_single_20260706_230950`, `padding_padded_20260707_013353`,
`padding_triple_20260707_040358`), 16 models × 3 arms × 78, temp=0, zero retries; launcher machine-asserted
T1@378 + length-match on the host; preamble hashes verified byte-identical cross-machine pre-launch.
**Judge:** locked A′ 5-vendor panel, one session, **$12.20** (single $2.20 / padded $2.31 / triple $7.70).
**Analysis:** `tools/padding_analyze.py … --arm mech --per-facet --sp-expansion-bank` (deterministic,
seed 0; primary verdict seed-robust across {0,1,7,42,123,999}). **Results-stage pressure test (new, this
run):** a verdict-blind data audit ran BEFORE analysis (completeness 78/78 all arms; zero analyzer-INVALID;
5 healthy vendors; ABSENT fractions match the filler epoch; no duplicates), and TWO adversarial reviewers
(statistical + claims-scope) audited the data→claims chain BEFORE this document was written; all their
MUST_FIX amendments are folded below.

## Headline — GATE 3′ FAILED: the verdict is again WITHHELD; even tokenless platitudes re-enter the first-person channel

The padding-phrase **echo gate failed** on the mech-11 decision cell: **0.109** of open-SP responses
(60/550, spread over 10 of 11 models) contain a locked padding phrase verbatim, vs the ≤0.05 threshold —
with the single-arm false-positive floor at exactly **0.000** (the phrases are distinctive; the gate is
valid, not void). Per the lock, the TOST verdict is **not issued** and the per-token length question is
not stamped.

Of the 60 echoes, 29 are second/third-person recitation and 20 non-attributive — but **11 (2.0% of
responses) are first-person paraphrase absorption**:

> *"**Note-taking and Review**: **I maintain brief notes** in this workspace, which are **reviewed on a
> periodic cadence**."* (granite-3.0-8b, sp-N4)
> *"— **I follow conventions** and keep notes briefly, reviewing them on a periodic cadence."*
> (granite-3.0-8b, sp-N7)

The padding had **no coined token and no citable artifact** — and a measurable slice of models still wove
it into self-description.

## Gates (mech-11, decision cell)

| gate | value | status |
|---|---|---|
| G1 recall control | single 0.000 / padded 0.006 / triple 0.000 | **PASS** — Bem firewall holds, all arms |
| G2 replication (fresh single T1, `REPRO_FACETS`) | 0.182 vs anchor 0.182 (reproduces to 3 decimals; Δ=0.0002, computed fresh) | **PASS** |
| G3′ padding-phrase echo (≤0.05) | **0.109** (floor 0.000 — gate valid) | **FAIL — padding echoed** |
| G4 identical open-SP facet sets | 25/25/25 | **PASS** |

`padding_analyze.py` emits **"GATES FAILED — verdict NOT interpretable"** exactly as pre-committed.

## MEASURED (pre-specified measurements; reported as found)

1. **Echo of tokenless padding into self-presentation:** 0.109 of open-SP responses (G3′, a verbatim
   raw-text scan — **not** A′ ownership; see the instrument note below). First-person paraphrase subset:
   **11/550 ≈ 0.020** — that subset, not 0.109, is the figure loosely comparable to the A′ adoption rates
   of prior runs.
2. **Co-adoption, not displacement:** responses that echo the padding have **higher** T1 adoption (0.250)
   than non-echo responses (0.202). Absorption is whole-block-correlated — a model that soaks up one part
   of the persona block soaks up the rest — replicating the filler run's additive (never competitive)
   pattern at the echo level.
3. **Treatment-induced response lengthening (mediator, disclosed):** padded-arm open-SP answers run ~12%
   longer than single-arm (mean 655 vs 584 chars). The arms are NOT matched on response length — the
   longer preamble makes answers longer — yet T1 stayed flat, which is the conservative direction.
4. **Distill cell (pre-registered descriptive, 5 models):** all gates PASS there (echo 0.024); verdict
   **INCONCLUSIVE** with a **nonzero negative Δ = −0.052 [−0.096, −0.008]** — see FLAGGED.

## FLAGGED OBSERVATIONS (descriptive only — the decision cell is gate-failed; nothing here is stamped)

- **The TOST internals land length-clean, and carry zero confirmatory weight.** Δ = T1(padded)−T1(single)
  = +0.005, 95% CI [−0.038, +0.047], LB95 −0.031 / UB95 +0.040, entirely inside ±M = ±0.067; seed-robust;
  LOO stable (+0.00…+0.02). On a gate-failed control this is recorded as shape only. **"Length is clean"
  is NOT asserted — see NOT assertable.**
- **Within-epoch composite** (triple−padded = fact-count + repetition − generic-content, a bounded
  composite, never re-labeled "fact-count") = **−0.011** [−0.049, +0.027]; in-epoch triple−single =
  −0.005 [−0.038, +0.027]. No fact-count/repetition signal either, descriptively.
- **Distill discordance (flagged per the note-flagged-observations discipline, n=5, open):** the distill
  Δ is **nonzero-negative** (−0.052, CI excludes 0) — the padded arm dips below both single and triple
  (composite +0.072 [+0.024, +0.120]) — the §7(a)-flagged suppressive direction, and it does **not**
  corroborate cleanliness. Bounds: 5 models, pre-registered descriptive/non-decision, INCONCLUSIVE under
  its own rule (CI straddles −M = −0.041), Δ small. The mech cell (11 models) shows **no** dip (+0.005);
  the two cells **disagree in sign**, consistent with a small/noisy rather than consistent length effect.
  Offsetting distill internals: composite positive and multiplicity LB > 0, both consistent with framing.
- **Exploratory, quarantined — echo-excluded TOST:** dropping the 60 echo responses moves Δ from +0.005
  to −0.003. This is **selection on a post-treatment, outcome-correlated variable** (echo responses have
  higher T1) and is therefore biased; it is reported ONLY to show the +0.005 is not driven by the echoing
  responses. It does **not** and cannot lift the withheld verdict.

## Reproducibility ledgers (pre-reg §8 — a MEASURED strength of the series)

Same-estimand, same-facet-basis, three independent generation+judge epochs:

| quantity (mech-11) | multifact epoch | filler epoch | padding epoch |
|---|---|---|---|
| fresh single T1 (`REPRO_FACETS`, 7f) | 0.182 | 0.169 | **0.182** |
| fresh triple multiplicity (7f basis) | 0.182 | 0.182 | **0.182** |
| fresh triple multiplicity (25f basis) | — (no 25f bank yet) | 0.198 | 0.196 |
| multiplicity one-sided LB95 > 0 | 0.091 (7f) | yes | 0.142 (25f) |

On the common 7-facet basis the multiplicity carrier replicates **identically (0.182 / 0.182 / 0.182)**
across three epochs — the apparent 0.182→0.198→0.196 "drift" in earlier drafts was a facet-basis artifact
(pressure-test MUST_FIX: ledgers are apples-to-apples or annotated). The generate→judge→score path is
stable across days, and the carrier keeps confirming.

## NOT assertable

- **"Length is clean" — not asserted.** The decision cell is gate-failed; its clean-looking TOST internals
  carry no confirmatory weight (gate-fail is not evidence, in either direction). The per-token in-block
  length question ends this run **formally OPEN**.
- **"Platitudes are adopted like achievements" — not asserted.** 0.109 is verbatim echo (grep); the
  ownership-comparable first-person subset is ≈0.020, an order below achievement adoption (~0.2, A′).
  The instruments differ; the verbs stay distinct (owned vs echoed).
- **Any distill-cell direction** — nonzero-negative but INCONCLUSIVE, 5 models, descriptive.

## Series synthesis (discussion-level, instrument-labeled — not one measured quantity)

Across three in-block length-control designs, every content type placed in the persona block has re-entered
the first-person self-presentation channel: achievement gists **A′-adopted** ~0.2 (multifact/clean-strata,
gate-passing); stative coined-token dependency facts **A′-adopted** ~0.1 (filler, G3); tokenless process
platitudes **echoed into first-person paraphrase** in ~2% of responses (padding, G3′ — a grep-level echo
signal, not adoption-grade). We have not been able to construct in-block content that stays out of the
first-person channel. Precision note: **multifact CONFIRMED its verdict (gate-passing, via the multiplicity
carrier); filler and padding are gate-failed control attempts** whose internals are consistent-with but
cannot re-confirm it — and the padding distill cell does not even descriptively land on framing.

## Architecture significance

Filler established that ingest hygiene cannot triage by content **type** (achievements ~0.2, stative deps
~0.1, both A′-owned). Padding sharpens it one step: even content with **no coined token and no citable
artifact** re-enters the first-person channel (~2% first-person paraphrase). The hazard is the
persona-block **attribution frame**, not the citability of what is rendered into it. Actionable for the
CDMS-D world-fence: hygiene cannot strip citable artifacts and treat the residue as inert — any content
rendered into a P-attributed block is attribution-risk, and the block must be treated **wholesale** as
non-assistant-attributable. Bounded: the contentless-platitude leak is low-rate and echo-grade — a
directional sharpening, not a magnitude comparable to achievement adoption. The load-bearing boundary is
unchanged: the recall control stayed ≈0 in all three arms (G1) — this is a rendering/list-mode statement,
not a recall-channel one.

## RECOMMENDATION — close the per-token in-block length thread as BOUNDED (Josh's call)

> **Outcome (2026-07-08):** Josh chose depth over closure — a 4th design ran as the **attribution-frame
> decomposition** (`FRAME_RESULTS.md`): the subject slot is causal but weak (~23% reduction), third-party
> facts still enter the first-person channel at 0.085 (CROSS-ENTITY-LEAK), and the in-block identifying
> cell self-destructed a fourth time (GT-fail via cross-entity adoption) — note (i)'s estimand concern was
> handled by testing out-of-block length as a *separate, pre-registered* SECONDARY rather than as the
> multifact treatment (WITHHELD on mech, GO echo 0.156; knife-edge LENGTH-CLEAN on distill only). The
> per-token **in-block** length question remains formally OPEN and structurally unidentifiable, as argued
> below; the multiplicity carrier re-confirmed a 4th epoch (0.182, 7f mech).

The justification is **structural, not inductive**: the identifying cell — added persona-block length with
NO added P-attributable content — **cannot exist**, because the persona block IS the attribution surface
(added length is added attributable content). The three designs are the empirical demonstration of that
wall (filler: content re-entered via A′ adoption; padding: via first-person echo), not three tries a fourth
might beat. The parent question — framing-pull vs availability — is already answered **length-clean by the
multiplicity carrier** (≥2-token ownership cannot be produced by single-fact availability OR by length;
three epochs 0.182/0.182/0.182 on the common basis, LB95 > 0 each), so closure costs the framing verdict
nothing. Three candidate fourth designs, declined with reasons: **(i)** padding outside the persona block —
changes the estimand (un-attributed length is not the multifact treatment); **(ii)** single-word generic
padding — weakens the echo gate without solving paraphrase-unmeasurability; **(iii)** a relaxed G3′
threshold — would license a "clean" verdict while first-person paraphrase adoption is demonstrably present
(laundering a real contamination). If a falsifiable length/identity question remains worth resources, it is
the **controlled-FT frontier arm** already on the arc, not a fourth in-block length control. What is
asserted: "length is structurally unidentifiable at the per-token in-block channel, and the parent verdict
does not depend on it." What is NOT asserted: "length is clean."

## Data + reproduction

- `gen_sweep/padding_single_JUDGE.jsonl`, `gen_sweep/padding_padded_JUDGE.jsonl`,
  `gen_sweep/padding_triple_JUDGE.jsonl` (committed).
- `python tools/padding_analyze.py gen_sweep/padding_single_JUDGE.jsonl gen_sweep/padding_padded_JUDGE.jsonl
  gen_sweep/padding_triple_JUDGE.jsonl --arm mech --per-facet --sp-expansion-bank` (deterministic, seed 0).
  Distill: `--arm distill --allow-incomplete`.
- Scaffold `setup_bem_padded` + `PADDING_GISTS`/`PADDING_PHRASES` (locked, `tests/test_padding.py`);
  expansion bank `tools/probes_sp_expansion.py`; power sim `padding/power_sim.py`. Caches off-repo (Sparky).
- Terminology note: "zero INVALID" refers to the analyzer's surfacing-row definition; rows with
  `panel_label=INVALID` and empty votes (15/24/82 per arm) are non-surfacing and score 0, balanced across
  arms (2.7% vs 3.5% on the decision subset).

## Pressure-test outcome vs prediction

The §7(a) conservativeness argument was put to the test and **held — via a different mechanism than it
stated**. §7(a) reasoned absorption would displace T1 (→ EFFECT(−)); the data instead show **co-adoption**
(echo responses have *higher* T1, 0.250 vs 0.202) — which pushes Δ *up*, still the conservative direction:
echo cannot manufacture a false LENGTH-CLEAN. And the wired-gate discipline paid off a **second time**: the
mech Δ (+0.005) alone would have stamped LENGTH-CLEAN on a contaminated control — it was G3′ (0.109, floor
0.000) that caught the echo and withheld the verdict, exactly as the filler run's G3 did for adoption. The
distill cell's nonzero-negative Δ is weakly consistent with §7(a)'s original displacement direction —
underpowered, descriptive, unstamped. Results-stage discipline (this run's addition): the verdict-blind
audit caught nothing (clean pipeline), and the two-reviewer pass caught a facet-basis mixing in the
multiplicity ledger and a 4×-understated response-length drift before either number entered this document.
