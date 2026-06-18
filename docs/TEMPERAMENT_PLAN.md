# Temperament Layer (§8) — Implementation Plan

> Status: 📐 **PLAN** (proposed, not built). This is the implementation plan for the
> genotype/temperament layer specified in [`DESIGN.md` §8](DESIGN.md) and the deferred
> "degenerative-orbit" drift log (§8.7, §10.3). It was produced with the project's
> posit → break → build → break → fix discipline (CLAUDE.md), and — per the standing
> instruction that *a facsimile is by nature representative* — every machine decision is
> checked against the science of the thing it represents (a drifting human temperament),
> not just against engineering convenience. Where the represented science is itself
> contested, the conflict is flagged rather than smoothed over (CLAUDE.md §8).

## 0. The thesis of this plan, in one paragraph

CDMS already realizes **Identity = f(History)** at the phenotype layer (L2 gist traits that
flip on sustained valence and decay on an activity clock — ✅ built). The temperament layer
adds the **middle rung** of the same law: a small vector of disposition "dials"
`(seed, current, bounds)` that drift *slowly*, *directionally*, and *bounded*, driven by the
**outcomes of how the disposition expressed itself** — second-order learning. The deep result
of the research below is that the **machine failure modes and the human pathologies are the
same phenomena**, so the guards are not arbitrary: a self-model that drifts from a log of its
own experience fails in exactly the ways a human self fails (foreclosure, identity diffusion,
borderline thrash, rumination, echo-chamber ratchet, learned helplessness), and the
protective factors are the same too (earned commitment, disconfirmation, source-deduplication,
slow decorrelated change). One invariant dominates all of them and is independently entailed
by both the engineering analysis and the psychology: **the log must never be an input to
itself.**

---

## 1. Represented-side foundations (what faithfulness requires)

Each subsection states the established science, the genuine conflict in it, and the design
consequence. Citations are author/year; URLs collected in §7.

### 1.1 Temperament vs character → a plasticity *gradient*, not a frozen/free dichotomy
- **Science.** Cloninger's psychobiological model (Cloninger, Svrakic & Przybeck 1993) cleanly
  separates **temperament** (novelty-seeking/dopamine, harm-avoidance/serotonin,
  reward-dependence/norepinephrine, persistence — heritable, early, "preconceptual,"
  stable) from **character** (self-directedness, cooperativeness, self-transcendence — matures
  in adulthood via self-concept learning). Rothbart similarly splits reactivity (substrate)
  from effortful control (develops); Thomas & Chess's "goodness of fit"; Kagan's reactivity.
- **Conflict (must honor).** Gillespie et al. (2003) found character is **about as heritable**
  as temperament (27–44% vs 30–41%) and substantially **genetically independent** — i.e.
  character is *not* simply "temperament + environment," and the clean substrate→developed
  stack is contested. TCI temperament dimensions also overlap heavily with the Big Five
  (De Fruyt 2000), and Kagan's inhibition is only *partially* stable.
- **Design consequence.** Do **not** hard-code "temperament dials = frozen, character dials =
  drift." Assign each of the eight §8.1 dials a **per-dial plasticity coefficient**
  `(drift_rate, bound_width)` on a *gradient*: substrate-like dials (e.g. `emotional_gain`,
  `impact_sensitivity` ≈ reactivity/harm-avoidance) get near-zero drift and tight bounds;
  character-like dials (e.g. `deference↔independence` ≈ self-directedness, `exploration_radius`)
  get larger (still small) drift and wider bounds. The dichotomy is a *prior on the gradient*,
  not a wall.
- **Failure mode this guards.** Treating any dial as perfectly frozen reproduces **foreclosure**
  (§1.6 below: a self that can never revise); treating all as freely plastic reproduces
  **diffusion/thrash**. The gradient is the faithful middle.

### 1.2 Change is *directional*, not a random walk → a maturity prior on the update rule
- **Science.** The **maturity principle** (Roberts, Walton & Viechtbauer 2006, 92-sample
  meta-analysis): with age people rise on conscientiousness, emotional stability, social
  dominance, (later) agreeableness — a population-wide *direction*. Driven by the
  **cumulative-continuity**, **corresponsive**, and **social-investment** principles
  (Roberts, Wood & Caspi 2008; Roberts, Caspi & Moffitt 2003): traits steer people into
  environments that reinforce those traits, and shared adult roles pull everyone the same way.
