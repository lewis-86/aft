# tests/integration/test_observability_e2e.py
"""End-to-end integration test for the full observability flow."""
import pytest
import tempfile
import os
from unittest.mock import MagicMock
from aft.github_app.app import AFTApp
from aft.llm.client import LLMClient, LLMResponse
from aft.policy.parser import PolicyRuleParser
from aft.policy.test_builder import TestBuilder
from aft.engine.plugins.pytest_plugin import PytestPlugin
from aft.llm.prompts.rule_analyzer import RuleAnalyzerPrompt
from aft.github_app.comments import CommentFormatter


class TestObservabilityE2E:
    def test_full_flow_writes_observation_and_renders_trends(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_client = MagicMock(spec=LLMClient)
            mock_client.complete = MagicMock(return_value=LLMResponse(
                content='{"semantic_summary": "test", "risk_assessment": "low", "suggested_test_cases": []}'
            ))

            app = AFTApp(
                llm_client=mock_client,
                rule_parser=PolicyRuleParser(),
                test_builder=TestBuilder(llm_client=mock_client),
                tester=PytestPlugin(),
                comment_formatter=CommentFormatter(),
                analyzer_prompt=RuleAnalyzerPrompt(),
                observability_enabled=True,
                observability_data_dir=tmpdir,
                observability_trend_window=5,
                coverage_warn_threshold=0.70,
            )

            payload = {
                "pull_request": {
                    "number": 5001,
                    "title": "test: add coverage for violence rules",
                    "state": "open",
                    "user": {"login": "tester"},
                    "head": {"ref": "feat/violence-coverage"},
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
            # Check observation file was written
            obs_file = os.path.join(tmpdir, "pr-5001.json")
            assert os.path.exists(obs_file), f"Expected {obs_file} to exist"
            # Check Quality Trends section in comment
            assert "Quality Trends" in result["comment"]

    def test_first_pr_no_history_renders_dash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_client = MagicMock(spec=LLMClient)
            mock_client.complete = MagicMock(return_value=LLMResponse(
                content='{"semantic_summary": "test", "risk_assessment": "low", "suggested_test_cases": []}'
            ))

            app = AFTApp(
                llm_client=mock_client,
                observability_enabled=True,
                observability_data_dir=tmpdir,
                observability_trend_window=5,
                coverage_warn_threshold=0.70,
            )

            payload = {
                "pull_request": {
                    "number": 9999,
                    "title": "first pr",
                    "state": "open",
                    "user": {"login": "newbie"},
                    "head": {"ref": "main"},
                },
                "diff": "--- a/rules/test.yaml\n+++ b/rules/test.yaml\n@@ -1 +1 @@\n-old: 1\n+new: 2",
                "repository": {"full_name": "test/repo"},
            }

            result = app.process_pr_event("pull_request.opened", payload)
            assert result["status"] == "success"
            assert "—" in result["comment"]  # No history available