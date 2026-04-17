const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'

export interface UserProfile {
  id: number
  name: string
  status_line: string
  avatar_path: string
  mask: string
  profession: string
  personalization: string
  updated_at: string
}

export async function getUserProfile(): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/api/user`)
  if (!res.ok) throw new Error(`GET /api/user -> ${res.status}`)
  return res.json()
}

export async function updateUserProfile(data: Partial<UserProfile>): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/api/user`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!res.ok) throw new Error(`PUT /api/user -> ${res.status}`)
  return res.json()
}
