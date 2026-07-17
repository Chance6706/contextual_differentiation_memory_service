# Stage-1 bounded recall-drift (reconsolidation) — design + safety review

**STATUS: PRESSURE-TESTED → NO (this substrate) → PARKED. See DRIFT_RECONSOLIDATION_RESULTS.md.** The rule-12
three-agent pressure-test was decisive before build: bounded drift produces recency-HOMOGENIZATION, not
disposition-specific structure (same-disp corr 0.075 < diff-disp 0.178); safety and effect are in tension (the
plasticity bounding that makes it safe starves the coupling); "fact never drifts" was false (centroid = match
key); and fastembed's ~0.07 cone gives the discrete metric no SNR to see drift. Individuation pivots to the
FUNCTIONAL/behavioral arm. This draft is retained as the design + pressure-test record. (Original draft below.)

**Cost:** build + run are **$0 local** (eval harness). No real-CDMS wiring until (a) the experiment shows drift
creates disposition-structure AND (b) a dedicated safety review of the real-CDMS integration.

---

## 0. Why — the diagnosis the negative handed us
At single-pass consolidation the survivor is **per-topic-independent recency**, NOT disposition-structured,
because `_gists_from_clusters` blends each gist only toward **its own topic's** new episodes → **no cross-topic
coupling** → nothing for a disposition to shape (history_effect sits AT its seed-shuffle null). **Drift adds the
one missing thing:** reprocessed gists also drift toward the **shared current-activity centroid**, so topics
touched together move **coherently** — the cross-topic coupling that was absent.

## 1. Hypothesis (falsifiable; the instrument already exists)
- **H-drift:** with drift ON, the goal_hint-fixed `history_effect` **BEATS its seed-shuffle null** (cross-topic,
  seed-coherent structure appears); with drift OFF it **sits at** the null (the committed negative).
- **H-disp (the necessary companion — see §8 risk):** the drift-induced structure is **disposition-specific**
  (same-disposition-across-seeds structures are more similar to each other than to different-disposition ones),
  NOT merely **recency-coherent homogenization.** Beating the shuffle null is necessary but NOT sufficient;
  both a real disposition signal and a recency-collapse would beat it, so H-disp must also hold.
- Falsifier: drift-ON ≈ drift-OFF (no coupling created) OR structure appears but is recency-only (H-disp fails).

## 2. Mechanism
- **Trigger = the consolidate pass.** Canonical home = the **SessionEnd "dreaming" consolidation** (`hooks.py`
  SessionEnd = drain+ingest+consolidate; fires on session-CLOSE, so a closed agent still drifts — the coverage
  Josh flagged). Optionally also PreCompact (currently flush-only) for mid-session freshness. In the
  **experiment**, the per-cycle `Consolidator.run()` is the analog.
- **Attractor = the current-activity centroid** — the embedding centroid of the episodes ingested this
  consolidation window (this cycle's / session's shared activity). Deliberately **NOT** the temperament vector
  (that would *inject* the disposition = the tautology reincarnated) and **NOT** the surfaced-gestalt (that would
  be a self-reinforcing runaway). The disposition acts **indirectly**, through what you happen to be working on.
- **What drifts = only the gists REINFORCED/touched this window** (selective). For each, blend its centroid (and
  running valence) a bounded step toward the current-activity centroid — IN ADDITION to the existing per-topic
  blend toward its own episodes. The shared attractor is what couples them.
- **What NEVER drifts:** the SRO **factual tuple** (subject-relation-object). Drift moves *how a memory is
  weighted/positioned/toned*, never *what it says happened*.
- **Bounding (the firewall — all four hold at once):**
  1. **support-weighted resistance** — reuse `ema_eff = max(ema_min, ema/√support)`: established traits barely
     drift, fresh ones drift more, and an attacker's small cluster can't lower its own resistance;
  2. **magnitude cap** per pass — the drift step is ≤ `α_drift` (small, e.g. ≤0.1) of the distance to the attractor;
  3. **provenance-gated** — an *untrusted* current-activity context cannot drive drift of a trusted gist (the BEM
     never-authors-tuple firewall holds at the drift boundary);
  4. **selective** — only touched gists drift (not all gists → no blanket pull toward recency / homogenization).

