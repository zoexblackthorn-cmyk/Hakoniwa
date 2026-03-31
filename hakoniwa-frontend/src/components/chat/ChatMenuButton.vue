<script setup lang="ts">
defineEmits<{
  click: []
}>()
</script>

<template>
  <button class="menu-btn" @click="$emit('click')">
    <span class="dots">⋯</span>
  </button>
</template>

<style scoped lang="scss">
.menu-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;

  &:hover {
    background: rgba(106, 154, 184, 0.1);
  }

  &:active {
    background: rgba(106, 154, 184, 0.2);
  }
}

.dots {
  font-size: 20px;
  color: #6a9ab8;
  line-height: 1;
  transform: translateY(-2px);
}
</style>
