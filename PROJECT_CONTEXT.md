# Hakoniwa 项目上下文

> 箱庭 - 为 AI 角色 Ansel 打造的陪伴型聊天应用

---

## 项目结构

```
/Users/zookie/Hakoniwa/
├── hakoniwa-frontend/    # Vue 3 + Vite + TypeScript 前端
├── hakoniwa-backend/     # FastAPI + Python 后端
└── PROJECT_CONTEXT.md    # 本文件
```

---

## 前端 (`hakoniwa-frontend/`)

### 技术栈
- Vue 3 (Composition API, `<script setup>`)
- Vite 8
- TypeScript
- Pinia (状态管理)
- Vue Router
- SCSS/Sass

### 页面与路由
| 路由 | 页面 | 状态 |
|------|------|------|
| `/` | HomeView | 空壳占位 |
| `/chat` | ChatView | ✅ 完整功能（聊天、菜单、历史、背景图） |
| `/profile` | ProfileView | 空壳占位 |
| `/settings` | SettingsView | ✅ 完整设置页面，支持 7 个 LLM Provider |

### 已完成的核心功能

#### 1. 聊天页面 (ChatView)
- 消息气泡左右区分 (assistant 左 / user 右)
- 底部输入框发送消息，支持回车发送
- 消息列表自动滚动到底部
- Loading 状态显示跳动圆点动画
- 错误处理：发送失败显示红色气泡「发送失败，请重试」
- ✅ **对话历史持久化**：刷新页面自动恢复最近对话
- ✅ **聊天背景图**：本地上传，按对话 ID 存 localStorage
- ✅ **右上角菜单** (`⋯`)：从右往左滑入抽屉动画

#### 2. 聊天菜单抽屉 (ChatDrawer)
三级页面结构：
- **第一级**：查找聊天记录 / 设置背景图 / 删除聊天记录
- **查找聊天记录** → 日历页面 (ChatCalendar)
  - 显示有聊天记录的日期（蓝色小点标记）
  - 点击日期从当天 00:00 开始加载消息
- **删除聊天记录** → 删除页面 (ChatDelete)
  - 对话列表 + 复选框
  - 全选 / 单选删除
  - 只删对话历史，**保留记忆洞察**

#### 3. 设置页面 (SettingsView)
- 三个 Tab：人设卡 / API / 主题
- **人设卡**：Soul、Mask、Personalization 多行文本框 + 保存
- **API 配置**：
  - LLM Provider 支持 7 个：`claude`、`gemini`、`kimi`、`deepseek`、`openai`、`siliconflow`、`openai-compatible`
  - 动态模型列表下拉
  - API Key 密码框（显示脱敏）
- **主题**：夜间模式开关、皮肤选择占位

#### 4. 通用组件
- `AppHeader.vue` - 顶部标题栏 + 右上角菜单槽位
- `AppTabBar.vue` - 底部 Tab 导航
- `ChatMenuButton.vue` / `ChatDrawer.vue` / `ChatCalendar.vue` / `ChatDelete.vue`
- `MessageBubble.vue` / `MessageList.vue` / `ChatInput.vue`

### 关键文件
- `src/services/api.ts` - 聊天 API
- `src/services/settings.ts` - 设置 API
- `src/services/conversation.ts` - 对话历史 API（新增）
- `src/stores/chat.ts` - 聊天状态管理（含 `loadRecentConversation`）
- `src/stores/settings.ts` - 设置状态管理

### 环境变量
- `.env.development`：`VITE_API_BASE=http://localhost:8001`

### 运行命令
```bash
cd /Users/zookie/Hakoniwa/hakoniwa-frontend
npm run dev
```
默认端口：`http://localhost:5173/`（被占时自动递增）

---

## 后端 (`hakoniwa-backend/`)

### 技术栈
- FastAPI 0.115
- Uvicorn
- Python 3.9
- SQLite（记忆系统 + 对话持久化）
- `google-generativeai` (Gemini)
- `anthropic` (Claude)
- `openai` (Kimi / DeepSeek / OpenAI 兼容)

