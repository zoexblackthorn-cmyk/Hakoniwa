<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
  label?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

function toggle() {
  emit('update:modelValue', !props.modelValue)
}
</script>

<template>
  <div class="toggle-switch" @click="toggle">
    <span v-if="label" class="label">{{ label }}</span>
    <div class="switch" :class="{ active: modelValue }">
      <div class="thumb"></div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.toggle-switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.label {
  font-size: 14px;
  color: #4a6a80;
}

.switch {
  width: 48px;
  height: 26px;
  border-radius: 13px;
  background: #d0e6f4;
  position: relative;
  transition: background 0.25s;

  &.active {
    background: #6a9ab8;

    .thumb {
      transform: translateX(22px);
    }
  }
}

.thumb {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ffffff;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.25s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style>
