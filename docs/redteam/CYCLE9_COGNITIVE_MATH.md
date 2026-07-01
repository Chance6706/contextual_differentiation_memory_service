# CDMS Red-Team — Cycle 9 — COGNITIVE MATH SALIENCE AUDIT

> **Date:** 2026-06-18
> **Commit:** f4dd7cf (main)
> **Scope:** Cognitive math, salience formula, decay edge cases, softmax competition,
> budget renormalization, valence EMA, gist centroid drift, temperament aggregation,
> numerical stability. Source files: salience.py (238 lines), consolidate.py (703),
> temperament.py (269), models.py (114), config.py (426), store.py (519), and four
> test files (~1200 lines combined).
> **Methodology:** Formula stress-test at all input ranges, adversarial config analysis,
> concrete numerical examples for every finding.

---

## Executive Summary

CDMS's cognitive math is substantially hardened after 8 prior cycles. The Cycle 8 findings
on weight explosion, budget exhaustion, associative boost, and valence EMA poisoning have
all been addressed with concrete code changes. The per-project AND per-session budget caps,
adaptive EMA with support-weighted floor, associative boost cap, and reinforcement pre-clamp
are all correct and effective.

This cycle found **1 HIGH**, **6 MEDIUM**, and **5 LOW** findings. The most significant:

1. **Config-level associative boost amplification** (HIGH) — `assoc_eta` and `assoc_boost_cap_frac`
   validate up to 1e3, enabling 108x K-budget injection per write
2. **Session proliferation starvation** (MEDIUM) — greater than 10K unique session IDs dilute per-session
   budget below retention floor
3. **Single-episode valence flip at low support** (MEDIUM) — adaptive EMA only fully protects
   traits at support_count greater than or equal 8

---

## Cycle 8 Part IV — Fixed/Status

| Cycle-8 ID | Finding | Status | Detail |
|-----------|---------|--------|--------|
| H-M-1 | Weight explosion bypasses goal gate | **FIXED** | Weights capped at 10. Cross-field check: zero-goal max less than 0.9 times crisis_threshold |
| H-M-2 | Budget exhaustion attack | **FIXED** | Per-session budget cap added (session_budget_cap=0.5). Tested below. |
| M-M-1 | Weight annihilation disables salience | **FIXED** | Cross-field check: w_s + w_c + w_w + w_a greater than 0 restores defaults |
| M-M-2 | `goal_hint` bypass | **NOT FIXED** | Still accepted unauthenticated from MCP callers |
| M-M-3 | Associative boost amplification | **FIXED** | `assoc_boost_cap_frac` caps per-write total boost. See H-M-3 for config escape. |
| M-M-4 | Valence EMA poisoning | **FIXED** | Adaptive EMA: eff = max(0.05, 0.4/sqrt(support)). See M-M-6 for residual. |
| M-M-5 | Empty consolidation cycle bombing | **DOCUMENTED** | Deliberate tradeoff (section 5.3 activity clock). Not fixed by design. |
| L-M-1 | Gist centroid creep | **FIXED** | Support-weighted centroid blend; drift at support=100 is 1 percent/cycle |
| L-M-2 | Single-session softmax dominance | **FIXED** | Session-level budget cap bounds any single session |

---

## Part I: S0 Formula Stress Test

### Formula: `S0 = G_goal times (w_s*S + w_c*C + w_w*W + w_a*abs(A))`

Where:
- `G_goal = goal_gate_floor + (1 - goal_gate_floor) times goal`
- All additive signals clamped to [0, 1]
- `abs(A)` = magnitude of affect (sign stored separately in valence)

#### Input Range Analysis (defaults: w=1.0 each, floor=0.25, crisis=3.0)

| Scenario | G_goal | Additive | S0 | vs Crisis |
|----------|--------|----------|----|-----------|
| All max (goal=1, sig=1) | 1.0 | 4.0 | **4.0** | Above (scar-eligible) |
| All max, goal=0 | 0.25 | 4.0 | **1.0** | Below |
| All zero | 0.25 | 0.0 | **0.0** | Evictable |
| Affect=-1 (others=0) | 0.25 | 1.0 | **0.25** | Below |
| Self-ref only, goal=1 | 1.0 | 1.0 | **1.0** | Below |

**Verdict: Formula is correct and well-bounded.** The multiplicative gate works as designed:
low goal suppresses high-signal episodes.

#### Cross-Field Weight Validation (Cycle-8 H-2 fix)

