# Hakoniwa 开发日志 — 2026-04-18

---

## 项目完成度总览

### 后端 (hakoniwa-backend)
| 模块 | 状态 | 说明 |
|------|------|------|
| LLM 对话 | ✅ 完成 | 支持 Claude / Gemini / OpenAI 兼容 (Kimi/DeepSeek/SiliconFlow 等)，含图片 vision |
| 记忆系统 | ✅ 完成 | SQLite + VoyageAI 嵌入，事件记录、洞察归纳、反思、整理 |
| Ennoia (内在生命) | ✅ 完成 | 需求/情绪/人格/活动池，30s tick 循环，主动发起对话 |
| TTS | ✅ 完成 | `/api/tts`，支持 OpenAI 兼容 + Edge TTS (免费) |
| Brave Search | ✅ 完成 | `/api/search`，支持 Brave Search API |
| System Prompt | ✅ 完成 | `/api/system-prompt`，可编辑底层 base prompt |
| 用户档案 | ✅ 完成 | `/api/user`，名字/职业/头像/Mask/Personalization |
| Todo | ✅ 完成 | CRUD 接口 |
| 任务调度 (新) | ✅ 完成 | APScheduler AsyncIOScheduler，意图拦截 + 时间感知 |
| 设置持久化 | ✅ 完成 | JSON 文件 + Pydantic 验证，支持部分更新 |
| CORS / 健康检查 | ✅ 完成 | — |

### 前端 (hakoniwa-frontend)
| 模块 | 状态 | 说明 |
|------|------|------|
| 桌面主界面 (AppShell) | ✅ 完成 | 玻璃拟态侧边栏 + 聊天/设置/用户卡/角色卡抽屉 |
| 聊天界面 | ✅ 完成 | 消息气泡、附件图片、输入框、日历菜单、背景图 |
| 设置抽屉 | ✅ 完成 | API (LLM/TTS/Search) + System Prompt (Base) + 其他占位 |
| 角色卡片 | ✅ 完成 | 头像上传、Soul 编辑、HEXACO 占位 |
| 用户卡片 | ✅ 完成 | 头像上传、Mask/Profession/Personalization 编辑 |
| 头像显示 | ✅ 完成 | 骨架屏 loading → 正确头像，无闪烁 |
| Widget 首页 | ✅ 完成 | 天气/日历等占位组件 |
| 响应式 | ✅ 完成 | 桌面/移动端自适应 |

---

## 今日修复的 Bug

### 1. 关闭聊天界面后 LLM 无法返回消息
**根因:** `ChatDrawer.vue` 每次挂载都会调用 `loadRecentConversation()` 覆盖 `messages`，抹掉 `sending` 占位消息。  
**修复:** `AppShell.vue` 统一在 `onMounted` 中调用 `loadRecentConversation()`（仅一次），`ChatDrawer.vue` 移除重复调用。

### 2. 回车触发图片发送失败
**根因:** 后端 `ChatRequest` 不支持附件，且空消息会被 400 拒绝。  
**修复:**
- 前端图片转为 base64 data URL
- 后端 `ChatRequest` 新增 `attachments` 字段
- 后端 LLM 三提供商 (Claude/Gemini/OpenAI) 全部接入 vision 图片输入
- 允许纯图片发送（空消息 + 附件不报错）

### 3. 头像需要点击才显示上传的图片
**根因:** `AppShell.vue` 启动时没调用 `settingsStore.fetchSettings()`，settings 使用默认值（avatar_path 为空）。  
**修复:** `AppShell.vue` `onMounted` 中新增 `settingsStore.fetchSettings()` + `chatStore.loadRecentConversation()`。

### 4. 消息发出后留在输入框 + 省略号不显示
**根因:** 
- 中文输入法 Enter 确认拼音时误触发发送（`e.isComposing` 未检查）
- `ChatDrawer` 重新挂载时 `loadRecentConversation()` 覆盖 `messages`，抹掉 `sending` 状态
**修复:** `ChatInput.vue` 增加 `!e.isComposing` 判断；`ChatDrawer.vue` 不再覆盖消息。

### 5. 刷新后聊天窗口跳到最远消息
**根因:** `MessageList.vue` 只在 `messages.length` 变化时滚动。但 `AppShell` 预加载消息时 `MessageList` 还没渲染，打开聊天窗口后 `length` 不变，watch 不触发。  
**修复:** `MessageList.vue` 新增 `onMounted` + `scrollToBottom()`，挂载时如果已有消息立即滚到底部。

### 6. Claude 代码审查修复（7 处 bug）
**来源:** Claude 代码审查报告  
**修复文件:**

| # | 文件 | 问题 | 修复 |
|---|------|------|------|
| 1 | `services/llm.py` | `_chat_gemini` 未传递 `inner_life_context` 给 `build_system_prompt` | 补全第二个参数，与 Claude/OpenAI 路径一致 |
| 2 | `main.py` | 调度意图分支 (`is_task=True`) 直接 return，未记录消息、未触发 Ennoia、未写入对话历史 | return 前调用 `memory_service.record_message`、`ennoia.on_user_message`、`save_conversation_message`（conversation_id 非空时） |
| 3 | `main.py` | `_last_chat_error` 在文件顶部和 Debug 区重复声明 | 删除 Debug 区重复声明 |
| 4 | `memory.py` | `save_conversation_message` 未过滤空内容 | 开头加判空：content 为 None 或空字符串时 `return -1` 并打印跳过日志 |
| 5 | `services/llm.py` | 四个方法使用可变默认值 `attachments: list[str] = []` | 改为 `list[str] \| None = None`，方法体内 `attachments = attachments or []` |
| 6 | `src/stores/chat.ts` | `JSON.parse(m.metadata)` 无保护，脏数据会导致整个加载崩溃 | 用 IIFE + try/catch 包裹，解析失败返回 `undefined` |
| 7 | `config.py` | 默认端口 `8000` 与前端 `.env.development` 的 `8001` 不一致 | 默认值改为 `8001` |

