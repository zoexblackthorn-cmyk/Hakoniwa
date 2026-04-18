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
  message_type?: string
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

// 获取有聊天记录的日期列表（全局）
export async function getConversationDates(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/conversation/dates`)
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  const data = await res.json()
  return data.dates
}

// 获取某对话有消息的日期列表
export async function getConversationMessageDates(conversationId: string): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/conversation/${encodeURIComponent(conversationId)}/dates`)
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  const data = await res.json()
  return data.dates
}

// 搜索对话消息
export async function searchConversationMessages(
  conversationId: string,
  options: { keyword?: string; messageType?: string; date?: string } = {}
): Promise<ConversationMessage[]> {
  const params = new URLSearchParams()
  if (options.keyword) params.append('keyword', options.keyword)
  if (options.messageType) params.append('message_type', options.messageType)
  if (options.date) params.append('date', options.date)
  const url = `${API_BASE}/api/conversation/${encodeURIComponent(conversationId)}/search?${params.toString()}`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  const data = await res.json()
  return data.messages
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

// 清空某对话的所有消息
export async function clearConversationMessages(conversationId: string): Promise<{ success: boolean; deleted: number }> {
  const res = await fetch(`${API_BASE}/api/conversation/${encodeURIComponent(conversationId)}/messages`, {
    method: 'DELETE'
  })
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  return res.json()
}
