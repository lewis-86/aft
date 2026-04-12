import pytest
from aft.policy.test_builder import TestBuilder
from aft.engine.plugins.types import PolicyTestCase, PolicyTestSuite


class TestTestBuilder:
    def test_build_from_rule_description(self):
        builder = TestBuilder()
        rule = "Violence content with risk_score > 0.8 should be blocked"
        suite = builder.build_from_rule(rule, count=3)
        assert isinstance(suite, PolicyTestSuite)
        assert len(suite.test_cases) == 3

    def test_test_case_has_required_fields(self):
        builder = TestBuilder()
        rule = "Spam content should trigger warn action"
        suite = builder.build_from_rule(rule, count=1)
        tc = suite.test_cases[0]
        assert tc.name.startswith("test_")
        assert tc.description != ""
        assert tc.code != ""