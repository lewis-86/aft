# tests/unit/test_cli.py
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock


class TestAFTCLI:
    def test_ci_check_command_exists(self):
        """CI check command should be registered."""
        from aft.cli import cli
        assert "ci-check" in cli.commands

    def test_report_command_exists(self):
        """Report command should be registered."""
        from aft.cli import cli
        assert "report" in cli.commands

    @patch("aft.cli.CIGate")
    def test_ci_check_returns_zero_when_passed(self, MockCIGate):
        from aft.cli import ci_check_command

        mock_gate = MagicMock()
        mock_gate.check.return_value = MagicMock(passed=True, reason="CI passed")
        MockCIGate.return_value = mock_gate

        with patch("aft.cli.load_config") as mock_config:
            mock_config.return_value = {"ci_gate": {}}
            runner = CliRunner()
            result = runner.invoke(ci_check_command, ["--pr", "2341", "--repo", "tiktok/repo"])
            assert result.exit_code == 0

    @patch("aft.cli.CIGate")
    def test_ci_check_returns_one_when_blocked(self, MockCIGate):
        from aft.cli import ci_check_command

        mock_gate = MagicMock()
        mock_gate.check.return_value = MagicMock(passed=False, reason="CI blocked: coverage 65% < 70%")
        MockCIGate.return_value = mock_gate

        with patch("aft.cli.load_config") as mock_config:
            mock_config.return_value = {"ci_gate": {}}
            runner = CliRunner()
            result = runner.invoke(ci_check_command, ["--pr", "2341", "--repo", "tiktok/repo"])
            assert result.exit_code == 1
            assert "blocked" in result.output.lower()

    @patch("aft.cli.ReportGenerator")
    def test_report_command_pr_closed(self, MockReportGen):
        from aft.cli import report_command

        mock_gen = MagicMock()
        mock_report = MagicMock()
        mock_report.title = "PR #2341 Quality Summary"
        mock_report.rendered = "### Quality Trends\n| Coverage | 80.9%"
        mock_report.metadata = {"pr": 2341}
        mock_report.trend = MagicMock()
        mock_gen.generate.return_value = mock_report
        MockReportGen.return_value = mock_gen

        with patch("aft.cli.load_config") as mock_config:
            mock_config.return_value = {
                "observability": {"data_dir": "data"},
                "alert": {}
            }
            runner = CliRunner()
            result = runner.invoke(report_command, ["--type", "pr-closed", "--pr", "2341"])
            assert result.exit_code == 0
            assert "2341" in result.output

    def test_load_config_returns_dict(self):
        from aft.cli import load_config
        # Should not raise, returns dict
        config = load_config()
        assert isinstance(config, dict)