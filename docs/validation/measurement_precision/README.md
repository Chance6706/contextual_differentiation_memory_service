# Measurement precision — error bars on the thesis numbers

_Thread 3 of the "precision like nature" effort. Companion to `src/cdms/stats.py` and
`tests/test_stats.py`. Where Threads 1–2 made the *mechanism* precise, this thread makes
the *reporting* precise: every headline number should carry its uncertainty._

## Supposition

The project's headline numbers — trait overlap `0.00`, adherence spread `1.67 → 3.67`,
coupling `+0.3`, disposition `dex == uma` — were reported as bare point estimates. That is
false precision in the other direction: a single decimal implies an exactness we never
established. Two falsifiable claims:

1. A reusable statistics layer (shuffle/permutation baseline, Wilson interval, bootstrap CI)
   can attach honest uncertainty to these numbers without new dependencies.
2. Doing so does not weaken the thesis — the headline differentiation result is *meaningful*
   against a proper chance baseline, while the underpowered probes are correctly shown to be
   *inconclusive* (not false-confirmed).

## Procedure

- `src/cdms/stats.py` (pure stdlib + numpy, deterministic given a seed):
  - `wilson_interval(successes, n)` — score CI for a binomial rate (disposition / adherence).
  - `bootstrap_ci(values, statistic=mean)` — percentile bootstrap for any axis-aware statistic.
  - `mean_se`, and `pooled_overlap_baseline` / `overlap_significance` — a shuffle null for the
    trait-overlap metric: each project draws its traits independently from the shared
    vocabulary (the union of all observed `(relation, object)` tuples), giving the overlap that
    chance alone would produce. `z = (observed − null_mean) / null_sd`.
- Wired into `tools/individuation_experiment.py` (overlap significance) and
  `tools/steering_experiment.py` (Wilson CI on the pooled disposition rate). Unit-tested in
  `tests/test_stats.py` (known-answer Wilson, bootstrap coverage/determinism, baseline properties).

## Results

### 1. Trait overlap is meaningfully below chance (offline, hash embedder)

`CDMS_EMBED_BACKEND=hash python tools/individuation_experiment.py`:

```
mean pairwise trait overlap = 0.048  [shuffle null 0.167 ± 0.036; z = -3.33; percentile = 0.000] -> MEANINGFUL
  (vocabulary = 34 distinct traits across 4 psyches; sizes = [11, 9, 9, 9])
```

The observed overlap sits **3.33 SD below** what independent sampling from the same 34-trait
vocabulary would produce. So the near-zero overlap is genuine differentiation, **not** an
artifact of disjoint vocabularies — quantified, where before it was a bare "0.00". (This is the
deterministic hash-embedder run, whose traits cluster more loosely; the real-embedder / real-data
run reports an even lower observed overlap, i.e. an even stronger result. The shuffle baseline is
also the right answer to the earlier critique that "0.00 might be a schema artifact" — it is not.)

### 2. The disposition probe is underpowered — now visible, not hidden

The Wilson 95% CI on the pooled `P_careful` rate makes the n=10 greedy test's limits explicit
(illustrative pooled counts):

```
n=10 :  dex P_careful 95% CI [0.40, 0.89]   uma 95% CI [0.49, 0.94]   -> CIs overlap heavily
n=100:  dex P_careful 95% CI [0.60, 0.78]   uma 95% CI [0.71, 0.87]   -> still overlap, far tighter
```

Overlapping CIs mean a dex/uma disposition shift is **not detectable at this n** — which is the
honest statement, versus asserting "dex == uma" as a confirmed null. The same `wilson_interval`
applies to the adherence rate. To *confirm* the null within a tight margin needs ~196 obs/arm
(40 probes × k=5) — the CI width is the lever, surfaced directly in the harness output now.

## Restating the headline numbers

| Number | Was | Now carries |
|---|---|---|
| Trait overlap | "0.00" | observed vs shuffle null μ±σ, z-score, MEANINGFUL/INCONCLUSIVE verdict |
| Disposition dex vs uma | "dex == uma" | Wilson 95% CI per condition; "not detectable at n" when CIs overlap |
| Adherence / rule-citation rate | "1.67 → 3.67", "9×" | Wilson CI tooling available; populate on next run with per-model n |
| Coupling, voice-shift | "+0.3", "+0.8" | `bootstrap_ci` / `mean_se` available for the per-model panel |

## Verdict

**CONFIRMED.** The stats layer attaches honest uncertainty with no new dependency. The headline
differentiation result strengthens (meaningful at z = −3.33 vs a proper chance baseline), and the
underpowered probes are correctly flagged inconclusive rather than false-confirmed. The
GPU-dependent panels (coupling, full disposition/adherence) have the tooling wired; their CIs
populate when those experiments next run (they need a live model — not required to land the
precision layer itself). Reproduce: `CDMS_EMBED_BACKEND=hash python tools/individuation_experiment.py`.
