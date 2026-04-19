# tests/unit/test_diff_router.py
import pytest
from aft.cli.router import DiffRouter, RuleFileChange, SkillFileChange, CodeChange


class TestDiffRouter:
    def test_route_rule_yaml(self):
        """rule.yaml changes routed to rule_changes."""
        diff = """--- a/rules/exec-001/rule.yaml
+++ b/rules/exec-001/rule.yaml
@@ -5,7 +5,7 @@
-level: WARNING
+level: HINT"""

        router = DiffRouter(diff)
        result = router.route()

        assert len(result.rule_changes) == 1
        assert result.rule_changes[0].rule_id == "exec-001"
        assert "level" in result.rule_changes[0].changed_fields

    def test_route_skill_md(self):
        """SKILL.md changes routed to skill_changes."""
        diff = """--- a/fixtures/canonical-skills/test-skill.md
+++ b/fixtures/canonical-skills/test-skill.md
@@ -1,3 +1,3 @@
 ---
-name: test
+name: updated-test
 ---"""

        router = DiffRouter(diff)
        result = router.route()

        assert len(result.skill_changes) == 1
        assert result.skill_changes[0].skill_name == "updated-test"

    def test_route_ts_rule_implementation(self):
        """TS rule implementation routed to code_changes."""
        diff = """--- a/src/lint/rules/exec-001.ts
+++ b/src/lint/rules/exec-001.ts
@@ -10,3 +10,4 @@
+  // new line"""

        router = DiffRouter(diff)
        result = router.route()

        assert len(result.code_changes) == 1
        assert "exec-001.ts" in result.code_changes[0].file_path

    def test_route_mixed_diff(self):
        """Combined diff with multiple file types."""
        diff = """--- a/rules/exec-001/rule.yaml
+++ b/rules/exec-001/rule.yaml
@@ -1 +1 @@
-old
+new
--- a/fixtures/canonical-skills/test.md
+++ b/fixtures/canonical-skills/test.md
@@ -1 +1 @@
-old
+new
--- a/src/lint/rules/exec-001.ts
+++ b/src/lint/rules/exec-001.ts
@@ -1 +1 @@
-old
+new"""

        router = DiffRouter(diff)
        result = router.route()

        assert len(result.rule_changes) == 1
        assert len(result.skill_changes) == 1
        assert len(result.code_changes) == 1
        assert "rule" in result.change_types
        assert "skill" in result.change_types
        assert "code" in result.change_types

    def test_change_types_list(self):
        """change_types lists all detected change categories."""
        diff = """--- a/rules/exec-001/rule.yaml
+++ b/rules/exec-001/rule.yaml
@@ -1 +1 @@
-old
+new"""

        router = DiffRouter(diff)
        result = router.route()

        assert "rule" in result.change_types
        assert "skill" not in result.change_types