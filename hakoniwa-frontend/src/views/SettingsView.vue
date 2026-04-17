<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import SettingsTabBar from '@/components/settings/SettingsTabBar.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import CollapsibleCard from '@/components/common/CollapsibleCard.vue'
import SecretInput from '@/components/common/SecretInput.vue'
import { useSettingsStore } from '@/stores/settings'
import type { Settings } from '@/types/settings'

const settingsStore = useSettingsStore()
const activeTab = ref('character')

const tabs = [
  { key: 'character', label: '人设卡' },
  { key: 'api', label: 'API' },
  { key: 'theme', label: '主题' }
]

// 本地表单状态
const form = reactive<Settings>({
  character: { soul: '', mask: '', personalization: '', avatar_path: '' },
  api: {
    llm: { provider: 'gemini', api_key: '', model: '', base_url: '' },
    tts: { provider: '', api_key: '', voice_id: '', base_url: '' },
    search: { provider: 'brave', api_key: '' },
    image_gen: { provider: '', api_key: '', model: '' }
  },
  theme: { dark_mode: false, skin: 'default' }
})

const llmModels = ref<string[]>([])
const llmLoadingModels = ref(false)

// 掩码占位符，用于判断用户是否修改了 key
const maskedPlaceholders = reactive({
  llm: '',
  tts: '',
  search: '',
  image_gen: ''
})

function maskKey(key: string): string {
  if (!key || key.length <= 8) return key
  return `${key.slice(0, 4)}${'*'.repeat(key.length - 8)}${key.slice(-4)}`
}

function isKeyChanged(current: string, placeholder: string): boolean {
  if (!placeholder) return current !== ''
  return current !== placeholder
}

function resetForm() {
  const s = settingsStore.settings
  form.character = { ...s.character }
  form.api.llm = { ...s.api.llm }
  form.api.tts = { ...s.api.tts }
  form.api.search = { ...s.api.search }
  form.api.image_gen = { ...s.api.image_gen }
  form.theme = { ...s.theme }

  maskedPlaceholders.llm = maskKey(s.api.llm.api_key)
  maskedPlaceholders.tts = maskKey(s.api.tts.api_key)
  maskedPlaceholders.search = maskKey(s.api.search.api_key)
  maskedPlaceholders.image_gen = maskKey(s.api.image_gen.api_key)

  // 如果 key 存在，表单显示掩码值（用户可覆盖输入）
  if (s.api.llm.api_key) form.api.llm.api_key = maskedPlaceholders.llm
  if (s.api.tts.api_key) form.api.tts.api_key = maskedPlaceholders.tts
  if (s.api.search.api_key) form.api.search.api_key = maskedPlaceholders.search
  if (s.api.image_gen.api_key) form.api.image_gen.api_key = maskedPlaceholders.image_gen
}

async function loadLlmModels() {
  if (!form.api.llm.provider) return
  llmLoadingModels.value = true
  const models = await settingsStore.loadModels(form.api.llm.provider)
  llmModels.value = models
  llmLoadingModels.value = false
}

watch(() => form.api.llm.provider, () => {
  loadLlmModels()
})

async function onSaveCharacter() {
  await settingsStore.saveSettings({ character: { ...form.character } })
}

async function onSaveApi() {
  // 构造要发送的 llm / tts / search / image_gen 对象，始终发送所有非 key 字段
  const llmToSend: any = {
    provider: form.api.llm.provider,
    model: form.api.llm.model,
    base_url: form.api.llm.base_url,
  }
  // 只在 api_key 真的改了的时候才发送它，避免把掩码当成新 key
  if (isKeyChanged(form.api.llm.api_key, maskedPlaceholders.llm)) {
    llmToSend.api_key = form.api.llm.api_key
  }

  const ttsToSend: any = {
    provider: form.api.tts.provider,
    voice_id: form.api.tts.voice_id,
    base_url: form.api.tts.base_url,
  }
  if (isKeyChanged(form.api.tts.api_key, maskedPlaceholders.tts)) {
    ttsToSend.api_key = form.api.tts.api_key
  }

  const searchToSend: any = {
    provider: form.api.search.provider,
  }
  if (isKeyChanged(form.api.search.api_key, maskedPlaceholders.search)) {
    searchToSend.api_key = form.api.search.api_key
  }

  const imageGenToSend: any = {
    provider: form.api.image_gen.provider,
    model: form.api.image_gen.model,
  }
  if (isKeyChanged(form.api.image_gen.api_key, maskedPlaceholders.image_gen)) {
    imageGenToSend.api_key = form.api.image_gen.api_key
  }

  await settingsStore.saveSettings({
    api: {
      llm: llmToSend,
      tts: ttsToSend,
      search: searchToSend,
      image_gen: imageGenToSend,
    },
  })

  resetForm()
}

