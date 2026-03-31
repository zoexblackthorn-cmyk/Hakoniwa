from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    id: str
    role: str = "assistant"
    content: str
    timestamp: str
    
    @classmethod
    def create(cls, content: str) -> "ChatResponse":
        """快速创建响应"""
        return cls(
            id=str(int(datetime.now().timestamp() * 1000)),
            role="assistant",
            content=content,
            timestamp=datetime.now().isoformat()
        )


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
    model: str = ""
