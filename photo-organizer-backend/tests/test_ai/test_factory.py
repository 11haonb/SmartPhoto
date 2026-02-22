import pytest
from unittest.mock import AsyncMock, patch

from app.ai.factory import create_provider
from app.ai.providers.local_provider import LocalProvider
from app.ai.providers.claude_provider import ClaudeProvider
from app.ai.providers.tongyi_provider import TongyiProvider
from app.ai.providers.huggingface_provider import HuggingFaceProvider


class TestAIFactory:
    def test_create_local_provider(self):
        provider = create_provider("local")
        assert isinstance(provider, LocalProvider)

    def test_create_claude_provider(self):
        provider = create_provider("claude", api_key="sk-test")
        assert isinstance(provider, ClaudeProvider)

    def test_create_tongyi_provider(self):
        provider = create_provider("tongyi", api_key="sk-test")
        assert isinstance(provider, TongyiProvider)

    def test_create_huggingface_provider(self):
        provider = create_provider("huggingface")
        assert isinstance(provider, HuggingFaceProvider)

    def test_claude_requires_api_key(self):
        with pytest.raises(ValueError, match="requires an API key"):
            create_provider("claude")

    def test_tongyi_requires_api_key(self):
        with pytest.raises(ValueError, match="requires an API key"):
            create_provider("tongyi")

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider("unknown")

    def test_custom_model(self):
        provider = create_provider("claude", api_key="sk-test", model="claude-opus-4-20250514")
        assert isinstance(provider, ClaudeProvider)
