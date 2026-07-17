# Differentiation experiment — results

## VERDICT (as-shipped gf=0.25, surfaced): NULL — no entity-level individuation (entity-set sep CI includes 0) AND identity-overlap does not track goal-overlap (permutation r=+0.08, p=0.709).

## Run config
```json
{
  "cdms_file": "D:\\Repo\\cdms-evalbuild\\src\\cdms\\__init__.py",
  "cdms_repo": "D:\\Repo\\cdms-evalbuild",
  "cdms_commit": "0b8dc55",
  "is_worktree_src": true,
  "seeds": 8,
  "cycles": 80,
  "embedder": "fastembed",
  "preconditions": {
    "median_evicted_frac": 0.280625,
    "median_n_traits": 17.0,
    "min_n_traits": 12,
    "erasure_fired": true,
    "HALT": false
  }
}
```

## CO-PRIMARY — entity-set separation (drop relation; ~0 => NO entity-level individuation)
- gate_floor=0.25 [raw]: entity-set sep=0.000 [0.000,0.000]
- gate_floor=0.25 [surfaced]: entity-set sep=-0.031 [-0.078,0.031]
- gate_floor=0.0 [raw]: entity-set sep=0.000 [0.000,0.000]
- gate_floor=0.0 [surfaced]: entity-set sep=0.047 [-0.031,0.109]

## Permutation null (M2) — does identity-overlap TRACK goal-overlap beyond chance?
- gate_floor=0.25 [raw]: r=+0.124  p=0.5517  (n=24)
- gate_floor=0.25 [surfaced]: r=+0.082  p=0.7086  (n=24)
- gate_floor=0.0 [raw]: r=+0.160  p=0.4413  (n=24)
- gate_floor=0.0 [surfaced]: r=+0.545  p=0.0055  (n=24)

## Cross-disposition tuple metric (similar > different; NOTE: separation lives in the relation label — see co-primary above)
- gate_floor=0.25 [raw]: similar_AB=0.743 [0.694,0.790]  different_AC=0.705 [0.614,0.796]  **sep=0.038 [-0.032,0.112]**  null_AU=0.659 [0.597,0.725]
- gate_floor=0.25 [surfaced]: similar_AB=0.497 [0.385,0.616]  different_AC=0.466 [0.401,0.531]  **sep=0.030 [-0.100,0.167]**  null_AU=0.482 [0.369,0.580]
- gate_floor=0.0 [raw]: similar_AB=0.657 [0.581,0.717]  different_AC=0.609 [0.546,0.676]  **sep=0.048 [-0.028,0.119]**  null_AU=0.667 [0.621,0.715]
- gate_floor=0.0 [surfaced]: similar_AB=0.449 [0.399,0.508]  different_AC=0.310 [0.268,0.360]  **sep=0.138 [0.094,0.183]**  null_AU=0.462 [0.394,0.560]

blind conditions collapse cross-disposition overlap to 1.0 by construction (A=B=C under none/uniform/random).

## Flagged observations (record every anomaly, status + n)
- **F1 — as-shipped NULL (headline, 8 seeds):** at `gf=0.25` entity-set individuation = 0.00 and the
  permutation null is non-significant (r≈+0.08, p=0.71). The product does not individuate by disposition
  on a frozen history. This is the honest negative that motivates the erasure arm.
- **F2 — CEILING signal (gf=0.0, non-shipped, FLAGGED to investigate):** the permutation null IS
  significant at the ceiling — surfaced r=+0.545, p=0.0055 (n=24). BUT entity-set separation is still ~0
  (+0.047, CI incl. 0), so the goal-structured signal lives in the RELATION labels, not in which topics
  survive — AND this is a FROZEN history (nothing was forgotten), so it is NOT erasure-driven. So even the
  ceiling "signal" is the goal-gate tilting relation valence, not the thesis. The erasure arm must show
  whether this survives when forgetting actually fires and at the entity level. Not claimed as support.
- **F3 — precondition semantics caveat:** `erasure_fired=true` (median evicted-frac 0.28 ≥ 0.20) reflects
  EPISODE churn (budget competition), NOT topic/gist erasure — the frozen cube keeps ALL topics (entity
  individuation 0). The erasure arm needs a TOPIC-DISAPPEARANCE precondition (gist-level), not episode
  eviction. Fixed in step 2.
- **F4 — factorial CIs are still pseudo-replicated:** `factorial_decomposition`/`same_disposition_null`
  still bootstrap over dependent seed-pairs (`_cluster_ci` helper added but not yet wired in). The VERDICT
  does NOT depend on them (it rests on the per-seed entity-set + the permutation test). Wire cluster-
  bootstrap for the erasure arm before any "comparable forces" claim.

## Factorial: disposition vs history main effects + interaction (effect = 1 − overlap) — CIs PSEUDO-REPLICATED (F4)
- gate_floor=0.25 [raw]: disposition_effect=0.295 [0.204,0.386]  history_effect=0.413 [0.380,0.445]  both=0.379 [0.341,0.416]  interaction=-0.329
- gate_floor=0.25 [surfaced]: disposition_effect=0.534 [0.469,0.599]  history_effect=0.605 [0.563,0.646]  both=0.627 [0.592,0.659]  interaction=-0.512
- gate_floor=0.0 [raw]: disposition_effect=0.391 [0.324,0.454]  history_effect=0.417 [0.386,0.448]  both=0.437 [0.401,0.471]  interaction=-0.371
- gate_floor=0.0 [surfaced]: disposition_effect=0.690 [0.640,0.732]  history_effect=0.629 [0.593,0.665]  both=0.710 [0.663,0.753]  interaction=-0.609

## Fulcrum — overlap vs shared-history fraction f (SAME vs DIFF disposition)
- [raw] same-disposition: f=0.0:0.657  f=0.25:0.622  f=0.5:0.734  f=0.75:0.744  f=1.0:1.000
- [raw] diff-disposition: f=0.0:0.641  f=0.25:0.595  f=0.5:0.627  f=0.75:0.677  f=1.0:0.705
- [surfaced] same-disposition: f=0.0:0.376  f=0.25:0.405  f=0.5:0.535  f=0.75:0.546  f=1.0:1.000
- [surfaced] diff-disposition: f=0.0:0.396  f=0.25:0.366  f=0.5:0.396  f=0.75:0.400  f=1.0:0.466

## Drift-against-self (overlap WITH the keep-all `none` baseline; lower = more drift)
- [raw]: uniform=0.584 [0.517,0.650]  random=0.568 [0.472,0.668]  disposition-salience@0.25=0.539 [0.464,0.608]  disposition-salience@0.0=0.556 [0.515,0.593]
- [surfaced]: uniform=0.444 [0.379,0.512]  random=0.429 [0.343,0.530]  disposition-salience@0.25=0.449 [0.349,0.568]  disposition-salience@0.0=0.417 [0.354,0.478]