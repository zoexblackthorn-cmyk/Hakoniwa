"""
Hakoniwa LLM Provider
支持多个 LLM 服务商：Claude、Gemini、Kimi/Moonshot、OpenAI 兼容
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai_compatible"  # claude / gemini / openai_compatible
    api_key: str = ""
    model: str = ""
    base_url: str = ""


# 预设的 provider 配置
PROVIDER_PRESETS = {
    "claude": {
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-20250514",
    },
    "gemini": {
        "base_url": None,  # Gemini 用自己的 SDK
        "default_model": "gemini-2.0-flash",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "default_model": "Qwen/Qwen2.5-7B-Instruct",
    },
}


class LLMProvider:
    """统一的 LLM 调用接口"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or self._load_from_env()
        self._client = None
    
    def _load_from_env(self) -> LLMConfig:
        """从环境变量加载配置"""
        provider = os.environ.get("LLM_PROVIDER", "kimi").lower()
        
        # 获取预设
        preset = PROVIDER_PRESETS.get(provider, {})
        
        # API key 支持多种环境变量名
        api_key = (
            os.environ.get("LLM_API_KEY") or
            os.environ.get(f"{provider.upper()}_API_KEY") or
            os.environ.get("ANTHROPIC_API_KEY") or
            os.environ.get("GOOGLE_API_KEY") or
            os.environ.get("OPENAI_API_KEY") or
            ""
        )
        
        return LLMConfig(
            provider=provider,
            api_key=api_key,
            model=os.environ.get("LLM_MODEL", preset.get("default_model", "")),
            base_url=os.environ.get("LLM_BASE_URL", preset.get("base_url", "")),
        )
    
    def chat(self, prompt: str, temperature: float = 0.3) -> str:
        """发送消息并获取回复"""
        provider = self.config.provider.lower()
        
        if provider == "claude":
            return self._chat_claude(prompt, temperature)
        elif provider == "gemini":
            return self._chat_gemini(prompt, temperature)
        else:
            # OpenAI 兼容格式（Kimi、DeepSeek、SiliconFlow、OpenAI 等）
            return self._chat_openai_compatible(prompt, temperature)
    
    def _chat_claude(self, prompt: str, temperature: float) -> str:
        """Anthropic Claude"""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.config.api_key)
        
        response = client.messages.create(
            model=self.config.model,
            max_tokens=1024,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def _chat_gemini(self, prompt: str, temperature: float) -> str:
        """Google Gemini"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.config.api_key)
        model = genai.GenerativeModel(self.config.model)
        
        response = model.generate_content(
            prompt,
            generation_config={"temperature": temperature}
        )
        
        return response.text
    
    def _chat_openai_compatible(self, prompt: str, temperature: float) -> str:
        """OpenAI 兼容格式（Kimi、DeepSeek、SiliconFlow 等）"""
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url or None,
        )
        
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        
        return response.choices[0].message.content


# 默认实例（延迟初始化）
_default_provider: Optional[LLMProvider] = None


def get_llm() -> LLMProvider:
    """获取默认 LLM provider"""
    global _default_provider
    if _default_provider is None:
        _default_provider = LLMProvider()
    return _default_provider


def configure_llm(
    provider: str = None,
    api_key: str = None,
    model: str = None,
    base_url: str = None,
):
    """配置 LLM（可在运行时调用）"""
    global _default_provider
    
    # 获取当前配置
    current = _default_provider.config if _default_provider else LLMConfig()
    
    # 新 provider
    new_provider = provider or current.provider
    preset = PROVIDER_PRESETS.get(new_provider, {})
    
    # 如果切换了 provider 且没指定 model，用新 provider 的默认 model
    if provider and provider != current.provider and not model:
        new_model = preset.get("default_model", "")
        new_base_url = preset.get("base_url", "")
    else:
        new_model = model or current.model or preset.get("default_model", "")
        new_base_url = base_url or current.base_url or preset.get("base_url", "")
    
    _default_provider = LLMProvider(LLMConfig(
        provider=new_provider,
        api_key=api_key or current.api_key,
        model=new_model,
        base_url=new_base_url,
    ))
