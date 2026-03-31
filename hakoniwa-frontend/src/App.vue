<script setup lang="ts">
import AppTabBar from '@/components/layout/AppTabBar.vue'
</script>

<template>
  <div class="app-container">
    <main class="main-content">
      <RouterView />
    </main>
    <AppTabBar />
  </div>
</template>

<style scoped lang="scss">
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 480px;
  margin: 0 auto;
  background: #e8f4fc;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
}

.main-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
