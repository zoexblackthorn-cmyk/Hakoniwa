import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { Message, Attachment } from '@/types/message'
import { sendMessage } from '@/services/api'
import { getConversations, getConversationMessages, deleteConversation } from '@/services/conversation'

let messageIdCounter = 0
function generateMessageId(): string {
  return `${Date.now()}-${++messageIdCounter}`
}

function generateConversationId(): string {
  return `conv-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const conversationId = ref<string | null>(null)

  function addMessage(
    content: string,
    role: 'user' | 'assistant',
    status: Message['status'] = 'sent',
    attachments?: Attachment[]
  ) {
    const newMessage: Message = {
      id: generateMessageId(),
      role,
      content,
      timestamp: new Date(),
      status,
      attachments
    }
    messages.value.push(newMessage)
    return newMessage
  }

  async function sendUserMessage(content: string, attachments?: Attachment[]) {
    // 1. 确保有 conversation_id
    if (!conversationId.value) {
      conversationId.value = generateConversationId()
    }

    // 2. 添加用户消息
    addMessage(content, 'user', 'sent', attachments)

    // 3. 添加 loading 占位消息
    const loadingMsg = addMessage('', 'assistant', 'sending')
    isLoading.value = true
    error.value = null

    try {
      // 4. 调用 API
      const response = await sendMessage({
        message: content,
        conversation_id: conversationId.value || undefined
      })

      // 5. 更新占位消息为真实回复
      const idx = messages.value.findIndex(m => m.id === loadingMsg.id)
      if (idx !== -1) {
        messages.value[idx] = {
          id: response.id,
          role: 'assistant',
          content: response.content,
          timestamp: new Date(response.timestamp),
          status: 'sent'
        }
      }

    } catch (e) {
      // 6. 错误处理：移除 loading 消息，显示错误
      const idx = messages.value.findIndex(m => m.id === loadingMsg.id)
      if (idx !== -1) {
        messages.value[idx].content = '发送失败，请重试'
        messages.value[idx].status = 'error'
      }
      error.value = e instanceof Error ? e.message : '未知错误'
    } finally {
      isLoading.value = false
    }
  }

  // 加载最近的对话（用于页面刷新后恢复）
  async function loadRecentConversation() {
    isLoading.value = true
    try {
      // 获取最近的对话
      const conversations = await getConversations()
      if (conversations.length > 0) {
        const recentConv = conversations[0]
        conversationId.value = recentConv.conversation_id
        
        // 加载该对话的所有消息
        const dbMessages = await getConversationMessages(recentConv.conversation_id)
        messages.value = dbMessages.map(m => ({
          id: m.id.toString(),
          role: m.role as 'user' | 'assistant',
          content: m.content,
          timestamp: new Date(m.timestamp),
          status: 'sent' as const
        }))
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载历史消息失败'
    } finally {
      isLoading.value = false
    }
  }

  async function loadMessagesFromDate(date: string) {
    if (!conversationId.value) return
    
    isLoading.value = true
    try {
      // 从指定日期的 00:00:00 开始加载
      const fromTime = `${date}T00:00:00`
      const dbMessages = await getConversationMessages(conversationId.value, fromTime)
      
      // 转换为前端 Message 格式
      messages.value = dbMessages.map(m => ({
        id: m.id.toString(),
        role: m.role as 'user' | 'assistant',
        content: m.content,
        timestamp: new Date(m.timestamp),
        status: 'sent' as const
      }))
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载消息失败'
    } finally {
      isLoading.value = false
    }
  }

  async function deleteCurrentConversation() {
    if (!conversationId.value) return
    
    try {
      await deleteConversation(conversationId.value)
      // 清除 localStorage 中的背景图
      localStorage.removeItem(`chat-bg-${conversationId.value}`)
      // 清空当前状态
      messages.value = []
      conversationId.value = null
    } catch (e) {
      error.value = e instanceof Error ? e.message : '删除失败'
    }
  }

  function clearMessages() {
    messages.value = []
    conversationId.value = null
  }

  return {
    messages,
    isLoading,
    error,
    conversationId,
    addMessage,
    sendUserMessage,
    loadRecentConversation,
    loadMessagesFromDate,
    deleteCurrentConversation,
    clearMessages
  }
})
