<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
</script>

<template>
  <div class="profile-view">
    <AppHeader title="资料卡" />
    <div class="content">
      <div class="card">
        <span class="icon">📇</span>
        <p class="text">Profile 页面建设中...</p>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.profile-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.card {
  background: #ffffff;
  border: 2px solid #d0e6f4;
  border-radius: 14px;
  padding: 32px;
  text-align: center;
}

.icon {
  font-size: 32px;
  display: block;
  margin-bottom: 12px;
}

.text {
  font-size: 14px;
  color: #6a9ab8;
  margin: 0;
}
</style>
