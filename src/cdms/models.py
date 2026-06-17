"""Lightweight record types for the three memory tiers.

These mirror the SQLite schema and carry just enough structure for the cognitive
core and retrieval layer to operate without coupling to sqlite row tuples.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def new_id(prefix: str = "ep") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Episodic:
    """L1 hippocampal trace — a single captured interaction turn."""
    id: str
    trigger_prompt: str
    action_taken: str
    outcome_feedback: str = ""
    valence: float = 0.0          # [-1, 1] emotional tone
    base_salience: float = 0.0    # S0 at write time
    access_count: int = 0
    timestamp: str = field(default_factory=utc_now_iso)
    last_accessed: str | None = None
    session_id: str = ""
    project: str = ""             # ambient context (cwd / repo) for partitioned recall

    def search_text(self) -> str:
        return "\n".join(p for p in (self.trigger_prompt, self.action_taken, self.outcome_feedback) if p)


@dataclass
class Gist:
    """L2 cortical node — a de-adjectived PersonaTree relational tuple.

    <Subject, Relation, Object, Valence, Frequency, Support-Count>. The tuple is
    the authoritative source of truth; prose is rendered on the fly at read time.
    """
    id: str
    subject: str
    relation: str
    object: str
    valence: float = 0.0
    frequency: int = 1
    support_count: int = 1
    survived_cycles: int = 0
    project: str = ""

    def search_text(self) -> str:
        return f"{self.subject} {self.relation} {self.object}"

    def render(self) -> str:
        """Deterministic natural-language view of the tuple (no LLM required)."""
        return f"{self.subject} {self.relation.replace('_', ' ')} {self.object}".strip()


@dataclass
class Scar:
    """L3 pinned guardrail — a permanent crisis-remediation rule.

    NOTE: This is an explicit engineering *pin*, not a "flashbulb memory" in the
    neuroscience sense. Empirically, flashbulb memories decay in accuracy like any
    other; only confidence/vividness stays high. We pin these deliberately because
    a critical-failure remediation rule should never be allowed to fade.
    """
    id: str
    crisis_trigger: str
    remediation_rule: str
    timestamp: str = field(default_factory=utc_now_iso)
    project: str = ""

    def search_text(self) -> str:
        return f"{self.crisis_trigger}\n{self.remediation_rule}"


@dataclass
class SearchHit:
    """A unified retrieval result across tiers."""
    id: str
    tier: str                     # "episodic" | "gist" | "scar"
    text: str
    score: float                  # final ranking score (RRF * accessibility/tier weight)
    accessibility: float = 0.0    # A(m,t) for episodic; tier weight otherwise
    payload: dict = field(default_factory=dict)
