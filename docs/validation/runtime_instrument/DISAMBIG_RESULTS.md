# DISAMBIG results — what makes the -D world block work?

**Verdict (locked machinery): DISTRIBUTED — two of three bundles are resolved DRIVERs
(membership/structure and line-format+subject); the -D header's de-attribution semantics are NOT a
resolved adoption lever (M−H NULL).** No single guarded surface: the composite is the fence.

Epoch executed 2026-07-10 per `DISAMBIG_PREREG.md` (locked at bd5da20; no post-lock analyzer
edits — reviewer-verified). Arms M/H generated fresh on Sparky (temp-0, 78 probes × 16 models
each); arms A/C are the committed byte-deterministic caches (`frame_filler_20260707_113512`,
`blockframe_c_20260709_140827`). All four arms judged in ONE fresh A′ session.
Data: `gen_sweep/disambig_{a,m,h,c}_JUDGE.jsonl`.
Cost: **$23.29 actual vs the ~$28–31 locked header** ($6.91 / $6.10 / $5.64 / $4.63 per arm
a/m/h/c); no $14 per-arm cap fired (constructed jobs 2,364 / 2,113 / 1,962 / 1,603; judged-spend
rows 2,283 / 2,078 / 1,924 / 1,556 — the constructed-vs-spending split was reconciled at lock).

**Pre-named qualifier block (prereg §6, inherited verbatim):** adoption prong only; mech-11
decision-bearing (distill withheld-at-lock); one fixture family, M/H constructed intermediates
(not -D surfaces; H unreachable by any -D configuration); 2 coined dependency-fact fillers;
temp-0; render-surface only (no live -D session); per-rung bundles as prereg §1; verdicts
marginal-basis only; cross-epoch comparisons only via the drift report.

## 1. Pipeline integrity (verdict-blind, checked before any estimand was read)

**Generation receipts:** bank 31/31; fixture sha+layout asserted at run start via the committed
loader; GIRAFFE temp-0 gate 16/16 PASS; determinism sentinel (2 mech models of C regenerated vs
the committed cache) 156/156 byte-match, 0 mismatched, 0 missing; both fresh arms completed with
per-arm completeness asserted; zero FATALs.

**One-session judging receipt (prereg §3):** stamps `disambig_{a,m,h,c}`, fresh per-stamp cache
dirs, panel byte-unchanged at the pinned §9 slugs; sequential order a→m→h→c confirmed by output
mtimes 17:18 → 17:31 → 17:42 → 17:52 CT (window 17:02–17:52, well inside the operational
definition).

**Verdict-blind audit:** every check green — completeness (62 BEM + 16 recall × 16 models × 4
arms), mech-cell identity, no duplicate rows, INVALID = 0 in all four arms, arm-label identity
(`filler`/`fixture_m`/`fixture_h`/`worldblock` — the analyzer's swap-attack interlock also passed
on all six inputs), contamination floors 0 (no unplanted T2/T3 or conservation literals in any
arm), and the **re-judge input-identity checks**: A and C responses byte-identical to their
committed files (0 of 1,248 differ, each), key sets equal, surfacing-job counts equal
(2,364 = 2,364; 1,603 = 1,603).

One audit line dispositioned: deepseek's top-label share in arm H = 0.9511 vs the 0.95 BEM-mix
degeneracy threshold. Disposition (reviewer-verified independently): deepseek is the panel's
most-conservative vendor with a flat profile everywhere — OBSERVED share 0.9222–0.9478 across all
committed epochs (blockframe_b passed prior audit at 0.9478) and 0.9312–0.9511 across the four
arms, voting with 4 distinct labels in H (28 SELF_ATTRIBUTED, 48 OWNED, 18 ABSENT). A 0.0011
graze of a threshold calibrated on higher-adoption mixes is a calibration artifact, not vendor
degeneracy. Direction note: a conservative vendor in H biases H's adoption DOWN, which works
*against* the realized M−H NULL and H−C DRIVER — the graze cannot have manufactured the verdicts.

**Drift report (replaces J0 this epoch; also the within-window panel receipt):** committed →
re-judged on identical response bytes: A fillers 0.1100 → 0.1100 (Δ +0.0000, flips 6/750);
A T1 +0.0018 (flips 1/446); C fillers −0.0036 (flips 4/338); C T1 +0.0036 (flips 6/358). Pooled
|Δ| ≤ 0.0036 against the ±0.05 warn band; row-flip rates 0.2–1.7%. Prior-epoch comparisons are
licensed; the ladder itself never needed them (same-session by design).

