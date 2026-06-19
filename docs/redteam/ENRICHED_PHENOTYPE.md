# Red-team — enriched phenotype (exemplars + flashbulb floor)

_Recorded 2026-06-19. Target: PR #40 (gist exemplars + flashbulb floor) / PR #41 (validated those
steer). Motivation: we empirically proved the recall channel steers ~9× more after enrichment, so
the abuse surface must be checked. Threat: memory-POISONING — an attacker who controls the text of
an ingested turn (poisoned tool output / a file or web page the agent reads) plants memory that
steers future sessions. All hypotheses reproduced against the live tip (hash backend); PoCs were
disposable. Triage discipline: nothing asserted until a working PoC confirmed it._

## Verdict

**The enriched-phenotype PR opened no new structural hole. Its structural defenses hold. The one
real residual — guardrail/recall poisoning — is PRE-EXISTING; enrichment raises its *impact* (the
injected content steers harder), not its reachability.** My lead hypothesis (that the flashbulb
floor *widened* the surface) was **refuted** by the PoC.

| Hypothesis | Result | Evidence |
|---|---|---|
| Poisoned exemplar breaks/forges the `<memory:persona>` fence | **Defended** | `_sanitize` escapes `<>`→`&lt;&gt;`, backticks→`'`, strips control/zero-width/bidi/TAG chars, flattens whitespace; exemplar goes through `_sanitize(g.exemplar,160)`. Breakout `</memory:persona>` rendered escaped; fences balanced. |
| Flashbulb floor widens guardrail-poisoning | **Refuted** | A crafted catastrophe scores natural **S0=3.284 ≥ 3.0** and elevates with the floor **on AND off** — the floor is neutral for attacker input. A terse one (S0=1.896) fails the **valence gate** (−0.25 > −0.4), so the floor correctly does nothing. The floor's only window is valence-pass ∧ S0∈[natural, 3.0) — narrow, and an attacker who can drive valence ≤ −0.4 has already pushed S0 over 3.0. |
| Single crafted turn manufactures an attacker-written guardrail | **Real, but PRE-EXISTING** | One turn whose outcome contains a `_CATASTROPHE_HARM` substring (e.g. `"data loss"`, matched *unconditionally*) + crisis-negative lexical valence elevates to a scar whose `remediation_rule` is attacker text, rendered identically to a human pin. Works via *natural* elevation (≥3.0), independent of the floor — i.e. it predates this PR. |
| `valence_hint` injectable from a hook payload | **Defended** | `valence_hint` is never read from the hook→pipeline path; only the lexical path is attacker-reachable, and it still needs the valence gate. |

## What enrichment *does* change

It does not create a hole, but it raises the **impact** of the pre-existing poisoning vector: PR #41
showed injected rules/guardrails are cited ~9× more and flip decisions the thin phenotype couldn't.
So a poisoned guardrail that lands is now a stronger lever than before. Same reachability, bigger
blast radius.

## Residual risk + the one proportionate lever

The sharpest residual is **provenance opacity**: an auto-`elevated` scar renders identically to a
human-`pinned` guardrail (`hooks.py` guardrails block), so the model can't tell a vetted rule from
one auto-derived from untrusted captured text. Since guardrails steer, discounting untrusted-origin
ones is prudent. The candidate hardening — render auto-elevated scars with a truthful provenance
marker (e.g. "auto-detected") distinct from pinned — is **informational, not suppression** (a
genuine auto-crisis still shows, just labeled). Tradeoff: a real auto-detected crisis may be
slightly discounted. Left as an explicit decision (not auto-applied) because it changes every
session's preamble. NOT recommended: tightening the floor or the lexicon — the PoC shows the floor
isn't the weak link, and narrowing `_CATASTROPHE_HARM` would re-open genuine-crisis false-negatives.

## Locked by regression tests

`tests/test_redteam_enriched_phenotype.py` (3): poisoned exemplar can't break the persona fence;
poisoned scar can't break the guardrail fence; the flashbulb floor still requires BOTH gates
(lexicon match with non-crisis valence does NOT auto-elevate — the invariant that stops a single
positive/neutral turn carrying a harm phrase from minting a guardrail).
