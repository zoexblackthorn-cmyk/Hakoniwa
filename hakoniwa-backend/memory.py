"""
Hakoniwa 记忆系统
- events: 原始事件（对话、行为、观察）
- insights: 从事件归纳的洞察（标签、结论）
"""

import sqlite3
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

# 数据库路径（可通过环境变量配置）
DB_PATH = Path(os.environ.get("HAKONIWA_DB", Path(__file__).parent / "hakoniwa.db"))

# 写入锁（防止并发写入冲突）
_db_lock = asyncio.Lock()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    conn.executescript("""
        -- 事件表：原始记忆素材
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            type TEXT NOT NULL,           -- message/action/observation
            role TEXT,                    -- user/assistant/system
            content TEXT NOT NULL,
            importance REAL DEFAULT 0.5,  -- 0-1，影响衰减速度
            decayed INTEGER DEFAULT 0,    -- 是否已衰减（软删除）
            metadata TEXT                 -- JSON，扩展字段
        );
        
        -- 洞察表：归纳后的认知
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            content TEXT NOT NULL,        -- 洞察内容，如 "Zo不喜欢奢侈品"
            category TEXT,                -- preference/fact/pattern/boundary
            confidence REAL DEFAULT 0.5,  -- 0-1，越高越确定
            source_event_ids TEXT,        -- JSON array，来源事件
            validation_count INTEGER DEFAULT 1,  -- 被验证次数
            invalidated INTEGER DEFAULT 0, -- 是否被推翻
            parent_id INTEGER DEFAULT NULL, -- 如果是证据，指向主洞察
            processed INTEGER DEFAULT 0,   -- 是否已被 inner-life 处理
            FOREIGN KEY (parent_id) REFERENCES insights(id)
        );
        
        -- 对话表
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL UNIQUE,
            title TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        
        -- 对话消息表
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
        );
        
        -- 索引
        CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
        CREATE INDEX IF NOT EXISTS idx_events_decayed ON events(decayed);
        CREATE INDEX IF NOT EXISTS idx_insights_category ON insights(category);
        CREATE INDEX IF NOT EXISTS idx_insights_confidence ON insights(confidence);
        CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at);
        CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id ON conversation_messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_conversation_messages_timestamp ON conversation_messages(timestamp);
    """)
    conn.commit()
    conn.close()


# ============ 事件操作 ============

def write_event(
    content: str,
    type: str = "message",
    role: Optional[str] = None,
    importance: float = 0.5,
    metadata: Optional[dict] = None,
    timestamp: Optional[str] = None
) -> int:
    """写入事件，返回 event_id"""
    conn = get_db()
    ts = timestamp or datetime.now().isoformat()
    meta_json = json.dumps(metadata) if metadata else None
    
    cursor = conn.execute(
        """INSERT INTO events (timestamp, type, role, content, importance, metadata)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (ts, type, role, content, importance, meta_json)
    )
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    return event_id


def query_events(
    time_start: Optional[str] = None,
    time_end: Optional[str] = None,
    type: Optional[str] = None,
    role: Optional[str] = None,
    keyword: Optional[str] = None,
    include_decayed: bool = False,
    limit: int = 100
) -> list[dict]:
    """查询事件"""
    conn = get_db()
    
    conditions = []
    params = []
    
    if not include_decayed:
        conditions.append("decayed = 0")
    
    if time_start:
        conditions.append("timestamp >= ?")
        params.append(time_start)
    
    if time_end:
        conditions.append("timestamp <= ?")
        params.append(time_end)
    
    if type:
        conditions.append("type = ?")
        params.append(type)
    
    if role:
        conditions.append("role = ?")
        params.append(role)
    
    if keyword:
        conditions.append("content LIKE ?")
        params.append(f"%{keyword}%")
    
    where = " AND ".join(conditions) if conditions else "1=1"
    params.append(limit)
    
    rows = conn.execute(
        f"SELECT * FROM events WHERE {where} ORDER BY timestamp DESC LIMIT ?",
        params
    ).fetchall()
    
    conn.close()
    return [dict(row) for row in rows]


def decay_events(before_days: int = 7, importance_threshold: float = 0.3):
    """衰减旧的低重要性事件"""
    conn = get_db()
    cutoff = (datetime.now() - timedelta(days=before_days)).isoformat()
    
    conn.execute(
        """UPDATE events 
           SET decayed = 1 
           WHERE timestamp < ? AND importance < ? AND decayed = 0""",
        (cutoff, importance_threshold)
    )
    affected = conn.total_changes
    conn.commit()
    conn.close()
    return affected


# ============ 洞察操作 ============

def write_insight(
    content: str,
    category: str = "observation",
    confidence: float = 0.5,
    source_event_ids: Optional[list[int]] = None
) -> int:
    """写入洞察，返回 insight_id"""
    conn = get_db()
    now = datetime.now().isoformat()
    source_json = json.dumps(source_event_ids) if source_event_ids else "[]"
    
    cursor = conn.execute(
        """INSERT INTO insights (created_at, updated_at, content, category, confidence, source_event_ids)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (now, now, content, category, confidence, source_json)
    )
    conn.commit()
    insight_id = cursor.lastrowid
    conn.close()
    return insight_id