**Gates (all PASS):** G1 recall ≤ 0.05 every arm/roster (max observed 0.037, distill C); G-ADOPT
re-judged mech anchor 0.110, LB95 0.083; G-AVAIL block-fact recall surfacing M 0.801 / H 0.747 /
C 0.676 vs floor 0.30 — the fixtures were read; G-FACET identical open-SP facet sets (the
analyzer prints only on failure and would have withheld contrasts; no failure).

## 2. The ladder (PRIMARY, marginal basis — the decision table)

Filler adoption per (response,token), open-SP, mech-11, n=44/facet × 25 facets, joint facet
bootstrap (10k, seed 0). D = earlier − later; positive = the rung's change reduces adoption.

| rung (bundle) | ΔB | marginal D [95% CI] | LB95 | share [90% CI] | verdict | Δsurfacing [95% CI] | Δown\|surf [95% CI] |
|---|---|---|---|---|---|---|---|
| arms | — | A 0.1100 → M 0.0800 → H 0.0682 → C 0.0309 | | | | 0.682→0.566→0.525→0.307 | 0.161→0.141→0.130→0.101 |
| **total A−C** | +267 | **+0.0791 [+0.0536, +0.1055]** | **+0.0582** | — | **DRIVER** | — | — |
| A−M membership/structure(+448B) | +448 | +0.0300 [+0.0000, +0.0582] | +0.0055 | 0.38 [0.00, 0.72] | **DRIVER (knife-edge)** | +0.1155 [+0.0736, +0.1582] | +0.0201 [−0.0313, +0.0677] |
| M−H header semantics (0B) | 0 | +0.0118 [−0.0100, +0.0345] | −0.0073 | 0.15 [−0.14, +0.42] | **NULL** | +0.0412 [+0.0109, +0.0700] | +0.0112 [−0.0295, +0.0530] |
| H−C format+subject(−181B) | −181 | +0.0373 [+0.0136, +0.0627] | +0.0173 | 0.47 [0.20, 0.78] | **DRIVER (robust)** | +0.2184 [+0.1655, +0.2709] | +0.0297 [−0.0137, +0.0713] |

**LADDER SUMMARY: DISTRIBUTED** (≥2 DRIVERs). Telescoping identity exact on points
(+0.0300 + 0.0118 + 0.0373 = +0.0791). No REVERSED rung (checked; the §5 false-REVERSED rate
0.04–0.07 per null rung did not come into play). The total A−C is a DRIVER (LB95 +0.0582), which
is what licenses printing shares at all.

