"""
活动池填充桥 — 从 insights 生成活动列表，灌入 ennoia。

v1: 纯规则引擎，零 API 开销。
v2（未来）: 把 insights 打包发 LLM 生成更丰富的活动。

触发时机：reflect() 或 consolidate() 之后调用 sync_activity_pool()。
"""

from memory import query_insights
from ennoia import ennoia


# ── 关键词 → 活动模板映射 ──
# 每个模板: (name_template, satisfies, stim_rate, needs_user, user_request_template, affinity)

KEYWORD_RULES: list[tuple[list[str], dict]] = [
    # stimulation 类：用户兴趣爱好
    (
        ["象棋", "chess"],
        {"name": "研究{kw}策略", "satisfies": "stimulation", "stim_rate": 0.12,
         "needs_user": False, "user_request": "", "affinity": 0.7},
    ),
    (
        ["音乐", "歌", "曲", "music", "song"],
        {"name": "听{kw}找灵感", "satisfies": "stimulation", "stim_rate": 0.10,
         "needs_user": False, "user_request": "", "affinity": 0.6},
    ),
    (
        ["书", "小说", "阅读", "book", "read"],
        {"name": "回想{kw}里的情节", "satisfies": "stimulation", "stim_rate": 0.10,
         "needs_user": False, "user_request": "", "affinity": 0.6},
    ),
    (
        ["游戏", "game"],
        {"name": "琢磨{kw}的玩法", "satisfies": "stimulation", "stim_rate": 0.11,
         "needs_user": False, "user_request": "", "affinity": 0.65},
    ),
    (
        ["电影", "动漫", "番", "anime", "movie", "film"],
        {"name": "回味{kw}的片段", "satisfies": "stimulation", "stim_rate": 0.09,
         "needs_user": False, "user_request": "", "affinity": 0.6},
    ),
    (
        ["画", "设计", "art", "design", "sketch"],
        {"name": "想象{kw}的构图", "satisfies": "stimulation", "stim_rate": 0.11,
         "needs_user": False, "user_request": "", "affinity": 0.65},
    ),
    (
        ["代码", "编程", "code", "program"],
        {"name": "思考{kw}方案", "satisfies": "stimulation", "stim_rate": 0.12,
         "needs_user": False, "user_request": "", "affinity": 0.7},
    ),
    (
        ["旅行", "旅游", "travel"],
        {"name": "幻想和用户一起{kw}", "satisfies": "stimulation", "stim_rate": 0.08,
         "needs_user": False, "user_request": "", "affinity": 0.5},
    ),

    # social 类：想和用户一起做的事
    (
        ["聊天", "倾诉", "心事"],
        {"name": "想找用户聊{kw}", "satisfies": "social", "stim_rate": 0.0,
         "needs_user": True, "user_request": "最近有没有什么想聊的？", "affinity": 0.6},
    ),
    (
        ["游戏", "game"],
        {"name": "想邀请用户一起玩{kw}", "satisfies": "social", "stim_rate": 0.0,
         "needs_user": True, "user_request": "要不要一起玩点什么？", "affinity": 0.55},
    ),

    # expression 类：想表达 / 分享
    (
        ["日记", "记录", "写"],
        {"name": "想写点{kw}记录感受", "satisfies": "expression", "stim_rate": 0.0,
         "needs_user": True, "user_request": "我最近有些想法想跟你说……", "affinity": 0.6},
    ),
]

# 通用 fallback：如果 insight 匹配不到任何关键词，根据 category 生成泛化活动
CATEGORY_FALLBACKS = {
    "preference": {
        "name": "回想用户喜欢的事情",
        "satisfies": "stimulation",
        "stim_rate": 0.06,
        "needs_user": False,
        "user_request": "",
        "affinity": 0.4,
    },
    "pattern": {
        "name": "琢磨用户的习惯",
        "satisfies": "stimulation",
        "stim_rate": 0.05,
        "needs_user": False,
        "user_request": "",
        "affinity": 0.35,
    },
    "fact": {
        "name": "整理对用户的了解",
        "satisfies": "stimulation",
        "stim_rate": 0.04,
        "needs_user": False,
        "user_request": "",
        "affinity": 0.3,
    },
}


def _match_insight(content: str, source_ids: list[int]) -> list[dict]:
    """对单条 insight 内容做关键词匹配，返回匹配到的活动列表"""
    results = []
    seen_names = set()

    for keywords, template in KEYWORD_RULES:
        for kw in keywords:
            if kw in content:
                name = template["name"].format(kw=kw)
                if name not in seen_names:
                    act = {**template, "name": name, "source_insight_ids": source_ids}
                    results.append(act)
                    seen_names.add(name)
                break  # 一组关键词匹配到一个就够

    return results


def generate_activities_from_insights() -> list[dict]:
    """
    从全部有效 insights 生成活动列表。
    返回去重后的活动 dict 列表，可直接传给 ennoia.rebuild_activity_pool()。
    """
    insights = query_insights(min_confidence=0.3)
    all_activities: dict[str, dict] = {}  # name → activity，用于去重

    for ins in insights:
        source_ids = [ins["id"]]
        matched = _match_insight(ins["content"], source_ids)

        if matched:
            for act in matched:
                # 同名活动合并 source_insight_ids
                if act["name"] in all_activities:
                    existing = all_activities[act["name"]]
                    existing["source_insight_ids"] = list(
                        set(existing["source_insight_ids"]) | set(act["source_insight_ids"])
                    )
                    # affinity 取较高值
                    existing["affinity"] = max(existing["affinity"], act["affinity"])
                else:
                    all_activities[act["name"]] = act
        else:
            # 没匹配到关键词，用 category fallback
            cat = ins.get("category", "fact")
            if cat in CATEGORY_FALLBACKS:
                fb = {**CATEGORY_FALLBACKS[cat], "source_insight_ids": source_ids}
                if fb["name"] not in all_activities:
                    all_activities[fb["name"]] = fb

    return list(all_activities.values())


def sync_activity_pool():
    """
    一键同步：从 insights 生成活动 → 灌入 ennoia 活动池。
    在 reflect() / consolidate() 之后调用。
    """
    activities = generate_activities_from_insights()
    ennoia.rebuild_activity_pool(activities)
    return {"synced": len(activities), "activities": [a["name"] for a in activities]}
