"""
Hakoniwa 认知系统
- 判断事件重要性
- 从事件归纳洞察
- 验证/修正已有洞察
"""

import json
import os
import re
from memory import (
    write_event, query_events, 
    write_insight, query_insights, update_insight_confidence,
    merge_insights, get_evidence,
    search_insights_semantic
)
from llm_provider import get_llm

# ============ Mock 模式 ============
MOCK_MODE = os.environ.get("MOCK_MODE", "false").lower() == "true"

# ============ 认知视角配置 ============
# S/N: 0=感觉（具体事实）, 1=直觉（模式含义）
# T/F: 0=思考（逻辑分析）, 1=情感（关系感受）
PERSPECTIVE = {
    "s_n": 0.5,  # 中性默认
    "t_f": 0.5,  # 中性默认
}

def get_perspective_prompt() -> str:
    """根据 S/N 和 T/F 数值生成视角描述"""
    s_n = PERSPECTIVE["s_n"]
    t_f = PERSPECTIVE["t_f"]
    
    # 感知维度
    if s_n < 0.3:
        perception = "注重具体细节和事实，记住确切发生了什么"
    elif s_n > 0.7:
        perception = "注重模式和深层含义，理解事件背后的意义"
    else:
        perception = "平衡细节与整体，既记住事实也理解含义"
    
    # 判断维度
    if t_f < 0.3:
        judgment = "倾向分析原因和逻辑，关注事情为什么发生"
    elif t_f > 0.7:
        judgment = "倾向关注情绪和关系，关心对方的感受"
    else:
        judgment = "兼顾逻辑与情感，既分析原因也关心感受"
    
    return f"你的认知风格：{perception}，{judgment}。"


def set_perspective(s_n: float, t_f: float):
    """设置认知视角数值"""
    PERSPECTIVE["s_n"] = max(0.0, min(1.0, s_n))
    PERSPECTIVE["t_f"] = max(0.0, min(1.0, t_f))

# ============ 重要性判断 ============

def assess_importance(content: str, role: str) -> float:
    """
    快速判断一条消息的重要性（0-1）
    规则式判断，不调用 LLM，省 token
    """
    importance = 0.3  # 基线
    
    # 长度：太短的通常不重要
    if len(content) < 10:
        importance -= 0.1
    elif len(content) > 100:
        importance += 0.1
    
    # 情感信号
    emotional_markers = ["喜欢", "讨厌", "爱", "恨", "害怕", "开心", "难过", "生气", "！", "..."]
    for marker in emotional_markers:
        if marker in content:
            importance += 0.1
            break
    
    # 偏好信号
    preference_markers = ["想要", "不要", "希望", "别", "最好", "不喜欢", "喜欢"]
    for marker in preference_markers:
        if marker in content:
            importance += 0.15
            break
    
    # 事实陈述
    fact_markers = ["我是", "我叫", "我在", "我的", "住在", "工作"]
    for marker in fact_markers:
        if marker in content:
            importance += 0.15
            break
    
    # 边界信号（高重要性）
    boundary_markers = ["不许", "禁止", "别再", "不可以", "受不了"]
    for marker in boundary_markers:
        if marker in content:
            importance += 0.25
            break
    
    return min(1.0, max(0.0, importance))


# ============ 洞察归纳 ============

def mock_reflect(events: list[dict], existing_insights: list[dict]) -> dict:
    """
    Mock 模式：用规则提取洞察，不调用 API
    """
    new_insights = []
    event_ids = [e["id"] for e in events]
    
    # 只看 user 消息
    user_messages = [e for e in events if e.get("role") == "user"]
    
    for e in user_messages:
        content = e["content"]
        
        # 偏好：喜欢/不喜欢
        if "喜欢" in content or "爱" in content:
            # 提取对象
            match = re.search(r"(不喜欢|讨厌|不爱|喜欢|爱)(.{1,10})", content)
            if match:
                verb, obj = match.groups()
                obj = obj.strip("，。！？、 ")[:8]
                if "不" in verb or "讨厌" in verb:
                    new_insights.append({
                        "content": f"Zo 不喜欢{obj}",
                        "category": "preference",
                        "confidence": 0.5,
                        "source_event_ids": event_ids
                    })
                else:
                    new_insights.append({
                        "content": f"Zo 喜欢{obj}",
                        "category": "preference",
                        "confidence": 0.5,
                        "source_event_ids": event_ids
                    })
        
        # 边界：不许/禁止
        if any(kw in content for kw in ["不许", "禁止", "别再", "不要再"]):
            match = re.search(r"(不许|禁止|别再|不要再)(.{1,15})", content)
            if match:
                _, action = match.groups()
                action = action.strip("，。！？、 ")[:10]
                new_insights.append({
                    "content": f"Zo 的边界：不要{action}",
                    "category": "boundary",
                    "confidence": 0.6,
                    "source_event_ids": event_ids
                })
        
        # 事实：我是/我在/我的
        if any(kw in content for kw in ["我是", "我在", "我叫", "我住"]):
            match = re.search(r"(我是|我在|我叫|我住)(.{1,15})", content)
            if match:
                verb, fact = match.groups()
                fact = fact.strip("，。！？、 ")[:10]
                new_insights.append({
                    "content": f"Zo {verb[1:]}{fact}",
                    "category": "fact",
                    "confidence": 0.7,
                    "source_event_ids": event_ids
                })
    
    # 去重（简单按 content 去重）
    seen = set()
    unique_insights = []
    for i in new_insights:
        if i["content"] not in seen:
            seen.add(i["content"])
            unique_insights.append(i)
    
    return {
        "new_insights": unique_insights,
        "validated": [],
        "invalidated": []
    }


