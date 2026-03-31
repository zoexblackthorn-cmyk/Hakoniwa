<script setup lang="ts">
defineProps<{
  role: 'user' | 'assistant'
}>()
</script>

<template>
  <div class="avatar" :class="role">
    <span class="avatar-icon">{{ role === 'assistant' ? '👼' : '😊' }}</span>
  </div>
</template>

<style scoped lang="scss">
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid #d0e6f4;
  background: #ffffff;

  &.assistant {
    background: #f5fbff;
    border-color: #b8d4e8;
  }

  &.user {
    background: #ffffff;
    border-color: #d0e6f4;
  }
}

.avatar-icon {
  font-size: 20px;
  line-height: 1;
}
</style>
