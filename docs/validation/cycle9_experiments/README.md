# Cycle-9 Validation Experiments — Non-Interference & Phenotype Study

_Recorded 2026-06-19. Purpose: verify that the Cycle-9 hardening changes (PRs #27–#33) do not
perturb the system's measured behavior/identity, using a deterministic before/after methodology
on the **real** embedding model — and, separately, pressure-test the assumptions behind a future
"steering" experiment, which surfaced a phenotype-richness limitation and a prototype fix._

All raw run outputs are in [`raw/`](raw/). This file is the synthesis.

---

## TL;DR (claim, stated precisely)

> **No detectable impact on core identity/individuation metrics within the tested parameters.**

That wording is deliberate (and was tightened after an independent review — see §6). What we
actually demonstrated:

- **Synthetic drift harness:** byte-**identical** before vs after.
- **Synthetic individuation:** identical except **one** number — an anti-howlround stress-test's
  `min episodic salience` moved `2.1268 → 1.9270`. The headline **trait-overlap matrix stayed
  `0.000`**; continuity, plasticity, differentiation all identical.
- **Real transcripts (~10k turns, 3 projects):** cross-project trait overlap **`0.00` across all 6
  windows in BOTH** the before and after runs.
- The single shift is **attributable solely to finding #1** (the associative-boost crisis-gate
  clamp), is **benign** (nothing annihilated; budget conserved), and does **not** degrade under
  load escalation.

