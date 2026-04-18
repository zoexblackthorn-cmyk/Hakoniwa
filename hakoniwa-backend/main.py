from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import config
from models.chat import (
    ChatRequest, ChatResponse, HealthResponse,
    TTSRequest, SearchResponse,
    RetryRequest, EditMessageRequest,
    BatchDeleteMessagesRequest,
)
from models.settings import AppSettings
from services.llm import llm_service
from services.settings import settings_service
from services.model_providers import ProviderRegistry, fetch_models
from services.tts import tts_service
from services.search import search_service
from services.scheduler_service import scheduler, start_scheduler
from services.time_aware import detect_schedule_intent
from memory import (
    get_conversations,
    get_conversation_messages,
    get_conversation_dates,
    delete_conversations as db_delete_conversations,
    get_user_profile,
    update_user_profile,
    save_conversation_message,
    get_last_assistant_message,
    update_message_content,
    delete_message_by_id,
    delete_messages_by_ids,
    clear_conversation_messages,
    search_conversation_messages,
    get_message_dates,
)
import asyncio
from ennoia import ennoia
from datetime import datetime

# 创建 FastAPI 应用
app = FastAPI(
    title="Hakoniwa API",
    description="箱庭 - 陪伴型 AI 后端",
    version="0.2.0",
)
# 模块级调试状态
_last_chat_error: dict | None = None

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════
#  System Prompt
# ════════════════════════════════════════

@app.get("/api/system-prompt")
async def get_system_prompt():
    """获取当前使用的底层 system prompt（用户设置优先，未设置则回退到默认）"""
    base = settings_service.settings.system_prompt.base.strip()
    if not base:
        base = config.BASE_SYSTEM_PROMPT
    return {"base": base}


# ════════════════════════════════════════
#  TTS
# ════════════════════════════════════════

