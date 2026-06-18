"""Cycle 8 — fuzz-hardening surfaced by a local-model (Gemma) adversarial-input pass.

The model generated the inputs; expected behaviour was adjudicated against the real
functions. Genuine gaps found and fixed:
  * redact: OpenAI project/service keys (sk-proj-/sk-svcacct-) have hyphens the sk- rule
    missed; `pwd=` assignments had no alias.
  * infer_success: marker stems bled into unrelated longer words ("success"->"successive",
    "cannot"->"cannotation"), producing false outcome inferences that poison valence.
"""

from __future__ import annotations

from cdms.pipeline import _infer_success
from cdms.store import redact_secrets


# --- redaction gaps ---------------------------------------------------------- #
def test_fuzz_openai_project_key_redacted():
    out = redact_secrets('{"model":"gpt-4","key":"sk-proj-7hG9kLp1nM3rT5vX8wYz0qP2sR4tU6"}')
    assert "[REDACTED]" in out and "sk-proj-7hG9" not in out


def test_fuzz_openai_svcacct_key_redacted():
    out = redact_secrets("OPENAI=sk-svcacct-" + "A" * 24)
    assert "[REDACTED]" in out and "sk-svcacct-AAA" not in out


def test_fuzz_pwd_assignment_redacted():
    out = redact_secrets('config: pwd="super-secret-value-here"')
    assert "[REDACTED]" in out and "super-secret-value-here" not in out


def test_fuzz_decoys_not_over_redacted():
    decoys = [
        "request_id: 550e8400-e29b-41d4-a716-446655440000",          # uuid
        "build_version: 1.2.0-beta+exp.sha.5114e23",                  # version
        "commit_hash: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",     # git hash
        "The system password requirement is now mandatory for users.",  # word, no value
    ]
    for d in decoys:
        assert "[REDACTED]" not in redact_secrets(d), f"over-redacted: {d!r}"


# --- inference: marker stems must not bleed into longer words ---------------- #
def test_fuzz_marker_does_not_overmatch_longer_words():
    assert _infer_success("Successive calls were made.") is None        # not "success"
    assert _infer_success("annotation of the broken cannotation") is None  # not "cannot"


def test_fuzz_marker_inflections_still_match():
    assert _infer_success("errors occurred during the run") is False     # error -> errors
    assert _infer_success("all tests passed") is True
    assert _infer_success("successfully resolved without any errors") is True  # success -> successfully
    assert _infer_success("the deploy completed; zero failures remained") is True
