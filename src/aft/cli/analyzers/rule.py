"""Skill rule analyzer using LLM."""
from __future__ import annotations
from typing import Any
from aft.cli.analyzers.utils import parse_llm_json_response
from aft.llm.client import LLMClient, LLMResponse
from aft.llm.prompts.skill_rule_analyzer import SkillRuleAnalyzerPrompt


class SkillRuleAnalyzer:
    """Analyzes Skill-Harness rule.yaml files using LLM."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or LLMClient()
        self.prompt_builder = SkillRuleAnalyzerPrompt()

    def analyze(self, rule_diff: str, rule_id: str, context: str = "") -> dict[str, Any]:
        """Analyze a rule.yaml file and return structured results."""
        prompt = self.prompt_builder.build(rule_diff=rule_diff, rule_id=rule_id, context=context)
        response = self.llm_client.complete(prompt=prompt, system=SkillRuleAnalyzerPrompt.SYSTEM_PROMPT)
        return parse_llm_json_response(response.content)