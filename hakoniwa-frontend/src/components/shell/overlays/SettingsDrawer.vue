<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { useShellStore } from '@/stores/shell'
import { useSettingsStore } from '@/stores/settings'
import OverlayContainer from './OverlayContainer.vue'
import { X, Search, Heart, SlidersHorizontal, FileText, LayoutGrid, Cloud, Trash2 } from 'lucide-vue-next'
import DebugPanel from '@/components/debug/DebugPanel.vue'

const shell = useShellStore()
const settingsStore = useSettingsStore()

// 导航状态
const expanded = ref<Record<string, boolean>>({ api: true })
const selectedGroup = ref('api')
const selectedSub = ref('llm')

const searchQuery = ref('')

// 本地表单状态（仅 LLM）
const llmForm = reactive({
  provider: 'gemini',
  api_key: '',
  model: '',
  base_url: ''
})

const llmModels = ref<string[]>([])
const llmLoadingModels = ref(false)
const maskedPlaceholder = ref('')

function maskKey(key: string): string {
  if (!key || key.length <= 8) return key
  return `${key.slice(0, 4)}${'*'.repeat(key.length - 8)}${key.slice(-4)}`
}

function isKeyChanged(current: string, placeholder: string): boolean {
  if (!placeholder) return current !== ''
  return current !== placeholder
}

function resetLlmForm() {
  const s = settingsStore.settings
  llmForm.provider = s.api.llm.provider
  llmForm.model = s.api.llm.model
  llmForm.base_url = s.api.llm.base_url
  maskedPlaceholder.value = maskKey(s.api.llm.api_key)
  llmForm.api_key = s.api.llm.api_key ? maskedPlaceholder.value : ''
}

async function loadLlmModels() {
  if (!llmForm.provider) return
  llmLoadingModels.value = true
  const models = await settingsStore.loadModels(llmForm.provider)
  llmModels.value = models
  llmLoadingModels.value = false
}

watch(() => llmForm.provider, () => {
  loadLlmModels()
})

onMounted(() => {
  settingsStore.fetchSettings().then(() => {
    resetLlmForm()
    loadLlmModels()
  })
})

async function onSaveLlm() {
  const payload: any = {
    provider: llmForm.provider,
    model: llmForm.model,
    base_url: llmForm.base_url,
  }
  if (isKeyChanged(llmForm.api_key, maskedPlaceholder.value)) {
    payload.api_key = llmForm.api_key
  }
  await settingsStore.saveSettings({
    api: {
      llm: payload,
      tts: settingsStore.settings.api.tts,
      search: settingsStore.settings.api.search,
      image_gen: settingsStore.settings.api.image_gen,
    }
  })
  resetLlmForm()
}

const navItems = [
  {
    key: 'heartbeat',
    label: 'Heartbeat',
    icon: Heart,
    children: [
      { key: 'debug', label: 'Debug' }
    ]
  },
  {
    key: 'api',
    label: 'API',
    icon: SlidersHorizontal,
    children: [
      { key: 'llm', label: 'LLM' },
      { key: 'tts', label: 'TTS' },
      { key: 'search', label: 'Search' },
      { key: 'more', label: '...' },
    ]
  },
  { key: 'system_prompt', label: 'System Prompt', icon: FileText },
  { key: 'logs', label: 'Logs', icon: LayoutGrid },
  { key: 'record', label: 'Record', icon: Cloud },
  { key: 'data_erasure', label: 'Data Erasure', icon: Trash2 },
]

function selectItem(group: string, sub?: string) {
  selectedGroup.value = group
  selectedSub.value = sub || ''
}

function toggleExpand(key: string) {
  expanded.value[key] = !expanded.value[key]
}
</script>

