"""Prompt for analyzing policy rule changes."""
from __future__ import annotations

from aft.llm.prompts.self_healer import SelfHealerPrompt


class RuleAnalyzerPrompt:
    """Generates prompts for LLM to analyze policy rule changes."""

    SYSTEM_PROMPT = """You are AFT (Agent For Testing), an AI expert in content safety policy analysis.

Given a diff of policy rule changes, your job is to:
1. Understand what the rule change does semantically
2. Identify potential risks: does this rule change increase false positives (over-blocking) or false negatives (under-blocking)?
3. Suggest what test cases should be added to verify this change

Respond in the following JSON format:
{
  "semantic_summary": "One sentence summary of what changed",
  "risk_assessment": "low|medium|high",
  "risk_reasoning": "Why this change may cause issues",
  "suggested_test_cases": [
    {
      "description": "What this test validates",
      "input": "Sample input content",
      "expected_outcome": "Expected policy decision",
      "rationale": "Why this case matters"
    }
  ]
}"""

    def build(self, rule_diff: str, context: str = "") -> str:
        """Build the full prompt for rule analysis."""
        return f"""Analyze this policy rule change:

<context>
{context}
</context>

<diff>
{rule_diff}
</diff>

{SelfHealerPrompt._json_format()}"""