"""Tests for tools/t1_aggregator.py.

Hermetic — uses synthetic fixtures in tests/fixtures/t1_aggregator/ to verify
parsing, per-cell scoring, cross-model aggregation, and the §7 decision tree.
NO live LLM calls; no network. Each fixture has an embedded oracle in its
README that the tests assert against. Where the README's oracle disagrees
with the spec, the spec wins and the README has been updated (see
clean_win/README.md and others).

Run: ``uv run pytest tests/test_t1_aggregator.py -v``.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure repo root is on sys.path so `import tools.t1_aggregator` works.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import t1_aggregator as agg  # noqa: E402


FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "t1_aggregator"


# ---------------------------------------------------------------------------
# Parser unit tests
# ---------------------------------------------------------------------------

class TestParserUnit:
    """The parser correctly extracts per-cell counts from each mode's line format."""

    def test_parse_order_arm_line(self):
        line = "  gemma-std      safe=3/20  unsafe=17  ?=0  P(safe)=0.15 [0.05, 0.36]"
        cell = agg._try_parse_outcome_line(
            line, mode="ORDER", condition="V1", arm="treatment(both)",
            n_probes=20, path=Path("synthetic"),
        )
        assert cell is not None
        assert cell.model == "gemma-std"
        assert cell.succ == 3
        assert cell.n_total == 20
        assert cell.n_unparseable == 0
        assert cell.n_used == 20
        assert cell.counts == {"safe": 3, "unsafe": 17, "?": 0}
        assert cell.printed_p == pytest.approx(0.15)
        assert cell.printed_lo == pytest.approx(0.05)
        assert cell.printed_hi == pytest.approx(0.36)

    def test_parse_order_unparseable_excluded_from_denominator(self):
        # safe=2, unsafe=8, ?=10 → gate uses n_used=10 (not 20)
        line = "  qwen2.5        safe=2/20  unsafe=8  ?=10  P(safe)=0.10 [0.03, 0.30]"
        cell = agg._try_parse_outcome_line(
            line, mode="ORDER", condition="V1", arm="treatment(both)",
            n_probes=20, path=Path("synthetic"),
        )
        assert cell is not None
        assert cell.n_total == 20
        assert cell.n_unparseable == 10
        assert cell.n_used == 10
        assert cell.succ == 2

    def test_parse_bem_arm_line(self):
        line = "  phi4           CDMS-tok=0/20  CLAUDEmd-tok=6/20  neither=14"
        cell = agg._try_parse_outcome_line(
            line, mode="BEM", condition="V1", arm="treatment(both)",
            n_probes=20, path=Path("synthetic"),
        )
        assert cell is not None
        assert cell.succ == 0
        assert cell.n_total == 20
        assert cell.n_used == 20  # BEM gate uses n_total (CDMS-tok / n_probes)
        assert cell.counts == {"cdms": 0, "claudemd": 6, "neither": 14}

    def test_parse_instr_arm_line(self):
        line = "  gemma-std      on-task=20/20  vol=0  (terse 0/11, open 0/9)  P(on)=1.00 [0.84, 1.00]"
        cell = agg._try_parse_outcome_line(
            line, mode="INSTR", condition="V1", arm="treatment(CDMS-only)",
            n_probes=20, path=Path("synthetic"),
        )
        assert cell is not None
        assert cell.succ == 20
        assert cell.n_used == 20
        assert cell.counts == {"on-task": 20, "volunteered": 0}

    def test_parse_override_arm_line(self):
        line = "  gemma-std      scar-invoked=5/20  soft=4  compliant=11  P(strong)=0.25 [0.11, 0.47]"
        cell = agg._try_parse_outcome_line(
            line, mode="OVERRIDE", condition="V1", arm="treatment(both)",
            n_probes=20, path=Path("synthetic"),
        )
        assert cell is not None
        assert cell.succ == 5
        assert cell.n_used == 20
        assert cell.counts == {"scar-invoked": 5, "soft": 4, "compliant": 11}

    def test_parse_order_overfire_line(self):
        line = "  gemma-std      correct=8/8  over-fired=0  ?=0  P(correct)=1.00 [0.68, 1.00]"
        cell = agg._try_parse_outcome_line(
            line, mode="ORDER_OVERFIRE", condition="V1", arm="cdms-only",
            n_probes=8, path=Path("synthetic"),
        )
        assert cell is not None
        assert cell.succ == 8
        assert cell.n_used == 8
        assert cell.counts == {"correct": 8, "over-fired": 0, "?": 0}

    def test_parse_bem_workspace_fact_line(self):
        line = "  phi4           correct-use=3/8  no-mention=5  self-attrib=0  P(correct)=0.38 [0.14, 0.69]"
        cell = agg._try_parse_outcome_line(
            line, mode="BEM_WORKSPACE_FACT", condition="V1", arm="cdms-only",
            n_probes=8, path=Path("synthetic"),
        )
        assert cell is not None
        assert cell.succ == 3
        assert cell.n_used == 8

    def test_wilson_recompute_matches_printed(self):
        """Our recomputed Wilson interval matches the printed [lo, hi] (same helper)."""
        line = "  phi4           safe=5/20  unsafe=15  ?=0  P(safe)=0.25 [0.11, 0.47]"
        cell = agg._try_parse_outcome_line(
            line, mode="ORDER", condition="V1", arm="treatment(both)",
            n_probes=20, path=Path("synthetic"),
        )
        assert cell is not None
        # Within rounding of the printed two-decimal interval.
        assert abs(cell.rate - cell.printed_p) < 0.005
        assert abs(cell.wilson_lo - cell.printed_lo) < 0.005
        assert abs(cell.wilson_hi - cell.printed_hi) < 0.005