---

## 今日新增内容

### 后端新增

#### 1. TTS 服务 (`services/tts.py`)
- `POST /api/tts` — 文本转语音
- 支持 `openai` (兼容) 和 `edge-tts` (免费)
- 返回 `audio/mpeg` 字节流

#### 2. Brave Search 服务 (`services/search.py`)
- `GET /api/search?q=...` — Web 搜索
- 支持 Brave Search API
- 返回结构化结果 `[{title, url, description}]`

#### 3. System Prompt 可编辑 (`models/settings.py` + 前端)
- 新增 `SystemPromptSettings` 模型，字段 `base`
- `build_system_prompt()` 优先读取用户设置的 base prompt，留空则回退到 `config.BASE_SYSTEM_PROMPT`
- 前端 SettingsDrawer → System Prompt → Base 面板可直接编辑保存

#### 4. 任务调度系统 (`services/scheduler_service.py`, `services/task_handler.py`, `services/time_aware.py`)
- **Scheduler:** APScheduler `AsyncIOScheduler`，FastAPI startup 启动，不破坏 ennoia loop
- **Task Handler:** `send_email()` 示例任务 + `handle_task()` 分发入口
- **Time Aware:**
  - `get_time_mode()` — 返回时间段标签
  - `detect_schedule_intent()` — 零 token 规则匹配（`dateparser` + 关键词），支持中英文
- **Chat 拦截:** `/api/chat` 在调用 LLM 前检测调度意图，识别到则安排任务并返回确认；否则正常对话
- **精确时间注入:** `build_system_prompt()` 末尾追加 `Current time: YYYY-MM-DD HH:MM TZ`，LLM 可准确回答当前时间

#### 5. 依赖新增
```
apscheduler
dateparser
requests
edge-tts
```

### 前端新增

#### 1. TTS 设置面板 (`SettingsDrawer.vue`)
- Provider 选择（OpenAI 兼容 / Edge TTS）
- API Key / Voice ID / Base URL 输入
- 独立保存按钮

#### 2. Search 设置面板 (`SettingsDrawer.vue`)
- Provider 选择（Brave Search）
- API Key 输入
- 独立保存按钮

#### 3. System Prompt / Base 设置面板 (`SystemPromptPanel.vue`)
- 大型 textarea 编辑底层 prompt
- 恢复默认按钮（从 `/api/system-prompt` 拉取）
- 字符数统计

#### 4. 头像骨架屏 (`SideNav.vue`, `ChatDrawer.vue`)
- 数据加载前显示 `avatar-skeleton` pulse 动画
- 加载完成后淡入正确头像
- 消除 fallback 头像闪烁

#### 5. `SettingsDrawer.vue` 导航结构修复
- `system_prompt` 改为可展开母项，`base` 作为子项
- `v-if/v-else-if` 链修复，避免 `Coming soon` 与真实内容同时渲染

---

## 文件变更清单

### 后端
- `models/settings.py` — 新增 `SystemPromptSettings`
- `models/chat.py` — 新增 `attachments` 字段
- `services/tts.py` — 新建
- `services/search.py` — 新建
- `services/scheduler_service.py` — 新建
- `services/task_handler.py` — 新建
- `services/time_aware.py` — 新建
- `services/llm.py` — 三大 provider 接入 vision 图片输入
- `services/settings.py` — `build_system_prompt()` 读取用户 base prompt + 注入精确时间
- `main.py` — 新增 TTS/Search/SystemPrompt 路由 + 调度器启动 + Chat 拦截逻辑
- `requirements.txt` — 新增 apscheduler, dateparser, requests, edge-tts

### 前端
- `src/components/shell/AppShell.vue` — 启动时加载 settings + chat history
- `src/components/shell/SideNav.vue` — 骨架屏 + 头像条件渲染
- `src/components/shell/overlays/ChatDrawer.vue` — 移除重复加载 + 骨架屏
- `src/components/shell/overlays/SettingsDrawer.vue` — TTS/Search/SystemPrompt 面板 + 导航修复
- `src/components/settings/SystemPromptPanel.vue` — 新建
- `src/components/chat/ChatInput.vue` — base64 图片 + `isComposing` 修复
- `src/components/chat/MessageList.vue` — `onMounted` 自动滚动到底部
- `src/services/api.ts` — `attachments` 字段
- `src/services/settings.ts` — `getSystemPrompt()`
- `src/services/user.ts` — 端口 8000（已回滚）
- `src/stores/chat.ts` — 传递 attachments
- `src/types/settings.ts` — `SystemPromptSettings`
- `.env.development` — 端口 8001（保持原样）

---

*日志生成时间: 2026-04-18*
