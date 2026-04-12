"""Types for AFT observability data model."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class PCoverageData:
    """Coverage data for a single PR run."""
    rules_total: int = 0
    rules_covered: int = 0
    coverage_ratio: float = 0.0


@dataclass
class PRuleCoverageEntry:
    """Per-rule coverage status."""
    rule: str
    covered: bool
    test_names: list[str] = field(default_factory=list)


@dataclass
class PRObservationData:
    """Full observation record for a single PR."""
    pr_number: int
    repo: str
    branch: str
    author: str
    timestamp: str = ""  # ISO8601, set by store on save
    rule_files_changed: list[str] = field(default_factory=list)
    test_result: dict = field(default_factory=dict)
    coverage: dict = field(default_factory=dict)
    rule_coverage: list[PRuleCoverageEntry] = field(default_factory=list)
    self_healed: bool = False
    risk_assessment: str = ""
    trend_reference: str = ""


@dataclass
class PTrendMetrics:
    """Computed trend metrics from historical data."""
    current_coverage: float
    avg_coverage: float
    coverage_delta: float
    coverage_trend: str  # "up" | "down" | "stable" | "none"
    current_failures: int
    avg_failures: float
    failure_delta: float
    current_duration_ms: int
    avg_duration_ms: float
    duration_delta_pct: float
    has_history: bool


@dataclass
class PTrendResult:
    """Result of trend computation."""
    metrics: PTrendMetrics
    history_count: int  # number of historical records used
    uncovered_rules: list[str] = field(default_factory=list)