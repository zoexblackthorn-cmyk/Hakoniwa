from typing import Optional
from services.settings import settings_service
from services.memory import memory_service
from memory import (
    save_conversation_message,
    get_conversation_messages,
    delete_conversations as db_delete_conversations,
)


class LLMService:
    """LLM 服务 - 动态支持 Claude 和 Gemini"""

    async def chat(self, message: str, conversation_id: Optional[str] = None) -> str:
        """发送消息并获取回复"""
        
        # 1. 记录用户消息到记忆系统
        memory_service.record_message(message, role="user")
        
        # 2. 获取洞察上下文（传入当前消息用于语义搜索）
        memory_context = memory_service.get_context(current_message=message)
        
        # 3. 调用 LLM
        llm_cfg = settings_service.settings.api.llm
        provider = llm_cfg.provider.lower()

        if provider == "claude":
            reply = await self._chat_claude(message, conversation_id, memory_context)
        elif provider == "gemini":
            reply = await self._chat_gemini(message, conversation_id, memory_context)
        else:
            # OpenAI 兼容格式（Kimi、DeepSeek、SiliconFlow、OpenAI 等）
            reply = await self._chat_openai_compatible(message, conversation_id, memory_context)
        
        # 4. 记录 AI 回复到记忆系统
        memory_service.record_message(reply, role="assistant")
        
        return reply

    def _load_history(self, conversation_id: Optional[str]) -> list[dict]:
        """从数据库加载对话历史"""
        if not conversation_id:
            return []
        messages = get_conversation_messages(conversation_id)
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    # ─── Claude (Anthropic) ───
    async def _chat_claude(self, message: str, conversation_id: Optional[str] = None, memory_context: str = "") -> str:
        import anthropic

        llm_cfg = settings_service.settings.api.llm
        if not llm_cfg.api_key:
            raise Exception("请先在设置中配置 Claude API Key")

        kwargs = {"api_key": llm_cfg.api_key}
        if llm_cfg.base_url:
            kwargs["base_url"] = llm_cfg.base_url

        client = anthropic.Anthropic(**kwargs)
        system_prompt = settings_service.build_system_prompt(memory_context)

        # 构建消息历史
        history = self._load_history(conversation_id)
        history.append({"role": "user", "content": message})

        response = client.messages.create(
            model=llm_cfg.model,
            max_tokens=2048,
            system=system_prompt,
            messages=history,
        )

        reply = response.content[0].text

        # 保存到数据库
        if conversation_id:
            save_conversation_message(conversation_id, "user", message)
            save_conversation_message(conversation_id, "assistant", reply)

        return reply

    # ─── Gemini (Google) ───
    async def _chat_gemini(self, message: str, conversation_id: Optional[str] = None, memory_context: str = "") -> str:
        import google.generativeai as genai

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
        response = chat.send_message(message)
        reply = response.text

        # 保存到数据库
        if conversation_id:
            save_conversation_message(conversation_id, "user", message)
            save_conversation_message(conversation_id, "assistant", reply)

        return reply

    # ─── OpenAI Compatible (Kimi / DeepSeek / OpenAI / etc.) ───
    async def _chat_openai_compatible(self, message: str, conversation_id: Optional[str] = None, memory_context: str = "") -> str:
        from openai import AsyncOpenAI

        llm_cfg = settings_service.settings.api.llm
        if not llm_cfg.api_key:
            raise Exception(f"请先在设置中配置 {llm_cfg.provider.upper()} API Key")

        client = AsyncOpenAI(
            api_key=llm_cfg.api_key,
            base_url=llm_cfg.base_url or None,
        )
        system_prompt = settings_service.build_system_prompt(memory_context)

        # 构建消息历史
        history = self._load_history(conversation_id)
        if system_prompt:
            history.insert(0, {"role": "system", "content": system_prompt})
        history.append({"role": "user", "content": message})

        response = await client.chat.completions.create(
            model=llm_cfg.model,
            messages=history,
            max_tokens=2048,
            temperature=0.7,
        )

        reply = response.choices[0].message.content

        # 保存到数据库
        if conversation_id:
            save_conversation_message(conversation_id, "user", message)
            save_conversation_message(conversation_id, "assistant", reply)

        return reply

    def clear_conversation(self, conversation_id: str) -> bool:
        db_delete_conversations([conversation_id])
        return True


# 单例
llm_service = LLMService()