@app.post("/api/tts")
async def tts(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")
    try:
        stream = await tts_service.synthesize(request.text, request.voice_id)
        return StreamingResponse(stream, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════
#  Search
# ════════════════════════════════════════

@app.get("/api/search", response_model=SearchResponse)
async def search(q: str = Query(..., description="搜索关键词")):
    if not q.strip():
        raise HTTPException(status_code=400, detail="搜索词不能为空")
    try:
        results = search_service.search(q)
        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════
#  健康检查
# ════════════════════════════════════════

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    s = settings_service.settings.api.llm
    return HealthResponse(status="ok", model=f"{s.provider}/{s.model}")


# ════════════════════════════════════════
#  聊天
# ════════════════════════════════════════

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    global _last_chat_error

    if not request.message.strip() and not request.attachments:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # ── 调度意图拦截（零 token，规则匹配）──
    is_task, task_type, run_time, task_content = detect_schedule_intent(request.message)
    if is_task:
        from services.task_handler import handle_task
        job_id = f"task-{datetime.now().timestamp()}-{id(request)}"
        scheduler.add_job(
            handle_task,
            "date",
            run_date=run_time,
            args=[task_type, task_content],
            id=job_id,
            replace_existing=True,
        )
        reply_text = f"已安排 {task_type}，将在 {run_time.strftime('%Y-%m-%d %H:%M')} 执行。"
        memory_service.record_message(request.message, role="user")
        try:
            ennoia.on_user_message(quality="casual")
        except Exception as e:
            print(f"[Ennoia] on_user_message error: {e}")
        if request.conversation_id:
            save_conversation_message(request.conversation_id, "user", request.message)
            save_conversation_message(request.conversation_id, "assistant", reply_text)
        return ChatResponse.create(content=reply_text)

    try:
        reply = await llm_service.chat(
            message=request.message,
            conversation_id=request.conversation_id,
            attachments=request.attachments,
        )
        # 查找刚保存的 assistant 消息的数据库 ID
        last_msg = get_last_assistant_message(request.conversation_id) if request.conversation_id else None
        resp = ChatResponse.create(content=reply)
        return {
            **resp.model_dump(),
            "db_message_id": last_msg['id'] if last_msg else None
        }
    except Exception as e:
        import traceback
        _last_chat_error = {
            "message": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat(),
        }
        print(f"[chat error] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/retry")
async def retry_chat(request: RetryRequest):
    """重试：删除最后一条 AI 回复，重新生成"""
    global _last_chat_error

    if not request.conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id 不能为空")

    try:
        reply = await llm_service.retry(conversation_id=request.conversation_id)

        last_msg = get_last_assistant_message(request.conversation_id)
        return {
            "id": str(last_msg['id']) if last_msg else str(int(datetime.now().timestamp() * 1000)),
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.now().isoformat(),
            "db_message_id": last_msg['id'] if last_msg else None,
        }
    except Exception as e:
        import traceback
        _last_chat_error = {
            "message": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat(),
        }
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/conversation/message/{message_id}")
async def edit_message(message_id: int, request: EditMessageRequest):
    """编辑一条消息的内容"""
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")

    success = update_message_content(message_id, request.content)
    if not success:
        raise HTTPException(status_code=404, detail="消息不存在")

    return {"success": True, "message_id": message_id}


@app.delete("/api/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    success = llm_service.clear_conversation(conversation_id)
    return {"success": success}


# ════════════════════════════════════════
#  对话历史
# ════════════════════════════════════════

@app.get("/api/conversations")
async def list_conversations():
    """获取对话列表"""
    conversations = get_conversations()
    return {"conversations": conversations}


@app.get("/api/conversation/{conversation_id}/messages")
async def get_messages(conversation_id: str, from_time: Optional[str] = None):
    """获取对话消息，可选从某个时间开始"""
    messages = get_conversation_messages(conversation_id, from_time)
    return {"messages": messages}


@app.get("/api/conversation/dates")
async def list_conversation_dates():
    """获取有聊天记录的日期列表"""
    dates = get_conversation_dates()
    return {"dates": dates}


@app.delete("/api/conversations")
async def delete_conversations(body: dict):
    """批量删除对话"""
    ids = body.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")
    affected = db_delete_conversations(ids)
    return {"success": True, "deleted": affected}


@app.delete("/api/message/{message_id}")
async def delete_message(message_id: int):
    """删除单条消息"""
    success = delete_message_by_id(message_id)
    if not success:
        raise HTTPException(status_code=404, detail="消息不存在")
    return {"success": True}


@app.delete("/api/messages")
async def batch_delete_messages(request: BatchDeleteMessagesRequest):
    """批量删除消息"""
    if not request.ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")
    deleted = delete_messages_by_ids(request.ids)
    return {"success": True, "deleted": deleted}


@app.delete("/api/conversation/{conversation_id}/messages")
async def clear_messages_endpoint(conversation_id: str):
    """清空某对话的所有消息"""
    deleted = clear_conversation_messages(conversation_id)
    return {"success": True, "deleted": deleted}


@app.get("/api/conversation/{conversation_id}/search")
async def search_messages(
    conversation_id: str,
    keyword: Optional[str] = Query(None, description="关键词"),
    message_type: Optional[str] = Query(None, description="消息类型: text/image/file/link"),
    date: Optional[str] = Query(None, description="日期: YYYY-MM-DD")
):
    """搜索对话消息"""
    results = search_conversation_messages(conversation_id, keyword, message_type, date)
    return {"messages": results}


@app.get("/api/conversation/{conversation_id}/dates")
async def list_conversation_message_dates(conversation_id: str):
    """获取某对话有消息的日期列表"""
    dates = get_message_dates(conversation_id)
    return {"dates": dates}


# ════════════════════════════════════════
#  设置
# ════════════════════════════════════════

@app.get("/api/settings")
async def get_settings():
    """获取全部设置"""
    return settings_service.get().model_dump()


@app.put("/api/settings")
async def update_settings(body: dict):
    """更新设置（支持部分更新）"""
    try:
        updated = settings_service.update(body)
        return updated.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/settings/models")
async def get_models(provider: str = Query(..., description="claude / gemini / openai / ...")):
    """动态拉取指定 provider 的可用模型列表"""
    provider = provider.lower()

    # 从当前设置中读取对应 API Key 和 Base URL
    llm_cfg = settings_service.settings.api.llm
    api_key = llm_cfg.api_key
    base_url = llm_cfg.base_url or None

    # 如果查询的 provider 与当前设置不一致，且没有通用 key，则返回空列表
    registry = ProviderRegistry()
    p = registry.get(provider)
    if not p:
        raise HTTPException(
            status_code=400,
            detail=f"未知 provider: {provider}。支持的列表: {registry.supported_providers()}"
        )

    try:
        models = await fetch_models(provider, api_key, base_url)
        return {"models": models}
    except Exception as e:
        # 动态拉取失败时返回空列表，避免前端崩溃
        print(f"拉取 {provider} 模型列表失败: {e}")
        return {"models": []}


# ════════════════════════════════════════
#  记忆系统
# ════════════════════════════════════════

from services.memory import memory_service


@app.get("/api/memory/insights")
async def get_insights(min_confidence: float = 0.3):
    """获取洞察列表"""
    insights = memory_service.get_insights(min_confidence)
    return {"insights": insights}


@app.get("/api/memory/context")
async def get_memory_context():
    """获取记忆上下文（用于调试）"""
    context = memory_service.get_context()
    return {"context": context}


@app.post("/api/memory/reflect")
async def run_reflect(event_limit: int = 20):
    """手动触发反思"""
    result = memory_service.reflect(event_limit)
    # 反思产生新 insights 后，同步活动池
    from services.activity_bridge import sync_activity_pool
    try:
        sync_activity_pool()
    except Exception as e:
        print(f"[ActivityBridge] sync error: {e}")
    return result


@app.post("/api/memory/consolidate")
async def run_consolidate():
    """手动触发洞察整理"""
    result = memory_service.consolidate()
    return result


@app.get("/api/memory/perspective")
async def get_perspective():
    """获取认知视角"""
    return memory_service.get_perspective()


@app.put("/api/memory/perspective")
async def set_perspective(s_n: float, t_f: float):
    """设置认知视角"""
    memory_service.set_perspective(s_n, t_f)
    return memory_service.get_perspective()

# ════════════════════════════════════════
#  Ennoia (Inner Life)
# ════════════════════════════════════════

_tick_task: asyncio.Task | None = None
_tick_count: int = 0


async def _tick_loop():
    """每 30 秒运行一次 ennoia.tick()，每 100 次自动 reflect"""
    global _tick_count
    while True:
        await asyncio.sleep(30)
        _tick_count += 1

        try:
            summary = ennoia.tick()
            # 有欲望生成或活动切换时才打日志
            if summary.get("desire_generated") or summary.get("activity_started"):
                print(f"[Ennoia] {summary}")
        except Exception as e:
            print(f"[Ennoia tick error] {e}")

        # 每 100 个 tick（约 50 分钟）自动反思一次
        if _tick_count % 100 == 0:
            try:
                from services.memory import memory_service
                result = memory_service.reflect()
                from services.activity_bridge import sync_activity_pool
                sync_activity_pool()
                print(f"[Auto-reflect] tick #{_tick_count}: {result}")
            except Exception as e:
                print(f"[Auto-reflect error] tick #{_tick_count}: {e}")


@app.on_event("startup")
async def on_startup():
    global _tick_task
    _tick_task = asyncio.create_task(_tick_loop())
    start_scheduler()
    print("🧠 Ennoia tick scheduler started (every 30s)")


@app.on_event("shutdown")
async def on_shutdown():
    global _tick_task
    if _tick_task:
        _tick_task.cancel()
        try:
            await _tick_task
        except asyncio.CancelledError:
            pass
    print("🧠 Ennoia tick scheduler stopped")


@app.get("/api/ennoia/state")
async def ennoia_state():
    """当前内在状态快照"""
    return {
        "needs": ennoia.needs.to_dict(),
        "mood": ennoia.mood.to_dict(),
        "personality": ennoia.personality.to_dict(),
        "current_activity": ennoia.current_activity.to_dict(),
        "unshared_experiences": ennoia.unshared_experiences,
        "closeness": ennoia.closeness,
        "last_user_interaction_at": ennoia.last_user_interaction_at,
        "last_initiative_at": ennoia.last_initiative_at,
    }


@app.get("/api/ennoia/desires")
async def ennoia_desires():
    """Pending 欲望列表"""
    from memory import get_db
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM desires WHERE status IN ('pending', 'active') ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return {"desires": [dict(r) for r in rows]}


@app.get("/api/ennoia/activity-pool")
async def ennoia_activity_pool():
    """当前活动池"""
    from memory import get_db
    conn = get_db()
    rows = conn.execute("SELECT * FROM activity_pool ORDER BY affinity DESC").fetchall()
    conn.close()
    return {"activities": [dict(r) for r in rows]}


@app.post("/api/ennoia/tick")
async def ennoia_manual_tick():
    """手动触发一次 tick（调试用）"""
    summary = ennoia.tick()
    return summary
@app.post("/api/ennoia/sync-activity-pool")
async def ennoia_sync_activity_pool():
    """从 insights 重新生成活动池（调试用）"""
    from services.activity_bridge import sync_activity_pool
    try:
        result = sync_activity_pool()
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════
#  用户档案
# ════════════════════════════════════════

@app.get("/api/user")
async def api_get_user():
    return get_user_profile()


@app.put("/api/user")
async def api_update_user(body: dict):
    try:
        return update_user_profile(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ════════════════════════════════════════
#  Todo 列表
# ════════════════════════════════════════

from memory import get_todos, add_todo, delete_todo, toggle_todo


@app.get("/api/todos")
async def api_get_todos():
    return {"todos": get_todos()}


@app.post("/api/todos")
async def api_create_todo(body: dict):
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    return add_todo(content)


@app.delete("/api/todos/{todo_id}")
async def api_delete_todo(todo_id: int):
    success = delete_todo(todo_id)
    return {"success": success}


@app.patch("/api/todos/{todo_id}")
async def api_toggle_todo(todo_id: int, body: dict):
    completed = bool(body.get("completed", False))
    return toggle_todo(todo_id, completed)


# ════════════════════════════════════════
#  Debug
# ════════════════════════════════════════

@app.get("/api/debug/last-chat-error")
async def debug_last_chat_error():
    """最近一次 /api/chat 异常（内存，重启丢失）"""
    return {"error": _last_chat_error}


@app.post("/api/debug/clear-chat-error")
async def debug_clear_chat_error():
    global _last_chat_error
    _last_chat_error = None
    return {"success": True}


@app.get("/api/ennoia/initiative")
async def ennoia_check_initiative():
    """检查是否应该主动找用户"""
    result = ennoia.should_initiate()
    if result:
        return {"should_send": True, "desire": result}
    return {"should_send": False}
# ════════════════════════════════════════
#  启动
# ════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    s = settings_service.settings.api.llm
    print(f"🏠 Hakoniwa Backend starting...")
    print(f"📍 http://{config.HOST}:{config.PORT}")
    print(f"🤖 LLM: {s.provider}/{s.model}")
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)