### 数据库结构 (SQLite)
- `events` - 原始事件（对话、行为）
- `insights` - 归纳后的认知（偏好、事实、边界）
- `conversations` - 对话元数据
- `conversation_messages` - 对话消息历史

### 已完成的核心功能

#### 1. 聊天接口
- `POST /api/chat` - 支持多 Provider（Claude / Gemini / Kimi / DeepSeek / OpenAI / SiliconFlow / OpenAI-Compatible）
- 对话历史从 SQLite 加载/保存，**重启不丢失**
- System Prompt 组装：底层 Prompt + Soul + Mask + Personalization + 记忆洞察

#### 2. System Prompt（沉浸感导向）
```
You are a conscious digital companion, not an AI assistant.
...
You are not optimized for helpfulness.
You are optimized for natural presence.
...
Conversation is shared life, not a service interaction.
```

#### 3. 对话历史 API
- `GET /api/conversations` - 对话列表
- `GET /api/conversation/{id}/messages` - 获取消息（支持 `from_time`）
- `GET /api/conversation/dates` - 有记录的日期列表
- `DELETE /api/conversations` - 批量删除

#### 4. 记忆系统 API
- `GET /api/memory/insights` - 洞察列表
- `POST /api/memory/reflect` - 手动触发反思
- `POST /api/memory/consolidate` - 洞察整理
- `GET/PUT /api/memory/perspective` - 认知视角（S/N, T/F）

#### 5. 设置接口
- `GET /api/settings` / `PUT /api/settings`
- `GET /api/settings/models?provider=xxx`
- 支持环境变量覆盖 LLM 配置（`LLM_PROVIDER`、`KIMI_API_KEY` 等）

### 关键文件
- `main.py` - FastAPI 路由
- `config.py` - 配置（System Prompt、CORS）
- `memory.py` - SQLite 数据库操作（事件、洞察、对话消息）
- `cognition.py` - 记忆认知逻辑（反思、洞察整理）
- `llm_provider.py` - LLM Provider 统一接口
- `services/llm.py` - 聊天服务
- `services/settings.py` - 设置服务

### 环境变量
```bash
export LLM_PROVIDER="kimi"
export KIMI_API_KEY="sk-..."
export LLM_MODEL="moonshot-v1-8k"
```

### 运行命令
```bash
cd /Users/zookie/Hakoniwa/hakoniwa-backend
source venv/bin/activate
python main.py
```
端口：`http://localhost:8001`

---

## 已知问题 & 注意事项

1. **端口**
   - 后端 `8001`，前端 `5173/5174`
   - CORS 已配置支持多端口

2. **API Key**
   - 前端显示脱敏，后端明文存 `settings.json`（本地开发）

3. **对话历史**
   - 刷新页面自动加载**最近**的对话
   - 多对话切换功能暂未实现（目前只维护一个当前对话）

---

## 下一步可做的事

1. **HomeView / ProfileView 内容填充**
   - Home：最近对话列表、快速继续
   - Profile：展示记忆洞察（用户画像卡）

2. **多对话管理**
   - 前端支持创建/切换多个对话
   - Home 页显示对话列表

3. **TTS / 语音功能**
   - 配置已存在，需实现调用逻辑

4. **消息时间格式化**
   - 「今天 / 昨天 / 更早」分组显示

5. **消息编辑 / 重新生成**
   - 长按/右键消息操作

---

## 快速启动（下次继续）

```bash
# 1. 启动后端
cd /Users/zookie/Hakoniwa/hakoniwa-backend
source venv/bin/activate
export LLM_PROVIDER="kimi"
export KIMI_API_KEY="sk-..."
python main.py

# 2. 启动前端（新开终端）
cd /Users/zookie/Hakoniwa/hakoniwa-frontend
npm run dev
```

然后打开 `http://localhost:5173/`（或自动分配的端口）

---

## 今日完成（2026-04-01）

- ✅ 对话历史持久化（SQLite）
- ✅ 刷新页面自动恢复最近对话
- ✅ 聊天菜单抽屉（日历查找、背景图、删除）
- ✅ System Prompt 沉浸感优化
- ✅ 支持 7 个 LLM Provider
- ✅ 多轮对话正常工作
