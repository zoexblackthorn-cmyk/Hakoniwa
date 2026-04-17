const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'

export interface EnnoiaState {
  needs: { social: number; stimulation: number; expression: number }
  mood: { valence: number; arousal: number }
  personality: { social: number; stimulation: number; expression: number }
  current_activity: { name: string; satisfies: string; ticks_on: number }
  unshared_experiences: number
  closeness: number
}

export interface Desire {
  id: number
  need: string
  intensity: number
  activity_name: string
  needs_user: number
  user_request: string
  origin: string
  status: string
  created_at: string
}

export interface Activity {
  id: number
  name: string
  satisfies: string
  stim_rate: number
  needs_user: number
  user_request: string
  affinity: number
  times_done: number
  last_done_at: string | null
}

export async function fetchEnnoiaState(): Promise<EnnoiaState> {
  const res = await fetch(`${API_BASE}/api/ennoia/state`)
  if (!res.ok) throw new Error(`GET /api/ennoia/state -> ${res.status}`)
  return res.json()
}

export async function fetchEnnoiaDesires(): Promise<Desire[]> {
  const res = await fetch(`${API_BASE}/api/ennoia/desires`)
  if (!res.ok) throw new Error(`GET /api/ennoia/desires -> ${res.status}`)
  const data = await res.json()
  return data.desires
}

export async function fetchEnnoiaActivities(): Promise<Activity[]> {
  const res = await fetch(`${API_BASE}/api/ennoia/activity-pool`)
  if (!res.ok) throw new Error(`GET /api/ennoia/activity-pool -> ${res.status}`)
  const data = await res.json()
  return data.activities
}
