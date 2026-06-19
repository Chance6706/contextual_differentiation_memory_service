# Steering Experiment (L1) — Design v2

_Does injecting an **enriched CDMS phenotype** into a live model change its **behavior**,
idiosyncratically, in the direction its history predicts? This is the first test of the memory's
**effect**, not its form — everything prior validated the artifact (the phenotype); this measures
the consequence._

> Status: **design, pre-build — REVISED after Stage-0 + a 3-model review (2026-06-19).** Runs against
> the enriched phenotype on branch `claude/proto-rich-tuples` (exemplars + flashbulb scars). P3
> (decoding/cache) and P4 (heretic coherence) settled; Stage-0 run. The revisions below changed the
> **probe philosophy** and **demoted the heretic arm** — read that section first.

---

## Stage-0 + 3-model review — key revisions (2026-06-19)
**Stage-0** (gemma-std, greedy, DATA-injection, 3 probes): steering is **real** — the model
demonstrably reads and uses the phenotype (tessa recited its rules *"never merge red"/"always
pytest"*; cole invoked its force-push **scar**). **But** the clean same-domain pair barely moved:
dex (struggler) ≈ baseline; on *"found a bug"* baseline/cole/uma/dex gave near-identical *"reproduce
first"* answers. Non-obvious bonus: **cole's scar steered toward *caution*** (avoid the past
disaster) — a guardrail trumps disposition on its own axis.

**A 3-model review** (gemma-std, heretic, phi4; deepcoder returned nothing — coder, not a judge)
**converged on three corrections, which this spec adopts:**
1. **dex≈baseline is a PROBE problem, not (mainly) an RLHF-floor problem.** The probes have an obvious
   correct SOP (*"reproduce the bug"*), leaving no room for disposition. → **dispositional steering is
   UNTESTED, not "weak."** (The earlier baseline-bias attribution was overstated.)
2. **Fix = conflict / forced-tradeoff probes** with no single correct answer, so latent temperament
   must break the tie. *Central revision — see the new probe battery.*
3. **Demote the heretic arm.** Abliteration is a "blunt instrument" that removes safety rails, **not a
   disposition unlock** — *the heretic model said this of itself.* It becomes a confounded secondary,
   run only after conflict-probes test disposition on the standard model.

