"""Parser for Skill-Harness lint JSON output."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from aft.engine.plugins.types import PolicyTestSuiteResult, TestResult


class Level(Enum):
    """Validation result level."""
    BLOCKER = "BLOCKER"
    WARNING = "WARNING"
    HINT = "HINT"


@dataclass
class LintResult:
    """Represents a single validation result (ValidationResult from TypeScript).

    Spec fields: rule_id, message, level.
    """
    rule_id: str
    message: str
    level: Level

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LintResult:
        """Parse from a dictionary.

        Parses all available fields from input but only populates the
        3 spec fields: rule_id, message, level.
        """
        level_str = data.get("level", "WARNING")
        try:
            level = Level(level_str)
        except ValueError:
            level = Level.WARNING

        return cls(
            rule_id=data.get("ruleId", ""),
            message=data.get("message", ""),
            level=level,
        )


@dataclass
class LintReport:
    """Represents a complete lint report (LintReport from TypeScript)."""
    skill_path: str
    skill_name: str | None
    overall_passed: bool
    blockers: list[LintResult] = field(default_factory=list)
    warnings: list[LintResult] = field(default_factory=list)
    hints: list[LintResult] = field(default_factory=list)
    timestamp: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LintReport:
        """Parse from a dictionary."""
        blockers = [LintResult.from_dict(r) for r in data.get("blockers", [])]
        warnings = [LintResult.from_dict(r) for r in data.get("warnings", [])]
        hints = [LintResult.from_dict(r) for r in data.get("hints", [])]

        return cls(
            skill_path=data.get("skillPath", ""),
            skill_name=data.get("skillName"),
            overall_passed=data.get("overallPassed", False),
            blockers=blockers,
            warnings=warnings,
            hints=hints,
            timestamp=data.get("timestamp", ""),
        )

    def to_policy_test_suite_result(self) -> PolicyTestSuiteResult:
        """Convert to AFT's PolicyTestSuiteResult.

        Mapping:
        - blockers.length == 0 -> passed_count = 1, failed_count = 0
        - blockers.length > 0 -> passed_count = 0, failed_count = 1
        """
        if len(self.blockers) == 0:
            # Passed: no blockers
            test_result = TestResult(
                name=self.skill_name or self.skill_path,
                passed=True,
                duration_ms=0.0,
                error_message="",
                output="",
            )
            passed_count = 1
            failed_count = 0
        else:
            # Failed: has blockers
            error_messages = [f"{b.rule_id}: {b.message}" for b in self.blockers]
            error_message = "; ".join(error_messages)
            test_result = TestResult(
                name=self.skill_name or self.skill_path,
                passed=False,
                duration_ms=0.0,
                error_message=error_message,
                output="",
            )
            passed_count = 0
            failed_count = 1

        result = PolicyTestSuiteResult(
            suite_name=self.skill_name or self.skill_path,
            results=[test_result],
            total_duration_ms=0.0,
        )
        return result


class LintResultParser:
    """Parser for Skill-Harness lint JSON output."""

    @staticmethod
    def parse_object(data: dict[str, Any]) -> LintReport:
        """Parse a single lint report object."""
        return LintReport.from_dict(data)

    @staticmethod
    def parse_jsonl_file(file_path: str | Path) -> list[LintReport]:
        """Parse a JSONL file containing lint reports.

        Args:
            file_path: Path to the JSONL file.

        Yields:
            LintReport objects from the file.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                yield LintReport.from_dict(data)
