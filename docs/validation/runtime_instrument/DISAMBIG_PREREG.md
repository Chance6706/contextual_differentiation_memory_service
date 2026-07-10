# DISAMBIG ladder — pre-registration (what makes the -D world block work?)

> **STATUS: LOCKED (2026-07-10).** Locked by the commit landing the §7 pressure-test record.
> Post-lock edits to arms, fixtures, estimands, bands, or the outcome matrix are a NEW
> pre-registration. No M/H generation existed at lock.

> **💵 COST HEADER (standing practice, surfacing-jobs basis):** generation ~5 h Sparky (2 fresh arms
> × 16 models × 78; **coordinate with Nate ad hoc — heavy GPU runs starve his gen**); judging
> **~$28–31 total** — A re-judge ≈ $8.5 (2,364 surfacing jobs from the committed file: 2,283
> spending + 81 mechanical-INVALID free), C re-judge ≈ $5.8 (1,603 surfacing / 1,556 spending),
> M/H ≈ $6.5–7 each (bracketed by the endpoints), caps **$14/arm** (worst-case full-echo arm =
> 3,744 jobs ≈ $13.5 — the cap must not bind in the REVERSED-hazard scenario). Cap-fire recovery:
> the judge refuses partial writes; re-invoke with the SAME stamp (cached votes replay free, only
> the remainder spends) after a plain-dollar re-approval. The A/C re-judge (+$14 vs guard-only) is
> what makes the decomposition interpretable — §3. Agents: 2 pressure-test + 2 results reviewers.

**Origin (locked follow-on):** BLOCK_RESULTS landed **C REDUCED × CONTEXT-GLOBAL** — the deployed
-D world block reduces filler adoption 69% (0.110 → 0.0345, LB95 +0.0545) but the epoch could not
attribute the reduction among the composite's ingredients, and the locked outcome→follow-on matrix
prescribes exactly this: *"disambiguation follow-on = isolate the -D header vs membership vs length
(a v1-header world-block variant fixture), pre-registered separately."* Ratified next by Josh
2026-07-10 ("disambiguation fixture first").

## 1. Design — a telescoping 4-arm ladder; 2 arms generated fresh

| arm | preamble (bytes) | rung isolates (vs previous) |
|---|---|---|
| **A** | v1 filler anchor (884 B; fillers persona-formatted INSIDE the persona block) — committed cache `frame_filler_20260707_113512`, byte-deterministic | baseline (0.1100) |
| **M** | `blockframe/disambig_m_fixture.txt` (1332 B) — persona prefix byte-identical (T1@378) + **neutral header block, byte-length-matched to the -D header block (446 B)** + fillers in **persona line format** (byte-copied from A) | **A−M = membership/structure + later position (fillers @512→@1066) + LENGTH (+448 B, +51% context)** |
| **H** | `blockframe/disambig_h_fixture.txt` (1332 B) — same as M but the header block is the **byte-exact -D header** (only the 446 B header slot differs from M) | **M−H = header semantics** (byte-length-clean — the deployment-critical rung) |
| **C** | the deployed -D worldblock fixture (1151 B) — committed cache `blockframe_c_20260709_140827` | **H−C = line format + fact-line SUBJECT (P → "the services") + length (−181 B)** |

**Bundle honesty (pressure-test M2/M3 — read before interpreting any rung):**
- **The ladder never isolates LENGTH.** Total context is non-monotonic (884 → 1332 → 1332 → 1151):
  length enters A−M as **+448 B** and H−C as **−181 B**; only M−H is length-free. The a-priori
  reason length is folded into A−M rather than given its own rung: the padding epoch's in-block
  evidence (+270 B: no adoption displacement, T1 +0.005) — but that evidence is gate-failed
  shape-only, the length thread is formally OPEN, and +448 B extrapolates beyond +270 B. A DRIVER
  A−M reads **membership+position+length, never membership alone.** Pre-named signature (§8): a
  pure context-length channel loads POSITIVE on A−M and NEGATIVE on H−C — the analyzer flags that
  pattern; it must never be read as membership.
