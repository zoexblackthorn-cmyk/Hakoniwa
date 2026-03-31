<script setup lang="ts">
import type { Message } from '@/types/message'
import Avatar from './Avatar.vue'

const props = defineProps<{
  message: Message
}>()

const isAssistant = props.message.role === 'assistant'
</script>

<template>
  <div class="message-row" :class="isAssistant ? 'left' : 'right'">
    <Avatar v-if="isAssistant" :role="message.role" />
    <div class="bubble-wrapper">
      <div class="bubble" :class="[message.role, message.status]">
        <p v-if="message.status === 'sending'" class="content loading-dots">
          <span></span><span></span><span></span>
        </p>
        <p v-else class="content">{{ message.content }}</p>
      </div>
      <span class="time">{{ message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}</span>
    </div>
    <Avatar v-if="!isAssistant" :role="message.role" />
  </div>
</template>

<style scoped lang="scss">
.message-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-bottom: 16px;

  &.left {
    justify-content: flex-start;
  }

  &.right {
    justify-content: flex-end;
  }
}

.bubble-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 70%;

  .left & {
    align-items: flex-start;
  }

  .right & {
    align-items: flex-end;
  }
}

.bubble {
  padding: 10px 14px;
  border-radius: 14px;
  border: 2px solid;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;

  &.assistant {
    background: #ffffff;
    border-color: #d0e6f4;
    color: #4a6a80;
    border-bottom-left-radius: 4px;
  }

  &.user {
    background: #e8f4fc;
    border-color: #c8dff0;
    color: #3a5a70;
    border-bottom-right-radius: 4px;
  }

  &.sending {
    opacity: 0.7;
  }

  &.error {
    border-color: #f5a0a0;
    background: #fff5f5;
    color: #c55;
  }
}

.content {
  margin: 0;
}

.loading-dots {
  display: flex;
  align-items: center;
  gap: 3px;
  min-width: 24px;
  min-height: 1em;

  span {
    width: 5px;
    height: 5px;
    background: currentColor;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;

    &:nth-child(1) {
      animation-delay: -0.32s;
    }

    &:nth-child(2) {
      animation-delay: -0.16s;
    }
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.time {
  font-size: 11px;
  color: #9bb8cc;
}
</style>
