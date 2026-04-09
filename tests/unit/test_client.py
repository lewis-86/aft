import pytest
from unittest.mock import patch, AsyncMock
from aft.llm.client import LLMClient, LLMResponse


class TestLLMClient:
    def test_client_initialization(self):
        client = LLMClient(provider="anthropic", model="claude-sonnet-4-20250514")
        assert client.provider == "anthropic"
        assert client.model == "claude-sonnet-4-20250514"

    def test_build_messages(self):
        client = LLMClient(provider="anthropic", model="test")
        messages = client._build_messages("hello", [{"role": "user", "content": "world"}])
        assert messages[0]["role"] == "user"
        assert "hello" in messages[0]["content"]

    @patch("aft.llm.client.Anthropic")
    def test_complete_returns_response(self, mock_anthropic):
        mock_client = AsyncMock()
        mock_response = {"content": [{"text": "test output"}]}
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        client = LLMClient(provider="anthropic", model="test")
        # This will fail - method not implemented yet