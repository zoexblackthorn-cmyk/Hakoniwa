<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import { Trash2, X, CheckSquare } from 'lucide-vue-next'

const chatStore = useChatStore()

const selectedCount = computed(() => chatStore.selectedMessageIds.size)
const totalSelectable = computed(() =>
  chatStore.messages.filter((m: any) => m.status !== 'typing' && m.status !== 'sending').length
)
const allSelected = computed(() =>
  selectedCount.value > 0 && selectedCount.value === totalSelectable.value
)

function onSelectAll() {
  if (allSelected.value) {
    chatStore.selectedMessageIds.clear()
  } else {
    for (const m of chatStore.messages) {
      if (m.status !== 'typing' && m.status !== 'sending') {
        chatStore.selectedMessageIds.add(m.id)
      }
    }
  }
}

function onDelete() {
  if (selectedCount.value === 0) return
  if (confirm(`确定要删除选中的 ${selectedCount.value} 条消息吗？`)) {
    chatStore.batchDeleteSelected()
  }
}

function onCancel() {
  chatStore.exitMultiSelectMode()
}
</script>

<template>
  <div class="multi-select-bar">
    <div class="bar-content">
      <button class="bar-btn cancel" @click="onCancel">
        <X :size="18" />
        <span>取消</span>
      </button>

      <span class="select-count">
        已选 {{ selectedCount }} 条
      </span>

      <button class="bar-btn select-all" @click="onSelectAll">
        <CheckSquare :size="16" />
        <span>{{ allSelected ? '取消全选' : '全选' }}</span>
      </button>

      <button
        class="bar-btn delete"
        :disabled="selectedCount === 0"
        @click="onDelete"
      >
        <Trash2 :size="16" />
        <span>删除</span>
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.multi-select-bar {
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  background: rgba(235, 248, 255, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid rgba(154, 201, 255, 0.3);
  padding: 10px 16px;
}

.bar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.select-count {
  font-size: 13px;
  color: #5a7a90;
  font-weight: 500;
  white-space: nowrap;
}

.bar-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  border-radius: 10px;
  border: none;
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  font-weight: 500;

  &.cancel {
    background: rgba(200, 210, 220, 0.3);
    color: #6a8a9f;

    &:hover {
      background: rgba(200, 210, 220, 0.5);
    }
  }

  &.select-all {
    background: rgba(154, 201, 255, 0.2);
    color: #4a7a98;

    &:hover {
      background: rgba(154, 201, 255, 0.35);
    }
  }

  &.delete {
    background: rgba(217, 122, 122, 0.15);
    color: #c55;

    &:hover:not(:disabled) {
      background: rgba(217, 122, 122, 0.3);
    }

    &:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
  }
}
</style>
