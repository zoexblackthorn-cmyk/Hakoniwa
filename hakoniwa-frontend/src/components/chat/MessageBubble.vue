<script setup lang="ts">
import type { Message } from '@/types/message'
import Avatar from './Avatar.vue'
import { RotateCcw, Copy, Edit3 } from 'lucide-vue-next'

const props = defineProps<{
  message: Message
}>()

const isAssistant = props.message.role === 'assistant'

function onCopy() {
  navigator.clipboard.writeText(props.message.content)
}

function onRegenerate() {
  // 占位
  console.log('regenerate')
}

function onEdit() {
  // 占位
  console.log('edit')
}

function formatTime(date: Date): string {
  let hours = date.getHours()
  const minutes = date.getMinutes()
  const ampm = hours >= 12 ? 'PM' : 'AM'
  hours = hours % 12
  hours = hours ? hours : 12
  const mm = minutes < 10 ? '0' + minutes : minutes
  return `${hours}.${mm} ${ampm}`
}
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
        <div v-if="message.attachments && message.attachments.length" class="attachments">
          <img
            v-for="att in message.attachments"
            :key="att.url"
            :src="att.url"
            :alt="att.name"
            class="attachment-img"
          />
        </div>
      </div>
      <!-- meta-row: purely visual wrapper keeping time + actions on one line -->
      <div class="meta-row">
        <span class="time">{{ formatTime(message.timestamp) }}</span>
        <!-- 悬停操作栏（仅 assistant） -->
        <div v-if="isAssistant && message.status === 'sent'" class="actions">
          <button class="action-btn" title="重新生成" @click="onRegenerate">
            <RotateCcw :size="14" />
          </button>
          <button class="action-btn" title="复制全部" @click="onCopy">
            <Copy :size="14" />
          </button>
          <button class="action-btn" title="编辑" @click="onEdit">
            <Edit3 :size="14" />
          </button>
        </div>
      </div>
    </div>
    <Avatar v-if="!isAssistant" :role="message.role" />
  </div>
</template>

<style scoped lang="scss">
.message-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-bottom: 14px;

  &.left {
    justify-content: flex-start;
  }

  &.right {
    justify-content: flex-end;
  }
}

/* Hide the side avatars — the design shows bubbles only,
   with a single centered character avatar in the header */
.message-row :deep(.avatar) {
  display: none;
}

.bubble-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 74%;

  .left & {
    align-items: flex-start;
  }

  .right & {
    align-items: flex-end;
  }
}

.bubble {
  padding: 13px 20px;
  border-radius: 22px;
  border: none;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
  min-width: 120px;
  box-shadow: 0 2px 10px rgba(120, 170, 210, 0.12);

  /* assistant bubble — mid blue, slightly deeper */
  &.assistant {
    background: #9AC9FF;
    color: #2f4f68;
    border-bottom-left-radius: 8px;
  }

  /* user bubble — near-white with subtle blue tint */
  &.user {
    background: #FFFFFF;
    color: #3a5a70;
    border-bottom-right-radius: 8px;
  }

  &.sending {
    opacity: 0.75;
  }

  &.error {
    background: #fff5f5;
    color: #c55;
  }
}

.content {
  margin: 0;
}

.attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.attachment-img {
  max-width: 200px;
  max-height: 200px;
  border-radius: 12px;
  object-fit: cover;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
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

    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
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

/* Actions — hover-revealed, rendered inline with timestamp */
.actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.message-row:hover .actions {
  opacity: 1;
  pointer-events: auto;
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  color: #8FB0C6;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 0;

  &:hover { color: #4a7a98; }
}

/* meta-row: flex container keeping time + actions on one baseline */
.meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 4px;
}

.left .meta-row {
  flex-direction: row;          /* time | actions */
  justify-content: flex-start;
}

.right .meta-row {
  flex-direction: row-reverse;  /* (no actions for user) time sits flush right */
  justify-content: flex-start;
}

.time {
  font-size: 11px;
  color: rgba(74, 106, 128, 0.65);
  font-weight: 500;
  letter-spacing: 0.02em;
}
</style>
