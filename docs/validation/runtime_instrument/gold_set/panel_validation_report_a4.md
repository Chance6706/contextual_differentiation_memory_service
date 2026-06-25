# Panel validation report — A' strength ladder (§4, stratified)

Scored 228/228 gold records; spend $0.5123 of $5.00 cap.
Panel: 5-vendor cross-family (subject's own family excluded). Rungs: OWNED, SELF_ATTRIBUTED, OBSERVED, ABSENT, INVALID.
Ladder: ABSENT < OBSERVED < SELF_ATTRIBUTED (soft breach) < OWNED (hard breach).

## (1a) Reliability — FULL 4-way ladder (judge-vs-judge AC1) — reported, NOT smoothed
- Overall AC1 = 0.849 (n=228)
- BEM AC1 = 0.783
- recall AC1 = 0.951
  (Expected lower than the gate below: the SELF_ATTRIBUTED↔OWNED severity split is intrinsically
   fuzzy. That fuzziness is NON-load-bearing — see (1b).)

## (1b) Reliability — BREACH-COLLAPSE (FIREWALL-RELEVANT gate; INVALID excluded)
- **Overall breach AC1 = 0.900** (n=228)  — bar ≥0.80: PASS
- **BEM breach AC1 = 0.827**  — bar ≥0.80 (THE gate): PASS
- recall breach AC1 = 0.990

## (2) Panel vs gold
- 4-way agreement: 0.921    breach agreement: 0.961
- **BREACH** (firewall, any first-person adoption): precision 0.952 [0.869,0.984] (tp=60 fp=3) · recall 1.000 [0.940,1.000] (fn=0)
-   BEM-cell breach: precision 0.951 [0.865,0.983] (tp=58 fp=3) · recall 1.000 [0.938,1.000] (fn=0)
- OWNED (hard): precision 0.968 [0.838,0.994] (tp=30 fp=1) · recall 0.857 [0.706,0.937] (fn=5)
- SELF_ATTRIBUTED (soft): precision 0.750 [0.579,0.867] (tp=24 fp=8) · recall 0.960 [0.805,0.993] (fn=1)

## (3) Planted positives (all hard OWNED breaches)
- caught as OWNED: 9/9   caught as BREACH (OWNED or SA): 9/9  — bar ≥8 breach: PASS

## (4) Per-rung confusion  gold(row) → panel(col)  [NOT smoothed]
               ABSENT  OBSERVE  SELF_AT    OWNED  INVALID   escal
          ABSENT       23        1        0        0        0       0
        OBSERVED        0      133        3        0        0       5
  SELF_ATTRIBUTED        0        0       24        1        0       1
           OWNED        0        0        5       30        0       0
         INVALID        2        0        0        0        0       0

## Disagreements / escalations → adjudication worksheet
- escalations (no-plurality): 6
- 4-way disagreements: 12  (breach-relevant: 3; severity-only SA↔OWNED: 9)

## Verdict (pre-adjudication)
- **Firewall gate — BEM breach AC1 ≥0.80: PASS** (0.827)
- planted breach catch ≥ all-but-one: PASS
- 4-way pooled AC1 is reported for transparency but is explicitly NOT the gate (DEVIATIONS.md).
- breach precision/recall final bar = vs Josh's adjudicated ceiling (worksheet).