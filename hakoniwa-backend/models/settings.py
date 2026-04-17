from pydantic import BaseModel
from typing import Optional


class CharacterSettings(BaseModel):
    """人设卡"""
    soul: str = ""             # AI 的人设
    mask: str = ""             # AI 眼中的用户
    personalization: str = ""  # 用户喜好
    avatar_path: str = ""      # 角色头像


class LLMSettings(BaseModel):
    """LLM API 配置"""
    provider: str = "gemini"   # "claude" | "gemini"
    api_key: str = ""
    model: str = "gemini-1.5-flash"
    base_url: str = ""         # 自定义端点（留空则用官方默认）


class TTSSettings(BaseModel):
    """TTS 配置"""
    provider: str = ""
    api_key: str = ""
    voice_id: str = ""
    base_url: str = ""


class SearchSettings(BaseModel):
    """搜索 API 配置"""
    provider: str = ""
    api_key: str = ""


class ImageGenSettings(BaseModel):
    """图像生成配置"""
    provider: str = ""
    api_key: str = ""
    model: str = ""


class APISettings(BaseModel):
    """所有 API 配置集合"""
    llm: LLMSettings = LLMSettings()
    tts: TTSSettings = TTSSettings()
    search: SearchSettings = SearchSettings()
    image_gen: ImageGenSettings = ImageGenSettings()


class ThemeSettings(BaseModel):
    """主题设置"""
    dark_mode: bool = False
    skin: str = "default"


class AppSettings(BaseModel):
    """完整应用设置"""
    character: CharacterSettings = CharacterSettings()
    api: APISettings = APISettings()
    theme: ThemeSettings = ThemeSettings()
