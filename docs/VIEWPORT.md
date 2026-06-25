# CDMS Viewport

A loopback, **read-only** browser dashboard over the CDMS store — a window into the agent's
accumulated self: the three tiers (episodic / gist / scars), the temperament disposition, and a
live ingestion feed (SSE). It is a read-only consumer of `cdms.store`; it never modifies CDMS state.

Originally authored by **owl-alpha** in a standalone `CDMS-viewport` repo, then pulled into the
package and hardened (see the changelog below).

## Run

```
cdms viewport --port 8765            # or:  python -m cdms.viewport --port 8765
```

Then open <http://127.0.0.1:8765>. The store is read from the usual `CDMS_HOME`
(set `CDMS_EMBED_BACKEND=hash` for the offline embedder).

## Invariants (load-bearing)

- **Read-only.** Every endpoint is a GET; all SQL is SELECT/COUNT; search passes `reinforce=False`
  so browsing the store does NOT bump access counts or reinforce memories — the observer must not
  perturb the salience/decay dynamics it displays.
- **Loopback-only.** It serves the entire store AND the operator-only temperament dials with no
  auth. A non-loopback `--host` is **refused**. For remote access (e.g. the planned GX10 / Open
  WebUI exposure) front it with an authenticated tunnel / reverse proxy — never bind it to the LAN.
- **Operator-only dials.** Showing the temperament dials is consistent with their operator-only
  design — the Bem firewall is about the *model's context*, which this dashboard never touches.
- **Additive.** The live feed polls the SQLite tables on a background thread; CDMS has no knowledge
  of the viewport and is not modified.

## API

| Path | Returns |
|---|---|
| `/` | dashboard HTML |
| `/api/stats` | tier counts + health signals + archetype |
| `/api/timeline` | recent episodic memories (`?limit=`, `?project=`) |
| `/api/persona` | top gists |
| `/api/paths` | PersonaTree paths |
| `/api/scars` | guardrails |
| `/api/temperament` | disposition dials (operator view) |
| `/api/search?q=` | unified retrieval (non-mutating) |
| `/api/sse` | live event stream (`episode` / `gist` / `scar`) |

## Hardening applied when pulled into the package

- **SSE route un-shadowed** — `/api/sse` was captured by the `/api/` router and 404'd, so the live
  feed (which the frontend connects to via `EventSource('/api/sse')`) never connected.
- **Search made non-mutating** — `retrieve(..., reinforce=False)` (the default reinforces episodic memory).
- **Static serving contained** to the static dir (no `..` path traversal).
- **Non-loopback binds refused.**
- **Store access serialized** across the threaded server (one shared sqlite connection).

Locked by `tests/test_viewport.py`. This is the richer successor to the older, lighter
`cdms observe` Observer UI (`src/cdms/observer.py`); both are read-only and loopback-only.
