<script setup lang="ts">
import DebugPanel from '@/components/debug/DebugPanel.vue'
</script>

<template>
  <div class="debug-view">
    <DebugPanel />
  </div>
</template>

<style scoped lang="scss">
.debug-view {
  min-height: 100vh;
  padding: 16px;
  background: #f5faff;
  background-image:
    linear-gradient(#e0edf7 1px, transparent 1px),
    linear-gradient(90deg, #e0edf7 1px, transparent 1px);
  background-size: 24px 24px;
}
</style>
