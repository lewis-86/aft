# src/aft/cli.py
"""AFT CLI — command-line interface for CI gate and report generation."""
from __future__ import annotations
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import click
import yaml
from pathlib import Path

from aft.alert.ci_gate import CIGate
from aft.report.generator import ReportGenerator, ReportType


def load_config() -> dict:
    """Load AFT configuration from config/default.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "default.yaml"
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


@click.group()
def cli():
    """AFT CLI — Agent For Testing command-line tools."""
    pass


@cli.command("ci-check")
@click.option("--pr", required=True, type=int, help="PR number")
@click.option("--repo", required=True, help="Repository (owner/repo)")
def ci_check_command(pr: int, repo: str):
    """Run CI quality gate check for a PR.

    Returns exit code 0 if CI passes, 1 if CI should block.
    """
    config = load_config()
    gate_config = config.get("ci_gate", {})

    gate = CIGate(config=gate_config)
    result = gate.check(pr_number=pr, repo=repo)

    click.echo(result.reason)

    if result.passed:
        sys.exit(0)
    else:
        sys.exit(1)


@cli.command("report")
@click.option("--type", "report_type", required=True,
              type=click.Choice(["daily", "weekly", "on-demand", "pr-closed"]),
              help="Type of report to generate")
@click.option("--prs", help="Comma-separated PR numbers (for on-demand)")
@click.option("--pr", "single_pr", type=int, help="Single PR number (for pr-closed)")
@click.option("--output", default="stdout",
              help="Output channels: stdout,slack,feishu (comma-separated)")
def report_command(report_type: str, prs: str, single_pr: int, output: str):
    """Generate a quality report.

    Types:
      daily       - Daily aggregation report
      weekly      - Weekly report with week-over-week comparison
      on-demand   - Report for specific PR numbers
      pr-closed   - Quality summary for a single closed PR
    """
    config = load_config()

    from aft.observability.store import ObservabilityStore
    from aft.observability.trends import TrendCalculator

    store = ObservabilityStore(data_dir=config.get("observability", {}).get("data_dir", "data"))
    trend_calc = TrendCalculator(
        coverage_warn_threshold=config.get("observability", {}).get("coverage_warn_threshold", 0.70)
    )

    gen = ReportGenerator(obs_store=store, trend_calc=trend_calc)

    rt = ReportType(report_type)

    if rt == ReportType.ON_DEMAND:
        pr_list = [int(p.strip()) for p in prs.split(",")] if prs else []
        report = gen.generate(rt, prs=pr_list)
    elif rt == ReportType.PR_CLOSED:
        if not single_pr:
            click.echo("Error: --pr required for pr-closed report", err=True)
            sys.exit(1)
        report = gen.generate(rt, pr=single_pr)
    else:
        report = gen.generate(rt)

    # Output
    if "stdout" in output:
        click.echo(f"# {report.title}")
        click.echo(report.rendered)

    channels = [c.strip() for c in output.split(",") if c.strip() not in ("stdout",)]

    if channels and not report.trend:
        click.echo("No trend data to send to channels", err=True)
        return

    if "slack" in channels and config.get("alert", {}).get("slack_webhook_url"):
        from aft.alert.channels.slack import SlackNotifier
        notifier = SlackNotifier(webhook_url=config["alert"]["slack_webhook_url"])
        pr_info = {
            "pr_number": single_pr or report.metadata.get("pr", "?"),
            "repo": config.get("observability", {}).get("repo", "?"),
            "pr_url": f"https://github.com/{config.get('observability', {}).get('repo', '?')}/pull/{single_pr or '?'}",
        }
        notifier.send(trend=report.trend, pr_info=pr_info)

    if "feishu" in channels and config.get("alert", {}).get("feishu_webhook_url"):
        from aft.alert.channels.feishu import FeishuNotifier
        notifier = FeishuNotifier(webhook_url=config["alert"]["feishu_webhook_url"])
        pr_info = {
            "pr_number": single_pr or report.metadata.get("pr", "?"),
            "repo": config.get("observability", {}).get("repo", "?"),
            "pr_url": f"https://github.com/{config.get('observability', {}).get('repo', '?')}/pull/{single_pr or '?'}",
        }
        notifier.send(trend=report.trend, pr_info=pr_info)


if __name__ == "__main__":
    cli()