## 3. Instrumentation (Stage-1 rich measurement — how / which-direction / why from ONE mechanism)
Per drift event, record: **magnitude** (‖Δcentroid‖); **direction-projection** = cosine of the drift vector
onto each candidate attractor {current-activity, disposition/frequency-centroid, recency-centroid,
surfaced-gestalt}; **cross-topic coherence** (do co-drifted gists become more mutually similar, and does it
plateau or overshoot into collapse?). This measures WHERE drift actually points and WHY — without building the
other attractor mechanisms (that's Stage-2, gated). It is also how we watch for the homogenization failure mode.

## 4. Experiment (drift-ON vs drift-OFF)
Reuse `PT2-nondeg`'s clean **frequency-driven gradient** fixture (uniform goal, re-live frequency = the
disposition; frequency⊥goalset, so non-circular) + the goal_hint-fixed `history_effect` + the **seed-shuffle
null**. Run drift-ON and drift-OFF, ≥16 seeds.
- **PRIMARY:** does `history_effect` beat the seed-shuffle null under drift-ON (it did NOT under OFF)? (H-drift)
- **CO-PRIMARY:** is the drift-induced structure **disposition-specific** (H-disp — same-disp-across-seeds more
  similar than diff-disp), tested against a **disposition-BLIND recency null** (a recency drift with disposition
  labels shuffled)? NOTE: recency is NOT a nuisance to control out — the disposition *acts through* recency (you
  live your goals → they're recent), so they are entangled by design and that is fine. The question is only
  whether the disposition's *characteristic* activity pattern is needed, or whether disposition-blind recency
  reproduces the structure.
- **SECONDARY:** the §3 instrumentation map (direction, magnitude, coherence).
- **Discipline (EXPLORATORY, same bar):** a null on every probe; generate-not-confirm; a candidate graduates
  only if it beats its null AND survives a fresh-seed pre-registered replication. Pre-register the `α_drift`
  and the schedule by mechanism, not by outcome.

## 5. Safety review (load-bearing — recall-drift is a poisoning/confabulation surface)
| failure mode | mitigation |
|---|---|
| **Confabulation** (memory diverges from fact) | drift touches centroid/valence/emphasis, **NEVER the SRO fact** — the fact is preserved; only weighting/position/tone drift, capped |
| **Poisoning via activity context** (attacker-set activity reshapes memory) | provenance gate (untrusted activity can't drive drift) + support-weighted resistance + the BEM never-authors-tuple firewall at the drift boundary |
| **Runaway / identity-creep** (positive feedback) | attractor is current-activity, NOT the self-gestalt → no self-reinforcing loop; support resistance means established identity barely moves; magnitude cap |
| **Over-homogenization** (all gists collapse to one centroid) | selective (touched-only) + cap + support resistance → a nudge, not a collapse; §3 instruments coherence to catch overshoot empirically |
| **Hard-kill misattribution** (crashed session's spool consolidated at *next* SessionEnd → drifts toward wrong activity) | rare edge; cap + provenance limit blast radius; **flagged as a known limitation**, not fully closed |

## 6. Deliberate deviation (register in docs/DEVIATIONS.md)
Reconsolidation-drift makes -A memory **more mutable than pure eviction** — a deliberate step beyond "100%
mechanical eviction" (Josh). Bounded, NOT full human mutability (full mutability is the confabulation surface we
**refuse**). Framed as **representation-not-reproduction**: an optional enrichment, disclosed; the mechanism
emulates reconsolidation's *function* (present-integrating drift) while refusing its *failure modes*.
**Recency-homogenization is an INTENDED brain-like property, not a defect** (six months on one thing dims the
rest): safe because the SRO fact never drifts (recency reshapes the *gestalt*, not the *record*, and the record
stays -D-retrievable) and because -A recency-shaped accessibility is backstopped by -D effortful explicit
retrieval — the human top-of-mind / sit-and-recall division.

## 7. Staging + gates
1. This DRAFT → **rule-12 double pressure-test** → fold → **build** (eval harness, $0).
2. Run drift-ON/OFF → adjudicate H-drift (shuffle null) + H-disp (disposition-specificity).
3. Only if both hold: consider real-CDMS wiring, behind its **own** integration safety review.
4. **Stage-2 (gated on Stage-1 signal):** the alternative-attractor map — drop the tautological
   temperament-vector target, bound the runaway surfaced-gestalt target.

## 8. Pressure-test record (rule-12) — RESERVED. Attack these hardest:
- **THE key risk — disposition-SPECIFICITY, not "recency vs disposition".** Recency-homogenization is an
  INTENDED brain-like property (Josh), safe because (a) drift moves centroid/emphasis, NEVER the SRO fact — the
  fact stays -D-retrievable, so recency reshapes the gestalt not the record; and (b) -A recency-shaped
  accessibility + -D effortful explicit retrieval = the human top-of-mind/sit-and-recall split. So we do NOT
  try to remove recency. The risk is only: does the drift-structure require the disposition's *characteristic*
  pattern (H-disp), or does a disposition-BLIND recency null reproduce it? The disposition-blind null must be a
  fair reproduction of the recency dynamics with only the disposition identity removed.
- **Circularity check on the attractor.** Is "current-activity centroid" truly indirect, or does it smuggle the
  disposition back in (if activity ≡ goalset, is this the tautology again)? Show the coupling is *emergent*,
  not injected. (The frequency-driven fixture's frequency⊥goalset property is the defense — verify it holds.)
- **Do the cap + support-resistance empirically prevent runaway + homogenization?** Perturb `α_drift` and show
  the coherence plateaus rather than collapses.
- **Provenance-gate integrity** at the drift boundary (untrusted activity truly cannot drive drift).
- **Hard-kill misattribution** blast radius.