def reflect_on_events(events: list[dict], existing_insights: list[dict]) -> dict:
    """
    从最近的事件中归纳洞察
    返回：{new_insights, validated, invalidated}
    """
    if not events:
        return {"new_insights": [], "validated": [], "invalidated": []}
    
    # Mock 模式
    if MOCK_MODE:
        print("  [MOCK MODE] 使用规则式归纳")
        return mock_reflect(events, existing_insights)
    
    # 构建 prompt
    events_text = "\n".join([
        f"[{e['timestamp']}] {e['role']}: {e['content']}"
        for e in events
    ])
    
    existing_text = "\n".join([
        f"- {i['content']} (confidence: {i['confidence']:.1f})"
        for i in existing_insights
    ]) if existing_insights else "（暂无）"
    
    prompt = f"""{get_perspective_prompt()}

分析以下对话，提取关于用户 (Zo) 的洞察。

## 最近的对话
{events_text}

## 已有的洞察
{existing_text}

## 任务
1. 从对话中归纳出关于 Zo 的新洞察（偏好、事实、模式、边界）
2. 如果对话验证了已有洞察，指出来
3. 如果对话推翻了已有洞察，指出来

## 输出格式（JSON）
{{
    "new_insights": [
        {{"content": "洞察内容", "category": "preference/fact/pattern/boundary", "confidence": 0.5}}
    ],
    "validated": [
        {{"insight_content": "被验证的洞察", "reason": "原因"}}
    ],
    "invalidated": [
        {{"insight_content": "被推翻的洞察", "reason": "原因"}}
    ]
}}

只输出 JSON，不要其他内容。如果没有发现任何洞察，返回空数组。"""

    result_text = get_llm().chat(prompt, temperature=0.3)
    
    # 解析响应
    try:
        # 清理可能的 markdown 代码块
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]
        
        result = json.loads(result_text.strip())
        
        # 给新洞察添加来源事件 ID
        event_ids = [e["id"] for e in events]
        for insight in result.get("new_insights", []):
            insight["source_event_ids"] = event_ids
        
        return result
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        print(f"Failed to parse reflection response: {e}")
        print(f"Raw response: {result_text}")
        return {"new_insights": [], "validated": [], "invalidated": []}


# ============ 完整流程 ============

def process_message(content: str, role: str = "user") -> int:
    """
    处理一条新消息：
    1. 评估重要性
    2. 存入事件
    3. 返回 event_id
    """
    importance = assess_importance(content, role)
    event_id = write_event(
        content=content,
        type="message",
        role=role,
        importance=importance
    )
    return event_id


def run_reflection(event_limit: int = 20) -> dict:
    """
    运行反思：从最近事件归纳洞察
    """
    # 获取最近事件
    recent_events = query_events(limit=event_limit)
    
    # 获取已有洞察
    existing_insights = query_insights(min_confidence=0.3)
    
    # 调用 LLM 归纳
    result = reflect_on_events(recent_events, existing_insights)
    
    # 存储新洞察
    new_insight_ids = []
    for insight in result.get("new_insights", []):
        insight_id = write_insight(
            content=insight["content"],
            category=insight.get("category", "observation"),
            confidence=insight.get("confidence", 0.5),
            source_event_ids=insight.get("source_event_ids")
        )
        new_insight_ids.append(insight_id)
    
    # 更新被验证的洞察
    for validated in result.get("validated", []):
        # 找到对应的洞察并增加置信度
        for existing in existing_insights:
            if validated["insight_content"] in existing["content"]:
                update_insight_confidence(existing["id"], 0.1)
                break
    
    # 处理被推翻的洞察
    for invalidated in result.get("invalidated", []):
        for existing in existing_insights:
            if invalidated["insight_content"] in existing["content"]:
                update_insight_confidence(existing["id"], -0.2)
                break
    
    return {
        "new_insights": len(new_insight_ids),
        "validated": len(result.get("validated", [])),
        "invalidated": len(result.get("invalidated", [])),
        "details": result
    }


