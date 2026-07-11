"""Local A' judge harness (LOCALJUDGE validation arc).

Judges committed JUDGE.jsonl rows (or the A4 gold set) with a LOCAL ollama model, mirroring the
panel's per-job contract byte-for-byte at the rubric/prompt/parse layer:
  system  = ownership_judge.RUBRIC_A4 (imported, never copied)
  user    = f"TOKEN: {token}\\nMODE: {mode}\\nRESPONSE:\\n{response}\\n\\nLabel:"  (classify_one's shape;
            equivalence enforced by tests/test_local_judge.py against the real classify_one)
  parse   = ownership_judge._parse_label (earliest-label, SELF-ATTRIBUTED normalization)
  filter  = ownership_judge._mechanical_invalid applied IDENTICALLY before any call

Transport is deliberately NOT redteam_claude_md_interference.ollama_chat: that is the generation
transport (drags src/ imports; no num_ctx). Judging needs an explicit num_ctx — ollama silently
FRONT-truncates past the window, which eats the rubric first — so every call asserts
prompt_eval_count < num_ctx afterward and a conservative pre-call estimate skips oversized rows
(flagged local_skip="ctx_overflow", never silently judged).

Row universes (must match the committed files exactly; the swap/score tools rely on it):
  - regex-ABSENT rows (panel_label ABSENT, no votes): passed through BYTE-IDENTICAL, never judged
    (the whole-word surfacing regex is job-construction ground truth, not judge output);
  - mechanical-INVALID responses: local_label=INVALID, local_mechanical=true, no call;
  - everything else: one call -> local_label (+ local_raw, prompt_eval_count).

Output: input row + local_* keys, same order, one line per input line; sidecar <out>.meta.json
records model digest, ollama version, num_ctx, counts. Resume = per-model response cache keyed
sha256(model\\0system\\0user) (empty responses never cached), .tmp + atomic rename.

Runs ON Sparky (ship with ownership_judge.py + openrouter_chat.py + openrouter_cost_guard.py —
stdlib-only chain) or over LAN via --url for probes/smoke tests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ownership_judge import LABELS_A4, RUBRIC_A4, _mechanical_invalid, _parse_label  # noqa: E402

DEFAULT_URL = os.environ.get("CDMS_OLLAMA_URL", "http://localhost:11434")
DEFAULT_NUM_CTX = 8192
N_PREDICT = 16          # panel parity (ownership_judge.classify_one)
CTX_MARGIN = 256        # pre-call estimate headroom
CHARS_PER_TOK = 3       # conservative (real English ~4 chars/tok; lower = safer estimate)

# Family maps for the self-family audit (single-judge analog of the panel's no-self-grading rule).
# Substring-matched on lowercased names, first hit wins — mirrors ownership_judge.subject_family's
# style but covers the LOCAL model zoo (subjects AND judge candidates).
_FAMILY_PATTERNS = (
    ("llama", "llama"), ("gemma", "gemma"), ("qwen", "qwen"), ("granite", "granite"),
    ("mistral", "mistral"), ("mixtral", "mistral"), ("phi", "phi"), ("yi:", "yi"), ("yi-", "yi"),
    ("command-r", "cohere"), ("internlm", "internlm"), ("falcon", "falcon"), ("olmo", "olmo"),
    ("nemotron", "nemotron"), ("deepseek", "deepseek"), ("laguna", "qwen"),
    # empero claude-distills are Qwen3.5-based (project-cdms-quant-replication)
    ("claude-opus-distill", "qwen"), ("claude-code", "qwen"), ("claude-fable", "qwen"),
    ("claude-mythos", "qwen"),
)


def model_family(name: str) -> str | None:
    low = (name or "").lower()
    for pat, fam in _FAMILY_PATTERNS:
        if pat in low:
            return fam
    return None


def build_user_prompt(token: str, mode: str, response: str) -> str:
    """MUST stay byte-identical to ownership_judge.classify_one's user string (lock-tested)."""
    return f"TOKEN: {token}\nMODE: {mode}\nRESPONSE:\n{response}\n\nLabel:"


def _cache_path(cache_dir: Path, model: str, system: str, user: str) -> Path:
    key = hashlib.sha256(f"{model}\x00{system}\x00{user}".encode()).hexdigest()[:24]
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", model)
    return cache_dir / f"{safe}__{key}.json"


class CtxOverflowError(RuntimeError):
    """prompt_eval_count reached num_ctx — ollama front-truncated the prompt (rubric eaten)."""


