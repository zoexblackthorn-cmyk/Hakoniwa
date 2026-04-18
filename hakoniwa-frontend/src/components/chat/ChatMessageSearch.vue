<script setup lang="ts">
import { ref, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { Search, X, Calendar, FileText, Image, Link, Filter } from 'lucide-vue-next'

const emit = defineEmits<{
  close: []
}>()

const chatStore = useChatStore()
const keyword = ref('')
const selectedType = ref<string>('')
const selectedDate = ref('')

const messageTypes = [
  { value: '', label: '全部', icon: Filter },
  { value: 'text', label: '文字', icon: FileText },
  { value: 'image', label: '图片', icon: Image },
  { value: 'link', label: '链接', icon: Link },
]

async function onSearch() {
  await chatStore.searchMessages(
    keyword.value || undefined,
    selectedType.value || undefined,
    selectedDate.value || undefined
  )
}

function onResultClick(dbMessageId?: number) {
  if (dbMessageId) {
    chatStore.setHighlightDbMessageId(dbMessageId)
  }
  chatStore.exitSearchMode()
  emit('close')
}

function formatTime(date: Date): string {
  const d = new Date(date)
  const month = d.getMonth() + 1
  const day = d.getDate()
  let hours = d.getHours()
  const minutes = d.getMinutes()
  const ampm = hours >= 12 ? 'PM' : 'AM'
  hours = hours % 12
  hours = hours ? hours : 12
  const mm = minutes < 10 ? '0' + minutes : minutes
  return `${month}月${day}日 ${hours}.${mm} ${ampm}`
}

// 高亮关键词
function highlightText(text: string, query: string): string {
  if (!query.trim()) return escapeHtml(text)
  const escapedQuery = escapeRegex(query.trim())
  const regex = new RegExp(`(${escapedQuery})`, 'gi')
  return escapeHtml(text).replace(regex, '<mark>$1</mark>')
}

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// Debounce search
let searchTimer: ReturnType<typeof setTimeout> | null = null
watch([keyword, selectedType, selectedDate], () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(onSearch, 400)
})
</script>

<template>
    <div class="search-overlay" @click.self="emit('close')">
      <div class="search-panel">
        <div class="search-header">
          <h3 class="search-title">
            <Search :size="18" />
            搜索聊天记录
          </h3>
          <button class="close-btn" @click="emit('close')">
            <X :size="18" />
          </button>
        </div>

        <div class="search-filters">
          <div class="search-input-wrap">
            <Search :size="15" class="search-icon" />
            <input
              v-model="keyword"
              type="text"
              placeholder="搜索关键词..."
              class="search-input"
            />
            <button v-if="keyword" class="clear-input" @click="keyword = ''">
              <X :size="14" />
            </button>
          </div>

          <div class="filter-row">
            <div class="type-filters">
              <button
                v-for="t in messageTypes"
                :key="t.value"
                class="type-btn"
                :class="{ active: selectedType === t.value }"
                @click="selectedType = t.value"
              >
                <component :is="t.icon" :size="13" />
                <span>{{ t.label }}</span>
              </button>
            </div>

            <div class="date-filter">
              <Calendar :size="13" />
              <input
                v-model="selectedDate"
                type="date"
                class="date-input"
              />
              <button v-if="selectedDate" class="clear-date" @click="selectedDate = ''">
                <X :size="12" />
              </button>
            </div>
          </div>
        </div>

        <div class="search-results">
          <div v-if="chatStore.isLoading" class="loading">
            搜索中...
          </div>
          <div v-else-if="chatStore.searchResults.length === 0 && (keyword || selectedType || selectedDate)" class="empty">
            未找到匹配的消息
          </div>
          <div v-else-if="chatStore.searchResults.length === 0" class="empty-hint">
            输入关键词开始搜索
          </div>
          <div v-else class="result-list">
            <div
              v-for="msg in chatStore.searchResults"
              :key="msg.id"
              class="result-item"
              :class="msg.role"
              @click="onResultClick(msg.dbMessageId)"
            >
              <div class="result-role">{{ msg.role === 'user' ? '我' : 'Ansel' }}</div>
              <div
                class="result-content"
                v-html="highlightText(msg.content, keyword)"
              />
              <div class="result-time">{{ formatTime(msg.timestamp) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
</template>

<style scoped lang="scss">
.search-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.25);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 60px;
  animation: fade-in 0.2s ease;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.search-panel {
  width: 92%;
  max-width: 520px;
  max-height: 70vh;
  background: rgba(250, 252, 255, 0.96);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(154, 201, 255, 0.3);
  box-shadow: 0 12px 40px rgba(80, 140, 200, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: panel-up 0.25s ease;
}

@keyframes panel-up {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.search-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(154, 201, 255, 0.2);
}

.search-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #4a6a80;
}

.close-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #8FB0C6;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;

  &:hover {
    background: rgba(154, 201, 255, 0.15);
    color: #4a7a98;
  }
}

