<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const inputValue = ref('')

function onSend() {
  const text = inputValue.value.trim()
  if (!text || chatStore.isLoading) return
  chatStore.sendUserMessage(text)
  inputValue.value = ''
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend()
  }
}
</script>

<template>
  <div class="chat-input">
    <div class="input-wrapper">
      <input
        v-model="inputValue"
        type="text"
        class="input"
        placeholder="说点什么吧..."
        :disabled="chatStore.isLoading"
        @keydown="onKeydown"
      />
      <button
        class="send-btn"
        :disabled="!inputValue.trim() || chatStore.isLoading"
        @click="onSend"
      >
        <span v-if="chatStore.isLoading">⏳</span>
        <span v-else>➤</span>
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat-input {
  padding: 10px 12px 14px;
  background: #ffffff;
  border-top: 2px solid #d0e6f4;
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f5fbff;
  border: 2px solid #d0e6f4;
  border-radius: 24px;
  padding: 4px 4px 4px 14px;
}

.input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  color: #4a6a80;
  outline: none;
  padding: 8px 0;

  &::placeholder {
    color: #a8c8dc;
  }

  &:disabled {
    opacity: 0.6;
  }
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: #b8d4e8;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;

  &:hover:not(:disabled) {
    background: #a8c8dc;
  }

  &:disabled {
    background: #d0e6f4;
    cursor: not-allowed;
  }

  span {
    font-size: 14px;
    transform: translateX(1px);
  }
}
</style>
