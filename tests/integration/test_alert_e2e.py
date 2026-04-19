# tests/integration/test_alert_e2e.py
"""End-to-end integration test for alert and report flows."""
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from aft.observability.store import ObservabilityStore
from aft.observability.types import PRObservationData
from aft.alert.dispatcher import AlertDispatcher
from aft.alert.ci_gate import CIGate
from aft.report.generator import ReportGenerator, ReportType


class TestAlertE2E:
    def test_full_alert_flow_with_mocked_webhook(self):
        """Full flow: store observation -> CI gate check -> alert dispatch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Save observation data
            store = ObservabilityStore(data_dir=tmpdir)
            obs = PRObservationData(
                pr_number=5001,
                repo="tiktok/content-safety",
                branch="feat/violence",
                author="tester",
                timestamp=datetime.now(timezone.utc).isoformat(),
                test_result={"passed": 3, "failed": 2, "skipped": 0, "duration_ms": 520},
                coverage={"rules_total": 47, "rules_covered": 30, "coverage_ratio": 0.638},
            )
            store.save(obs)

            # 2. Save history
            for i in range(3):
                hist = PRObservationData(
                    pr_number=5000 - i,
                    repo="tiktok/content-safety",
                    branch="main",
                    author="other",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    test_result={"passed": 3, "failed": 0, "skipped": 0, "duration_ms": 400},
                    coverage={"rules_total": 47, "rules_covered": 38, "coverage_ratio": 0.809},
                )
                store.save(hist)

            # Patch ObservabilityStore so CIGate uses the same temp directory
            with patch("aft.alert.ci_gate.ObservabilityStore", return_value=store):
                # 3. CI gate should block (coverage 63.8% < 70%)
                gate = CIGate(config={
                    "conditions": {"coverage_below": 0.70, "composite": "OR"},
                    "fail_on_violation": True,
                })
                result = gate.check(pr_number=5001, repo="tiktok/content-safety")
                assert result.passed is False, f"Expected blocked but got: {result.reason}"
                assert "blocked" in result.reason.lower()

                # 4. Alert dispatcher should trigger
                from aft.observability.trends import TrendCalculator
                trend_calc = TrendCalculator()
                trend = trend_calc.compute(obs, store.load_history(limit=5))

                dispatcher = AlertDispatcher(trend_result=trend, config={
                    "conditions": {"coverage_below": 0.70, "composite": "OR"},
                    "channels": [],  # No actual webhooks
                })
                assert dispatcher.should_alert() is True

    def test_report_generator_with_real_store(self):
        """Report generator uses real store to produce daily report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ObservabilityStore(data_dir=tmpdir)
            for i in range(3):
                obs = PRObservationData(
                    pr_number=6000 + i,
                    repo="tiktok/content-safety",
                    branch="main",
                    author="tester",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    test_result={"passed": 3, "failed": 0, "skipped": 0, "duration_ms": 400},
                    coverage={"rules_total": 47, "rules_covered": 38, "coverage_ratio": 0.809},
                )
                store.save(obs)

            from aft.observability.trends import TrendCalculator
            trend_calc = TrendCalculator()
            gen = ReportGenerator(obs_store=store, trend_calc=trend_calc)

            report = gen.generate(ReportType.DAILY)
            assert report.type == ReportType.DAILY
            assert report.metadata["pr_count"] >= 3

    def test_pr_closed_report_with_real_store(self):
        """PR-closed report generates for specific PR."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ObservabilityStore(data_dir=tmpdir)
            obs = PRObservationData(
                pr_number=7001,
                repo="tiktok/content-safety",
                branch="feat/test",
                author="tester",
                timestamp=datetime.now(timezone.utc).isoformat(),
                test_result={"passed": 3, "failed": 0, "skipped": 0, "duration_ms": 412},
                coverage={"rules_total": 47, "rules_covered": 38, "coverage_ratio": 0.809},
            )
            store.save(obs)

            from aft.observability.trends import TrendCalculator
            trend_calc = TrendCalculator()
            gen = ReportGenerator(obs_store=store, trend_calc=trend_calc)

            report = gen.generate(ReportType.PR_CLOSED, pr=7001)
            assert report.type == ReportType.PR_CLOSED
            assert "7001" in report.title
            assert report.trend is not None

    def test_observability_file_created_on_pr_event(self):
        """Verify that saving an observation creates the expected JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ObservabilityStore(data_dir=tmpdir)
            obs = PRObservationData(
                pr_number=8001,
                repo="tiktok/content-safety",
                branch="feat/test",
                author="tester",
                timestamp=datetime.now(timezone.utc).isoformat(),
                test_result={"passed": 3, "failed": 0, "skipped": 0, "duration_ms": 400},
                coverage={"rules_total": 47, "rules_covered": 38, "coverage_ratio": 0.809},
            )
            path = store.save(obs)

            assert path.exists()
            assert os.path.basename(path) == "pr-8001.json"

            # Verify it can be loaded back
            loaded = store.load(8001)
            assert loaded.pr_number == 8001
            assert loaded.coverage["coverage_ratio"] == 0.809