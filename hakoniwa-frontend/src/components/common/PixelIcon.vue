<script setup lang="ts">
defineProps<{
  name: string
}>()
</script>

<template>
  <span class="pixel-icon">{{ name }}</span>
</template>

<style scoped lang="scss">
.pixel-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 1;
  color: #a8c8dc;
}
</style>