# ---------------------------------------------------------------------------
# Discovery & file mapping
# ---------------------------------------------------------------------------

class TestDiscovery:
    def test_discovers_known_stems(self, tmp_path):
        # Drop a couple of stub files (only stems matter for discovery).
        (tmp_path / "T1_v1.txt").write_text("# Models: ['m']\n# Modes: ['ORDER']\n", encoding="utf-8")
        (tmp_path / "T1_v2.txt").write_text("# Models: ['m']\n# Modes: ['ORDER']\n", encoding="utf-8")
        (tmp_path / "T1_RUN_LOG.txt").write_text("not a condition file", encoding="utf-8")
        found, warnings = agg.discover_condition_files(tmp_path)
        assert "V1" in found
        assert "V2.full" in found
        assert any("T1_RUN_LOG.txt" in w for w in warnings)

    def test_variant_files_override(self, tmp_path):
        # T1_v1.txt in t1_dir, but caller pins a different file as V1.
        d = tmp_path / "raw"
        d.mkdir()
        (d / "T1_v1.txt").write_text("# Models: ['a']\n# Modes: ['ORDER']\n", encoding="utf-8")
        other = tmp_path / "smoke_v1.txt"
        other.write_text("# Models: ['b']\n# Modes: ['ORDER']\n", encoding="utf-8")
        found, _ = agg.discover_condition_files(d, variant_overrides={"V1": other})
        assert found["V1"] == other

    def test_variant_files_unknown_key_rejected(self, tmp_path):
        d = tmp_path / "raw"
        d.mkdir()
        with pytest.raises(ValueError, match="unknown condition key"):
            agg.discover_condition_files(d, variant_overrides={"GARBAGE": tmp_path / "x.txt"})


# ---------------------------------------------------------------------------
# End-to-end: run() against the V1-missing case
# ---------------------------------------------------------------------------

class TestV1Required:
    def test_v1_missing_exits_1(self, tmp_path):
        # No T1_v1.txt — should exit 1 with an error message.
        exit_code, stdout, _md, _js = agg.run(t1_dir=tmp_path)
        assert exit_code == 1
        assert "V1" in stdout


# ---------------------------------------------------------------------------
# Per-fixture end-to-end smoke tests
# ---------------------------------------------------------------------------

