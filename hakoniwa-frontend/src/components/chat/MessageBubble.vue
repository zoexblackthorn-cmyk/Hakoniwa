<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Message } from '@/types/message'
import { RotateCcw, Copy, Edit3, Trash2, CheckSquare } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'

const props = defineProps<{
  message: Message
}>()

const emit = defineEmits<{
  'open-action-menu': [message: Message, x: number, y: number]
  'toggle-select': [messageId: string]
}>()

const chatStore = useChatStore()
const isEditing = ref(false)
const editText = ref('')
const isAssistant = props.message.role === 'assistant'

const isSelected = computed(() => chatStore.isMessageSelected(props.message.id))

const hasAttachments = computed(() => {
  const a = (props.message as any).attachments
  return Array.isArray(a) && a.length > 0
})

const normalizedAttachments = computed(() => {
  const a = (props.message as any).attachments
  if (!Array.isArray(a)) return []
  return a.map((att: any, i: number) => {
    if (typeof att === 'string') {
      return { url: att, name: '', key: `${i}-${att.slice(0, 20)}` }
    }
    return {
      url: att.url || '',
      name: att.name || '',
      key: `${i}-${(att.url || '').slice(0, 20)}`
    }
  })
})

function onCopy() {
  navigator.clipboard.writeText(props.message.content)
}

function onRegenerate() {
  chatStore.retryLastAssistant()
}

function onEdit() {
  editText.value = props.message.content
  isEditing.value = true
}

function onEditSave() {
  if (editText.value.trim()) {
    chatStore.editBubble(props.message.id, editText.value.trim())
  }
  isEditing.value = false
}

function onEditCancel() {
  isEditing.value = false
}

function onDelete() {
  chatStore.deleteSingleMessage(props.message.id)
}

function onContextMenu(e: MouseEvent) {
  e.preventDefault()
  if (chatStore.isMultiSelectMode) return
  emit('open-action-menu', props.message, e.clientX, e.clientY)
}

let longPressTimer: ReturnType<typeof setTimeout> | null = null

function onTouchStart(e: TouchEvent) {
  if (chatStore.isMultiSelectMode) return
  longPressTimer = setTimeout(() => {
    const touch = e.touches[0]
    emit('open-action-menu', props.message, touch.clientX, touch.clientY)
  }, 600)
}

