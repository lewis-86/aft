# src/aft/alert/ci_gate.py
"""CI Gate — evaluates whether a PR should be allowed to merge."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aft.alert.conditions import evaluate_conditions
from aft.observability.store import ObservabilityStore
from aft.observability.trends import TrendCalculator

if TYPE_CHECKING:
    from aft.observability.types import PTrendResult


@dataclass
class CIGateResult:
    """Result of a CI gate evaluation."""
    passed: bool
    reason: str
    details: dict


class CIGate:
    """Evaluates CI gate conditions for a PR.

    Uses Layer 2 ObservabilityStore to load trend data,
    then evaluates against configured conditions.
    """

    def __init__(self, config: dict):
        self.config = config

    def check(self, pr_number: int, repo: str) -> CIGateResult:
        """Evaluate CI gate for a PR.

        Args:
            pr_number: GitHub PR number
            repo: Full repository name (owner/repo)

        Returns:
            CIGateResult with passed status and reason.
        """
        store = ObservabilityStore()
        trend_calc = TrendCalculator()

        try:
            obs = store.load(pr_number)
        except FileNotFoundError:
            # No observation data = no violation = pass
            return CIGateResult(
                passed=True,
                reason=f"No observation data for PR #{pr_number} — CI passes by default",
                details={},
            )

        history = store.load_history(limit=5)
        trend = trend_calc.compute(obs, history)

        conditions = self.config.get("conditions", {})
        violated = evaluate_conditions(trend, conditions)
        passed = not violated if self.config.get("fail_on_violation", True) else violated

        reason = self._build_reason(trend, violated)
        return CIGateResult(passed=passed, reason=reason, details=self._build_details(trend))

    def _build_reason(self, trend: "PTrendResult", violated: bool) -> str:
        m = trend.metrics
        if not violated:
            return f"CI passed: coverage={m.current_coverage * 100:.1f}%, failures={m.current_failures}"
        reasons = []
        if m.current_coverage < 0.70:
            reasons.append(f"coverage {m.current_coverage * 100:.1f}% < 70%")
        if m.current_failures > 0:
            reasons.append(f"failures={m.current_failures}")
        return f"CI blocked: {', '.join(reasons)}"

    def _build_details(self, trend: "PTrendResult") -> dict:
        m = trend.metrics
        return {
            "coverage": f"{m.current_coverage * 100:.1f}%",
            "failures": m.current_failures,
            "duration_ms": m.current_duration_ms,
            "uncovered_rules": trend.uncovered_rules,
        }