# ============ 获取上下文（给对话用）============

def get_context_for_conversation(current_message: str = "") -> str:
    """
    获取用于注入对话 context 的洞察
    
    Args:
        current_message: 当前用户消息，用于语义搜索相关洞察
    
    Returns:
        格式化的上下文字符串
    """
    insights = []

    # 如果有当前消息，先尝试语义搜索
    if current_message:
        insights = search_insights_semantic(current_message, top_k=8)

    # Fallback：语义搜索为空（无 embedding 或无匹配），按 confidence 排序
    if not insights:
        insights = query_insights(min_confidence=0.3, limit=30)
    
    if not insights:
        return ""
    
    lines = ["## 关于 Zo 的认知"]
    
    # 按类别分组
    categories = {
        "fact": "事实",
        "preference": "偏好",
        "pattern": "模式",
        "boundary": "边界"
    }
    
    for cat_key, cat_name in categories.items():
        cat_insights = [i for i in insights if i.get("category") == cat_key]
        if cat_insights:
            lines.append(f"\n### {cat_name}")
            for i in cat_insights:
                conf = "★" * int(i["confidence"] * 5)
                lines.append(f"- {i['content']} [{conf}]")
    
    # 未分类的
    other = [i for i in insights if i.get("category") not in categories]
    if other:
        lines.append("\n### 其他")
        for i in other:
            conf = "★" * int(i["confidence"] * 5)
            lines.append(f"- {i['content']} [{conf}]")
    
    return "\n".join(lines)


# ============ 认知整理 ============

def consolidate_insights() -> dict:
    """
    整理洞察：合并同类，降级证据
    调用 LLM 判断哪些洞察在说同一件事
    """
    insights = query_insights(min_confidence=0.0, include_evidence=False)
    
    if len(insights) < 2:
        return {"merged_groups": 0, "message": "洞察数量不足，无需整理"}
    
    # 构建 prompt
    insights_text = "\n".join([
        f"[ID:{i['id']}] {i['content']} (类别:{i['category']}, 置信度:{i['confidence']:.2f})"
        for i in insights
    ])
    
    prompt = f"""审视以下洞察列表，找出在说"同一件事"的洞察组。

## 当前洞察
{insights_text}

## 任务
1. 找出语义重复或高度相关的洞察组
2. 对每组，选出最本质、最精炼的那条作为"主洞察"
3. 注意主体边界：
   - "那家咖啡店难喝" 和 "咖啡难喝" 不是同一件事
   - "不喜欢香菜" 和 "在社交场合避免香菜" 是同一件事

## 输出格式（JSON）
{{
    "groups": [
        {{
            "keep_id": 1,
            "merge_ids": [2, 3],
            "reason": "这三条都在说 Zo 不喜欢香菜"
        }}
    ]
}}

如果没有需要合并的洞察，返回 {{"groups": []}}
只输出 JSON，不要其他内容。"""

    if MOCK_MODE:
        print("  [MOCK MODE] 跳过 LLM 整理")
        return {"merged_groups": 0, "message": "Mock 模式，跳过整理"}
    
    result_text = get_llm().chat(prompt, temperature=0.2)
    
    try:
        # 清理 markdown
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]
        
        result = json.loads(result_text.strip())
        
        # 执行合并
        merged_count = 0
        for group in result.get("groups", []):
            keep_id = group["keep_id"]
            merge_ids = group["merge_ids"]
            if merge_ids:
                merge_insights(keep_id, merge_ids)
                merged_count += 1
                print(f"  合并: 保留 ID:{keep_id}, 降级 {merge_ids}")
        
        return {
            "merged_groups": merged_count,
            "details": result
        }
    
    except (json.JSONDecodeError, KeyError) as e:
        print(f"整理失败: {e}")
        return {"merged_groups": 0, "error": str(e)}
