import pytest
from aft.policy.parser import PolicyRuleParser, RuleChange


class TestPolicyRuleParser:
    def test_parse_simple_rule_change(self):
        parser = PolicyRuleParser()
        diff = """--- a/rules/violence.yaml
+++ b/rules/violence.yaml
@@ -1 +1 @@
-risk_score: 0.7
+risk_score: 0.8"""
        changes = parser.parse_diff(diff)
        assert len(changes) == 1
        assert changes[0].field == "risk_score"
        assert changes[0].old_value == "0.7"
        assert changes[0].new_value == "0.8"

    def test_parse_multiple_changes(self):
        parser = PolicyRuleParser()
        diff = """--- a/rules/spam.yaml
+++ b/rules/spam.yaml
@@ -1,3 +1,3 @@
 threshold: 0.5
-action: warn
+action: block
 enabled: true"""
        changes = parser.parse_diff(diff)
        assert len(changes) == 1  # only action changed
        assert changes[0].field == "action"
        assert changes[0].old_value == "warn"
        assert changes[0].new_value == "block"