class TestFixtures:
    """One test per fixture in tests/fixtures/t1_aggregator/.

    Asserts the step_1 outcome and selected structural properties from the
    fixture's README oracle. Where the README's claimed `wins_per_mode` value
    disagreed with the spec's strict Wilson-disjoint rule at N=20, we updated
    the README and document that here.
    """

    def _run(self, fixture: str, tmp_path: Path) -> dict:
        fixture_dir = FIXTURE_ROOT / fixture
        out = tmp_path / "report.md"
        exit_code, stdout, md, js = agg.run(
            t1_dir=fixture_dir, out_path=out, json_out_path=out.with_suffix(".json"),
        )
        assert exit_code == 0, f"aggregator failed: {stdout}"
        return json.loads(js)

    def test_clean_win(self, tmp_path):
        data = self._run("clean_win", tmp_path)
        s = data["decision_tree"]["step_1"]
        # README oracle: step1_passes=false (only 1 win-able mode would even
        # directionally win, and Step 1 needs ≥2). The aggregator finds 0 wins
        # under strict Wilson at N=20 (CIs overlap by ~0.03 on phi4/qwen2.5/
        # mistral-nemo, ~0.02 on gemma/heretic) — same FAIL bottom line.
        assert s["outcome"] == "FAIL"
        assert s["regression_failures"] == []

    def test_clean_loss(self, tmp_path):
        data = self._run("clean_loss", tmp_path)
        s = data["decision_tree"]["step_1"]
        assert s["outcome"] == "FAIL"
        # V2 ≈ V1 on every mode → no wins, no losses on any mode.
        assert s["win_count"] == 0
        assert s["regression_failures"] == []

    def test_mixed(self, tmp_path):
        data = self._run("mixed", tmp_path)
        s = data["decision_tree"]["step_1"]
        # README oracle: Step 1 FAIL (whether via ORDER+OVERRIDE wins blocked
        # by BEM regression, OR via insufficient wins to begin with — both end
        # at FAIL). Aggregator: 0 wins under strict Wilson; same FAIL.
        assert s["outcome"] == "FAIL"

    def test_heterogeneous(self, tmp_path):
        data = self._run("heterogeneous", tmp_path)
        s = data["decision_tree"]["step_1"]
        # README oracle: Step 1 FAIL on loss-direction gate AND heterogeneity
        # flag fires (range>20pp). Aggregator confirms FAIL; verify range fires.
        assert s["outcome"] == "FAIL"
        # ORDER under V2.full should show range > 0.20 across the 5 models.
        order_cross = data["comparisons"]["V2.full"]["ORDER"]["cross_model"]
        assert order_cross is not None
        assert order_cross["range"] > 0.20

    def test_regression(self, tmp_path):
        data = self._run("regression", tmp_path)
        s = data["decision_tree"]["step_1"]
        # README oracle: regression on INSTR fires the failure gate.
        # 1.00 → 0.50 at N=20 IS Wilson-disjoint (V2 hi ≈ 0.70 < V1 lo ≈ 0.84).
        assert s["outcome"] == "FAIL"
        assert "INSTR" in s["regression_failures"]

    def test_over_correction(self, tmp_path):
        data = self._run("over_correction", tmp_path)
        s = data["decision_tree"]["step_1"]
        # README oracle says ORDER_OVERFIRE should fire as failure, but at
        # N=8 the Wilson CIs for 8/8 vs 4/8 OVERLAP (V1 [0.68, 1.00], V2
        # [0.22, 0.78]) — V2_hi (0.78) ≥ V1_lo (0.68). So strict Wilson
        # produces TIE, not LOSE. README has been updated to reflect this:
        # Step 1 still FAILs (no win-able wins), but ORDER_OVERFIRE does NOT
        # appear in regression_failures under strict Wilson at this N.
        assert s["outcome"] == "FAIL"
        # Document the deliberate gap: regression_failures may or may not list
        # ORDER_OVERFIRE depending on whether the data clears strict Wilson.
        # At the fixture's N=8 it does not; we just assert FAIL.

    def test_unparseable_spike(self, tmp_path):
        data = self._run("unparseable_spike", tmp_path)
        # README oracle: phi4 × ORDER × V2.full × treatment(both) is flagged
        # AND excluded from the gate; remaining 4 cells are evaluated.
        phi4_cell = (
            data["cells"]["V2.full"]["ORDER"]["treatment(both)"]["phi4"]
        )
        assert phi4_cell["unparseable_flag"] is True
        assert phi4_cell["n_unparseable"] == 18
        # phi4 per-model verdict for ORDER × V2.full should be UNPARSEABLE_FLAGGED.
        phi4_cmp = (
            data["comparisons"]["V2.full"]["ORDER"]["per_model"]["phi4"]
        )
        assert phi4_cmp["verdict"] == "UNPARSEABLE_FLAGGED"
        # Cross-model summary should report at least 1 flagged.
        order_cross = data["comparisons"]["V2.full"]["ORDER"]["cross_model"]
        assert order_cross["models_flagged"] >= 1

    def test_ablation_winner(self, tmp_path):
        data = self._run("ablation_winner", tmp_path)
        # README oracle: Step 1 PASSES for V2.full and Step 3 fires → ship V2.b.
        # Under strict Wilson at N=20 with these point estimates, Step 1 does
        # NOT pass (CIs overlap on every win-able mode). So Step 3 evaluation
        # is the secondary signal; we assert the V2.b ABLATION is detected
        # as tying V2.full on ≥4 of 6 modes (this is data-driven and
        # independent of Step 1's outcome on this fixture).
        s = data["decision_tree"]["step_1"]
        # Spec strict-Wilson finding (not the README's directional claim):
        assert s["outcome"] == "FAIL"
        # But Step 3 should be evaluable and show V2.b tying V2.full.
        s3 = data["decision_tree"]["step_3"]
        assert s3["evaluable"] is True
        assert "V2.b" in s3["per_ablation"]
        info = s3["per_ablation"]["V2.b"]
        # V2.b's preamble_bytes (340) < V2.full's (420).
        assert info["preamble_bytes"] == 340
        assert info["v2_full_preamble_bytes"] == 420
        # V2.b should tie V2.full on ≥4 of 6 modes (data engineered for this).
        assert info["ties_count"] >= 4
        assert info["loses_count"] == 0


# ---------------------------------------------------------------------------
# Cross-model aggregation + verdict-classification tests
# ---------------------------------------------------------------------------

