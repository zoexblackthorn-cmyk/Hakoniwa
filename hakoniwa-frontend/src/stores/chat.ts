import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { Message, Attachment } from '@/types/message'
import { sendMessage, retryMessage, editMessage, deleteMessage, batchDeleteMessages } from '@/services/api'
import { getConversations, getConversationMessages, deleteConversation, searchConversationMessages } from '@/services/conversation'

let messageIdCounter = 0
function generateMessageId(): string {
  return `${Date.now()}-${++messageIdCounter}`
}

function generateConversationId(): string {
  return `conv-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

/** 返回 [min, max] 之间的随机整数 */
function randomDelay(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

/** Promise-based delay */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/** 按 --- 分隔符拆分 LLM 回复为多个气泡
 * 兼容：\n---\n、\r\n---\r\n、前后有空格等情况
 */
function splitBubbles(text: string): string[] {
  const parts = text.split(/\r?\n\s*---\s*\r?\n/).map(s => s.trim()).filter(Boolean)
  return parts.length > 0 ? parts : [text]
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const conversationId = ref<string | null>(null)

  // ═══ 聊天节奏状态 ═══
  /** 'idle' | 'read' | 'typing' — 安安当前的状态，驱动 UI */
  const typingStatus = ref<'idle' | 'read' | 'typing'>('idle')

  // ═══ 消息管理状态 ═══
  const isMultiSelectMode = ref(false)
  const selectedMessageIds = ref<Set<string>>(new Set())
  const isSearchMode = ref(false)
  const searchResults = ref<Message[]>([])
  const searchKeyword = ref('')
  const highlightDbMessageId = ref<number | null>(null)

  // ═══ 新增：Debounce 机制 ═══
  let pendingTexts: string[] = []
  let pendingAttachments: Attachment[] = []
  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  const DEBOUNCE_MS = 6000 // 用户停止发送 6 秒后触发

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

  // ═══ 消息管理方法 ═══

  function enterMultiSelectMode() {
    isMultiSelectMode.value = true
    selectedMessageIds.value.clear()
  }

  function exitMultiSelectMode() {
    isMultiSelectMode.value = false
    selectedMessageIds.value.clear()
  }

  function toggleMessageSelection(messageId: string) {
    if (selectedMessageIds.value.has(messageId)) {
      selectedMessageIds.value.delete(messageId)
    } else {
      selectedMessageIds.value.add(messageId)
    }
  }

  function isMessageSelected(messageId: string): boolean {
    return selectedMessageIds.value.has(messageId)
  }

  async function batchDeleteSelected() {
    const ids = Array.from(selectedMessageIds.value)
    if (ids.length === 0) return

    // 收集需要删除的数据库 ID
    const dbIds: number[] = []
    const frontendIds = new Set<string>()

    for (const id of ids) {
      const msg = messages.value.find(m => m.id === id)
      if (msg) {
        frontendIds.add(id)
        if (msg.dbMessageId && !dbIds.includes(msg.dbMessageId)) {
          dbIds.push(msg.dbMessageId)
        }
      }
    }

    // 先删数据库
    if (dbIds.length > 0) {
      try {
        await batchDeleteMessages(dbIds)
      } catch (e) {
        error.value = e instanceof Error ? e.message : '批量删除失败'
        return
      }
    }

    // 再删前端
    messages.value = messages.value.filter(m => !frontendIds.has(m.id))
    exitMultiSelectMode()
  }

  async function deleteSingleMessage(messageId: string) {
    const msg = messages.value.find(m => m.id === messageId)
    if (!msg) return

    if (msg.dbMessageId) {
      try {
        await deleteMessage(msg.dbMessageId)
      } catch (e) {
        error.value = e instanceof Error ? e.message : '删除失败'
        return
      }
    }

    const idx = messages.value.findIndex(m => m.id === messageId)
    if (idx !== -1) {
      messages.value.splice(idx, 1)
    }
  }

  function enterSearchMode() {
    isSearchMode.value = true
    searchResults.value = []
  }

  function exitSearchMode() {
    isSearchMode.value = false
    searchResults.value = []
  }

  async function searchMessages(keyword?: string, messageType?: string, date?: string) {
    if (!conversationId.value) return
    isLoading.value = true
    searchKeyword.value = keyword || ''
    try {
      const results = await searchConversationMessages(conversationId.value, {
        keyword,
        messageType,
        date
      })
      const mapped: Message[] = []
      for (const m of results) {
        const ts = new Date(m.timestamp)
        if (m.role === 'assistant') {
          // assistant 搜索结果：取第一个气泡展示，避免显示 raw ---
          const bubbles = splitBubbles(m.content)
          mapped.push({
            id: `search-${m.id}`,
            role: 'assistant',
            content: bubbles[0] || m.content,
            timestamp: ts,
            status: 'sent',
            dbMessageId: m.id,
            messageType: (m.message_type as any) || 'text',
          })
        } else {
          mapped.push({
            id: `search-${m.id}`,
            role: m.role as 'user' | 'assistant',
            content: m.content,
            timestamp: ts,
            status: 'sent',
            dbMessageId: m.id,
            messageType: (m.message_type as any) || 'text',
          })
        }
      }
      searchResults.value = mapped
    } catch (e) {
      error.value = e instanceof Error ? e.message : '搜索失败'
    } finally {
      isLoading.value = false
    }
  }

  function setHighlightDbMessageId(id: number | null) {
    highlightDbMessageId.value = id
  }

  /**
   * 用户发送消息 — 立即显示气泡，但延迟发给 LLM
   * 连续发送的多条消息会被合并
   */
  function sendUserMessage(content: string, attachments?: Attachment[]) {
    // 1. 确保有 conversation_id
    if (!conversationId.value) {
      conversationId.value = generateConversationId()
    }

    // 2. 立即显示用户气泡
    addMessage(content, 'user', 'sent', attachments)

    // 3. 累积待发送内容
    pendingTexts.push(content)
    if (attachments) {
      pendingAttachments.push(...attachments)
    }

    // 4. 重置 debounce 计时器
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }
    debounceTimer = setTimeout(() => {
      flushMessages()
    }, DEBOUNCE_MS)
  }

  /**
   * Debounce 触发：合并消息 → 并行发 API + 延迟编排 → 拆气泡显示
   */
  async function flushMessages() {
    debounceTimer = null
    if (pendingTexts.length === 0) return

    const combinedText = pendingTexts.join('\n')
    const allAttachments = [...pendingAttachments]
    pendingTexts = []
    pendingAttachments = []

    isLoading.value = true
    error.value = null

    // 并行：API 调用 + 延迟编排
    const apiPromise = sendMessage({
      message: combinedText,
      conversation_id: conversationId.value || undefined,
      attachments: allAttachments.length > 0
        ? allAttachments.map(a => a.url)
        : undefined
    })

    const typingDelay = randomDelay(1000, 3000)

    // 用于追踪 typing 占位气泡
    let typingMsgId: string | null = null

    function showTypingBubble() {
      const msg = addMessage('', 'assistant', 'typing')
      typingMsgId = msg.id
    }

    function removeTypingBubble() {
      if (typingMsgId) {
        const idx = messages.value.findIndex(m => m.id === typingMsgId)
        if (idx !== -1) {
          messages.value.splice(idx, 1)
        }
        typingMsgId = null
      }
    }

    try {
      // 阶段 1：「已读」（立即）
      typingStatus.value = 'read'
      markUserMessagesRead()

      // 阶段 2：显示 typing 气泡（脉冲圆点）
      await delay(typingDelay)
      typingStatus.value = 'typing'
      showTypingBubble()

      // 阶段 3：等 API 返回
      const response = await apiPromise

      // 阶段 4：拆分气泡，逐个显示
      const bubbles = splitBubbles(response.content)

      // 第一个气泡：移除 typing 占位，显示真实内容
      removeTypingBubble()
      typingStatus.value = 'idle'
      const firstBubble = addMessage(bubbles[0], 'assistant', 'sent')
      // 记录数据库消息 ID
      const dbId = response.db_message_id ?? undefined
      if (dbId) firstBubble.dbMessageId = dbId

      // 后续气泡：每个前面都先显示一会儿 typing 气泡
      for (let i = 1; i < bubbles.length; i++) {
        const bubble = bubbles[i]
        const typeTime = bubble.length * randomDelay(60, 100) + randomDelay(800, 1500)
        const clampedDelay = Math.min(typeTime, 5000)

        typingStatus.value = 'typing'
        showTypingBubble()
        await delay(clampedDelay)

        removeTypingBubble()
        typingStatus.value = 'idle'
        const newBubble = addMessage(bubble, 'assistant', 'sent')
        if (dbId) newBubble.dbMessageId = dbId
      }

    } catch (e) {
      removeTypingBubble()
      typingStatus.value = 'idle'
      addMessage('发送失败，请重试', 'assistant', 'error')
      error.value = e instanceof Error ? e.message : '未知错误'
    } finally {
      isLoading.value = false
      typingStatus.value = 'idle'
    }
  }

  /** 将最近的用户消息标记为 read */
  function markUserMessagesRead() {
    // 从末尾向前找所有连续的用户消息，标记为 read
    for (let i = messages.value.length - 1; i >= 0; i--) {
      const msg = messages.value[i]
      if (msg.role === 'user' && msg.status === 'sent') {
        msg.status = 'read'
      } else if (msg.role === 'assistant') {
        break 
      }
    }
  }


  async function loadRecentConversation() {
    isLoading.value = true
    try {
      const conversations = await getConversations()
      if (conversations.length > 0) {
        const recentConv = conversations[0]
        conversationId.value = recentConv.conversation_id

        const dbMessages = await getConversationMessages(recentConv.conversation_id)
const result: Message[] = []
for (const m of dbMessages) {
  const attachments = (() => {
    if (!m.metadata) return undefined
    try {
      return JSON.parse(m.metadata)?.attachments
    } catch {
      return undefined
    }
  })()
  const ts = new Date(m.timestamp)

  if (m.role === 'assistant') {
    // assistant 消息：按 --- 拆分成多个气泡
    const bubbles = splitBubbles(m.content)
    for (const bubble of bubbles) {
      result.push({
        id: generateMessageId(),
        role: 'assistant',
        content: bubble,
        timestamp: ts,
        status: 'sent',
      })
    }
  } else {
    result.push({
      id: m.id.toString(),
      role: m.role as 'user' | 'assistant',
      content: m.content,
      timestamp: ts,
      status: 'sent',
      attachments,
    })
  }
}
messages.value = result
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
      const fromTime = `${date}T00:00:00`
      const dbMessages = await getConversationMessages(conversationId.value, fromTime)
      const result: Message[] = []
      for (const m of dbMessages) {
        const attachments = (() => {
          if (!m.metadata) return undefined
          try {
            return JSON.parse(m.metadata)?.attachments
          } catch {
            return undefined
          }
        })()
        const ts = new Date(m.timestamp)

        if (m.role === 'assistant') {
          const bubbles = splitBubbles(m.content)
          for (const bubble of bubbles) {
            result.push({
              id: generateMessageId(),
              role: 'assistant',
              content: bubble,
              timestamp: ts,
              status: 'sent',
              dbMessageId: m.id,
              messageType: (m.message_type as any) || 'text',
            })
          }
        } else {
          result.push({
            id: m.id.toString(),
            role: m.role as 'user' | 'assistant',
            content: m.content,
            timestamp: ts,
            status: 'sent',
            attachments,
            dbMessageId: m.id,
            messageType: (m.message_type as any) || 'text',
          })
        }
      }
      messages.value = result
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
      localStorage.removeItem(`chat-bg-${conversationId.value}`)
      messages.value = []
      conversationId.value = null
    } catch (e) {
      error.value = e instanceof Error ? e.message : '删除失败'
    }
  }

  function clearMessages() {
    messages.value = []
    conversationId.value = null
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    pendingTexts = []
    pendingAttachments = []
    typingStatus.value = 'idle'
  }

  /**
   * 重试：删除最后一组 assistant 气泡，重新请求 LLM
   */
  async function retryLastAssistant() {
    if (!conversationId.value) return

    // 从末尾往前删除所有连续的 assistant 气泡
    while (messages.value.length > 0) {
      const last = messages.value[messages.value.length - 1]
      if (last.role === 'assistant') {
        messages.value.pop()
      } else {
        break
      }
    }

    isLoading.value = true
    error.value = null
    typingStatus.value = 'typing'

    // 显示 typing 气泡
    const typingMsg = addMessage('', 'assistant', 'typing')

    try {
      const response = await retryMessage(conversationId.value)
      const bubbles = splitBubbles(response.content)
      const dbId = response.db_message_id ?? undefined

      // 移除 typing 占位
      const idx = messages.value.findIndex(m => m.id === typingMsg.id)
      if (idx !== -1) messages.value.splice(idx, 1)

      typingStatus.value = 'idle'

      // 第一个气泡
      const first = addMessage(bubbles[0], 'assistant', 'sent')
      if (dbId) first.dbMessageId = dbId

      // 后续气泡（带节奏）
      for (let i = 1; i < bubbles.length; i++) {
        const bubble = bubbles[i]
        const typeTime = bubble.length * randomDelay(60, 100) + randomDelay(800, 1500)
        typingStatus.value = 'typing'
        const typingBubble = addMessage('', 'assistant', 'typing')
        await delay(Math.min(typeTime, 5000))
        const tIdx = messages.value.findIndex(m => m.id === typingBubble.id)
        if (tIdx !== -1) messages.value.splice(tIdx, 1)
        typingStatus.value = 'idle'
        const b = addMessage(bubble, 'assistant', 'sent')
        if (dbId) b.dbMessageId = dbId
      }
    } catch (e) {
      // 移除 typing 占位
      const idx = messages.value.findIndex(m => m.id === typingMsg.id)
      if (idx !== -1) messages.value.splice(idx, 1)
      typingStatus.value = 'idle'
      addMessage('重试失败，请再试一次', 'assistant', 'error')
      error.value = e instanceof Error ? e.message : '重试失败'
    } finally {
      isLoading.value = false
      typingStatus.value = 'idle'
    }
  }

  /**
   * 编辑气泡：更新前端显示 + 持久化到数据库
   */
  async function editBubble(messageId: string, newContent: string) {
    // 1. 在前端更新这个气泡的内容
    const msg = messages.value.find(m => m.id === messageId)
    if (!msg) return

    const oldContent = msg.content
    msg.content = newContent

    // 2. 如果有 dbMessageId，持久化到数据库
    if (msg.dbMessageId) {
      try {
        // 找到所有同一个 dbMessageId 的气泡，合并成完整消息
        const siblings = messages.value.filter(
          m => m.dbMessageId === msg.dbMessageId && m.role === 'assistant'
        )
        const fullContent = siblings.map(s => s.content).join('\n---\n')
        await editMessage(msg.dbMessageId, fullContent)
      } catch (e) {
        // 持久化失败，回退显示
        msg.content = oldContent
        error.value = e instanceof Error ? e.message : '编辑保存失败'
      }
    }
  }

  return {
    messages,
    isLoading,
    error,
    conversationId,
    typingStatus,
    isMultiSelectMode,
    selectedMessageIds,
    isSearchMode,
    searchResults,
    addMessage,
    sendUserMessage,
    loadRecentConversation,
    loadMessagesFromDate,
    deleteCurrentConversation,
    clearMessages,
    retryLastAssistant,
    editBubble,
    enterMultiSelectMode,
    exitMultiSelectMode,
    toggleMessageSelection,
    isMessageSelected,
    batchDeleteSelected,
    deleteSingleMessage,
    enterSearchMode,
    exitSearchMode,
    searchMessages,
    searchKeyword,
    highlightDbMessageId,
    setHighlightDbMessageId,
  }
})
