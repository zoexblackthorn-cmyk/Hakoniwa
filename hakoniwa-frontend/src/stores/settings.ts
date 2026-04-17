import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import type { Settings } from '@/types/settings'
import { getSettings, updateSettings, getModels } from '@/services/settings'

const defaultSettings: Settings = {
  character: {
    soul: '',
    mask: '',
    personalization: '',
    avatar_path: ''
  },
  api: {
    llm: {
      provider: 'gemini',
      api_key: '',
      model: '',
      base_url: ''
    },
    tts: {
      provider: '',
      api_key: '',
      voice_id: '',
      base_url: ''
    },
    search: {
      provider: 'brave',
      api_key: ''
    },
    image_gen: {
      provider: '',
      api_key: '',
      model: ''
    }
  },
  theme: {
    dark_mode: false,
    skin: 'default'
  }
}

function maskApiKey(key: string): string {
  if (!key || key.length <= 8) return key
  return `${key.slice(0, 4)}${'*'.repeat(key.length - 8)}${key.slice(-4)}`
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<Settings>(JSON.parse(JSON.stringify(defaultSettings)))
  const loading = ref(false)
  const saving = ref(false)
  const error = ref<string | null>(null)
  const toast = ref<{ message: string; type: 'success' | 'error' } | null>(null)

  const maskedSettings = computed(() => {
    const s = JSON.parse(JSON.stringify(settings.value)) as Settings
    s.api.llm.api_key = maskApiKey(s.api.llm.api_key)
    s.api.tts.api_key = maskApiKey(s.api.tts.api_key)
    s.api.search.api_key = maskApiKey(s.api.search.api_key)
    s.api.image_gen.api_key = maskApiKey(s.api.image_gen.api_key)
    return s
  })

  async function fetchSettings() {
    loading.value = true
    error.value = null
    try {
      const data = await getSettings()
      settings.value = { ...defaultSettings, ...data }
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载设置失败'
      showToast(error.value, 'error')
    } finally {
      loading.value = false
    }
  }

  async function saveSettings(partial: Partial<Settings>) {
    saving.value = true
    error.value = null
    try {
      const data = await updateSettings(partial)
      settings.value = { ...defaultSettings, ...data }
      showToast('保存成功', 'success')
    } catch (e) {
      error.value = e instanceof Error ? e.message : '保存设置失败'
      showToast(error.value, 'error')
      throw e
    } finally {
      saving.value = false
    }
  }

  async function loadModels(provider: string) {
    try {
      const res = await getModels(provider)
      return res.models
    } catch (e) {
      return []
    }
  }

  function showToast(message: string, type: 'success' | 'error' = 'success') {
    toast.value = { message, type }
    setTimeout(() => {
      toast.value = null
    }, 2500)
  }

  // 监听 dark_mode 变化，切换 body class
  watch(
    () => settings.value.theme.dark_mode,
    (dark) => {
      if (dark) {
        document.body.classList.add('dark-mode')
      } else {
        document.body.classList.remove('dark-mode')
      }
    },
    { immediate: true }
  )

  return {
    settings,
    maskedSettings,
    loading,
    saving,
    error,
    toast,
    fetchSettings,
    saveSettings,
    loadModels,
    showToast
  }
})
