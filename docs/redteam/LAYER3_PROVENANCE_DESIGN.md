# Layer 3 — capture-time provenance (BUILT 2026-06-19)

_Designed then built 2026-06-19. Closes the worst poisoning bypass the 5-model pressure test
(`pressure_test.txt`) found against L1+L2._

**RESULT (built + validated, `layer3_validation.txt`):** the persistent untrusted poison across 2
sessions — the worst bypass — goes **20/20 → 1/20 unsafe** on the 5-model panel once provenance is
enforced (0 scars elevated vs 4; demoted to the recent tier where L2 neutralizes the outcome).
Untrusted content is also excluded from gist-trait formation (unit-tested). `enforce_provenance`
defaults True; classifier `pipeline.classify_provenance` (web/foreign-path → untrusted, in-project →
trusted, unknown → ambiguous). The accepted residual stands: untrusted, non-catastrophe content may
still flash in the cold-start recent tier, by design.

Full all-variant 5-model sweep (`layer3_full_validation.txt`, untrusted poison, enforce off vs on):
outcome2s (persistent) **20/20 → 1/20 CLOSED**; outcome1 1→1, action1 2→2, benign1 11→11 (the
cold-start recent-tier residuals — L3 blocks their *durable* gist-trait path, which a cold-start
probe can't show, not the one-shot recent flash). So L3 closes the recurrence/guardrail bypass; the
residuals are the documented by-design ones, pending recent-tier gating / conversational tuning.

## What it must close (ranked by the measured threat)

1. **Persistent multi-session poison — 20/20, every model.** THE priority: store-maturity-independent,
   mints a full authoritative guardrail, and `session_id` comes verbatim from the hook payload so a
   poisoned repo file read across sessions is the *common* case. Corroboration (L1) is defeated by
   recurrence.
2. **Non-catastrophe content — 11/20, 4 of 5 models.** "Team standard is to deploy to prod" never
   trips the catastrophe matcher, so L1/L2 are blind. (Strongest in cold-start / once it forms a
   gist; in a mature store a single such turn may not surface.)
3. **Imperative in `action` not `outcome` — 2/20, phi4 only.** Minor; L2 surfaces `trigger → action`.

## The load-bearing lesson from the data

**Framing does not work; only content removal does.** The render-time marker bought ~0 (4/4 even
marked); descriptive "recent activity" framing still steered (11/20 benign). What worked was taking
content OUT of the authoritative path (L1: no guardrail) and removing the imperative text (L2: 0/12
for that shape). So Layer 3 must **gate untrusted content OUT of injection / authority — not relabel
it.** This is why provenance (a content-admission gate) is the right lever and why it's
recurrence-independent: it never asks "did this recur?", only "can we trust where this came from?"

## Trust model (DECIDED 2026-06-19)

Three provenance states, with authority that climbs only as trust is established:

- **trusted** — the OUTCOME of the user's own directed actions (their command/edit succeeded/failed,
  what the user intended). The legitimate persona signal.
- **untrusted** — the CONTENT of external data the agent merely *read* (WebFetch/WebSearch, foreign
  files/repos, tool output reflecting third-party data, external MCP).
- **ambiguous** — the classifier can't tell. **This is the default for unknown** (a quarantine
  middle tier, not fail-open).

| provenance | guardrail elevation | gist trait | recent / recall context |
|---|---|---|---|
| trusted | ✓ | ✓ | ✓ |
| ambiguous (quarantine) | ✗ | ✓ | ✓ |
| untrusted | ✗ | ✗ | ✓ (low-authority recent only) |

**Load-bearing invariant: only trusted-provenance content can become an authoritative guardrail.**
That alone closes the 20/20 persistent bypass for everything the classifier doesn't positively
trust. Untrusted additionally cannot become a persona *trait* (no gist). Ambiguous content still
learns (gist + recent) but can never be enshrined as a rule.

**Accepted residual (explicit):** untrusted content may still surface in the low-authority *recent*
tier, where the pressure test showed benign content can still steer (~11/20, strongest in
cold-start). This was a deliberate call — retain external-read context for usefulness, deny it
authority — accepting that recent-tier residual rather than dropping the info entirely.

**The fundamental limit (state it up front):** provenance is undecidable in general. `cat
poisoned.md` run under the user's own Bash command yields trusted-LOOKING output that is actually
attacker content — it would be misclassified `trusted` and could elevate. So provenance is a
heuristic that raises the bar a lot (kills drive-by WebFetch / foreign-file poison and all
persistent-recurrence attacks routed through recognizably-external channels) but is not a silver
bullet against an attacker who launders poison through a trusted-looking channel.

