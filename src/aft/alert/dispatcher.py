# src/aft/alert/dispatcher.py
"""Alert dispatcher — evaluates conditions and dispatches to notification channels."""
from __future__ import annotations
from typing import TYPE_CHECKING

from aft.alert.channels.slack import SlackNotifier
from aft.alert.channels.feishu import FeishuNotifier
from aft.alert.conditions import evaluate_conditions

if TYPE_CHECKING:
    from aft.observability.types import PTrendResult


class AlertDispatcher:
    """Evaluates alert conditions and dispatches notifications to channels."""

    def __init__(self, trend_result: "PTrendResult", config: dict):
        self.trend = trend_result
        self.config = config

    def should_alert(self) -> bool:
        """Return True if alert conditions are met."""
        return evaluate_conditions(self.trend, self.config.get("conditions", {}))

    def dispatch(self) -> dict:
        """Dispatch alert to all configured channels.

        Returns:
            dict mapping channel name to success (bool).
        """
        results = {}
        channels = self.config.get("channels", [])

        if "slack" in channels and self.config.get("slack_webhook_url"):
            notifier = SlackNotifier(webhook_url=self.config["slack_webhook_url"])
            pr_info = self._build_pr_info()
            results["slack"] = notifier.send(trend=self.trend, pr_info=pr_info)

        if "feishu" in channels and self.config.get("feishu_webhook_url"):
            notifier = FeishuNotifier(webhook_url=self.config["feishu_webhook_url"])
            pr_info = self._build_pr_info()
            results["feishu"] = notifier.send(trend=self.trend, pr_info=pr_info)

        if "github_comment" in channels:
            # GitHub comment is handled separately in AFTApp._record_observability
            results["github_comment"] = True

        return results

    def _build_pr_info(self) -> dict:
        return {
            "pr_number": getattr(self.trend, "pr_number", "?"),
            "repo": getattr(self.trend, "repo", "?"),
            "pr_url": f"https://github.com/{getattr(self.trend, 'repo', '?')}/pull/{getattr(self.trend, 'pr_number', '?')}",
        }