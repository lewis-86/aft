"""AFT LLM prompts."""
from __future__ import annotations


def json_response_format() -> str:
    """Shared JSON format directive for all AFT LLM prompts."""
    return """
Respond in JSON format:
{
  "diagnosis": "What caused the failure",
  "root_cause": "test_bug|implementation_bug|environment_issue|ambiguous",
  "fix_required": "Which side needs to change",
  "proposed_fix": "If test needs fixing, provide the corrected test code",
  "reasoning": "Why this is the correct diagnosis"
}"""
