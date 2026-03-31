<script setup lang="ts">
const props = defineProps<{
  modelValue: string
  tabs: { key: string; label: string }[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

function select(key: string) {
  emit('update:modelValue', key)
}
</script>

<template>
  <div class="settings-tab-bar">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="tab"
      :class="{ active: modelValue === tab.key }"
      @click="select(tab.key)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<style scoped lang="scss">
.settings-tab-bar {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  background: #e8f4fc;
  border-bottom: 2px solid #d0e6f4;
  flex-shrink: 0;
  overflow-x: auto;
}

.tab {
  flex: 1;
  min-width: 80px;
  padding: 8px 12px;
  border-radius: 10px;
  border: none;
  background: #ffffff;
  font-size: 13px;
  color: #6a9ab8;
  cursor: pointer;
  transition: all 0.2s;

  &.active {
    background: #6a9ab8;
    color: #ffffff;
    font-weight: 500;
  }

  &:hover:not(.active) {
    background: #f5fbff;
  }
}
</style>