*(Caveat: the two gemmas share a family; phi4's independent corroboration is what makes this solid.)*

_Raw evidence: [`docs/validation/steering_stage0/`](validation/steering_stage0/) — the Stage-0 + P4
run and the verbatim 3-model review._

## Hypotheses (pre-registered)
- **H1 (recall steering — CONFIRMED in Stage-0):** the model reads and acts on explicit injected
  content (rules, guardrails/scars, topic). Strong; the enrichment (exemplars/scars) drives it.
- **H2 (dispositional steering — THE claim, currently UNTESTED):** on **conflict probes with no
  correct SOP**, dex-memory and uma-memory steer the same prompt **differently**, in the
  history-predicted direction — latent temperament breaks a tie that explicit rules don't decide.
- **H0 (null):** a response under persona-X's memory is no more X-typical, and no more identifiable
  to X, than under a length-matched **scrambled** control. **Refuting H0 is the win condition; failing
  to is a real, recorded negative.**

Primary endpoint: **behavioral-direction delta (dex vs uma) on CONFLICT probes**, scored by the
**behavioral rubric** (Stage-0 showed keyword tallies are noise), greedy, pre-registered before Stage 1.

## Model roster
| Model (ollama tag) | Role |
|---|---|
| `gemma4:12b` | **primary subject** (standard, aligned) |
| `igorls/gemma-4-12B-it-heretic-GGUF` | **secondary, CONFOUNDED contrast** — abliteration removes safety rails, it is *not* a disposition unlock (the 3-model review, incl. the heretic itself, said so). Run only AFTER conflict-probes test disposition on the standard model; interpret any delta cautiously (noise vs. genuine unlock). |
| `phi4:14b-q4_K_M` | **breadth subject** + **primary cross-family judge** (independent lineage → relieves "same brain judging itself", P5; gave the most useful Stage-0 review). |
| `deepcoder:latest` | **breadth SUBJECT only** — returned nothing usable as a reviewer/judge (coder model); use as a steering subject, never a judge. |

Breadth matters: if the phenotype steers *multiple families*, "memory steers a model" generalizes beyond a Gemma quirk (partially relieves external-validity, P8). Subjects run in stages (Gemma first); judging is **cross-family** (a model never judges its own family's outputs).

## Factors (staged factorial)
- **Condition:** `{none, dex, uma, scrambled, mismatched}` — primary disposition pair **dex/uma**
  (same Unity domain, opposite temperament — the only clean disposition isolation). tessa/cole added
  only as a *topic* contrast.
- **Injection site:** `{fenced DATA (mirrors the real hook), system message (steers harder)}`.
- **Subject model:** the roster above.
- **Decoding:** primary **greedy (temp=0, K=1)**; variance check **temp=0.7, K=5** on a subset.

**Staging (to control ~10 s/gen cost):**
- **Stage 0 — smoke (~3 min):** dex/uma/none × gemma-std × DATA × ~5 probes, greedy. *Does it move at
  all, in-direction?* Plus read whether responses differ in **what they do**, not just tone (P1).
- **Stage 1 — primary (~20 min):** full conditions × full probe battery × gemma-std × DATA × greedy.
  The headline numbers + a temp=0.7 K=5 variance check on the dex/uma decision probes.
- **Stage 2 — factorial (hours, staged):** add heretic + system-message + phi4/deepcoder. The
  contrast/breadth arms.

## Probe battery (held-out; CONFLICT-first — the Stage-0/review revision)
Stage-0 proved the old "neutral decision" probes fail: they have an obvious SOP (*"reproduce the
bug"*), so every persona converges and disposition can't surface. The battery is now **forced
tradeoffs with no single correct answer**, so latent temperament has to break the tie:
- **Conflict / tradeoff (core):** *"10 minutes before the deploy window closes — fix the bug properly
  or ship the workaround now?"* · *"CI is red on a test you believe is flaky and unrelated — block the
  release or merge?"* · *"You can ship today by skipping the test you'd normally write, or slip a day —
  which?"* A careful self pays the time cost; a fast/struggler self takes the shortcut. **No SOP
  resolves these; disposition does.**
- **Forced-choice + free-form twin:** each tradeoff also asked as *"A or B? one line why"* (categorical
  DV) paired with its free-form version — agreement validates the constrained measure (P7).
- **Topic (separate, weak claim):** domain-touching probes → recall-steering, reported apart.

Keep the dex/uma probes **domain-neutral** so re-ID/direction can't be won on Unity vocabulary (P6).

## Measurement — triangulated (dual judge + deterministic)
1. **Behavioral-direction (PRIMARY for H2):** blind rubric — *did the response exhibit X's predicted
   behavior?* — scored by **both** a cross-family LLM-judge (blind to condition + memory) **and** a
   deterministic keyword/embedding rubric. `mismatched` must score ~0 in the wrong direction.
2. **Blind re-identification (omnibus):** judge recovers which persona produced each response;
   permutation test vs `1/N`. *Supporting, not primary* — re-ID can be won by self-description or
   topic echo; only the same-domain dex/uma pair makes it disposition-not-topic.
3. **Magnitude (existence floor):** response-embedding cosine divergence vs `none` (CDMS's own
   embedder, deterministic). `real > scrambled` proves **content** matters, not length.

The deterministic rubric/embedding measures are the **trustworthy anchor**; the LLM-judge adds
richness but is cross-family + blinded to limit shared-prior bias.

## Determinism & caching (settled by P3)
P3 result: ollama does **not** reproduce output for a fixed seed at temp>0 (same seed → different
output); **temp=0 greedy IS deterministic**; ~9.6 s/gen.
- **Primary = greedy (temp=0, K=1):** deterministic, bit-reproducible, exactly replayable.
- **Variance check = temp=0.7, K=5** on the dex/uma decision subset (confirms greedy isn't brittle).
- **Cache = content-addressed**, key `(model, phenotype_hash, probe_id, condition, site, temp,
  sample_idx)`. At temp=0 the cell is exact-replay; at temp>0 the cache **stores the sampled
  outputs** (resume-only — a missing cell regenerates fresh, never bit-identical). No seed-replay.

## Falsification (decided before running)
- dex-vs-uma behavioral-direction delta ≈ 0 → **dispositional steering refuted**.
- `real ≈ scrambled` divergence → **content irrelevant** (only "some text" mattered).
- steering only on topic probes, null on disposition → honest **weaker** result (recall-steering).
- `mismatched` steers wrong-direction → **generic**, not idiosyncratic.

## Safety / scope
Subjects are sandboxed (no FS/tools). Memory fenced as DATA. **Bonus probe:** a benign imperative
planted in a scar → executed (injection) or quoted (firewall)? Reported separately, not part of the
steering claim. **Scope honesty:** Gemma/phi4/deepcoder are *proxies* — a positive result is "a
phenotype can steer *a* model," not "steers Claude in Claude Code."

---

## Pressure test of the concepts (carried from design review)
| # | Risk | Status / mitigation |
|---|---|---|
| **P1** | Model *describes itself* differently vs *acts* differently | Behavioral/forced-choice probes; rubric scores the **decision**, not tone. Stage-0 manual read. |
| **P2** | Baseline bias — aligned model already uma-like, swamps direction | Characterize `none` on the rubric **first**; the **heretic** arm relieves it (less baseline disposition). |
| **P3** | Seed nondeterminism breaks cache | **RESOLVED** — greedy-primary + content-addressed cache; no seed-replay. |
| **P4** | Heretic not a clean instrument | Base-match **confirmed** (`gemma-4-12B-it` abliterated). **Coherence smoke still TODO** before using it as a measurement arm. |
| **P5** | 12B judge weak / same-brain bias | **Cross-family judge** (phi4 judges gemma, etc.) + deterministic anchor. |
| **P6** | "Neutral" probes leak topic → re-ID by topic | **Handled** — dex/uma share a domain, so dex-vs-uma re-ID *can't* be topic. |
| **P7** | Forced-choice ≠ free behavior | Each forced-choice paired with a free-form twin; agreement validates it. |
| **P8** | Gemma ≠ Claude (external validity) | **Multi-family breadth** (gemma/phi4/deepcoder) generalizes "a model"; scope stated honestly. |
| **P9** | Enriched phenotype still too thin for a 12B to *use* | **Stage 0 gates this** — no movement ⇒ revisit the phenotype before the factorial. |

## Pre-build checklist
1. **P4 coherence smoke** on the heretic (does it still answer sensibly?).
2. **Stage-0 smoke** (dex/uma/none, gemma-std, DATA, greedy) — the go/no-go gate for the whole build.
3. Build `tools/steering_experiment.py`: reuse `individuation_experiment.PERSONAS`/`build_psyche` →
   extract enriched phenotypes; probe battery; ollama driver (`/api/chat`, `think:false`,
   greedy + sampled); content-addressed response cache; the three scorers; staged runner.

## Cost note
~10 s/gen. Stage 0 ≈ 3 min; Stage 1 ≈ 20–25 min; full factorial ≈ a couple hours (staged). The cache
makes re-runs of already-computed cells free (resume); greedy makes the headline reproducible. This
is GPU-inference-bound, not embedding-bound — so the embedding-cache efficiency track doesn't help
here; staging + greedy + the response cache are the levers.
