"""A' panel vendor-health check for verdict-blind data audits (DISAMBIG D-F3 fix).

The per-epoch audit scripts flag a judge vendor as DEGENERATE when it stops discriminating
(rubber-stamps one label). A flat top-share threshold conflates "vendor broken" with "ground
truth skewed + vendor conservative": deepseek honestly sits at 0.79-0.96 OBSERVED across ALL
committed epochs (max 0.9606 in cons_p2, which passed its audit), so the old flat 0.95 BEM-mix
line false-fired inside a healthy vendor's range (DISAMBIG arm h, 0.9511 — dispositioned as
D-F3 in DISAMBIG_RESULTS.md).

Calibrated rule (empirical basis: sweep of all 37 committed gen_sweep/*_JUDGE.jsonl, 2026-07-10):
  DEGENERATE iff any of
    (a) single label voted;
    (b) top-share > 0.995 (absolute collapse line — above every healthy max in both arm kinds);
    (c) top-share > (this vendor's committed-epoch max for this arm kind) + 0.02
        (per-vendor drift line; unknown vendors fall back to (a)+(b) only, with a warning reason).

Caveats (registered here, on the artifact):
  - The baseline table is regenerated ONLY deliberately (run this module as a script) so a bad
    future epoch cannot silently raise its own bar; review the diff when updating.
  - Baselines are keyed by vendor NAME under the panel slugs pinned in the epoch preregs; if a
    vendor's model slug changes, its baseline is stale — re-sweep before reuse.
  - This check catches rubber-stamping, not subtle mislabeling; drift reports and 5-vendor
    pooling own that axis.
"""
from __future__ import annotations

# vendor -> healthy max top-label share observed across committed epochs, per arm kind.
# Swept 2026-07-10 over 37 files (32 bem-mix, 5 recall-only). Regenerate: python tools/panel_vendor_health.py
CALIBRATION = {
    "bem-mix": {
        "claude": 0.8738, "deepseek": 0.9606, "gemini": 0.8606, "gpt": 0.8996, "mistral": 0.7805,
    },
    "recall-only": {
        "claude": 0.9939, "deepseek": 0.9913, "gemini": 0.9865, "gpt": 0.9593, "mistral": 0.9510,
    },
}
ABSOLUTE_COLLAPSE = 0.995
DRIFT_MARGIN = 0.02


def vendor_degenerate(vendor: str, top_share: float, n_labels: int, kind: str):
    """Return (is_degenerate, reason). kind is 'bem-mix' or 'recall-only' (caller classifies
    the arm: recall-only = the file's modes are exactly {'recall'})."""
    if kind not in CALIBRATION:
        raise ValueError(f"unknown arm kind {kind!r} (expected 'bem-mix' or 'recall-only')")
    if n_labels <= 1:
        return True, "single label voted"
    if top_share > ABSOLUTE_COLLAPSE:
        return True, f"top-share {top_share:.4f} > absolute collapse line {ABSOLUTE_COLLAPSE}"
    base = CALIBRATION[kind].get(vendor)
    if base is None:
        return False, (f"vendor {vendor!r} has no committed baseline for {kind} — "
                       f"absolute rules only (re-sweep before relying on this)")
    trip = base + DRIFT_MARGIN
    if top_share > trip:
        return True, (f"top-share {top_share:.4f} > per-vendor drift line {trip:.4f} "
                      f"(committed max {base:.4f} + {DRIFT_MARGIN})")
    return False, f"healthy (top-share {top_share:.4f} <= {trip:.4f})"


def sweep(gen_sweep_dir="docs/validation/runtime_instrument/gen_sweep"):
    """Recompute the calibration table from every committed *_JUDGE.jsonl. Prints a table
    suitable for pasting into CALIBRATION; does not modify this file."""
    import glob
    import json
    from collections import Counter, defaultdict

    out = {"bem-mix": defaultdict(float), "recall-only": defaultdict(float)}
    files = sorted(glob.glob(f"{gen_sweep_dir}/*_JUDGE.jsonl"))
    for f in files:
        vend, modes = defaultdict(Counter), set()
        for ln in open(f, encoding="utf-8"):
            if not ln.strip():
                continue
            r = json.loads(ln)
            modes.add(r.get("mode"))
            if not r.get("votes"):
                continue
            for v, lab in r["votes"].items():
                vend[v][lab] += 1
        kind = "recall-only" if modes == {"recall"} else "bem-mix"
        for v, c in vend.items():
            share = c.most_common(1)[0][1] / sum(c.values())
            out[kind][v] = max(out[kind][v], share)
    print(f"# swept {len(files)} files")
    for kind, d in out.items():
        print(f'    "{kind}": {{')
        print("        " + ", ".join(f'"{v}": {s:.4f}' for v, s in sorted(d.items())) + ",")
        print("    },")
    return out


if __name__ == "__main__":
    sweep()
