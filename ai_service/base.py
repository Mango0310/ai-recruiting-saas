from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        ...


_provider: Optional[LLMProvider] = None


def get_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        from ai_service.config_loader import get_config

        cfg = get_config()
        if not cfg.get("api_key"):
            from ai_service.providers.deepseek import MockProvider
            _provider = MockProvider()
        elif cfg["provider"] == "deepseek":
            from ai_service.providers.deepseek import DeepSeekProvider
            _provider = DeepSeekProvider(cfg["api_key"], cfg["base_url"], cfg["model"])
        elif cfg["provider"] == "qwen":
            from ai_service.providers.qwen import QwenProvider
            _provider = QwenProvider(cfg["api_key"], cfg["base_url"], cfg["model"])
        else:
            raise ValueError(f"Unknown LLM provider: {cfg['provider']}")
    return _provider


def set_provider(provider: LLMProvider):
    global _provider
    _provider = provider