def ollama_judge_call(model: str, system: str, user: str, cache_dir: Path,
                      url: str = DEFAULT_URL, num_ctx: int = DEFAULT_NUM_CTX,
                      n_predict: int = N_PREDICT, timeout: int = 900) -> dict:
    """One judged call -> {"response": str, "prompt_eval_count": int, "eval_duration": int}.
    Cached (never caches empty). Raises CtxOverflowError on detected truncation."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cp = _cache_path(cache_dir, model, system, user)
    if cp.exists():
        return json.loads(cp.read_text(encoding="utf-8"))
    payload = {
        "model": model, "think": False, "stream": False,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": n_predict, "num_ctx": num_ctx},
    }
    req = urllib.request.Request(f"{url}/api/chat", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    raw = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    out = {"response": (raw.get("message") or {}).get("content", ""),
           "prompt_eval_count": raw.get("prompt_eval_count"),
           "eval_duration": raw.get("eval_duration")}
    pec = out["prompt_eval_count"]
    if pec is not None and pec >= num_ctx - n_predict:
        raise CtxOverflowError(
            f"prompt_eval_count {pec} >= num_ctx-n_predict {num_ctx - n_predict} for {model} — "
            f"prompt was front-truncated; raise --num-ctx")
    if out["response"]:
        cp.write_text(json.dumps(out), encoding="utf-8")
    return out


def _est_tokens(system: str, user: str) -> int:
    return (len(system) + len(user)) // CHARS_PER_TOK


def is_passthrough(row: dict) -> bool:
    """Regex-non-surfaced rows: job-construction ground truth, never judged (by panel or local)."""
    return row.get("panel_label") == "ABSENT" and not row.get("votes")


def judge_row(row: dict, model: str, cache_dir: Path, url: str, num_ctx: int,
              gold: bool = False, timeout: int = 900) -> dict | None:
    """Return the local_* fields for one row, or None for passthrough rows."""
    if not gold and is_passthrough(row):
        return None
    response = row.get("response") or ""
    add = {"local_judge_model": model}
    jf, sf = model_family(model), model_family(row.get("subject_model", ""))
    add["local_self_family"] = bool(jf and sf and jf == sf)
    if _mechanical_invalid(response):
        add.update(local_label="INVALID", local_mechanical=True)
        return add
    user = build_user_prompt(row["token"], row["mode"], response)
    if _est_tokens(RUBRIC_A4, user) >= num_ctx - N_PREDICT - CTX_MARGIN:
        add.update(local_label=None, local_skip="ctx_overflow")
        return add
    out = ollama_judge_call(model, RUBRIC_A4, user, cache_dir, url=url, num_ctx=num_ctx,
                            timeout=timeout)
    add.update(local_label=_parse_label(out["response"], LABELS_A4),
               local_raw=out["response"][:120],
               local_prompt_eval_count=out["prompt_eval_count"])
    return add


def local_panel_result(response: str, token: str, mode: str, model: str, cache_dir: Path,
                       url: str = DEFAULT_URL, num_ctx: int = DEFAULT_NUM_CTX,
                       timeout: int = 900) -> dict:
    """panel_judge-shaped result from the LOCAL judge — the fresh-epoch adoption seam
    (multifact_judge --local-judge swaps panel_judge for this; same contract:
    {label, escalate, votes}). Mechanical-INVALID short-circuits before any call, identically to
    panel_judge; a single judge has no tie, so escalate is always False and votes carries the one
    'local' vote (breach_from_votes({"local": label}) resolves it downstream)."""
    if _mechanical_invalid(response):
        return {"label": "INVALID", "escalate": False, "votes": {}, "mechanical": True}
    user = build_user_prompt(token, mode, response)
    if _est_tokens(RUBRIC_A4, user) >= num_ctx - N_PREDICT - CTX_MARGIN:
        return {"label": None, "escalate": False, "votes": {"local": None},
                "local_skip": "ctx_overflow"}
    out = ollama_judge_call(model, RUBRIC_A4, user, cache_dir, url=url, num_ctx=num_ctx,
                            timeout=timeout)
    lab = _parse_label(out["response"], LABELS_A4)
    return {"label": lab, "escalate": False, "votes": {"local": lab}}


def _load_manifest(path: str | None):
    if not path:
        return None
    coords = {}
    for ln in open(path, encoding="utf-8"):
        if not ln.strip():
            continue
        r = json.loads(ln)
        coords.setdefault(Path(r["file"]).name, set()).add(int(r["line"]))
    return coords


def run_file(in_path: Path, out_path: Path, model: str, cache_dir: Path, url: str,
             num_ctx: int, gold: bool, manifest, limit: int | None, meta: dict,
             timeout: int = 900) -> None:
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    sel = manifest.get(in_path.name) if manifest else None
    n_judged = n_pass = n_skip = 0
    t0 = time.time()
    with open(in_path, encoding="utf-8", newline="") as fin, \
            open(tmp, "w", encoding="utf-8", newline="\n") as fout:
        for i, line in enumerate(fin):
            if not line.strip():
                continue
            if sel is not None and i not in sel:
                continue
            if limit is not None and n_judged >= limit:
                break
            row = json.loads(line)
            add = judge_row(row, model, cache_dir, url, num_ctx, gold=gold, timeout=timeout)
            if add is None:
                fout.write(line if line.endswith("\n") else line + "\n")  # byte-identical passthrough
                n_pass += 1
                continue
            if add.get("local_skip"):
                n_skip += 1
            row.update(add)
            fout.write(json.dumps(row) + "\n")
            n_judged += 1
            if n_judged % 200 == 0:
                rate = n_judged / max(time.time() - t0, 1e-9)
                print(f"  {in_path.name}: judged {n_judged} ({rate:.2f} rows/s)", flush=True)
    tmp.replace(out_path)
    meta["files"][in_path.name] = {"judged": n_judged, "passthrough": n_pass,
                                   "ctx_skipped": n_skip, "seconds": round(time.time() - t0, 1)}
    print(f"DONE {in_path.name}: judged={n_judged} passthrough={n_pass} ctx_skipped={n_skip} "
          f"({meta['files'][in_path.name]['seconds']}s)", flush=True)


def assert_digest_unchanged(cache_dir: Path, digest) -> None:
    """Digest guard (red-team S6): the response-cache key is the model NAME; a re-pull/update
    under the same name would silently serve stale labels across a resumed run. Pin the digest
    per cache dir; refuse on mismatch."""
    if not digest:
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    marker = cache_dir / "digest.txt"
    if marker.exists() and marker.read_text(encoding="utf-8").strip() != str(digest):
        raise SystemExit(
            f"cache dir {cache_dir} was built under model digest "
            f"{marker.read_text(encoding='utf-8').strip()!r}; server now serves {digest!r} — "
            f"the model changed under the same name; use a fresh --cache-dir")
    marker.write_text(str(digest), encoding="utf-8")


def _server_meta(url: str, model: str) -> dict:
    meta = {}
    try:
        meta["ollama_version"] = json.loads(urllib.request.urlopen(
            f"{url}/api/version", timeout=30).read()).get("version")
        req = urllib.request.Request(f"{url}/api/show", data=json.dumps({"model": model}).encode(),
                                     headers={"Content-Type": "application/json"})
        show = json.loads(urllib.request.urlopen(req, timeout=30).read())
        meta["model_digest"] = (show.get("details") or {}).get("parent_model") or show.get("digest")
        meta["model_details"] = show.get("details")
    except Exception as e:  # meta is best-effort; the run itself must not die on it
        meta["meta_error"] = repr(e)[:200]
    return meta


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inputs", nargs="+", help="committed *_JUDGE.jsonl files (or gold jsonl with --gold)")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--num-ctx", type=int, default=DEFAULT_NUM_CTX)
    ap.add_argument("--gold", action="store_true", help="gold-set mode (no passthrough class)")
    ap.add_argument("--sample-manifest", help="jsonl of {file, line} coords to restrict rows")
    ap.add_argument("--limit", type=int, help="judge at most N rows per file (probes)")
    ap.add_argument("--timeout", type=int, default=900,
                    help="per-call timeout (s); cold loads on this box run ~25s/GB — pre-warm "
                         "big models or raise this (ollama cancels a load when the client "
                         "request that triggered it disconnects)")
    args = ap.parse_args()

    out_dir, cache_dir = Path(args.out_dir), Path(args.cache_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest(args.sample_manifest)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", args.model)
    meta = {"model": args.model, "url": args.url, "num_ctx": args.num_ctx,
            "n_predict": N_PREDICT, "rubric_sha": hashlib.sha256(RUBRIC_A4.encode()).hexdigest(),
            "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "files": {},
            **_server_meta(args.url, args.model)}
    assert_digest_unchanged(cache_dir, meta.get("model_digest"))
    for fi, p in enumerate(args.inputs, 1):
        in_path = Path(p)
        out_path = out_dir / f"{in_path.stem}__{safe}.jsonl"
        run_file(in_path, out_path, args.model, cache_dir, args.url, args.num_ctx,
                 args.gold, manifest, args.limit, meta, timeout=args.timeout)
        done_rows = sum(f["judged"] for f in meta["files"].values())
        print(f"== progress: file {fi}/{len(args.inputs)}  cumulative judged {done_rows}", flush=True)
    (out_dir / f"localjudge_meta__{safe}.json").write_text(json.dumps(meta, indent=1),
                                                           encoding="utf-8")
    print("ALL FILES DONE", flush=True)


if __name__ == "__main__":
    main()
