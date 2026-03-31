const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export interface Conversation {
  id: number
  conversation_id: string
  title: string
  created_at: string
  updated_at: string
}

export interface ConversationMessage {
  id: number
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  metadata: string | null
}

// 获取对话列表
export async function getConversations(): Promise<Conversation[]> {
  const res = await fetch(`${API_BASE}/api/conversations`)
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  const data = await res.json()
  return data.conversations
}

// 获取对话消息
export async function getConversationMessages(
  conversationId: string,
  fromTime?: string
): Promise<ConversationMessage[]> {
  let url = `${API_BASE}/api/conversation/${encodeURIComponent(conversationId)}/messages`
  if (fromTime) {
    url += `?from_time=${encodeURIComponent(fromTime)}`
  }
  const res = await fetch(url)
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  const data = await res.json()
  return data.messages
}

// 获取有聊天记录的日期列表
export async function getConversationDates(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/conversation/dates`)
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  const data = await res.json()
  return data.dates
}

// 批量删除对话
export async function deleteConversations(ids: string[]): Promise<{ success: boolean; deleted: number }> {
  const res = await fetch(`${API_BASE}/api/conversations`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids })
  })
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  return res.json()
}

// 删除单条对话
export async function deleteConversation(id: string): Promise<{ success: boolean; deleted: number }> {
  return deleteConversations([id])
}