def query_insights(
    category: Optional[str] = None,
    min_confidence: float = 0.0,
    include_invalidated: bool = False,
    include_evidence: bool = False,
    limit: int = 50
) -> list[dict]:
    """查询洞察（默认只返回主洞察，不含证据）"""
    conn = get_db()
    
    conditions = ["confidence >= ?"]
    params = [min_confidence]
    
    if not include_invalidated:
        conditions.append("invalidated = 0")
    
    if not include_evidence:
        conditions.append("parent_id IS NULL")
    
    if category:
        conditions.append("category = ?")
        params.append(category)
    
    where = " AND ".join(conditions)
    params.append(limit)
    
    rows = conn.execute(
        f"SELECT * FROM insights WHERE {where} ORDER BY confidence DESC, updated_at DESC LIMIT ?",
        params
    ).fetchall()
    
    conn.close()
    return [dict(row) for row in rows]


def update_insight_confidence(insight_id: int, delta: float):
    """更新洞察置信度（验证 +，推翻 -）"""
    conn = get_db()
    now = datetime.now().isoformat()
    
    conn.execute(
        """UPDATE insights 
           SET confidence = MIN(1.0, MAX(0.0, confidence + ?)),
               validation_count = validation_count + 1,
               updated_at = ?
           WHERE id = ?""",
        (delta, now, insight_id)
    )
    conn.commit()
    conn.close()


def invalidate_insight(insight_id: int):
    """标记洞察为无效（被推翻）"""
    conn = get_db()
    now = datetime.now().isoformat()
    
    conn.execute(
        "UPDATE insights SET invalidated = 1, updated_at = ? WHERE id = ?",
        (now, insight_id)
    )
    conn.commit()
    conn.close()


def set_insight_parent(insight_id: int, parent_id: int):
    """把一条洞察降级为证据，挂到主洞察下"""
    conn = get_db()
    now = datetime.now().isoformat()
    
    conn.execute(
        "UPDATE insights SET parent_id = ?, updated_at = ? WHERE id = ?",
        (parent_id, now, insight_id)
    )
    conn.commit()
    conn.close()


def get_evidence(parent_id: int) -> list[dict]:
    """获取某条主洞察的所有证据"""
    conn = get_db()
    
    rows = conn.execute(
        "SELECT * FROM insights WHERE parent_id = ? AND invalidated = 0",
        (parent_id,)
    ).fetchall()
    
    conn.close()
    return [dict(row) for row in rows]


def merge_insights(keep_id: int, merge_ids: list[int]):
    """
    合并洞察：保留 keep_id，把 merge_ids 降级为证据
    合并后主洞察的 confidence 取最高值
    """
    conn = get_db()
    now = datetime.now().isoformat()
    
    # 获取所有相关洞察的 confidence
    all_ids = [keep_id] + merge_ids
    placeholders = ",".join("?" * len(all_ids))
    rows = conn.execute(
        f"SELECT id, confidence FROM insights WHERE id IN ({placeholders})",
        all_ids
    ).fetchall()
    
    max_confidence = max(row["confidence"] for row in rows)
    
    # 更新主洞察的 confidence
    conn.execute(
        "UPDATE insights SET confidence = ?, updated_at = ? WHERE id = ?",
        (max_confidence, now, keep_id)
    )
    
    # 把其他洞察降级为证据
    for merge_id in merge_ids:
        conn.execute(
            "UPDATE insights SET parent_id = ?, updated_at = ? WHERE id = ?",
            (keep_id, now, merge_id)
        )
    
    conn.commit()
    conn.close()
    
    return {"kept": keep_id, "merged": merge_ids, "new_confidence": max_confidence}


