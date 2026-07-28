"""Guard + record WHICH cdms the harness actually imported (pressure-test M-A).

The eval venv editable-installs cdms pointing at the SIBLING main repo src, so under
PYTHONPATH=<repo-root> or none the harness silently imports the WRONG (possibly pre-fence)
cdms — which can INVERT the fence headline (cdms-full looks unfenced, Δ≈0) with no error, and
run.py stamps the worktree HEAD regardless so the doc can't tell the two apart. This module
hard-fails unless the imported cdms is THIS worktree's own src, and records its actual file +
its own repo's commit so a results doc is never ambiguous about which code was measured.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

# .../cdms-evalbuild/tools/eval_harness/provenance.py -> parents[2] = worktree root
_WORKTREE_SRC = (Path(__file__).resolve().parents[2] / "src").resolve()


def _imported_cdms_path() -> Path:
    import cdms
    return Path(cdms.__file__).resolve()


def assert_worktree_cdms() -> Path:
    """Hard-fail unless the imported cdms is THIS worktree's src (not the editable-installed
    sibling main repo). Returns the verified path. Call before any measurement of a CDMS condition."""
    p = _imported_cdms_path()
    try:
        under = p.is_relative_to(_WORKTREE_SRC)      # py3.9+
    except AttributeError:                            # pragma: no cover
        under = str(p).startswith(str(_WORKTREE_SRC))
    if not under:
        raise RuntimeError(
            f"eval-harness imported the WRONG cdms: {p}\n"
            f"  expected under worktree src: {_WORKTREE_SRC}\n"
            f"The eval venv editable-installs cdms from the SIBLING main repo, which silently "
            f"measures a different (possibly pre-fence) codebase and can INVERT the fence result.\n"
            f'  FIX: run with PYTHONPATH="{_WORKTREE_SRC}" (the src dir ONLY, not the repo root).'
        )
    return p


def _git_commit(cwd: Path) -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, cwd=cwd).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def cdms_provenance() -> dict:
    """The ACTUAL imported cdms file + its OWN repo's commit (NOT the worktree HEAD — they differ
    exactly when the wrong cdms is imported) + whether it is the expected worktree src. For the
    run-config header, so a paper reviewer can see precisely which code produced the numbers."""
    p = _imported_cdms_path()
    repo_root = p.parents[2]                          # <root>/src/cdms/__init__.py -> <root>
    try:
        is_worktree = p.is_relative_to(_WORKTREE_SRC)
    except AttributeError:                            # pragma: no cover
        is_worktree = str(p).startswith(str(_WORKTREE_SRC))
    return {"cdms_file": str(p), "cdms_repo": str(repo_root),
            "cdms_commit": _git_commit(repo_root), "is_worktree_src": bool(is_worktree)}
