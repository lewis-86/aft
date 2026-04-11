"""End-to-end integration tests for the PR flow."""
import pytest
from unittest.mock import patch, MagicMock
from aft.github_app.app import AFTApp
from aft.llm.client import LLMClient, LLMResponse
from aft.policy.parser import PolicyRuleParser
from aft.policy.test_builder import TestBuilder
from aft.engine.plugins.pytest_plugin import PytestPlugin
from aft.engine.plugins.types import TestSuite
from aft.llm.prompts.rule_analyzer import RuleAnalyzerPrompt


class TestPRFlow:
    """Integration tests for complete PR handling flow."""

    @patch.object(LLMClient, 'complete')
    def test_full_flow_mocked_llm(self, mock_complete):
        """Test the full flow with mocked LLM."""
        mock_complete.return_value = LLMResponse(
            content='{"semantic_summary": "test", "risk_assessment": "low", "risk_reasoning": "minor change", "suggested_test_cases": []}'
        )

        app = AFTApp(
            llm_client=None,  # Will use fallback mode
        )

        payload = {
            "pull_request": {
                "number": 42,
                "title": "Increase violence risk_score threshold",
                "body": "Changed risk_score from 0.7 to 0.8",
                "state": "open",
            },
            "diff": """--- a/rules/violence.yaml
+++ b/rules/violence.yaml
@@ -1 +1 @@
-risk_score: 0.7
+risk_score: 0.8""",
            "repository": {"full_name": "tiktok/content-safety"},
        }

        result = app.process_pr_event("pull_request.opened", payload)

        assert result["status"] == "success"
        assert "test_result" in result
        assert result["test_result"].total_duration_ms >= 0

    @patch("aft.llm.client.Anthropic")
    def test_full_flow_with_mocked_api(self, mock_anthropic):
        """Test full flow with mocked Anthropic API."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"semantic_summary": "test", "risk_assessment": "low", "risk_reasoning": "minor change", "suggested_test_cases": []}')]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        llm_client = LLMClient(provider="anthropic", model="test")
        app = AFTApp(llm_client=llm_client)

        payload = {
            "pull_request": {
                "number": 1,
                "title": "Test PR",
                "body": "Test",
                "state": "open",
            },
            "diff": "--- a/rules/test.yaml\n+++ b/rules/test.yaml\n@@ -1 +1 @@\n-old: 1\n+new: 2",
            "repository": {"full_name": "test/repo"},
        }

        result = app.process_pr_event("pull_request.opened", payload)
        assert result["status"] == "success"