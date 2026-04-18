# src/aft/report/generator.py
"""Report generator for AFT — supports daily/weekly/on-demand/pr-closed reports."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from aft.observability.comments import ObservabilityComment
from aft.observability.store import ObservabilityStore
from aft.observability.trends import TrendCalculator


class ReportType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    ON_DEMAND = "on-demand"
    PR_CLOSED = "pr-closed"


@dataclass
class Report:
    """A generated quality report."""
    type: ReportType
    title: str
    trend: Optional["PTrendResult"] = None
    rendered: str = ""
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ReportGenerator:
    """Generates quality reports in multiple formats.

    Uses ObservabilityComment.render() for formatting trend data.
    """

    def __init__(self, obs_store: "ObservabilityStore", trend_calc: "TrendCalculator"):
        self.store = obs_store
        self.trend_calc = trend_calc

    def generate(self, report_type: ReportType, **kwargs) -> Report:
        """Generate a report of the given type.

        Args:
            report_type: One of DAILY, WEEKLY, ON_DEMAND, PR_CLOSED
            **kwargs:
                - pr: int (for PR_CLOSED, ON_DEMAND)
                - prs: list[int] (for ON_DEMAND)
        """
        if report_type == ReportType.DAILY:
            return self._daily_report()
        elif report_type == ReportType.WEEKLY:
            return self._weekly_report()
        elif report_type == ReportType.ON_DEMAND:
            return self._on_demand_report(prs=kwargs.get("prs", []))
        elif report_type == ReportType.PR_CLOSED:
            return self._pr_closed_report(pr=kwargs["pr"])
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    def _daily_report(self) -> Report:
        """Generate daily report for last 24 hours."""
        recent = self.store.load_recent(hours=24)
        if not recent:
            return Report(
                type=ReportType.DAILY,
                title="AFT Daily Quality Report — No PRs in last 24h",
                rendered="No PRs in the last 24 hours.",
            )

        avg_coverage = sum(o.coverage.get("coverage_ratio", 0) for o in recent) / len(recent)
        total_failures = sum(o.test_result.get("failed", 0) for o in recent)
        trend = self._build_aggregate_trend(recent)

        renderer = ObservabilityComment()
        rendered = renderer.render(trend) if trend else ""

        return Report(
            type=ReportType.DAILY,
            title=f"AFT Daily Quality Report — {len(recent)} PRs",
            trend=trend,
            rendered=rendered,
            metadata={"pr_count": len(recent), "avg_coverage": avg_coverage},
        )

    def _weekly_report(self) -> Report:
        """Generate weekly report with week-over-week comparison."""
        current_period = self.store.load_recent(hours=24 * 7)
        previous_period = self.store.load_previous_period(days=7, offset=7)

        if not current_period:
            return Report(
                type=ReportType.WEEKLY,
                title="AFT Weekly Quality Report — No PRs this week",
                rendered="No PR observations in the last 7 days.",
            )

        current_avg = sum(o.coverage.get("coverage_ratio", 0) for o in current_period) / len(current_period)
        previous_avg = (
            sum(o.coverage.get("coverage_ratio", 0) for o in previous_period) / len(previous_period)
            if previous_period else 0.0
        )
        wow_delta = current_avg - previous_avg if previous_period else 0.0

        trend = self._build_aggregate_trend(current_period)

        renderer = ObservabilityComment()
        rendered = renderer.render(trend) if trend else ""

        wow_section = f"**Week-over-Week:** coverage {wow_delta:+.1%}"
        rendered = rendered + f"\n\n{wow_section}"

        return Report(
            type=ReportType.WEEKLY,
            title=f"AFT Weekly Report — {len(current_period)} PRs (WoW: {wow_delta:+.1%})",
            trend=trend,
            rendered=rendered,
            metadata={"pr_count": len(current_period), "wow_delta": wow_delta},
        )

    def _on_demand_report(self, prs: list[int]) -> Report:
        """Generate report for specific PR numbers."""
        if not prs:
            return Report(
                type=ReportType.ON_DEMAND,
                title="AFT On-Demand Report — No PRs specified",
                rendered="No PRs specified.",
            )

        observations = []
        for pr in prs:
            try:
                observations.append(self.store.load(pr))
            except FileNotFoundError:
                continue

        trend = self._build_aggregate_trend(observations)

        renderer = ObservabilityComment()
        rendered = renderer.render(trend) if trend else ""

        return Report(
            type=ReportType.ON_DEMAND,
            title=f"AFT On-Demand Report — PRs {prs}",
            trend=trend,
            rendered=rendered,
            metadata={"prs": prs, "pr_count": len(observations)},
        )

    def _pr_closed_report(self, pr: int) -> Report:
        """Generate quality summary for a single closed PR."""
        try:
            obs = self.store.load(pr)
        except FileNotFoundError:
            return Report(
                type=ReportType.PR_CLOSED,
                title=f"PR #{pr} Quality Summary — No data",
                rendered=f"No observation data for PR #{pr}.",
            )

        history = self.store.load_history(limit=5)
        trend = self.trend_calc.compute(obs, history)

        renderer = ObservabilityComment()
        rendered = renderer.render(trend)

        return Report(
            type=ReportType.PR_CLOSED,
            title=f"PR #{pr} Quality Summary",
            trend=trend,
            rendered=rendered,
            metadata={"pr": pr},
        )

    def _build_aggregate_trend(self, observations: list) -> Optional["PTrendResult"]:
        """Build a PTrendResult from a list of observations (for aggregate reports)."""
        if not observations:
            return None

        from aft.observability.types import PTrendMetrics, PTrendResult

        avg_coverage = sum(o.coverage.get("coverage_ratio", 0) for o in observations) / len(observations)
        total_failures = sum(o.test_result.get("failed", 0) for o in observations)
        avg_duration = sum(o.test_result.get("duration_ms", 0) for o in observations) / len(observations)

        metrics = PTrendMetrics(
            current_coverage=avg_coverage,
            avg_coverage=avg_coverage,
            coverage_delta=0.0,
            coverage_trend="stable",
            current_failures=total_failures,
            avg_failures=float(total_failures),
            failure_delta=0.0,
            current_duration_ms=int(avg_duration),
            avg_duration_ms=avg_duration,
            duration_delta_pct=0.0,
            has_history=False,
        )
        return PTrendResult(metrics=metrics, history_count=len(observations), uncovered_rules=[])