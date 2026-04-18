from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    conversation_id: Optional[str] = None
    attachments: list[str] = []


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


class TTSRequest(BaseModel):
    """TTS 请求"""
    text: str
    voice_id: Optional[str] = None


class SearchResultItem(BaseModel):
    """搜索结果条目"""
    title: str
    url: str
    description: str


class SearchResponse(BaseModel):
    """搜索响应"""
    results: list[SearchResultItem]


class RetryRequest(BaseModel):
    """重试请求"""
    conversation_id: str


class EditMessageRequest(BaseModel):
    """编辑消息请求"""
    content: str


class BatchDeleteMessagesRequest(BaseModel):
    """批量删除消息请求"""
    ids: list[int]
