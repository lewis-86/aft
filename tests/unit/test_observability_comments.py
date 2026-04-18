# tests/unit/test_observability_comments.py
import pytest
from aft.observability.comments import ObservabilityComment
from aft.observability.types import PTrendResult, PTrendMetrics


class TestObservabilityComment:
    def test_render_with_history(self):
        metrics = PTrendMetrics(
            current_coverage=0.809,
            avg_coverage=0.782,
            coverage_delta=0.027,
            coverage_trend="up",
            current_failures=0,
            avg_failures=0.3,
            failure_delta=-0.3,
            current_duration_ms=412,
            avg_duration_ms=380,
            duration_delta_pct=8.4,
            has_history=True,
        )
        result = PTrendResult(metrics=metrics, history_count=5, uncovered_rules=["spam.action_block"])
        comment = ObservabilityComment()
        output = comment.render(result)
        assert "Quality Trends" in output
        assert "80.9%" in output
        assert "78.2%" in output
        assert "📈" in output
        assert "spam.action_block" in output

    def test_render_first_run_no_history(self):
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
        result = PTrendResult(metrics=metrics, history_count=0, uncovered_rules=[])
        comment = ObservabilityComment()
        output = comment.render(result)
        assert "Quality Trends" in output
        assert "—" in output  # no history

    def test_render_coverage_below_threshold_warns(self):
        metrics = PTrendMetrics(
            current_coverage=0.65,
            avg_coverage=0.70,
            coverage_delta=-0.05,
            coverage_trend="down",
            current_failures=1,
            avg_failures=0.2,
            failure_delta=0.8,
            current_duration_ms=500,
            avg_duration_ms=400,
            duration_delta_pct=25.0,
            has_history=True,
        )
        result = PTrendResult(metrics=metrics, history_count=5, uncovered_rules=["spam.action_block"])
        comment = ObservabilityComment()
        output = comment.render(result)
        assert "⚠️" in output

    def test_render_no_uncovered_rules_no_gaps_section(self):
        metrics = PTrendMetrics(
            current_coverage=0.90,
            avg_coverage=0.88,
            coverage_delta=0.02,
            coverage_trend="up",
            current_failures=0,
            avg_failures=0.1,
            failure_delta=-0.1,
            current_duration_ms=300,
            avg_duration_ms=320,
            duration_delta_pct=-6.3,
            has_history=True,
        )
        result = PTrendResult(metrics=metrics, history_count=5, uncovered_rules=[])
        comment = ObservabilityComment()
        output = comment.render(result)
        assert "Rule Coverage Gaps" not in output