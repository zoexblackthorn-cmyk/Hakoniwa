"""
时间感知工具 - 最小化 token 开销
"""
from datetime import datetime


def get_time_mode() -> str:
    """
    返回当前时间段标签，用于注入 LLM 输入。
    标签列表: deep_night, morning, day, night
    """
    hour = datetime.now().hour
    if 0 <= hour < 5:
        return "deep_night"
    elif 5 <= hour < 11:
        return "morning"
    elif 11 <= hour < 17:
        return "day"
    else:
        return "night"


def _extract_time(message: str) -> datetime | None:
    """从消息中提取时间（多层 fallback）"""
    import dateparser
    from dateparser.search import search_dates

    # 1. search_dates 处理英文混合场景
    results = search_dates(message, languages=["en", "zh"])
    if results:
        return results[-1][1]

    # 2. 逐步缩短尝试解析（英文从末尾，中文从开头）
    words = message.split()
    for i in range(len(words), 0, -1):
        sub = " ".join(words[-i:])
        parsed = dateparser.parse(sub)
        if parsed:
            return parsed

    # 3. 中文前缀逐步缩短
    chars = list(message)
    for i in range(len(chars), 0, -1):
        sub = "".join(chars[:i])
        parsed = dateparser.parse(sub, languages=["zh"])
        if parsed:
            return parsed

    # 4. 硬编码处理常见词
    msg_lower = message.lower()
    now = datetime.now()
    if "tonight" in msg_lower:
        return now.replace(hour=21, minute=0, second=0, microsecond=0)
    if "今晚" in message or "今天晚上" in message:
        return now.replace(hour=21, minute=0, second=0, microsecond=0)

    return None


def detect_schedule_intent(message: str) -> tuple[bool, str, datetime, str]:
    """
    基于规则的调度意图检测（不使用 LLM，零 token 开销）

    返回: (is_task, task_type, run_time, task_content)
    """
    # 1. 提取时间
    parsed = _extract_time(message)
    if not parsed:
        return False, "", datetime.now(), ""

    # 2. 必须是未来时间
    now = datetime.now()
    if parsed <= now:
        return False, "", now, ""

    # 3. 必须包含调度关键词
    schedule_keywords = [
        "remind", "reminder", "schedule", "notify",
        "定时", "提醒", "通知",
    ]
    msg_lower = message.lower()
    if not any(kw in msg_lower for kw in schedule_keywords):
        return False, "", now, ""

    # 4. 识别任务类型
    task_type = "generic_reminder"
    if "email" in msg_lower or "邮件" in message:
        task_type = "send_email"

    # 5. 任务内容 = 原消息（简单保留）
    task_content = message.strip()

    return True, task_type, parsed, task_content
