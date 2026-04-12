# tests/unit/test_observability_types.py
import pytest
from aft.observability.types import (
    PRObservationData,
    PCoverageData,
    PTrendResult,
    PTrendMetrics,
)


class TestPRObservationData:
    def test_create_minimal_observation(self):
        obs = PRObservationData(
            pr_number=1,
            repo="test/repo",
            branch="main",
            author="test",
            test_result={"passed": 1, "failed": 0, "skipped": 0, "duration_ms": 100},
            coverage={"rules_total": 10, "rules_covered": 8, "coverage_ratio": 0.8},
        )
        assert obs.pr_number == 1
        assert obs.coverage["coverage_ratio"] == 0.8
        assert obs.self_healed is False


class TestPTrendResult:
    def test_trend_result_with_history(self):
        metrics = PTrendMetrics(
            current_coverage=0.80,
            avg_coverage=0.75,
            coverage_delta=0.05,
            coverage_trend="up",
            current_failures=0,
            avg_failures=0.3,
            failure_delta=-0.3,
            current_duration_ms=400,
            avg_duration_ms=380,
            duration_delta_pct=5.3,
            has_history=True,
        )
        tr = PTrendResult(metrics=metrics, history_count=5)
        assert tr.metrics.coverage_trend == "up"
        assert tr.history_count == 5

    def test_trend_result_first_run(self):
        metrics = PTrendMetrics(
            current_coverage=0.80,
            avg_coverage=0.0,
            coverage_delta=0.0,
            coverage_trend="none",
            current_failures=0,
            avg_failures=0.0,
            failure_delta=0.0,
            current_duration_ms=400,
            avg_duration_ms=0.0,
            duration_delta_pct=0.0,
            has_history=False,
        )
        tr = PTrendResult(metrics=metrics, history_count=0)
        assert tr.metrics.coverage_trend == "none"
        assert tr.history_count == 0