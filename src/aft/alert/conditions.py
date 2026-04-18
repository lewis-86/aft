# src/aft/alert/conditions.py
"""Alert condition evaluation engine."""
from __future__ import annotations


def evaluate_conditions(trend: "PTrendResult", conditions: dict) -> bool:
    """Evaluate whether alert/CI-gate conditions are met by a trend result.

    Args:
        trend: PTrendResult from TrendCalculator.compute()
        conditions: dict with keys:
            - coverage_below: float | None
            - failures_above: int | None
            - coverage_drop_above: float | None
            - duration_spike_above: float | None (as ratio, e.g. 0.30 for 30%)
            - self_heal_failed: bool
            - composite: "OR" | "AND"

    Returns:
        True if conditions are met, False otherwise.
    """
    results: list[bool] = []
    m = trend.metrics

    if conditions.get("coverage_below") is not None:
        results.append(m.current_coverage < conditions["coverage_below"])

    if conditions.get("failures_above") is not None:
        results.append(m.current_failures > conditions["failures_above"])

    if conditions.get("coverage_drop_above") is not None:
        results.append(m.coverage_delta < -conditions["coverage_drop_above"])

    if conditions.get("duration_spike_above") is not None:
        threshold_pct = conditions["duration_spike_above"] * 100
        results.append(m.duration_delta_pct > threshold_pct)

    if conditions.get("self_heal_failed"):
        results.append(len(trend.uncovered_rules) > 0)

    composite = conditions.get("composite", "OR")
    if not results:
        return False
    if composite == "AND":
        return all(results)
    return any(results)