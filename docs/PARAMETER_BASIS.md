# Parameter basis — what is free, what is derived, what is coincidence

_Thread 1 of "derive, don't dial." Companion to `src/cdms/config.py` and
`tests/test_parameter_basis.py`._

## Why this document exists

The genotype — the cognitive constants in `Config` — is the policy that shapes a
deployment's identity. A recurring intuition is that it lacks the *precision* of
natural systems (fractals, power laws), because almost every value is stated to one
or two significant figures. This document is the honest answer to that intuition.

The precision worth having is **not more decimal places on guesses** — that is false
precision, and it actively manufactures fake structure. (A recent external analysis
"proved" that adding `K/2` of new salience advances eviction by *exactly* one
half-life. The round numbers `K` and `1/2` produced a clean-looking identity that was
simply wrong: the real renormalization is `K/(K+S_new)`, and the true figure is
16.96 days, not 29.) The precision worth having is **structural**: knowing which
constants are independent principle-parameters, which are exact *consequences* of
others, and which merely happen to share a value. A consequence should be computed
from its sources, not hand-copied — so that moving a free parameter moves everything
downstream of it, and so that no one ever again mistakes a coincidence for a law.

Every numeric cognitive constant falls into one of three classes.

## 1. FREE — independent principle-parameters

Chosen, not derived. These are the genuine degrees of freedom of the genotype. Each
carries roughly one significant figure of real information; stating more digits would
imply knowledge we do not have. They are independent: there is no hidden equation
relating them, and `tests/test_parameter_basis.py` proves the apparent coincidences
among them (§3) are not couplings.

| Constant | Default | Role |
|---|---|---|
| `decay_halflife_days` | 29.0 | Ebbinghaus half-life; sets the decay timescale |
| `reinforce_alpha` | 1.15 | Per-retrieval reinforcement base (testing effect) |
| `reinforce_cap` | 2.0 | Attentional ceiling on one hot memory |
| `retention_floor` | 0.10 | Accessibility below which an episode is evictable |
| `crisis_threshold` | 3.0 | S0 bar for scar elevation; calibrated to a measured 2.8 data-loss crisis |
| `crisis_valence_max` | −0.4 | Valence gate: scars are negative crises |
| `w_surprise / w_contingency / w_self_ref / w_affect` | 1.0 each | Four additive S0 drivers (equal by design choice) |
| `goal_gate_floor` | 0.25 | Floor of the multiplicative goal-relevance veto |
| `gist_valence_ema` | 0.4 | Base learning rate for trait valence |
| `gist_valence_ema_min` | 0.05 | Floor on the adaptive learning rate |
| `gist_decay_per_cycle` | 0.985 | Per-cycle idle-decay multiplier for traits |
| `gist_retention_floor` | 0.25 | Trait strength below which it is forgotten |
| `gist_support_decay_cap` | 100 | Cap on support that counts toward decay resistance |
| `relation_pos_threshold` | 0.15 | Valence above → `handles_well` |
| `relation_neg_threshold` | −0.15 | Valence below → `has_trouble_with` |
| `cluster_sim_threshold` | 0.78 | Cosine link threshold for gist clustering |
| `gist_match_sim_threshold` | 0.90 | Reinforce an existing gist at/above this centroid similarity |
| `dedup_sim_threshold` | 0.95 | Merge near-duplicate episodes at/above this |
| `scar_dedup_sim_threshold` | 0.95 | Dedup near-identical scars (independent of episode dedup) |
| `min_cluster_support` | 2 | Min supporting episodes for a gist tuple |
| `scar_elevation_min_sessions` | 2 | Distinct sessions needed to auto-elevate a scar |
| `scar_project_cap` | 100 | Max auto-elevated scars kept per project |
| `salience_budget` (K) | 1000.0 | Total conserved salience across live episodes |
| `project_budget_cap` | 0.5 | Max fraction of K one project may hold |
| `session_budget_cap` | 0.5 | Max fraction of a project's share one session may hold |
| `assoc_eta` | 0.20 | Retroactive association boost coefficient |
| `assoc_sim_floor` | 0.60 | Only boost past episodes more similar than this |
| `assoc_boost_cap_frac` | 0.5 | Max boost one write injects, as a fraction of its own salience |
| `rest_idle_minutes` | 20.0 | Idle gap marking a rest boundary for auto-consolidation |

## 2. DERIVED — consequences, computed from free parameters

These are **not dials**. Each is an exact function of the free parameters above and is
implemented as a `@property` on `Config` so there is a single source of truth, it
tracks its inputs automatically, and it is regression-locked by tests. Hand-setting
any of these would be a category error.

