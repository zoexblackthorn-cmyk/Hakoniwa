<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { useShellStore } from '@/stores/shell'
import { useUserProfileStore } from '@/stores/userProfile'
import { useChatStore } from '@/stores/chat'
import { useSettingsStore } from '@/stores/settings'
import DesktopBackground from './DesktopBackground.vue'
import SideNav from './SideNav.vue'
import MobileTabBar from './MobileTabBar.vue'
import ChatDrawer from './overlays/ChatDrawer.vue'
import SettingsDrawer from './overlays/SettingsDrawer.vue'
import UserCardPanel from './overlays/UserCardPanel.vue'
import CharacterCardPanel from './overlays/CharacterCardPanel.vue'
import NotifyOverlay from './overlays/NotifyOverlay.vue'
import HomeWidgets from './home/HomeWidgets.vue'

const { isDesktop } = useBreakpoint()
const shell = useShellStore()
const userProfile = useUserProfileStore()
const chatStore = useChatStore()
const settingsStore = useSettingsStore()

onMounted(() => {
  userProfile.load()
  chatStore.loadRecentConversation()
  settingsStore.fetchSettings()
  window.addEventListener('keydown', onKey)
})
onUnmounted(() => window.removeEventListener('keydown', onKey))

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') shell.closeTop()
}
</script>

<template>
  <div class="app-shell" :class="{ desktop: isDesktop, mobile: !isDesktop }">
    <DesktopBackground />
    <Transition name="widgets-slide">
      <HomeWidgets v-if="shell.widgetsVisible" />
    </Transition>

    <SideNav v-if="isDesktop" />

    <Transition name="slide-right">
      <ChatDrawer v-if="shell.activeDrawer === 'chat'" :z-index="shell.getZ('chat')" @focus="shell.bringToFront('chat')" />
    </Transition>
    <Transition name="slide-right">
      <SettingsDrawer v-if="shell.activeDrawer === 'settings'" :z-index="shell.getZ('settings')" @focus="shell.bringToFront('settings')" />
    </Transition>
    <Transition name="slide-left">
      <UserCardPanel v-if="shell.userCardOpen" :z-index="shell.getZ('userCard')" @focus="shell.bringToFront('userCard')" />
    </Transition>
    <Transition name="slide-left">
      <CharacterCardPanel v-if="shell.characterCardOpen" :z-index="shell.getZ('characterCard')" @focus="shell.bringToFront('characterCard')" />
    </Transition>
    <Transition name="fade-scale">
      <NotifyOverlay v-if="shell.notifyOpen" :z-index="shell.getZ('notify')" />
    </Transition>

    <MobileTabBar v-if="!isDesktop" />
  </div>
</template>

<style lang="scss">
/* 全局 CSS 变量（app-shell 级别，未来暗色模式切换用） */
.app-shell {
  --color-primary: #5a8bb0;
  --color-text: #1a3a52;
  --color-text-muted: #6b8ca8;
  --color-text-weak: #9bb8cc;
  --color-bg-light: #e0edf7;
  --color-border: #d0e6f4;
  --color-card-bg: rgba(255, 255, 255, 0.75);
  --color-danger: #d32f2f;

  --radius-card: 24px;
  --radius-input: 12px;
  --radius-button: 14px;

  --blur-strength: 20px;
  --enable-blur: 1;  /* 未来可在设置里关掉 */

  --z-background: 0;
  --z-widgets: 10;
  --z-nav: 100;
  --z-overlay-bg: 200;
  --z-drawer: 300;
  --z-panel: 400;
  --z-notify: 500;

  position: fixed;
  inset: 0;
  overflow: hidden;
  font-family: -apple-system, 'Helvetica Neue', 'PingFang SC', sans-serif;
  color: var(--color-text);
}

/* Overlay 进入/离开动效 */
.slide-right-enter-active,
.slide-right-leave-active,
.slide-left-enter-active,
.slide-left-leave-active {
  transition: transform 0.45s cubic-bezier(0.32, 0.72, 0.32, 1), opacity 0.35s ease;
}

.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(calc(100% + 20px));
  opacity: 0;
}

.slide-left-enter-from,
.slide-left-leave-to {
  transform: translateX(calc(-100% - 20px));
  opacity: 0;
}

/* Notify 淡入淡出 + 轻微缩放 */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: opacity 0.35s ease, transform 0.4s cubic-bezier(0.32, 0.72, 0.32, 1);
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

/* Widgets 滑入动效：带预备动作 + 弹性结束 */
.widgets-slide-enter-active {
  animation: widget-enter 0.85s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.widgets-slide-leave-active {
  transition: transform 0.45s ease-in, opacity 0.35s ease;
}

.widgets-slide-leave-to {
  transform: translateX(-40%) scale(0.96);
  opacity: 0;
}

@keyframes widget-enter {
  0% {
    transform: translateX(-120%) scale(0.92);
    opacity: 0;
  }
  8% {
    /* 预备动作：先微微后缩 */
    transform: translateX(-125%) scale(0.9);
    opacity: 0;
  }
  70% {
    /* 弹性 overshoot */
    transform: translateX(2%) scale(1.01);
    opacity: 1;
  }
  88% {
    transform: translateX(-1%) scale(0.998);
  }
  100% {
    transform: translateX(0) scale(1);
    opacity: 1;
  }
}
</style>