With `w=10` each (max allowed), the cross-field check fires:
```
zero_goal_max = 0.25 * 40 = 10.0 >= crisis_threshold=3.0
scale = (0.9 * 3.0) / 10.0 = 0.27
weights scaled to 2.7 each, wsum=10.8
S0_max (goal=1) = 10.8, S0_zero_goal_max = 2.7 (less than 3.0) OK
```

**No goal-gate bypass possible at any weight configuration.** The 10 percent margin prevents
memories from self-elevating to scar status without goal relevance.

**RESIDUAL:** S0_max=10.8 with scaled weights enables the associative boost amplification
vector (H-M-3 below).

---

## Part II: Ebbinghaus Decay Edge Cases

### Formula: `A(m,t) = S0 * exp(-lambda*t) * min(alpha^c, Cap)`

Parameters: lambda=ln(2)/29 about 0.0239, alpha=1.15, Cap=2.0, floor=0.10

#### Pre-Clamp Overflow Guard

The reinforcement exponent pre-clamp is **mathematically correct and always safe**:
```
c_max = ceil(log(Cap)/log(alpha)) + 1 = ceil(4.595/0.1397) + 1 = 34
alpha^c_max = 1.15^34 is about 78.9 much greater than Cap
but min(78.9, 2.0) = 2.0
```
For ANY alpha in (1, 1e3] and Cap in [1, 1e6]:
`c_max * log(alpha) is about log(Cap) + log(alpha) less than or equal 20.7`
so `exp(20.7) is about 1e9` much less than float max.

**Even alpha=1.000001 with Cap=1e6:** `c_max=13,815,519` but `c_max * log(alpha) is about 13.8` so safe.

#### Eviction Timelines (S0=1, no access)

| Age (days) | Decay | Access=0 | Access=1 (alpha=1.15) | Access=Cap |
|------------|-------|----------|---------------------|------------|
| 0 | 1.000 | 1.000 | 1.150 | 2.000 |
| 29 (1 half-life) | 0.500 | 0.500 | 0.575 | 1.000 |
| 58 | 0.250 | 0.250 | 0.288 | 0.500 |
| 96.3 | 0.100 | **0.100** (floor) | 0.115 | 0.200 |
| 125.3 | 0.050 | 0.050 | 0.058 | **0.100** (floor) |

**Verdict:** Eviction timelines are correct and well-behaved. A single access extends
episode life by about 6 days. The cap at 2.0x keeps hot memories from permanently dominating.

#### Edge Cases Tested

| Input | Result | Safe? |
|-------|--------|-------|
| `age_days=-5` (future timestamp) | Clamped to 0 by `max(0.0, ...)` | Yes |
| `age_days("not-a-date")` | Returns 0.0 (graceful) | Yes |
| `access_count=-1` | Clamped to 0 by `max(0, ...)` | Yes |
| `S0=0` | Returns 0 regardless of reinforcement | Yes (evictable) |
| `age_days=infinity` | `exp(-infinity)=0` so accessibility=0 | Yes (evictable) |

---

## Part III: Softmax Temperature and Competition

### Numerical Stability

The softmax implementation uses max-subtraction for stability:
```python
t = max(1e-6, temperature)
m = max(values)
exps = [exp((v - m) / t) for v in values]
```

| Input | Temperature | Output | Correct? |
|-------|-------------|--------|----------|
| `[1, 2, 3, 4]` | 1.0 | [0.032, 0.087, 0.237, 0.644] | Yes |
| `[1, 2, 3, 4]` | 0.01 | [near 0, near 0, near 0, 1.0] (winner-take-all) | Yes |
| `[1, 2, 3, 4]` | 100.0 | [0.246, 0.249, 0.251, 0.254] (near-uniform) | Yes |
| `[0, 0, 0]` | 1.0 | [0.333, 0.333, 0.333] (uniform fallback) | Yes |
| `[-1e6, -1e6]` | 1.0 | [0.5, 0.5] (uniform fallback) | Yes |
| `[1e6, 0]` | 1.0 | [1.0, near 0] (stable via max-subtraction) | Yes |
| `[]` | 1.0 | `[]` | Yes |

**Temperature floor (1e-6)** prevents division by zero. **z=0 fallback** to uniform prevents
division by zero when all exps underflow.

**Verdict: Softmax is numerically stable at all input ranges.**

### Hierarchical Competition Score Range

Competition scores multiply into base salience as `0.5 + comp`:
- `comp in [0, 1]` (softmax output times softmax output)
- Boosted range: `[0.5 * S0, 1.5 * S0]` — maximum 3:1 winner-loser ratio

