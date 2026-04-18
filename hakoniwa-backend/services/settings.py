import json
import os
from models.settings import AppSettings
import config

BUBBLE_SPLIT_INSTRUCTION = """

## 回复格式（Message Formatting）
你在即时通讯软件中回复。像真人一样，把回复拆成自然的消息气泡。
用一行只包含 --- 的分隔符来标记气泡边界。

规则：
- 1-3 个气泡是最常见的，4 个以上应该很少出现
- 短回复（一句话）不需要分隔符
- 永远不要把 --- 当作可见内容展示
- 根据你的情绪和语境自然断句，不要机械分割

示例：
输入: 你在干嘛
输出: 在看书
---
你呢

输入: 晚饭吃了吗
输出: 吃了
---
你呢，别告诉我又忘了"""

# Provider 预设配置
PROVIDER_PRESETS = {
    "claude": {"base_url": "", "default_model": "claude-sonnet-4-20250514"},
    "gemini": {"base_url": "", "default_model": "gemini-2.0-flash"},
    "kimi": {"base_url": "https://api.moonshot.cn/v1", "default_model": "moonshot-v1-8k"},
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "default_model": "deepseek-chat"},
    "openai": {"base_url": "https://api.openai.com/v1", "default_model": "gpt-4o-mini"},
    "siliconflow": {"base_url": "https://api.siliconflow.cn/v1", "default_model": "Qwen/Qwen2.5-7B-Instruct"},
}


class SettingsService:
    """设置持久化服务 - JSON 文件存储"""

    def __init__(self):
        self._settings: AppSettings | None = None

    @property
    def settings(self) -> AppSettings:
        if self._settings is None:
            self._settings = self._load()
        return self._settings

    def _load(self) -> AppSettings:
        """从文件加载设置，环境变量可覆盖 LLM 配置"""
        if os.path.exists(config.SETTINGS_FILE):
            try:
                with open(config.SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"⚠️ 读取设置失败，使用默认值: {e}")
                data = {}
        else:
            data = {}
        
        # 环境变量覆盖 LLM 配置
        if "api" not in data:
            data["api"] = {}
        if "llm" not in data["api"]:
            data["api"]["llm"] = {}
        
        llm = data["api"]["llm"]
        old_provider = llm.get("provider", "gemini").lower()
        
        if os.environ.get("LLM_PROVIDER"):
            llm["provider"] = os.environ.get("LLM_PROVIDER")
        if os.environ.get("LLM_API_KEY"):
            llm["api_key"] = os.environ.get("LLM_API_KEY")
        if os.environ.get("LLM_MODEL"):
            llm["model"] = os.environ.get("LLM_MODEL")
        if os.environ.get("LLM_BASE_URL"):
            llm["base_url"] = os.environ.get("LLM_BASE_URL")
        
        # 兼容 provider 特定的 API Key 环境变量
        provider = llm.get("provider", "gemini").lower()
        env_key = os.environ.get(f"{provider.upper()}_API_KEY")
        if env_key:
            llm["api_key"] = env_key
        
        # 如果切换了 provider 且没指定 model/base_url，应用预设
        preset = PROVIDER_PRESETS.get(provider, {})
        if provider != old_provider or not llm.get("model"):
            if not os.environ.get("LLM_MODEL") and not llm.get("model"):
                llm["model"] = preset.get("default_model", "")
        if provider != old_provider or not llm.get("base_url"):
            if not os.environ.get("LLM_BASE_URL") and not llm.get("base_url"):
                llm["base_url"] = preset.get("base_url", "")
        
        return AppSettings(**data)

    def _save(self):
        """保存设置到文件"""
        with open(config.SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._settings.model_dump(), f, ensure_ascii=False, indent=2)

    def get(self) -> AppSettings:
        return self.settings

    def update(self, partial: dict) -> AppSettings:
        """部分更新设置（深合并）

        特殊逻辑：如果 provider 变了但 model 没一起给，自动应用新 provider 的 preset
        """
        current = self.settings.model_dump()

        # 检测 provider 切换
        old_provider = current.get("api", {}).get("llm", {}).get("provider", "").lower()
        new_llm = partial.get("api", {}).get("llm", {}) if partial else {}
        new_provider = new_llm.get("provider", "").lower() if new_llm else ""

        provider_changed = new_provider and new_provider != old_provider

        self._deep_merge(current, partial)

        # provider 变了，但 model / base_url 没明确给出 → 应用 preset
        if provider_changed:
            preset = PROVIDER_PRESETS.get(new_provider, {})
            if "model" not in new_llm or not new_llm.get("model"):
                current["api"]["llm"]["model"] = preset.get("default_model", "")
            if "base_url" not in new_llm or not new_llm.get("base_url"):
                current["api"]["llm"]["base_url"] = preset.get("base_url", "")

        self._settings = AppSettings(**current)
        self._save()
        return self._settings

    def build_system_prompt(self, memory_context: str = "", inner_life_context: str = "") -> str:
        """组装最终 system prompt：底层 + soul + mask + personalization + memory + inner life"""
        s = self.settings.character
        base_prompt = self.settings.system_prompt.base.strip()
        if not base_prompt:
            base_prompt = config.BASE_SYSTEM_PROMPT
        parts = [base_prompt]

        if s.soul.strip():
            parts.append(f"\n\n## 你是谁（Soul）\n{s.soul}")
        if s.mask.strip():
            parts.append(f"\n\n## 你的用户（Mask）\n{s.mask}")
        if s.personalization.strip():
            parts.append(f"\n\n## 用户偏好（Personalization）\n{s.personalization}")
        
        # 新增：注入用户信息
        from memory import get_user_profile
        user = get_user_profile()
        user_section = ""
        if any([user['name'], user['mask'], user['profession'], user['personalization']]):
            uparts = ["【与你对话的人】"]
            if user['name']: uparts.append(f"- 名字：{user['name']}")
            if user['profession']: uparts.append(f"- 职业：{user['profession']}")
            if user['mask']: uparts.append(f"- 她希望在你面前呈现的样子：\n{user['mask']}")
            if user['personalization']: uparts.append(f"- 她希望你如何对待她：\n{user['personalization']}")
            user_section = "\n".join(uparts) + "\n\n"
        parts.append(user_section)

        # 跨对话桥梁：注入最近的用户消息摘要（不依赖 conversation_id）
        try:
            from memory import query_events
            recent_events = query_events(role="user", limit=10)
            if recent_events:
                recent_lines = []
                for e in recent_events:
                    # 截取前80字符，避免过长
                    text = e['content'][:80].replace('\n', ' ')
                    recent_lines.append(f"- {text}")
                parts.append(f"\n\n## 最近 Zo 说过的话\n" + "\n".join(recent_lines))
        except Exception as e:
            print(f"[build_system_prompt] recent events error: {e}")

        if memory_context.strip():
            parts.append(f"\n\n## 你对用户的了解（Memory）\n{memory_context}")
        if inner_life_context.strip():
            parts.append(f"\n\n## 你的内在状态（Inner Life）\n{inner_life_context}")

        # 气泡分隔指令（始终注入，不受自定义 prompt 影响）
        parts.append(BUBBLE_SPLIT_INSTRUCTION)

        # 注入当前精确时间
        from datetime import datetime
        now = datetime.now()
        parts.append(f"\n\nCurrent time: {now.strftime('%Y-%m-%d %H:%M')} {now.astimezone().tzinfo}")

        return "".join(parts)
    @staticmethod
    def _deep_merge(base: dict, override: dict):
        """递归深合并"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                SettingsService._deep_merge(base[key], value)
            else:
                base[key] = value


# 单例
settings_service = SettingsService()