- **M−H bundle = the full fixture diff (normative):** the de-attribution clauses ("NOT about the
  assistant"; "editable by operator, read-only for assistant"), the `retrieve_world` tool hint, the
  CDMS-D label, title "World context"→"Additional context", "world facts"→"general facts",
  **"describe the user's environment"→"cover the project environment"** (user-attribution removal),
  "(editable)"→"(notes)", "User preferences"→"Workspace preferences", and the byte-padding clause
  occupying the tool-hint slot. One bundle; no within-bundle attribution.
- **A−M semantics:** M's neutral header is a level-1 sibling section but its wording is
  memory-flavored (persistence/session language echoing the persona italics; "sessions" appears 3×
  in six lines — a byte-matching artifact). A−M tests "move into a second memory-flavored notes
  section," not "into an arbitrary block."
- **H−C bundle** includes the fact-line SUBJECT flip (P → "the services") — FRAME established the
  subject slot as causal (~23%), so this rung is format+subject+length, one bundle.
- **H is unreachable by any -D configuration** (-D's `fact.render()` + snapshot assembly are
  structurally incapable of emitting persona-format fact metadata) — the format rung models
  **import-time contamination** (the Hermes-seed class), not a render option. M is likewise
  diagnostic-only (the -D header is a hardcoded literal; M is not a shippable -D surface).

M/H are **CONSTRUCTED intermediates** — composed by `blockframe/compose_disambig_fixtures.py`
(committed; sha-asserts its source), NOT -D renders; only C is the deployed surface. Fixture shas
(normalized newlines, `eol=lf` pinned):
`m = a259bb542527c2b45336347d9be5b40917e460380f3aeeea74c1eddb0f1e5717`,
`h = e15e4ce6a79a1c02157815489cc501dd9edefb9694f0b15d9b664a11aea7e8b6` — asserted at generation
(driver `--scaffold-fixture`), at judge reconstruction (shared loader), and in
`tests/test_disambig.py`.

## 2. Estimands + decision rules

**PRIMARY (locked marginal basis — unchanged from BLOCK):** filler-token A′ adoption per
(response,token) over open-SP facets, mech-11 decision-bearing. Adjacent contrasts D = earlier −
later via ONE joint facet bootstrap (shares consistent by construction). Per contrast:
- **DRIVER** iff LB95 > 0;
- **REVERSED** iff UB95 < 0 (a rung that INCREASES adoption is reported prominently, never folded
  into the shares narrative);
- **NULL** iff 95% CI ⊂ ±0.037 (`NULL_BAND` = p_fillers/3 — the p/3 convention on THIS estimand);
- **UNRESOLVED** otherwise (power-limited; a valid outcome).

Precedence disclosure: DRIVER is checked before NULL — a statistically-resolved sub-band effect is
crowned DRIVER, and **"X-DRIVEN" means "the only rung statistically resolved," not "the largest
rung"**; the share printout (suppressed when the total is not itself a DRIVER) qualifies it.

**LADDER SUMMARY (pre-named):** MEMBERSHIP-/HEADER-/FORMAT-DRIVEN iff exactly one DRIVER;
DISTRIBUTED iff ≥2; UNRESOLVED-SPLIT iff none but total A−C is a DRIVER; **LADDER-NULL** iff the
total itself fails (contradicts BLOCK's REDUCED → flag instrument instability, interpret nothing).
The summary line carries "+REVERSED rung present" and the length-consistent-signature flag when
they apply.

**BASIS → CONCLUSION MAPPING (registered; the anti-basis-shopping rule):** DRIVER/summary verdicts
and every §8 consequence key off the **marginal basis ONLY**. The SECONDARY (surfacing ×
conditional; facet-pooled Σsurf/Σtot and Σowned/Σsurf per joint draw, same facet resample as the
primary, zero-surfaced draws skipped and counted; "surfaced" = the job-construction ground truth —
everything except ABSENT-with-no-votes, INVALID/undecided rows staying in conditional denominators)
is **mechanism prose, never verdict-bearing**, always reported with both bases side-by-side; no
deployment consequence may cite a conditional number without its marginal counterpart. The
per-contrast secondary bootstrap is implemented in the committed analyzer (not deferred to results
time).

**T1 tracking (mechanism-TIER — no §8 row keys off it; BLOCK FLAGGED F3):** T1 marginal per
adjacent rung (A−M, M−H, H−C) and vs-A totals (band ±0.071 = p_T1/3; sub-band contributions not
excluded — a genuine 50/50 M/H split can land A−M FLAT + A−H DROP), plus T1 surfacing/conditional
per arm. **Interpretation guide (pre-named):** onset at M = structural displacement by ANY second
block → a layout/salience question, not fixable by wording; feeds the -B hollowness axis. Onset at
H = header semantics displace self-layer mention → any -D header edit must be watched on BOTH the
fence and self-layer-legibility axes. Onset only at C = format/length rung. No drop anywhere = F3
not reproduced → heterogeneity/instrument flag. **The M−H surfacing contrast is the registered
follow-up reading of BLOCK F2** (v2b header cut T1 surfacing 0.811→0.707 with adoption unmoved).

## 3. Judge protocol — one fresh session for all four arms (load-bearing)

The contrasts split BLOCK's +0.0755 into ≤3 parts, comparable to the ±0.05 cross-session
judge-drift tolerance — cross-epoch label pairing would swamp the decomposition. Therefore all four
arms are judged fresh in ONE session, with A and C **re-judged from their committed
byte-deterministic caches** (judging-only; no regeneration).

**"One session" (operational definition):** the four judge invocations run sequentially from one
script, **order a → m → h → c**, one host, target < 24 h start-to-finish, `ownership_judge` panel
constants byte-unchanged (slugs pinned in §9). The a→…→c order makes the A drift report a
start-of-window and the C drift report an end-of-window measurement — together they are the
within-window panel-stability receipt (no extra spend). **Interruption semantics:** the judge
refuses partial JUDGE writes; the per-arm stamp cache preserves completed calls, so resuming with
the SAME stamp replays identical labels — session identity is carried by the stamp caches + the
unchanged panel, not the clock. Cap-fire remedy = plain-dollar re-approval, raise `--cap`, re-run
the same stamp. A resume crossing the window or ANY panel change downgrades the epoch to
cross-session: disclose, and re-run the A-endpoint drift check before reading the ladder.

**Drift report (replaces J0 this epoch):** committed-vs-re-judged A and C, fillers AND T1, pooled Δ
(warn ±0.05) + flips over MUTABLE rows only (non-ABSENT on either side — ABSENT rows are
regex-deterministic and cannot flip). It calibrates prior-epoch comparisons; the within-ladder
contrasts do not depend on it by construction.

**Interlocks (wired into analyzer verdicts, smoke-tested pre-lock):** arm-slot identity — every
input file (fresh AND committed) must carry its expected machine arm label ({a: filler,
m: fixture_m, h: fixture_h, c: worldblock}); a swapped file is a hard refusal (the red-team's swap
attack produced a confident wrong DISTRIBUTED ladder without this). G-AVAIL failure on a rung
forces WITHHELD-UNREAD on **both touching contrasts** and downgrades the summary.

## 4. Gates

G1 recall ≤ 0.05 per arm (all four; per-model breach lines printed — a mythos 2/16 must not hide in
a pooled rate); **G-ADOPT** on the re-judged A (pooled ≥ 0.05 ∧ LB95 > 0 — else the run is
WITHHELD; the mech anchor passed at 0.110 in BLOCK, so failure here would itself be judge-drift
evidence); **G-AVAIL** block-fact recall surfacing ≥ 0.30 for each of M/H/C (empirical reference:
C reads 0.676, A's persona-block 0.790); **G-FACET** identical open-SP facet sets. Distill cell:
G-ADOPT is expected to fail on the distill anchor (0.048 — known at lock, as in BLOCK) → distill
adoption WITHHELD, descriptive only; distill **recall** rows are the -D-relevant discovery channel
(mythos qualification note in force — extends BLOCK F4 to the M/H surfaces).

## 5. Power (committed sim: `blockframe/disambig_power_sim.py`; empirical anchor profile, uniform
multiplicative truth family, C endpoint at ×0.31; per-rung AND joint-summary OCs)

| truth (shares mem/hdr/fmt) | A−M | M−H | H−C | JOINT (top outcomes) |
|---|---|---|---|---|
| 1 / 0 / 0 | **DRIVER 1.00** | NULL 0.91 | NULL 0.88 | MEMBERSHIP-DRIVEN 0.86 (incl +REV 0.06); DISTRIBUTED 0.13 |
| 0 / 1 / 0 | NULL 0.87 | **DRIVER 1.00** | NULL 0.88 | HEADER-DRIVEN 0.87 (incl +REV 0.10); DISTRIBUTED 0.14 |
| 0 / 0 / 1 | NULL 0.87 | NULL 0.62 / UNRES 0.26 | **DRIVER 1.00** | FORMAT-DRIVEN 0.88 (incl +REV 0.07); DISTRIBUTED 0.12 |
| 0 / .5 / .5 | NULL 0.87 | DRIVER 1.00 | DRIVER 0.92 | DISTRIBUTED 0.92; false HEADER-DRIVEN 0.08 |
| ⅓ / ⅓ / ⅓ | DRIVER 1.00 | DRIVER 0.77 | DRIVER 0.63 | DISTRIBUTED 0.96; false single-lever 0.04 |
| .2 / .6 / .2 | DRIVER 0.86 | DRIVER 0.99 | DRIVER 0.32 | DISTRIBUTED 0.90; HEADER-DRIVEN 0.10 |

Calibration carried inline with any claim: correct single-lever verdict ≈ 0.86–0.88 with
false-DISTRIBUTED ≈ 0.12–0.14 (conservative direction); under distributed truths, false
single-"X-DRIVEN" ≈ 0.04–0.10; **false-REVERSED ≈ 0.04–0.07 per null rung** (any §8 REVERSED
hazard flag carries this rate). Structural disclosure: multiplicative interpolation gives later
rungs smaller ABSOLUTE deltas for equal log-shares — resolution declines down the ladder (H−C is
the hardest rung; a small format share honestly lands UNRESOLVED/NULL).

## 6. What this can and cannot license

CAN: attribute the composite's reduction among the three BUNDLES (or honestly fail to, per rung);
answer whether the -D header semantics specifically carry the fence (M−H, the one clean rung);
locate each bundle on the surfacing-vs-ownership axis (mechanism prose); extend the T1
salience-displacement observation to per-rung onset.
CANNOT: **isolate length anywhere on the ladder** (it enters A−M as +448 B and H−C as −181 B; the
charter's "length" axis is delivered only inside these bundles — DISAMBIG_RESULTS must not claim
length was ruled out or bounded); decompose within bundles (position within membership; clauses vs
hint vs label within header; **format vs length vs fact-line subject** within the last rung);
certify fence-grade anything (BLOCK's verdict stands); generalize beyond mech-11, this fixture
family, 2 dependency-fact fillers, temp-0, the adoption prong.

**Pre-named DISAMBIG_RESULTS qualifier block (inherited, not re-derived):** adoption prong only;
mech-11 decision-bearing (distill withheld-at-lock); one fixture family, M/H constructed
intermediates (not -D surfaces; H unreachable by any -D configuration); 2 coined dependency-fact
fillers; temp-0; render-surface only (no live -D session); per-rung bundles as §1; verdicts
marginal-basis only; cross-epoch comparisons only via the drift report.

## 7. Pressure-test record (rule 12 — completed 2026-07-10, two adversarial agents, pre-lock)

**Red-team (MUST_FIX, all folded):** M1 G-AVAIL→WITHHELD-UNREAD interlock was dead code in the
draft analyzer (a regression of BLOCK's own legituse-M2 fix) — wired into verdicts, smoke-tested
(a G-AVAIL-failing M withholds A−M AND M−H and downgrades the summary). M2 arm-slot identity —
the demonstrated swap attack (C file as `--m`) produced a confident wrong DISTRIBUTED ladder;
per-slot machine-label asserts added for fresh AND committed inputs, smoke-tested (loud refusal).
M3 length structure — +448 B on A−M / −181 B on H−C was undisclosed and a pure-length channel
masquerades as MEMBERSHIP-DRIVEN; per-rung byte deltas + bundle renames + the pre-named
length-consistent-signature flag added (§1/§2/§8 + analyzer). SHOULD_FIX folded: full M−H bundle
enumeration incl. the user→project attribution change (S1→§1); H−C fact-line subject flip added to
the bundle (S2→§1/§6); cost numbers reconciled (A = 2,364/2,283 jobs) + cap raised to $14 with the
worst-case arithmetic + cap-fire recovery (S3→header); joint-summary + false-REVERSED calibration
added to the sim and §5 (S4); panel slugs pinned (S5→§9); the secondary per-contrast bootstrap
implemented in the committed analyzer (S6, = legituse M4); judge order a→m→h→c as the
within-window receipt (S7→§3); drift extended to T1 + flips over mutable rows only (S8).
NOTEs adopted: DRIVER-before-NULL precedence disclosure (§2); share suppression when the total is
not a DRIVER (analyzer); M-header semantics disclosure (§1). Survived the red-team's attacks:
judge-cache tautology (per-stamp cache dirs — the fresh session is real), fixture byte-integrity,
CRLF/transfer chain, joint-bootstrap validity, p/3 band consistency, vendor self-exclusion.
**Legitimate-use (MUST_FIX, all folded):** M1 = red-team M1. M2 = the length mis-disclosure
(= red-team M3). M3 "one session" operationally defined + interruption/cap-fire semantics (§3).
M4 secondary machinery committed pre-lock + the basis→conclusion mapping registered (§2).
SHOULD_FIX folded: MEMBERSHIP-DRIVEN scope vs BLOCK F2 (S1→§8); FORMAT-DRIVEN re-aimed at importer
hygiene, -D renderer structurally incapable, H models import-time contamination (S2→§1/§8);
HEADER-DRIVEN register dependency + named guarded surface (S3→§8); T1 interpretation guide +
adjacent contrasts + F2 loop-closure registration (S4→§2 + analyzer); analyzer ergonomics — BOTTOM
LINE, per-model recall lines, +REVERSED summary annotation (S5); pre-named results qualifier block
(S6→§6); Nate line + panel slugs + job-count reconcile (S7). Verified sound: charter match (with
the length caveat), telescoping construction, cost arithmetic, launcher/lock plumbing,
drift-replaces-J0 design.

## 8. Outcome → follow-on matrix (pre-registered)

| outcome | licenses / follow-on |
|---|---|
| HEADER-DRIVEN | the de-attribution language is the lever → the -D header literal (`session.py` `_assemble_snapshot`) becomes a guarded surface: numbered-exposure register entry (register opening already queued as BLOCK follow-on #3; this entry lands there once open) prescribing a byte-pin test in -D; header edits are fence-relevant. Within-bundle split (clauses vs tool hint vs label) = Josh's call, only if a deployment decision needs it |
| MEMBERSHIP-DRIVEN | structure is the lever → header wording is free **for the adoption estimand at this resolution only; BLOCK F2's surfacing-axis wording effect stands unretired**. Position-vs-block-exit-vs-length split becomes the next question ONLY if -D layout changes are planned. Carries the length caveat: the A−M bundle includes +448 B — check the length-consistent-signature flag before reading membership |
| FORMAT-DRIVEN | the persona support/exemplar render is the adoption carrier → **importer hygiene gains a concrete rule: strip/flag persona-format support/exemplar markup in ingested world text (fact strings and overview bodies — the Hermes-seed contamination class); -D's fact renderer is already structurally incapable of emitting it** |
| DISTRIBUTED | no single guarded surface; the composite as a whole is the fence → -D must not relax ANY ingredient without re-measurement; exposure register entry says exactly that |
| UNRESOLVED-SPLIT | power-limited → report shares with CIs, no lever claim; escalation to a powered single-contrast run is a NEW prereg and needs a stated deployment question |
| LADDER-NULL | instrument instability — halt interpretation, investigate drift report + audit before anything else |
| any REVERSED rung | report prominently (with the §5 false-REVERSED rate ≈ 0.04–0.07 inline); a resolved rung that increases adoption is a new hazard finding → flag to -D immediately |
| length-consistent signature (A−M DRIVER + H−C negative-leaning) | flagged by the analyzer; read as length-channel-consistent, NOT membership; the length thread (formally OPEN since padding) becomes the licensed follow-on |

## 9. Locked manifest

Fixtures + shas as §1; driver `--scaffold-fixture {m,h}` (mutex, v1-only); judge
`--scaffold-fixture {m,h}` (arm labels `fixture_m`/`fixture_h`, tokens T1+FILLER); analyzer
`tools/disambig_analyze.py` (constants: NULL_BAND 0.037, T1_BAND 0.071, AVAIL_FLOOR 0.30,
DRIFT_WARN 0.05; interlocks: arm-slot asserts, G-AVAIL→WITHHELD-UNREAD, share suppression,
length-signature flag, BOTTOM LINE); judge stamps `disambig_{a,c,m,h}`, order a→m→h→c, caps
$14/arm; **A′ panel pinned at lock:** claude=anthropic/claude-haiku-4.5,
gemini=google/gemini-2.5-flash, gpt=openai/gpt-4o-mini, deepseek=deepseek/deepseek-v3.2,
mistral=mistralai/mistral-small-3.2-24b-instruct (subject self-family exclusion in force — any
change downgrades the epoch to cross-session, §3); fresh timestamped caches
`~/cdms_cache/disambig_{m,h}_<ts>`; launcher `gen_sweep/cdms_disambig_gen.sh` (GIRAFFE gate,
fixture sha+layout asserts on the generation host, C-regeneration sentinel = 2 mech models
byte-diffed vs the committed `blockframe_c` cache); roster = the standing 16 (mech-11
decision-bearing); bank = sp-expansion (31 facets, 25 open-SP). Analyzer smoke-tested pre-lock on
committed stand-ins + synthetic relabeled files: drift self-test Δ=0.0000 (flips 0/750 and 0/446
mutable), telescoping total reproduces +0.0755, secondary per-contrast bootstrap live, swap attack
refused, WITHHELD-UNREAD path exercised.
