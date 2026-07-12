#!/usr/bin/env python3
"""Verdict-blind audit of local-judge Phase B outputs (LOCALJUDGE_PREREG §4).

Runs BEFORE any scoring. Checks structure only — it never compares a local label
to a committed vote/panel label, so reading its output cannot leak the verdict:

  1. line pairing: every output file has exactly the committed file's rows, in order;
     passthrough rows byte-identical; judged rows identical after stripping local_* keys;
  2. universe accounting: judged / passthrough / mechanical-INVALID / ctx-skip /
     parse-failure counts per file, reconciled against the meta sidecar;
  3. coverage of the DECIDED universe (rows where breach_from_votes is not None —
     the scorer's denominator): usable local_label in LABELS_A4; pooled + per-file;
  4. degeneracy: local-label marginals pooled + per-file max-share (vendor-health analog);
  5. self-family counts (roster disclosure check: gemma 196, others 0, qwen = probe).

Exit 1 on any structural failure (pairing/reconciliation); coverage/degeneracy are
REPORTED here and gated later by local_judge_score.py (G-B) — this tool does not gate
them, so a low number prints loudly but does not mask the rest of the audit.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from local_judge import is_passthrough, model_family  # noqa: E402
from ownership_judge import LABELS_A4, breach_from_votes  # noqa: E402

LOCAL_KEYS = {"local_judge_model", "local_self_family", "local_label", "local_raw",
              "local_prompt_eval_count", "local_skip", "local_mechanical"}
DEGENERACY_WARN = 0.995  # single-label collapse line, mirrors panel_vendor_health


def audit_file(committed: Path, local: Path) -> tuple[dict, list[str]]:
    errors: list[str] = []
    stats = Counter()
    labels = Counter()
    with committed.open(encoding="utf-8") as fc, local.open(encoding="utf-8") as fl:
        for i, (cline, lline) in enumerate(zip(fc, fl)):
            crow = json.loads(cline)
            if is_passthrough(crow):
                stats["passthrough"] += 1
                if lline != cline:
                    errors.append(f"{local.name}:{i + 1} passthrough row not byte-identical")
                continue
            lrow = json.loads(lline)
            stripped = {k: v for k, v in lrow.items() if k not in LOCAL_KEYS}
            if stripped != crow:
                errors.append(f"{local.name}:{i + 1} judged row differs from committed after "
                              f"stripping local_* keys")
            if lrow.get("local_self_family"):
                stats["self_family"] += 1
            if lrow.get("local_mechanical"):
                stats["mech_invalid"] += 1
            elif lrow.get("local_skip"):
                stats["ctx_skipped"] += 1
            elif lrow.get("local_label") in LABELS_A4:
                stats["judged"] += 1
                labels[lrow["local_label"]] += 1
            else:
                stats["parse_fail"] += 1
            if breach_from_votes(crow.get("votes") or {}) is not None:
                stats["decided"] += 1
                if lrow.get("local_label") in LABELS_A4:
                    stats["decided_covered"] += 1
        extra_c = sum(1 for _ in fc)
        extra_l = sum(1 for _ in fl)
    if extra_c or extra_l:
        errors.append(f"{local.name}: line-count mismatch (committed +{extra_c}, local +{extra_l})")
    stats["mech_invalid_or_judged"] = stats["judged"] + stats["mech_invalid"]
    if labels:
        top, top_n = labels.most_common(1)[0]
        share = top_n / sum(labels.values())
        if share > DEGENERACY_WARN:
            errors.append(f"{local.name}: DEGENERATE — {top} share {share:.4f} > {DEGENERACY_WARN}")
    return {"stats": stats, "labels": labels}, errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--committed-dir", required=True, help="dir with the 37 *_JUDGE.jsonl files")
    ap.add_argument("--local-dir", required=True, help="Phase B output dir for one candidate")
    ap.add_argument("--model", required=True, help="model name as embedded in output filenames")
    args = ap.parse_args()

    committed_dir, local_dir = Path(args.committed_dir), Path(args.local_dir)
    safe = args.model.replace(":", "_").replace("/", "_")
    locals_ = sorted(local_dir.glob(f"*_JUDGE__{safe}.jsonl"))
    if not locals_:
        print(f"FAIL: no *_JUDGE__{safe}.jsonl files in {local_dir}")
        return 1

    total, all_labels, failures = Counter(), Counter(), []
    per_file_cov = {}
    print(f"== verdict-blind audit: {args.model} ({len(locals_)} files) ==")
    for lp in locals_:
        cname = lp.name.split(f"__{safe}")[0] + ".jsonl"
        cp = committed_dir / cname
        if not cp.exists():
            failures.append(f"{lp.name}: no committed counterpart {cname}")
            continue
        result, errs = audit_file(cp, lp)
        failures.extend(errs)
        total.update(result["stats"])
        all_labels.update(result["labels"])
        s = result["stats"]
        cov = s["decided_covered"] / s["decided"] if s["decided"] else 1.0
        per_file_cov[cname] = cov
        flag = "" if cov >= 0.97 else "  <-- below per-channel line 0.97"
        print(f"  {cname}: judged={s['judged']} pass={s['passthrough']} mech={s['mech_invalid']} "
              f"ctx_skip={s['ctx_skipped']} parse_fail={s['parse_fail']} "
              f"decided_cov={cov:.4f}{flag}")

    meta_path = local_dir / f"localjudge_meta__{safe}.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        m_judged = sum(f.get("judged", 0) for f in meta.get("files", {}).values())
        m_skip = sum(f.get("ctx_skipped", 0) for f in meta.get("files", {}).values())
        if m_skip != total["ctx_skipped"]:
            failures.append(f"meta reconcile: ctx_skipped meta={m_skip} audited={total['ctx_skipped']}")
        print(f"meta sidecar: judged={m_judged} ctx_skipped={m_skip} "
              f"num_ctx={meta.get('num_ctx')} model={meta.get('model')}")
    else:
        failures.append(f"missing meta sidecar {meta_path.name}")

    pooled_cov = total["decided_covered"] / total["decided"] if total["decided"] else 0.0
    n_lab = sum(all_labels.values())
    print(f"\nTOTALS judged={total['judged']} passthrough={total['passthrough']} "
          f"mech_invalid={total['mech_invalid']} ctx_skipped={total['ctx_skipped']} "
          f"parse_fail={total['parse_fail']} self_family={total['self_family']}")
    print(f"decided universe={total['decided']}  pooled coverage={pooled_cov:.4f} "
          f"(gate line 0.98, enforced by scorer)")
    print("label marginals: " + ", ".join(
        f"{k}={v} ({v / n_lab:.3f})" for k, v in all_labels.most_common()))

    if failures:
        print(f"\nAUDIT FAIL — {len(failures)} structural failure(s):")
        for f in failures[:50]:
            print(f"  - {f}")
        return 1
    print("\nAUDIT PASS (structural). Coverage/degeneracy above are informational here; "
          "the scorer gates them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
