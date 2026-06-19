# Observer UI — design spec (read-only memory viewer)

_Drafted 2026-06-19. A local, read-only, operator-only viewer onto a CDMS store. Long-parked as
"L0"; resurfaced because Layer 3 (provenance) made it an **audit/security tool**, not just a
curiosity — it's how an operator SPOTS poisoned/untrusted memory._

## Purpose
1. **Audit/security** (post-L3): see every `untrusted`/`ambiguous` episode, every auto-`elevated`
   scar vs human-`pinned` guardrail, the gist traits + their support — i.e. catch a poisoned memory.
2. **Observability / dogfooding**: watch the store grow; see exactly what the model is given.
3. **Research aid**: inspect the structural residue the harnesses measure (a human-readable companion
   to `tools/*` and the "how much glass" study).

## Hard invariants (non-negotiable)
- **Read-only.** Opens the SQLite store with `mode=ro` (URI). No endpoint writes anything, ever.
- **Operator-only, localhost.** Binds 127.0.0.1 only. Not part of, and never feeds, the model's context.
- **Never blocks the daemon.** WAL reader; a snapshot read like SessionStart, no locks held.
- **Never an injection path.** It only *displays* stored content (already `_sanitize`-able); it adds
  no route by which viewed text re-enters the model.

## Access model — operator sees WIDER than the model
The model only ever sees the SessionStart preamble. The operator view deliberately shows MORE:
provenance, scar origin, raw salience/decay, session ids, timestamps, support counts. (Josh's call.)

## Views (MVP)
1. **Dashboard** — per-tier + per-project counts; consolidation stats; **provenance breakdown**
   (trusted / untrusted / ambiguous); scar origin breakdown (pinned / elevated).
2. **Episodic (L1)** — trigger / action / outcome, base_salience, accessibility (decay), valence,
   **provenance**, session, project, timestamp. Filter by project / provenance.
3. **Gists (L2 PersonaTree)** — subject·relation·object, support, frequency, survived_cycles,
   **exemplar**, valence, project.
4. **Scars (L3)** — crisis_trigger → remediation_rule, **origin (pinned vs elevated, clearly marked)**,
   project.
5. **"What the model sees"** — renders `_session_start_context(cfg, {"cwd": <project>})` per project:
   the exact SessionStart preamble. **Dials NEVER appear here.**

## Temperament dials (§8) — gated diagnostics (Josh's cautious call)
- The dials live behind a **separate, explicitly-opened "Diagnostics (operator-only)" panel**, OFF
  the default dashboard, **read-only**, labeled *"operator-only — never feed to the model (Bem
  self-perception firewall)."*
- They are **structurally excluded** from the "what the model sees" preview and from every default
  view. The firewall governs the *model* reading its disposition; a human behind a deliberate gate
  is fine — but we keep it un-casual and walled off so it never leaks into a model-facing surface.

## Tech (lean, local-first)
- Prefer **minimal deps**: stdlib `http.server` rendering server-side HTML, OR a tiny Flask app —
  NOT a heavy framework. The repo is uv/Python, CPU, no Rust; keep the footprint small. (Decision to
  confirm at build time; stdlib is zero-new-dep, Flask is friendlier routing.)
- SQLite opened read-only via `sqlite3.connect("file:...?mode=ro", uri=True)`. Reuses existing
  `Database` read methods (`all_episodic`, `top_gist`, `all_scars`, `stats`) and `_session_start_context`.
- Launch via a new CLI command: `cdms observe [--port N]` (default port configurable; the user
  referenced agentmemory's `:3113`).

## Build plan (MVP)
1. `src/cdms/observer.py` — read-only DB handle + HTML rendering of the 5 views + the gated dials panel.
2. `cdms observe` CLI command (binds localhost, opens store `mode=ro`).
3. Tests: read-only invariant (no write methods reachable); the preamble-preview view equals
   `_session_start_context` and contains NO dial values; provenance/origin surfaced correctly.
4. Later (not MVP): full-text search, decay/timeline curves, drift visualization, diff-over-time.

## Open decision for build
- **Dependency**: stdlib `http.server` (zero new deps, recommended for the minimal ethos) vs Flask
  (nicer routing, one dep). Lean stdlib unless routing gets painful.
