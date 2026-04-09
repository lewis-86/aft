import pytest
from aft.llm.prompts.rule_analyzer import RuleAnalyzerPrompt
from aft.llm.prompts.test_generator import TestGeneratorPrompt
from aft.llm.prompts.self_healer import SelfHealerPrompt


class TestRuleAnalyzerPrompt:
    def test_build_prompt_with_rule_change(self):
        prompt = RuleAnalyzerPrompt()
        rule_diff = '--- a/policy/rules.json\n+++ b/policy/rules.json\n@@ -1 +1 @@\n-{"risk_score": 0.7}\n+{"risk_score": 0.8}'
        result = prompt.build(rule_diff=rule_diff, context="Add violence detection")
        assert "risk_score" in result
        assert "0.8" in result


class TestTestGeneratorPrompt:
    def test_build_generates_test_cases(self):
        prompt = TestGeneratorPrompt()
        rule_desc = "Violence content: risk_score > 0.8 triggers ban"
        result = prompt.build(rule_description=rule_desc, test_count=3)
        assert "test" in result.lower()
        assert "3" in result or "三" in result


class TestSelfHealerPrompt:
    def test_build_identifies_failure(self):
        prompt = SelfHealerPrompt()
        failure = "AssertionError: expected 'allow' but got 'block'"
        test_code = "assert result.status == 'allow'"
        result = prompt.build(failure_output=failure, test_code=test_code)
        assert "AssertionError" in result or "assert" in result.lower()