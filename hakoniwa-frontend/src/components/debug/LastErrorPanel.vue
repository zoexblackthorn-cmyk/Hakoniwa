<script setup lang="ts">
import { ref } from 'vue'
import { debugApi } from '@/services/debugApi'
import type { ChatError } from '@/services/debugApi'

const props = defineProps<{ error: ChatError | null }>()
const emit = defineEmits<{ cleared: [] }>()

const expanded = ref(false)

async function clear() {
  await debugApi.clearChatError()
  emit('cleared')
}
</script>

<template>
  <section class="panel" :class="{ hasError: !!error }">
    <div class="panel-title">
      Last chat error
      <button v-if="error" class="clear" @click="clear">clear</button>
    </div>
    <div v-if="!error" class="empty">none</div>
    <div v-else class="content">
      <div class="row"><span class="k">time </span><span class="v">{{ error.timestamp }}</span></div>
      <div class="row"><span class="k">type </span><span class="v">{{ error.type }}</span></div>
      <div class="row"><span class="k">msg  </span><span class="v">{{ error.message }}</span></div>
      <div class="tb-header" @click="expanded = !expanded">
        {{ expanded ? '▼' : '▶' }} traceback
      </div>
      <pre v-if="expanded" class="tb">{{ error.traceback }}</pre>
    </div>
  </section>
</template>

<style scoped lang="scss">
.panel {
  background: #ffffff;
  border: 1px solid #5a8bb0;
  padding: 12px 14px;

  &.hasError { border-color: #d32f2f; }

  .panel-title {
    font-weight: 700;
    color: #5a8bb0;
    font-size: 13px;
    border-bottom: 1px dashed #b0cbdf;
    padding-bottom: 6px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .clear {
      font-family: inherit;
      font-size: 10px;
      background: #fff;
      border: 1px solid #d32f2f;
      color: #d32f2f;
      padding: 2px 8px;
      cursor: pointer;
    }
  }

  &.hasError .panel-title { color: #d32f2f; }

  .empty { color: #90a8bc; font-size: 11px; }

  .row {
    display: flex;
    gap: 8px;
    font-size: 11px;
    line-height: 1.5;

    .k { color: #6b8ca8; white-space: pre; }
    .v { color: #d32f2f; word-break: break-all; }
  }

  .tb-header {
    margin-top: 6px;
    color: #5a8bb0;
    cursor: pointer;
    font-size: 11px;
    &:hover { color: #1a3a52; }
  }

  .tb {
    margin-top: 4px;
    padding: 8px;
    background: #fef5f5;
    border: 1px solid #f0c8c8;
    color: #8a2a2a;
    font-size: 10px;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 200px;
    overflow: auto;
  }
}
</style>