function onTouchEnd() {
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

function onTouchMove() {
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

function onBubbleClick() {
  if (chatStore.isMultiSelectMode) {
    emit('toggle-select', props.message.id)
  }
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
  <div
    class="message-row"
    :class="[isAssistant ? 'left' : 'right', { 'select-mode': chatStore.isMultiSelectMode }]"
    @contextmenu="onContextMenu"
    @touchstart="onTouchStart"
    @touchend="onTouchEnd"
    @touchmove="onTouchMove"
  >
    <!-- 多选复选框 -->
    <div
      v-if="chatStore.isMultiSelectMode && message.status !== 'typing' && message.status !== 'sending'"
      class="select-checkbox"
      :class="{ checked: isSelected }"
      @click.stop="emit('toggle-select', message.id)"
    >
      <CheckSquare v-if="isSelected" :size="18" />
      <div v-else class="checkbox-empty" />
    </div>

    <div class="bubble-wrapper" @click.stop="onBubbleClick">
      <div
        class="bubble"
        :class="[message.role, message.status, { 'selectable': chatStore.isMultiSelectMode }]"
      >
        <p v-if="message.status === 'typing'" class="content typing-dot-wrap">
          <span class="typing-dot"></span>
        </p>
        <p v-else-if="message.status === 'sending'" class="content loading-dots">
          <span></span><span></span><span></span>
        </p>
        <div v-else-if="isEditing" class="edit-area">
          <textarea v-model="editText" class="edit-input" rows="3"></textarea>
          <div class="edit-actions">
            <button class="edit-btn save" @click="onEditSave">保存</button>
            <button class="edit-btn cancel" @click="onEditCancel">取消</button>
          </div>
        </div>
        <p v-else-if="message.content" class="content">{{ message.content }}</p>
        <div v-if="hasAttachments" class="attachments">
          <img
            v-for="att in normalizedAttachments"
            :key="att.key"
            :src="att.url"
            :alt="att.name"
            class="attachment-img"
          />
        </div>
      </div>
      <!-- meta-row: purely visual wrapper keeping time + actions on one line -->
      <div class="meta-row">
        <span v-if="!isAssistant && message.status === 'read'" class="read-mark">已读</span>
        <span class="time">{{ formatTime(message.timestamp) }}</span>
        <!-- 悬停操作栏（仅 assistant） -->
        <div v-if="isAssistant && message.status === 'sent' && !chatStore.isMultiSelectMode" class="actions">
          <button class="action-btn" title="重新生成" @click="onRegenerate">
            <RotateCcw :size="14" />
          </button>
          <button class="action-btn" title="复制全部" @click="onCopy">
            <Copy :size="14" />
          </button>
          <button class="action-btn" title="编辑" @click="onEdit">
            <Edit3 :size="14" />
          </button>
          <button class="action-btn" title="删除" @click="onDelete">
            <Trash2 :size="14" />
          </button>
        </div>
      </div>
    </div>
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

  &.select-mode {
    padding-left: 4px;
  }
}

/* Hide the side avatars — the design shows bubbles only,
   with a single centered character avatar in the header */
.message-row :deep(.avatar) {
  display: none;
}

.select-checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  color: #7ab8d6;
  cursor: pointer;
  margin-bottom: 20px;

  .checkbox-empty {
    width: 18px;
    height: 18px;
    border: 2px solid #c0d8e8;
    border-radius: 50%;
    transition: all 0.2s;
  }

  &:hover .checkbox-empty {
    border-color: #7ab8d6;
  }

  &.checked {
    color: #4a9fd4;
  }
}

.bubble-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 74%;
}
.message-row.left .bubble-wrapper {
  align-items: flex-start;
}

.message-row.right .bubble-wrapper {
  align-items: flex-end;
}

.bubble {
  padding: 10px 16px;
  border-radius: 22px;
  border: none;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
  min-width: 20px;
  box-shadow: 0 2px 10px rgba(120, 170, 210, 0.12);
  transition: transform 0.15s, box-shadow 0.15s;

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

  &.selectable {
    cursor: pointer;

    &:hover {
      box-shadow: 0 4px 16px rgba(120, 170, 210, 0.22);
    }
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
  min-width: 80px;
  min-height: 80px;
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

.message-row.left .meta-row {
  flex-direction: row;
  justify-content: flex-start;
}

.message-row.right .meta-row {
  flex-direction: row-reverse;
  justify-content: flex-start;
}

.read-mark {
  font-size: 11px;
  color: #7ab8d6;
  font-weight: 500;
}

.time {
  font-size: 11px;
  color: rgba(74, 106, 128, 0.65);
  font-weight: 500;
  letter-spacing: 0.02em;
}

/* ---- 编辑区域 ---- */
.edit-area {
  width: 100%;
}

.edit-input {
  width: 100%;
  min-height: 60px;
  padding: 8px;
  border: 1.5px solid #a8c8dc;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  line-height: 1.5;
  color: #3a5a70;
  resize: vertical;
  outline: none;
  font-family: inherit;
  box-sizing: border-box;

  &:focus {
    border-color: #7ab8d6;
  }
}

.edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 6px;
  justify-content: flex-end;
}

.edit-btn {
  padding: 4px 14px;
  border-radius: 6px;
  border: none;
  font-size: 12px;
  cursor: pointer;
  font-family: inherit;

  &.save {
    background: #9AC9FF;
    color: #2f4f68;
  }
  &.save:hover {
    background: #7ab8f0;
  }

  &.cancel {
    background: #e8e8e8;
    color: #666;
  }
  &.cancel:hover {
    background: #d8d8d8;
  }
}

/* typing 脉冲圆点 */
.typing-dot-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  min-height: 1.2em;
  padding: 2px 0;
}

.typing-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #FFFFFF;
  animation: slow-pulse 2s ease-in-out infinite;
}

@keyframes slow-pulse {
  0%, 100% {
    opacity: 0.25;
    transform: scale(0.85);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