| Derived property | Formula | Sources | Default |
|---|---|---|---|
| `decay_lambda` | `ln(2) / halflife` | `decay_halflife_days` | 0.023902 d⁻¹ |
| `reinforce_saturation_clamp` | `ceil(ln(cap)/ln(alpha)) + 1` | `reinforce_alpha`, `reinforce_cap` | 6 |
| `ema_floor_onset_support` | `(ema / ema_min)²` | `gist_valence_ema`, `gist_valence_ema_min` | 64 |
| `gist_idle_survival_cycles` | `ln(cap/floor) / |ln(gamma)|` | `gist_support_decay_cap`, `gist_retention_floor`, `gist_decay_per_cycle` | 396.4 |

Details:

- **`decay_lambda`** — the only derived value that already existed; the template for the
  rest. `e^(−λ·halflife) = 0.5` by construction.
- **`reinforce_saturation_clamp`** — reinforcement saturates once `alpha**c` first reaches
  the cap, at the saturation count `c* = ceil(ln(cap)/ln(alpha)) = 5` (α⁵ = 2.0114 > 2.0).
  `salience.accessibility` clamps `access_count` one step past that (`c*+1 = 6`) purely as
  overflow protection — `1.15**access_count` for a very hot, long-lived memory would
  otherwise overflow before the `min(…, cap)` is applied. This property is the single
  source of truth that `accessibility` now reads (it previously recomputed the formula
  inline).
- **`ema_floor_onset_support`** — the adaptive trait-valence rate is
  `max(ema_min, ema/√support)`. The √ term equals the floor exactly at
  `support = (ema/ema_min)² = 64`. Below 64 the floor binds (constant rate); above it the
  rate keeps shrinking. **Counter-intuitive lever:** *lowering* `gist_valence_ema_min`
  *raises* this onset (0.05→0.02 moves it 64→400) and makes mature traits **more** rigid.
  The correct knob for "my instance won't update" is to *raise* `gist_valence_ema_min`.
- **`gist_idle_survival_cycles`** — a gist pinned at the support cap fades to the floor after
  `ln(cap/floor)/|ln(gamma)| = 396.4` idle consolidation cycles (first discrete eviction at
  idle 397). This is what the `gist_support_decay_cap` comment's "~400 cycles" refers to.

## 3. COINCIDENCE — equal by accident, not by relationship

These constants share a value today but live in unrelated computations. They are **not**
coupled; a future change to one must not be assumed to move the other.
`tests/test_parameter_basis.py` locks their independence (each is set to a distinct value
and survives validation).

- **Three `0.5`s** — `project_budget_cap` (project share of K), `session_budget_cap`
  (session share within a project), and `assoc_boost_cap_frac` (write-time boost ceiling).
  Three different allocation layers; independently settable.
- **Two `2`s** — `min_cluster_support` (clustering geometry) and
  `scar_elevation_min_sessions` (cross-session recurrence corroboration). Unrelated domains.
- **Two `100`s** — `gist_support_decay_cap` (idle-decay resistance) and `scar_project_cap`
  (L3 table quota). Unrelated resource controls.
- **`crisis_threshold` (3.0) vs Σweights (4.0)** — the tempting identity `crisis = Σw − 1`
  (4 − 1 = 3) is a coincidence. `crisis_threshold` is calibrated to real incident data (a
  measured 2.8 data-loss crisis just under the 3.0 gate), independent of how many S0 drivers
  exist. Changing the weight count does not move the threshold.
- **`relation_pos_threshold` / `relation_neg_threshold` (±0.15)** — symmetric today, but the
  band is used asymmetry-tolerantly; `_validate` requires only `neg < pos`, not `neg = −pos`.
  Treat them as independent endpoints.

## 4. Laws enforced in `config._validate` (invariants, not derivations)

Relationships the validator actively repairs (warning on stderr), regression-locked by
the same test file:

- **Similarity ladder:** `cluster_sim ≤ gist_match_sim ≤ dedup_sim` (0.78 ≤ 0.90 ≤ 0.95).
- **Zero-goal sub-crisis:** `goal_gate_floor · Σweights < crisis_threshold` with a 10% margin
  (default `0.25 · 4.0 = 1.0 < 3.0`); overpowered weights are scaled down, never the threshold.
- **Relation band ordering:** `relation_neg_threshold < relation_pos_threshold`.
- **EMA floor ≤ base:** `gist_valence_ema_min ≤ gist_valence_ema`.

## 5. Recalibration candidates (open, not done here)

Thread 1 changed **no values** — it only made existing structure explicit and locked it.
Genuine recalibration questions deferred to later threads / experiments:

- The `0.78 / 0.90` similarity thresholds were never benchmarked for code-heavy content
  (see `docs/VALIDATION.md`, A10).
- `decay_halflife_days = 29` is a chosen timescale, not a measured one. Whether forgetting
  should be exponential at all — versus a scale-free power law — is **Thread 2**.
- Whether the four S0 weights should remain equal is untested; equal is a simplicity choice.
