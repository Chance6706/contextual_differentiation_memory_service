# External red-team packs (Cycle 4)

Self-contained, paste-ready prompt packs for an **external, cross-lineage** red-team
of CDMS — the value is orthogonal failure-mode coverage that a Claude-auditing-Claude
pass structurally misses (`CLAUDE.md` §9: stress-test from more than one viewpoint).

Three internal cycles (run by Claude) are recorded in
[`../REDTEAM_FINDINGS.md`](../REDTEAM_FINDINGS.md); these packs drive a fourth,
external cycle. Each pack is fully self-contained (context + the 8-agent fan-out +
rules + output format) so it can be pasted straight into an OpenRouter chat or agent
harness, with or without repo/tool access.

## Run order

1. **Pass A — DeepSeek V4 Pro** → [`CYCLE4_DEEPSEEK.md`](CYCLE4_DEEPSEEK.md)
   (breadth-first: exhaustive branch/path/config enumeration; leads on A0/A5/A7).
2. **Pass B — GPT-5.5** → [`CYCLE4_GPT55.md`](CYCLE4_GPT55.md)
   (depth-first: novel multi-step attacks, breaks the Cycle-3 fix claims, challenges
   the deferred X1–X6 tradeoffs; leads on A0/A1/A2/A4). Feed it the DeepSeek report as
   prior art so it confirms/refutes and goes deeper rather than repeating.

Both cover the same 8 surfaces: **A0** re-audit the Cycle-3 fixes, **A1** concurrency/
durability, **A2** privacy/forget, **A3** embedder integrity, **A4** identity/cognitive-
math, **A5** long-horizon resources/numerics, **A6** MCP/install/supply-chain, **A7**
config/clock/packaging/test-integrity.

## Integrating the results

Save each model's report (e.g. `CYCLE4_DEEPSEEK_REPORT.md`, `CYCLE4_GPT55_REPORT.md`)
here. Then, back in Claude Code: triage by severity, **independently reproduce** every
CRIT/HIGH before acting (an external model can hallucinate a defect), fix with mutation-
sensitive tests, re-audit the fixes, and fold a "Cycle 4" section into
`../REDTEAM_FINDINGS.md`. Treat a report's claims as untrusted input until reproduced.
