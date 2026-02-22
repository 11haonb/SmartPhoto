from app.ai.base import AIProvider
from app.ai.providers.local_provider import LocalProvider
from app.ai.providers.claude_provider import ClaudeProvider
from app.ai.providers.tongyi_provider import TongyiProvider
from app.ai.providers.huggingface_provider import HuggingFaceProvider


def create_provider(
    provider_name: str,
    api_key: str | None = None,
    model: str | None = None,
) -> AIProvider:
    """Factory function to create AI provider instances."""
    match provider_name:
        case "local":
            return LocalProvider()
        case "claude":
            if not api_key:
                raise ValueError("Claude provider requires an API key")
            return ClaudeProvider(
                api_key=api_key,
                model=model or "claude-sonnet-4-20250514",
            )
        case "tongyi":
            if not api_key:
                raise ValueError("Tongyi provider requires an API key")
            return TongyiProvider(
                api_key=api_key,
                model=model or "qwen-vl-max",
            )
        case "huggingface":
            return HuggingFaceProvider(
                api_key=api_key,
                model=model or "Salesforce/blip2-opt-2.7b",
            )
        case _:
            raise ValueError(f"Unknown provider: {provider_name}")