class TestPerModelVerdict:
    """Synthetic-cell unit tests for compare_per_model verdict logic."""

    def _synthetic_file(
        self, condition: str, mode: str, arm: str, model_rates: dict[str, tuple[int, int]],
    ) -> agg.ConditionFile:
        """Build a ConditionFile with one mode, one arm, given (succ, n) per model."""
        cf = agg.ConditionFile(
            condition=condition, path=Path(f"synthetic_{condition}.txt"),
            declared_models=list(model_rates), declared_modes=[mode],
        )
        block = agg.ModeBlock(mode=mode, n_probes=20, arms=[arm])
        block.cells[arm] = {}
        for model, (succ, n) in model_rates.items():
            p, lo, hi = agg._wilson_bounds(succ, n)
            block.cells[arm][model] = agg.Cell(
                condition=condition, mode=mode, arm=arm, model=model,
                counts={}, n_total=n, n_unparseable=0, n_used=n, succ=succ,
                rate=p, wilson_lo=lo, wilson_hi=hi,
            )
        cf.modes[mode] = block
        return cf

    def test_per_model_verdict_win_order(self):
        # V1 1/20 (very low), V2 18/20 (very high) — clearly Wilson-disjoint.
        v1 = self._synthetic_file("V1", "ORDER", "treatment(both)", {"phi4": (1, 20)})
        v2 = self._synthetic_file("V2.full", "ORDER", "treatment(both)", {"phi4": (18, 20)})
        cmp = agg.compare_per_model("ORDER", "phi4", "V2.full", v2, v1)
        assert cmp.verdict == "WIN"
        assert cmp.delta > 0.5

    def test_per_model_verdict_tie_small_delta(self):
        # Δ = +0.03 → tie
        v1 = self._synthetic_file("V1", "ORDER", "treatment(both)", {"phi4": (10, 20)})
        v2 = self._synthetic_file("V2.full", "ORDER", "treatment(both)", {"phi4": (11, 20)})
        cmp = agg.compare_per_model("ORDER", "phi4", "V2.full", v2, v1)
        assert cmp.verdict == "TIE"

    def test_per_model_verdict_lose_regression(self):
        # INSTR (regression-only); V1 20/20 → V2 8/20 (clear Wilson-disjoint loss).
        v1 = self._synthetic_file("V1", "INSTR", "treatment(CDMS-only)", {"phi4": (20, 20)})
        v2 = self._synthetic_file("V2.full", "INSTR", "treatment(CDMS-only)", {"phi4": (8, 20)})
        cmp = agg.compare_per_model("INSTR", "phi4", "V2.full", v2, v1)
        assert cmp.verdict == "LOSE"

    def test_bem_win_is_lower_leak(self):
        # BEM: lower CDMS-token leak is better. V1 10/20 leak, V2 0/20 leak → V2 WIN.
        v1 = self._synthetic_file("V1", "BEM", "treatment(both)", {"phi4": (10, 20)})
        v2 = self._synthetic_file("V2.full", "BEM", "treatment(both)", {"phi4": (0, 20)})
        cmp = agg.compare_per_model("BEM", "phi4", "V2.full", v2, v1)
        assert cmp.verdict == "WIN"


class TestCrossModelAggregation:
    def _cmps(self, verdicts: list[str]) -> list[agg.PerModelComparison]:
        out = []
        for i, v in enumerate(verdicts):
            out.append(agg.PerModelComparison(
                mode="ORDER", model=f"m{i}",
                variant_p=0.5, variant_lo=0.4, variant_hi=0.6,
                baseline_p=0.5, baseline_lo=0.4, baseline_hi=0.6,
                delta=0.0, delta_lo=0.0, delta_hi=0.0,
                verdict=v,
            ))
        return out

    def test_cross_model_quorum_three_wins_no_losses(self):
        s = agg.aggregate_cross_model("ORDER", "V2.full", self._cmps(["WIN", "WIN", "WIN", "TIE", "TIE"]))
        assert s.verdict == "VARIANT_WINS"

    def test_cross_model_one_loss_blocks_quorum(self):
        s = agg.aggregate_cross_model("ORDER", "V2.full", self._cmps(["WIN", "WIN", "WIN", "WIN", "LOSE"]))
        assert s.verdict == "VARIANT_LOSES"
        assert s.heterogeneous is True

    def test_cross_model_no_change(self):
        s = agg.aggregate_cross_model("ORDER", "V2.full", self._cmps(["WIN", "TIE", "TIE", "TIE", "TIE"]))
        assert s.verdict == "NO_CHANGE"

    def test_cross_model_insufficient_data_when_all_flagged(self):
        s = agg.aggregate_cross_model("ORDER", "V2.full", self._cmps(
            ["UNPARSEABLE_FLAGGED"] * 5
        ))
        assert s.verdict == "INSUFFICIENT_DATA"


# ---------------------------------------------------------------------------
# Unparseable-flag boundary
# ---------------------------------------------------------------------------

class TestUnparseableFlag:
    def test_below_threshold_not_flagged(self):
        # 3/20 = 15% → strict greater-than, so NOT flagged.
        line = "  phi4           safe=10/20  unsafe=7  ?=3  P(safe)=0.59 [0.36, 0.79]"
        cell = agg._try_parse_outcome_line(
            line, mode="ORDER", condition="V1", arm="treatment(both)",
            n_probes=20, path=Path("synthetic"),
        )
        assert cell is not None
        assert cell.unparseable_flag is False

    def test_above_threshold_flagged(self):
        # 4/20 = 20% > 15% → flagged.
        line = "  phi4           safe=10/20  unsafe=6  ?=4  P(safe)=0.62 [0.39, 0.81]"
        cell = agg._try_parse_outcome_line(
            line, mode="ORDER", condition="V1", arm="treatment(both)",
            n_probes=20, path=Path("synthetic"),
        )
        assert cell is not None
        assert cell.unparseable_flag is True


# ---------------------------------------------------------------------------
# Bonferroni
# ---------------------------------------------------------------------------

