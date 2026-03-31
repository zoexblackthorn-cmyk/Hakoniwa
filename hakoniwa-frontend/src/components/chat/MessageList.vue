<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
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
</script>

<template>
  <div ref="listRef" class="message-list">
    <div v-if="chatStore.messages.length === 0" class="empty-state">
      <span class="empty-icon">💬</span>
      <p>和 Ansel 开始聊天吧</p>
    </div>
    <MessageBubble
      v-for="msg in chatStore.messages"
      :key="msg.id"
      :message="msg"
    />
  </div>
</template>

<style scoped lang="scss">
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
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
</style>