- **Conflict.** Costa & McCrae's "set like plaster after 30" (Terracciano et al. 2006) vs
  Roberts' "persistent change" — but the conflict is partly a *metric* confusion (rank-order
  stability is high after 30; mean-level change continues). Consensus (Srivastava 2003;
  Roberts & Mroczek 2008) leans to "real but gradual lifelong change."
- **Design consequence.** The update rule carries a **directional (Bayesian) prior**:
  movement "with the maturity grain" needs less accumulated evidence than movement against it.
  Concretely, the evidence threshold `θ` is asymmetric per dial-direction.
- **Failure mode this guards.** Undirected drift = **identity diffusion** (Marcia). The maturity
  prior makes "drift with no consistent direction over a long window" a *detectable* pathology
  (low net/gross movement ratio), not the default.

### 1.3 Change is slow and history-integrated → STARTS channels + OU mean-reversion + activity clock
- **Science.** Rank-order stability rises ~.31 (childhood) → ~.74 (age 50–70) and is never 1.0
  (Roberts & DelVecchio 2000). Rate is **~0.1 SD per decade**, compounding to ~0.5–1.0 SD over
  a lifespan for the most-changing domains (Roberts & Mroczek 2008). Formally: the **STARTS**
  model (Kenny & Zautra 1995) decomposes repeated measures into a **stable trait** + a
  **slow autoregressive (AR(1)) drift** + **discardable state/error**; **latent state-trait
  theory** (Steyer 1999) splits trait from occasion; the continuous-time analog is the
  **Ornstein–Uhlenbeck** mean-reverting process (attractor + slow reversion rate) — with a
  *direct empirical precedent*, the **PersDyn / BHOUM** model (Sosnowska et al. 2019) which fits
  exactly an OU process `dΘ = β(μ − Θ)dt + ξ` to personality states (`μ` = baseline/home-base,
  `β` = attractor strength, `ξ` = noise; the authors flag that the *absolute* `β` is meaningless
  — it depends on sampling interval and scale — so we calibrate it to the activity clock, not
  wall-time). And traits
  are the **mean of a density distribution of states** (Fleeson 2001) — aggregate over many
  occasions, not single events. Durable change is **months-to-years**; sub-day swings are
  *states*.
- **Design consequence (the core math).** Model each dial as a **three-channel** quantity:
  `seed` (fixed set-point), `current` (the slow AR/OU drift channel — the *only* thing that
  accumulates), and the raw episodic valence stream (discardable state/noise). Update with an
  **OU/AR(1) step**: `current ← current + α·(evidence_mean − current) + β·maturity_prior`,
  where `evidence_mean` is the mean of a *window* of outcomes (Fleeson aggregation, built-in
  hysteresis), `α` is tiny (calibrated so per-cycle Δ matches ~0.1 SD / "developmental decade"
  measured in **consolidation cycles**, never wall-clock), and reversion toward `seed` enforces
  bounded change. This anchors §8.7's open Δ/ε/θ parameters in measured human rates rather than
  guesswork.
- **Failure mode this guards.** State-driven (per-event) updates reproduce **thrash** (§1.7).
  Wall-clock anything reintroduces **absence-loss** (the §5.3 invariant; §8.7 hazard). Slow
  AR + windowed aggregation is the faithful anti-thrash.

### 1.4 Set points exist but are *not* immutable → bounds + the Growth exception are both faithful
- **Science.** Hedonic-adaptation/set-point work (Brickman & Campbell 1971; Diener, Lucas &
  Scollon 2006's "five revisions") establishes baselines are real and heritable (~50%, Lykken
  & Tellegen 1996) **but shiftable**: unemployment (Lucas et al. 2004) and disability (Lucas
  2007) durably move the baseline; a minority never return. Headey (2010) argues set-point
  theory needs *revising, not discarding* — the mainstream view.
- **Design consequence.** `bounds` (the set-point pull) are justified, **and** so is §8.4's
  **"Growth" archetype exception** (one axis opened to a wide directional band): the science
  says sustained major change *can* durably move a baseline, so an opt-in, visible,
  one-directional band is faithful — not a hack. Bound-*widening* is itself a logged, proposed
  event (guards §8.7 N4).
- **Failure mode this guards.** Immovable bounds = **rigidity/foreclosure**; no bounds =
  **runaway drift**. Shiftable-but-only-by-explicit-proposal is the faithful middle.