<template>
  <OverlayContainer
    side="right"
    width="70%"
    offset="16px"
  >
    <div class="settings-drawer">
      <!-- Header -->
      <div class="drawer-header">
        <h2 class="drawer-title">Settings</h2>
        <button class="close-btn" @click="shell.toggleDrawer('settings')">
          <X :size="20" />
        </button>
      </div>

      <div class="drawer-body">
        <!-- 左栏 -->
        <aside class="settings-nav">
          <div class="search-box">
            <Search :size="14" class="search-icon" />
            <input v-model="searchQuery" type="text" placeholder="Search..." />
          </div>

          <div class="nav-list">
            <div
              v-for="item in navItems"
              :key="item.key"
              class="nav-group"
            >
              <button
                class="nav-item"
                :class="{ active: selectedGroup === item.key }"
                @click="item.children ? toggleExpand(item.key) : selectItem(item.key)"
              >
                <component :is="item.icon" v-if="item.icon" :size="16" />
                <span class="nav-label">{{ item.label }}</span>
              </button>

              <div v-if="item.children && expanded[item.key]" class="nav-children">
                <button
                  v-for="child in item.children"
                  :key="child.key"
                  class="nav-child"
                  :class="{ active: selectedGroup === item.key && selectedSub === child.key }"
                  @click="selectItem(item.key, child.key)"
                >
                  {{ child.label }}
                </button>
              </div>
            </div>
          </div>
        </aside>

        <!-- 右栏 -->
        <main class="settings-content">
          <!-- API → LLM 真实功能 -->
          <template v-if="selectedGroup === 'api' && selectedSub === 'llm'">
            <h3 class="content-title">API / LLM</h3>
            <div class="form-fields">
              <div class="field">
                <label>Provider</label>
                <select v-model="llmForm.provider" class="input-like">
                  <option value="claude">Claude</option>
                  <option value="gemini">Gemini</option>
                  <option value="kimi">Kimi (Moonshot)</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="openai">OpenAI</option>
                  <option value="siliconflow">SiliconFlow</option>
                  <option value="openai-compatible">OpenAI 兼容</option>
                </select>
              </div>

              <div class="field">
                <label>API Key</label>
                <input
                  v-model="llmForm.api_key"
                  type="password"
                  class="input-like"
                  placeholder="输入 API Key"
                />
              </div>

              <div class="field">
                <label>Model</label>
                <select v-model="llmForm.model" class="input-like" :disabled="llmLoadingModels">
                  <option value="">-- 选择模型 --</option>
                  <option v-for="m in llmModels" :key="m" :value="m">{{ m }}</option>
                </select>
              </div>

              <div class="field">
                <label>Base URL（可选）</label>
                <input
                  v-model="llmForm.base_url"
                  type="text"
                  class="input-like"
                  placeholder="https://api.example.com/v1"
                />
              </div>
            </div>

            <button
              class="save-btn"
              :disabled="settingsStore.saving"
              @click="onSaveLlm"
            >
              {{ settingsStore.saving ? 'Saving...' : 'Save' }}
            </button>
          </template>

            <!-- Heartbeat → Debug -->
          <template v-if="selectedGroup === 'heartbeat' && selectedSub === 'debug'">
            <DebugPanel />
          </template>

          <!-- 其他全部占位 -->
          <template v-else>
            <div class="coming-soon">
              <p>Coming soon</p>
            </div>
          </template>
        </main>
      </div>
    </div>
  </OverlayContainer>
</template>

<style scoped lang="scss">
.settings-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: var(--radius-card);
  overflow: hidden;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}

.drawer-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--color-text);
}

.close-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.4);
  color: var(--color-text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.7);
  }
}

.drawer-body {
  display: flex;
  flex: 1;
  min-height: 0;
}

.settings-nav {
  width: 35%;
  min-width: 180px;
  max-width: 260px;
  border-right: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 12px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-input);
  border: 1px solid rgba(255, 255, 255, 0.5);

  input {
    flex: 1;
    border: none;
    background: transparent;
    font-size: 13px;
    color: var(--color-text);
    outline: none;

    &::placeholder {
      color: var(--color-text-muted);
    }
  }
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-button);
  border: none;
  background: transparent;
  color: var(--color-text);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.35);
  }

  &.active {
    background: rgba(255, 255, 255, 0.6);
    font-weight: 600;
  }
}

.nav-children {
  display: flex;
  flex-direction: column;
  padding-left: 28px;
}

.nav-child {
  text-align: left;
  padding: 8px 12px;
  border-radius: var(--radius-button);
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 12px;
  cursor: pointer;

  &:hover {
    color: var(--color-text);
    background: rgba(255, 255, 255, 0.25);
  }

  &.active {
    color: var(--color-text);
    background: rgba(255, 255, 255, 0.45);
    font-weight: 600;
  }
}

.settings-content {
  flex: 1;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-y: auto;
  min-height: 0;
}

.content-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px;
  color: var(--color-text);
}

.form-fields {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;

  label {
    font-size: 12px;
    font-weight: 500;
    color: var(--color-text-muted);
  }
}

.input-like {
  padding: 10px 12px;
  border-radius: var(--radius-input);
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  color: var(--color-text);
  outline: none;

  &:focus {
    border-color: rgba(90, 139, 176, 0.5);
    background: rgba(255, 255, 255, 0.55);
  }

  &::placeholder {
    color: var(--color-text-weak);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.save-btn {
  align-self: flex-end;
  margin-top: auto;
  padding: 10px 28px;
  border-radius: var(--radius-button);
  border: none;
  background: #a8c8e8;
  color: #1a3a52;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;

  &:hover:not(:disabled) {
    background: #98b8d8;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.coming-soon {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-size: 14px;
}
</style>
