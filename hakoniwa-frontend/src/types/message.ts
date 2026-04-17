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
  status?: 'sending' | 'sent' | 'error'
  attachments?: Attachment[]
}
