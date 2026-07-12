"""Swap seam for verdict reproduction (LOCALJUDGE arc): committed JUDGE.jsonl + local-judge
mirror -> analyzer-ready clone with the panel's decision replaced by the local judge's.

Analyzers consume decisions through TWO fields (verified: multifact_analyze.py breach via
breach_from_votes(votes); disambig_analyze.py surfaced = NOT(panel_label=="ABSENT" and no votes);
blockframe_analyze.py recall surfacing via panel_label != "ABSENT" feeding verdict-bearing
G-AVAIL), so the swap must write BOTH coherently:

  - committed rows WITHOUT votes (regex-ABSENT + mechanical-INVALID) -> emitted from the ORIGINAL
    LINE BYTES (CRLF lesson, commit 4e59c13) — these were never judged by either instrument;
  - committed rows WITH votes -> votes={"local": <local_label>}, panel_label=<local_label>,
    escalate=False (escalate is reporting-only in all consumers); the committed decision is
    preserved under committed_panel_label / committed_votes (extra keys are inert — analyzers
    read specific keys only).

Interlocks: equal line counts and per-line identity on (subject_model, generation, arm, mode,
probe_idx, token) between committed and local files — a swapped/wrong pairing refuses loudly
(SystemExit), mirroring the disambig arm-slot lesson.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

IDENTITY = ("subject_model", "generation", "arm", "mode", "probe_idx", "token")


def swap_file(committed: Path, local: Path, out: Path) -> dict:
    c_lines = [l for l in open(committed, encoding="utf-8", newline="") if l.strip()]
    l_lines = [l for l in open(local, encoding="utf-8", newline="") if l.strip()]
    if len(c_lines) != len(l_lines):
        raise SystemExit(f"SWAP MISMATCH: {committed.name} has {len(c_lines)} rows, "
                         f"{local.name} has {len(l_lines)} — wrong pairing; refusing")
    n_swapped = n_pass = n_unparsed = 0
    with open(out, "w", encoding="utf-8", newline="\n") as fout:
        for i, (cl, ll) in enumerate(zip(c_lines, l_lines)):
            crow, lrow = json.loads(cl), json.loads(ll)
            cid = tuple(crow.get(k) for k in IDENTITY)
            lid = tuple(lrow.get(k) for k in IDENTITY)
            if cid != lid:
                raise SystemExit(f"SWAP MISMATCH at line {i}: committed {cid} != local {lid} "
                                 f"— files are not the same row universe; refusing")
            if not crow.get("votes"):
                fout.write(cl if cl.endswith("\n") else cl + "\n")
                n_pass += 1
                continue
            lab = lrow.get("local_label")
            if lab is None:
                n_unparsed += 1
            crow["committed_panel_label"] = crow.get("panel_label")
            crow["committed_votes"] = crow.get("votes")
            crow["votes"] = {"local": lab}
            crow["panel_label"] = lab
            crow["escalate"] = False
            crow["local_judge_model"] = lrow.get("local_judge_model")
            fout.write(json.dumps(crow) + "\n")
            n_swapped += 1
    return {"swapped": n_swapped, "passthrough": n_pass, "unparsed_local": n_unparsed}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--committed", required=True)
    ap.add_argument("--local", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    stats = swap_file(Path(args.committed), Path(args.local), Path(args.out))
    print(f"{Path(args.out).name}: swapped={stats['swapped']} passthrough={stats['passthrough']} "
          f"unparsed_local={stats['unparsed_local']}")


if __name__ == "__main__":
    main()
