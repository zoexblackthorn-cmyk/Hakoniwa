<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getConversations, deleteConversation } from '@/services/conversation'
import type { Conversation } from '@/services/conversation'

const emit = defineEmits<{
  delete: []
}>()

const conversations = ref<Conversation[]>([])
const selectedIds = ref<Set<string>>(new Set())
const loading = ref(false)
const deleting = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  loading.value = true
  try {
    conversations.value = await getConversations()
    // 默认选中当前对话（如果有）
  } catch (e) {
    error.value = '加载对话列表失败'
  } finally {
    loading.value = false
  }
})

function toggleSelect(id: string) {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
}

function toggleSelectAll() {
  if (selectedIds.value.size === conversations.value.length) {
    selectedIds.value.clear()
  } else {
    selectedIds.value = new Set(conversations.value.map(c => c.conversation_id))
  }
}

function isAllSelected() {
  return conversations.value.length > 0 && selectedIds.value.size === conversations.value.length
}

async function confirmDelete() {
  if (selectedIds.value.size === 0) return
  
  deleting.value = true
  try {
    for (const id of selectedIds.value) {
      await deleteConversation(id)
    }
    emit('delete')
  } catch (e) {
    error.value = '删除失败'
  } finally {
    deleting.value = false
  }
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}
</script>

<template>
  <div class="delete-page">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div class="select-all-row">
        <label class="checkbox-label">
          <input
            type="checkbox"
            :checked="isAllSelected()"
            @change="toggleSelectAll"
          />
          <span>全选</span>
        </label>
        <span class="count">已选 {{ selectedIds.size }} 项</span>
      </div>
      
      <div class="conversation-list">
        <label
          v-for="conv in conversations"
          :key="conv.conversation_id"
          class="conversation-item"
          :class="{ selected: selectedIds.has(conv.conversation_id) }"
        >
          <input
            type="checkbox"
            :checked="selectedIds.has(conv.conversation_id)"
            @change="toggleSelect(conv.conversation_id)"
          />
          <div class="conv-info">
            <span class="conv-title">{{ conv.title || '未命名对话' }}</span>
            <span class="conv-date">{{ formatDate(conv.updated_at) }}</span>
          </div>
        </label>
        
        <div v-if="conversations.length === 0" class="empty">
          暂无聊天记录
        </div>
      </div>
      
      <div class="actions">
        <button
          class="delete-btn"
          :disabled="selectedIds.size === 0 || deleting"
          @click="confirmDelete"
        >
          {{ deleting ? '删除中...' : `删除所选 (${selectedIds.size})` }}
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.delete-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  color: #6a9ab8;
}

.error {
  color: #d97a7a;
}

.select-all-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e8f4fc;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #4a6a80;
}

.count {
  font-size: 13px;
  color: #9bb8cc;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #f5fbff;
  }

  &.selected {
    background: #e8f4fc;
  }
}

.conv-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conv-title {
  font-size: 14px;
  color: #4a6a80;
}

.conv-date {
  font-size: 12px;
  color: #9bb8cc;
}

.empty {
  text-align: center;
  padding: 40px;
  color: #9bb8cc;
  font-size: 14px;
}

.actions {
  padding: 12px 16px;
  border-top: 1px solid #e8f4fc;
}

.delete-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 10px;
  background: #d97a7a;
  color: #ffffff;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover:not(:disabled) {
    background: #c96a6a;
  }

  &:disabled {
    background: #e8c4c4;
    cursor: not-allowed;
  }
}
</style>
