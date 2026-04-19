"""Tests for SkillRuleAnalyzer."""
import pytest
from unittest.mock import patch, MagicMock
from aft.llm.client import LLMClient, LLMResponse
from aft.cli.analyzers.rule import SkillRuleAnalyzer


class TestSkillRuleAnalyzer:
    """Test cases for SkillRuleAnalyzer."""

    def test_analyzer_initialization(self):
        """Test SkillRuleAnalyzer can be initialized."""
        mock_client = MagicMock(spec=LLMClient)
        analyzer = SkillRuleAnalyzer(llm_client=mock_client)
        assert analyzer.llm_client is mock_client
        assert analyzer.prompt_builder is not None

    @patch.object(LLMClient, "complete")
    def test_analyze_returns_structured_results(self, mock_complete):
        """Test analyze method returns structured results from LLM."""
        mock_response = MagicMock(spec=LLMResponse)
        mock_response.content = '{"rule_summary": "Test rule", "coverage_assessment": "good"}'
        mock_complete.return_value = mock_response

        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete = mock_complete
        analyzer = SkillRuleAnalyzer(llm_client=mock_client)
        result = analyzer.analyze("rule: test")

        assert "rule_summary" in result
        assert result["rule_summary"] == "Test rule"

    @patch.object(LLMClient, "complete")
    def test_analyze_passes_correct_prompt(self, mock_complete):
        """Test analyze method builds correct prompt."""
        mock_response = MagicMock(spec=LLMResponse)
        mock_response.content = '{"rule_summary": "Test"}'
        mock_complete.return_value = mock_response

        mock_client = MagicMock(spec=LLMClient)
        mock_client.complete = mock_complete
        analyzer = SkillRuleAnalyzer(llm_client=mock_client)
        analyzer.analyze("rule: test content", context="additional context")

        call_args = mock_complete.call_args
        prompt = call_args[1]["prompt"]
        assert "rule: test content" in prompt
        assert "additional context" in prompt

    def test_parse_response_handles_markdown_json(self):
        """Test _parse_response extracts JSON from markdown code blocks."""
        mock_client = MagicMock(spec=LLMClient)
        analyzer = SkillRuleAnalyzer(llm_client=mock_client)

        mock_response = MagicMock(spec=LLMResponse)
        mock_response.content = '```json\n{"rule_summary": "Test"}\n```'

        result = analyzer._parse_response(mock_response)
        assert result["rule_summary"] == "Test"

    def test_parse_response_handles_plain_json(self):
        """Test _parse_response handles plain JSON."""
        mock_client = MagicMock(spec=LLMClient)
        analyzer = SkillRuleAnalyzer(llm_client=mock_client)

        mock_response = MagicMock(spec=LLMResponse)
        mock_response.content = '{"rule_summary": "Test"}'

        result = analyzer._parse_response(mock_response)
        assert result["rule_summary"] == "Test"

    def test_parse_response_handles_invalid_json(self):
        """Test _parse_response handles invalid JSON gracefully."""
        mock_client = MagicMock(spec=LLMClient)
        analyzer = SkillRuleAnalyzer(llm_client=mock_client)

        mock_response = MagicMock(spec=LLMResponse)
        mock_response.content = "This is not JSON"

        result = analyzer._parse_response(mock_response)
        assert "error" in result
        assert "raw" in result