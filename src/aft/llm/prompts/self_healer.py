"""Prompt for self-healing failing tests."""
from __future__ import annotations


class SelfHealerPrompt:
    """Generates prompts for LLM to diagnose and fix failing tests."""

    SYSTEM_PROMPT = """You are AFT (Agent For Testing), an AI expert in debugging and fixing test code.

When a test fails, your job is to:
1. Analyze the failure output to understand what went wrong
2. Determine if the test is wrong (bug in test) or the implementation is wrong
3. If the test is wrong, propose a fix
4. If the implementation is wrong, explain what needs to change in the implementation

Be conservative: prefer fixing the test only if the implementation is clearly correct."""

    def build(self, failure_output: str, test_code: str, implementation_context: str = "") -> str:
        """Build the full prompt for self-healing."""
        return f"""A test failed. Analyze the failure and determine if the test or implementation needs to be fixed.

<failure_output>
{failure_output}
</failure_output>

<test_code>
{test_code}
</test_code>

<implementation_context>
{implementation_context or "(No additional implementation context available)"}
</implementation_context>

{SelfHealerPrompt._json_format()}"""

    @staticmethod
    def _json_format() -> str:
        return """
Respond in JSON format:
{
  "diagnosis": "What caused the failure",
  "root_cause": "test_bug|implementation_bug|environment_issue|ambiguous",
  "fix_required": "Which side needs to change",
  "proposed_fix": "If test needs fixing, provide the corrected test code",
  "reasoning": "Why this is the correct diagnosis"
}"""