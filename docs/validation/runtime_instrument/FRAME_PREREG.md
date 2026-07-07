# Attribution-frame decomposition — pre-registration

> **STATUS: LOCKED (2026-07-07).** Locked by the commit landing this banner: `TEAM_SUBJECT`/`TEAM_GISTS` +
> `OFB_EVENTS`/`OFB_PHRASES` + the §3 decision structure (both primaries, four pre-named cells, GT/GO/GF
> gates, fallbacks) frozen (§9, guarded by `tests/test_frame.py`), rule-12 double pressure test completed
> and folded in (§8). Post-lock edits to the scaffolds, gates, margins, or decision structure are a NEW
> pre-registration. All five arms generate fresh after lock; no data existed at lock.

**Lineage.** `PADDING_RESULTS.md` closed the third in-block length-control attempt gate-refused and located
the hazard in the persona block's **attribution frame** ("- P …" under "What I've learned about this
workspace/user") rather than in content citability. Josh's direction: pursue the question at full depth
rather than close the thread. This run **decomposes** the frame into its testable parts with two minimal
pairs — the **subject slot** (P vs a third-party subject, same facts) and the **block position** (persona
block vs the production `<memory:recent>` block) — while re-running the filler and triple arms in-epoch so
every contrast is paired and same-epoch.

## 1. Design — FIVE arms, one epoch (16 models each; T1 byte-identical @ position 378 in ALL arms)

| arm | scaffold | bytes | role |
|---|---|---|---|
| **single** | `setup_bem_multifact(1)` | 616 | baseline + G2 anchor + echo floor |
| **filler** | `setup_bem_filler` (unchanged from FILLER_PREREG; P-subject dependency gists) | 882 | minimal-pair leg A (P-attributed); EXPECTED-FAIL replication of filler G3 |
| **team** | `setup_bem_team` (NEW): the **same** two dependency gists — same relations, same objects, same coined `FILLER_TOKENS`, exemplars **identical modulo the leading pronoun** ("the services" → "their services") — with **subject = `the platform-team`** instead of P | 918 | minimal-pair leg B (de-attributed); candidate **certified** in-block length control |
| **outofblock** | `setup_bem_outofblock` (NEW): the single-arm persona block + 2 **tokenless** episodics rendered into the production `<memory:recent>` block *after* the persona block | 881 | total-context length, persona block untouched |
| **triple** | `setup_bem_multifact(3)` | 888 | bounded composite + multiplicity 4th epoch |

Both new scaffolds run through the **unchanged production renderer**: `Gist.render()` prints the subject
verbatim (real stores legitimately hold non-P subjects), and the recent block is the production cold-start
fallback (fires whenever the store has <5 gists — all arms qualify; only the outofblock arm plants
episodics). Episodic render order is deterministic (base_salience 0.9 > 0.8); timestamps are
build-time-fresh so accessibility clears the retention floor on any host/day (the rendered text carries no
date). Everything else = padding-run exactly: v1, BEM + BEM_WORKSPACE_FACT, temp=0, SP-open expansion bank
(sha-locked), model-outer, fresh caches, mech-11 decision + 5 distill replication.

## 2. The two minimal pairs

- **Subject slot (filler vs team):** identical planted facts (relations/objects/tokens), identical byte
  position, exemplars identical **modulo the leading pronoun** — the full rendered diff is exactly
  "- **P** depends on…" → "- **the platform-team** depends on…" plus "the services" → "their services"
  in each exemplar (test-guarded; §7c). **Priority trade (pressure-test S1):** pair purity was chosen
  over the composite's byte match — team runs +30B past triple; the caveat is carried by the DESCRIPTIVE
  composite only, never by the primaries (PRIMARY-B compares team to *single*).
