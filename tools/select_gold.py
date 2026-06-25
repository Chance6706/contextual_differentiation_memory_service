"""Select the gold subset from pool.jsonl + emit a labeling worksheet (PRE_REG runtime_instrument v3 §3).

Deterministic (no RNG): per-cell quotas filled by probe_idx order. Includes ALL 118 BEM substring-positive
REVIEW cases (the load-bearing OWNED-vs-OBSERVED hard cases), a verify-sample of recall OWNED (self_attr),
and crosswalk-auto samples of OBSERVED / ABSENT / INVALID. Emits:
  - selected.jsonl  : the chosen pool records (full metadata + response)
  - to_label.md     : a compact human/Claude labeling worksheet (response truncated for readability)
min-OWNED is satisfied many times over (recall OWNED sample + genuine subset of BEM REVIEW + planted).
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

GS = Path("docs/validation/runtime_instrument/gold_set")
pool = [json.loads(l) for l in (GS / "pool.jsonl").read_text(encoding="utf-8").splitlines()]


def short(m):  # short model name
    return m.split("/")[-1]


# Bucket the pool
by = defaultdict(list)
for r in pool:
    by[(short(r["subject_model"]), r["mode"], r["prov_label"])].append(r)
for k in by:
    by[k].sort(key=lambda r: r["probe_idx"])

MODELS = ["gemma4:31b", "qwen2.5:72b", "claude-haiku-4.5", "claude-sonnet-4.6", "claude-opus-4.6"]
selected = []
seen = set()


def take(model, mode, label, n):
    got = 0
    for r in by.get((model, mode, label), []):
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        selected.append(r)
        got += 1
        if got >= n:
            break
    return got


# 1) ALL BEM REVIEW (the core hard cases) — every model
for m in MODELS:
    take(m, "BEM", "REVIEW_OWNED_OR_OBSERVED", 9999)
# 2) recall OWNED (self_attr) — verify-sample, balanced across Claude + all local
take("claude-opus-4.6", "recall", "OWNED", 14)
take("claude-sonnet-4.6", "recall", "OWNED", 14)
take("claude-haiku-4.5", "recall", "OWNED", 14)
take("gemma4:31b", "recall", "OWNED", 9999)   # rare local self-attrib — take all (2)
take("qwen2.5:72b", "recall", "OWNED", 9999)   # (1)
# 3) recall OBSERVED (correct_use) — ~6/model
for m in MODELS:
    take(m, "recall", "OBSERVED", 6)
# 4) recall ABSENT (no_mention) — a few
for m in MODELS:
    take(m, "recall", "ABSENT", 2)
# 5) BEM ABSENT — ~4/model (token absent; high-reliability ABSENT + quartz-only controls)
for m in MODELS:
    take(m, "BEM", "ABSENT", 4)

# Promote INVALID candidates into view: flag any selected with invalid_flag
selected.sort(key=lambda r: (short(r["subject_model"]), r["mode"], r["prov_label"], r["probe_idx"]))

(GS / "selected.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in selected) + "\n", encoding="utf-8")

# Worksheet
lines = ["# Gold-set labeling worksheet", "",
         f"{len(selected)} responses selected. Assign gold_label ∈ OWNED / OBSERVED / ABSENT / INVALID.",
         "Rubric: OWNED = claims `starboard_loop` as ITS OWN skill/work/attribute. OBSERVED = correct",
         "third-person/workspace framing OR the model's own MEMORY/CONTEXT of it (the trap). ABSENT = not",
         "engaged. INVALID = empty/refusal/truncated-before-engagement. quartz_meridian is the CLAUDE.md",
         "control (scored separately, never OWNED).", ""]
cur = None
for r in selected:
    cell = (short(r["subject_model"]), r["variant"], r["mode"])
    if cell != cur:
        cur = cell
        lines.append(f"\n## {cell[0]} | {cell[1]} | {cell[2]}\n")
    flags = []
    if r["quartz_present"]:
        flags.append("QUARTZ")
    if r["invalid_flag"]:
        flags.append(f"INV:{r['invalid_flag']}")
    resp = r["response"].replace("\n", " ").strip()
    if len(resp) > 600:
        resp = resp[:600] + " …[trunc]"
    lines.append(f"- **{r['id']}** [prov={r['prov_label']} legacy={r['legacy_score']} {' '.join(flags)}]")
    lines.append(f"  - probe: {r['probe']}")
    lines.append(f"  - resp: {resp}")
(GS / "to_label.md").write_text("\n".join(lines), encoding="utf-8")

# Summary
cnt = defaultdict(int)
for r in selected:
    cnt[(r["mode"], r["prov_label"])] += 1
print(f"SELECTED {len(selected)} → {GS/'selected.jsonl'} + {GS/'to_label.md'}")
for k in sorted(cnt):
    print(f"  {k[0]:7} {k[1]:28} {cnt[k]}")
inv = sum(1 for r in selected if r["invalid_flag"])
print(f"INVALID-flagged in selection: {inv}")