# ============ inner-life 接口 ============

def get_unprocessed_insights() -> list[dict]:
    """获取尚未被 inner-life 处理的洞察"""
    conn = get_db()
    
    rows = conn.execute(
        """SELECT * FROM insights 
           WHERE processed = 0 AND invalidated = 0 AND parent_id IS NULL
           ORDER BY created_at DESC"""
    ).fetchall()
    
    conn.close()
    return [dict(row) for row in rows]


def mark_insights_processed(insight_ids: list[int]):
    """标记洞察已被 inner-life 处理"""
    if not insight_ids:
        return
    
    conn = get_db()
    now = datetime.now().isoformat()
    
    placeholders = ",".join("?" * len(insight_ids))
    conn.execute(
        f"UPDATE insights SET processed = 1, updated_at = ? WHERE id IN ({placeholders})",
        [now] + insight_ids
    )
    conn.commit()
    conn.close()


# ============ 对话持久化 ============

def ensure_conversation(conversation_id: str, title: Optional[str] = None) -> None:
    """确保对话记录存在"""
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute(
        """INSERT OR IGNORE INTO conversations (conversation_id, title, created_at, updated_at)
           VALUES (?, ?, ?, ?)""",
        (conversation_id, title or "", now, now)
    )
    conn.execute(
        """UPDATE conversations SET updated_at = ? WHERE conversation_id = ?""",
        (now, conversation_id)
    )
    conn.commit()
    conn.close()


def save_conversation_message(
    conversation_id: str,
    role: str,
    content: str,
    timestamp: Optional[str] = None,
    metadata: Optional[dict] = None
) -> int:
    """保存一条对话消息，返回 message_id"""
    ensure_conversation(conversation_id)
    conn = get_db()
    ts = timestamp or datetime.now().isoformat()
    meta_json = json.dumps(metadata) if metadata else None
    
    cursor = conn.execute(
        """INSERT INTO conversation_messages (conversation_id, role, content, timestamp, metadata)
           VALUES (?, ?, ?, ?, ?)""",
        (conversation_id, role, content, ts, meta_json)
    )
    conn.commit()
    message_id = cursor.lastrowid
    conn.close()
    return message_id


def get_conversation_messages(
    conversation_id: str,
    from_time: Optional[str] = None
) -> list[dict]:
    """获取对话消息，可选从某个时间开始"""
    conn = get_db()
    
    conditions = ["conversation_id = ?"]
    params = [conversation_id]
    
    if from_time:
        conditions.append("timestamp >= ?")
        params.append(from_time)
    
    where = " AND ".join(conditions)
    
    rows = conn.execute(
        f"SELECT * FROM conversation_messages WHERE {where} ORDER BY timestamp ASC",
        params
    ).fetchall()
    
    conn.close()
    return [dict(row) for row in rows]


def get_conversations(limit: int = 100) -> list[dict]:
    """获取对话列表"""
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_conversation_dates() -> list[str]:
    """获取有聊天记录的日期列表（YYYY-MM-DD）"""
    conn = get_db()
    rows = conn.execute(
        """SELECT DISTINCT date(timestamp) as day 
           FROM conversation_messages 
           ORDER BY day DESC"""
    ).fetchall()
    conn.close()
    return [row["day"] for row in rows]


def delete_conversations(conversation_ids: list[str]) -> int:
    """批量删除对话及其消息"""
    if not conversation_ids:
        return 0
    
    conn = get_db()
    placeholders = ",".join("?" * len(conversation_ids))
    conn.execute(
        f"DELETE FROM conversations WHERE conversation_id IN ({placeholders})",
        conversation_ids
    )
    affected = conn.total_changes
    conn.commit()
    conn.close()
    return affected


# ============ 初始化 ============

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
