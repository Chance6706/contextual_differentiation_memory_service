"""Memory-system adapters for the CDMS ablation harness.

Unit of comparison = a CDMS CONFIGURATION (an ablation), not an external product.
The CdmsAdapter applies one mechanism toggle per condition (§2 of the v2 prereg);
naive-dump / no-memory are the ceiling / floor bookends.

Two v1 bugs are fixed here and MUST stay fixed:
  * query() passes `project=` into retrieve() (v1 dropped scope → fake 100% isolation);
  * reset() verifies isolation with `is_relative_to`, not substring `in`.
Provenance is threaded per-turn (v1 hardcoded "trusted", disabling the fence).
"""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Protocol, runtime_checkable


@dataclass
class Scope:
    project: str = "eval-project"
    provenance: str = "trusted"


@dataclass
class Turn:
    role: str
    content: str
    tool_name: str = ""
    success: Optional[bool] = None
    timestamp: str = ""
    provenance: str = ""          # per-turn; "" -> fall back to scope.provenance


@dataclass
class Answer:
    text: str
    citations: list[str] = field(default_factory=list)
    tokens_injected: int = 0      # INJECTED CONTEXT tokens (the cost), NOT answer length
    latency_ms: float = 0.0


@dataclass
class ForgetSpec:
    project: Optional[str] = None
    session: Optional[str] = None
    ids: Optional[list[str]] = None    # TARGETED delete by id
    facts: Optional[list[str]] = None  # TARGETED delete by CONTENT (find episodes containing each, delete them)


# A reader turns retrieved context into an answer. ONE fixed reader model across all
# conditions (so the only variable is what memory surfaces); it is DISJOINT from the
# scoring panel (reader != judge — the v1 self-preference bug). Default = return the
# context verbatim (mechanical mode, $0); the runner injects a real reader for gate axes.
Reader = Callable[[str, str], str]

def _passthrough_reader(question: str, context: str) -> str:
    return context


@runtime_checkable
class MemorySystem(Protocol):
    def reset(self, run_id: str) -> None: ...
    def ingest(self, turns: list[Turn], *, scope: Scope) -> None: ...
    def consolidate(self, now=None) -> None: ...
    def query(self, question: str, *, scope: Scope) -> Answer: ...
    def forget(self, target: ForgetSpec) -> None: ...
    def health(self) -> dict: ...


# condition -> Config field overrides. Only fields that EXIST on Config are applied
# directly; conditions needing a not-yet-built seam are guarded in reset() so they
# can never SILENTLY degrade to cdms-full (the v1 disease).
_CONDITION_OVERRIDES: dict[str, dict] = {
    "cdms-full":            {},
    "cdms-fence":           {"enforce_provenance": False},
    "cdms-forgetting":      {"retention_floor": 0.0},
    "cdms-random-discard":  {"discard_policy": "random", "discard_random_seed": 1729},
    "cdms-no-scope":        {},   # no config change; query() drops the project filter (isolation ablation)
    # cdms-provenance-write: not separable from enforce_provenance today (Gap 2) — omitted
    # until granular flags exist; do not fake it.
}
_KNOWN_CONDITIONS = set(_CONDITION_OVERRIDES) | {"naive-dump", "no-memory"}


