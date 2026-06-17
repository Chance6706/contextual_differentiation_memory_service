"""CI guard for the self-validating phenotype-drift harness.

Runs `tools/drift_trajectory.py` under the offline hash embedder and asserts a
clean exit. The harness is self-validating — it exits non-zero if a healthy regime
degenerates OR a degeneration detector goes blind — so this single assertion guards
both the consolidation dynamics and the instrument itself. Offline (no model
download); ~10s.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_drift_trajectory_self_validates():
    env = dict(os.environ, CDMS_EMBED_BACKEND="hash")
    proc = subprocess.run(
        [sys.executable, str(REPO / "tools" / "drift_trajectory.py")],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=240,
    )
    assert proc.returncode == 0, (
        f"drift-trajectory harness failed (exit {proc.returncode}).\n"
        f"--- stdout (tail) ---\n{proc.stdout[-3000:]}\n"
        f"--- stderr (tail) ---\n{proc.stderr[-2000:]}"
    )


# --------------------------------------------------------------------------- #
# --real mode: the multi-project differentiation branch (fires on local CLI with
# many real projects). Guarded here against a synthetic two-project fixture shaped
# like Claude Code session transcripts so it runs offline & deterministically.
# --------------------------------------------------------------------------- #
_DETAILS = ["users", "orders", "payments", "sessions", "invoices", "accounts", "tokens", "audit"]
_ALPHA = [("migrate the database schema for {x}", "ran the database schema migration for the {x} table", "Bash", "migration completed successfully"),
          ("optimize the database index for {x}", "tuned the database schema query index for {x}", "Edit", "index optimized, done")]
_BETA = [("render the react component for {x}", "built the react component view for the {x} page", "Edit", "component rendered, success"),
         ("style the react button for {x}", "styled the react component button on the {x} screen", "Edit", "styling done, passed")]


def _write_project(pdir: Path, families, sid: str) -> None:
    pdir.mkdir(parents=True, exist_ok=True)
    lines, i = [], 0
    for d in _DETAILS:
        for (prompt, action, tool, outcome) in families:
            ts = f"2026-06-01T{10 + i // 60:02d}:{i % 60:02d}:00Z"
            i += 1
            lines += [
                {"type": "user", "timestamp": ts, "sessionId": sid,
                 "message": {"content": [{"type": "text", "text": prompt.format(x=d)}]}},
                {"type": "assistant", "timestamp": ts, "sessionId": sid,
                 "message": {"content": [{"type": "text", "text": action.format(x=d)},
                                         {"type": "tool_use", "name": tool, "input": {"x": 1}}]}},
                {"type": "user", "timestamp": ts, "sessionId": sid,
                 "message": {"content": [{"type": "tool_result", "content": outcome}]}},
            ]
    (pdir / "s1.jsonl").write_text("\n".join(json.dumps(x) for x in lines))


def test_drift_trajectory_real_multiproject(tmp_path):
    projects = tmp_path / "projects"
    _write_project(projects / "proj_alpha", _ALPHA, "a1")
    _write_project(projects / "proj_beta", _BETA, "b1")

    env = dict(os.environ, CDMS_EMBED_BACKEND="hash")
    proc = subprocess.run(
        [sys.executable, str(REPO / "tools" / "drift_trajectory.py"),
         "--real", str(projects), "--windows", "3"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=120,
    )
    out = proc.stdout
    assert proc.returncode == 0, f"exit {proc.returncode}\n{out}\n{proc.stderr[-1500:]}"
    # Both projects formed an identity and the >=2-project branch fired.
    assert "proj_alpha" in out and "proj_beta" in out, out
    assert "cross-project trait overlap" in out, out
    # The real-data individuation oracle: distinct-vocabulary projects stay distinct.
    overlaps = [float(v) for v in re.findall(r"w\d+=([\d.]+)", out)]
    assert overlaps, out
    assert max(overlaps) <= 0.34, f"projects not individuated: overlaps={overlaps}\n{out}"
