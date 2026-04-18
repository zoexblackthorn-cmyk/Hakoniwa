<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import AppHeader from '@/components/layout/AppHeader.vue'
import MessageList from '@/components/chat/MessageList.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import ChatMenuButton from '@/components/chat/ChatMenuButton.vue'
import ChatMenuDrawer from '@/components/chat/ChatMenuDrawer.vue'
import MessageMultiSelectBar from '@/components/chat/MessageMultiSelectBar.vue'
import ChatMessageSearch from '@/components/chat/ChatMessageSearch.vue'

const chatStore = useChatStore()
const drawerOpen = ref(false)
const showSearch = ref(false)
const backgroundImage = ref<string | null>(null)

// 页面加载时：恢复最近对话和背景图
onMounted(async () => {
  // 先加载最近对话（会自动设置 conversationId）
  await chatStore.loadRecentConversation()

  // 从 localStorage 加载背景图
  if (chatStore.conversationId) {
    const saved = localStorage.getItem(`chat-bg-${chatStore.conversationId}`)
    if (saved) {
      backgroundImage.value = saved
    }
  }
})

const chatViewStyle = computed(() => {
  if (backgroundImage.value) {
    return {
      backgroundImage: `url(${backgroundImage.value})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  return {}
})

function openDrawer() {
  drawerOpen.value = true
}

function onLoadFromDate(date: string) {
  // 从指定日期加载消息
  chatStore.loadMessagesFromDate(date)
}

function onDeleteConversation() {
  // 删除当前对话
  if (chatStore.conversationId) {
    chatStore.deleteCurrentConversation()
    backgroundImage.value = null
  }
}

function onSetBackground() {
  // 触发文件选择
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result as string
        backgroundImage.value = result
        // 保存到 localStorage
        if (chatStore.conversationId) {
          localStorage.setItem(`chat-bg-${chatStore.conversationId}`, result)
        }
      }
      reader.readAsDataURL(file)
    }
  }
  input.click()
}

function onOpenSearch() {
  console.log('[ChatView] onOpenSearch called, showSearch =', showSearch.value)
  showSearch.value = true
  chatStore.enterSearchMode()
}

function onCloseSearch() {
  showSearch.value = false
  chatStore.exitSearchMode()
}
</script>

<template>
  <div class="chat-view" :style="chatViewStyle">
    <AppHeader title="Ansel">
      <template #right>
        <ChatMenuButton @click="openDrawer" />
      </template>
    </AppHeader>
    <MessageList :background-image="backgroundImage" />
    <ChatInput v-if="!chatStore.isMultiSelectMode" />
    <MessageMultiSelectBar v-else />

    <ChatMenuDrawer
      v-model="drawerOpen"
      @load-from-date="onLoadFromDate"
      @delete-conversation="onDeleteConversation"
      @set-background="onSetBackground"
      @search="onOpenSearch"
    />

    <ChatMessageSearch
      v-if="showSearch"
      @close="onCloseSearch"
    />
  </div>
</template>

<style scoped lang="scss">
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5fbff;
}
</style>
