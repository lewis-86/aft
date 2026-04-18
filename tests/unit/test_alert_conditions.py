# tests/unit/test_alert_conditions.py
import pytest
from aft.observability.types import PTrendResult, PTrendMetrics, PRObservationData
from aft.alert.conditions import evaluate_conditions


class TestEvaluateConditions:
    def test_no_conditions_means_no_violation(self):
        """Empty conditions should not trigger any violation."""
        trend = _make_trend(coverage=0.5, failures=0, duration_delta=0.0)
        result = evaluate_conditions(trend, {})
        assert result is False

    def test_coverage_below_triggers(self):
        """Coverage below threshold should trigger."""
        trend = _make_trend(coverage=0.65, failures=0, duration_delta=0.0)
        conditions = {"coverage_below": 0.70}
        result = evaluate_conditions(trend, conditions)
        assert result is True

    def test_coverage_above_threshold_no_trigger(self):
        """Coverage above threshold should not trigger."""
        trend = _make_trend(coverage=0.80, failures=0, duration_delta=0.0)
        conditions = {"coverage_below": 0.70}
        result = evaluate_conditions(trend, conditions)
        assert result is False

    def test_failures_above_triggers(self):
        """Failures above threshold should trigger."""
        trend = _make_trend(coverage=0.80, failures=2, duration_delta=0.0)
        conditions = {"failures_above": 0}
        result = evaluate_conditions(trend, conditions)
        assert result is True

    def test_failures_zero_no_trigger(self):
        """Zero failures with failures_above=0 should not trigger."""
        trend = _make_trend(coverage=0.80, failures=0, duration_delta=0.0)
        conditions = {"failures_above": 0}
        result = evaluate_conditions(trend, conditions)
        assert result is False

    def test_composite_or_triggers_on_one(self):
        """OR composite: triggers if exactly one condition is met."""
        trend = _make_trend(coverage=0.65, failures=0, duration_delta=0.0)
        conditions = {
            "coverage_below": 0.70,  # True
            "failures_above": 0,     # False
            "composite": "OR",
        }
        result = evaluate_conditions(trend, conditions)
        assert result is True

    def test_composite_and_requires_all(self):
        """AND composite: all conditions must be met."""
        trend = _make_trend(coverage=0.65, failures=2, duration_delta=0.0)
        conditions = {
            "coverage_below": 0.70,  # True
            "failures_above": 0,     # True
            "composite": "AND",
        }
        result = evaluate_conditions(trend, conditions)
        assert result is True

    def test_composite_and_fails_if_one_missing(self):
        """AND composite: fails if one condition is not met."""
        trend = _make_trend(coverage=0.65, failures=0, duration_delta=0.0)
        conditions = {
            "coverage_below": 0.70,  # True
            "failures_above": 0,     # False
            "composite": "AND",
        }
        result = evaluate_conditions(trend, conditions)
        assert result is False

    def test_duration_spike_triggers(self):
        """Duration spike above threshold triggers."""
        trend = _make_trend(coverage=0.80, failures=0, duration_delta=40.0)
        conditions = {"duration_spike_above": 0.30}
        result = evaluate_conditions(trend, conditions)
        assert result is True

    def test_coverage_drop_triggers(self):
        """Coverage drop (negative delta) above threshold triggers."""
        trend = _make_trend(coverage=0.80, failures=0, duration_delta=0.0,
                             coverage_delta=-0.08)
        conditions = {"coverage_drop_above": 0.05}
        result = evaluate_conditions(trend, conditions)
        assert result is True

    def test_self_heal_failed_triggers_when_uncovered_rules(self):
        """self_heal_failed=True triggers when there are uncovered rules."""
        trend = _make_trend(coverage=0.65, failures=2, duration_delta=0.0,
                             uncovered=["spam.action_block"])
        conditions = {"self_heal_failed": True}
        result = evaluate_conditions(trend, conditions)
        assert result is True

    def test_empty_results_returns_false(self):
        """No conditions configured returns False."""
        trend = _make_trend(coverage=0.90, failures=0, duration_delta=0.0)
        result = evaluate_conditions(trend, {"composite": "OR"})
        assert result is False


def _make_trend(coverage, failures, duration_delta, coverage_delta=0.0,
                uncovered=None):
    """Helper to build PTrendResult for testing."""
    metrics = PTrendMetrics(
        current_coverage=coverage,
        avg_coverage=coverage - coverage_delta,
        coverage_delta=coverage_delta,
        coverage_trend="down" if coverage_delta < -0.02 else "stable",
        current_failures=failures,
        avg_failures=0.0,
        failure_delta=float(failures),
        current_duration_ms=400,
        avg_duration_ms=380,
        duration_delta_pct=duration_delta,
        has_history=True,
    )
    return PTrendResult(
        metrics=metrics,
        history_count=5,
        uncovered_rules=uncovered or [],
    )