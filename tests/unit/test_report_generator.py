# tests/unit/test_report_generator.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from aft.report.generator import ReportGenerator, ReportType, Report
from aft.observability.types import PTrendResult, PTrendMetrics, PRObservationData


class TestReportGenerator:
    def test_pr_closed_report_generates_comment(self):
        """PR-closed report generates quality summary."""
        with patch("aft.report.generator.ObservabilityStore") as MockStore, \
             patch("aft.report.generator.TrendCalculator") as MockCalc, \
             patch("aft.report.generator.ObservabilityComment") as MockComment:

            mock_store = MagicMock()
            mock_store.load.return_value = _make_obs(pr_number=2341, coverage=0.809)
            mock_store.load_history.return_value = [_make_obs(coverage=0.78)]
            MockStore.return_value = mock_store

            mock_calc = MagicMock()
            mock_calc.compute.return_value = _make_trend(coverage=0.809, failures=0)
            MockCalc.return_value = mock_calc

            mock_renderer = MagicMock()
            mock_renderer.render.return_value = "### Quality Trends\n| Coverage | 80.9% |"
            MockComment.return_value = mock_renderer

            gen = ReportGenerator(obs_store=mock_store, trend_calc=mock_calc)
            report = gen.generate(ReportType.PR_CLOSED, pr=2341)

            assert report.type == ReportType.PR_CLOSED
            assert "2341" in report.title
            assert report.trend is not None

    def test_daily_report_aggregates_recent_observations(self):
        """Daily report aggregates observations from last 24h."""
        with patch("aft.report.generator.ObservabilityStore") as MockStore, \
             patch("aft.report.generator.TrendCalculator") as MockCalc:

            mock_store = MagicMock()
            mock_store.load_recent.return_value = [
                _make_obs(pr_number=100 + i, coverage=0.80 + i * 0.01)
                for i in range(3)
            ]
            MockStore.return_value = mock_store

            mock_calc = MagicMock()
            mock_calc.compute.return_value = _make_trend(coverage=0.82, failures=0)
            MockCalc.return_value = mock_calc

            gen = ReportGenerator(obs_store=mock_store, trend_calc=mock_calc)
            report = gen.generate(ReportType.DAILY)

            assert report.type == ReportType.DAILY
            assert "daily" in report.title.lower()

    def test_weekly_report_compares_two_periods(self):
        """Weekly report compares current vs previous week."""
        with patch("aft.report.generator.ObservabilityStore") as MockStore, \
             patch("aft.report.generator.TrendCalculator") as MockCalc:

            mock_store = MagicMock()
            mock_store.load_recent.return_value = [_make_obs(coverage=0.80)]
            mock_store.load_previous_period.return_value = [_make_obs(coverage=0.75)]
            MockStore.return_value = mock_store

            mock_calc = MagicMock()
            mock_calc.compute.return_value = _make_trend(coverage=0.80, failures=0)
            MockCalc.return_value = mock_calc

            gen = ReportGenerator(obs_store=mock_store, trend_calc=mock_calc)
            report = gen.generate(ReportType.WEEKLY)

            assert report.type == ReportType.WEEKLY
            assert "week" in report.title.lower()

    def test_on_demand_report_with_prs(self):
        """On-demand report for specific PRs."""
        with patch("aft.report.generator.ObservabilityStore") as MockStore, \
             patch("aft.report.generator.TrendCalculator") as MockCalc:

            mock_store = MagicMock()
            mock_store.load.side_effect = lambda pr: _make_obs(pr_number=pr, coverage=0.80)
            MockStore.return_value = mock_store

            mock_calc = MagicMock()
            mock_calc.compute.return_value = _make_trend(coverage=0.80, failures=0)
            MockCalc.return_value = mock_calc

            gen = ReportGenerator(obs_store=mock_store, trend_calc=mock_calc)
            report = gen.generate(ReportType.ON_DEMAND, prs=[100, 101])

            assert report.type == ReportType.ON_DEMAND
            assert "100" in report.title

    def test_daily_report_no_data(self):
        """Daily report with no data returns empty report."""
        with patch("aft.report.generator.ObservabilityStore") as MockStore:
            mock_store = MagicMock()
            mock_store.load_recent.return_value = []
            MockStore.return_value = mock_store

            gen = ReportGenerator(obs_store=mock_store, trend_calc=MagicMock())
            report = gen.generate(ReportType.DAILY)

            assert report.type == ReportType.DAILY
            assert "No PRs" in report.rendered


class TestReportType:
    def test_report_type_enum_values(self):
        assert ReportType.DAILY.value == "daily"
        assert ReportType.WEEKLY.value == "weekly"
        assert ReportType.ON_DEMAND.value == "on-demand"
        assert ReportType.PR_CLOSED.value == "pr-closed"


class TestReport:
    def test_report_dataclass_fields(self):
        report = Report(type=ReportType.DAILY, title="Daily Report")
        assert report.type == ReportType.DAILY
        assert report.title == "Daily Report"
        assert report.trend is None
        assert report.rendered == ""
        assert report.metadata == {}


def _make_obs(pr_number=2341, coverage=0.80):
    return PRObservationData(
        pr_number=pr_number,
        repo="tiktok/content-safety",
        branch="feat/test",
        author="tester",
        timestamp=datetime.now(timezone.utc).isoformat(),
        test_result={"passed": 3, "failed": 0, "skipped": 0, "duration_ms": 400},
        coverage={"rules_total": 47, "rules_covered": int(47 * coverage), "coverage_ratio": coverage},
    )


def _make_trend(coverage, failures):
    metrics = PTrendMetrics(
        current_coverage=coverage,
        avg_coverage=0.78,
        coverage_delta=coverage - 0.78,
        coverage_trend="up",
        current_failures=failures,
        avg_failures=0.3,
        failure_delta=float(failures - 0.3),
        current_duration_ms=412,
        avg_duration_ms=380,
        duration_delta_pct=8.4,
        has_history=True,
    )
    return PTrendResult(metrics=metrics, history_count=5, uncovered_rules=[])