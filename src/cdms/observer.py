"""Observer UI — read-only, operator-only viewer onto a CDMS store. See docs/OBSERVER_UI_DESIGN.md.

Read-only BY CONSTRUCTION: opens the store with `mode=ro` (falling back to a normal open + PRAGMA
query_only=ON for WAL robustness), issues only SELECTs, never writes / injects / blocks the daemon.
The operator sees WIDER than the model (provenance, scar origin, raw salience). The §8 temperament
dials live behind a gated /diagnostics page and NEVER appear in the model-facing preamble preview
(Bem firewall). Localhost only. Stdlib http.server — zero new deps. ALL stored content is
HTML-escaped: a poisoned memory must not XSS the operator's browser.
"""
from __future__ import annotations

import html
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .config import Config, load_config


def open_ro(db_path) -> sqlite3.Connection:
    """A hard read-only handle: prefer URI mode=ro; fall back to a normal open (WAL stores can be
    awkward to open ro) but then force PRAGMA query_only=ON so writes are rejected either way."""
    p = str(db_path)
    try:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
    except sqlite3.OperationalError:
        conn = sqlite3.connect(f"file:{p}", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA query_only=ON")
    except sqlite3.Error:
        pass
    return conn


def _rows(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.Error:
        return []


def _scalar(conn, sql, params=()):
    r = _rows(conn, sql, params)
    return r[0][0] if r else 0


def E(x) -> str:
    return html.escape("" if x is None else str(x))


_PROV_CLASS = {"trusted": "t", "untrusted": "u", "ambiguous": "a"}
STYLE = ("<style>body{font-family:system-ui,sans-serif;margin:1.4rem;max-width:1150px;color:#222}"
         "table{border-collapse:collapse;width:100%;font-size:12.5px;margin:.5rem 0}"
         "th,td{border:1px solid #ddd;padding:4px 7px;text-align:left;vertical-align:top}"
         "th{background:#f4f4f4}nav{margin:.3rem 0 1rem}nav a{margin-right:.5rem}"
         "code,pre{white-space:pre-wrap;font-size:12px}h1{font-size:18px}.dim{color:#888}"
         ".u{color:#b00020;font-weight:600}.a{color:#9a6700;font-weight:600}.t{color:#0a7d2c}"
         ".pin{color:#0a7d2c;font-weight:600}.elev{color:#9a6700;font-weight:600}"
         ".warn{background:#fff3f3;border:1px solid #d33;padding:10px;border-radius:5px;margin:.6rem 0}"
         ".kv{display:inline-block;background:#eef;border-radius:3px;padding:1px 6px;margin:2px}</style>")
NAV = ('<nav><a href="/">Dashboard</a>·<a href="/episodic">Episodic (L1)</a>·'
       '<a href="/gists">PersonaTree (L2)</a>·<a href="/scars">Guardrails (L3)</a>·'
       '<a href="/preamble">What the model sees</a>·<a href="/diagnostics">⚙ Diagnostics</a></nav>')


def page(title, body) -> str:
    return f"<!doctype html><meta charset=utf-8><title>{E(title)}</title>{STYLE}<h1>{E(title)}</h1>{NAV}{body}"


# ---- views (pure: conn/cfg in, HTML str out — directly unit-testable) -------------------------

def render_dashboard(conn) -> str:
    ne = _scalar(conn, "SELECT count(*) FROM mem_episodic")
    ng = _scalar(conn, "SELECT count(*) FROM mem_gist")
    ns = _scalar(conn, "SELECT count(*) FROM mem_scars")
    prov = _rows(conn, "SELECT provenance, count(*) c FROM mem_episodic GROUP BY provenance ORDER BY c DESC")
    orig = _rows(conn, "SELECT origin, count(*) c FROM mem_scars GROUP BY origin ORDER BY c DESC")
    proj = _rows(conn, "SELECT project, count(*) c FROM mem_episodic GROUP BY project ORDER BY c DESC")
    b = [f"<p>Episodic <b>{ne}</b> · PersonaTree gists <b>{ng}</b> · Guardrails <b>{ns}</b></p>"]
    b.append("<p><b>Provenance</b> (operator audit — wider than the model sees): ")
    for r in prov:
        cls = _PROV_CLASS.get(r["provenance"] or "trusted", "")
        b.append(f'<span class="kv {cls}">{E(r["provenance"] or "trusted")}: {r["c"]}</span>')
    b.append("</p><p><b>Guardrail origin</b>: ")
    for r in orig:
        cls = "pin" if r["origin"] == "pinned" else "elev"
        b.append(f'<span class="kv {cls}">{E(r["origin"])}: {r["c"]}</span>')
    b.append("</p><p><b>By project</b>: ")
    for r in proj:
        b.append(f'<span class="kv">{E(r["project"] or "(global)")}: {r["c"]}</span>')
    b.append("</p>")
    cyc = _rows(conn, "SELECT key, value FROM cdms_meta ORDER BY key")
    if cyc:
        b.append("<p class=dim>meta: " + " · ".join(f"{E(r['key'])}={E(r['value'])}" for r in cyc) + "</p>")
    return page("CDMS Observer — Dashboard", "".join(b))


def render_episodic(conn, project=None, provenance=None) -> str:
    sql = ("SELECT trigger_prompt,action_taken,outcome_feedback,valence,base_salience,access_count,"
           "provenance,session_id,project,timestamp FROM mem_episodic")
    where, params = [], []
    if project:
        where.append("project=?"); params.append(project)
    if provenance:
        where.append("provenance=?"); params.append(provenance)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY base_salience DESC LIMIT 500"
    rows = _rows(conn, sql, tuple(params))
    head = ("<tr><th>trigger</th><th>action</th><th>outcome</th><th>S0</th><th>val</th>"
            "<th>seen</th><th>provenance</th><th>project</th><th>when</th></tr>")
    body = []
    for r in rows:
        cls = _PROV_CLASS.get(r["provenance"] or "trusted", "")
        body.append(
            f"<tr><td>{E(r['trigger_prompt'])}</td><td>{E(r['action_taken'])}</td>"
            f"<td>{E(r['outcome_feedback'])}</td><td>{r['base_salience']:.2f}</td>"
            f"<td>{r['valence']:.2f}</td><td>{r['access_count']}</td>"
            f"<td class='{cls}'>{E(r['provenance'] or 'trusted')}</td>"
            f"<td>{E(r['project'])}</td><td class=dim>{E((r['timestamp'] or '')[:19])}</td></tr>")
    filt = ('<p class=dim>filter: <a href="/episodic?provenance=untrusted">untrusted</a> · '
            '<a href="/episodic?provenance=ambiguous">ambiguous</a> · <a href="/episodic">all</a></p>')
    return page("Episodic (L1)", filt + f"<table>{head}{''.join(body)}</table>")


def render_gists(conn, project=None) -> str:
    sql = ("SELECT subject,relation,object,valence,support_count,frequency,survived_cycles,exemplar,"
           "project FROM mem_gist")
    params = ()
    if project:
        sql += " WHERE project=?"; params = (project,)
    sql += " ORDER BY (support_count+frequency+survived_cycles) DESC LIMIT 500"
    rows = _rows(conn, sql, params)
    head = ("<tr><th>subject</th><th>relation</th><th>object</th><th>val</th><th>support</th>"
            "<th>freq</th><th>cyc</th><th>exemplar</th><th>project</th></tr>")
    body = "".join(
        f"<tr><td>{E(r['subject'])}</td><td>{E(r['relation'])}</td><td>{E(r['object'])}</td>"
        f"<td>{r['valence']:.2f}</td><td>{r['support_count']}</td><td>{r['frequency']}</td>"
        f"<td>{r['survived_cycles']}</td><td class=dim>{E(r['exemplar'])}</td>"
        f"<td>{E(r['project'])}</td></tr>" for r in rows)
    return page("PersonaTree (L2 gists)", f"<table>{head}{body}</table>")


def render_scars(conn) -> str:
    rows = _rows(conn, "SELECT crisis_trigger,remediation_rule,origin,project FROM mem_scars "
                       "ORDER BY origin, project")
    head = "<tr><th>origin</th><th>crisis trigger</th><th>remediation rule</th><th>project</th></tr>"
    body = []
    for r in rows:
        cls = "pin" if r["origin"] == "pinned" else "elev"
        body.append(f"<tr><td class='{cls}'>{E(r['origin'])}</td><td>{E(r['crisis_trigger'])}</td>"
                    f"<td>{E(r['remediation_rule'])}</td><td>{E(r['project'])}</td></tr>")
    note = ('<p class=dim>pinned = human-authored guardrail · elevated = auto-promoted from a '
            'corroborated, trusted-provenance crisis (Layer 1/3).</p>')
    return page("Guardrails (L3 scars)", note + f"<table>{head}{''.join(body)}</table>")


def render_preamble(cfg: Config, conn, project=None) -> str:
    """The faithful 'what the model sees' at SessionStart for a project — via the SAME
    _session_start_context the hook uses. Dials are structurally absent from this output."""
    projects = sorted({(r["project"] or "") for r in
                       _rows(conn, "SELECT DISTINCT project FROM mem_episodic "
                                   "UNION SELECT DISTINCT project FROM mem_gist "
                                   "UNION SELECT DISTINCT project FROM mem_scars")})
    links = " · ".join(f'<a href="/preamble?project={E(p)}">{E(p or "(global)")}</a>' for p in projects)
    body = [f"<p class=dim>project: {links}</p>"]
    if project is not None:
        from .hooks import _session_start_context
        ctx = _session_start_context(cfg, {"cwd": project}) or "(empty — nothing recalled for this project)"
        body.append(f"<p class=dim>Exactly what the model is given at SessionStart for "
                    f"<code>{E(project)}</code>. The temperament dials are NOT here (Bem firewall):</p>")
        body.append(f"<pre>{E(ctx)}</pre>")
    else:
        body.append("<p class=dim>Pick a project above to preview its SessionStart injection.</p>")
    return page("What the model sees (SessionStart preamble)", "".join(body))


def render_diagnostics(conn) -> str:
    rows = _rows(conn, "SELECT dial,seed,current,lower,upper,plasticity FROM mem_temperament ORDER BY rowid")
    warn = ('<div class=warn><b>⚠ Operator-only diagnostics.</b> The §8 temperament dials below are '
            '<b>NEVER</b> shown to the model (Bem self-perception firewall) and never appear in the '
            'SessionStart preamble. This page is for human debugging only — do not paste these values '
            'back into the model\'s context.</div>')
    if not rows:
        return page("⚙ Diagnostics (operator-only)", warn + "<p class=dim>No temperament dials in this store.</p>")
    head = "<tr><th>dial</th><th>seed</th><th>current</th><th>range</th><th>plasticity</th></tr>"
    body = "".join(
        f"<tr><td>{E(r['dial'])}</td><td>{r['seed']:.3f}</td><td>{r['current']:.3f}</td>"
        f"<td class=dim>[{r['lower']:.2f}, {r['upper']:.2f}]</td><td>{r['plasticity']:.3f}</td></tr>"
        for r in rows)
    return page("⚙ Diagnostics (operator-only)", warn + f"<table>{head}{body}</table>")


# ---- HTTP server -------------------------------------------------------------------------------

def _handler(cfg: Config):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):       # quiet
            pass

        def _send(self, body: str, code=200):
            data = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            conn = open_ro(cfg.db_path)
            try:
                if u.path == "/":
                    self._send(render_dashboard(conn))
                elif u.path == "/episodic":
                    self._send(render_episodic(conn, q.get("project", [None])[0], q.get("provenance", [None])[0]))
                elif u.path == "/gists":
                    self._send(render_gists(conn, q.get("project", [None])[0]))
                elif u.path == "/scars":
                    self._send(render_scars(conn))
                elif u.path == "/preamble":
                    self._send(render_preamble(cfg, conn, q["project"][0] if "project" in q else None))
                elif u.path == "/diagnostics":
                    self._send(render_diagnostics(conn))
                else:
                    self._send(page("404", "<p>not found</p>"), 404)
            finally:
                conn.close()
    return H


def serve(cfg: Config | None = None, host: str = "127.0.0.1", port: int = 8765) -> int:
    cfg = cfg or load_config()
    if not cfg.db_path.exists():
        print(f"cdms observer: no store at {cfg.db_path}")
        return 1
    srv = ThreadingHTTPServer((host, port), _handler(cfg))
    print(f"CDMS Observer (read-only) → http://{host}:{port}   store: {cfg.db_path}")
    print("Ctrl-C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        srv.server_close()
    return 0
