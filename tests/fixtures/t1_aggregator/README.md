# T1 aggregator synthetic fixtures

Hermetic test fixtures for the T1 aggregator (no live LLM calls). Each subdirectory
is one fixture: one or more variant `.txt` files (matching the output format of
`tools/redteam_claude_md_interference.py`) plus a `README.md` containing the
EXPECTED aggregator verdict — the test oracle.

## Fixtures

| Fixture | Variant files | What it exercises |
|---|---|---|
| `clean_win/` | v1, v2 | V2.full +20pp on ORDER all 5 models, ties elsewhere. Only 1 of 3 win-able modes wins → Step 1 FAILS (needs ≥2). |
| `clean_loss/` | v1, v2 | V2.full ≈ V1 on every win-able mode. Step 1 FAILS. |
| `mixed/` | v1, v2 | V2.full wins ORDER + OVERRIDE but LOSES BEM. Step 1 FAILS on loss gate. |
| `heterogeneous/` | v1, v2 | V2.full wins +40pp on 3 models, LOSES -15pp on 2 (Gemma flip). Step 1 FAILS on loss gate; heterogeneity flag fires. |
| `regression/` | v1, v2 | V2.full wins ORDER but breaks INSTR (1.00 → 0.50). Step 1 FAILS on regression-only gate. |
| `over_correction/` | v1, v2 | V2.full wins ORDER but spikes ORDER_OVERFIRE (0% → 50%). Step 1 FAILS on regression-only gate. |
| `unparseable_spike/` | v1, v2 | One cell at 90% unparseable. Aggregator MUST flag + exclude + still evaluate gate on remaining cells. |
| `ablation_winner/` | v1, v2, v2b | V2.full passes Step 1+2; V2.b ties within ±5pp on all modes. Step 3 → ship V2.b instead. |

## Format reference

Every `T1_*.txt` file matches `tools/redteam_claude_md_interference.py`'s output:
- 6 header lines starting with `#`
- Per-mode block opened by `## Mode: <NAME>` + 4 metadata lines
- Per-arm block opened by `### <MODE> — <arm> per-model outcomes`
- Per-model outcome lines indented 2 spaces, label left-aligned in 14 chars,
  with mode-specific outcome fields and a Wilson interval `[lo, hi]`
- Per-arm sample-response block opened by `### <MODE> — <arm> sample responses (probe 0)`
- 5 model sample-response lines

The aggregator parses the outcome lines (the lines with `=N/M` counts and
`P(*)=p [lo, hi]`). Sample-response lines are filler the parser SHOULD tolerate
without crashing but does not depend on for verdicts.

## Regenerating

The fixtures are checked-in `.txt` files. The `_gen_fixtures.py` helper rebuilds
them deterministically:

```
uv run python tests/fixtures/t1_aggregator/_gen_fixtures.py
```

Aggregator tests MUST NOT import from `_gen_fixtures.py` — they consume only the
checked-in `.txt` + `README.md` files (so the helper can evolve without breaking
the test oracle, and the oracle remains a human-readable spec).
