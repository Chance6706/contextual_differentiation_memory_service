"""CI guard for the self-validating phenotype-drift harness.

Runs `tools/drift_trajectory.py` under the offline hash embedder and asserts a
clean exit. The harness is self-validating — it exits non-zero if a healthy regime
degenerates OR a degeneration detector goes blind — so this single assertion guards
both the consolidation dynamics and the instrument itself. Offline (no model
download); ~10s.
"""

from __future__ import annotations

import os
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