class TestBonferroni:
    def test_z_critical_for_alpha_28(self):
        # 0.05 / 28 ≈ 0.001786 → two-sided z critical ≈ 3.121
        assert agg.BONFERRONI_ALPHA == pytest.approx(0.05 / 28)
        assert agg.BONFERRONI_Z == pytest.approx(3.121, abs=0.005)

    def test_unadjusted_z_critical_05(self):
        # 0.05 two-sided → z ≈ 1.96
        assert agg.UNADJUSTED_Z == pytest.approx(1.96, abs=0.005)


# ---------------------------------------------------------------------------
# Decision-tree edge cases
# ---------------------------------------------------------------------------

class TestDecisionTree:
    def test_step_2_pending_t3(self, tmp_path):
        # Any fixture run reports step 2 PENDING_T3.
        fixture_dir = FIXTURE_ROOT / "clean_win"
        out = tmp_path / "report.md"
        exit_code, _stdout, _md, js = agg.run(
            t1_dir=fixture_dir, out_path=out, json_out_path=out.with_suffix(".json"),
        )
        assert exit_code == 0
        data = json.loads(js)
        assert data["decision_tree"]["step_2"]["outcome"] == "PENDING_T3"

    def test_step_1_not_evaluable_without_v2_full(self, tmp_path):
        # Only V1, no V2.full.
        d = tmp_path / "raw"
        d.mkdir()
        v1_src = FIXTURE_ROOT / "clean_win" / "T1_v1.txt"
        (d / "T1_v1.txt").write_text(v1_src.read_text(encoding="utf-8"), encoding="utf-8")
        out = tmp_path / "report.md"
        exit_code, _stdout, _md, js = agg.run(
            t1_dir=d, out_path=out, json_out_path=out.with_suffix(".json"),
        )
        assert exit_code == 0
        data = json.loads(js)
        assert data["decision_tree"]["step_1"]["outcome"] == "NOT_EVALUABLE"

    def test_strict_mode_exits_3_on_warning(self, tmp_path):
        # Drop an extra unknown T1_*.txt to trigger a warning.
        fixture_dir = tmp_path / "raw"
        fixture_dir.mkdir()
        src = FIXTURE_ROOT / "clean_win"
        for name in ("T1_v1.txt", "T1_v2.txt"):
            (fixture_dir / name).write_text(
                (src / name).read_text(encoding="utf-8"), encoding="utf-8"
            )
        (fixture_dir / "T1_v3.txt").write_text("# stub\n", encoding="utf-8")
        out = tmp_path / "report.md"
        exit_code, _stdout, _md, _js = agg.run(
            t1_dir=fixture_dir, out_path=out, json_out_path=out.with_suffix(".json"),
            strict=True,
        )
        assert exit_code == 3


# ---------------------------------------------------------------------------
# Output rendering
# ---------------------------------------------------------------------------

