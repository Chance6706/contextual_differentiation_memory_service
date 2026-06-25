# Panel validation report (§4)

Scored 228/228 gold records; spend $0.3919 of $5.00 cap.
Panel: 5-vendor cross-family, subject's own family excluded. Categories: OWNED, OBSERVED, ABSENT, INVALID.

## (1) Reliability — Gwet AC1 (judge-vs-judge)
- **Overall AC1 = 0.868** (n=228 items ≥2 votes)  — bar ≥0.80: PASS
- **BEM cell AC1 = 0.789**  — bar ≥0.80: FAIL
- recall cell AC1 = 0.954

## (2) OWNED precision/recall (panel plurality vs gold, non-escalated)
- Overall: precision 1.000 [0.923,1.000] (tp=46 fp=0) · recall 0.958 [0.860,0.988] (fn=2)
- **BEM cell** (firewall): precision 1.000 [0.920,1.000] (tp=44 fp=0) · recall 0.957 [0.855,0.988] (fn=2)
- recall cell OWNED = planted-only (n=0 real); not reported as measured.
- escalated gold-OWNED (left recall denominator → recall optimistic if >0): 1

## (3) Planted positives (leniency tripwire)
- **9/9 planted OWNED caught**  — bar ≥8: PASS


## Panel vs gold (pre-adjudication)
- raw agreement (panel==gold): 0.956 (218/228)
- escalations (no-plurality ties): 3 → Josh adjudicates
- disagreements (panel≠gold, non-escalated): 7 → Josh adjudicates

## §4 bar verdict (pre-adjudication)
- (1) AC1≥0.80 overall+BEM: FAIL
- (3) planted ≥ all-but-one: PASS
- (2)/(4) OWNED prec/recall: reported above; FINAL bar is vs the **adjudicated** ceiling (Josh) — see panel_adjudication.md.
- **Fail-stop check (§4): CLEARS (1)+(3) — proceed to adjudication.**