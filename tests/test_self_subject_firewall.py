"""Bem firewall: the model may never author a fact ABOUT ITSELF (never-authors-a-self-tuple).

A pressure-test (2026-06-25) found the one residual write-to-self channel: the MCP store(kind="fact")
tool hands a model-supplied subject straight to MemoryService.upsert_fact with no subject filter, so a
model could persist `subject="claude"` ("claude handles well starboard_loop") which renders verbatim into
the persona block. This locks the code-enforced refusal at upsert_fact, and that near-miss PROJECT names
(a repo literally named "claude-tools") are NOT collateral-blocked.
"""
import pytest

from cdms.store import _is_self_subject

_SELF = ["claude", "Claude", "Claude.", "  claude  ", "I", "me", "my", "mine", "myself", "self",
         "assistant", "the assistant", "an assistant", "AI", "the AI", "the model", "this AI",
         "yourself", "i, claude", "the language model"]
# "you"/"user" are the HUMAN, not the assistant — must stay allowed. Project-like names must pass.
_NOT_SELF = ["user", "you", "the user", "app", "payments", "workspace", "P", "the database",
             "claude-tools", "claudette", "ai-service", "my-project", "models"]


@pytest.mark.parametrize("s", _SELF)
def test_self_subjects_detected(s):
    assert _is_self_subject(s), f"{s!r} should be flagged as a self-subject"


@pytest.mark.parametrize("s", _NOT_SELF)
def test_non_self_subjects_allowed(s):
    assert not _is_self_subject(s), f"{s!r} must NOT be flagged self (it's a project/user/other)"


def test_upsert_fact_refuses_self_subject(service):
    for s in ("claude", "I", "the assistant", "myself", "AI"):
        with pytest.raises(ValueError, match="never-authors-a-self-tuple"):
            service.upsert_fact(s, "handles_well", "starboard_loop", project="p")


def test_upsert_fact_allows_project_user_and_namesake(service):
    assert service.upsert_fact("user", "prefers", "tabs over spaces", project="p") is not None
    assert service.upsert_fact("payments", "handles_well", "idempotency", project="p") is not None
    # a project literally named "claude-tools" is NOT the assistant — must still record
    assert service.upsert_fact("claude-tools", "handles_well", "routing", project="p") is not None
