"""Tests for SkillContentAnalyzer."""
import pytest
from unittest.mock import patch, MagicMock
from aft.cli.parsers.lint import LintReport, LintResult, Level
from aft.cli.analyzers.utils import parse_llm_json_response
from aft.llm.client import LLMClient, LLMResponse
from aft.cli.analyzers.content import SkillContentAnalyzer


class TestSkillContentAnalyzer:
    """Test cases for SkillContentAnalyzer."""

    def test_analyzer_initialization(self):
        """Test SkillContentAnalyzer can be initialized."""
        mock_client = MagicMock(spec=LLMClient)
        analyzer = SkillContentAnalyzer(llm_client=mock_client)
        assert analyzer.llm_client is mock_client
        assert analyzer.prompt_builder is not None

    @patch.object(LLMClient, "complete")
    def test_analyze_returns_structured_results(self, mock_complete):
        """Test analyze method returns structured results from LLM."""
        mock_response = MagicMock(spec=LLMResponse)
        mock_response.content = '{"skill_summary": "Test skill", "clarity_assessment": "clear"}'
        mock_complete.return_value = mock_response

        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete = mock_complete

        lint_report = LintReport(
            skill_path="test_skill",
            skill_name="Test Skill",
            overall_passed=True,
        )

        analyzer = SkillContentAnalyzer(llm_client=mock_client)
        result = analyzer.analyze("skill diff content", lint_report)

        assert "skill_summary" in result
        assert result["skill_summary"] == "Test skill"

    @patch.object(LLMClient, "complete")
    def test_analyze_passes_correct_prompt(self, mock_complete):
        """Test analyze method builds correct prompt."""
        mock_response = MagicMock(spec=LLMResponse)
        mock_response.content = '{"skill_summary": "Test"}'
        mock_complete.return_value = mock_response

        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete = mock_complete

        lint_report = LintReport(
            skill_path="test_skill",
            skill_name="Test Skill",
            overall_passed=True,
        )

        analyzer = SkillContentAnalyzer(llm_client=mock_client)
        analyzer.analyze("skill diff content", lint_report, context="additional context")

        call_args = mock_complete.call_args
        prompt = call_args[1]["prompt"]
        assert "skill diff content" in prompt
        assert "Test Skill" in prompt
        assert "additional context" in prompt

    @patch.object(LLMClient, "complete")
    def test_analyze_with_lint_blockers(self, mock_complete):
        """Test analyze method includes lint blocker messages in prompt."""
        mock_response = MagicMock(spec=LLMResponse)
        mock_response.content = '{"skill_summary": "Test"}'
        mock_complete.return_value = mock_response

        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete = mock_complete

        lint_report = LintReport(
            skill_path="test_skill",
            skill_name="Test Skill",
            overall_passed=False,
            blockers=[
                LintResult(rule_id="RULE001", message="Missing description", level=Level.BLOCKER),
            ],
        )

        analyzer = SkillContentAnalyzer(llm_client=mock_client)
        analyzer.analyze("skill diff", lint_report)

        call_args = mock_complete.call_args
        prompt = call_args[1]["prompt"]
        assert "RULE001" in prompt
        assert "Missing description" in prompt
        assert "Blockers:" in prompt


class TestParseLlJsonResponse:
    """Test cases for parse_llm_json_response utility function."""

    def test_parse_llm_json_response_handles_markdown_json(self):
        """Test parse_llm_json_response extracts JSON from markdown code blocks."""
        content = '```json\n{"skill_summary": "Test"}\n```'
        result = parse_llm_json_response(content)
        assert result["skill_summary"] == "Test"

    def test_parse_llm_json_response_handles_plain_json(self):
        """Test parse_llm_json_response handles plain JSON."""
        content = '{"skill_summary": "Test"}'
        result = parse_llm_json_response(content)
        assert result["skill_summary"] == "Test"

    def test_parse_llm_json_response_handles_json_in_text(self):
        """Test parse_llm_json_response extracts JSON from text."""
        content = 'Here is my response: {"skill_summary": "Test"} - end of response'
        result = parse_llm_json_response(content)
        assert result["skill_summary"] == "Test"

    def test_parse_llm_json_response_handles_invalid_json(self):
        """Test parse_llm_json_response handles invalid JSON gracefully."""
        content = "This is not JSON at all"
        result = parse_llm_json_response(content)
        assert "error" in result
        assert "raw" in result

    def test_parse_llm_json_response_handles_malformed_json(self):
        """Test parse_llm_json_response handles malformed JSON gracefully."""
        content = '{"skill_summary": "Test", invalid}'
        result = parse_llm_json_response(content)
        assert "error" in result
        assert "raw" in result