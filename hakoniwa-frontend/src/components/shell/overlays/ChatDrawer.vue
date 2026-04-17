<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useShellStore } from '@/stores/shell'
import { useChatStore } from '@/stores/chat'
import { useSettingsStore } from '@/stores/settings'
import OverlayContainer from './OverlayContainer.vue'
import MessageList from '@/components/chat/MessageList.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import ChatMenuDrawer from '@/components/chat/ChatMenuDrawer.vue'
import { X, MoreHorizontal } from 'lucide-vue-next'

const shell = useShellStore()
const chatStore = useChatStore()
const settingsStore = useSettingsStore()

const anselAvatar = computed(() =>
  settingsStore.settings.character?.avatar_path || 'https://api.dicebear.com/7.x/notionists/svg?seed=Ansel'
)

const menuDrawerOpen = ref(false)
const backgroundImage = ref<string | null>(null)

onMounted(() => {
  if (chatStore.conversationId) {
    const saved = localStorage.getItem(`chat-bg-${chatStore.conversationId}`)
    if (saved) backgroundImage.value = saved
  }
})

const drawerStyle = computed(() => {
  if (backgroundImage.value) {
    return {
      backgroundImage: `url(${backgroundImage.value})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  return {
    background: 'linear-gradient(135deg, #B0DEFF 10%, #D4F6FF 100%)'
  }
})

function openMenu() {
  menuDrawerOpen.value = true
}

function onLoadFromDate(date: string) {
  chatStore.loadMessagesFromDate(date)
}

function onDeleteConversation() {
  if (chatStore.conversationId) {
    chatStore.deleteCurrentConversation()
    backgroundImage.value = null
  }
}

function onSetBackground() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (ev) => {
        const result = ev.target?.result as string
        backgroundImage.value = result
        if (chatStore.conversationId) {
          localStorage.setItem(`chat-bg-${chatStore.conversationId}`, result)
        }
      }
      reader.readAsDataURL(file)
    }
  }
  input.click()
}
</script>

<template>
  <OverlayContainer
    side="right"
    width="45%"
    offset="16px"
  >
    <div class="chat-drawer" :style="drawerStyle">
      <!-- Header -->
      <div class="chat-header">
        <button class="header-btn menu-btn" @click="openMenu">
          <MoreHorizontal :size="20" />
        </button>
        <div class="header-pill">
          <button
            class="ansel-avatar"
            title="Ansel 资料"
            @click="shell.toggleCharacterCard()"
          >
            <img
              v-if="!settingsStore.loading && settingsStore.settings.character?.avatar_path"
              :src="settingsStore.settings.character.avatar_path"
              alt="Ansel"
            />
            <img
              v-else-if="!settingsStore.loading"
              :src="anselAvatar"
              alt="Ansel"
            />
            <div v-else class="avatar-skeleton" />
          </button>
        </div>
        <button class="header-btn close-btn" @click="shell.toggleDrawer('chat')">
          <X :size="20" />
        </button>
      </div>

      <!-- Messages -->
      <MessageList class="chat-messages" />

      <!-- Input -->
      <ChatInput />
    </div>

    <!-- Chat Menu Drawer（复用旧组件，已重命名） -->
    <ChatMenuDrawer
      v-model="menuDrawerOpen"
      @load-from-date="onLoadFromDate"
      @delete-conversation="onDeleteConversation"
      @set-background="onSetBackground"
    />
  </OverlayContainer>
</template>
<style scoped lang="scss">
.chat-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: var(--radius-card);
  overflow: hidden;
}
.chat-header {
  position: relative;
  padding: 14px 18px 0;
  flex-shrink: 0;
  margin-bottom: 40px;
}

.header-btn {
  position: absolute;
  top: 30px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: rgba(26, 58, 82, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  z-index: 3;

  &:hover {
    background: rgba(180, 210, 230, 0.3);
    color: var(--color-text);
  }

  &.menu-btn  { left: 30px; }
  &.close-btn { right: 30px; }
}

.header-pill {
  width: 100%;
  background: #ffffff;
  border-radius: 15px;
  height: 64px;
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: visible;
  position: relative;
}
.ansel-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 3px solid #ffffff;
  overflow: hidden;
  cursor: pointer;
  background: #ffffff;
  padding: 0;
  transform: translateY(20px);
  position: relative;
  z-index: 2;
  transition: transform 0.2s ease;

  &:hover {
    transform: translateY(20px) scale(1.04);
  }

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.avatar-skeleton {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(200, 220, 240, 0.5);
  animation: skeleton-pulse 1.4s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 0.9; }
}

.chat-messages {
  flex: 1;
  min-height: 0;
}
</style>
