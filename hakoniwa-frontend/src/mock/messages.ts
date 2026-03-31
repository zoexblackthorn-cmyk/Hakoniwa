import type { Message } from '@/types/message'

export const mockMessages: Message[] = [
  {
    id: '1',
    role: 'assistant',
    content: '早上好，今天感觉怎么样？',
    timestamp: new Date('2024-01-15T08:00:00')
  },
  {
    id: '2',
    role: 'user',
    content: '还好～有点困',
    timestamp: new Date('2024-01-15T08:01:00')
  },
  {
    id: '3',
    role: 'assistant',
    content: '要不要我给你放点轻音乐？🎵',
    timestamp: new Date('2024-01-15T08:01:30')
  }
]
