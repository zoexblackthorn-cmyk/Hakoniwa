const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export interface ChatRequest {
  message: string
  conversation_id?: string
  attachments?: string[]
}

export interface ChatResponse {
  id: string
  role: 'assistant'
  content: string
  timestamp: string
}

export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  })

  if (!res.ok) {
    throw new Error(`API Error: ${res.status}`)
  }

  return res.json()
}

// 健康检查
export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`)
    return res.ok
  } catch {
    return false
  }
}
