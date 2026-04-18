# tests/unit/test_slack_notifier.py
import pytest
from unittest.mock import patch, MagicMock
from aft.alert.channels.slack import SlackNotifier
from aft.observability.types import PTrendResult, PTrendMetrics


class TestSlackNotifier:
    @patch("aft.alert.channels.slack.urllib.request.urlopen")
    def test_send_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        trend = _make_trend(coverage=0.65, failures=2)
        pr_info = {"pr_number": 2341, "pr_url": "https://github.com/tiktok/repo/pull/2341", "repo": "tiktok/repo"}

        result = notifier.send(trend=trend, pr_info=pr_info)

        assert result is True
        mock_urlopen.assert_called_once()
        call_args = mock_urlopen.call_args
        assert "hooks.slack.com" in str(call_args)

    @patch("aft.alert.channels.slack.urllib.request.urlopen")
    def test_send_failure_returns_false(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection refused")

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        trend = _make_trend(coverage=0.65, failures=2)
        pr_info = {"pr_number": 2341, "pr_url": "https://github.com/tiktok/repo/pull/2341", "repo": "tiktok/repo"}

        result = notifier.send(trend=trend, pr_info=pr_info)

        assert result is False

    def test_build_markdown_contains_metrics(self):
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        trend = _make_trend(coverage=0.65, failures=2)
        pr_info = {"pr_number": 2341, "pr_url": "https://github.com/tiktok/repo/pull/2341", "repo": "tiktok/repo"}

        text = notifier._build_markdown(trend=trend, pr_info=pr_info)

        assert "65.0%" in text
        assert "2341" in text
        assert "AFT Quality Alert" in text
        assert "Coverage" in text

    def test_build_text_contains_pr_number(self):
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        trend = _make_trend(coverage=0.65, failures=2)
        pr_info = {"pr_number": 2341, "pr_url": "https://github.com/tiktok/repo/pull/2341", "repo": "tiktok/repo"}

        text = notifier._build_text(trend=trend, pr_info=pr_info)

        assert "2341" in text
        assert "AFT Quality Alert" in text

    def test_build_markdown_includes_uncovered_rules(self):
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        trend = _make_trend(coverage=0.65, failures=2, uncovered=["spam.action_block"])
        pr_info = {"pr_number": 2341, "pr_url": "https://github.com/tiktok/repo/pull/2341", "repo": "tiktok/repo"}

        text = notifier._build_markdown(trend=trend, pr_info=pr_info)

        assert "spam.action_block" in text


def _make_trend(coverage, failures, uncovered=None):
    metrics = PTrendMetrics(
        current_coverage=coverage,
        avg_coverage=0.78,
        coverage_delta=-0.13,
        coverage_trend="down",
        current_failures=failures,
        avg_failures=0.3,
        failure_delta=1.7,
        current_duration_ms=520,
        avg_duration_ms=380,
        duration_delta_pct=36.8,
        has_history=True,
    )
    return PTrendResult(metrics=metrics, history_count=5, uncovered_rules=uncovered or [])