<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  title: string
  defaultExpanded?: boolean
}>()

const expanded = ref(props.defaultExpanded ?? false)

function toggle() {
  expanded.value = !expanded.value
}
</script>

<template>
  <div class="collapsible-card">
    <div class="header" @click="toggle">
      <h3 class="title">{{ title }}</h3>
      <span class="icon" :class="{ expanded }">▼</span>
    </div>
    <Transition name="slide">
      <div v-show="expanded" class="body">
        <slot />
      </div>
    </Transition>
  </div>
</template>

<style scoped lang="scss">
.collapsible-card {
  background: #ffffff;
  border: 2px solid #d0e6f4;
  border-radius: 14px;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  cursor: pointer;
  user-select: none;
  background: #f5fbff;
}

.title {
  font-size: 14px;
  font-weight: 600;
  color: #4a6a80;
  margin: 0;
}

.icon {
  font-size: 12px;
  color: #6a9ab8;
  transition: transform 0.25s;

  &.expanded {
    transform: rotate(180deg);
  }
}

.body {
  padding: 12px 14px 14px;
  border-top: 1px solid #e8f4fc;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 800px;
}
</style>
