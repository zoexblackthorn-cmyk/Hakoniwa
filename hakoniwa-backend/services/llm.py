import re
import base64
from io import BytesIO
from typing import Optional
from services.settings import settings_service
from services.memory import memory_service
from memory import (
    save_conversation_message,
    get_conversation_messages,
    delete_conversations as db_delete_conversations,
)
from ennoia import ennoia


def _parse_data_url(data_url: str) -> tuple[str, bytes]:
    """解析 base64 data URL，返回 (mime_type, binary_data)"""
    match = re.match(r'data:([^;]+);base64,(.+)', data_url)
    if not match:
        raise ValueError(f"Invalid data URL: {data_url[:50]}...")
    mime_type = match.group(1)
    data = base64.b64decode(match.group(2))
    return mime_type, data


class LLMService:
    """LLM 服务 - 动态支持 Claude、Gemini 和 OpenAI 兼容"""

    async def chat(self, message: str, conversation_id: Optional[str] = None, attachments: list[str] = []) -> str:
        """发送消息并获取回复"""

        memory_service.record_message(message, role="user")

        try:
            ennoia.on_user_message(quality="casual")
        except Exception as e:
            print(f"[Ennoia] on_user_message error: {e}")

        memory_context = memory_service.get_context(current_message=message)

        try:
            inner_life_context = ennoia.get_prompt_context()
        except Exception:
            inner_life_context = ""

        llm_cfg = settings_service.settings.api.llm
        provider = llm_cfg.provider.lower()

        if provider == "claude":
            reply = await self._chat_claude(message, conversation_id, memory_context, inner_life_context, attachments)
        elif provider == "gemini":
            reply = await self._chat_gemini(message, conversation_id, memory_context, inner_life_context, attachments)
        else:
            reply = await self._chat_openai_compatible(message, conversation_id, memory_context, inner_life_context, attachments)

        memory_service.record_message(reply, role="assistant")

        return reply

    def _load_history(self, conversation_id: Optional[str]) -> list[dict]:
        """从数据库加载对话历史（跳过空消息）"""
        if not conversation_id:
            return []
        messages = get_conversation_messages(conversation_id)
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["content"] and m["content"].strip()
        ]

    # ─── Claude (Anthropic) ───
    async def _chat_claude(self, message: str, conversation_id: Optional[str] = None, memory_context: str = "", inner_life_context: str = "", attachments: list[str] = []) -> str:
        import anthropic

        llm_cfg = settings_service.settings.api.llm
        if not llm_cfg.api_key:
            raise Exception("请先在设置中配置 Claude API Key")

        kwargs = {"api_key": llm_cfg.api_key}
        if llm_cfg.base_url:
            kwargs["base_url"] = llm_cfg.base_url

        client = anthropic.Anthropic(**kwargs)
        system_prompt = settings_service.build_system_prompt(memory_context, inner_life_context)
        # 构建消息历史
        history = self._load_history(conversation_id)

        # 构建当前用户消息（含图片）
        if attachments:
            user_content = []
            for i, att in enumerate(attachments):
                try:
                    mime_type, data = _parse_data_url(att)
                    b64 = base64.b64encode(data).decode()
                    user_content.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": mime_type, "data": b64}
                    })
                except Exception as e:
                    raise ValueError(f"[Claude] 解析第 {i+1} 张图片失败: {e}")
            if message.strip():
                user_content.append({"type": "text", "text": message})
            history.append({"role": "user", "content": user_content})
        else:
            history.append({"role": "user", "content": message})

        response = client.messages.create(
            model=llm_cfg.model,
            max_tokens=2048,
            system=[
                {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}
            ],
            messages=history,
        )

        reply = response.content[0].text

        # 保存到数据库
        if conversation_id:
            save_conversation_message(
                conversation_id, "user", message,
                metadata={"attachments": attachments} if attachments else None
            )
            save_conversation_message(conversation_id, "assistant", reply)

        return reply

    # ─── Gemini (Google) ───
    async def _chat_gemini(self, message: str, conversation_id: Optional[str] = None, memory_context: str = "", inner_life_context: str = "", attachments: list[str] = []) -> str:
        import google.generativeai as genai
        from PIL import Image

        llm_cfg = settings_service.settings.api.llm
        if not llm_cfg.api_key:
            raise Exception("请先在设置中配置 Gemini API Key")

        genai.configure(api_key=llm_cfg.api_key)
        system_prompt = settings_service.build_system_prompt(memory_context)

        model = genai.GenerativeModel(
            model_name=llm_cfg.model,
            system_instruction=system_prompt,
        )

        # 加载历史并转换为 Gemini 格式
        db_history = self._load_history(conversation_id)
        gemini_history = []
        for m in db_history:
            role = "user" if m["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [m["content"]]})

        chat = model.start_chat(history=gemini_history)

        # 构建当前消息 parts（含图片）
        parts = []
        for i, att in enumerate(attachments):
            try:
                _, data = _parse_data_url(att)
                img = Image.open(BytesIO(data))
                parts.append(img)
            except Exception as e:
                raise ValueError(f"[Gemini] 解析第 {i+1} 张图片失败: {e}")
        if message.strip():
            parts.append(message)

        response = chat.send_message(parts)
        reply = response.text

        # 保存到数据库
        if conversation_id:
            save_conversation_message(
                conversation_id, "user", message,
                metadata={"attachments": attachments} if attachments else None
            )
            save_conversation_message(conversation_id, "assistant", reply)

        return reply

    # ─── OpenAI Compatible (Kimi / DeepSeek / OpenAI / etc.) ───
    async def _chat_openai_compatible(self, message: str, conversation_id: Optional[str] = None, memory_context: str = "", inner_life_context: str = "", attachments: list[str] = []) -> str:
        from openai import AsyncOpenAI

        llm_cfg = settings_service.settings.api.llm
        if not llm_cfg.api_key:
            raise Exception(f"请先在设置中配置 {llm_cfg.provider.upper()} API Key")

        client = AsyncOpenAI(
            api_key=llm_cfg.api_key,
            base_url=llm_cfg.base_url or None,
        )
        system_prompt = settings_service.build_system_prompt(memory_context, inner_life_context)
        # 构建消息历史
        history = self._load_history(conversation_id)
        if system_prompt:
            history.insert(0, {"role": "system", "content": system_prompt})

        # 构建当前用户消息（含图片）
        if attachments:
            content = []
            for i, att in enumerate(attachments):
                try:
                    content.append({"type": "image_url", "image_url": {"url": att}})
                except Exception as e:
                    raise ValueError(f"[OpenAI] 构建第 {i+1} 张图片消息失败: {e}")
            if message.strip():
                content.append({"type": "text", "text": message})
            history.append({"role": "user", "content": content})
        else:
            history.append({"role": "user", "content": message})

        create_kwargs = {
            "model": llm_cfg.model,
            "messages": history,
            "max_tokens": 2048,
        }
        # kimi-k2.5 不允许自定义 temperature,强制为 1
        if "k2.5" not in llm_cfg.model.lower():
            create_kwargs["temperature"] = 0.7

        response = await client.chat.completions.create(**create_kwargs)

        reply = response.choices[0].message.content

        # 保存到数据库
        if conversation_id:
            save_conversation_message(
                conversation_id, "user", message,
                metadata={"attachments": attachments} if attachments else None
            )
            save_conversation_message(conversation_id, "assistant", reply)

        return reply

    def clear_conversation(self, conversation_id: str) -> bool:
        db_delete_conversations([conversation_id])
        return True


# 单例
llm_service = LLMService()
