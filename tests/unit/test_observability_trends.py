# tests/unit/test_observability_trends.py
import pytest
from aft.observability.trends import TrendCalculator
from aft.observability.types import PTrendResult, PRObservationData


class TestTrendCalculator:
    def test_compute_with_no_history(self):
        calc = TrendCalculator()
        current = _make_obs(pr_number=1, passed=3, failed=0, duration_ms=400, coverage_ratio=0.8)
        result = calc.compute(current, [])
        assert result.metrics.has_history is False
        assert result.metrics.coverage_trend == "none"
        assert result.history_count == 0

    def test_compute_coverage_up(self):
        calc = TrendCalculator()
        # 5 history records: coverage ~70%, current is 80%
        history = [_make_obs(pr_number=100+i, passed=3, failed=0, duration_ms=400,
                              coverage_ratio=0.7) for i in range(5)]
        current = _make_obs(pr_number=200, passed=3, failed=0, duration_ms=400, coverage_ratio=0.8)
        result = calc.compute(current, history)
        assert result.metrics.has_history is True
        assert result.metrics.coverage_trend == "up"
        assert result.metrics.coverage_delta > 0
        assert result.history_count == 5

    def test_compute_coverage_down_warns(self):
        calc = TrendCalculator(coverage_warn_threshold=0.7)
        history = [_make_obs(pr_number=100+i, passed=3, failed=0, duration_ms=400,
                              coverage_ratio=0.85) for i in range(5)]
        # Current drops to 65% - below 70% threshold
        current = _make_obs(pr_number=200, passed=3, failed=0, duration_ms=400, coverage_ratio=0.65)
        result = calc.compute(current, history)
        assert result.metrics.coverage_trend == "down"

    def test_compute_failure_spike_warns(self):
        calc = TrendCalculator()
        history = [_make_obs(pr_number=100+i, passed=3, failed=0, duration_ms=400,
                              coverage_ratio=0.8) for i in range(5)]
        current = _make_obs(pr_number=200, passed=1, failed=2, duration_ms=400, coverage_ratio=0.8)
        result = calc.compute(current, history)
        assert result.metrics.failure_delta > 0

    def test_compute_duration_spike(self):
        calc = TrendCalculator(duration_warn_pct=30.0)
        history = [_make_obs(pr_number=100+i, passed=3, failed=0, duration_ms=100,
                              coverage_ratio=0.8) for i in range(5)]
        # Current is 140ms, avg is 100ms -> +40% spike
        current = _make_obs(pr_number=200, passed=3, failed=0, duration_ms=140, coverage_ratio=0.8)
        result = calc.compute(current, history)
        assert result.metrics.duration_delta_pct > 30

    def test_compute_uncovered_rules_passed_through(self):
        calc = TrendCalculator()
        from aft.observability.types import PRuleCoverageEntry
        history = [_make_obs(pr_number=100+i, passed=3, failed=0, duration_ms=100,
                              coverage_ratio=0.8) for i in range(5)]
        current = _make_obs(pr_number=200, passed=3, failed=0, duration_ms=100, coverage_ratio=0.8)
        # Add uncovered rules to current
        current.rule_coverage = [
            PRuleCoverageEntry(rule="spam.action_block", covered=False),
            PRuleCoverageEntry(rule="violence.threshold", covered=True, test_names=["test_violence"]),
        ]
        result = calc.compute(current, history)
        assert "spam.action_block" in result.uncovered_rules
        assert "violence.threshold" not in result.uncovered_rules


def _make_obs(pr_number, passed, failed, duration_ms, coverage_ratio):
    return PRObservationData(
        pr_number=pr_number,
        repo="test/repo",
        branch="main",
        author="tester",
        test_result={"passed": passed, "failed": failed, "skipped": 0, "duration_ms": duration_ms},
        coverage={"rules_total": 100, "rules_covered": int(100*coverage_ratio), "coverage_ratio": coverage_ratio},
    )