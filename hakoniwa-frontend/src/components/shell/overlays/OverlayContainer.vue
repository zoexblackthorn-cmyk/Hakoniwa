<script setup lang="ts">
const emit = defineEmits<{ focus: [] }>()

defineProps<{
  side: 'left' | 'right'
  offset?: string
  width: string
  zIndex?: number
}>()
</script>

<template>
  <div
    class="overlay-container"
    :class="side"
    :style="{
      [side === 'right' ? 'right' : 'left']: offset || '16px',
      width,
      zIndex: zIndex ?? 300
    }"
  >
    <slot />
  </div>
</template>

<style scoped lang="scss">
.overlay-container {
  position: fixed;
  top: 16px;
  bottom: 16px;
  background: var(--color-card-bg);
  backdrop-filter: blur(calc(var(--blur-strength) * var(--enable-blur)));
  -webkit-backdrop-filter: blur(calc(var(--blur-strength) * var(--enable-blur)));
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-card);
  box-shadow: 0 8px 32px rgba(90, 139, 176, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 移动端：铺满 */
@media (max-width: 899px) {
  .overlay-container {
    inset: 0 !important;
    width: 100% !important;
    border-radius: 0;
    border: none;
  }
}
</style>
