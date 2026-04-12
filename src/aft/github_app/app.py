"""GitHub App entry point and event routing."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from typing import Callable
from aft.llm.client import LLMClient
from aft.policy.parser import PolicyRuleParser
from aft.policy.test_builder import TestBuilder
from aft.engine.plugins.pytest_plugin import PytestPlugin
from aft.engine.plugins.types import PolicyTestSuite as TestSuite, PolicyTestSuiteResult as TestSuiteResult
from aft.llm.prompts.rule_analyzer import RuleAnalyzerPrompt
from aft.llm.prompts.self_healer import SelfHealerPrompt
from aft.github_app.comments import CommentFormatter


@dataclass
class AFTApp:
    """AFT GitHub App - orchestrates all components."""

    llm_client: LLMClient = None
    rule_parser: PolicyRuleParser = field(default_factory=PolicyRuleParser)
    test_builder: TestBuilder = None
    tester: PytestPlugin = field(default_factory=PytestPlugin)
    comment_formatter: CommentFormatter = field(default_factory=CommentFormatter)
    analyzer_prompt: RuleAnalyzerPrompt = field(default_factory=RuleAnalyzerPrompt)
    healer_prompt: SelfHealerPrompt = field(default_factory=SelfHealerPrompt)
    max_self_heal_retries: int = 2

    def __post_init__(self):
        if self.llm_client is None:
            self.llm_client = LLMClient()
        if self.test_builder is None:
            self.test_builder = TestBuilder(llm_client=self.llm_client)

    def process_pr_event(
        self,
        event_type: str,
        payload: dict,
        write_comment: Callable[[str], None] | None = None,
    ) -> dict:
        """Process a GitHub PR event and return AFT response."""
        if event_type == "pull_request.opened":
            return self._handle_pr_opened(payload, write_comment)
        elif event_type == "pull_request.synchronize":
            return self._handle_pr_sync(payload, write_comment)
        elif event_type == "pull_request_review_comment":
            return self._handle_review_comment(payload, write_comment)
        else:
            return {"status": "ignored", "reason": f"Event {event_type} not handled"}

    def _handle_pr_opened(self, payload: dict, write_comment: Callable[[str], None] | None) -> dict:
        """Handle PR opened event."""
        pr = payload["pull_request"]
        diff = payload.get("diff", "")

        # 1. Analyze rule changes
        analysis_prompt = self.analyzer_prompt.build(
            rule_diff=diff,
            context=f"PR #{pr['number']}: {pr['title']}",
        )
        analysis = self.llm_client.complete(prompt=analysis_prompt)

        # 2. Build test suite
        suite = self.test_builder.build_from_rule(
            rule_description=analysis.content,
            count=5,
        )

        # 3. Run tests
        test_result = self.tester.run_suite(suite)

        # 4. Self-heal if tests failed
        healed = False
        if test_result.failed_count > 0:
            healed, test_result = self._try_self_heal(suite, test_result)

        # 5. Build and post comment
        comment = self.comment_formatter.build_full_comment(
            analysis=analysis.content,
            test_results=self.comment_formatter.format_test_results(
                name=suite.metadata.get("name", "aft_suite"),
                passed=test_result.passed_count,
                failed=test_result.failed_count,
                duration_ms=test_result.total_duration_ms,
            ),
            test_code=suite.to_pytest_code() if test_result.failed_count > 0 else "",
        )

        if write_comment:
            write_comment(comment)

        return {
            "status": "success",
            "analysis": analysis.content,
            "test_result": test_result,
            "healed": healed,
            "comment": comment,
        }

    def _handle_pr_sync(self, payload: dict, write_comment: Callable[[str], None] | None) -> dict:
        """Handle PR synchronize (new commits pushed)."""
        return self._handle_pr_opened(payload, write_comment)

    def _handle_review_comment(self, payload: dict, write_comment: Callable[[str], None] | None) -> dict:
        """Handle inline review comments for deeper interaction."""
        comment_body = payload.get("comment", {}).get("body", "")
        if "AFT" not in comment_body:
            return {"status": "ignored"}

        # Allow users to ask AFT to do specific things via comments
        if "regenerate tests" in comment_body.lower():
            return self._handle_pr_opened(payload, write_comment)

        return {"status": "acknowledged"}

    def _try_self_heal(self, suite: TestSuite, test_result: TestSuiteResult) -> tuple[bool, TestSuiteResult]:
        """Attempt to self-heal failing tests.

        Parses LLM response for test_name + corrected_code pairs, updates
        the suite, then re-runs tests to verify the fix.
        """
        if self.llm_client is None:
            return False, test_result

        failed_tests = [r for r in test_result.results if not r.passed]

        for retry in range(self.max_self_heal_retries):
            healer_prompt = self.healer_prompt.build(
                failure_output="\n".join([
                    f"Test {t.name} failed: {t.error_message or t.output}"
                    for t in failed_tests
                ]),
                test_code=suite.to_pytest_code(),
            )
            response = self.llm_client.complete(prompt=healer_prompt)
            healed_suite = self._apply_heal_response(suite, response.content)
            test_result = self.tester.run_suite(healed_suite)
            if test_result.failed_count == 0:
                return True, test_result

        return False, test_result

    def _apply_heal_response(self, suite: TestSuite, llm_content: str) -> TestSuite:
        """Parse LLM's JSON response and apply test code fixes to the suite.

        Looks for JSON with test_name + corrected_code pairs and updates
        matching PolicyTestCase objects in the suite.
        """
        try:
            # Try to extract JSON from LLM output
            json_match = re.search(r'\{.*\}', llm_content, re.DOTALL)
            if not json_match:
                return suite
            data = json.loads(json_match.group())
            proposed_fix = data.get("proposed_fix", "")
            if not proposed_fix:
                return suite
        except (json.JSONDecodeError, KeyError):
            return suite

        # Try to extract test_name and corrected_code from proposed_fix
        test_name_match = re.search(r'def\s+(test_\w+)\s*\(', proposed_fix)
        if not test_name_match:
            return suite

        fixed_name = test_name_match.group(1)
        for tc in suite.test_cases:
            if tc.name == fixed_name:
                tc.code = proposed_fix
                break

        return suite