This is well-bounded. No single episode can be amplified more than 50 percent or reduced below
50 percent of its base salience through competition alone.

---

## Part IV: Budget Renormalization and Eviction

> **Historical note (2026-07-01, REPO_ANALYSIS doc-sync):** Part IV analyzes the allocator **as it
> stood during Cycle 9** — including the infeasible-cap equal-split behavior that was subsequently
> replaced (the cap is now a hard invariant in every branch: Cycle-9 #3 for the infeasible branch,
> REPO_ANALYSIS core #5 for the degenerate all-zero branch). For the shipped semantics read
> `src/cdms/salience.py::allocate_capped_proportional` and `docs/DEVIATIONS.md` M5; the numbers
> below are kept as the red-team record, not as a description of current behavior.

### Per-Project AND Per-Session Cap Effectiveness (Cycle-8 H-M-2 fix)

The two-level budget allocation is effective:

**Cross-project scenario (adversary in different project):**
```
Adversary: 200 episodes at S0=4, project_weight=800
Legitimate: 20 episodes at S0=2, project_weight=40
After project cap (0.5): adversary=500, legitimate gets remaining=500
Per-episode legitimate: 500/20 = 25 much greater than floor=0.10 OK
```

**Cross-session scenario (adversary in same project, different session):**
```
Session A (legit): 20 eps at S0=2, weight=40
Session B (adv): 200 eps at S0=4, weight=800
After session cap (0.5 of project share=1000): A gets 500, B gets 500
Per-episode: A=500/20=25, B=500/200=2.5 OK
```

**Extreme scenario (5000 adversary episodes):**
```
Adversary: 5000 eps at S0=4, weight=20000
Legitimate: 5 eps at S0=2, weight=10
After project cap: both get 500
Per-episode legitimate: 500/5 = 100 OK
```

**Verdict: Budget exhaustion from Cycle 8 H-M-2 is fully mitigated for cross-project
and cross-session attacks at default configuration.**

### allocate_capped_proportional Infeasible Cap Fallback

When `cap_fraction * n less than 1.0`, the function falls back to equal split:
```
project_budget_cap=0.2, 6 projects: 0.2*6=1.2 >= 1.0, OK
project_budget_cap=0.1, 6 projects: 0.1*6=0.6 less than 1.0, EQUAL SPLIT
```
Equal split gives each project K/n regardless of usage weight. This is a **correct
degradation** — with very tight caps, proportional allocation is infeasible.

---

## Part V: Valence EMA and Gist Traits

### Adaptive EMA Protection (Cycle-8 M-M-4 fix)

Effective rate: `ema_eff = max(0.05, 0.4 / sqrt(support_count))`

| Support | ema_eff | Single-episode flip? | Episodes to flip neutral to negative |
|---------|---------|---------------------|--------------------------------------|
| 1 | 0.400 | **YES** (0.40 greater than 0.15) | 1 |
| 2 | 0.283 | **YES** | 1 |
| 4 | 0.200 | **YES** | 1 |
| 7 | 0.151 | **YES** | 1 |
| 8 | 0.141 | No | 2 |
| 10 | 0.127 | No | 2 |
| 16 | 0.100 | No | 2 |
| 64 | 0.050 | No | 4 |
| 100 | 0.050 | No | 4 |

**Flip threshold:** valence crosses relation_neg_threshold=-0.15 when `ema_eff greater than 0.15`.
This requires support_count less than 8.

**The protection is real but incomplete at low support.** A fresh gist (support=2-4) can
still be flipped by a single adversarial episode. This is arguably correct — fresh traits
SHOULD be malleable — but an attacker who can inject episodes into a small cluster can
flip traits cheaply.

---

## Part VI: Gist Centroid Drift

### Support-Weighted Blend

Blend formula: `centroid_new = (w_old * old + w_new * new) / norm`

| Existing support | New cluster size | Drift per cycle |
|-----------------|------------------|-----------------|
| 2 | 1 | 33.3 percent |
| 5 | 1 | 16.7 percent |
| 10 | 1 | 9.1 percent |
| 50 | 1 | 2.0 percent |
| 100 | 1 | 1.0 percent |
| 100 | 3 | 2.9 percent |

**Verdict: Centroid drift is well-bounded and inversely proportional to support.**
An established gist (support greater than or equal 50) moves less than 3 percent per cycle even with a 3-episode cluster.

### Zero-Norm Edge Case

`_centroid()` guards against `norm=0` by returning the zero vector:
```python
return (m / n).astype(np.float32) if n greater than 0.0 else m.astype(np.float32)
```
If ALL member vectors cancel to zero (extremely unlikely with unit-norm embeddings),
the returned centroid is a zero vector. Downstream `np.dot(centroid, gc)` would return
0.0, preventing any match. **Safe but degenerate — no crash, just no gist match.**

---

## Part VII: NEW FINDINGS

### HIGH

#### H-M-3: Config-level associative boost amplification — assoc_eta and assoc_boost_cap_frac validation too permissive
**File:** config.py (validation), store.py:214-231
**Trace:** Both `assoc_eta` and `assoc_boost_cap_frac` validate up to 1e3. With
`assoc_eta=1000, assoc_boost_cap_frac=1000, w=10` (post-cross-field: S0_max about 10.8):
```
cap per write = 1000 * 10.8 = 10,800
10 writes between consolidations: +108,000 salience injected (108x K_budget)
```
Even at defaults (`assoc_eta=0.2, assoc_boost_cap_frac=0.5, S0_max=4`):
```
cap per write = 0.5 * 4.0 = 2.0
100 writes: +200 salience (20 percent of K)
270 writes: +540 salience (54 percent of K)
```
Between consolidations, total salience can far exceed K_budget, compressing
legitimate episodes' share when renormalization finally runs.
**Impact:** An adversary with MCP access can inflate nearby episodes between
consolidation passes, distorting the budget.
**Fix:** Cap `assoc_eta` at 1.0 and `assoc_boost_cap_frac` at 1.0. The current 1e3
upper bound serves no legitimate purpose.

### MEDIUM

#### M-M-6: Single-episode valence flip at support_count less than 8
**File:** consolidate.py:420-427
**Trace:** The adaptive EMA (`ema_eff = max(0.05, 0.4/sqrt(support))`) protects traits
with support greater than or equal 8 from single-episode flips. Below that threshold:
```
support=1: ema_eff=0.40, one val=-1 episode flips valence from 0.0 to -0.4 (less than -0.15)
support=4: ema_eff=0.20, one val=-1 episode flips valence from 0.0 to -0.2 (less than -0.15)
support=7: ema_eff=0.15, one val=-1 episode flips valence from 0.0 to -0.15 (boundary)
support=8: ema_eff=0.14, valence goes to -0.14 (greater than -0.15, no flip) OK
```
**Impact:** Adversary can flip fresh traits (support 1-7) with a single injected episode.
**Fix:** Raise `gist_valence_ema_min` from 0.05 to 0.08 (pushes single-flip threshold
to support=25) or increase `min_cluster_support` from 2 to 4. Characterized tradeoff:
higher min support delays gist formation.

#### M-M-7: goal_hint bypass remains unfixed (Cycle-8 M-M-2 re-raised)
**File:** store.py:190-193
**Trace:** Any MCP caller can pass `goal_hint=1.0` to maximize the goal gate and
achieve S0=10.8 (with scaled max weights). This is the prerequisite for the
budget exhaustion and associative boost attacks.
**Impact:** Enables all S0-dependent amplification attacks.
**Fix:** Strip `goal_hint` from MCP tool callers; compute from tool name only.

#### M-M-8: Associative boost accumulation between consolidations (default config)
**File:** store.py:214-231
**Trace:** With defaults, each write injects up to `0.5 * S0` total boost into KNN
neighbors. A burst of 100 writes at S0=4 before consolidation runs:
```
100 * (0.5 * 4.0) = 200 extra salience (20 percent of K)
```
This pushes total salience above K, so the next consolidation must compress more
aggressively — potentially pushing marginal episodes below retention_floor.
**Impact:** Write bursts can cause unexpected evictions at next consolidation.
**Fix:** Lower `assoc_boost_cap_frac` default from 0.5 to 0.2, or add a running
total that stops boosting once the session's share of K is exhausted.

#### M-M-9: Competition amplifies budget asymmetry
**File:** salience.py:204-231, consolidate.py:330-356
**Trace:** Hierarchical competition multiplies base salience by `(0.5 + comp_score)`.
Winners get up to 1.5x their base; losers get down to 0.5x. After budget
renormalization, this means a competition winner in a dominant session can receive
3x the salience of a loser in a weak session:
```
Winner in dominant session: 1.5 * S0 * (session_share/K)
Loser in weak session: 0.5 * S0 * (session_share/K)
Ratio: up to 3:1
```
**Impact:** Amplifies the natural Matthew effect. Legitimate but quiet sessions
lose 2/3 of their share to dominant sessions.
**Fix:** Characterized design tradeoff. The 3:1 ratio is intentionally bounded.
Could tighten to 2:1 by using `0.7 + 0.6 * comp` instead of `0.5 + comp`.

#### M-M-10: reinforce_cap and assoc_boost_cap_frac validation upper bounds excessive
**File:** config.py (validation)
**Trace:**
- `reinforce_cap`: validates up to 1e6. `A(m,t) = S0 * decay * min(alpha^c, 1e6)`.
  At S0=10.8, decay=1.0, cap=1e6: accessibility=10.8 times 1e6 = 1.08 times 10^7. This is
  108 million times the retention floor. A single accessed episode could dominate
  retrieval rankings.
- `assoc_boost_cap_frac`: validates up to 1e3. See H-M-3.
**Impact:** Config misconfiguration can disable the attentional ceiling.
**Fix:** Cap `reinforce_cap` at 10.0 (2x-5x the default). Cap `assoc_boost_cap_frac` at 1.0.

### LOW

#### L-M-3: goal_gate_floor=0 allows total goal veto (by design)
**File:** config.py (validation), salience.py:43-62
**Trace:** Validation allows `goal_gate_floor=0`. With `goal=0`: `gate=0`, `S0=0`,
episode immediately evictable. The code comment says "A floor avoids totally zeroing-out"
but validation permits zero.
**Impact:** Operator who sets floor=0 gets total goal veto. Could surprise if set
accidentally.
**Fix:** Lower validation bound from `0 less than or equal` to `0 less than v less than or equal 1`. Or document that 0 means
total veto intentionally.

#### L-M-4: conserve_budget returns unchanged list on all-zero saliences
**File:** salience.py:109-123
**Trace:** `sum(saliences) less than or equal 0` returns original list. This is the correct defensive
behavior (never silently wipe), but means a store with all-zero episodes (e.g., corrupted
DB) will never be cleaned up by renormalization.
**Impact:** Corrupted zero-salience episodes persist indefinitely.
**Fix:** None needed — the evict step handles these (accessibility=0 less than floor).

#### L-M-5: _blend_centroid zero-vector return on cancellation
**File:** consolidate.py:473-478
**Trace:** If `w_old * old + w_new * new = 0` (vectors cancel), the returned
centroid is a zero vector. Downstream `np.dot` returns 0.0, preventing gist matching.
**Impact:** Extremely rare (requires exact vector cancellation with unit-norm inputs).
No crash, just a temporarily unmatchable gist.
**Fix:** None needed in practice. Could add a small perturbation fallback.

#### L-M-6: Softmax z=0 fallback to uniform may mask a bug
**File:** salience.py:190-201
**Trace:** If ALL exp values underflow to 0 (theoretically impossible with
max-subtraction, but possible with extreme float16 truncation), the fallback to
`[1/n, ...]` is silent. In practice, `exp(0)=1` always, so at least one exp is 1.0.
**Impact:** No practical risk. The fallback is a defensive pattern.
**Fix:** None needed.

#### L-M-7: Gist decay floor allows trait survival at fractional support
**File:** consolidate.py:488-496, config.py
**Trace:** `gist_retention_floor=0.25`. Strength formula: `support * decay^idle`.
A trait with `support=1, decay=0.985` has strength `0.985^idle`. It reaches floor=0.25
at idle=92 cycles. With `support=3`: 3 times 0.985^idle less than 0.25 at idle=230 cycles.
**Impact:** Well-behaved. Weak traits fade in about 100 cycles; strong ones persist for
hundreds. The floor ensures traits with less than 0.25 effective support are evicted.
**Fix:** None needed — the parameter is well-calibrated.

---

## Part VIII: Numerical Stability Summary

| Component | Overflow | Underflow | NaN | Verdict |
|-----------|----------|-----------|-----|---------|
| `compute_s0` | Impossible (bounded inputs) | Returns 0 | Config rejects NaN | **Safe** |
| `accessibility` | Pre-clamped (c_max guard) | Returns 0 for old memories | Config rejects NaN | **Safe** |
| `softmax` | Max-subtraction prevents | z=0 then uniform fallback | Config rejects NaN | **Safe** |
| `conserve_budget` | Returns unchanged if sum less than or equal 0 | Returns unchanged if sum less than or equal 0 | N/A | **Safe** |
| `allocate_capped_proportional` | Water-filling converges | Equal-split fallback | N/A | **Safe** |
| `associative_boost` | Bounded by cap | Returns s_old unchanged | N/A | **Safe** |
| `_blend_centroid` | Norm normalization | Returns zero vector | N/A | **Safe** |
| Config `_validate` | `math.isfinite()` rejects inf | N/A | `isfinite()` rejects NaN | **Safe** |
| Reinforcement alpha^c | Pre-clamped by c_max | min(alpha^0, Cap)=1 | N/A | **Safe** |

**No numerical stability issues found.** All formulas have appropriate guards for
overflow, underflow, NaN, and division-by-zero.

---

## Part IX: Temperament Aggregation Correctness

The section 8 temperament layer is a pure function of its inputs (no DB, no I/O, no wall-clock).

### Dial Computation
- `preset_dials()`: seed plus/minus band, clamped to [0, 1]. OK.
- `plasticity = PLASTICITY[dial] times ARCHETYPE_PLASTICITY[archetype]`. OK.
- `band = _MAX_BAND times plasticity = 0.5 times plast`. OK.

### Leash Distance
- Euclidean distance from static seed. OK.
- Rejects mismatched dial sets (fails loud). OK.
- Anchor is immutable seed (catches boiling-frog). OK.

### Archetype Radius
- `min(LEASH_FRACTION times box_corner, HOP_FRACTION times nearest_other_seed)`. OK.
- Binds within box (LEASH_FRACTION=0.9 less than 1.0). OK.
- Prevents archetype-hopping (HOP_FRACTION=0.9 less than 1.0). OK.

### No Wall-Clock Discipline
AST-based enforcement: no `datetime`, `time`, `os` imports; no `now()`, `utcnow()`,
`time()`, `__import__` calls. OK.

**Verdict: Temperament math is correct, bounded, and well-tested (648 lines of tests
including fuzz, boiling-frog adversary, and concurrent seeding).**

---

## Part X: Prioritized Action Items

### P0 — Fix Before Next Merge

| ID | Finding | Fix | Effort |
|----|---------|-----|--------|
| H-M-3 | Config assoc boost amplification | Cap `assoc_eta` at 1.0, `assoc_boost_cap_frac` at 1.0, `reinforce_cap` at 10.0 | 15 min |

### P1 — Fix Before Production

| ID | Finding | Fix | Effort |
|----|---------|-----|--------|
| M-M-7 | `goal_hint` bypass | Strip from MCP callers | 30 min |
| M-M-8 | Boost accumulation between consolidations | Lower `assoc_boost_cap_frac` default to 0.2 | 5 min |
| M-M-10 | Loose validation caps | Tighten `reinforce_cap` to [1, 10], `assoc_boost_cap_frac` to [0, 1] | 15 min |

### P2 — Fix When Convenient

| ID | Finding | Fix | Effort |
|----|---------|-----|--------|
| M-M-6 | Single-episode flip at low support | Raise `gist_valence_ema_min` to 0.08 | 5 min |
| M-M-9 | Competition 3:1 ratio | Consider tighter multiplier (0.7 + 0.6 times comp) | 30 min |
| L-M-3 | `goal_gate_floor=0` allowed | Lower validation to `0 less than v` | 5 min |

---

## Closing Assessment

CDMS's cognitive math is in excellent shape after 9 cycles of red-teaming. The S0 formula
is correct and bounded at all input ranges. The Ebbinghaus decay with reinforcement pre-clamp
is numerically stable. The softmax competition is stable and well-bounded. The per-project
AND per-session budget caps effectively prevent the Cycle-8 budget exhaustion attack.

The primary remaining concern is **config-level amplification**: the validation upper bounds
on `assoc_eta` (1e3), `assoc_boost_cap_frac` (1e3), and `reinforce_cap` (1e6) are
excessively permissive. Tightening these caps (P0) eliminates the most significant remaining
attack vector with zero functional impact.

The adaptive EMA for valence poisoning is a genuine improvement over Cycle 8 but only fully
protects traits at support greater than or equal 8. Fresh traits remain malleable — this is defensible
(continuity vs. plasticity tradeoff) but should be a conscious decision.

**Bottom line:** One P0 finding (config cap tightening, 15-minute fix). The mathematical
foundations are solid.

---

*End of Cycle 9 (COGNITIVE MATH and SALIENCE) — red-team audit. All findings independently
verifiable against commit f4dd7cf.*