class CdmsAdapter:
    """Wraps cdms.store.MemoryService in one ablation configuration."""

    def __init__(self, condition: str = "cdms-full", base_path: Path | None = None,
                 reader: Reader | None = None):
        if condition not in _CONDITION_OVERRIDES:
            raise ValueError(f"unknown CDMS condition {condition!r}; "
                             f"expected one of {sorted(_CONDITION_OVERRIDES)}")
        self.condition = condition
        # cdms-no-scope drops the project filter at query time (isolates the project-scoping
        # mechanism: cdms-full scoped vs cdms-no-scope unscoped -> cross-project leak).
        self._scope_queries = condition != "cdms-no-scope"
        self._base_path = base_path or Path(tempfile.mkdtemp(prefix="cdms-eval-"))
        self._reader: Reader = reader or _passthrough_reader
        self._svc = None
        self._home: Path | None = None

    def reset(self, run_id: str) -> None:
        if self._svc is not None:
            self._svc.close()
        self._home = self._base_path / _safe(run_id)
        self._home.mkdir(parents=True, exist_ok=True)
        os.environ["CDMS_HOME"] = str(self._home)
        os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")   # deterministic mechanical runs
        os.environ["CDMS_EVAL_MODE"] = "1"   # this adapter IS the sanctioned eval context (gates random-discard)

        from cdms.config import Config, load_config
        from cdms.store import MemoryService
        from tools.eval_harness.provenance import assert_worktree_cdms

        # M-A GUARD: hard-fail if we imported the editable-installed sibling cdms instead of the
        # worktree's fenced src. A wrong import silently inverts the fence result (pressure-test M-A).
        assert_worktree_cdms()

        cfg = load_config()
        # Isolation: resolved home MUST be inside the tmp base (is_relative_to, NOT substring).
        resolved = Path(cfg.home).resolve()
        base = self._base_path.resolve()
        if not resolved.is_relative_to(base):
            raise AssertionError(f"CDMS_HOME {resolved} is not under the tmp base {base}; refusing to run")

        overrides = _CONDITION_OVERRIDES[self.condition]
        for field_name, value in overrides.items():
            # GUARD: never silently no-op an ablation. If the Config lacks the field the
            # condition needs (e.g. discard_policy before the Gap-1 seam lands), FAIL LOUD.
            if not hasattr(cfg, field_name):
                raise NotImplementedError(
                    f"condition {self.condition!r} needs Config.{field_name}, which does not exist yet "
                    f"(see IMPLEMENTATION_NOTES.md Gap 1). Refusing to run it as a silent no-op.")
            setattr(cfg, field_name, value)

        self._svc = MemoryService(cfg)

    def ingest(self, turns: list[Turn], *, scope: Scope) -> None:
        assert self._svc is not None, "reset() must precede ingest()"
        from cdms.store import TurnEvent
        for t in turns:
            self._svc.ingest(TurnEvent(
                trigger_prompt=t.content if t.role == "user" else "",
                action_taken=t.content if t.role in ("assistant", "tool") else "",
                outcome_feedback="",
                tool_name=t.tool_name,
                success=t.success,
                session_id="",
                project=scope.project,
                # Per-turn provenance threads through so the fence is actually under test.
                provenance=t.provenance or scope.provenance,
            ))

    def consolidate(self, now=None) -> None:
        """Run a real consolidation pass (dedup / gist / decay / EVICTION). REQUIRED for the
        forgetting + random-discard ablations to do anything — MemoryService.ingest never
        consolidates, so without this those toggles are inert (rule-12 M1). `now` lets a scenario
        age the store so episodes fall below the retention floor. Blueprint: individuation_experiment.py."""
        assert self._svc is not None, "reset() must precede consolidate()"
        from cdms.consolidate import Consolidator
        Consolidator(self._svc.cfg, db=self._svc.db, embedder=self._svc.embedder).run(now=now)

    def query(self, question: str, *, scope: Scope) -> Answer:
        assert self._svc is not None, "reset() must precede query()"
        t0 = time.perf_counter()
        # PASS the project scope (v1 dropped it -> retrieved across all projects -> fake isolation).
        # cdms-no-scope deliberately drops it, as the isolation ablation.
        proj = scope.project if self._scope_queries else ""
        hits = self._svc.retrieve(question, top_k=8, project=proj)
        elapsed = (time.perf_counter() - t0) * 1000
        context = "\n".join(h.text[:400] for h in hits) if hits else "(no memories)"
        text = self._reader(question, context)
        return Answer(
            text=text,
            citations=[h.id for h in hits],
            tokens_injected=len(context) // 4,   # injected CONTEXT cost, not answer length
            latency_ms=elapsed,
        )

    def forget(self, target: ForgetSpec) -> None:
        assert self._svc is not None, "reset() must precede forget()"
        # TARGETED content delete (right-to-forget): find episodes CONTAINING each fact and delete
        # only those — not the whole project (the v1/pressure-test nuke that also wiped legit re-writes).
        if target.facts:
            ids: set[str] = set()
            for fact in target.facts:
                hits = self._svc.retrieve(fact, top_k=20, tiers=("episodic",),
                                          reinforce=False, include_untrusted=True)
                ids.update(h.id for h in hits if fact.lower() in h.text.lower())
            if ids:
                self._svc.forget(ids=list(ids))
        if target.ids or target.project or target.session:
            self._svc.forget(project=target.project, session=target.session, ids=target.ids)

    def health(self) -> dict:
        return {"status": "healthy" if self._svc else "not_initialized",
                "condition": self.condition, "home": str(self._home)}

    def cleanup(self) -> None:
        if self._svc is not None:
            self._svc.close()
            self._svc = None
        if self._home and self._home.exists():
            shutil.rmtree(self._home, ignore_errors=True)


class NaiveDumpAdapter:
    """Ceiling bookend: dumps every ingested turn on every query (no selection, no fence)."""

    def __init__(self, reader: Reader | None = None):
        self._turns: list[Turn] = []
        self._reader = reader or _passthrough_reader

    def reset(self, run_id: str) -> None:
        self._turns = []

    def ingest(self, turns: list[Turn], *, scope: Scope) -> None:
        self._turns.extend(turns)

    def consolidate(self, now=None) -> None:
        pass   # a dump has no consolidation — that's the point of the ceiling bookend

    def query(self, question: str, *, scope: Scope) -> Answer:
        context = "\n".join(f"[{t.role}] {t.content}" for t in self._turns) or "(no memories)"
        return Answer(text=self._reader(question, context), tokens_injected=len(context) // 4)

    def forget(self, target: ForgetSpec) -> None:
        # No selective delete; a dump keeps everything (that's the point of the bookend).
        pass

    def health(self) -> dict:
        return {"status": "ok", "stored_turns": len(self._turns)}


class NoMemoryAdapter:
    """Floor bookend: no memory at all."""

    def reset(self, run_id: str) -> None: ...
    def ingest(self, turns: list[Turn], *, scope: Scope) -> None: ...
    def consolidate(self, now=None) -> None: ...
    def query(self, question: str, *, scope: Scope) -> Answer:
        return Answer(text="(no memory available)")
    def forget(self, target: ForgetSpec) -> None: ...
    def health(self) -> dict:
        return {"status": "ok"}


def _safe(run_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in run_id)[:120] or "run"
