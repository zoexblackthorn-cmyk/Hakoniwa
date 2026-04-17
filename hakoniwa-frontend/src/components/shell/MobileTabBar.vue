<script setup lang="ts">
import { useShellStore } from '@/stores/shell'
import { Home, MessageCircle, SlidersHorizontal, Bell } from 'lucide-vue-next'

const shell = useShellStore()
</script>

<template>
  <nav class="mobile-tab-bar">
    <button
      class="tab-btn"
      :class="{ active: !shell.anyOverlayOpen }"
      @click="shell.goHome()"
    >
      <Home class="icon" :size="22" />
      <span class="label">首页</span>
    </button>

    <button
      class="tab-btn"
      :class="{ active: shell.activeDrawer === 'chat' }"
      @click="shell.toggleDrawer('chat')"
    >
      <MessageCircle class="icon" :size="22" />
      <span class="label">聊天</span>
    </button>

    <button
      class="tab-btn"
      :class="{ active: shell.activeDrawer === 'settings' }"
      @click="shell.toggleDrawer('settings')"
    >
      <SlidersHorizontal class="icon" :size="22" />
      <span class="label">设置</span>
    </button>

    <button
      class="tab-btn"
      :class="{ active: shell.notifyOpen }"
      @click="shell.toggleNotify()"
    >
      <Bell class="icon" :size="22" />
      <span class="label">通知</span>
    </button>
  </nav>
</template>

<style scoped lang="scss">
.mobile-tab-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: 64px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(calc(var(--blur-strength) * var(--enable-blur)));
  -webkit-backdrop-filter: blur(calc(var(--blur-strength) * var(--enable-blur)));
  border-top: 1px solid rgba(255, 255, 255, 0.6);
  z-index: var(--z-nav);
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.tab-btn {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color 0.2s;

  &.active {
    color: var(--color-primary);
  }
}

.label {
  font-size: 11px;
}
</style>
