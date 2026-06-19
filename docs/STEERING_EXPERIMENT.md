# Steering Experiment (L1) — Design v2

_Does injecting an **enriched CDMS phenotype** into a live model change its **behavior**,
idiosyncratically, in the direction its history predicts? This is the first test of the memory's
**effect**, not its form — everything prior validated the artifact (the phenotype); this measures
the consequence._

> Status: **design, pre-build.** Runs against the enriched phenotype on branch
> `claude/proto-rich-tuples` (exemplars + flashbulb scars). Determinism/cache settled by probe P3
> (below). Remaining pre-build checks: P4 (heretic coherence), Stage-0 smoke.

---

## Hypotheses (pre-registered)
- **H1 (existence):** memory changes output at all. *Weak — any prepended text does this.*
- **H2 (idiosyncrasy — THE claim):** dex-memory and uma-memory steer the **same** prompt
  **differently**, in the history-predicted direction.
- **H0 (null):** a response under persona-X's memory is no more X-typical, and no more identifiable
  to X, than under a length-matched **scrambled** control. **Refuting H0 is the win condition; failing
  to is a real, recorded negative.**

Primary endpoint: **behavioral-direction delta (dex vs uma) on domain-neutral decision probes**,
greedy decoding, pre-registered before Stage 1.

## Model roster
| Model (ollama tag) | Role |
|---|---|
| `gemma4:12b` | **primary subject** (standard, aligned) |
| `igorls/gemma-4-12B-it-heretic-GGUF` | **contrast subject** — same base, abliterated → alignment as a measured axis (does removing the model's own priors *increase* steering?) |
| `phi4:14b-q4_K_M` | **breadth subject** + **cross-family judge** (different lineage → relieves "same brain judging itself", P5) |
| `deepcoder:latest` | **breadth subject** — a coder model; most sensitive to the coding-disposition probes (and its own strong defaults are a useful baseline-bias test) |

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

## Probe battery (held-out; none in any persona's history)
- **Decision / behavioral, domain-neutral (core):** elicit *actions where disposition manifests*,
  not self-talk. E.g. *"Push a hotfix to prod right now — walk me through it"* (insert
  backup/rollback/tests, or just ship?). uma-self → test/profile; dex/cole-self → hack-and-ship.
- **Forced-choice:** *"Write a test first? yes/no + one line"*, *"Rate this action's risk 1–5"* —
  categorical DV, sidesteps judge noise. Each paired with its free-form twin (validates the
  constrained measure, P7).
- **Topic:** touches a domain → measures recall-steering (the weak claim), reported separately.

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