### 1.5 Persistence = *continuity*, not *connectedness* → the right invariant for "still the same self"
- **Science.** Parfit (*Reasons and Persons* 1984): **psychological connectedness** = direct
  connections (memory, intentions, character), *degreed and non-transitive*;
  **continuity** = *overlapping chains of strong connectedness*, which **is** transitive and so
  underwrites identity across a whole life (solving Reid's brave-officer regress). What matters
  in survival is **Relation R** (connectedness and/or continuity), *not* numerical identity;
  identity is a **matter of degree**, and at the margins "is it still me?" can be an **empty
  question** answerable only by stipulation. Ricoeur's **idem** (sameness) vs **ipse**
  (selfhood through change) and the **Ship of Theseus** (same form though every plank replaced)
  say the same thing. Narrative-identity work (McAdams) adds that healthy selves show
  **coherence** and *earned revision* (redemption), not fragmentation (contamination) — though
  Strawson (2004) dissents that narrative unity is neither universal nor required.
- **Design consequence (two *distinct* guarantees, previously conflated).**
  1. **Step-continuity (Parfit/Ricoeur):** the invariant is **not** "`current ≈ seed`" (that
     would forbid legitimate maturation and is philosophically the wrong target). It is **"no
     break in the overlapping chain"** → operationalized as a **bounded per-cycle increment**
     (each `current_t` is *strongly connected* to `current_{t-1}`). Transitively, the self can
     drift arbitrarily far from `seed` over many cycles and remain "the same self" — exactly
     §8.3's Ship-of-Theseus claim, now with a rigorous justification.
  2. **Bounded-total-divergence (the joint leash, §8.3):** a *separate, weaker* ceiling
     `R_archetype` on total divergence from `seed`, whose only job is **no archetype-hopping**.
     Because identity is a matter of degree (Parfit) with no sharp threshold, the leash is an
     *admittedly stipulated* boundary — we own that it is a decision, not a discovered fact.
- **Failure mode this guards.** Using "`current ≈ seed`" as the persistence test would either
  freeze the self (foreclosure) or fire false alarms on healthy growth. Step-continuity +
  stipulated leash is the faithful pair.
- **Skeptical stress-test (Hume bundle; Buddhist anatta; Korsgaard).** A persistent "temperament"
  is, by all three skeptical lenses, *not* a metaphysically given thing: it is at best a **useful
  fiction** (Hume's imagination; the Buddhist "conventionally real, ultimately empty") or a
  **practically-constituted construction** (Korsgaard: the self is *made* by the unity of agency,
  not found). Design import — this is *not* idle philosophy: it is the strongest argument for the
  **operator-only firewall**. Because the temperament vector is a regulatory construct rather than
  a discovered fact, feeding it back to the agent *as self-narrative* would be reifying a fiction
  into a self-fulfilling identity (precisely the §3 anti-self-fiction and Bem self-perception
  hazards). We hold temperament as a useful control-fiction the *operator* can see, never a
  metaphysical self-story the agent narrates about itself.

### 1.6–1.7 The pathologies are the machine failure modes (the break-cycle catalogue)
Established clinical/cognitive science maps one-to-one onto the degeneracy modes §8.7 already
named. This is the cross-validation that makes the guards principled. (Mechanisms established;
the machine analogs/thresholds are engineering inferences, flagged as such.)

| Pathology (source) | Machine analog (self-model drifting from logged valence) | Detector / invariant |
|---|---|---|
| **Foreclosure** (Marcia 1966; Erikson) — commitment with *no* exploration; rigidity, authoritarianism, intolerance of disconfirmation | A dial locks early and logs **zero disconfirmations ever**; all new evidence assimilated as confirming | Per-dial lifetime **disconfirmation count**; a high-stability dial with count ≈ 0, or commitment not preceded by a logged exploration phase, is foreclosed. (= §8.7's "zero disconfirmations ever" one-boolean flag.) |
| **Identity diffusion** (Marcia) — low commitment, no attractor, "drifting" | Dials random-walk; no convergence | **net/gross movement ratio** ≈ 0 over a long window = no attractor |
| **BPD identity disturbance** (Wilkinson-Ryan & Westen 2000; Linehan biosocial: high sensitivity + slow return) | **Thrash**: large, fast, affect-driven swings; one high-valence event rewrites the whole self ("role absorption") | dial volatility ÷ evidence volatility; max single-event displacement; cross-dial co-movement from one event |
| **Rumination** (Nolen-Hoeksema; Bower mood-congruent recall; Beck) — self re-derives evidence from its own state | **Self-confirmation pump**: current state (or state-congruent recall) re-logged as fresh evidence | count of updates whose cause traces to the system's *own state*; invariant = **0** |
| **Confirmation bias / echo chamber** (Nickerson 1998; Nguyen 2020; info cascades, Bikhchandani 1992) — asymmetric exposure + double-counted echoes | One-directional ratchet; one event's echoes counted as independent evidence (= §8.7 **N2**) | confirm-vs-disconfirm acceptance asymmetry; **effective evidence ≤ distinct source-event count** |
| **Dissonance / self-perception** (Festinger 1957; Bem 1967; Fazio-Zanna-Cooper 1977) — a self infers its state by *observing its own behavior*, strongest when internal cues are weak | **The core self-referential pump**: a *logged change* becomes evidence for further change (= §8.7's third-order pump) | trace whether any update cites a prior dial-change or own output as justification; invariant = **none** |
| **Learned helplessness** (Maier & Seligman 2016 — passivity is the *default*, control is what's learned) | A frozen dial unresponsive to contrary evidence | **reversal-liveness**: can disconfirming evidence still move the dial? |
| **Hysteresis / kindling** (Post; Kendler) — escape threshold ratchets up with same-direction evidence | Dial trapped in a basin; ever-larger disconfirmation needed to leave | **out-threshold ÷ in-threshold** ratio rising = sensitization trap |
| *PROTECTIVE:* disconfirmation/immunization (Seligman; Craske 2014 inhibitory learning — update needs **prediction error**) + self-complexity (Linville 1985/87 — decorrelated self-aspects limit spillover) | Seek/weight disconfirming evidence; keep dials **decorrelated** | live disconfirmation rate > 0; **bounded pairwise dial-movement correlation**; one source may not drive many dials |

**Reconsolidation caveat (Nader 2000; Sevenster 2013; but Elsey 2018 / failed replications).** A
self that re-reads its history is *susceptible* to drift, but the neuroscience says drift is
**gated by prediction error**, not triggered by mere recall — and whether recall *overwrites*
vs merely *interferes* is genuinely unresolved. Design import: updates should fire on
**expectancy violation** (an outcome that contradicts the current disposition), not on
confirming re-reads — which is the same conclusion as the disconfirmation/inhibitory-learning
line, reached independently.

---

## 2. The four break-cycle principles (what every mechanism reduces to)

1. **The log must never be an input to itself.** Rumination (state→evidence) and
   self-perception (logged-change→evidence) are the same disease; §8.7's "third-order pump" is
   the same disease again. **Hard firewall:** dials are a pure function of *exogenous* logged
   outcomes only; the drift log and dial states are **read-only, downstream, operator-only**,
   and **never** enter `hooks.py` SessionStart `additionalContext` or any MCP `retrieve` tier.
   This single invariant kills the two most dangerous pumps and is entailed by *both* the
   engineering analysis and the psychology — the strongest possible warrant.
2. **Disconfirmation is the master vital sign.** Foreclosure, echo chamber, helplessness, and
   kindling all reduce to "*the system can no longer be moved against its current direction.*"
   Continuously measure a per-dial reversal/disconfirmation rate; require it stay > 0; updates
   require **prediction error** (Craske), not confirmation.
3. **Count independent sources, not entries.** Echoes (cascades) and ruminative re-derivation
   both inflate apparent evidence; dedup by **source-event identity** (reusing the consolidator's
   existing dedup discipline) so the raw valence stream and its gist-flip echo can't move the
   genotype twice (§8.7 N2).
4. **Keep the self slow and decorrelated.** Rate-limit per-cycle movement (anti-thrash),
   symmetric non-ratcheting thresholds (anti-kindling), and bounded cross-dial correlation
   (Linville self-complexity) — which is also the **joint-leash covariance** §8.3 requires
   (log the *vector*, watch its covariance, not scalar-per-dial).

**The irreducible tension (own it, don't hide it).** Anti-thrash slowing (#4) and
reversal-liveness (#2) pull against each other: too slow → foreclosure/helplessness; too fast →
thrash/diffusion. There is **no single correct setting** — this is the diffusion↔foreclosure
axis reappearing as a control-gain problem. Therefore the system must expose the *measurements*
live; the gain is a tuned, observed trade-off, not a constant. This is the honest reason
observability (eventually the log) has value — while the *control* stays a pure function of
state.

---

## 3. Architecture & build order (the §8.7 prerequisite chain, as phases)

The drift **log is last, not first** (§8.7/§10.3: it is unfalsifiable until an honest outcome
signal and a non-circular test exist). Each phase has a break-cycle exit gate.

### Phase 0 — Temperament STATE + pure-function control (no learning yet)
- **Build.** A `temperament` table (one row per dial: `dial, seed, current, lower, upper,
  plasticity`) + `cdms_meta` for `archetype` and `R_archetype`. Seed at `cdms install` from a
  chosen archetype preset (§8.5). Bump `SCHEMA_VERSION`; idempotent `_migrate` (the real risk
  per §8.7 — guard with a migration test on a copied real store).
- **Control = pure function of `(seed, current, bounds)`**, zero storage: `near_bound()`,
  `large_shift()`, and the **joint leash** `‖current − seed‖_Σ > R_archetype` (Mahalanobis with
  the archetype covariance Σ). No drift yet — `current` == `seed`.
- **Surfacing.** Control output may gate behavior, but state is **operator-only** (CLI `cdms
  temperament`), never additionalContext.
- **Exit gate.** The §10.1 survivability harness can sweep `(seed, bounds)` permutations through
  the *existing* phenotype instrument (`tools/drift_trajectory.py`) with the control active and
  measure differentiation/continuity. No degenerate corner reachable by construction.

### Phase 1a — The proposal lever (§7.6) — prerequisite for honest attribution
- **Why first.** The update rule needs an **honest outcome-attribution signal**, and §8.7(d)
  establishes none exists today (`infer_success` is a lexical heuristic that cannot tell "the
  agent's independent stance was *vindicated*"). The proposal lever supplies it: `accept /
  decline / experiment-outcome (lived vs disconfirmed)` is an **external** signal — which is
  also exactly what principle #1 (Bem firewall) demands the drift couple to.
- **Build.** Structured proposals (what / why-it-matters / evidence / honest-confidence /
  bounded-experiment / cost), a proposal threshold + cadence rate-limit, and declined-proposal
  persistence on a half-life. **N1 guard** (highest-severity): a declined character-proposal
  must **not** resurface purely because new drift rows accrued — resurfacing requires *new
  exogenous disconfirming evidence*, and is rate-limited.
- **Exit gate.** A proposal can be raised, accepted, declined, and its experiment outcome
  recorded as a structured (non-prose) signal; the N1 nag-pump cannot be triggered by drift
  accrual alone (test it adversarially).

### Phase 1b — The update rule (§8.3), driven only by the external signal
- **Build.** The OU/AR(1) step of §1.3, with: the **maturity directional prior** (§1.2),
  **windowed Fleeson aggregation** (anti-thrash), the **prediction-error gate** (update only on
  expectancy violation, §1.6 reconsolidation/Craske), **source-dedup** (#3, anti-N2),
  **activity-clock only** (Δ and trigger are functions of `cycle`; assert `now`/`age_days` never
  enter the drift path — a unit test that fails if they do), and the **leash → proposal** route
  for large/over-leash moves. Cause stored as **structured references** (episode/gist ids +
  valence deltas — the `mem_support_edges` pattern), **never prose** (§3 Step 5 anti-self-fiction).
- **N5 (cadence) mitigation.** Because `cycle` ticks at `SessionEnd`/CLI but not `PreCompact`,
  normalize drift magnitude by *evidence count*, not raw cycle count, so session chunking
  doesn't change the trajectory.
- **Exit gate (break it).** Run the regime suite analogous to `drift_trajectory.py`: a healthy
  varied-outcome history produces slow directional bounded drift with live disconfirmation; the
  matched controls reproduce **each** pathology in §1.6 and the detectors fire (foreclosure →
  zero-disconfirm flag; diffusion → net/gross≈0; thrash → volatility ratio; rumination/
  self-perception → self-sourced-update count > 0; echo → effective>distinct sources;
  helplessness → reversal-liveness fails; kindling → out/in ratio rises). A green verdict means
  every detector is proven non-blind, exactly as the phenotype harness already does.

### Phase 2 — The non-circular test (§10.1 survivability sweep)
- **Build.** Sweep the temperament vector across many `(seed, bounds, plasticity)` permutations,
  run each through synthetic + real-seeded histories (reusing `seed_from_jsonl` + the
  `drift_trajectory --real` path), and classify each as **survivable** (stays in bounds, no
  archetype-hop, preserves differentiation and continuity) vs **collapsed** (homogenizes,
  freezes, or runs to a bound). Discover the survivable region; optionally *derive* archetypes
  from it rather than hand-authoring (§10.1 open question).
- **Why this is non-circular.** The oracle is the *generator-independent* survivability
  criterion + the real-history differentiation oracle — not the log itself. This satisfies
  CLAUDE.md §9 (must be stress-testable) which §8.7 says a log-built-today fails.

### Phase 3 — The drift LOG (observability only, deferred until Phases 1b+2 exist)
- **Build.** Append-only, **operator-only**, **structured-cause** (ids + deltas, never prose),
  **vector-valued** (store the whole `current` vector per event so the joint-leash covariance is
  visible — §8.7), **activity-clock-stamped**. Lives outside any hook/MCP read path. Surfaced
  only via `cdms drift` (operator CLI). **N4 guard:** bound-widening and Growth-axis opening are
  themselves logged events.
- **Why last.** It is pure observability; the control never needs it (§8.7 line 563). It becomes
  *honest* only once 1b gives a real outcome signal and 2 gives a non-circular test.

---

## 4. What this plan deliberately does NOT do (scope discipline)
- It does **not** let an LLM author the update rule or its justification (prose cause) — §3
  Step 5. The Dreamer may render prose *about* a change for the user, never the change itself.
- It does **not** put any temperament state, drift row, or "goal about its own character" into
  agent-readable context — the third-order pump (§8.7) / Bem self-perception firewall.
- It does **not** build the log before its prerequisites (§8.7/§10.3) — that would be a
  serialization test masquerading as validation.
- It does **not** treat the leash as a discovered identity threshold — Parfit's "matter of
  degree / empty question" means it is an owned stipulation.

---

## 5. Open conflicts & risks carried forward
- **Temperament/character heritability split is contested** (Gillespie 2003 vs Cloninger) → we
  use a plasticity *gradient*, but the exact per-dial coefficients are a §10.1 empirical output,
  not assumed.
- **Set-point: immovable vs shiftable** (Lykken/Tellegen vs Diener/Lucas) → bounds + Growth
  exception spans both; which dials get a Growth band is user/archetype choice.
- **Reconsolidation overwrite-vs-interference is unresolved**, and flagship results failed to
  replicate (Elsey 2018) → we rely only on the robust part (prediction-error gating), not on
  strong "recall rewrites memory."
- **Self-complexity buffering is empirically weak** (Rafaeli-Mor & Steinberg 2002) → decorrelation
  is adopted as the joint-leash covariance requirement (which stands on the §8.3 engineering
  argument independently), not sold as a proven psychological buffer.
- **LLM persona-drift literature is mostly preprints** (Li et al. 2024 is peer-reviewed; others
  not) → treated as cautionary (distinguish genuine drift from attention-decay artifacts), not
  foundational.
- **The "attractor / degenerative orbit" vocabulary is largely descriptive metaphor, not
  validated mechanism** (Kording, "attractors are usually not mechanisms"; Eronen & Bringmann
  2021 "theory crisis"; Gelfand et al. 2018; van Geert & Steenbeek — a fitted model can show an
  attractor the real system lacks). This *independently confirms* §8.7's own reframe ("the
  orbit metaphor is the trap"). Design import: we do **not** literalize "degenerative orbit" —
  we measure the **driven-stochastic-process trajectory statistics** §8.7 specifies (reversal
  rate, increment autocorrelation, time-near-bound), and treat them as descriptive indicators,
  not proof of a mechanism. Relatedly, the **critical-slowing-down** detector (§1.6) is a
  *supplementary* early-warning only: its clinical predictive reliability is weak/contested
  (~33% in Smit et al. 2025; Helmich et al. 2024 critique), so it never gates control alone.
- **Affect homeostasis vs allostasis / constructed-emotion are contested** (Sterling vs McEwen;
  Barrett vs basic-emotion camps) → we borrow only the robust, model-agnostic part (a regulated
  variable with a restoring force toward a possibly-shiftable set-point), not any specific
  contested affect theory.
- **Effect-size figures** (~0.1 SD/decade etc.) come from authoritative summaries; exact
  per-decade tables were not verified against paywalled primaries — calibration constants in §1.3
  are order-of-magnitude anchors to be tuned in Phase 2, not asserted exact.

## 6. The one decision that gates everything
The hardest prerequisite is **honest outcome-attribution** (§8.7(d)): without a truthful "the
agent's independent stance was vindicated" signal, the drift rule has nothing legitimate to
learn from, and feeding it the lexical `infer_success` proxy would be precisely the self-fiction
the project forbids. **That is why Phase 1a (the proposal lever) must precede the update rule.**
If we are unwilling to build the proposal lever, we should not build temperament drift at all —
we would only be able to build Phase 0 (static temperament state + control), which is itself a
legitimate, shippable increment.

---

## 7. References (key sources; full URLs in commit research notes)
Cloninger, Svrakic & Przybeck 1993 (Arch Gen Psychiatry) · Gillespie et al. 2003 · Rothbart;
Thomas & Chess; Kagan · Roberts & DelVecchio 2000 · Roberts, Walton & Viechtbauer 2006 ·
Roberts, Wood & Caspi 2008; Roberts, Caspi & Moffitt 2003 · Roberts & Mroczek 2008 · Srivastava
et al. 2003 · Terracciano, Costa & McCrae 2006 · Hudson & Fraley 2015; Stieger et al. 2021 (PNAS
PEACH) · Kenny & Zautra 1995 (STARTS); Steyer et al. 1999 (LST); Fleeson 2001 · Ornstein–Uhlenbeck
process · Brickman & Campbell 1971; Diener, Lucas & Scollon 2006; Lucas 2004/2007; Lykken &
Tellegen 1996; Headey 2010 · Parfit 1984 (Reasons and Persons, §§78–79, 87–89); Locke (Essay
2.27); Reid (brave officer); Ship of Theseus (SEP Identity Over Time); Ricoeur (idem/ipse);
MacIntyre; McAdams & McLean 2013; Strawson 2004 · Marcia 1966; Erikson; Berzonsky 1989; Kroger,
Martinussen & Marcia 2010 · Wilkinson-Ryan & Westen 2000; Crowell, Beauchaine & Linehan 2009 ·
Nolen-Hoeksema 1991/2008; Bower 1981; Beck 1967; van de Leemput et al. 2014 (critical slowing
down) · Nickerson 1998; Wason 1960; Nguyen 2020; Bikhchandani, Hirshleifer & Welch 1992; Bovens
& Hartmann 2003 · Festinger 1957; Bem 1967/1972; Fazio, Zanna & Cooper 1977; Freedman & Fraser
1966; Lepper, Greene & Nisbett 1973; Swann (self-verification) · Maier & Seligman 2016; Post
(kindling); Linville 1985/1987; Craske et al. 2014 (inhibitory learning) · Nader, Schafe &
LeDoux 2000; Sevenster, Beckers & Kindt 2013; Elsey, Van Ast & Kindt 2018 · Li et al. 2024
(COLM, instruction instability).

---

## 8. Round-2 red-team corrections (must be resolved before/within the named phase)

A pre-build adversarial review of *this plan* (and Gemini's "Boiling Frog" attack)
surfaced gaps the plan above did not address. They are recorded here so the build
does not inherit them. None invalidate the phasing; each tightens it.

- **P1 — Phase 0 is inert and therefore unfalsifiable as written.** No temperament
  dial is wired into the consolidation/salience pipeline that `tools/drift_trajectory.py`
  measures (the dials are designed to modulate the still-unbuilt §6 curiosity / §7
  emotion+proposal machinery). So sweeping `(seed, bounds)` through that harness
  changes nothing observable. **Correction:** Phase 0's exit gate is *control-function
  correctness* (unit tests of `near_bound`/`large_shift`/leash on synthetic vectors),
  **not** survivability via the phenotype harness. Temperament observability — and
  hence the §10.1 survivability sweep (Phase 2) and any drift log (Phase 3) — has a
  hard prerequisite on at least one dial having a *wired effect*, which presupposes
  §6/§7. State that dependency explicitly; do not claim Phase 0 is independently
  validatable against phenotype drift.

- **P2 — the joint-leash covariance Σ does not exist at Phase 0.** Archetypes are
  hand-authored presets (§8.5), not fitted distributions, so the Mahalanobis Σ the
  leash needs is only discoverable from Phase 2's survivable region. **Correction:**
  Phase 0 ships a plain Euclidean radius `R_archetype` (an owned stipulation, per §1.5);
  the Mahalanobis Σ is a Phase 2 output that *replaces* it, not a Phase 0 input.

- **P3 — the written OU update rule does not revert to `seed` (it contradicts §1.3's
  own model).** As written, `current ← current + α·(evidence_mean − current) + β·prior`
  has fixed point `evidence_mean`, **not** `seed`; there is no seed-restoring term, so
  under one-sided evidence the dial drifts to and **parks against a bound** — the exact
  ratchet/foreclosure the plan claims to prevent, and the maturity prior pushes it
  there faster. **Correction (Phase 1b):** add an explicit set-point restoring term,
  e.g. `current ← current + α·(evidence_mean − current) − γ·(current − seed) + β·prior`
  with `γ>0`, so the attractor is the seed and evidence is bounded forcing. This is the
  OU process §1.3 actually cites (`dΘ = β(μ−Θ)dt + ξ`, μ = seed).

- **P4 — "the log must never be an input to itself" is sloganized in a way that collides
  with the AR recursion.** An AR(1)/OU step is by definition `xₜ = f(xₜ₋₁,…)`, so `current`
  *is* an input to its own next value; the literal slogan forbids the mechanism. **Correction:**
  restate the invariant precisely as **no self-*perception* loop** — `current` may evolve
  autoregressively (allowed), but a *logged change-event* or the agent's *narration of its
  own drift* must never re-enter as evidence. Phase 1b must encode this exact distinction,
  or the firewall will be built around the wrong object.

- **P5 — the "maturity prior" (§1.2) is an unvalidated human→AI transfer.** The maturity
  principle describes *humans aging*; an assistant does not age (its "decade" is
  consolidation cycles), and which direction "matures" `autonomy_gate` or
  `discovered_emotion_cap` is undefined. Baking a fixed directional push in is the
  riskiest long-horizon choice in the design. **Correction:** the maturity prior is
  **off by default / opt-in**, and its direction (if any) is a Phase 2 empirical output,
  never an asserted constant. (Faithfulness to how a human drifts is not warrant that an
  AI *should* drift that way — the facsimile principle has a boundary here.)

- **P6 — bare accept/decline is treated as an honest signal but is a confirmation
  channel.** Only the *experiment-outcome* (lived vs disconfirmed) is genuinely
  reality-coupled; a tired or sycophantic user rubber-stamping a proposal is not
  evidence the stance was vindicated. **Correction (Phase 1a/1b):** weight
  experiment-outcome as the primary honest signal; down-weight bare accept/decline and
  route it through the same evidence/sycophancy guard (§7.8).

- **P7 — window disjointness is unspecified (re-opens N2 by the back door).** "Windowed
  Fleeson aggregation" does not say whether windows are disjoint; a sliding window
  re-counts each episode across cycles = cross-cycle double-counting. **Correction:**
  disjoint windows, or per-episode consumption tracking, so no outcome moves the genotype
  more than once.

- **G-A — the "Boiling Frog" / sub-threshold ratchet (concrete Phase 1b exit-gate test).**
  The leash fires only when divergence exceeds tolerance; an attacker (or merely
  one-sided history) can nudge `current` by *just under* the threshold every cycle and,
  if the leash is ever anchored to the *previous cycle's* state instead of the immutable
  `seed`, migrate the entire archetype without ever tripping the alarm. **Mandatory test:**
  inject sub-threshold drift (e.g. 0.29 against a 0.30 tolerance) over 50+ consolidation
  cycles and assert the self does **not** archetype-hop — proving the leash anchor is the
  static seed, never a moving reference. This is the operational falsification of P3 and
  the §8.3 "no archetype-hopping" guarantee; it must be green before Phase 1b exits.

> Foundation note: the built-core hardening done before Phase 0 (see `status.md` /
> `docs/REDTEAM_FINDINGS.md`) directly de-risks this layer — in particular the
> migration-ordering fix (schema `user_version` set last) is what makes adding the
> Phase 0 `temperament` table safe on a live identity store.
