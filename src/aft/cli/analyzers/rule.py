"""Skill rule analyzer using LLM."""
from __future__ import annotations
from typing import Any
from aft.llm.client import LLMClient, LLMResponse
from aft.llm.prompts.skill_rule_analyzer import SkillRuleAnalyzerPrompt


class SkillRuleAnalyzer:
    """Analyzes Skill-Harness rule.yaml files using LLM."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or LLMClient()
        self.prompt_builder = SkillRuleAnalyzerPrompt()

    def analyze(self, rule_content: str, context: str = "") -> dict[str, Any]:
        """Analyze a rule.yaml file and return structured results."""
        prompt = self.prompt_builder.build(rule_content=rule_content, context=context)
        response = self.llm_client.complete(prompt=prompt, system=SkillRuleAnalyzerPrompt.SYSTEM_PROMPT)
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