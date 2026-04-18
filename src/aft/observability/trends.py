"""Trend calculation from historical observation records."""
from __future__ import annotations
from aft.observability.types import PTrendMetrics, PTrendResult, PRObservationData


class TrendCalculator:
    """Computes quality trends from historical PR observation data."""

    def __init__(
        self,
        coverage_warn_threshold: float = 0.70,
        duration_warn_pct: float = 30.0,
        coverage_up_delta: float = 0.02,
        coverage_down_delta: float = 0.02,
    ):
        self.coverage_warn_threshold = coverage_warn_threshold
        self.duration_warn_pct = duration_warn_pct
        self.coverage_up_delta = coverage_up_delta
        self.coverage_down_delta = coverage_down_delta

    def compute(
        self,
        current: PRObservationData,
        history: list[PRObservationData],
    ) -> PTrendResult:
        """Compute trend metrics comparing current run against historical average."""
        if not history:
            metrics = PTrendMetrics(
                current_coverage=self._get_coverage(current),
                avg_coverage=0.0,
                coverage_delta=0.0,
                coverage_trend="none",
                current_failures=self._get_failures(current),
                avg_failures=0.0,
                failure_delta=0.0,
                current_duration_ms=self._get_duration(current),
                avg_duration_ms=0.0,
                duration_delta_pct=0.0,
                has_history=False,
            )
            return PTrendResult(metrics=metrics, history_count=0)

        avg_coverage = sum(self._get_coverage(o) for o in history) / len(history)
        current_coverage = self._get_coverage(current)
        coverage_delta = current_coverage - avg_coverage

        avg_failures = sum(self._get_failures(o) for o in history) / len(history)
        current_failures = self._get_failures(current)
        failure_delta = current_failures - avg_failures

        avg_duration = sum(self._get_duration(o) for o in history) / len(history)
        current_duration = self._get_duration(current)
        duration_delta_pct = (
            ((current_duration - avg_duration) / avg_duration * 100)
            if avg_duration > 0 else 0.0
        )

        coverage_trend = self._classify_coverage_trend(coverage_delta)

        metrics = PTrendMetrics(
            current_coverage=current_coverage,
            avg_coverage=avg_coverage,
            coverage_delta=coverage_delta,
            coverage_trend=coverage_trend,
            current_failures=current_failures,
            avg_failures=avg_failures,
            failure_delta=failure_delta,
            current_duration_ms=current_duration,
            avg_duration_ms=avg_duration,
            duration_delta_pct=duration_delta_pct,
            has_history=True,
        )

        # Collect uncovered rules
        uncovered = [
            e.rule for e in current.rule_coverage if not e.covered
        ]

        return PTrendResult(
            metrics=metrics,
            history_count=len(history),
            uncovered_rules=uncovered,
        )

    def _get_coverage(self, obs: PRObservationData) -> float:
        cov = obs.coverage
        if isinstance(cov, dict):
            return cov.get("coverage_ratio", 0.0)
        return 0.0

    def _get_failures(self, obs: PRObservationData) -> int:
        tr = obs.test_result
        if isinstance(tr, dict):
            return tr.get("failed", 0)
        return 0

    def _get_duration(self, obs: PRObservationData) -> int:
        tr = obs.test_result
        if isinstance(tr, dict):
            return tr.get("duration_ms", 0)
        return 0

    def _classify_coverage_trend(self, delta: float) -> str:
        if delta > self.coverage_up_delta:
            return "up"
        elif delta < -self.coverage_down_delta:
            return "down"
        return "stable"