The honest caveat (§6): the experiments only put **two** of the changes (#1 boost-clamp, I-1
read-snapshot) through their changed code paths; the rest (#3/#4/#5/#7/#8) are **gated off** under
the default/single-project config the experiments use, so their *new branches* are validated by
the build→break→fix **unit tests**, not by these diffs.

---

## Methodology

Deterministic before/after. Both tools (`tools/individuation_experiment.py`,
`tools/drift_trajectory.py`) use fixed per-self seeds (blake2b/crc32) and a fixed clock, so
identical inputs ⇒ identical outputs (verified, §3). We ran each experiment at two commits and
diffed. Tools were **byte-identical** across the commit range (`git diff` empty) — only `src/cdms/`
changed — so a checkout cleanly isolates the source changes.

| Commit | Contents | Role |
|---|---|---|
| `2ada6fd` | Cycle-8 code (docs-only delta from f4dd7cf) | **baseline (before)** |
| `4ab721b` | + PR #27 (#3 cap-enforce, #4 weight-zeroing, #7 assoc caps) | attribution intermediate |
| `06e9b5d` | + all Cycle-9 (#27–#33: #1, #5, #8, I-1, quick-wins) | **current (after)** |

Embedder: the **real** CPU model (`bge-small`, unset `CDMS_EMBED_BACKEND`), not the hash backend
used for the fast test gate.

---

## 1. Synthetic drift harness — IDENTICAL
`raw/01_drift_synthetic_{before,after}.txt` — `diff` is empty. Steady-state persistence, absence
erosion (30→5, 400→0), thrash detection, and the differentiation contrast (distinct 0.00 /
identical 0.44, gap +0.44) are bit-identical before vs after. The identity-regression gate reads
exactly the same with and without the Cycle-9 changes.

## 2. Synthetic individuation — ONE number changed
`raw/02_individuation_{before,after}.txt` — the entire 78-line output is identical **except**:
```
min episodic salience = 2.1268   (before)
min episodic salience = 1.9270   (after)
```
Headline metrics unchanged: trait-overlap Jaccard `0.000` off-diagonal (incl. the same-domain
dex/uma pair), cosine mean `0.656`, continuity 100% persisted, plasticity drift `0.341`,
anti-howlround total `1000.0 (=K)`, episodes alive `24`.

## 3. Determinism — CONFIRMED
`raw/03_individuation_determinism_rerun.txt` — re-running the after-experiment a second time is
**bit-identical** to the first. The method's determinism assumption holds; the diffs are real code
effects, not RNG noise.

## 4. Attribution — the shift is finding #1
`raw/04_individuation_attribution_pre1.txt` — at `4ab721b` (config fixes #3/#4/#7 applied, boost
clamp #1 NOT yet), `min` is still **2.1268** and the whole output matches baseline. So #27's config
changes have **provably zero effect** here, and the shift is post-#27 — by elimination, the
associative-boost crisis-gate clamp (**#1**), the only post-#27 change touching episodic write-path
salience.

## 5. Direction under load — benign, not a degradation
`raw/05_howlround_probe_{pre1,current}.txt` — escalating the obsession `80×→640×` and consolidation
`1→4` cycles: `min` stays **well above 0** (nothing annihilated) in both versions, and the clamp
version is *slightly higher* (e.g. 1-cycle 35.13 vs pre-#1 31.31). So #1 does **not** push the
salience floor toward annihilation under load — the earlier "makes it stronger" framing was
retracted as unproven; the accurate statement is a **small, regime-dependent redistribution with
the anti-howlround invariant intact** (the synthetic experiment's `min` moved *down*, the probe's
moved *up* — sign depends on memory composition).

## 6. Real transcripts — headline holds, but the diff is CONFOUNDED
`raw/06_real_data_{before,after}.txt` — cross-project trait overlap is **`0.00` across all 6 windows
in both runs** (individuation holds on the real, grown corpus, both code versions). **But** the
gist-content and turn-counts differ between runs (this repo: 2217 → 2285 turns) because the
transcripts are **live and grew between runs — the working session is itself being logged into
`~/.claude/projects`**. So the real-data before/after is **not** a clean code-isolation diff; the
clean isolation comes only from the deterministic synthetic runs. (For a clean future run: copy a
**frozen snapshot** of the transcripts and run both commits against that.)

## Independent second opinion (Gemma `gemma4:12b`)
`raw/08_gemma_second_opinion.txt` — a skeptical cross-model review. Its substantive points, which we
**accepted**:
- "Zero effect" is an overstatement → downgrade to **"no detectable impact on core identity metrics
  within tested parameters."** (Adopted in the TL;DR.)
- **Biggest risk = the scope gap:** the config/DB/hook changes are "dark" in this suite — not
  exercised, so not validated *by these experiments*. (This matches our own coverage audit; the
  nuance Gemma understates is that those modules **are** covered by the build→break→fix unit tests,
  just not by the experiment diffs.)
- Don't discard the real-data run — `0.00` in both is a strong **sanity check** of functional parity
  under live/noisy input, even if not proof of non-perturbation. (Agreed.)

---

## Pressure-test → phenotype richness → prototype (separate thread)

While designing a future **steering experiment** (does injecting a CDMS phenotype change a live
model's behavior?), we pressure-tested its assumptions and found the **gist tuples too thin to
steer**:
- `raw/07_phenotypes_thin_baseline.txt` — the current SRO object is the **top-2 frequency-reordered
  keywords** (`"merge never"`, `"shader always"`), a great differentiation *fingerprint* but a poor
  behavioral *brief*. And **`scars=0`** for all personas: only one had a crisis, and its natural
  S0=2.8 missed the 3.0 elevation gate — so the richest channel (verbatim guardrails) was empty.
- `raw/07_phenotypes_enriched_prototype.txt` — a prototype (branch `claude/proto-rich-tuples`,
  **not merged**) that (a) attaches a render-only **verbatim exemplar** to each gist, and (b)
  **flashbulb-floors** a genuine catastrophe's salience so guardrails actually elevate. Result: the
  disposition signal returns — cole gains the verbatim `force push … data loss … restore from
  reflog` guardrail + cowboy exemplars (`"move fast, ship it"`); dex vs uma (same Unity domain)
  become cleanly separable (`"just make it compile"` + null-refs vs `"always profile"` /
  `"write an edit-mode test"` + `"cleanly refactored"`). Full suite: no new failures; drift PASS.

---

## Status & next (for tomorrow)
- **Validated:** Cycle-9 hardening does not perturb core identity/individuation metrics (synthetic,
  deterministic). Real-data individuation holds (`0.00`), with the confound noted.
- **LANDED (gated), 2026-06-19:** the rich-tuples prototype shipped to `main` behind config gates —
  exemplars bounded to the top-N highest-support gists (`recall_exemplars` / `recall_exemplar_top_n`,
  +37–63% preamble vs the prototype's unbounded ~+85%) and the flashbulb floor (`flashbulb_floor_catastrophes`).
  Recall-quality + cost validated on the real embedder: see [`../enriched_phenotype/`](../enriched_phenotype/).
- **Open threads:** the L1 **steering experiment** (now better-grounded — needs the enriched
  phenotype; consider standard vs "heretic"/abliterated Gemma as a *contrast condition*, not a
  swap); the falsifiable **C1 determinism control** cell for the drift harness; the read-only
  **memory viewer** (L0); and the **embedding cache / batch / offline-GPU** efficiency track for the
  validation loop.
