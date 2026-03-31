<script setup lang="ts">
import LaceBorder from './LaceBorder.vue'

defineProps<{
  title?: string
}>()
</script>

<template>
  <header class="app-header">
    <div class="header-content">
      <div class="header-left">
        <slot name="left" />
      </div>
      <div class="header-center">
        <span class="pixel-icon">✦</span>
        <h1 class="title">{{ title || 'Hakoniwa' }}</h1>
        <span class="pixel-icon">✦</span>
      </div>
      <div class="header-right">
        <slot name="right" />
      </div>
    </div>
    <LaceBorder />
  </header>
</template>

<style scoped lang="scss">
.app-header {
  background: linear-gradient(180deg, #d8ecfa 0%, #e8f4fc 100%);
  padding-top: 12px;
  flex-shrink: 0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px 12px;
}

.header-left,
.header-right {
  width: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #5a8bb0;
  margin: 0;
  letter-spacing: 1px;
}

.pixel-icon {
  font-size: 12px;
  color: #a8c8dc;
}
</style>
