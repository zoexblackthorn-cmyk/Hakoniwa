const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`${path} -> ${res.status}`)
  return res.json()
}

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`${path} -> ${res.status}`)
  return res.json()
}

// --- Types ---
export interface EnnoiaState {
  needs: { social: number; stimulation: number; expression: number }
  mood: { valence: number; arousal: number }
  personality: { social: number; stimulation: number; expression: number }
  current_activity: { name: string; satisfies: string; stim_rate: number; ticks_on: number; started_at: string }
  unshared_experiences: number
  closeness: number
  last_user_interaction_at: string | null
  last_initiative_at: string | null
}

export interface Desire {
  id: number
  need: string
  activity_name: string
  intensity: number
  origin: string
  status: string
  created_at: string
  needs_user?: number
}

export interface ActivityPoolItem {
  name: string
  satisfies: string
  affinity: number
  times_done: number
  last_done_at: string | null
  stim_rate: number
}

export interface Insight {
  id: number
  content: string
  category: string
  confidence: number
  created_at: string
  updated_at: string
}

export interface ChatError {
  message: string
  type: string
  traceback: string
  timestamp: string
}

// --- Queries ---
export const debugApi = {
  getEnnoiaState: () => getJson<EnnoiaState>('/api/ennoia/state'),
  getDesires: () => getJson<{ desires: Desire[] }>('/api/ennoia/desires'),
  getActivityPool: () => getJson<{ activities: ActivityPoolItem[] }>('/api/ennoia/activity-pool'),
  getInsights: (minConfidence = 0.3) =>
    getJson<{ insights: Insight[] }>(`/api/memory/insights?min_confidence=${minConfidence}`),
  getLastChatError: () => getJson<{ error: ChatError | null }>('/api/debug/last-chat-error'),

  // Actions
  manualTick: () => postJson<unknown>('/api/ennoia/tick'),
  reflect: () => postJson<unknown>('/api/memory/reflect'),
  consolidate: () => postJson<unknown>('/api/memory/consolidate'),
  syncActivityPool: () => postJson<unknown>('/api/ennoia/sync-activity-pool'),
  clearChatError: () => postJson<unknown>('/api/debug/clear-chat-error'),
}
