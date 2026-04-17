<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import type { Message } from '@/types/message'
import MessageBubble from './MessageBubble.vue'

const chatStore = useChatStore()
const listRef = ref<HTMLElement | null>(null)

// 消息变化时自动滚动到底部
watch(
  () => chatStore.messages.length,
  async () => {
    await nextTick()
    if (listRef.value) {
      listRef.value.scrollTo({
        top: listRef.value.scrollHeight,
        behavior: 'smooth'
      })
    }
  }
)

interface GroupedItem {
  type: 'date' | 'message'
  date?: Date
  label?: string
  message?: Message
}

const groupedItems = computed<GroupedItem[]>(() => {
  const items: GroupedItem[] = []
  let lastDateLabel = ''

  for (const msg of chatStore.messages) {
    const label = formatDateLabel(msg.timestamp)
    if (label !== lastDateLabel) {
      items.push({ type: 'date', label, date: msg.timestamp })
      lastDateLabel = label
    }
    items.push({ type: 'message', message: msg })
  }

  return items
})

function formatDateLabel(date: Date): string {
  const now = new Date()
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (d.getTime() === today.getTime()) return 'Today'
  if (d.getTime() === yesterday.getTime()) return 'Yesterday'
  return `${d.getMonth() + 1}月${d.getDate()}日`
}
</script>

<template>
  <div ref="listRef" class="message-list">
    <div v-if="chatStore.messages.length === 0" class="empty-state">
      <span class="empty-icon">💬</span>
      <p>和 Ansel 开始聊天吧</p>
    </div>
    <template v-else>
      <template v-for="(item, index) in groupedItems" :key="index">
        <div v-if="item.type === 'date'" class="date-divider">
          <span class="date-pill">{{ item.label }}</span>
        </div>
        <MessageBubble
          v-else-if="item.message"
          :message="item.message"
        />
      </template>
    </template>
  </div>
</template>

<style scoped lang="scss">
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 18px 12px;
  display: flex;
  flex-direction: column;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9bb8cc;

  .empty-icon {
    font-size: 48px;
    margin-bottom: 12px;
  }

  p {
    font-size: 14px;
    margin: 0;
  }
}

.date-divider {
  display: flex;
  justify-content: center;
  margin: 14px 0;
}

.date-pill {
  background: #ffffff;
  color: #5E7E93;
  font-size: 13px;
  font-weight: 700;
  padding: 7px 22px;
  border-radius: 999px;
  box-shadow: 0 3px 10px rgba(120, 170, 210, 0.15);
  letter-spacing: 0.02em;
}
</style>
