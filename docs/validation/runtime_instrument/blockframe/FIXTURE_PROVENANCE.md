# worldblock_fixture.txt — provenance (BLOCK_PREREG arm C)

`worldblock_fixture.txt` is the FROZEN arm-C preamble: the byte-exact CDMS-A single-arm persona
preamble (T1-only, `setup_bem_multifact(1)`, variant v1 — T1@378 preserved) composed through
**CDMS-D's production snapshot renderer** with the two filler dependency facts as WORLD FACTS.

- Rendered by: `cdms_d.session.render_fixture_snapshot(persona, facts=[...])` — the deterministic
  render seam built for exactly this harness use ("score -D's own render as a variant alongside the
  CDMS-A-side renders"; -D PR #14). Byte-identical output for identical inputs (doc-guaranteed
  sha-pinnable).
- CDMS-D commit at render: `9d8bae928fd000d2d0d6eeea3de1bd154c0a54f0` (master, post attribution-guard
  PR #37; shipped guard semantics — project-subject facts render unscrubbed, as designed).
- World facts input: `{subject: "the services", relation: depend_on/run_on, object:
  cobalt_runtime/mesa_framework, project: "P"}` → rendered by -D's native `fact.render()` as
  `- the services depend on cobalt_runtime [P]` under
  `# World context (CDMS-D — editable by operator, read-only for assistant)` /
  `## User preferences and conventions (editable)`.
- Layout facts (locked, test-guarded): 1151 bytes; T1 @ 378 (UNCHANGED vs every prior epoch — the
  persona block renders first and is byte-identical to the single arm); cobalt_runtime @ 1085 (world
  section). The arm varies (block membership + -D header + -D fact-line format + length) as the
  PRODUCTION-HONEST bundle — that is the deployed surface, disclosed as such; the single-axis header
  contrast is arm B (v2b).
- The fixture file is byte-frozen (content sha in BLOCK_PREREG §manifest + tests); regenerating it
  requires re-running the render command above against the recorded -D commit and MUST produce
  identical bytes.
