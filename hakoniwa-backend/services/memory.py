"""
记忆服务 - 封装记忆系统的调用
"""

from memory import (
    init_db, write_event, query_events, decay_events,
    query_insights, get_unprocessed_insights, mark_insights_processed
)
from cognition import (
    process_message, run_reflection, get_context_for_conversation,
    consolidate_insights, set_perspective, PERSPECTIVE
)


class MemoryService:
    """记忆服务"""
    
    def __init__(self):
        self._initialized = False
    
    def _ensure_init(self):
        if not self._initialized:
            init_db()
            self._initialized = True
    
    # ============ 事件操作 ============
    
    def record_message(self, content: str, role: str = "user") -> int:
        """记录一条消息，返回 event_id"""
        self._ensure_init()
        return process_message(content, role)
    
    def get_recent_events(self, limit: int = 20) -> list[dict]:
        """获取最近事件"""
        self._ensure_init()
        return query_events(limit=limit)
    
    # ============ 洞察操作 ============
    
    def get_insights(self, min_confidence: float = 0.3) -> list[dict]:
        """获取洞察"""
        self._ensure_init()
        return query_insights(min_confidence=min_confidence)
    
    def get_context(self, current_message: str = "") -> str:
        """获取用于注入 system prompt 的上下文"""
        self._ensure_init()
        return get_context_for_conversation(current_message=current_message)
    
    # ============ 反思操作 ============
    
    def reflect(self, event_limit: int = 20) -> dict:
        """运行反思，归纳洞察"""
        self._ensure_init()
        return run_reflection(event_limit)
    
    def consolidate(self) -> dict:
        """整理洞察，合并同类"""
        self._ensure_init()
        return consolidate_insights()
    
    # ============ 认知视角 ============
    
    def set_perspective(self, s_n: float, t_f: float):
        """设置认知视角"""
        set_perspective(s_n, t_f)
    
    def get_perspective(self) -> dict:
        """获取当前认知视角"""
        return PERSPECTIVE.copy()
    
    # ============ inner-life 接口 ============
    
    def get_unprocessed_insights(self) -> list[dict]:
        """获取未被 inner-life 处理的洞察"""
        self._ensure_init()
        return get_unprocessed_insights()
    
    def mark_processed(self, insight_ids: list[int]):
        """标记洞察已处理"""
        self._ensure_init()
        mark_insights_processed(insight_ids)
    
    # ============ 维护操作 ============
    
    def decay(self, before_days: int = 7, importance_threshold: float = 0.3) -> int:
        """衰减旧事件"""
        self._ensure_init()
        return decay_events(before_days, importance_threshold)


# 单例
memory_service = MemoryService()