async function onSaveTheme() {
  await settingsStore.saveSettings({ theme: { ...form.theme } })
}

onMounted(() => {
  settingsStore.fetchSettings().then(() => {
    resetForm()
    loadLlmModels()
  })
})
</script>

<template>
  <div class="settings-view">
    <AppHeader title="设置" />
    <SettingsTabBar v-model="activeTab" :tabs="tabs" />

    <div class="scroll-content">
      <!-- 人设卡 -->
      <div v-show="activeTab === 'character'" class="tab-panel">
        <div class="card">
          <h2 class="section-title">AI 人设</h2>
          <div class="field">
            <label class="field-label">Soul（灵魂）</label>
            <textarea
              v-model="form.character.soul"
              class="textarea"
              rows="4"
              placeholder="描述你的AI伙伴是谁..."
            />
            <p class="field-hint">决定 AI 的性格、说话方式和核心身份</p>
          </div>
          <div class="field">
            <label class="field-label">Mask（面具）</label>
            <textarea
              v-model="form.character.mask"
              class="textarea"
              rows="4"
              placeholder="你希望AI怎么看待你..."
            />
            <p class="field-hint">AI 眼中你的形象、你们之间的关系</p>
          </div>
          <div class="field">
            <label class="field-label">Personalization（个性化）</label>
            <textarea
              v-model="form.character.personalization"
              class="textarea"
              rows="4"
              placeholder="你的兴趣爱好、习惯偏好..."
            />
            <p class="field-hint">让 AI 更了解你的喜好和日常习惯</p>
          </div>
        </div>
        <button class="save-btn" :disabled="settingsStore.saving" @click="onSaveCharacter">
          {{ settingsStore.saving ? '保存中...' : '保存人设' }}
        </button>
      </div>

      <!-- API 配置 -->
      <div v-show="activeTab === 'api'" class="tab-panel">
        <CollapsibleCard title="LLM 配置" :default-expanded="true">
          <div class="field">
            <label class="field-label">Provider</label>
            <select v-model="form.api.llm.provider" class="select">
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
            <label class="field-label">API Key</label>
            <SecretInput v-model="form.api.llm.api_key" placeholder="输入 API Key" />
          </div>
          <div class="field">
            <label class="field-label">Model</label>
            <select v-model="form.api.llm.model" class="select" :disabled="llmLoadingModels">
              <option value="">-- 选择模型 --</option>
              <option v-for="m in llmModels" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>
          <div class="field">
            <label class="field-label">Base URL（可选）</label>
            <input
              v-model="form.api.llm.base_url"
              type="text"
              class="input"
              placeholder="https://api.example.com/v1"
            />
          </div>
        </CollapsibleCard>

        <CollapsibleCard title="TTS 配置">
          <div class="field">
            <label class="field-label">Provider</label>
            <input v-model="form.api.tts.provider" type="text" class="input" placeholder="例如：elevenlabs" />
          </div>
          <div class="field">
            <label class="field-label">API Key</label>
            <SecretInput v-model="form.api.tts.api_key" placeholder="输入 API Key" />
          </div>
          <div class="field">
            <label class="field-label">Voice ID</label>
            <input v-model="form.api.tts.voice_id" type="text" class="input" placeholder="例如：Bella" />
          </div>
          <div class="field">
            <label class="field-label">Base URL（可选）</label>
            <input v-model="form.api.tts.base_url" type="text" class="input" placeholder="https://api.example.com" />
          </div>
        </CollapsibleCard>

        <CollapsibleCard title="搜索 API">
          <div class="field">
            <label class="field-label">Provider</label>
            <input v-model="form.api.search.provider" type="text" class="input" placeholder="例如：brave" />
          </div>
          <div class="field">
            <label class="field-label">API Key</label>
            <SecretInput v-model="form.api.search.api_key" placeholder="输入 API Key" />
          </div>
        </CollapsibleCard>

        <CollapsibleCard title="图像生成">
          <div class="field">
            <label class="field-label">Provider</label>
            <input v-model="form.api.image_gen.provider" type="text" class="input" placeholder="例如：dalle" />
          </div>
          <div class="field">
            <label class="field-label">API Key</label>
            <SecretInput v-model="form.api.image_gen.api_key" placeholder="输入 API Key" />
          </div>
          <div class="field">
            <label class="field-label">Model</label>
            <input v-model="form.api.image_gen.model" type="text" class="input" placeholder="例如：dall-e-3" />
          </div>
        </CollapsibleCard>

        <button class="save-btn" :disabled="settingsStore.saving" @click="onSaveApi">
          {{ settingsStore.saving ? '保存中...' : '保存 API 配置' }}
        </button>
      </div>

      <!-- 主题 -->
      <div v-show="activeTab === 'theme'" class="tab-panel">
        <div class="card">
          <h2 class="section-title">显示设置</h2>
          <div class="theme-row">
            <span class="theme-label">夜间模式</span>
            <ToggleSwitch v-model="form.theme.dark_mode" />
          </div>
        </div>

        <div class="card">
          <h2 class="section-title">皮肤</h2>
          <div class="skin-grid">
            <div class="skin-item active">
              <div class="skin-preview default" />
              <span class="skin-name">默认</span>
            </div>
            <div class="skin-item disabled">
              <div class="skin-preview placeholder" />
              <span class="skin-name">更多皮肤即将推出</span>
            </div>
          </div>
        </div>

        <button class="save-btn" :disabled="settingsStore.saving" @click="onSaveTheme">
          {{ settingsStore.saving ? '保存中...' : '保存主题' }}
        </button>
      </div>
    </div>

    <!-- Toast -->
    <Transition name="fade">
      <div v-if="settingsStore.toast" class="toast" :class="settingsStore.toast.type">
        {{ settingsStore.toast.message }}
      </div>
    </Transition>
  </div>