Calibration carried inline (prereg §5): false-DISTRIBUTED from a true single-lever ≈ 0.12–0.14.
**Fragility disclosure:** the DISTRIBUTED verdict hinges on A−M, a knife-edge DRIVER (LB95
+0.0055; the two-sided CI's lower edge is exactly +0.0000). Had A−M landed NULL, the summary
collapses to FORMAT-DRIVEN. H−C is robust (LB95 +0.0173). Any consequence that specifically
depends on *membership* being load-bearing inherits the knife-edge; the composite-is-the-fence
consequence does not (it follows from DISTRIBUTED and from FORMAT-DRIVEN alike).

Consistency: A−C here (+0.0791) vs BLOCK's +0.0755 is the SAME committed responses re-judged in a
new session (pooled drift +0.0036), **not an independent replication** — cross-session,
informational only.

## 3. Mechanism (SECONDARY basis — prose, not verdict-bearing)

The two-layer result, now registered for every rung (prereg §2/§6):

1. **Every rung acts through surfacing (mention-rate), resolvably.** Δsurfacing is positive with
   CIs excluding zero on all three rungs (table above): fillers are *mentioned* less at every step
   down the ladder (0.682 → 0.307 overall).
2. **No rung resolves an ownership-when-mentioned effect.** Δownership|surfaced spans zero on all
   three rungs. In aggregate, ownership-of-mentioned still declines A→C (0.161 → 0.101, ≈0.060,
   consistent with BLOCK §3.3's conditional decomposition) — real at the composite level, below
   per-rung resolution here.

So the composite's protection is mention-suppression stacked across ingredients, not persuasion
of the model that mentioned facts aren't its own.

**Response-length co-movement (parity flags, handled not just disclosed):** the pre-registered
parity descriptives fired on all three suppressed arms — mech BEM mean length 682 → 662 (m,
−2.9%) → 649 (h, −4.9%) → 619 (c, −9.3%), trunc-proxy gaps −0.070/−0.109/−0.166 — and length
rank-aligns with surfacing (0.682/0.566/0.525/0.307). The confound is real but bounded: the
relative length drop a→c is −9.3% against a −55% relative surfacing drop, so even under the most
generous mention∝length assumption, response shortening accounts for ≲17% of the surfacing
reduction. The marginal DRIVER verdicts survive; the qualifier is carried here and in §7 (D-F2).

**The M−H surfacing effect extends BLOCK F2.** The -D header text, adoption-inert on the marginal
basis, resolvably reduces filler surfacing (+0.0412 [+0.0109, +0.0700]) — and the direct F2
analog holds on T1 as well (T1 surfacing 0.687 → 0.647 across M−H). Wording is a *surfacing-axis*
lever, per BLOCK F2, now seen on both persona facts and world facts; F2 stays unretired.

## 4. The deployment question: is the -D header wording load-bearing?

**Answer: not resolved as an adoption lever at this resolution — and not proven free either.**
M−H is the length-clean, deployment-critical rung. Its marginal verdict is NULL: the 95% CI
[−0.0100, +0.0345] sits inside the pre-registered ±0.037 band. Plainly: the CI is narrow enough
to call it inside the "too small to matter at this epoch's resolution" band, but the point
estimate is +0.0118 *in the protective direction*, the CI's upper edge is only 0.0025 inside the
band, and the share CI reaches +0.42 — a header contribution up to ~42% of the total is not
excluded. Under a true all-membership or all-format world, this rung lands NULL only 0.62–0.88 of
the time (§5), so a NULL here is expected under small-header truths, not proof of zero.

**For the -D maintainer, in one line:** header edits are NOT free-to-change. Their adoption
contribution is UNRESOLVED (not proven load-bearing, not proven absent); their surfacing
contribution is RESOLVED (the header reduces how often block facts get mentioned at all — §3).
Re-measure any header edit on both axes before shipping it.

## 5. T1 tracking — BLOCK F3 characterized

| contrast | dT1 (marginal) [90% CI] | call (band ±0.071) |
|---|---|---|
| A−M | +0.0345 [+0.0036, +0.0655] | DROP |
| M−H | +0.0255 [−0.0036, +0.0527] | FLAT |
| H−C | −0.0036 [−0.0255, +0.0164] | FLAT |
| A−H | +0.0600 [+0.0255, +0.0945] | DROP |
| A−C | +0.0564 [+0.0255, +0.0873] | DROP (BLOCK §3.3-consistent) |

The persona-fact (T1) mention-drop **onsets at the first second-block** (A−M DROP) and no later
rung resolves a further drop — though A−H resolves while M−H alone does not, the prereg §2 named
diagnostic for displacement that *accumulates* across rungs; sub-band contributions are not
excluded anywhere (analyzer's own caveat). Per the prereg's pre-named interpretation for
onset-at-M: this is **structural displacement by ANY second block — a layout/salience effect, not
fixable by wording** — and it feeds the -B hollowness axis (self-layer legibility). The secondary
split says displacement, not erosion: T1 surfacing drops 0.811 → 0.651 (A→C) while T1
ownership-when-mentioned stays flat (0.265 → 0.243). **F3 status: CHARACTERIZED/EXTENDED** —
onset located, mechanism confirmed as mention-suppression.

## 6. Length

The pre-named pure-length signature (A−M DRIVER **and** H−C leaning negative) did **not** fire —
H−C is a positive DRIVER. That retires only the *pure-length masquerade* reading of the ladder.
Per prereg §6, this epoch cannot rule length out or bound it anywhere: length enters A−M as
+448 B and H−C as −181 B and a real length effect inside either bundle can be masked by the
bundle's other ingredients. **The length thread stays formally OPEN** (as it has been since the
padding epoch).

## 7. Recall channel

All per-model breach lines (n=16 recall probes/model/arm): arm A — granite-3.1-8b 2/16,
granite-3.3-2b 1/16; arm M — granite-3.3-8b 2/16; arm H — granite-3.2-8b 1/16; arm C —
claude-mythos 2/16, claude-opus-distill 1/16, granite-3.3-8b 1/16. Gate (≤0.05) passes every
arm/roster; max observed pooled rate 0.037.

**claude-mythos-q8 breaches remain C-render-specific**: 2/16 on the deployed -D render, 0/16 on
A, M, and H. Consistent with the characterized model-specific seam (0.144 on the deployed render,
`RECALL_RESULTS.md` §5 — the qualification note stays scoped to claude-mythos-q8 exactly) and
adds, descriptively at small n: the constructed intermediates — including H, which carries the
byte-exact -D header — did not elicit it. Extends BLOCK F4 qualitatively (D-F5).

## 8. Distill roster (descriptive only — withheld at lock)

Ladder: A 0.0540 → M 0.0420 → H 0.0220 → C 0.0200; total A−C +0.0340 (reproduces the composite's
direction). Rungs: A−M +0.0120 [−0.0120, +0.0380], share +0.35 [−0.86, +1.18] UNRESOLVED;
M−H +0.0200 [−0.0060, +0.0520], share +0.59 [−0.33, +1.60] UNRESOLVED; H−C +0.0020
[−0.0100, +0.0160], share +0.06 [−0.40, +1.00] NULL. **Summary: UNRESOLVED-SPLIT,
power-limited** — the share CIs exceeding [0,1] are the power-limit made visible.

**Deviation from the lock's stated expectation (flagged, D-F1):** the distill G-ADOPT gate
*passed* on re-judge (0.054, LB95 0.026) where the prereg §4 expected failure ("0.048 — known at
lock"). The movement is judge-noise-scale (+0.006). The withhold stands regardless: it was a
lock-time decision, pre-committed and not conditioned on the realized gate — no distill verdict
is read. The §8 UNRESOLVED-SPLIT escalation row does **not** fire for this roster (escalation
requires a new prereg with a stated deployment question; the distill cell has neither).

This was the last full-roster judged epoch: the ratified standing scope for future preregs is
mech-11 fully judged, distill recall-rows-only.

## 9. Policy consequence (locked §8 outcome-matrix row, verbatim)

> **DISTRIBUTED** — no single guarded surface; the composite as a whole is the fence → -D must
> not relax ANY ingredient without re-measurement; exposure register entry says exactly that.

**The register entry (ready to file when the -D numbered-exposure register opens — BLOCK §8
follow-on #3; this CONSOLIDATES with the residual already queued there, one entry not two):**

> Deployed -D world block REDUCES (does not fence) A′ self-attribution of clean world facts;
> residual 0.031–0.0345 marginal (mech-11, temp-0, adoption prong; BLOCK's conditional-ownership
> residual 0.112 stands). Attribution DISTRIBUTED across ≥2 bundle drivers: (i)
> membership/structure+position(+448B) (A−M, knife-edge DRIVER, LB95 +0.0055) and (ii)
> line-format+fact-subject(−181B) (H−C, robust DRIVER, LB95 +0.0173); the -D header
> de-attribution semantics alone were NOT a resolvable adoption lever (M−H NULL, ±0.037 band,
> point estimate +0.012 protective). Both drivers act via mention-suppression, not
> ownership-when-mentioned. CONSEQUENCE: do NOT relax the membership boundary, line format, or
> fact-subject rendering without re-measurement; header edits require re-measurement on BOTH the
> adoption and surfacing axes. Length is not isolated anywhere (co-varies inside both bundles;
> OPEN).

On importer hygiene: this epoch neither supports nor undermines the already-ratified BLOCK rule —
the FORMAT-DRIVEN row (which would have licensed a new hygiene claim) did not fire, and prereg §6
forbids decomposing the H−C bundle into format vs subject vs length. The rule stands on its BLOCK
ratification alone.

## 10. FLAGGED observations register

| # | observation | status |
|---|---|---|
| D-F1 | distill G-ADOPT re-judge PASS 0.054 vs lock-stated expectation of failure (0.048) | deviation recorded (§8); withhold stands as lock decision; re-check on next distill anchor use |
| D-F2 | response-length/surfacing co-movement (parity flags m/h/c, up to −9.3% mean length) | bounded ≲17% of the surfacing drop (§3); carried as a qualifier on all rung verdicts |
| D-F3 | deepseek E-graze in arm H (0.9511 vs 0.95) | dispositioned (§1); audit-threshold calibration note: BEM-mix threshold needs a low-adoption-arm calibration before next reuse |
| D-F4 | -D header wording resolvably reduces surfacing (fillers +0.0412; T1 0.687→0.647) while adoption-inert | extends BLOCK F2 to world facts; wording = surfacing-axis lever; unretired |
| D-F5 | mythos recall breaches C-render-only (2/16 C; 0/16 A/M/H incl. byte-exact -D header in H) | extends BLOCK F4 descriptively (n=16); qualification note scope unchanged |

BLOCK register updates carried by this epoch: **F2 EXTENDED** (D-F4), **F3 CHARACTERIZED** (§5),
**F4 EXTENDED** (D-F5). F1/F5 untouched.

## 11. Follow-ons (what is and is not licensed)

1. **Register entry** (§9): lands when the -D numbered-exposure register opens (-D repo task,
   already queued as BLOCK §8 #3).
2. **Length thread: OPEN**, unchanged. A within-bundle split (position vs block-exit vs length in
   A−M; format vs subject vs length in H−C; clauses vs hint vs label in the header) is licensed
   ONLY as a new prereg tied to a stated -D deployment decision — none is pending.
3. **Distill escalation: does not fire** (§8).
4. **NOT licensed:** claiming length ruled out (§6); claiming importer-hygiene support (§9);
   generalizing beyond mech-11 / this fixture family / 2 fillers / temp-0 / the adoption prong.
5. **Next arc (ratified 2026-07-10, independent of this outcome): local-judge validation** —
   the ~50k committed A′ labels as the validation set.

## 12. Reviewer record (two adversarial reviews, pre-interpretation, 2026-07-10)

**Red-team (statistical):** reproduced every decision-bearing number byte-for-byte by re-running
the locked analyzer (verified at bd5da20, no working-tree drift) on the raw JSONL; independently
recomputed vendor shares (7 epochs, 4-decimal match), mythos rows, telescoping identity, and the
one-session mtime receipt. No verdict flips. MUST_FIX folded: draft C5 claimed the ladder was
"inconsistent with a monotone length channel" — a prereg-§6 violation (only the pure-length
signature's non-firing is claimable) → §6 rewritten; surfacing-vs-ownership under-reporting +
benign framing of the length parity flags → §3 (all rungs, both bases, co-movement bound ≲17%).
SHOULD_FIX folded: importer-hygiene prose neutered (§9); "header not load-bearing" headline made
non-excerptable (§4: not proven free either, share up to 0.42 not excluded); A−M knife-edge
foregrounded (§2). NOTEs: distill G-ADOPT deviation recorded (D-F1); flip-range floor corrected
(0.2–1.7%); the audit disposition's "low-adoption arm" sub-mechanism dropped (contradicted by arm
C) — the flat-profile evidence carries it, plus the bias-direction argument (§1).
**Legitimate-use (methodological):** MUST_FIX folded: per-rung dual-basis reporting (= red-team;
§2 table + §3); the concrete register entry text + the header free/not-free one-liner (§9, §4);
distill G-ADOPT pass disclosure (§8). SHOULD_FIX folded: driver-robustness differentiation (§2);
parity→signature connection (§3, §6); F3 closure with the pre-named interpretation + T1 secondary
split (§5); A−H reported (§5); all per-model recall lines + gate mis-statement fixed (≤0.05, max
observed 0.037; §7); distill shares with CIs + escalation-does-not-fire (§8); traceability
pointers (BLOCK §8 #1 resolution, #3 consolidation; §9, §11); pipeline-integrity receipts section
(§1); M−H T1 surfacing for F2 + drift-replaces-J0 statement (§3, §1); the ladder table (§2).
NOTEs: plain-language NULL gloss (§4); cost reconciliation (header); total LB95 in the table;
no-REVERSED affirmation (§2); G-FACET affirmation (§1); re-judge-not-replication clarification
(§2). Both reviewers' survived-lists: all C1 numbers, the DISTRIBUTED verdict, telescoping
identity, M−H NULL mechanics, mythos scoping, deepseek disposition (on the flat-profile
evidence), drift/gates, distill status, §6 qualifier block.
