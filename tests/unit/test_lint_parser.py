"""Tests for LintResultParser."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from aft.cli.parsers.lint import Level, LintReport, LintResult, LintResultParser


class TestLintResult:
    """Tests for ValidationResult (LintResult)."""

    def test_lint_result_basic(self):
        """Test creating a basic LintResult."""
        result = LintResult(
            rule_id="no-debugger",
            level=Level.BLOCKER,
            message="debugger statement found",
        )
        assert result.rule_id == "no-debugger"
        assert result.level == Level.BLOCKER
        assert result.message == "debugger statement found"

    def test_lint_result_from_dict(self):
        """Test parsing LintResult from dictionary."""
        data = {
            "ruleId": "no-console",
            "ruleName": "No Console",
            "passed": True,
            "level": "WARNING",
            "message": "console statement allowed in dev",
        }
        result = LintResult.from_dict(data)
        assert result.rule_id == "no-console"
        assert result.level.value == "WARNING"
        assert result.message == "console statement allowed in dev"


class TestLintReport:
    """Tests for LintReport."""

    def test_lint_report_basic(self):
        """Test creating a basic LintReport."""
        report = LintReport(
            skill_path="/path/to/skill",
            skill_name="TestSkill",
            overall_passed=True,
            blockers=[],
            warnings=[],
            hints=[],
            timestamp="2024-01-01T00:00:00Z",
        )
        assert report.skill_path == "/path/to/skill"
        assert report.overall_passed is True
        assert len(report.blockers) == 0

    def test_lint_report_from_dict(self):
        """Test parsing LintReport from dictionary."""
        data = {
            "skillPath": "/path/to/skill",
            "skillName": "TestSkill",
            "overallPassed": True,
            "blockers": [
                {
                    "ruleId": "required-fields",
                    "ruleName": "Required Fields",
                    "passed": False,
                    "level": "BLOCKER",
                    "message": "missing required field",
                    "field": "name",
                }
            ],
            "warnings": [],
            "hints": [],
            "timestamp": "2024-01-01T00:00:00Z",
        }
        report = LintReport.from_dict(data)
        assert report.skill_path == "/path/to/skill"
        assert report.skill_name == "TestSkill"
        assert len(report.blockers) == 1
        assert report.blockers[0].rule_id == "required-fields"
        assert report.blockers[0].message == "missing required field"
        assert report.blockers[0].level.value == "BLOCKER"

    def test_to_policy_test_suite_result_no_blockers(self):
        """Test conversion to PolicyTestSuiteResult when no blockers (passed)."""
        report = LintReport(
            skill_path="/path/to/skill",
            skill_name="TestSkill",
            overall_passed=True,
            blockers=[],
            warnings=[],
            hints=[],
            timestamp="2024-01-01T00:00:00Z",
        )
        result = report.to_policy_test_suite_result()
        assert result.suite_name == "TestSkill"
        assert result.passed_count == 1
        assert result.failed_count == 0
        assert len(result.results) == 1
        assert result.results[0].passed is True

    def test_to_policy_test_suite_result_with_blockers(self):
        """Test conversion to PolicyTestSuiteResult when blockers exist (failed)."""
        blocker = LintResult(
            rule_id="required-fields",
            level=Level.BLOCKER,
            message="missing required field",
        )
        report = LintReport(
            skill_path="/path/to/skill",
            skill_name="TestSkill",
            overall_passed=False,
            blockers=[blocker],
            warnings=[],
            hints=[],
            timestamp="2024-01-01T00:00:00Z",
        )
        result = report.to_policy_test_suite_result()
        assert result.suite_name == "TestSkill"
        assert result.passed_count == 0
        assert result.failed_count == 1
        assert len(result.results) == 1
        assert result.results[0].passed is False
        assert "required-fields" in result.results[0].error_message


class TestLintResultParser:
    """Tests for LintResultParser."""

    def test_parse_object(self):
        """Test parsing a single lint report object."""
        data = {
            "skillPath": "/path/to/skill",
            "skillName": "TestSkill",
            "overallPassed": True,
            "blockers": [],
            "warnings": [],
            "hints": [],
            "timestamp": "2024-01-01T00:00:00Z",
        }
        report = LintResultParser.parse_object(data)
        assert report.skill_name == "TestSkill"
        assert report.overall_passed is True

    def test_parse_jsonl_file(self):
        """Test parsing a JSONL file with multiple lint reports."""
        jsonl_content = json.dumps({
            "skillPath": "/path/to/skill1",
            "skillName": "SkillOne",
            "overallPassed": True,
            "blockers": [],
            "warnings": [],
            "hints": [],
            "timestamp": "2024-01-01T00:00:00Z",
        }) + "\n" + json.dumps({
            "skillPath": "/path/to/skill2",
            "skillName": "SkillTwo",
            "overallPassed": False,
            "blockers": [
                {
                    "ruleId": "required-fields",
                    "ruleName": "Required Fields",
                    "passed": False,
                    "level": "BLOCKER",
                    "message": "missing required field",
                }
            ],
            "warnings": [],
            "hints": [],
            "timestamp": "2024-01-01T00:00:00Z",
        }) + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(jsonl_content)
            temp_path = f.name

        try:
            reports = list(LintResultParser.parse_jsonl_file(temp_path))
            assert len(reports) == 2
            assert reports[0].skill_name == "SkillOne"
            assert reports[0].overall_passed is True
            assert reports[1].skill_name == "SkillTwo"
            assert reports[1].overall_passed is False
        finally:
            Path(temp_path).unlink()

    def test_parse_jsonl_file_empty_file(self):
        """Test parsing an empty JSONL file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            reports = list(LintResultParser.parse_jsonl_file(temp_path))
            assert len(reports) == 0
        finally:
            Path(temp_path).unlink()
