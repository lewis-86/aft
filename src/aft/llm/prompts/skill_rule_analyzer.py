"""Prompt for analyzing Skill-Harness rule.yaml files."""
from __future__ import annotations
from aft.llm.prompts import json_response_format


class SkillRuleAnalyzerPrompt:
    """Generates prompts for LLM to analyze Skill-Harness rule.yaml files."""

    SYSTEM_PROMPT = """You are AFT (Agent For Testing), an AI expert in analyzing Skill-Harness rule.yaml files.

Given a rule.yaml file, your job is to:
1. Understand the rule structure and what it tests
2. Identify potential gaps or ambiguities in the rule
3. Suggest edge cases that might not be covered
4. Evaluate if the rule is comprehensive enough for testing

Respond in the following JSON format:
{
  "rule_summary": "One sentence summary of what this rule validates",
  "coverage_assessment": "good|adequate|insufficient",
  "identified_gaps": ["List of potential gaps or missing test scenarios"],
  "suggested_edge_cases": [
    {
      "description": "Edge case description",
      "rationale": "Why this edge case matters"
    }
  ],
  "recommendations": "Overall recommendations for improving test coverage"
}"""

    def build(self, rule_diff: str, rule_id: str, context: str = "") -> str:
        """Build the full prompt for skill rule analysis."""
        return f"""Analyze this Skill-Harness rule.yaml file:

<rule_id>
{rule_id}
</rule_id>

<context>
{context or "(No additional context)"}
</context>

<rule_diff>
{rule_diff}
</rule_diff>

{json_response_format()}"""