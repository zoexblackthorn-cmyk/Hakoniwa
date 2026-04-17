<script setup lang="ts">
import { useShellStore } from '@/stores/shell'
import { useUserProfileStore } from '@/stores/userProfile'
import {
  Home,
  MessageCircle,
  SlidersHorizontal,
  Bell
} from 'lucide-vue-next'

const shell = useShellStore()
const userStore = useUserProfileStore()
</script>

<template>
  <nav class="side-nav">
    <div class="nav-section top">
      <button class="nav-btn avatar-btn" title="用户资料" @click="shell.toggleUserCard()">
        <img
          v-if="!userStore.loading && userStore.profile?.avatar_path"
          :src="userStore.profile.avatar_path"
          alt="user"
          class="avatar-img"
        />
        <img
          v-else-if="!userStore.loading"
          :src="'https://api.dicebear.com/7.x/notionists/svg?seed=Zoe'"
          alt="user"
          class="avatar-img"
        />
        <div v-else class="avatar-skeleton" />
      </button>
    </div>

    <div class="nav-section middle">
      <button
        class="nav-btn"
        :class="{ active: !shell.anyOverlayOpen }"
        title="首页"
        @click="shell.toggleHome()"
      >
        <Home class="icon" :size="22" />
      </button>

      <button
        class="nav-btn"
        :class="{ active: shell.activeDrawer === 'chat' }"
        title="聊天"
        @click="shell.toggleDrawer('chat')"
      >
        <MessageCircle class="icon" :size="22" />
      </button>

      <button
        class="nav-btn"
        :class="{ active: shell.activeDrawer === 'settings' }"
        title="设置"
        @click="shell.toggleDrawer('settings')"
      >
        <SlidersHorizontal class="icon" :size="22" />
      </button>

      <button
        class="nav-btn notify-btn"
        :class="{ active: shell.notifyOpen }"
        title="通知"
        @click="shell.toggleNotify()"
      >
        <Bell class="icon" :size="22" />
        <span v-if="shell.notifyCount > 0" class="badge">{{ String(shell.notifyCount).padStart(2, '0') }}</span>
      </button>
    </div>


  </nav>
</template>

<style scoped lang="scss">
.side-nav {
  position: fixed;
  left: 20px;
  top: 20px;
  bottom: 20px;
  width: clamp(88px, 9vw, 118px);
  background: linear-gradient(
    180deg,
    #B8DDF0 0%,
    #CFE6F2 45%,
    #CFE6F2 55%,
    #AFD5EB 100%
  );
  backdrop-filter: blur(calc(var(--blur-strength) * var(--enable-blur)));
  -webkit-backdrop-filter: blur(calc(var(--blur-strength) * var(--enable-blur)));
  border-radius: 60px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    0 20px 40px rgba(100, 160, 200, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.55);
  z-index: var(--z-nav);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 22px 0 28px;
  gap: 0;
}

.nav-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.nav-section.top {
  flex-shrink: 0;
  padding-bottom: 8px;
}

.nav-section.middle {
  flex: 1;
  justify-content: center;
  gap: 52px;
  padding: 20px 0;
}

.nav-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  transition: transform 0.15s ease, color 0.2s;

  &:hover {
    transform: scale(1.08);
  }

  &:active {
    transform: scale(0.94);
  }

  /* Active state: vertical white indicator bar on the right */
  &.active::after {
    content: '';
    position: absolute;
    right: -32px;
    top: 50%;
    transform: translateY(-50%);
    width: 6px;
    height: 42px;
    background: #ffffff;
    border-radius: 4px;
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
  }
}

/* Icon sizing — strokes look lighter and larger */
.nav-btn :deep(.icon) {
  width: 26px;
  height: 26px;
  stroke-width: 1.8;
}

.avatar-btn {
  width: 82px;
  height: 82px;
  padding: 0;
  overflow: hidden;
  border: 3px solid rgba(255, 255, 255, 0.85);
  box-shadow: 0 4px 14px rgba(80, 130, 170, 0.25);
  background: #f5f5f7;

  &:hover {
    transform: scale(1.04);
  }

  &.active::after {
    display: none;
  }
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-skeleton {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.45);
  animation: skeleton-pulse 1.4s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 0.9; }
}

.notify-btn {
  position: relative;
}

.badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: #ff6b6b;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  border: 1.5px solid rgba(255, 255, 255, 0.8);
}
</style>