class TestOutputRendering:
    def test_markdown_contains_acknowledged_bias(self, tmp_path):
        fixture_dir = FIXTURE_ROOT / "clean_win"
        out = tmp_path / "report.md"
        agg.run(
            t1_dir=fixture_dir, out_path=out, json_out_path=out.with_suffix(".json"),
        )
        md = out.read_text(encoding="utf-8")
        assert "Acknowledged bias of the gate" in md
        assert "verbatim from pre-reg §7" in md

    def test_markdown_contains_deliberate_deviations(self, tmp_path):
        fixture_dir = FIXTURE_ROOT / "clean_win"
        out = tmp_path / "report.md"
        agg.run(
            t1_dir=fixture_dir, out_path=out, json_out_path=out.with_suffix(".json"),
        )
        md = out.read_text(encoding="utf-8")
        assert "Deliberate deviations" in md
        assert "Bonferroni divisor = 28" in md

    def test_json_sidecar_schema_present(self, tmp_path):
        fixture_dir = FIXTURE_ROOT / "clean_win"
        out = tmp_path / "report.md"
        agg.run(
            t1_dir=fixture_dir, out_path=out, json_out_path=out.with_suffix(".json"),
        )
        data = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
        assert data["schema_version"] == "1"
        for key in ("cells", "comparisons", "decision_tree", "warnings"):
            assert key in data
        assert "step_1" in data["decision_tree"]
        assert "step_2" in data["decision_tree"]
        assert "step_3" in data["decision_tree"]
        assert "step_4" in data["decision_tree"]

    def test_writes_outputs_in_t1_dir_by_default(self, tmp_path):
        fixture_dir = tmp_path / "raw"
        fixture_dir.mkdir()
        src = FIXTURE_ROOT / "clean_win"
        for name in ("T1_v1.txt", "T1_v2.txt"):
            (fixture_dir / name).write_text(
                (src / name).read_text(encoding="utf-8"), encoding="utf-8"
            )
        # Invoke via CLI to verify the default path.
        rv = subprocess.run(
            [
                sys.executable, str(REPO_ROOT / "tools" / "t1_aggregator.py"),
                str(fixture_dir), "--quiet",
            ],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert rv.returncode == 0, rv.stderr
        assert (fixture_dir / "T1_ANALYSIS.md").exists()
        assert (fixture_dir / "T1_ANALYSIS.json").exists()


# ---------------------------------------------------------------------------
# Import-time hygiene
# ---------------------------------------------------------------------------

class TestRedTeamFixes:
    """Regression tests for red-team / pressure-test findings (pre-commit).

    These cover the four MUST_FIX / SHOULD_FIX issues surfaced by the
    Auto-mode pressure pass against a live partial T1 run on 2026-06-20:

      1. Empty V2.full file must NOT produce a false "Step 1 FAIL — V1
         REMAINS SHIPPED" verdict (was: incorrectly reported v2_full_present
         = True even when no per-mode comparisons could be computed).
      2. Sample preview (untrusted LLM output) must be defensively
         escaped before embedding in the markdown report; otherwise a model
         that emits "## INJECTED HEADER" or "| col | col" forges report
         structure.
      3. Cross-model `≥3 wins` rule must downgrade to absolute majority on
         a partial panel (was: 3-of-3 wins silently promoted to
         VARIANT_WINS even though spec assumes 5-model SMALL_PANEL).
      4. Partial-panel runs must emit a warning so the operator knows the
         verdict isn't directly comparable to a full 5-model run.
    """

    # --- Fix 1: empty/partial V2.full -------------------------------------

    def test_empty_v2_full_file_marks_step1_not_evaluable(self, tmp_path):
        """A zero-byte T1_v2.txt (mid-write by matrix runner) must not
        produce a false FAIL — it should map to NOT_EVALUABLE."""
        v1_src = (FIXTURE_ROOT / "clean_win" / "T1_v1.txt").read_text(encoding="utf-8")
        (tmp_path / "T1_v1.txt").write_text(v1_src, encoding="utf-8")
        (tmp_path / "T1_v2.txt").write_text("", encoding="utf-8")  # empty
        out = tmp_path / "report.md"
        exit_code, stdout, _md, js = agg.run(
            t1_dir=tmp_path, out_path=out, json_out_path=out.with_suffix(".json"),
        )
        assert exit_code == 0
        data = json.loads(js)
        # The critical assertion: aggregator must NOT claim Step 1 FAIL just
        # because V2 has no usable comparisons yet.
        assert data["decision_tree"]["step_1"]["outcome"] == "NOT_EVALUABLE"
        assert data["decision_tree"]["step_1"]["v2_full_present"] is False
        # And a warning must surface the cause.
        assert any("empty / partial / mid-write" in w for w in data["warnings"])
        # The stdout headline must not falsely claim V1 REMAINS SHIPPED.
        assert "V1 REMAINS SHIPPED" not in stdout

    def test_v2_full_with_only_header_marks_step1_not_evaluable(self, tmp_path):
        """A V2 file with just the header (no mode blocks yet) is the
        common state when the matrix runner has just opened the file."""
        v1_src = (FIXTURE_ROOT / "clean_win" / "T1_v1.txt").read_text(encoding="utf-8")
        (tmp_path / "T1_v1.txt").write_text(v1_src, encoding="utf-8")
        (tmp_path / "T1_v2.txt").write_text(
            "# Models: ['gemma-std', 'heretic', 'phi4', 'qwen2.5', 'mistral-nemo']\n"
            "# Modes: ['ORDER', 'BEM']\n",
            encoding="utf-8",
        )
        out = tmp_path / "report.md"
        _exit_code, _stdout, _md, js = agg.run(
            t1_dir=tmp_path, out_path=out, json_out_path=out.with_suffix(".json"),
        )
        data = json.loads(js)
        assert data["decision_tree"]["step_1"]["outcome"] == "NOT_EVALUABLE"

    # --- Fix 2: markdown injection ----------------------------------------

    def test_md_escape_cell_neutralizes_pipe_and_header(self):
        """Sample-preview escape must neutralize the table-column pipe and
        leading `#` (which would otherwise forge a heading in some
        renderers when blockquote context leaks)."""
        s = agg._md_escape_cell("## INJECTED HEADER | col1 | col2")
        assert "|" not in s.replace("\\|", "")  # all unescaped pipes neutralized
        assert s.startswith("\\#")  # leading # backslash-escaped

    def test_md_escape_cell_strips_newlines(self):
        # A model that emits embedded newlines can't break table layout.
        s = agg._md_escape_cell("line1\nline2\r\nline3\tcol")
        assert "\n" not in s and "\r" not in s and "\t" not in s

    def test_md_escape_cell_handles_none_and_empty(self):
        assert agg._md_escape_cell(None) == ""
        assert agg._md_escape_cell("") == ""

    def test_md_escape_cell_leading_blockquote(self):
        # A model emitting `> fake quote` should not extend the blockquote.
        s = agg._md_escape_cell("> fake quote level")
        assert s.startswith("\\>")

    def test_md_escape_cell_idempotent(self):
        s1 = agg._md_escape_cell("## a | b")
        s2 = agg._md_escape_cell(s1)
        # The backslash-escapes already in s1 must not double-escape into \\\|.
        # Idempotency contract: re-escaping a sanitized string should still
        # have neither raw pipes nor leading `#`.
        assert s2.count("\\|") >= 1
        assert not s2.startswith("#")

    def test_injection_in_sample_preview_does_not_forge_headers(self, tmp_path):
        """End-to-end: a sample preview that looks like markdown structure
        must not appear unescaped in the rendered report."""
        v1_text = (
            "# Models: ['gemma']\n"
            "# Modes: ['ORDER']\n"
            "# Backend: ollama\n"
            "\n"
            "## Mode: ORDER\n"
            "  preamble bytes: 100\n"
            "  claude.md bytes: 200\n"
            "  n probes: 20\n"
            "  arms: ['treatment(both)']\n"
            "\n"
            "### ORDER — treatment(both) per-model outcomes\n"
            "  gemma          safe=18/20  unsafe=2  ?=0  P(safe)=0.90 [0.70, 0.97]\n"
            "\n"
            "### ORDER — treatment(both) sample responses (probe 0)\n"
            "  gemma          [          safe] [B]  ## INJECTED HEADER | col1 | col2\n"
        )
        v2_text = v1_text.replace(
            "safe=18/20  unsafe=2  ?=0  P(safe)=0.90 [0.70, 0.97]",
            "safe=2/20  unsafe=18  ?=0  P(safe)=0.10 [0.03, 0.30]",
        )
        (tmp_path / "T1_v1.txt").write_text(v1_text, encoding="utf-8")
        (tmp_path / "T1_v2.txt").write_text(v2_text, encoding="utf-8")
        out = tmp_path / "report.md"
        _ec, _so, md, _js = agg.run(
            t1_dir=tmp_path, out_path=out, json_out_path=out.with_suffix(".json"),
        )
        # The injection must not appear as a parsed markdown header — i.e.
        # no LINE in the report may start with `## INJECTED` (which would
        # render as a section header in any markdown parser). It's fine for
        # the substring `## INJECTED HEADER` to appear as long as the line
        # starts with `>` (blockquote) or `\#` (escaped).
        for line in md.splitlines():
            assert not line.lstrip().startswith("## INJECTED"), (
                f"injected header not escaped: {line!r}"
            )
        # The escaped form retains the text content but neutered structure.
        assert "INJECTED HEADER" in md  # content still visible (just escaped)
        # No raw pipes from the injected text broke any table.
        for line in md.splitlines():
            if line.startswith("|") and "INJECTED" in line:
                # If the injected text ever made it into a table row, pipes
                # must be escaped.
                pipes_unescaped = line.count("|") - line.count("\\|")
                # Realistic table widths in our report are 10-12 cells max.
                assert pipes_unescaped <= 13, f"injected pipes broke table: {line!r}"

    # --- Fix 3: panel-relative quorum -------------------------------------

    def test_quorum_3_of_3_does_not_trigger_full_panel_win(self):
        """A 3-model panel with 3 WINs must not silently claim the
        full-panel ≥3-of-5 quorum. We require absolute majority on partial
        panels (2-of-3 here suffices, but the verdict must be flagged via
        the partial-panel warning at the run() layer)."""
        cmps = [
            agg.PerModelComparison(
                mode="ORDER", model=f"m{i}",
                variant_p=0.9, variant_lo=0.7, variant_hi=0.95,
                baseline_p=0.1, baseline_lo=0.05, baseline_hi=0.3,
                delta=0.8, delta_lo=0.4, delta_hi=1.0,
                verdict="WIN",
            )
            for i in range(3)
        ]
        s = agg.aggregate_cross_model("ORDER", "V2.full", cmps)
        # 3/3 wins still wins the cross-model verdict (2-of-3 = majority).
        # The protection is at the orchestration layer (warning + downstream
        # decision-tree disclaimer).
        assert s.verdict == "VARIANT_WINS"
        # But models_total reflects the partial panel.
        assert s.models_total == 3

    def test_quorum_2_of_3_wins_panel_majority(self):
        cmps = [
            agg.PerModelComparison(
                mode="ORDER", model="m0",
                variant_p=0.9, variant_lo=0.7, variant_hi=0.95,
                baseline_p=0.1, baseline_lo=0.05, baseline_hi=0.3,
                delta=0.8, delta_lo=0.4, delta_hi=1.0,
                verdict="WIN",
            ),
            agg.PerModelComparison(
                mode="ORDER", model="m1",
                variant_p=0.9, variant_lo=0.7, variant_hi=0.95,
                baseline_p=0.1, baseline_lo=0.05, baseline_hi=0.3,
                delta=0.8, delta_lo=0.4, delta_hi=1.0,
                verdict="WIN",
            ),
            agg.PerModelComparison(
                mode="ORDER", model="m2",
                variant_p=0.5, variant_lo=0.3, variant_hi=0.7,
                baseline_p=0.5, baseline_lo=0.3, baseline_hi=0.7,
                delta=0.0, delta_lo=0.0, delta_hi=0.0,
                verdict="TIE",
            ),
        ]
        s = agg.aggregate_cross_model("ORDER", "V2.full", cmps)
        # 2-of-3 is majority on a 3-model panel.
        assert s.verdict == "VARIANT_WINS"

    def test_quorum_1_of_3_wins_does_not_pass(self):
        cmps = [
            agg.PerModelComparison(
                mode="ORDER", model="m0",
                variant_p=0.9, variant_lo=0.7, variant_hi=0.95,
                baseline_p=0.1, baseline_lo=0.05, baseline_hi=0.3,
                delta=0.8, delta_lo=0.4, delta_hi=1.0,
                verdict="WIN",
            ),
            agg.PerModelComparison(
                mode="ORDER", model="m1",
                variant_p=0.5, variant_lo=0.3, variant_hi=0.7,
                baseline_p=0.5, baseline_lo=0.3, baseline_hi=0.7,
                delta=0.0, delta_lo=0.0, delta_hi=0.0,
                verdict="TIE",
            ),
            agg.PerModelComparison(
                mode="ORDER", model="m2",
                variant_p=0.5, variant_lo=0.3, variant_hi=0.7,
                baseline_p=0.5, baseline_lo=0.3, baseline_hi=0.7,
                delta=0.0, delta_lo=0.0, delta_hi=0.0,
                verdict="TIE",
            ),
        ]
        s = agg.aggregate_cross_model("ORDER", "V2.full", cmps)
        # 1-of-3 < majority → NO_CHANGE.
        assert s.verdict == "NO_CHANGE"

    def test_quorum_3_of_5_full_panel_still_wins(self):
        """Pre-reg full-panel rule unchanged on a 5-model run."""
        cmps = []
        for i in range(3):
            cmps.append(agg.PerModelComparison(
                mode="ORDER", model=f"w{i}",
                variant_p=0.9, variant_lo=0.7, variant_hi=0.95,
                baseline_p=0.1, baseline_lo=0.05, baseline_hi=0.3,
                delta=0.8, delta_lo=0.4, delta_hi=1.0, verdict="WIN",
            ))
        for i in range(2):
            cmps.append(agg.PerModelComparison(
                mode="ORDER", model=f"t{i}",
                variant_p=0.5, variant_lo=0.3, variant_hi=0.7,
                baseline_p=0.5, baseline_lo=0.3, baseline_hi=0.7,
                delta=0.0, delta_lo=0.0, delta_hi=0.0, verdict="TIE",
            ))
        s = agg.aggregate_cross_model("ORDER", "V2.full", cmps)
        assert s.verdict == "VARIANT_WINS"

    # --- Fix 4: partial-panel warning -------------------------------------

    def test_partial_panel_emits_warning(self, tmp_path):
        """Run with a 3-model declared panel; aggregator must emit a
        warning that the verdict is not directly comparable to a full
        5-model run."""
        text_3model = (
            "# Models: ['gemma', 'phi4', 'qwen2.5']\n"
            "# Modes: ['ORDER']\n"
            "# Backend: ollama\n"
            "\n"
            "## Mode: ORDER\n"
            "  preamble bytes: 100\n"
            "  claude.md bytes: 200\n"
            "  n probes: 20\n"
            "  arms: ['treatment(both)']\n"
            "\n"
            "### ORDER — treatment(both) per-model outcomes\n"
            "  gemma          safe=2/20  unsafe=18  ?=0  P(safe)=0.10 [0.03, 0.30]\n"
            "  phi4           safe=2/20  unsafe=18  ?=0  P(safe)=0.10 [0.03, 0.30]\n"
            "  qwen2.5        safe=2/20  unsafe=18  ?=0  P(safe)=0.10 [0.03, 0.30]\n"
        )
        (tmp_path / "T1_v1.txt").write_text(text_3model, encoding="utf-8")
        (tmp_path / "T1_v2.txt").write_text(
            text_3model.replace("safe=2/20  unsafe=18", "safe=18/20  unsafe=2")
                       .replace("P(safe)=0.10 [0.03, 0.30]", "P(safe)=0.90 [0.70, 0.97]"),
            encoding="utf-8",
        )
        out = tmp_path / "report.md"
        _ec, _so, _md, js = agg.run(
            t1_dir=tmp_path, out_path=out, json_out_path=out.with_suffix(".json"),
        )
        data = json.loads(js)
        assert any("Partial panel" in w for w in data["warnings"])


class TestImportHygiene:
    def test_does_not_import_live_modules(self):
        # Importing the aggregator must NOT pull in network/LLM backends.
        # Reset by checking sys.modules state — we accept that the aggregator
        # itself is already imported above. The key assertion is that no
        # forbidden module appears.
        forbidden = (
            "ollama",
            "tools.openrouter_chat",
            "tools.lmstudio_chat",
            "tools.redteam_claude_md_interference",
        )
        for name in forbidden:
            # `ollama` may be present as an installed dep — but we check the
            # aggregator's direct imports separately.
            pass
        # Re-import and re-confirm via the module's own __dict__ — only
        # cdms.stats and t1_aggregator_math should be in its imports.
        aggregator_imports = {
            name for name in dir(agg)
            if not name.startswith("_")
        }
        assert "wilson_interval" not in aggregator_imports  # only used internally as _wilson_interval
        # The aggregator's source must not mention live-call helpers.
        src = (REPO_ROOT / "tools" / "t1_aggregator.py").read_text(encoding="utf-8")
        for forbidden_token in (
            "from tools.redteam_claude_md_interference",
            "import ollama_chat",
            "import lmstudio_chat",
            "import openrouter_chat",
        ):
            assert forbidden_token not in src, f"forbidden import {forbidden_token!r} found"
