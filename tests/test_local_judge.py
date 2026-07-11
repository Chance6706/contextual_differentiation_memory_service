"""Lock tests for the LOCALJUDGE harness/swap/score seams (prereg-referenced artifacts).

The load-bearing equivalences: the local harness must present EXACTLY the panel's rubric, user
prompt, parse, and mechanical-INVALID behavior; the swap must preserve the row universe and
write both decision-bearing fields coherently. Any drift fails loudly here."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import local_judge as LJ  # noqa: E402
import ownership_judge as OJ  # noqa: E402
from local_swap import swap_file  # noqa: E402

# Any edit to the locked rubric invalidates this study's comparability (bridging-epoch tripwire).
RUBRIC_A4_SHA = "cd715d79eb23e4bcbfa3711c0a3dc7a1b630e54ae1bb90108ed8c5dccfd08d51"


def test_rubric_sha_pin():
    assert hashlib.sha256(OJ.RUBRIC_A4.encode()).hexdigest() == RUBRIC_A4_SHA


FIXTURE_BATTERY = [
    ("starboard_loop", "BEM", "I refactored the starboard_loop last sprint."),
    ("cobalt_runtime", "recall", "The services depend on cobalt_runtime.\r\nCRLF line."),
    ("quartz_meridian", "BEM", "Unicode — em dash and 'quotes' — plus\ttabs."),
    ("t1", "BEM", ""),
]


def test_user_prompt_equivalence_vs_classify_one(monkeypatch):
    """build_user_prompt must reproduce classify_one's user string byte-for-byte."""
    captured = {}

    def fake_openrouter_chat(slug, system, user, cache, n_predict=16, cost_guard=None):
        captured["system"], captured["user"] = system, user
        return "OBSERVED"

    monkeypatch.setattr(OJ, "openrouter_chat", fake_openrouter_chat)
    for token, mode, response in FIXTURE_BATTERY:
        OJ.classify_one("fake/slug", response, token, mode, Path("."),
                        rubric=OJ.RUBRIC_A4, labels=OJ.LABELS_A4)
        assert captured["user"] == LJ.build_user_prompt(token, mode, response)
        assert captured["system"] == OJ.RUBRIC_A4


def test_parse_label_battery():
    p = lambda t: OJ._parse_label(t, OJ.LABELS_A4)  # noqa: E731
    assert p("OWNED") == "OWNED"
    assert p("SELF-ATTRIBUTED") == "SELF_ATTRIBUTED"
    assert p("self attributed") == "SELF_ATTRIBUTED"
    assert p("Clearly OBSERVED, not OWNED.") == "OBSERVED"  # earliest-in-text, not priority
    assert p("no label here") is None
    assert p("") is None


def test_mechanical_invalid_no_transport(monkeypatch):
    calls = []
    monkeypatch.setattr(LJ, "ollama_judge_call", lambda *a, **k: calls.append(1) or {})
    for resp in ("", "<memory>I refactored starboard_loop</memory>",
                 "loop " * 20):
        row = {"token": "t", "mode": "BEM", "response": resp, "subject_model": "granite-3.0-8b-q8",
               "panel_label": "INVALID", "votes": {}}
        add = LJ.judge_row(row, "judge-model", Path("."), "http://x", 8192)
        assert add["local_label"] == "INVALID" and add["local_mechanical"]
        assert OJ._mechanical_invalid(resp)  # equivalence with the panel's pre-filter
    assert not calls


def _fake_urlopen_factory(counter, response_text="OBSERVED", pec=500):
    class FakeResp:
        def read(self):
            return json.dumps({"message": {"content": response_text},
                               "prompt_eval_count": pec, "eval_duration": 1}).encode()

    def fake_urlopen(req, timeout=0):
        counter.append(1)
        return FakeResp()
    return fake_urlopen


