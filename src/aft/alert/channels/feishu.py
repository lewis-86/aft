# src/aft/alert/channels/feishu.py
"""Feishu (Lark) notifier for AFT alerts."""
from __future__ import annotations
import json
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aft.observability.types import PTrendResult


class FeishuNotifier:
    """Sends AFT quality alerts to a Feishu webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, trend: "PTrendResult", pr_info: dict) -> bool:
        """Send an alert to Feishu.

        Args:
            trend: PTrendResult with current metrics
            pr_info: dict with pr_number, pr_url, repo, etc.

        Returns:
            True if sent successfully, False otherwise.
        """
        m = trend.metrics
        template = "red" if m.current_coverage < 0.70 else "orange"

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": "AFT Quality Alert"},
                    "template": template,
                },
                "elements": [
                    {"tag": "div", "content": self._build_markdown(trend, pr_info)},
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "text": "View PR"},
                                "type": "primary",
                                "url": pr_info.get("pr_url", ""),
                            }
                        ]
                    }
                ]
            }
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _build_markdown(self, trend, pr_info: dict) -> str:
        m = trend.metrics
        pr_num = pr_info.get("pr_number", "?")
        repo = pr_info.get("repo", "?")
        coverage_icon = "⚠️" if m.current_coverage < 0.70 else "✅"
        lines = [
            f"**AFT Quality Alert**",
            f"PR #{pr_num} | repo: {repo}",
            f"Coverage: {m.current_coverage * 100:.1f}% {coverage_icon}",
            f"Failures: {m.current_failures} (avg: {m.avg_failures:.1f})",
            f"Duration: {m.current_duration_ms}ms (avg: {m.avg_duration_ms:.0f}ms)",
        ]
        if trend.uncovered_rules:
            lines.append(f"Uncovered rules: {', '.join(trend.uncovered_rules)}")
        return "\n".join(lines)