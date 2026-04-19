"""Shared utilities for CLI analyzers."""
from __future__ import annotations
import re
import json
from typing import Any


def parse_llm_json_response(content: str) -> dict[str, Any]:
    """Extract and parse JSON from LLM response content."""
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if not json_match:
        return {"error": "No JSON found in response", "raw": content}
    try:
        return json.loads(json_match.group())
    except json.JSONDecodeError:
        return {"error": "Invalid JSON", "raw": content}