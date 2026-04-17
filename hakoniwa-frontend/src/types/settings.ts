export interface CharacterSettings {
  soul: string
  mask: string
  personalization: string
  avatar_path: string
}

export interface LlmSettings {
  provider: 'claude' | 'gemini' | 'kimi' | 'deepseek' | 'openai' | 'siliconflow' | 'openai-compatible'
  api_key: string
  model: string
  base_url: string
}

export interface TtsSettings {
  provider: string
  api_key: string
  voice_id: string
  base_url: string
}

export interface SearchSettings {
  provider: string
  api_key: string
}

export interface ImageGenSettings {
  provider: string
  api_key: string
  model: string
}

export interface ApiSettings {
  llm: LlmSettings
  tts: TtsSettings
  search: SearchSettings
  image_gen: ImageGenSettings
}

export interface ThemeSettings {
  dark_mode: boolean
  skin: string
}

export interface Settings {
  character: CharacterSettings
  api: ApiSettings
  theme: ThemeSettings
}

export interface ModelsResponse {
  models: string[]
}