</template>

<style scoped lang="scss">
.settings-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.scroll-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.tab-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card {
  background: #ffffff;
  border: 2px solid #d0e6f4;
  border-radius: 14px;
  padding: 16px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #4a6a80;
  margin: 0 0 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;

  &:last-child {
    margin-bottom: 0;
  }
}

.field-label {
  font-size: 13px;
  font-weight: 500;
  color: #5a8bb0;
}

.textarea,
.input,
.select {
  width: 100%;
  padding: 10px 12px;
  border: 2px solid #d0e6f4;
  border-radius: 10px;
  background: #f5fbff;
  font-size: 14px;
  color: #4a6a80;
  outline: none;
  transition: border-color 0.2s;
  resize: vertical;

  &:focus {
    border-color: #a8c8dc;
  }

  &::placeholder {
    color: #a8c8dc;
  }
}

.select {
  appearance: auto;
}

.field-hint {
  font-size: 12px;
  color: #9bb8cc;
  margin: 0;
}

.save-btn {
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: none;
  background: #6a9ab8;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 4px;

  &:hover:not(:disabled) {
    background: #5a8aa8;
  }

  &:disabled {
    background: #a8c8dc;
    cursor: not-allowed;
  }
}

.theme-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.theme-label {
  font-size: 14px;
  color: #4a6a80;
}

.skin-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.skin-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 12px;
  border: 2px solid #d0e6f4;
  background: #f5fbff;
  cursor: pointer;

  &.active {
    border-color: #6a9ab8;
  }

  &.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.skin-preview {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid #d0e6f4;

  &.default {
    background: linear-gradient(135deg, #e8f4fc 0%, #b8d4e8 100%);
  }

  &.placeholder {
    background: #e8f4fc;
  }
}

.skin-name {
  font-size: 12px;
  color: #4a6a80;
  text-align: center;
}

.toast {
  position: fixed;
  left: 50%;
  bottom: 80px;
  transform: translateX(-50%);
  padding: 10px 18px;
  border-radius: 20px;
  font-size: 13px;
  color: #ffffff;
  z-index: 100;
  pointer-events: none;

  &.success {
    background: #6a9ab8;
  }

  &.error {
    background: #d97a7a;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}
</style>
