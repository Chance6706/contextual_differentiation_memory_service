# Differentiation-over-time — pre-registration (CORE THESIS)

**Status:** DRAFT (pre-lock). Pipeline: draft → rule-12 double pressure-test (design + code) → fix →
LOCK → run (real embedder, long duration, $0 local) → red-team the results → analyze → report → PR.

**Costs (plain dollars, upfront):** $0 API — this is a fully local mechanical experiment (fastembed
embedder + CDMS consolidation, no LLM panel). Compute: local CPU, expected minutes-to-tens-of-minutes
per full sweep (many cycles × psyches × policies × seeds); "let it take as long as it takes" (Josh). No
Sparky, no OpenRouter. Agents: 2 pressure-test + 2 results-reviewers (surfaced, background).

---

## 0. Why this exists (what the prior attempt got wrong)

The first salience-vs-random control (`differentiation.py`, single-pass + `measure_selfshape`) measured a
**near-null for four compounding reasons**, all verified:
1. **Hash embedder** — clustering ran on bag-of-token-hashes, so semantically-related-but-differently-worded
   experiences never clustered; identity was really the entity-name vocabulary. (hash cos 0.224 vs fastembed
   0.765 for "fixed the login flow" ↔ "resolved the sign-in bug".)
2. **Homogeneous fixture** — every experience was "improved/debugged a module", so under the *real* embedder
   the whole life correctly collapses to ONE gist (`frequently_works_on / module improved`, support 13).
3. **Infant duration** — 8 cycles, everything reinforced each cycle → `decay=0` always, `evict=0–4` of ~120.
   No forgetting happened, so forgetting could not shape anything.
4. **Salience conflated with frequency** — salient entities recurred 24× so both policies kept them; only
   incidental noise flipped.

This prereg fixes all four and reframes the observable as a **trajectory**, per Josh: *show how it
differentiates over time*, not a single endpoint.

## 1. Question + hypotheses

**Core question:** As two agents accumulate *different* experience, do their identities differentiate
(gist-trait overlap decreases) over time — and is **forgetting BY SALIENCE** what drives it, versus
forgetting at random or not forgetting at all?

**Identity metric (unchanged from the individuation_experiment):** a psyche's identity = the set of
`(relation, object)` gist tuples. Cross-psyche similarity = **Jaccard overlap** of those sets. Lower =
more differentiated.

- **H1 (differentiation over time):** under salience forgetting, cross-archetype overlap **DECREASES** with
  accumulated experience (turns). Falsifier: flat trajectory → no differentiation-over-time.
- **H2 (salience drives it):** at late experience, `overlap_salience < overlap_random ≤ overlap_none`, with
  the salience curve **peeling away** from the others. Falsifier: `salience ≈ random` → salience adds
  nothing over forgetting-anything (the publishable negative). `salience ≈ none` → forgetting adds nothing.
- **H3 (mechanism, not artifact) — the same-archetype NULL:** two psyches from the *identical* experience
  distribution (seed only differs) must stay **HIGH overlap** and NOT differentiate under any policy.
  Falsifier: if same-archetype psyches diverge, the "differentiation" is the forgetting process
  manufacturing divergence from noise, not tracking experiential difference — which would **invalidate H1/H2**.

## 2. Design factors

| factor | levels |
|---|---|
| forgetting policy (ablation) | `salience` (cdms-full) · `random` (rate-matched, seeded) · `none` (retention_floor=0) |
| psyche pair | **cross-archetype** (A vs B) · **same-archetype null** (A vs A′, seed differs) |
| seed | ≥ 8 seeded realizations per (policy, pair) for CIs |
| experience length | snapshot after **every cycle** → the trajectory x-axis (cumulative turns) |

Real embedder **fastembed** (fingerprint recorded); NOT hash. `CDMS_EVAL_MODE=1` (random-discard is
eval-gated). All stores fresh + CDMS_HOME-isolated per (policy, pair, seed).

## 3. Fixture — salience decoupled from frequency (the load-bearing fix)

Salience is set **explicitly** via `TurnEvent.valence_hint ∈ [-1,1]`; `S0 ∝ w_affect·|affect| + w_surprise·
novelty + …`, and novelty (rarity) independently raises S0, so rare-distinctive events are doubly salient.

- **Shared substrate (BOTH archetypes):** routine objects `{logs, docs, config, deps, lint, formatting}`,
  `|valence_hint| ≈ 0.15` (mild), **HIGH frequency** (many per cycle). Low salience → pruned FIRST by
  salience, kept by none, pruned proportionally by random.
