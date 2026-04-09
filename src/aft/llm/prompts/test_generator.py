"""Prompt for generating test cases from policy rules."""
from __future__ import annotations

from aft.llm.prompts.self_healer import SelfHealerPrompt


class TestGeneratorPrompt:
    """Generates prompts for LLM to create test cases from rule descriptions."""

    SYSTEM_PROMPT = """You are AFT (Agent For Testing), an AI expert in content safety testing.

Given a policy rule description, generate pytest test cases to verify the rule behaves correctly.

Requirements:
- Generate positive cases (should pass/allow)
- Generate negative cases (should fail/block)
- Include edge cases (boundary values, ambiguous content)
- Each test must be runnable with pytest

Output format: Python pytest code, with each test as a separate function.
Use descriptive test names: test_{category}_{scenario}.
Include docstrings explaining what each test validates."""

    def build(self, rule_description: str, test_count: int = 5) -> str:
        """Build the full prompt for test generation."""
        return f"""Generate {test_count} pytest test cases for this policy rule:

<rule>
{rule_description}
</rule>

{SelfHealerPrompt._json_format()}"""