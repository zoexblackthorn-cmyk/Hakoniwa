<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { path: '/', label: '首页', icon: '🏠' },
  { path: '/chat', label: '聊天', icon: '💬' },
  { path: '/profile', label: '资料', icon: '📇' },
  { path: '/settings', label: '设置', icon: '⚙️' }
]

function isActive(path: string) {
  return route.path === path
}

function onTabClick(path: string) {
  router.push(path)
}
</script>

<template>
  <nav class="app-tab-bar">
    <button
      v-for="tab in tabs"
      :key="tab.path"
      class="tab-item"
      :class="{ active: isActive(tab.path) }"
      @click="onTabClick(tab.path)"
    >
      <span class="tab-icon">{{ tab.icon }}</span>
      <span class="tab-label">{{ tab.label }}</span>
    </button>
    <button
      class="tab-item debug-tab"
      :class="{ active: isActive('/debug') }"
      @click="onTabClick('/debug')"
    >
      <span class="tab-icon">🩵</span>
      <span class="tab-label">debug</span>
    </button>
  </nav>
</template>

<style scoped lang="scss">
.app-tab-bar {
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 60px;
  background: #ffffff;
  border-top: 2px solid #d0e6f4;
  flex-shrink: 0;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  flex: 1;
  height: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: background 0.2s;

  &:active {
    background: #f0f8fc;
  }

  &.active {
    .tab-icon {
      filter: none;
    }
    .tab-label {
      color: #5a8bb0;
      font-weight: 600;
    }
  }
}

.tab-icon {
  font-size: 18px;
  line-height: 1;
}

.tab-label {
  font-size: 11px;
  color: #9bb8cc;
  transition: color 0.2s;
}

.debug-tab {
  .tab-icon {
    color: #00bcd4;
  }
  .tab-label {
    color: #00bcd4;
  }
  &.active {
    .tab-icon {
      color: #0097a7;
    }
    .tab-label {
      color: #0097a7;
      font-weight: 600;
    }
  }
}
</style>