- **Distinctive experience (per archetype):**
  - A ("backend/security"): `{auth, crypto, database, session, migration}` — strong outcomes (triumphs
    `hint≈+0.9`, crises `hint≈−0.9`), **LOW frequency** (rare per cycle).
  - B ("frontend/product"): `{viewport, animation, checkout, onboarding, telemetry}` — same valence
    structure, low frequency.
  High salience + high novelty → survive salience-eviction; dropped by random (they're rare); kept by none.

**Why the predicted ordering follows:** salience prunes the shared low-salience substrate and keeps each
archetype's distinctive high-salience traits → identities defined by what's UNIQUE → low overlap. `none`
keeps the shared substrate too → high overlap. `random` prunes shared and distinctive proportionally → ratio
≈ preserved → overlap between the two, nearer `none`.

## 4. Precondition checks (fail LOUD before trusting any result)

The prior run's silent inertness must be impossible here. Before analysis, the rig MUST assert and REPORT:
- **Forgetting actually bit:** cumulative `episodes_evicted / episodes_ingested ≥ 0.20` under `salience`
  (else eviction is a rounding error → ablation inert → HALT, don't emit a null).
- **Gists actually formed and are non-trivial:** ≥ K distinct traits per psyche at the end (not the
  collapse-to-1 failure); trait count trajectory reported.
- **Policies actually differed:** `salience` and `none` evicted materially different counts (else the
  retention_floor override didn't take).
- **Embedder is fastembed** (assert backend, record fingerprint) — never silently hash.
- **cdms provenance** (worktree src, recorded commit) via the M-A guard.

## 5. Primary + secondary endpoints

- **PRIMARY:** overlap(t) trajectory per policy for the cross-archetype pair, mean ± bootstrap CI over
  seeds; and `Δ(t) = overlap_salience(t) − overlap_random(t)` with CI (H2). Report the **onset** (first t
  where salience CI separates from random) and the endpoint ordering.
- **SECONDARY:** trait-count trajectory per policy; eviction/decay trajectory; the same-archetype null
  overlap(t) (H3, must stay high); per-tier breakdown (how much of the divergence is substrate-pruning vs
  distinctive-accrual).
- **Report the x-axis in cumulative TURNS** (episodes ingested), mapped to cycles.

## 6. Analysis

- Snapshot trait sets after each cycle (one long run yields the whole curve — no re-running at each length).
- Cross-archetype overlap(t) = Jaccard(A_traits(t), B_traits(t)); average over seed-matched pairs.
- Cluster-bootstrap CIs over SEEDS (not cycles — cycles within a run are dependent).
- H2 test: sign + CI of Δ(t) at the final cycle and its trajectory; H1: monotone-decrease test on
  overlap_salience(t); H3: same-archetype overlap stays above a high floor (pre-registered, e.g. ≥ 0.6).
- **Verdicts:** DIFFERENTIATES (H1 holds) / SALIENCE-DRIVEN (H2 holds) / NULL (flat or salience≈random) /
  INVALID (H3 fails or preconditions fail). An honest NULL is a valid, publishable outcome.

## 7. Deliberate deviations / disclosures
- Synthetic fixture (not real logs) — differentiation of CONSTRUCTED distinct lives; the real-data 0.00
  overlap (task #9) is the complementary ecological check. Disclosed; not a real-world identity claim.
- `valence_hint` used to set salience directly — a control lever, disclosed; the lexical path is exercised
  separately by other axes.
- Supersedes `differentiation.py` `measure_selfshape` (kept, but marked INVALID-as-thesis-test with the
  four reasons above).

## Build-iteration findings (pre-lock; the rig-tuning caught these — record so they aren't re-learned)

Smoke-testing the rig (fastembed, 1 seed) surfaced four mechanistic facts that any valid run must respect:

1. **The `(relation, object)` Jaccard measured LABEL NOISE, not identity.** gist.object is a noisy top-2-
   term phrase ("auth cache", "crypto compile") that reshuffles cycle-to-cycle (consolidate warns of it),
   so the same-distribution NULL collapsed to ~0. FIX: anchor identity on the controlled entity vocabulary
   — `(relation, canonical_entity)` — a disclosed measurement choice. Null then held at 1.000 under `none`.
2. **Identity is NOISE below a stability threshold (the "infant" regime).** At 7 entities × 25 cycles, per-
   entity evidence was too thin: two identical "careful" psyches produced different relations
   (handles_well AND has_trouble_with AND frequently_works_on). FIX: fewer entities (4) + more turns/cycle
   (20) + cleaner disposition (p_strong 0.90) so per-entity relations converge.
3. **Forgetting is DEDUP-dominated, not eviction-dominated.** 800 ingested → 22 resident, but salience-
   EVICTION was only 1–4%; the collapse is consolidation DEDUP folding near-duplicate templated turns. The
   conserved salience budget (K=1000) then concentrates onto survivors (base_salience up to ~498, median
   accessibility 0.18 ≫ floor 0.10) so distinct-memory eviction barely fires. CONSEQUENCE: to give
   salience-forgetting a fair test, episodes must be genuinely VARIED (high novelty) so a large DISTINCT
   population forms and low-salience items age below the floor instead of being deduped. A repetitive
   fixture measures dedup+conservation, not salience-eviction. (This is itself a real characterization of
   how CDMS forgets — valuable for the yardstick.)
4. **Salience currently DEGRADES the null (noise injection).** Under salience the same-distribution null
   fell to 0.429 (vs `none` 1.000): sparse eviction on an unstable population injects seed-dependent
   divergence. MUST re-check once forgetting operates on a varied population — if it persists, that is a
   real finding (salience adds noise, not signal) and a strike against "salience differentiates."

Open param fork for the maintainer: test CDMS **as-shipped** (conservation on → forgetting weak, likely
"salience adds little beyond distinct input") vs a config that forces meaningful eviction (varied fixture,
possibly tuned retention/budget) to see whether salience CAN differentiate when forgetting actually bites.
Both are legitimate; the first tests the product, the second tests the mechanism's ceiling.

## Design LOCKED (with Josh) + first positive signal (1 seed — needs full-cube replication)

THE THESIS (sharpened): Identity = f(History) means the DISCARD POLICY *is* the disposition — the SAME
history through DIFFERENT dispositions yields DIFFERENT identities, because each finds different things
salient. A disposition = a GOAL SET; on-topic events get high `goal_hint` (survive), off-topic low (evict
first). Differentiation from IDENTICAL input.

**The cube:** identity[disposition ∈ {A, B(~A similar), C(≠A different), U(dispositionless)} × condition ∈
{none, uniform, random, disposition-salience} × goal_gate_floor ∈ {0.25 as-shipped, 0.0 ceiling} × seed].
U's disposition-salience column ≡ uniform (no goals). Read TWO ways (Josh):
  * DRIFT-AGAINST-SELF (fix disposition+history, vary CONDITION): does disposition-salience move the self
    from its `none` baseline, differently than uniform/random?
  * CROSS-DISPOSITION (fix condition, vary DISPOSITION): similar(A·B) vs different(A·C) vs null(A·U). Only
    disposition-salience should recover similar > different; none/uniform collapse it.
Two metrics: RAW trait set (all gists) AND SURFACED (top_gist(12) = what SessionStart injects) — the
individuation lives in the WEIGHTING, so surfaced is the faithful lens.

**Key mechanism fact (grounded):** `gate = goal_gate_floor + (1−goal_gate_floor)·goal_hint`. At the shipped
`goal_gate_floor=0.25`, off-topic memory keeps a 25% floor — a disposition is a **bounded ~3× salience
TILT, not an erasing filter** (deliberate: "avoid zeroing-out memories when goal is merely absent"). So
disposition does NOT concentrate the RAW trait set; it re-weights what SURFACES.

**First signal (seed 0, 100 cycles, fastembed — REPLICATE before trusting):** SURFACED cross-disposition
separation (similar − different): `none`=+0.00 (COLLAPSED, all dispositions identical) → `disposition-
salience` as-shipped=+0.24 → ceiling(floor 0)=+0.38 (on-topic concentration 0.50→0.60→0.70). So disposition-
driven salience individuates in a STRUCTURED way (similar>different) that `none` fully collapses; as-shipped
already shows it; the floor caps but does not kill it. This is a POSITIVE thesis signal, not the "salience
adds little" null. Raw-set separation is weaker/noisier (+0.17 as-shipped, +0.08 ceiling) — expected, since
the floor preserves off-topic traits; surfaced is the correct readout. Pending: full cube + N seeds + CIs +
shuffle-null significance + drift-against-self + uniform/random/U + the same-disposition null (must stay HIGH).

## Pressure-test record (rule-12) — PENDING (2 agents, pre-LOCK on the full cube runner + analysis)

## Results red-team — PENDING (2 agents, post-run)