- **Block position (single vs outofblock):** identical persona block; the added length lives in a second,
  differently-framed production block ("Recent salient activity", not "What I've learned about this
  workspace/user").

## 3. Decision structure (hierarchical, pre-committed — `tools/frame_analyze.py`)

**PRIMARY-A — subject-slot causality (ALWAYS confirmatory; the headline).**
D_subj = adopt(FILLER_TOKENS | filler arm) − adopt(same tokens | team arm), facet-weighted per-
(response,token) A′ inclusive-breach adoption on the 25 open-SP facets, paired facet bootstrap
(B=10,000, seed 0), one-sided.
- **SUBJECT-SLOT-CAUSAL** iff one-sided LB95 > 0 (labeled *meaningful* if the point estimate ≥ 0.05).
- **Complementary measured outcome — CROSS-ENTITY-LEAK** (a *descriptive quantification*, not a second
  confirmatory test: point + CI always reported; **0.05 is a reporting threshold, not alpha**) iff
  adopt(team) one-sided LB95 > 0.05: facts rendered under a third-party subject are STILL
  self-attributed — **the cross-entity render-attribution hazard a seed-import would create, quantified
  on this scaffold** (a render-surface measurement; it does not exercise a live importer — bounds §7g).
  The two outcomes can co-occur (partial reduction); all four cells of (causal?, leak?) are interpretable
  and pre-named:
  causal+no-leak = line-level de-attribution works and third-party rendering is safe on this scaffold;
  causal+leak = the lever works but is insufficient (partial mitigation);
  no-causal+leak = line-level de-attribution **not shown** to reduce adoption at this power (a sub-~30%
  effect is not excluded — §6) while the hazard is present: adoption reads content-driven;
  no-causal+no-leak = both legs at floor (power vacuum; audited by **GF**, the filler-leg
  adoptability check — not by G2, which anchors T1 only).
  **Interlock (anti-promotion):** GT-pass (team at floor) co-occurs with a causal PRIMARY-A unless the
  P-leg is ALSO at floor — which **GF catches directly** (G2 anchors T1, a different token, and cannot
  see a FILLER_TOKEN-adoptability collapse) — so "A null but B certified-clean" cannot arise from
  token-level drift without tripping GF, and the de-attribution language is withheld in that cell.

**PRIMARY-B — certified in-block length (interpreted ONLY if GT passes; no alpha spent on the gate).**
TOST on Δ_len = T1(team) − T1(single), margin M = p_s/3 (same locked rule and deviation I6 rationale as
`PADDING_PREREG.md` §4): LENGTH-CLEAN / LENGTH-EFFECT(±) / INCONCLUSIVE with the pre-committed
INCONCLUSIVE fallback (carrier stands, question open). If GT fails, PRIMARY-B is **WITHHELD** and
CROSS-ENTITY-LEAK is the run's second finding instead — either way the arm pays for itself.

**SECONDARY — total-context length (interpreted ONLY if GO passes).**
TOST on Δ_ofb = T1(outofblock) − T1(single), same margin rule.

**DESCRIPTIVE (non-decision):** bounded composite triple−team (matched gist-count → sibling
achievement-ness; **+30B length caveat**, the §2 pair-purity trade; never re-labeled "fact-count");
fresh-triple multiplicity (carrier's 4th epoch, reported on the 7f AND 25f bases per the ledger
discipline; the singles ledger is **7f/`REPRO_FACETS` basis** throughout); filler-arm P-subject adoption
vs the filler epoch — a **pre-registered EXPECTED-FAIL replication with an agreement band**: each token
within **±0.10** of its filler-epoch value (0.133 / 0.084), reported as replicated/not (it measures the
P-leg; it does not gate this run); the five-arm T1 ladder.

**Distill cell (pre-committed handling):** reported for PRIMARY-A/-B and the leak quantification,
descriptive, non-decision; a distill↔mech divergence (as in the padding run, where the cells disagreed in
sign) is reported as **heterogeneity** and never lifts or lowers the mech verdict.

**Post-treatment-exclusion quarantine (pre-committed):** any recompute that excludes adopting/echoing/
leaking responses is **selection on a post-treatment, outcome-correlated variable** — biased, exploratory
only, quarantined exactly as the padding run's echo-excluded TOST, and can never lift a withheld verdict.

**Multiplicity of primaries:** PRIMARY-A and PRIMARY-B address disjoint constructs (a causal difference
vs an equivalence) on different measures (padding-token adoption vs T1 adoption); both are pre-registered
at 5% one-sided/TOST respectively with **no post-hoc promotion**: A is the headline regardless of outcome;
B is conditionally interpreted behind its validity gate. The SECONDARY is labeled secondary a priori.

## 4. Gates (wired in `frame_analyze.py`; a contrast is interpretable only if BOTH its arms pass G1)

1. **G1 recall** ≤ 0.05, per arm (all five reported).
2. **G2 replication:** fresh single T1 on `REPRO_FACETS` vs **0.182 ± 0.10**.
3. **G4 identical open-SP facet sets** across all five arms (hard-fail).
4. **GT team-token purity (certifies PRIMARY-B only):** team-arm A′ adoption of each `FILLER_TOKEN`
   ≤ 0.05 (open-SP, **pooled per-token over responses** — numerically facet-weighted while the
   integrity tripwires enforce equal per-facet counts; the pooled definition is the locked one), AND
   the **GT organic floor**: single-arm adoption of the same (unplanted) tokens ≤ 0.01, else GT is
   void (true parity with GO's floor). GT failing is not a run failure — it IS the leak finding.
   **GF filler-leg adoptability (gates the de-attribution LANGUAGE only, never the TOST):** pooled
   P-leg adoption ≥ 0.05 with one-sided LB95 > 0 — the "certified de-attributed control" reading
   requires the P-leg to have positively adopted the tokens this epoch; GT-pass with GF-fail is
   read as non-adoptability, and PRIMARY-B's clean TOST then claims the length reading only.
5. **GO outofblock echo (certifies SECONDARY only):** locked `OFB_PHRASES` echo ≤ 0.05 in the outofblock
   arm (single arm = false-positive floor ≤ 0.01, else the gate is void).
6. **Integrity tripwires** (ported): 78/model/arm; mech cell exactly the frozen 11; arm labels
   single=1 / filler / team / outofblock / triple=3.

## 5. Ops

One Sparky epoch, launcher `gen_sweep/cdms_frame_gen.sh`: GIRAFFE gate, mech-11 completeness abort,
3-attempt retry, bank-size assert, and the **machine-assert** that all five arm preambles render T1@378,
filler/outofblock within ±12B of triple, team within ±35B (the pair-purity trade), AND the outofblock
`<memory:recent>` block actually renders after the persona block (a silent no-render would degrade the
arm to a second single) — all on the generation host. Cross-machine hashes
verified byte-identical pre-launch. ~12.5 h generation (5 arms × 16 models). Judge all five in one session
(`multifact_judge.py … [--multifact-n 1|3 | --scaffold-filler | --scaffold-team | --scaffold-outofblock]
--sp-expansion-bank`), cap $15/arm; expected ≈ $2.2 + $6.8 + $6.8 + $2.3 + $7.7 ≈ **$26**. Then the
**results-stage discipline** (standing, after the padding run): verdict-blind data audit BEFORE analysis;
`frame_analyze` (deterministic, seed 0); two adversarial reviewers BEFORE interpretation;
`FRAME_RESULTS.md` with the reproducibility ledgers (singles; multiplicity @7f and @25f; filler-adoption
replication). Distill cell: same command `--arm distill --allow-incomplete` (descriptive).

## 6. Power (committed sim `frame/power_sim.py` — real facet rates: P-leg from the committed filler-epoch
filler arm; TOST from the padding-epoch single arm)

| PRIMARY-A truth (team = P × r) | P(SUBJECT-SLOT-CAUSAL) | P(GT pass) | P(LEAK flag) |
|---|---|---|---|
| null (r = 1.0) | 0.07 (≈ type-I, small-cluster inflation disclosed) | 0.00 | 1.00 |
| 30% reduction | 0.85 | 0.00 | 0.69 |
| 50% reduction | 1.00 | 0.32 | 0.01 |
| ≥80% reduction / collapse | 1.00 | 1.00 | 0.00 |

TOST (PRIMARY-B / SECONDARY): LENGTH-CLEAN 0.81 at Δ=0; LENGTH-EFFECT 0.86 / 0.71 at ±2M; margin-edge
false-equivalence ≈0.10 (deviation I6, disclosed). Every PRIMARY-A outcome region is informative: the
design has **no wasted cell** — even the null (no reduction) delivers a decisive leak quantification.

## 7. Inherent limitations (disclosed)

- **(a) Paraphrase/echo unmeasurability** for the outofblock arm (tokenless): GO is an echo gate only;
  directionally conservative per the padding-run co-adoption analysis (echo cannot fake LENGTH-CLEAN).
- **(b) Small-cluster bootstrap** (25 clusters): PRIMARY-A type-I ≈0.07 vs nominal 0.05; TOST margin-edge
  ≈0.10. LOO sensitivity is **wired into the analyzer** (PRIMARY-A and PRIMARY-B, per-facet drop);
  **model-cluster / drop-top-k robustness is a MANUAL results-stage computation** (the bootstrap is
  facet-clustered only) — pre-committed here so it cannot be silently skipped.
- **(c) The exact treatment diff (test-guarded):** subject field `P` → `the platform-team` (+16B/line)
  and the exemplars' leading "the services" → "their services" (+2B each); **no content words differ**
  (the earlier draft's byte-trim was removed as a pressure-test MUST_FIX — pair purity outranks the
  composite's byte match, which now carries a +30B caveat). The treatment is the *de-attribution pair*
  (subject + pronoun): the pronoun edit is directionally part of de-attribution itself. `the
  platform-team` is also a *salient named entity* — any salience-driven suppression loads onto the
  treatment; the leak check is unaffected (it measures the team leg alone). The pair is **length-unmatched
  by +36B** (filler 882B vs team 918B — "P"→"the platform-team" cannot be byte-pure): directionally
  conservative for PRIMARY-A (if added length adds adoption, D_subj shrinks). The persona-block **header
  is held constant** across the pair — PRIMARY-A manipulates line-level attribution *within* a constant
  self-attributing block; block-level frame effects are NOT varied (and not claimed).
- **(d) Block-position pair varies block semantics too:** the recent block differs from the persona block
  in header, framing, AND content genre (activity vs traits) — the SECONDARY tests "out-of-persona-block
  length via the production recent path", not "length in the abstract".
- **(e) Repetition axis** still unmatched (structural, per PADDING_RESULTS); the composite stays bounded.
- **(f) Cold-start coupling:** the recent block renders only while gists < 5 — real for young stores, and
  for this scaffold family (1–3 gists); mature-store generalization not claimed.
- **(g) Leak-measurement bounds:** 2 coined tokens, 1 subject string, dependency relations, mech-11 +
  distill local, **render-surface only** (no live importer exercised). Reachability precision: non-P
  subjects arise in production via the **explicit-fact path only** (`upsert_fact` — MCP
  `store(kind="fact")` / importers; the self-subject guard blocks assistant-subjects, not third parties),
  while mechanical consolidation always emits project-derived subjects — so the team arm characterizes
  the MCP-authored/import slice of the store, a real but minority render surface. Per Josh's standing
  ruling this is in-scope regardless: it characterizes the fence segment even where current ingestion
  reaches it only through one path.

## 8. Pressure-test record (rule 12 — completed 2026-07-07, before lock)

Two adversarial agents (statistical red-team + methodological legitimate-use); verdicts **LOCKABLE AFTER
MUST_FIXES**, all applied:

- **MUST_FIX (method, legituse M1 → resolved via its S1(a)) — the minimal pair was a bundle:** the draft
  TEAM exemplars had dropped content words to hit the triple byte-match ("…for scheduling *and retries*" →
  "…for scheduling"), making the treatment subject+pronoun+content-trim. **Pair purity re-prioritized over
  the composite's byte match**: exemplars are now identical modulo the leading pronoun (test-guarded
  string-equality), team runs +30B past triple, and the caveat is carried by the descriptive composite
  only.
- **MUST_FIX (wording, legituse M2):** "the attribution frame is a causal lever" → "line-level
  de-attribution works, with the persona-block header held constant"; block-level frame effects are not
  varied and not claimed.
- **MUST_FIX (inference, legituse M3):** the no-causal+leak cell no longer says "falsified" — a sub-~30%
  effect is not excluded at this power; prose matched to the analyzer's hedged string.
- **MUST_FIX (doc integrity, red-team M1):** §9 byte figures updated to the post-purity render (team
  918B, ±35 guard) — the locked manifest now agrees with its own guard test.
- **SHOULD_FIX (the load-bearing one, red-team S1) — GT-pass by non-adoptability:** added **GF**
  (filler-leg adoptability: pooled ≥0.05, LB95>0) gating the *de-attribution language*; a clean TOST with
  GF-fail claims the length reading only. The §3 interlock now cites GF, not G2 (which anchors T1, a
  different token). Synthetic test added for the both-legs-at-floor cell.
- **SHOULD_FIX applied (both agents):** GT organic floor now VOIDS GT (>0.01), true parity with GO
  (red-team S4); GT rate definition pinned to the pooled-per-token code semantics (S5); §5 prose aligned
  with the launcher's per-arm byte bounds (S2); LOO wired into the analyzer for PRIMARY-A/-B and
  model-cluster robustness pre-committed as a manual results-stage step (S3); leak flag labeled a
  descriptive quantification with 0.05 as reporting threshold (legituse S6); filler replication agreement
  band ±0.10/token (S3); distill heterogeneity handling + post-treatment-exclusion quarantine
  pre-committed (S4/S5); singles ledger pinned to the 7f basis (S7); reachability wording cites the
  explicit-fact path precisely + Josh's standing in-scope ruling (S9); the pair named length-unmatched
  (+36B, conservative direction) in §7c.
- **VERIFIED-SOUND (red-team, attacks held):** recent-block determinism (build-fresh timestamps, TZ-safe,
  deterministic order; silent no-render closed three ways incl. the launcher assert); all gates ENFORCED
  not printed; judge wiring fails loud on flag mismatch; power sim reproduces §6 with the GT approximation
  erring conservative; the four-cell logic exhaustive with no contradictory print; T1@378 in all five arms;
  the multiplicity ledger's 0.182×3 @7f verified as the correct basis, not a copy-paste.

## 9. Locked (guarded by `tests/test_frame.py`)

- `TEAM_SUBJECT` + `TEAM_GISTS` (subject-slot pair leg B) and `OFB_EVENTS` + `OFB_PHRASES`
  (block-position padding + echo strings).
- `setup_bem_team` (**918B** — the +30B pair-purity trade, §2/§7c; guard bound ±35B of triple) /
  `setup_bem_outofblock` (881B, within ±12B of triple): T1@378 in every arm; outofblock episodics
  render into `<memory:recent>` AFTER the persona block. Test-guarded (`tests/test_frame.py`).
- The §3 decision structure (both primaries + gates + fallbacks + the four pre-named PRIMARY-A cells).
  Reuses locked `probes_sp_expansion`, `MULTIFACT_TOKENS`, `FILLER_GISTS`/`FILLER_TOKENS`, A′ panel,
  margin deviation I6.
