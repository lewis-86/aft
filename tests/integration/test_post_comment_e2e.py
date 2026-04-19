# tests/integration/test_post_comment_e2e.py
"""End-to-end test for aft post-comment command."""
import pytest
import tempfile
import json
import sys
import importlib
import importlib.util
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from aft.cli.github import GitHubCommentPoster
from aft.cli.router import DiffRouter
from aft.cli.parsers.lint import LintResultParser, Level


# Workaround for importing build_skill_harness_comment from cli.py module
# (cli.py is a standalone module file, not part of cli/ package)
_cli_package = sys.modules.get('aft.cli')

# Remove the cli package temporarily
if 'aft.cli' in sys.modules:
    del sys.modules['aft.cli']

# Load cli.py as a fresh module
_cli_path = '/Users/lijingnan/Desktop/project/test_haress_engine/aft/src/aft/cli.py'
_spec = importlib.util.spec_from_file_location('_cli_module', _cli_path)
_cli_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cli_module)

# Merge attributes into _cli_package
if _cli_package is not None:
    for attr in dir(_cli_module):
        if not attr.startswith('_'):
            setattr(_cli_package, attr, getattr(_cli_module, attr))
    sys.modules['aft.cli'] = _cli_package
else:
    sys.modules['aft.cli'] = _cli_module

# Extract what we need from the module
build_skill_harness_comment = _cli_module.build_skill_harness_comment


class TestPostCommentE2E:
    def test_build_skill_harness_comment_with_lint_results(self):
        """Build comment from diff + lint results without LLM."""
        from aft.cli.router import DiffRouterResult, RuleFileChange, SkillFileChange
        from aft.cli.parsers.lint import LintReport, LintResult

        diff = """--- a/rules/exec-001/rule.yaml
+++ b/rules/exec-001/rule.yaml
@@ -1 +1 @@
-old
+new"""

        router = DiffRouter(diff)
        diff_result = router.route()

        lint_report = LintReport(
            skill_path="test.md",
            skill_name="test",
            overall_passed=True,
            blockers=[],
            warnings=[LintResult(rule_id="exec-003", message="dir mismatch", level=Level.WARNING)],
            hints=[LintResult(rule_id="style-001", message="no language", level=Level.HINT)],
        )

        comment = build_skill_harness_comment(
            diff_result=diff_result,
            lint_results=[lint_report],
            rule_analysis=[],
            content_analysis=[],
            analysis_available=True,
        )

        assert "Change Analysis" in comment
        assert "Lint Results" in comment
        assert "Blockers | 0" in comment
        assert "Warnings | 1" in comment

    def test_build_comment_with_rule_changes(self):
        """Build comment with rule changes (no LLM)."""
        from aft.cli.router import DiffRouterResult, RuleFileChange

        diff_result = DiffRouterResult(
            rule_changes=[
                RuleFileChange(rule_id="exec-001", diff="...", changed_fields=["level"])
            ],
            change_types=["rule"],
        )

        comment = build_skill_harness_comment(
            diff_result=diff_result,
            lint_results=[],
            rule_analysis=[{
                "rule_id": "exec-001",
                "change_summary": "severity lowered",
                "risk_assessment": "low",
                "backward_compatible": True,
            }],
            content_analysis=[],
            analysis_available=True,
        )

        assert "exec-001" in comment
        assert "severity lowered" in comment

    @patch("aft.cli.github.urllib.request.urlopen")
    def test_github_poster_integration(self, mock_urlopen):
        """Test GitHubCommentPoster with real-like URL construction."""
        mock_response = MagicMock()
        mock_response.status = 201
        mock_urlopen.return_value.__enter__.return_value = mock_response

        poster = GitHubCommentPoster(token="ghp_test", repo="owner/repo")
        result = poster.post_comment(pr_number=2341, body="test")

        assert result is True