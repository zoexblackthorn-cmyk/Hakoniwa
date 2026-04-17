<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import { Paperclip, Mic } from 'lucide-vue-next'
import type { Attachment } from '@/types/message'

const chatStore = useChatStore()
const inputValue = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

function onSend() {
  const text = inputValue.value.trim()
  if ((!text && pendingAttachments.value.length === 0) || chatStore.isLoading) return

  const attachments = pendingAttachments.value.length > 0 ? [...pendingAttachments.value] : undefined
  chatStore.sendUserMessage(text, attachments)
  inputValue.value = ''
  pendingAttachments.value = []
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend()
  }
}

const pendingAttachments = ref<Attachment[]>([])

function onAttachClick() {
  fileInputRef.value?.click()
}

function onFileChange(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files) return

  for (const file of Array.from(files)) {
    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file)
      pendingAttachments.value.push({
        type: 'image',
        url,
        name: file.name
      })
    }
  }

  // 如果有文件且没有输入文字，自动发送
  if (pendingAttachments.value.length > 0 && !inputValue.value.trim()) {
    onSend()
  }

  // 清空 input 以便可以重复选择同一文件
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function removeAttachment(index: number) {
  const att = pendingAttachments.value[index]
  if (att) URL.revokeObjectURL(att.url)
  pendingAttachments.value.splice(index, 1)
}
</script>

<template>
  <div class="chat-input">
    <div class="input-bar">
      <button class="icon-btn attach-btn" title="添加附件" @click="onAttachClick">
        <Paperclip :size="22" />
      </button>
      <textarea
        v-model="inputValue"
        class="input"
        placeholder="Enter Your Message..."
        :disabled="chatStore.isLoading"
        rows="1"
        @keydown="onKeydown"
      />
      <button class="icon-btn mic-btn" title="语音输入（占位）">
        <Mic :size="22" />
      </button>
    </div>

    <!-- 待发送附件预览 -->
    <div v-if="pendingAttachments.length" class="attachment-preview">
      <div v-for="(att, idx) in pendingAttachments" :key="att.url" class="preview-item">
        <img :src="att.url" :alt="att.name" />
        <button class="remove-btn" @click="removeAttachment(idx)">×</button>
      </div>
    </div>

    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      multiple
      class="hidden-input"
      @change="onFileChange"
    />
  </div>
</template>

<style scoped lang="scss">
.chat-input {
  padding: 10px 18px 18px;
  flex-shrink: 0;
}

.input-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #CFE4F1;
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 40px;
  padding: 8px 10px 8px 22px;
  height: 62px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  color: #3a5c74;
  outline: none;
  padding: 8px 0;
  resize: none;
  max-height: 120px;
  line-height: 1.4;
  font-family: inherit;

  &::placeholder {
    color: #7A9BB3;
    font-weight: 500;
  }

  &:disabled {
    opacity: 0.6;
  }
}

.icon-btn {
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s, transform 80ms, box-shadow 0.2s;
  flex-shrink: 0;

  &:active {
    transform: scale(0.94);
  }
}

.attach-btn {
  width: 36px;
  height: 36px;
  background: transparent;
  color: #5a8bb0;

  &:hover {
    background: rgba(255, 255, 255, 0.45);
    color: #3a5a70;
  }
}

.mic-btn {
  width: 48px;
  height: 48px;
  background: linear-gradient(145deg, #9CC7E3 0%, #7FB2D3 100%);
  color: #ffffff;
  box-shadow:
    0 4px 14px rgba(100, 150, 190, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);

  &:hover {
    background: linear-gradient(145deg, #A8CFE8 0%, #89BADB 100%);
    box-shadow:
      0 6px 18px rgba(100, 150, 190, 0.45),
      inset 0 1px 0 rgba(255, 255, 255, 0.4);
  }
}

.hidden-input {
  display: none;
}

.attachment-preview {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  padding-left: 4px;
}

.preview-item {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .remove-btn {
    position: absolute;
    top: 2px;
    right: 2px;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: none;
    background: rgba(0, 0, 0, 0.45);
    color: #fff;
    font-size: 12px;
    line-height: 1;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
