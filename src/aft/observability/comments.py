# src/aft/observability/comments.py
"""Renders Quality Trends sections for GitHub PR comments."""
from __future__ import annotations
from aft.observability.types import PTrendResult


class ObservabilityComment:
    """Renders a GitHub PR comment section for quality trend observations."""

    COVERAGE_WARN_THRESHOLD = 0.70
    DURATION_WARN_PCT = 30.0

    def render(self, trend: PTrendResult) -> str:
        """Render the Quality Trends section as markdown."""
        m = trend.metrics

        if m.has_history:
            coverage_str = f"{m.current_coverage * 100:.1f}%"
            avg_coverage_str = f"{m.avg_coverage * 100:.1f}%"
            delta_str = self._format_delta(m.coverage_delta * 100, sign=True)
            trend_str = f"{self._coverage_icon(m.coverage_trend)} {delta_str}"
            failures_str = f"{m.current_failures}"
            avg_failures_str = f"{m.avg_failures:.1f}"
            failure_trend_str = self._format_failure_delta(m.failure_delta, has_history=True)
            duration_str = f"{m.current_duration_ms}ms"
            avg_duration_str = f"{m.avg_duration_ms:.0f}ms"
            duration_trend_str = f"{self._duration_icon(m.duration_delta_pct)} {m.duration_delta_pct:+.1f}%"
            history_note = f"Last {trend.history_count} runs avg"
        else:
            coverage_str = f"{m.current_coverage * 100:.1f}%"
            avg_coverage_str = "—"
            delta_str = "—"
            trend_str = "—"
            failures_str = f"{m.current_failures}"
            avg_failures_str = "—"
            failure_trend_str = "—"
            duration_str = f"{m.current_duration_ms}ms"
            avg_duration_str = "—"
            duration_trend_str = "—"
            history_note = "First run (no history)"

        coverage_warn = "⚠️" if m.current_coverage < self.COVERAGE_WARN_THRESHOLD else ""

        uncovered_section = ""
        if trend.uncovered_rules:
            lines = "\n".join(
                f"- `{r}` — no test coverage ⚠️" for r in trend.uncovered_rules
            )
            uncovered_section = f"\n### Rule Coverage Gaps\n{lines}\n"

        return f"""### Quality Trends

| Metric | This PR | {history_note} | Trend |
|--------|---------|---------------|-------|
| Coverage | {coverage_str} {coverage_warn} | {avg_coverage_str} | {trend_str} |
| Failures | {failures_str} | {avg_failures_str} | {failure_trend_str} |
| Duration | {duration_str} | {avg_duration_str} | {duration_trend_str} |

{uncovered_section}"""

    def _coverage_icon(self, trend: str) -> str:
        return {"up": "📈", "down": "📉", "stable": "✅", "none": "—"}.get(trend, "—")

    def _failure_icon(self, delta: float) -> str:
        if delta > 0:
            return "⚠️"
        return "✅"

    def _duration_icon(self, delta_pct: float) -> str:
        if delta_pct > self.DURATION_WARN_PCT:
            return "⚠️"
        if delta_pct < -self.DURATION_WARN_PCT:
            return "📈"
        return "✅"

    def _format_delta(self, delta: float, sign: bool = False) -> str:
        if delta == 0:
            return "—"
        prefix = "+" if (sign and delta > 0) else ""
        return f"{prefix}{delta:.1f}%"

    def _format_failure_delta(self, delta: float, has_history: bool) -> str:
        if not has_history:
            return "—"
        if delta > 0:
            return f"⚠️ +{delta:.1f}"
        if delta < 0:
            return f"✅ {delta:.1f}"
        return "✅ stable"