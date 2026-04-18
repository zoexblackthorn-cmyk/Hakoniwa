<script setup lang="ts">
import { ref, computed } from 'vue'
import ChatCalendar from './ChatCalendar.vue'
import ChatDelete from './ChatDelete.vue'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits([
  'update:modelValue',
  'loadFromDate',
  'deleteConversation',
  'setBackground',
  'search'
])

// 当前页面：menu | calendar | delete
const currentPage = ref<'menu' | 'calendar' | 'delete'>('menu')

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

function close() {
  isOpen.value = false
  // 延迟重置页面，等动画结束
  setTimeout(() => {
    currentPage.value = 'menu'
  }, 300)
}

function goToCalendar() {
  currentPage.value = 'calendar'
}

function goToDelete() {
  currentPage.value = 'delete'
}

function backToMenu() {
  currentPage.value = 'menu'
}

function onLoadFromDate(date: string) {
  emit('loadFromDate', date)
  close()
}

function onDeleteConversation() {
  emit('deleteConversation')
  close()
}

function onSetBackground() {
  emit('setBackground')
  close()
}

function onOpenSearch() {
  console.log('[ChatMenuDrawer] onOpenSearch clicked')
  emit('search')
  close()
}
</script>

<template>
  <Teleport to="body">
    <!-- 遮罩层 -->
    <Transition name="fade">
      <div v-if="isOpen" class="drawer-overlay" @click="close" />
    </Transition>

    <!-- 抽屉 -->
    <Transition name="slide">
      <div v-if="isOpen" class="drawer">
        <!-- 菜单页面 -->
        <div v-if="currentPage === 'menu'" class="page menu-page">
          <div class="drawer-header">
            <h3 class="drawer-title">聊天设置</h3>
            <button class="close-btn" @click="close">✕</button>
          </div>
          
          <div class="menu-list">
            <button class="menu-item" @click="goToCalendar">
              <span class="menu-icon">📅</span>
              <span class="menu-text">按日期查找</span>
              <span class="menu-arrow">›</span>
            </button>

            <button class="menu-item" @click="onOpenSearch">
              <span class="menu-icon">🔍</span>
              <span class="menu-text">搜索聊天内容</span>
              <span class="menu-arrow">›</span>
            </button>

            <button class="menu-item" @click="onSetBackground">
              <span class="menu-icon">🖼️</span>
              <span class="menu-text">设置当前聊天背景</span>
              <span class="menu-arrow">›</span>
            </button>
            
            <button class="menu-item delete" @click="goToDelete">
              <span class="menu-icon">🗑️</span>
              <span class="menu-text">删除聊天记录</span>
              <span class="menu-arrow">›</span>
            </button>
          </div>
        </div>

        <!-- 日历页面 -->
        <div v-else-if="currentPage === 'calendar'" class="page sub-page">
          <div class="drawer-header">
            <button class="back-btn" @click="backToMenu">‹</button>
            <h3 class="drawer-title">按日期查找</h3>
            <button class="close-btn" @click="close">✕</button>
          </div>
          
          <ChatCalendar @select="onLoadFromDate" />
        </div>

        <!-- 删除页面 -->
        <div v-else-if="currentPage === 'delete'" class="page sub-page">
          <div class="drawer-header">
            <button class="back-btn" @click="backToMenu">‹</button>
            <h3 class="drawer-title">删除聊天记录</h3>
            <button class="close-btn" @click="close">✕</button>
          </div>
          
          <ChatDelete @delete="onDeleteConversation" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped lang="scss">
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 320px;
  max-width: 85vw;
  background: #ffffff;
  z-index: 101;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
}

.page {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.drawer-header {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e8f4fc;
  gap: 12px;
}

.drawer-title {
  flex: 1;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #4a6a80;
}

.close-btn,
.back-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #6a9ab8;
  transition: background 0.2s;

  &:hover {
    background: rgba(106, 154, 184, 0.1);
  }
}

.back-btn {
  font-size: 24px;
  padding-bottom: 4px;
}

.menu-list {
  padding: 8px;
}

.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: none;
  background: transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
  text-align: left;

  &:hover {
    background: #f5fbff;
  }

  &.delete {
    color: #d97a7a;

    .menu-icon,
    .menu-text,
    .menu-arrow {
      color: #d97a7a;
    }
  }
}

.menu-icon {
  font-size: 20px;
  width: 24px;
  text-align: center;
}

.menu-text {
  flex: 1;
  font-size: 14px;
  color: #4a6a80;
}

.menu-arrow {
  font-size: 20px;
  color: #a8c8dc;
}

// 动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease-out;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