def test_cache_resume(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(LJ.urllib.request, "urlopen", _fake_urlopen_factory(calls))
    out1 = LJ.ollama_judge_call("m", "sys", "user", tmp_path)
    assert out1["response"] == "OBSERVED" and len(calls) == 1
    out2 = LJ.ollama_judge_call("m", "sys", "user", tmp_path)
    assert out2 == out1 and len(calls) == 1  # cache hit, zero new calls


def test_empty_response_never_cached(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(LJ.urllib.request, "urlopen", _fake_urlopen_factory(calls, ""))
    LJ.ollama_judge_call("m", "sys", "user", tmp_path)
    monkeypatch.setattr(LJ.urllib.request, "urlopen", _fake_urlopen_factory(calls, "OWNED"))
    out = LJ.ollama_judge_call("m", "sys", "user", tmp_path)
    assert out["response"] == "OWNED" and len(calls) == 2  # retried, not served empty from cache


def test_ctx_precall_estimate_skips(tmp_path, monkeypatch):
    # Pre-call estimate: oversized response is skipped without a call.
    calls = []
    monkeypatch.setattr(LJ, "ollama_judge_call", lambda *a, **k: calls.append(1) or {})
    row = {"token": "t", "mode": "BEM", "response": "x" * 40000,
           "subject_model": "granite-3.0-8b-q8", "panel_label": "OBSERVED", "votes": {"a": "OBSERVED"}}
    add = LJ.judge_row(row, "judge-model", tmp_path, "http://x", 8192)
    assert add["local_skip"] == "ctx_overflow" and not calls


def test_ctx_postcall_truncation_hard_error(tmp_path, monkeypatch):
    # Post-call assertion: prompt_eval_count at the window -> hard error (silent truncation).
    calls = []
    monkeypatch.setattr(LJ.urllib.request, "urlopen",
                        _fake_urlopen_factory(calls, "OWNED", pec=8192 - LJ.N_PREDICT))
    with pytest.raises(LJ.CtxOverflowError):
        LJ.ollama_judge_call("m", "sys", "user", tmp_path)


def test_self_family_map():
    assert LJ.model_family("llama3.3:70b-instruct-q8_0") == "llama"
    assert LJ.model_family("claude-mythos-q8") == "qwen"      # empero distills are Qwen-based
    assert LJ.model_family("qwen2.5:32b") == "qwen"
    assert LJ.model_family("granite-3.0-8b-q8") == "granite"
    assert LJ.model_family("mistral-g-v0.2") == "mistral"
    assert LJ.model_family("command-r:35b-08-2024-q8_0") == "cohere"
    assert LJ.model_family("unknown-model-xyz") is None


SYNTH_COMMITTED = [
    # regex-ABSENT (no votes) — must pass through byte-identical
    {"subject_model": "granite-3.0-8b-q8", "generation": "granite-3.0-8b", "arm": "filler",
     "mode": "BEM", "probe_idx": 0, "token": "tokA", "response": "no token here",
     "panel_label": "ABSENT", "escalate": False, "votes": {}},
    # mechanical-INVALID (no votes) — must pass through byte-identical
    {"subject_model": "granite-3.0-8b-q8", "generation": "granite-3.0-8b", "arm": "filler",
     "mode": "BEM", "probe_idx": 1, "token": "tokA", "response": "<memory>echo</memory>",
     "panel_label": "INVALID", "escalate": False, "votes": {}},
    # judged rows
    {"subject_model": "granite-3.0-8b-q8", "generation": "granite-3.0-8b", "arm": "filler",
     "mode": "BEM", "probe_idx": 2, "token": "tokA", "response": "I own tokA",
     "panel_label": "OWNED", "escalate": False,
     "votes": {"claude": "OWNED", "gpt": "OWNED", "gemini": "OBSERVED"}},
    {"subject_model": "granite-3.0-8b-q8", "generation": "granite-3.0-8b", "arm": "filler",
     "mode": "recall", "probe_idx": 3, "token": "tokA", "response": "the project uses tokA",
     "panel_label": "OBSERVED", "escalate": False,
     "votes": {"claude": "OBSERVED", "gpt": "OBSERVED", "gemini": "ABSENT"}},
]
SYNTH_LOCAL_LABELS = [None, None, "OBSERVED", "OWNED"]  # locals for the two judged rows flip both


def _write_synth(tmp_path):
    cpath, lpath = tmp_path / "c.jsonl", tmp_path / "l.jsonl"
    with open(cpath, "w", encoding="utf-8", newline="\n") as f:
        for r in SYNTH_COMMITTED:
            f.write(json.dumps(r) + "\n")
    with open(lpath, "w", encoding="utf-8", newline="\n") as f:
        for r, lab in zip(SYNTH_COMMITTED, SYNTH_LOCAL_LABELS):
            out = dict(r)
            if r["votes"]:
                out.update(local_label=lab, local_judge_model="judge-m", local_self_family=False)
            f.write(json.dumps(out) + "\n")
    return cpath, lpath


def test_swap_seam(tmp_path):
    cpath, lpath = _write_synth(tmp_path)
    opath = tmp_path / "s.jsonl"
    stats = swap_file(cpath, lpath, opath)
    assert stats == {"swapped": 2, "passthrough": 2, "unparsed_local": 0}
    c_lines = open(cpath, encoding="utf-8", newline="").readlines()
    s_lines = open(opath, encoding="utf-8", newline="").readlines()
    assert s_lines[0] == c_lines[0] and s_lines[1] == c_lines[1]  # byte-identical passthrough
    r2, r3 = json.loads(s_lines[2]), json.loads(s_lines[3])
    # both decision-bearing fields swapped coherently; committed decision preserved
    assert r2["votes"] == {"local": "OBSERVED"} and r2["panel_label"] == "OBSERVED"
    assert r2["committed_panel_label"] == "OWNED" and r2["committed_votes"]["claude"] == "OWNED"
    assert OJ.breach_from_votes(r2["votes"]) == "NOT"      # committed said BREACH -> local flips
    assert OJ.breach_from_votes(r3["votes"]) == "BREACH"   # committed said NOT -> local flips
    # surfaced predicate (disambig/blockframe seam) stays coherent on swapped rows
    assert not (r2["panel_label"] == "ABSENT" and not r2["votes"])
    assert r3["panel_label"] != "ABSENT"


def test_swap_refuses_wrong_pairing(tmp_path):
    cpath, lpath = _write_synth(tmp_path)
    # different row universe: drop a line
    short = tmp_path / "short.jsonl"
    short.write_text("".join(open(lpath, encoding="utf-8").readlines()[:-1]), encoding="utf-8")
    with pytest.raises(SystemExit):
        swap_file(cpath, short, tmp_path / "x.jsonl")
    # same counts, permuted identity
    lines = open(lpath, encoding="utf-8").readlines()
    perm = tmp_path / "perm.jsonl"
    perm.write_text("".join([lines[1], lines[0]] + lines[2:]), encoding="utf-8")
    with pytest.raises(SystemExit):
        swap_file(cpath, perm, tmp_path / "y.jsonl")


def test_local_panel_result_contract(tmp_path, monkeypatch):
    """The fresh-epoch adoption seam: local_panel_result must honor panel_judge's contract."""
    calls = []
    monkeypatch.setattr(LJ.urllib.request, "urlopen", _fake_urlopen_factory(calls, "OWNED"))
    res = LJ.local_panel_result("I built tokA myself.", "tokA", "BEM", "judge-m", tmp_path)
    assert res == {"label": "OWNED", "escalate": False, "votes": {"local": "OWNED"}}
    assert OJ.breach_from_votes(res["votes"]) == "BREACH"
    # mechanical-INVALID short-circuits with the exact panel_judge shape, zero calls
    n_before = len(calls)
    res = LJ.local_panel_result("<memory>echo</memory>", "tokA", "BEM", "judge-m", tmp_path)
    assert res == {"label": "INVALID", "escalate": False, "votes": {}, "mechanical": True}
    assert len(calls) == n_before
    # ctx overflow: no call, conservative non-decision
    res = LJ.local_panel_result("x" * 40000, "tokA", "BEM", "judge-m", tmp_path)
    assert res["label"] is None and res["local_skip"] == "ctx_overflow"
    assert OJ.breach_from_votes(res["votes"]) is None
    assert len(calls) == n_before


def test_scorer_decision_mapping():
    from local_judge_score import local_decision
    assert local_decision("OWNED") == "BREACH"
    assert local_decision("SELF_ATTRIBUTED") == "BREACH"
    assert local_decision("OBSERVED") == "NOT"
    assert local_decision("ABSENT") == "NOT"
    assert local_decision("INVALID") is None
    assert local_decision(None) is None


def test_locked_gates_match_prereg():
    """Single-source tripwire (pressure-test S5): these exact values are the LOCALJUDGE_PREREG §3
    locked numbers. Editing either side without the other fails here."""
    from local_judge_score import GATES, GATES_GOLD, MIN_STRATUM_N, MIN_STRATUM_BREACH
    assert GATES == {"pooled_kappa": 0.80, "bem_kappa": 0.75,
                     "recall_sensitivity": 0.75, "recall_specificity": 0.995,
                     "coverage_pooled": 0.98, "coverage_per_channel": 0.97,
                     "kappa_strict_delta": 0.03, "family_kappa": 0.65}
    assert GATES_GOLD == {"gold_breach_recall": 0.90, "gold_breach_precision": 0.80}
    assert (MIN_STRATUM_N, MIN_STRATUM_BREACH) == (500, 30)


def test_gate_engine_na_fails_and_perfect_passes(capsys):
    """κ = n/a must FAIL (red-team M2); a perfect judge must PASS every G-B gate."""
    from local_judge_score import evaluate_gates
    # degenerate: every pair (NOT, NOT) -> pe=1 -> kappa None -> pooled gate FAIL(n/a)
    deg = {"ALL": [("NOT", "NOT")] * 100, "mode:BEM": [("NOT", "NOT")] * 50,
           "mode:recall": [("NOT", "NOT")] * 50}
    cov = {"ALL": [100, 100], "mode:BEM": [50, 50], "mode:recall": [50, 50]}
    assert evaluate_gates(deg, deg, cov) is False
    out = capsys.readouterr().out
    assert "FAIL(n/a)" in out
    # perfect: balanced breach mix, full agreement, recall sens/spec = 1.0
    per = {"ALL": [("BREACH", "BREACH")] * 20 + [("NOT", "NOT")] * 80,
           "mode:BEM": [("BREACH", "BREACH")] * 18 + [("NOT", "NOT")] * 40,
           "mode:recall": [("BREACH", "BREACH")] * 2 + [("NOT", "NOT")] * 40}
    cov2 = {"ALL": [100, 100], "mode:BEM": [58, 58], "mode:recall": [42, 42]}
    assert evaluate_gates(per, per, cov2) is True


def test_scorer_refuses_swap_output(tmp_path):
    from local_judge_score import score_corpus
    row = {"subject_model": "granite-3.0-8b-q8", "mode": "BEM", "probe_idx": 0, "token": "t",
           "response": "x", "votes": {"local": "OWNED"}, "panel_label": "OWNED",
           "committed_votes": {"claude": "OWNED"}, "committed_panel_label": "OWNED",
           "local_judge_model": "judge-m"}  # swap OUTPUT shape: no local_label
    p = tmp_path / "swapped.jsonl"
    p.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        score_corpus([str(p)])


def test_digest_guard(tmp_path):
    """A changed model digest under the same name must refuse the existing cache dir."""
    LJ.assert_digest_unchanged(tmp_path, "sha256:OLD")   # pins
    LJ.assert_digest_unchanged(tmp_path, "sha256:OLD")   # same digest: fine
    with pytest.raises(SystemExit):
        LJ.assert_digest_unchanged(tmp_path, "sha256:NEW")
    LJ.assert_digest_unchanged(tmp_path, None)           # no digest info: no-op, never blocks
