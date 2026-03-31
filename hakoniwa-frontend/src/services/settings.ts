const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

import type { Settings, ModelsResponse } from '@/types/settings'

export async function getSettings(): Promise<Settings> {
  const res = await fetch(`${API_BASE}/api/settings`)
  if (!res.ok) {
    throw new Error(`API Error: ${res.status}`)
  }
  return res.json()
}

export async function updateSettings(data: Partial<Settings>): Promise<Settings> {
  const res = await fetch(`${API_BASE}/api/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!res.ok) {
    throw new Error(`API Error: ${res.status}`)
  }
  return res.json()
}

export async function getModels(provider: string): Promise<ModelsResponse> {
  const res = await fetch(`${API_BASE}/api/settings/models?provider=${encodeURIComponent(provider)}`)
  if (!res.ok) {
    throw new Error(`API Error: ${res.status}`)
  }
  return res.json()
}
