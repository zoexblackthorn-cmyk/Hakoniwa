export type MessageType = 'text' | 'image' | 'file' | 'link'

export interface Attachment {
  type: 'image'
  url: string
  name: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  status?: 'sending' | 'sent' | 'read' | 'typing' | 'error'
  attachments?: Attachment[]
  dbMessageId?: number      // 数据库中的消息 ID，用于编辑和重试
  messageType?: MessageType // 消息类型
}
