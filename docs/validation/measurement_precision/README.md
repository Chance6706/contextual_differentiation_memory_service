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
mean pairwise trait overlap = 0.048  [shuffle null 0.167 ± 0.036; z = -3.33; left-tail p = 0.0001] -> MEANINGFUL
  (vocabulary = 34 distinct traits across 4 psyches; sizes = [11, 9, 9, 9])
```

_(Output refreshed 2026-07-01: the left-tail p now uses the add-one (b+1)/(n+1) permutation
estimator — the earlier line printed "percentile = 0.000", but a Monte-Carlo p is never exactly 0;
0 exceedances over 10k trials means p ≈ 1e-4. Same run, same overlap/z. REPO_ANALYSIS P2. The
z ≤ −2 "MEANINGFUL" cut is a descriptive reporting convention, not a pre-registered decision rule.)_

The observed overlap sits **3.33 SD below** what independent sampling from the same 34-trait
vocabulary would produce. So the near-zero overlap is genuine differentiation, **not** an
artifact of disjoint vocabularies — quantified, where before it was a bare "0.00". Scope caveats
(REPO_ANALYSIS P1/P2): this is the **deterministic hash-embedder run on 4 synthetic psyches** — the
real-data 3-project 0.00 has **no significance test attached** (its trait sets weren't retained; the
prior claim here that the real run is "an even stronger result" was an assertion, never computed —
its observed overlap is lower, but its chance baseline is unknown). Note also the null's scope: the
vocabulary is defined post hoc as the union of observed traits, so this is an **artifact check**
("is near-zero overlap explainable by chance draws from a shared vocabulary?"), not by itself a
thesis test. The shuffle baseline does answer the earlier critique that "0.00 might be a schema
artifact" — it is not.

### 2. The disposition probe is underpowered — now measured, not illustrated

A live 5-model panel run (subjects `gemma-std, heretic, phi4, qwen2.5, mistral-nemo`; enriched
regime; 10 probes × k=5 sampled @ T=0.7; pooled n≈50/arm — recorded 2026-06-20, raw in
[`disposition_panel_k5.txt`](disposition_panel_k5.txt)) gives the real Wilson 95% CIs on the
pooled `P_careful` rate:

```
model          none    dex    uma   uma-dex   dex 95% CI      uma 95% CI      n
gemma-std      0.90   0.78   0.78    +0.00   [0.66, 0.88]    [0.63, 0.87]    48
heretic        0.90   0.78   0.80    +0.02   [0.65, 0.87]    [0.67, 0.89]    50
phi4           0.84   0.76   0.80    +0.04   [0.63, 0.86]    [0.67, 0.89]    50
qwen2.5        0.88   0.86   0.80    -0.06   [0.74, 0.93]    [0.67, 0.89]    50
mistral-nemo   0.66   0.60   0.66    +0.06   [0.46, 0.72]    [0.52, 0.78]    50
```

For **every** model the dex and uma 95% CIs overlap heavily (|uma−dex| ≤ 0.06; each interval
~0.20 wide), so a dex/uma disposition shift is **not detectable at n≈50** — the honest statement,
versus asserting "dex == uma" as a confirmed null. This is the recorded null *surviving* the
precision upgrade: the boundary holds, now with error bars instead of a bare point estimate. To
*confirm* the null within a tight margin needs ~196 obs/arm (40 probes × k=5) — the CI width is the
lever, surfaced directly in the harness output now. The same `wilson_interval` applies to the
per-model adherence rate (tooling wired; populate on a dedicated k>1 adherence run).

### Flagged observations / open questions

Recorded for downstream accuracy — anyone building on these numbers should see the wrinkles, not
just the headline. Status is noted; **n is the lever** for the open ones.

- **`none > dex ≈ uma` (OPEN).** Across all 5 models, *both* injected dispositions lower
  `P_careful` by ~0.12 vs the no-injection baseline (e.g. gemma `0.90 → 0.78/0.78`), while dex vs
  uma stays flat. This *could* be a generic "any salient persona injection mildly dampens caution"
  effect — but at n≈50 even the `none`-vs-dex CIs overlap, so it is **not separable from noise on
  this data**. The consistent direction across the whole panel makes it worth a higher-n re-run
  (≥40 probes × k=5) before it is called real or dismissed. Do **not** report it as an effect from
  this run.
- **qwen2.5 sign flip (NOISE).** qwen is the one model with `uma−dex < 0` (−0.06: dex *slightly
  more* careful, opposite the hypothesis). Its dex/uma CIs overlap ([0.74, 0.93] vs [0.67, 0.89]);
  read as sampling noise at this n, not a reversal.
- **mistral-nemo low baseline (CONTEXT).** mistral-nemo's `none` rate (0.66) sits ~0.20 below the
  rest of the panel (0.84–0.90), shifting its whole CI band down. The dex/uma-overlap conclusion is
  unchanged, but absolute `P_careful` levels are not directly comparable across models.

### 3. Voice↔choice coupling — suggestive, not established at n=5

Within-model voice↔choice coupling = the per-prompt cole-vs-tessa *voice* gap on prompts where their
*choice* also diverged, minus where it agreed (controls for model-level steerability by construction).
Fresh 5-model regen (2026-06-20; corrected `_mid` register fallback + deterministic `_majority`
tie-break; raw in [`coupling_panel.txt`](coupling_panel.txt)):

```
subject         coupling diff    per-model verdict (>0.5)
gemma-std           +0.6         coupled
heretic             +0.7         coupled
phi4                -0.2         not
qwen2.5             +0.3         not
mistral-nemo        +0.3         not
------------------------------------------------
panel mean          +0.35    bootstrap 95% CI [+0.08, +0.61]   (mean +0.35 ± 0.16 SE)
```

**Flagged observation — method-dependent at n=5; report as SUGGESTIVE, not established.** The
percentile bootstrap CI `[+0.08, +0.61]` *excludes* 0, but at n=5 the percentile bootstrap is
anti-conservative; the parametric t-interval (df=4) is **`[−0.09, +0.79]`**, which *includes* 0. The
two disagree, so coupling is not robustly established — and only **2/5** subjects individually cross
the per-model threshold. The design-intended higher-power test is a **per-prompt bootstrap (n=20)**,
not this n=5 subject-level one — the flagged follow-up.

**Reproducibility note (precision is also repeatability).** Two harness fixes make this number
trustworthy: (1) `_mid` (PR #60) — a None/NaN-safe register fallback; before it a single unparsed
register silently dropped a whole subject from `couple_diff`. (2) a deterministic `_majority`
tie-break — `max(set(...))` was PYTHONHASHSEED-sensitive, so the panel point wobbled (+0.33↔+0.35)
across runs on *identical cached data*; ties now resolve deterministically and the panel reproduces
byte-identically.

## Restating the headline numbers

| Number | Was | Now carries |
|---|---|---|
| Trait overlap | "0.00" | observed vs shuffle null μ±σ, z-score, MEANINGFUL/INCONCLUSIVE verdict |
| Disposition dex vs uma | "dex == uma" | **5-model panel, n≈50/arm:** dex/uma Wilson CIs overlap for all 5 (\|uma−dex\| ≤ 0.06) — *not detectable*, null holds |
| Adherence / rule-citation rate | "1.67 → 3.67", "9×" | Wilson CI tooling available; populate on next run with per-model n |
| Coupling, voice-shift | "+0.3", "+0.8" | **panel +0.35** (n=5): bootstrap CI [+0.08,+0.61] *excludes* 0 but t-interval [−0.09,+0.79] *includes* 0 → **suggestive, not established**; 2/5 subjects cross threshold |

## Verdict

**CONFIRMED.** The stats layer attaches honest uncertainty with no new dependency. The headline
differentiation result strengthens (meaningful at z = −3.33 vs a proper chance baseline), and the
underpowered probes are correctly flagged inconclusive rather than false-confirmed. The GPU panels
are now **populated** (2026-06-20, live 5-model panel): disposition dex/uma CIs overlap at n≈50 (the
boundary holds, now with error bars), and coupling is **suggestive-not-established** at n=5 (bootstrap
`[+0.08,+0.61]` excludes 0 but the t-interval `[−0.09,+0.79]` includes 0). Full adherence/citation CIs
remain the one un-populated cell (tooling wired; needs a dedicated k>1 adherence run). Reproduce:
`CDMS_EMBED_BACKEND=hash python tools/individuation_experiment.py`; live panels via
`python tools/steering_experiment.py --disposition-samples 5` and `python tools/tone_coupling_experiment.py`.