## Where it's tagged

At capture. `pipeline.iter_turns` already reconstructs the `TurnEvent` from the hook payload
(`tool_name`, `tool_input`, `tool_output`, `cwd`, ...). Add a `provenance` field:

- New `TurnEvent.provenance` + `Episodic.provenance` (+ `mem_*` column, additive migration like
  `exemplar`).
- A classifier `classify_provenance(tool_name, tool_input, cwd) -> "trusted"|"untrusted"` driven by
  a tool denylist/heuristics: WebFetch/WebSearch/fetch-by-URL → untrusted; Read/Bash whose target
  resolves OUTSIDE the project `cwd` → untrusted; Edit/Write/Bash within the project under user
  direction → trusted (default). MCP tools → untrusted unless allowlisted.

## Gating rules (DECIDED)

- **Guardrail elevation** (`consolidate._elevate_scars`): require `provenance == "trusted"`. Untrusted
  AND ambiguous are excluded — so the corroboration gate (L1) now has a provenance precondition, and
  the persistent bypass closes for all non-trusted content regardless of recurrence.
- **Gist-trait formation** (the consolidation clustering): untrusted episodes are excluded from
  cluster membership (they can't mint or reinforce a persona trait). Ambiguous and trusted form gists
  normally.
- **Recent / recall**: untrusted and ambiguous may surface in the low-authority recent tier (accepted
  residual). L2's existing catastrophe-neutralization still applies on top.
- **Trusted content is unaffected** → CDMS still learns the persona from the user's own actions.
- Untrusted/ambiguous content is **stored** (for the audit viewer) regardless of gating.

## Conceptual pressure-test of the design

| bypass | does provenance close it? |
|---|---|
| persistent (20/20) | **Yes** — untrusted stays untrusted across sessions; recurrence-independent. The big win. |
| non-catastrophe (11/20) | **Yes if** the poison entered via an untrusted tool (web/foreign file) — gated from gist + recall. |
| action-placement (2/20) | **Yes if** untrusted-tagged — not surfaced at all. |
| **residual** | classifier evasion: poison routed through a trusted-LOOKING channel (e.g. `cat` of a downloaded file under the user's own shell). Provenance can't see that. Document it; it's the irreducible limit. |

## The core tension + resolution

Agents read external content constantly — if *all* `tool_output` is "untrusted," CDMS learns almost
nothing. Resolution: trust the **outcome of the user's own directed actions** (success/failure,
their edits to their own files), distrust the **content of external reads**. The classifier's job is
exactly this split, and it's imperfect — so the **default for ambiguous provenance is a real
decision** (below).

## Decisions

1. **Ambiguous-provenance default:** RESOLVED → **quarantine/tiered** (no guardrail elevation, but
   may form gists + surface in recent). Not fail-open.
2. **Gate for untrusted:** RESOLVED → **no elevation + no gist-trait** (may still surface in
   low-authority recent; residual accepted).
3. **Classifier scope v1 (default unless overridden):** small tool-based heuristic —
   WebFetch/WebSearch/external-URL fetch → untrusted; Read/Bash targeting a path OUTSIDE `cwd` →
   untrusted; Edit/Write/Bash within the project → trusted; unrecognized → ambiguous. Iterate later.
4. **Effort/phasing:** (1) `provenance` field on TurnEvent/Episodic + additive `mem_*` migration;
   (2) `classify_provenance()` in the capture path; (3) gating in `_elevate_scars` + cluster
   membership; (4) tests; (5) 5-model pressure-test re-run to confirm persistent 20/20 → low.
   **BUILT 2026-06-19**: `provenance` field on TurnEvent/Episodic + additive `mem_episodic` migration;
   `classify_provenance` in pipeline (set in `iter_turns`); gates in `_elevate_scars` (trusted-only)
   and `_aggregate_gists` (exclude untrusted); `enforce_provenance` flag; `tests/test_layer3_provenance.py`;
   validated by `tools/redteam_layer3_validate.py`.

## Not in scope / rejected
Render-time labelling (measured dead). Tightening the catastrophe lexicon or stripping more fields
(whack-a-mole; root cause is trusting captured content). Per-turn LLM provenance classification
(cost/latency on the capture hot path; SessionStart-never-blocks).
