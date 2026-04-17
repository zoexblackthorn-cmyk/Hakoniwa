from typing import Optional, AsyncIterator

from services.settings import settings_service


class TTSService:
    """TTS 服务 - 支持 OpenAI 兼容 / Edge TTS"""

    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> AsyncIterator[bytes]:
        cfg = settings_service.settings.api.tts
        provider = (cfg.provider or "").lower()

        if not provider:
            raise ValueError("请先在设置中配置 TTS Provider")
        if provider == "openai":
            return await self._synthesize_openai(text, voice_id or cfg.voice_id or "alloy")
        elif provider == "edge-tts":
            return await self._synthesize_edge(text, voice_id or cfg.voice_id or "zh-CN-XiaoxiaoNeural")
        else:
            raise ValueError(f"不支持的 TTS Provider: {provider}")

    async def _synthesize_openai(self, text: str, voice: str) -> AsyncIterator[bytes]:
        from openai import AsyncOpenAI

        cfg = settings_service.settings.api.tts
        if not cfg.api_key:
            raise ValueError("请先在设置中配置 TTS API Key")

        client = AsyncOpenAI(
            api_key=cfg.api_key,
            base_url=cfg.base_url or None,
        )
        response = await client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
        )
        return response.iter_bytes()

    async def _synthesize_edge(self, text: str, voice: str) -> AsyncIterator[bytes]:
        try:
            import edge_tts
        except ImportError:
            raise ValueError("edge-tts 未安装，请执行: pip install edge-tts")

        communicate = edge_tts.Communicate(text, voice)

        async def generator():
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]

        return generator()


# 单例
tts_service = TTSService()
