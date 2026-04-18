# tests/unit/test_ci_gate.py
import pytest
from unittest.mock import patch, MagicMock
from aft.alert.ci_gate import CIGate, CIGateResult
from aft.observability.types import PTrendResult, PTrendMetrics, PRObservationData


class TestCIGate:
    def test_pass_when_no_observation_data(self):
        """No observation data = CI passes (no violation)."""
        with patch("aft.alert.ci_gate.ObservabilityStore") as MockStore:
            mock_store = MagicMock()
            mock_store.load.side_effect = FileNotFoundError("No observation")
            MockStore.return_value = mock_store

            gate = CIGate(config={"conditions": {"coverage_below": 0.70}, "fail_on_violation": True})
            result = gate.check(pr_number=9999, repo="test/repo")

            assert result.passed is True
            assert "No observation" in result.reason

    def test_pass_when_conditions_met_coverage_good(self):
        """CI passes when coverage is good."""
        with patch("aft.alert.ci_gate.ObservabilityStore") as MockStore, \
             patch("aft.alert.ci_gate.TrendCalculator") as MockCalc:

            mock_store = MagicMock()
            mock_store.load.return_value = _make_obs(coverage=0.85)
            mock_store.load_history.return_value = [_make_obs(coverage=0.80)]
            MockStore.return_value = mock_store

            mock_calc = MagicMock()
            mock_calc.compute.return_value = _make_trend(coverage=0.85, failures=0)
            MockCalc.return_value = mock_calc

            gate = CIGate(config={
                "conditions": {"coverage_below": 0.70, "composite": "OR"},
                "fail_on_violation": True,
            })
            result = gate.check(pr_number=2341, repo="tiktok/repo")

            assert result.passed is True

    def test_block_when_coverage_below_threshold(self):
        """CI blocks when coverage below threshold."""
        with patch("aft.alert.ci_gate.ObservabilityStore") as MockStore, \
             patch("aft.alert.ci_gate.TrendCalculator") as MockCalc:

            mock_store = MagicMock()
            mock_store.load.return_value = _make_obs(coverage=0.65)
            mock_store.load_history.return_value = [_make_obs(coverage=0.80)]
            MockStore.return_value = mock_store

            mock_calc = MagicMock()
            mock_calc.compute.return_value = _make_trend(coverage=0.65, failures=0)
            MockCalc.return_value = mock_calc

            gate = CIGate(config={
                "conditions": {"coverage_below": 0.70, "composite": "OR"},
                "fail_on_violation": True,
            })
            result = gate.check(pr_number=2341, repo="tiktok/repo")

            assert result.passed is False
            assert "blocked" in result.reason.lower()

    def test_cigateresult_dataclass_fields(self):
        result = CIGateResult(passed=False, reason="coverage 65% < 70%", details={"coverage": "65.0%"})
        assert result.passed is False
        assert "coverage" in result.reason
        assert result.details["coverage"] == "65.0%"

    def test_build_details_contains_metrics(self):
        with patch("aft.alert.ci_gate.ObservabilityStore") as MockStore, \
             patch("aft.alert.ci_gate.TrendCalculator") as MockCalc:

            mock_store = MagicMock()
            mock_store.load.return_value = _make_obs(coverage=0.65)
            mock_store.load_history.return_value = [_make_obs(coverage=0.80)]
            MockStore.return_value = mock_store

            mock_calc = MagicMock()
            mock_trend = _make_trend(coverage=0.65, failures=2)
            mock_calc.compute.return_value = mock_trend
            MockCalc.return_value = mock_calc

            gate = CIGate(config={
                "conditions": {"coverage_below": 0.70, "composite": "OR"},
                "fail_on_violation": True,
            })
            result = gate.check(pr_number=2341, repo="tiktok/repo")

            assert "coverage" in result.details
            assert "failures" in result.details


def _make_obs(coverage):
    return PRObservationData(
        pr_number=2341,
        repo="tiktok/repo",
        branch="main",
        author="tester",
        test_result={"passed": 3, "failed": 0, "skipped": 0, "duration_ms": 400},
        coverage={"rules_total": 10, "rules_covered": int(10 * coverage), "coverage_ratio": coverage},
    )


def _make_trend(coverage, failures):
    metrics = PTrendMetrics(
        current_coverage=coverage,
        avg_coverage=0.78,
        coverage_delta=coverage - 0.78,
        coverage_trend="stable",
        current_failures=failures,
        avg_failures=0.0,
        failure_delta=0.0,
        current_duration_ms=400,
        avg_duration_ms=380,
        duration_delta_pct=5.0,
        has_history=True,
    )
    return PTrendResult(metrics=metrics, history_count=5, uncovered_rules=[])