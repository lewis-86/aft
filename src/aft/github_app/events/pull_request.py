"""Pull Request event handler."""
from __future__ import annotations
from dataclasses import dataclass
from aft.llm.client import LLMClient
from aft.policy.parser import PolicyRuleParser
from aft.policy.test_builder import TestBuilder
from aft.engine.plugins.pytest_plugin import PytestPlugin
from aft.engine.plugins.types import TestSuite
from aft.llm.prompts.rule_analyzer import RuleAnalyzerPrompt


@dataclass
class PRActivator:
    """Handles PR events for AFT GitHub App."""
    llm_client: LLMClient
    rule_parser: PolicyRuleParser
    test_builder: TestBuilder
    tester: PytestPlugin
    analyzer_prompt: RuleAnalyzerPrompt

    def handle_opened(self, payload: dict) -> dict:
        """Handle PR opened event."""
        pr = payload.get("pull_request", {})
        diff = payload.get("diff", "")
        repo = payload.get("repository", {}).get("full_name", "")

        # Step 1: Analyze rule changes
        analysis_prompt = self.analyzer_prompt.build(
            rule_diff=diff,
            context=f"PR #{pr.get('number')}: {pr.get('title')}",
        )
        analysis = self.llm_client.complete(prompt=analysis_prompt)

        # Step 2: Build test suite
        suite = self.test_builder.build_from_rule(
            rule_description=analysis.content,
            count=5,
        )

        # Step 3: Run tests
        test_result = self.tester.run_suite(suite)

        return {
            "analysis": analysis.content,
            "test_suite": suite,
            "test_result": test_result,
            "comment_body": self._build_comment(analysis.content, test_result),
        }

    def handle_changed(self, payload: dict) -> dict:
        """Handle PR synchronize (push) event."""
        return self.handle_opened(payload)

    def _build_comment(self, analysis: str, test_result) -> str:
        """Build PR comment body."""
        status = "✅ All tests passed" if test_result.failed_count == 0 else f"❌ {test_result.failed_count} test(s) failed"
        return f"""## AFT Analysis

{analysis}

## Test Results

{status}
- Passed: {test_result.passed_count}
- Failed: {test_result.failed_count}
- Duration: {test_result.total_duration_ms:.0f}ms

---
*AFT (Agent For Testing) - AI Native Testing Engine*
"""