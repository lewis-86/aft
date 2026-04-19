"""Skill content analyzer using LLM."""
from __future__ import annotations
from typing import Any
from aft.cli.parsers.lint import LintReport
from aft.llm.client import LLMClient, LLMResponse
from aft.llm.prompts.skill_content_analyzer import SkillContentAnalyzerPrompt


class SkillContentAnalyzer:
    """Analyzes Skill-Harness SKILL.md files using LLM."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or LLMClient()
        self.prompt_builder = SkillContentAnalyzerPrompt()

    def analyze(self, skill_diff: str, lint_report: LintReport, context: str = "") -> dict[str, Any]:
        """Analyze a SKILL.md file and return structured results.

        Args:
            skill_diff: The diff/content of the SKILL.md file.
            lint_report: LintReport containing lint results for the skill.
            context: Optional additional context.
        """
        skill_name = lint_report.skill_name or lint_report.skill_path
        blocker_msgs = [f"{b.rule_id}: {b.message}" for b in lint_report.blockers]
        warning_msgs = [f"{w.rule_id}: {w.message}" for w in lint_report.warnings]
        hint_msgs = [f"{h.rule_id}: {h.message}" for h in lint_report.hints]
        lint_summary_parts = []
        if blocker_msgs:
            lint_summary_parts.append(f"Blockers: {'; '.join(blocker_msgs)}")
        if warning_msgs:
            lint_summary_parts.append(f"Warnings: {'; '.join(warning_msgs)}")
        if hint_msgs:
            lint_summary_parts.append(f"Hints: {'; '.join(hint_msgs)}")
        lint_summary = "; ".join(lint_summary_parts) if lint_summary_parts else ""

        prompt = self.prompt_builder.build(
            skill_diff=skill_diff,
            skill_name=skill_name,
            lint_summary=lint_summary,
            context=context,
        )
        response = self.llm_client.complete(prompt=prompt, system=SkillContentAnalyzerPrompt.SYSTEM_PROMPT)
        return self._parse_response(response)

    def _parse_response(self, response: LLMResponse) -> dict[str, Any]:
        """Parse LLM response into structured dict."""
        import json
        try:
            # Try to extract JSON from the response
            content = response.content.strip()
            if "```json" in content:
                # Extract from markdown code block
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response", "raw": response.content}