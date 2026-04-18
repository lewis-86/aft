# tests/unit/test_feishu_notifier.py
import pytest
from unittest.mock import patch, MagicMock
from aft.alert.channels.feishu import FeishuNotifier
from aft.observability.types import PTrendResult, PTrendMetrics


class TestFeishuNotifier:
    @patch("aft.alert.channels.feishu.urllib.request.urlopen")
    def test_send_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        notifier = FeishuNotifier(webhook_url="https://open.feishu.cn/test")
        trend = _make_trend(coverage=0.65, failures=2)
        pr_info = {"pr_number": 2341, "pr_url": "https://github.com/tiktok/repo/pull/2341", "repo": "tiktok/repo"}

        result = notifier.send(trend=trend, pr_info=pr_info)

        assert result is True

    @patch("aft.alert.channels.feishu.urllib.request.urlopen")
    def test_send_failure_returns_false(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection refused")

        notifier = FeishuNotifier(webhook_url="https://open.feishu.cn/test")
        trend = _make_trend(coverage=0.65, failures=2)
        pr_info = {"pr_number": 2341, "pr_url": "https://github.com/tiktok/repo/pull/2341", "repo": "tiktok/repo"}

        result = notifier.send(trend=trend, pr_info=pr_info)

        assert result is False

    def test_build_markdown_contains_metrics(self):
        notifier = FeishuNotifier(webhook_url="https://open.feishu.cn/test")
        trend = _make_trend(coverage=0.65, failures=2)
        pr_info = {"pr_number": 2341, "pr_url": "https://github.com/tiktok/repo/pull/2341", "repo": "tiktok/repo"}

        text = notifier._build_markdown(trend=trend, pr_info=pr_info)

        assert "65.0%" in text
        assert "2341" in text
        assert "AFT Quality Alert" in text


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