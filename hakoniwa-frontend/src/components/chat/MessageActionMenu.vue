<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import type { Message } from '@/types/message'
import { Copy, Trash2, CheckSquare, Search, X } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'

const props = defineProps<{
  message: Message | null
  x: number
  y: number
}>()

const emit = defineEmits<{
  close: []
}>()

const chatStore = useChatStore()
const menuRef = ref<HTMLElement | null>(null)
const adjustedPos = ref({ x: props.x, y: props.y })

function onCopy() {
  if (props.message?.content) {
    navigator.clipboard.writeText(props.message.content)
  }
  emit('close')
}

function onDelete() {
  if (props.message) {
    chatStore.deleteSingleMessage(props.message.id)
  }
  emit('close')
}

function onMultiSelect() {
  chatStore.enterMultiSelectMode()
  if (props.message) {
    chatStore.toggleMessageSelection(props.message.id)
  }
  emit('close')
}

function onSearch() {
  chatStore.enterSearchMode()
  emit('close')
}

function onClickOutside(e: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    emit('close')
  }
}

onMounted(() => {
  // Adjust position to keep menu on screen
  const menuWidth = 180
  const menuHeight = 200
  const winW = window.innerWidth
  const winH = window.innerHeight

  let nx = props.x
  let ny = props.y

  if (nx + menuWidth > winW) {
    nx = winW - menuWidth - 12
  }
  if (ny + menuHeight > winH) {
    ny = winH - menuHeight - 12
  }

  adjustedPos.value = { x: nx, y: ny }

  document.addEventListener('click', onClickOutside, { capture: true })
  document.addEventListener('scroll', () => emit('close'), { capture: true, once: true })
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside, { capture: true })
})
</script>

<template>
  <Teleport to="body">
    <div
      ref="menuRef"
      class="action-menu"
      :style="{ left: adjustedPos.x + 'px', top: adjustedPos.y + 'px' }"
    >
      <div class="menu-header">
        <span class="menu-title">消息操作</span>
        <button class="menu-close" @click="emit('close')">
          <X :size="14" />
        </button>
      </div>
      <div class="menu-items">
        <button class="menu-item" @click="onCopy">
          <Copy :size="15" />
          <span>复制</span>
        </button>
        <button class="menu-item" @click="onDelete">
          <Trash2 :size="15" />
          <span>删除</span>
        </button>
        <button class="menu-item" @click="onMultiSelect">
          <CheckSquare :size="15" />
          <span>多选</span>
        </button>
        <button class="menu-item" @click="onSearch">
          <Search :size="15" />
          <span>搜索聊天内容</span>
        </button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped lang="scss">
.action-menu {
  position: fixed;
  z-index: 200;
  min-width: 170px;
  background: rgba(235, 248, 255, 0.92);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 16px;
  border: 1px solid rgba(154, 201, 255, 0.35);
  box-shadow: 0 8px 32px rgba(100, 160, 210, 0.2);
  overflow: hidden;
  animation: menu-pop 0.15s ease-out;
}

@keyframes menu-pop {
  from {
    opacity: 0;
    transform: scale(0.92);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.menu-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px 6px;
}

.menu-title {
  font-size: 12px;
  font-weight: 600;
  color: #6a9ab8;
  letter-spacing: 0.04em;
}

.menu-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #9bb8cc;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
  border-radius: 50%;
  transition: background 0.2s;

  &:hover {
    background: rgba(154, 201, 255, 0.2);
    color: #4a7a98;
  }
}

.menu-items {
  padding: 4px 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border: none;
  background: transparent;
  border-radius: 10px;
  cursor: pointer;
  color: #4a6a80;
  font-size: 13px;
  font-family: inherit;
  transition: background 0.15s;
  text-align: left;

  &:hover {
    background: rgba(154, 201, 255, 0.22);
  }

  svg {
    color: #7ab8d6;
    flex-shrink: 0;
  }
}
</style>
