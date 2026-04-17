"""
动态模型列表提供者
支持 Gemini、Claude、OpenAI 及所有 OpenAI 兼容接口
"""

from abc import ABC, abstractmethod
from typing import Optional
import requests


class ModelProvider(ABC):
    """模型提供者抽象基类"""

    @abstractmethod
    def list_models(self, api_key: str, base_url: Optional[str] = None) -> list[str]:
        """返回可用模型 ID 列表"""
        pass


class GeminiProvider(ModelProvider):
    """Google Gemini"""

    def list_models(self, api_key: str, base_url: Optional[str] = None) -> list[str]:
        import google.generativeai as genai

        if api_key:
            genai.configure(api_key=api_key)

        models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                name = m.name
                if name.startswith("models/"):
                    name = name[7:]
                models.append(name)
        return models


class ClaudeProvider(ModelProvider):
    """Anthropic Claude"""

    def list_models(self, api_key: str, base_url: Optional[str] = None) -> list[str]:
        url = (base_url or "https://api.anthropic.com").rstrip("/") + "/v1/models"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return [item["id"] for item in data.get("data", [])]


class OpenAIProvider(ModelProvider):
    """OpenAI / Azure OpenAI"""

    def list_models(self, api_key: str, base_url: Optional[str] = None) -> list[str]:
        base = (base_url or "https://api.openai.com").rstrip("/")
        if base.endswith("/v1"):
            url = base + "/models"
        else:
            url = base + "/v1/models"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return [item["id"] for item in data.get("data", [])]


class OpenAICompatibleProvider(ModelProvider):
    """
    通用 OpenAI 兼容接口
    适用于 OneAPI、Ollama、vLLM、LocalAI 等
    """

    def list_models(self, api_key: str, base_url: Optional[str] = None) -> list[str]:
        if not base_url:
            raise ValueError("OpenAI 兼容接口必须配置 Base URL")
        base = base_url.rstrip("/")
        # 如果 base_url 已经以 /v1 结尾，直接拼 /models；否则加 /v1/models
        if base.endswith("/v1"):
            url = base + "/models"
        else:
            url = base + "/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return [item["id"] for item in data.get("data", [])]
        resp.raise_for_status()
        data = resp.json()
        return [item["id"] for item in data.get("data", [])]


class ProviderRegistry:
    """提供者注册中心"""

    _providers: dict[str, ModelProvider] = {
        "gemini": GeminiProvider(),
        "claude": ClaudeProvider(),
        "openai": OpenAIProvider(),
        "azure": OpenAIProvider(),
        "openai-compatible": OpenAICompatibleProvider(),
        # OpenAI 兼容的国内服务
        "kimi": OpenAICompatibleProvider(),
        "deepseek": OpenAICompatibleProvider(),
        "siliconflow": OpenAICompatibleProvider(),
    }

    @classmethod
    def get(cls, provider: str) -> Optional[ModelProvider]:
        return cls._providers.get(provider.lower())

    @classmethod
    def register(cls, name: str, provider: ModelProvider):
        cls._providers[name.lower()] = provider

    @classmethod
    def supported_providers(cls) -> list[str]:
        return list(cls._providers.keys())


# 便捷函数
async def fetch_models(provider: str, api_key: str, base_url: Optional[str] = None) -> list[str]:
    """根据 provider 名称动态拉取模型列表"""
    p = ProviderRegistry.get(provider)
    if not p:
        raise ValueError(f"不支持的 provider: {provider}。支持的列表: {ProviderRegistry.supported_providers()}")
    return p.list_models(api_key, base_url)
