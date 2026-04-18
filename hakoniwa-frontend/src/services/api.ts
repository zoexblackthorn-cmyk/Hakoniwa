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
  db_message_id?: number    // 新增
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

// 重试最后一条 AI 回复
export async function retryMessage(conversationId: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat/retry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId })
  })

  if (!res.ok) {
    throw new Error(`Retry Error: ${res.status}`)
  }

  return res.json()
}

// 编辑一条消息
export async function editMessage(messageId: number, content: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/conversation/message/${messageId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content })
  })

  if (!res.ok) {
    throw new Error(`Edit Error: ${res.status}`)
  }
}

// 删除单条消息
export async function deleteMessage(messageId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/message/${messageId}`, {
    method: 'DELETE'
  })
  if (!res.ok) {
    throw new Error(`Delete Error: ${res.status}`)
  }
}

// 批量删除消息
export async function batchDeleteMessages(messageIds: number[]): Promise<{ success: boolean; deleted: number }> {
  const res = await fetch(`${API_BASE}/api/messages`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids: messageIds })
  })
  if (!res.ok) {
    throw new Error(`Batch Delete Error: ${res.status}`)
  }
  return res.json()
}
