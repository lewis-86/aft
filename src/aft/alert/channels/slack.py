# src/aft/alert/channels/slack.py
"""Slack notifier for AFT alerts."""
from __future__ import annotations
import json
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aft.observability.types import PTrendResult


class _RequestWithUrl(urllib.request.Request):
    """Request subclass that includes URL in string representation for test assertion."""
    def __repr__(self):
        return self.full_url


class SlackNotifier:
    """Sends AFT quality alerts to a Slack webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, trend: "PTrendResult", pr_info: dict) -> bool:
        """Send an alert to Slack.

        Args:
            trend: PTrendResult with current metrics
            pr_info: dict with pr_number, pr_url, repo, etc.

        Returns:
            True if sent successfully, False otherwise.
        """
        payload = {
            "text": self._build_text(trend, pr_info),
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self._build_markdown(trend, pr_info),
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View PR"},
                            "url": pr_info.get("pr_url", ""),
                        }
                    ]
                }
            ]
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = _RequestWithUrl(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _build_text(self, trend, pr_info: dict) -> str:
        m = trend.metrics
        pr_num = pr_info.get("pr_number", "?")
        return f"[AFT Quality Alert] PR #{pr_num} coverage: {m.current_coverage * 100:.1f}%"

    def _build_markdown(self, trend, pr_info: dict) -> str:
        m = trend.metrics
        pr_num = pr_info.get("pr_number", "?")
        repo = pr_info.get("repo", "?")
        coverage_icon = "⚠️" if m.current_coverage < 0.70 else "✅"
        lines = [
            f"*AFT Quality Alert*",
            f"PR #{pr_num} | repo: {repo}",
            f"Coverage: {m.current_coverage * 100:.1f}% {coverage_icon}",
            f"Failures: {m.current_failures} (avg: {m.avg_failures:.1f})",
            f"Duration: {m.current_duration_ms}ms (avg: {m.avg_duration_ms:.0f}ms)",
        ]
        if trend.uncovered_rules:
            lines.append(f"Uncovered rules: {', '.join(trend.uncovered_rules)}")
        return "\n".join(lines)