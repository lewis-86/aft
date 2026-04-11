"""LLM Client for AFT."""
from __future__ import annotations
from typing import Any
import os

try:
    import anthropic
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    ANTHROPIC_AVAILABLE = False


class LLMResponse:
    """LLM response wrapper."""

    def __init__(self, content: str, raw: Any = None):
        self.content = content
        self.raw = raw


class LLMClient:
    """LLM API client supporting Anthropic and OpenAI."""

    def __init__(
        self,
        provider: str = "anthropic",
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = self._init_client()

    def _init_client(self):
        if self.provider == "anthropic" and ANTHROPIC_AVAILABLE:
            return Anthropic(api_key=self.api_key)
        raise ValueError(f"Unsupported provider: {self.provider}")

    def _build_messages(self, system: str, conversation: list[dict]) -> list[dict]:
        messages = []
        if system:
            messages.append({"role": "user", "content": f"<system>\n{system}\n</system>"})
        for msg in conversation:
            messages.append(msg)
        return messages

    def complete(
        self,
        prompt: str,
        conversation: list[dict] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        """Send a completion request to the LLM."""
        messages = self._build_messages(system or "", conversation or [])

        if self.provider == "anthropic":
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}] + messages,
            )
            content = response.content[0].text
            return LLMResponse(content=content, raw=response)

        raise ValueError(f"Unsupported provider: {self.provider}")