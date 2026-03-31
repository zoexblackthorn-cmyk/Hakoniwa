<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  modelValue: string
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const visible = ref(false)

function onInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="secret-input">
    <input
      :type="visible ? 'text' : 'password'"
      :value="modelValue"
      :placeholder="placeholder"
      class="input"
      @input="onInput"
    />
    <button type="button" class="eye-btn" @click="visible = !visible">
      <span>{{ visible ? '🙈' : '👁️' }}</span>
    </button>
  </div>
</template>

<style scoped lang="scss">
.secret-input {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f5fbff;
  border: 2px solid #d0e6f4;
  border-radius: 10px;
  padding: 4px 4px 4px 10px;
}

.input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  color: #4a6a80;
  outline: none;
  padding: 6px 0;

  &::placeholder {
    color: #a8c8dc;
  }
}

.eye-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;

  &:hover {
    background: #e8f4fc;
  }

  span {
    font-size: 14px;
  }
}
</style>