.search-filters {
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-bottom: 1px solid rgba(154, 201, 255, 0.15);
}

.search-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(235, 248, 255, 0.8);
  border-radius: 12px;
  padding: 9px 12px;
  border: 1.5px solid transparent;
  transition: border-color 0.2s;

  &:focus-within {
    border-color: rgba(154, 201, 255, 0.6);
  }
}

.search-icon {
  color: #9bb8cc;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  color: #3a5a70;
  outline: none;
  font-family: inherit;

  &::placeholder {
    color: #a0bcd0;
  }
}

.clear-input {
  background: none;
  border: none;
  cursor: pointer;
  color: #a0bcd0;
  padding: 2px;
  display: flex;
  align-items: center;
  line-height: 0;
  border-radius: 50%;

  &:hover {
    color: #6a9ab8;
  }
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.type-filters {
  display: flex;
  gap: 6px;
}

.type-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: 8px;
  border: 1px solid rgba(154, 201, 255, 0.25);
  background: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  color: #6a8a9f;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;

  &:hover {
    background: rgba(154, 201, 255, 0.15);
  }

  &.active {
    background: rgba(154, 201, 255, 0.3);
    border-color: rgba(154, 201, 255, 0.5);
    color: #3a5a70;
    font-weight: 500;
  }
}

.date-filter {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #6a8a9f;
  font-size: 12px;

  svg {
    color: #9bb8cc;
  }
}

.date-input {
  border: 1px solid rgba(154, 201, 255, 0.3);
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 12px;
  color: #4a6a80;
  background: rgba(255, 255, 255, 0.6);
  font-family: inherit;
  outline: none;

  &::-webkit-calendar-picker-indicator {
    filter: invert(0.5) sepia(0.3) saturate(2) hue-rotate(170deg);
    cursor: pointer;
  }
}

.clear-date {
  background: none;
  border: none;
  cursor: pointer;
  color: #a0bcd0;
  padding: 1px;
  display: flex;
  align-items: center;
  line-height: 0;

  &:hover {
    color: #6a9ab8;
  }
}

.search-results {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  min-height: 120px;
}

.loading,
.empty,
.empty-hint {
  text-align: center;
  padding: 40px 20px;
  color: #9bb8cc;
  font-size: 13px;
}

.empty-hint {
  color: #b8d0e0;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 8px;
}

.result-item {
  padding: 10px 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s;
  display: flex;
  flex-direction: column;
  gap: 4px;

  &:hover {
    background: rgba(154, 201, 255, 0.12);
  }

  &.user {
    .result-role {
      color: #4a9fd4;
    }
  }

  &.assistant {
    .result-role {
      color: #7ab8d6;
    }
  }
}

.result-role {
  font-size: 11px;
  font-weight: 600;
}

.result-content {
  font-size: 13px;
  color: #3a5a70;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;

  :deep(mark) {
    background: rgba(154, 201, 255, 0.45);
    color: #2a4a60;
    border-radius: 3px;
    padding: 0 2px;
    font-weight: 500;
  }
}

.result-time {
  font-size: 11px;
  color: #a0bcd0;
}
</style>
