from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import config
from models.chat import ChatRequest, ChatResponse, HealthResponse
from models.settings import AppSettings
from services.llm import llm_service
from services.settings import settings_service
from services.model_providers import ProviderRegistry, fetch_models
from memory import (
    get_conversations,
    get_conversation_messages,
    get_conversation_dates,
    delete_conversations as db_delete_conversations,
)
import asyncio
from ennoia import ennoia

# 创建 FastAPI 应用
app = FastAPI(
    title="Hakoniwa API",
    description="箱庭 - 陪伴型 AI 后端",
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    try:
        reply = await llm_service.chat(
            message=request.message,
            conversation_id=request.conversation_id,
        )
        return ChatResponse.create(content=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


async def _tick_loop():
    """每 30 秒运行一次 ennoia.tick()"""
    while True:
        await asyncio.sleep(30)
        try:
            summary = ennoia.tick()
            # 有欲望生成或活动切换时才打日志
            if summary.get("desire_generated") or summary.get("activity_started"):
                print(f"[Ennoia] {summary}")
        except Exception as e:
            print(f"[Ennoia tick error] {e}")


@app.on_event("startup")
async def on_startup():
    global _tick_task
    _tick_task = asyncio.create_task(_tick_loop())
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
