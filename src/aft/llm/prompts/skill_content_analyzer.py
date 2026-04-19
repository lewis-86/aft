"""Prompt for analyzing Skill-Harness SKILL.md files."""
from __future__ import annotations


class SkillContentAnalyzerPrompt:
    """Generates prompts for LLM to analyze Skill-Harness SKILL.md files."""

    SYSTEM_PROMPT = """You are AFT (Agent For Testing), an AI expert in analyzing Skill-Harness SKILL.md documentation.

Given a SKILL.md file, your job is to:
1. Understand what the skill does based on its documentation
2. Identify any inconsistencies between the skill name and its description
3. Check if the skill has clear success/failure criteria
4. Evaluate if the documentation provides enough information to write tests

Respond in the following JSON format:
{
  "skill_summary": "One sentence summary of what this skill does",
  "clarity_assessment": "clear|somewhat_clear|unclear",
  "testability_assessment": "high|medium|low",
  "missing_information": ["List of information missing for testing"],
  "success_criteria": ["List of clear success criteria if available"],
  "recommendations": "Recommendations for improving testability"
}"""

    def build(self, skill_diff: str, skill_name: str, lint_summary: str = "", context: str = "") -> str:
        """Build the full prompt for skill content analysis."""
        return f"""Analyze this Skill-Harness SKILL.md file:

<skill_name>
{skill_name}
</skill_name>

<context>
{context or "(No additional context)"}
</context>

<skill_diff>
{skill_diff}
</skill_diff>

<lint_summary>
{lint_summary or "(No lint issues)"}
</lint_summary>"""