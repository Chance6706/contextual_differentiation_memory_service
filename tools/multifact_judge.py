"""Reconstruct + A'-panel-judge the multi-fact scaffold cache (MULTIFACT_PREREG.md).

Unlike judge_ladder (one planted token), this judges each BEM response against EACH planted token in
the arm's scaffold (setup_bem_multifact(n)) — so per-token / union / multiplicity adoption all fall out
of the token-specific A' rubric. Reconstruction rebuilds the arm's preamble (n symmetric gists) so cache
keys match generation; a flag mismatch would reconstruct 0 responses (loud).

Output schema (one record per (response, token) that SURFACED, plus ABSENT rows for exact denominators):
  {subject_model, generation, arm (=n), mode, probe_idx, probe, response, token, panel_label, votes}
A response that surfaces 2 tokens yields 2 judged rows; tokens absent from a response yield ABSENT rows
(no spend). recall-mode rows are judged against EACH planted token too (a complete firewall check under
the n-gist store), same per-token surfacing rule.

Usage:
  python tools/multifact_judge.py SOURCES.json OUT.jsonl --multifact-n {1,3}
         [--subsample-n 130] [--rephrasings-cap 1] [--workers 12] [--cap 15] [--stamp multifact]
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

os.environ.setdefault("CDMS_EMBED_BACKEND", "hash")
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
import redteam_claude_md_interference as R  # noqa: E402
from ownership_judge import LABELS_A4, RUBRIC_A4, panel_judge  # noqa: E402
from openrouter_cost_guard import BudgetExceededError  # noqa: E402
from judge_ladder import safe_model, key_for, TSGuard  # noqa: E402

HOME = Path(os.path.expanduser("~"))


def tok_re(token: str):
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])")


def reconstruct(sources, n, variant="v1", subsample_n=130, rephrasings_cap=1, scaffold="multifact",
                sp_expansion=False):
    """Rebuild the arm's preamble, key each BEM+recall probe, pull cached responses.
    scaffold='multifact' -> setup_bem_multifact(n) (n gists); scaffold='filler' -> setup_bem_filler
    (1 achievement + 2 non-achievement fillers, length-matched to n=3). sp_expansion swaps the BEM bank."""
    if sp_expansion:
        from probes_sp_expansion import PROBES_SP_EXP as BEM_PROBES, REPHRASINGS_SP_EXP as BEM_REPH
    else:
        from probes_cleanstrata import PROBES_CLEANSTRATA as BEM_PROBES, REPHRASINGS_CLEANSTRATA as BEM_REPH
    import tempfile
    setup = R.setup_bem_filler if scaffold == "filler" else R.setup_bem_multifact(n)
    arm_label = "filler" if scaffold == "filler" else n
    with tempfile.TemporaryDirectory() as td:
        preamble = R._real_preamble_for_mode(setup, Path(td), variant=variant)
    modes = [("BEM", R.CLAUDE_MD_BEM, "BEM", BEM_PROBES, BEM_REPH),
             ("recall", "", "BEM_WORKSPACE_FACT", R.PROBES_BEM_WORKSPACE_FACT, None)]
    recs, miss = [], []
    for src in sources:
        backend, model = src["backend"], src["model"]
        leaf = Path(os.path.expanduser(src["cache_dir"])) / backend / "expand"
        sm = safe_model(backend, model)
        hits = 0
        for disp, claude_md, pkey, pconst, override in modes:
            system = R._system_prompt(claude_md, preamble)
            probes = R._select_probes(pkey, pconst, expand=True, subsample_n=subsample_n,
                                      rephrasings_cap=rephrasings_cap, rephrasings_override=override)
            for i, probe in enumerate(probes):
                user = probe if isinstance(probe, str) else probe[1]
                k = key_for(model, system, user)
                fn = (f"openrouter__{sm}__{k}.json" if backend == "openrouter" else f"{sm}__{k}.json")
                fp = leaf / fn
                if not fp.exists():
                    continue
                try:
                    resp = json.loads(fp.read_text(encoding="utf-8")).get("response")
                except (json.JSONDecodeError, OSError):
                    continue
                if not isinstance(resp, str):
                    continue
                hits += 1
                recs.append({"subject_model": model, "generation": src.get("generation", "?"),
                             "arm": arm_label, "mode": disp, "probe_idx": i, "probe": user, "response": resp})
        print(f"  {model:<28} {backend:<8} reconstructed {hits}", flush=True)
        if hits == 0:
            miss.append(model)
    return recs, miss


EXPECT_PER_MODEL = 146  # 130 BEM + 16 recall (clean-strata bank)


def assert_reconstruction_complete(recs, sources, allow_incomplete=False, expect_per_model=EXPECT_PER_MODEL):
    """Per-model completeness (pressure-test MUST_FIX): a partial cache (crash mid-model, or a triple-arm
    gist tie-order preamble mismatch) reconstructs < expected rows for a model. Ordered class-block
    emission means truncation drops later classes first -> biased missingness. Hard-fail loudly."""
    from collections import Counter
    per = Counter(r["subject_model"] for r in recs)
    bad = {m: per.get(m, 0) for m in {s["model"] for s in sources} if per.get(m, 0) != expect_per_model}
    if bad:
        print(f"  !! INCOMPLETE RECONSTRUCTION (expect {expect_per_model}/model): {bad}", flush=True)
        print("  !! likely a crash-truncated cache OR (triple arm) a gist tie-order preamble mismatch "
              "between generation and this host", flush=True)
        if not allow_incomplete:
            raise SystemExit(2)


def main():
    args = sys.argv[1:]
    sources_path, out_path = args[0], args[1]
    scaffold = "filler" if "--scaffold-filler" in args else "multifact"
    n = 1 if scaffold == "filler" else int(args[args.index("--multifact-n") + 1])
    subsample_n = int(args[args.index("--subsample-n") + 1]) if "--subsample-n" in args else 130
    rcap = int(args[args.index("--rephrasings-cap") + 1]) if "--rephrasings-cap" in args else 1
    workers = int(args[args.index("--workers") + 1]) if "--workers" in args else 12
    cap = float(args[args.index("--cap") + 1]) if "--cap" in args else 15.0
    stamp = args[args.index("--stamp") + 1] if "--stamp" in args else "multifact"
    recon_only = "--reconstruct-only" in args
    # filler judges T1 (the achievement) + the 2 FILLER_TOKENS (leak-check, expected ~0);
    # multifact judges the first n achievement tokens.
    tokens = (R.MULTIFACT_TOKENS[:1] + R.FILLER_TOKENS) if scaffold == "filler" else R.MULTIFACT_TOKENS[:n]
    token_res = {t: tok_re(t) for t in tokens}

    sp_expansion = "--sp-expansion-bank" in args
    sources = json.loads(Path(sources_path).read_text(encoding="utf-8"))
    print(f"=== reconstruct scaffold={scaffold} sp_expansion={sp_expansion} ({len(sources)} sources) ===",
          flush=True)
    recs, miss = reconstruct(sources, n, subsample_n=subsample_n, rephrasings_cap=rcap, scaffold=scaffold,
                             sp_expansion=sp_expansion)
    # sp-expansion bank = 31 facets * 2 variants = 62 BEM + 16 recall = 78/model; else clean-strata 146
    assert_reconstruction_complete(recs, sources, allow_incomplete="--allow-incomplete" in args,
                                   expect_per_model=(78 if sp_expansion else 146))

    # Build (response-record, token) judge jobs: only tokens that SURFACE spend; others -> ABSENT.
    jobs, absent = [], []
    for r in recs:
        surfaced = [t for t in tokens if token_res[t].search(r["response"] or "")]
        for t in tokens:
            base = {**{k: r[k] for k in ("subject_model", "generation", "arm", "mode",
                                         "probe_idx", "probe", "response")}, "token": t}
            if t in surfaced:
                jobs.append(base)
            else:
                absent.append({**base, "panel_label": "ABSENT", "escalate": False, "votes": {}})
    print(f"total reconstructed {len(recs)}; (response,token) surfacing jobs {len(jobs)} (to judge); "
          f"ABSENT rows {len(absent)}", flush=True)
    if miss:
        print(f"!! sources with ZERO reconstructed: {miss}", flush=True)
    if recon_only:
        print("(--reconstruct-only: stopping before judging)")
        return

    cache = HOME / "cdms_cache" / f"multifact_judge_{stamp}"
    cache.mkdir(parents=True, exist_ok=True)
    guard = TSGuard(cap)
    results, rlock, st = [], threading.Lock(), {"done": 0, "budget_hit": False}

    def work(j):
        try:
            res = panel_judge(j["response"], j["token"], j["mode"], j["subject_model"], cache,
                              cost_guard=guard, rubric=RUBRIC_A4, labels=LABELS_A4)
        except BudgetExceededError:
            with rlock:
                st["budget_hit"] = True     # pressure-test MUST_FIX: a dropped surfacing row corrupts
            return None                      # union/multiplicity denominators -> abort, never write partial
        rec = {**j, "panel_label": res["label"], "escalate": res["escalate"], "votes": res["votes"]}
        with rlock:
            results.append(rec); st["done"] += 1
            if st["done"] % 50 == 0:
                print(f"  judged {st['done']}/{len(jobs)}  spent=${guard._spent:.3f}", flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(work, j) for j in jobs]
        for _ in as_completed(futs):
            pass
    if st["budget_hit"] or len(results) != len(jobs):
        raise SystemExit(f"JUDGE INCOMPLETE: judged {len(results)}/{len(jobs)} surfacing jobs "
                         f"(budget_hit={st['budget_hit']}). Refusing to write a partial JUDGE file "
                         f"(a dropped surfacing row silently corrupts union/multiplicity). Raise --cap.")
    out = results + absent
    Path(out_path).write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + "\n",
                              encoding="utf-8")
    print(f"DONE: judged {len(results)} surfacing (response,token) + {len(absent)} ABSENT; "
          f"spent ${guard._spent:.3f} -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
