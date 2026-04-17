<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RotateCcw } from 'lucide-vue-next'
import { useSettingsStore } from '@/stores/settings'
import { getSystemPrompt } from '@/services/settings'

const settingsStore = useSettingsStore()

const base = ref('')
const loading = ref(false)
const saving = ref(false)
const error = ref('')

const charCount = computed(() => base.value.length)

function resetForm() {
  base.value = settingsStore.settings.system_prompt.base
}

async function loadFromApi() {
  loading.value = true
  error.value = ''
  try {
    const data = await getSystemPrompt()
    base.value = data.base
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function onSave() {
  saving.value = true
  error.value = ''
  try {
    await settingsStore.saveSettings({
      system_prompt: { base: base.value }
    })
    resetForm()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  resetForm()
  // 如果用户设置为空，从 API 拉取默认内容（包含回退逻辑）
  if (!base.value.trim()) {
    loadFromApi()
  }
})
</script>

<template>
  <div class="system-prompt-panel">
    <div class="panel-header">
      <h3 class="content-title">System Prompt / Base</h3>
      <button class="refresh-btn" :disabled="loading" @click="loadFromApi">
        <RotateCcw :size="14" :class="{ spin: loading }" />
        <span>{{ loading ? '加载中...' : '恢复默认' }}</span>
      </button>
    </div>

    <div v-if="error" class="error-msg">
      {{ error }}
    </div>

    <div class="field">
      <label>底层 Prompt（留空则使用默认）</label>
      <textarea
        v-model="base"
        class="input-like"
        rows="18"
        placeholder="输入底层 System Prompt..."
      />
    </div>

    <div class="panel-footer">
      <span class="char-count">{{ charCount.toLocaleString() }} 字符</span>
      <button
        class="save-btn"
        :disabled="saving || settingsStore.saving"
        @click="onSave"
      >
        {{ saving || settingsStore.saving ? 'Saving...' : 'Save' }}
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.system-prompt-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.content-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: var(--color-text);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-button);
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.35);
  color: var(--color-text);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.55);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  svg.spin {
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-msg {
  padding: 12px 16px;
  border-radius: var(--radius-card);
  background: rgba(217, 122, 122, 0.15);
  border: 1px solid rgba(217, 122, 122, 0.3);
  color: #b85a5a;
  font-size: 13px;
}

.field {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  gap: 6px;

  label {
    font-size: 12px;
    font-weight: 500;
    color: var(--color-text-muted);
  }
}

.input-like {
  flex: 1;
  min-height: 0;
  padding: 12px;
  border-radius: var(--radius-input);
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  color: var(--color-text);
  outline: none;
  resize: none;
  font-family: ui-monospace, 'Cascadia Code', 'SF Mono', Consolas, monospace;
  line-height: 1.7;

  &:focus {
    border-color: rgba(90, 139, 176, 0.5);
    background: rgba(255, 255, 255, 0.55);
  }

  &::placeholder {
    color: var(--color-text-weak);
  }
}

.panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.char-count {
  font-size: 11px;
  color: var(--color-text-muted);
}

.save-btn {
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
</style>
