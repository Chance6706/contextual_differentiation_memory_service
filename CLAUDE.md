# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

1. Plan mode by default. Enter plan mode for any task with 3+ steps or architectural decisions. If something goes sideways, stop and re-plan immediately. Write detailed specs upfront to reduce ambiguity.

2. Use subagents liberally. Offload research, exploration, and parallel analysis to subagents. Keep your main context window clean. For complex problems, throw more compute at it. One task per subagent for focused execution.

3. Verify before marking done. Never mark a task complete without testing that it works. Diff behavior between main and your changes.

4. Let Claude fix bugs autonomously. When given a bug report, just fix it. Point at logs, errors, failing tests and resolve them. Go fix failing CI tests without being told how.

5. Do not assume context. If critical context is missing, ask first.

6. Separate fact from inference. Never present guesses as answers.

7. Avoid overconfidence. Don't state uncertain things as definitive.

8. Acknowledge disagreement. If sources conflict, say so and summarize both sides.

9. Do not restrict yourself to a single point of view. If it cannot be stress-tested then it cannot be properly implemented.

10. Auto-merge PRs. For this repository, merge a pull request you open once it is mergeable (no conflicts, any required checks green) without waiting for explicit approval. Still do not *open* a PR unless asked. If a PR is not mergeable, or a review has requested changes, surface that instead of force-merging.

11. Flag deliberate deviations. Whenever the project departs from a "pure" mathematical derivation, or uses a borrowed term against its typical denotation/connotation/association, flag it explicitly at the point of use (a short `DELIBERATE DEVIATION` note) and register it in `docs/DEVIATIONS.md` (standard form/meaning → what we do → why → what we disclaim). Don't diverge silently. Companion discipline for constants: classify free vs derived vs coincidence in `docs/PARAMETER_BASIS.md`.

12. Pressure-test before locking. For any artifact that will be hard to change later — a pre-registration, a research methodology, a builder/test pair, an adapter contract, a critical config — run a double pressure test BEFORE commit: (a) red-team perspective ("how could this produce misleading results, fail silently, be bypassed by an attacker or careless caller, or break under Python/network/disk quirks?") and (b) legitimate-use perspective ("where does this over-design, fail to support real workflows, have rough developer ergonomics?"). Apply MUST_FIX and SHOULD_FIX findings inline; document inherent limitations in a register on the artifact itself (a `## Pressure-test record` section in the doc, or a comment block in the module). This discipline pays for itself — it has caught real bugs in this repo that solo work missed (NaN bypass that would have silently bricked the OpenRouter cost cap; API-key header smuggling via CRLF; cross-backend cache collision; `cost_guard.record()` ordered before cache write so a failed write debited budget for a re-spent call; duplicate `BudgetExceededError` shadowing the real exception). The discipline composes with rule 9: pressure-testing IS the stress-test that makes an implementation defensible.

13. Re-runs of matrices / experiments use a fresh cache by default. See `feedback-matrix-reruns-must-be-fresh` memory for the full three-tier protocol (crash-resume cached for operational continuity; canonical re-run as a paired cached-vs-fresh comparison; §6 reproducibility check deferred). Practical pattern: timestamped cache dir per run (`~/cdms_cache/$(date +%Y%m%d_%H%M%S)`). Crash recovery is the only sanctioned use of cached responses across run boundaries — and even then, publication requires a fresh end-to-end pass.