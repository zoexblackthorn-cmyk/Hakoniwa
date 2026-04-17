<script setup lang="ts">
import { ref } from 'vue'
import { debugApi } from '@/services/debugApi'

const emit = defineEmits<{ 'after-action': [] }>()

const lastAction = ref<{ name: string; ok: boolean; time: string; detail?: string } | null>(null)
const busy = ref(false)

async function run(name: string, fn: () => Promise<unknown>) {
  if (busy.value) return
  busy.value = true
  try {
    const result = await fn()
    lastAction.value = {
      name, ok: true,
      time: new Date().toTimeString().slice(0, 8),
      detail: typeof result === 'object' ? JSON.stringify(result).slice(0, 100) : String(result),
    }
    emit('after-action')
  } catch (e: unknown) {
    lastAction.value = { name, ok: false, time: new Date().toTimeString().slice(0, 8), detail: e instanceof Error ? e.message : String(e) }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="panel">
    <div class="panel-title">Actions</div>
    <div class="buttons">
      <button :disabled="busy" @click="run('manual tick', debugApi.manualTick)">manual tick</button>
      <button :disabled="busy" @click="run('reflect', debugApi.reflect)">reflect</button>
      <button :disabled="busy" @click="run('consolidate', debugApi.consolidate)">consolidate</button>
      <button :disabled="busy" @click="run('sync activity pool', debugApi.syncActivityPool)">sync activity pool</button>
    </div>
    <div v-if="lastAction" class="last" :class="{ err: !lastAction.ok }">
      <div class="line">
        <span>{{ lastAction.ok ? '✓' : '✗' }}</span>
        <span>{{ lastAction.name }}</span>
        <span class="t">{{ lastAction.time }}</span>
      </div>
      <div v-if="lastAction.detail" class="detail">{{ lastAction.detail }}</div>
    </div>
  </section>
</template>

<style scoped lang="scss">
.panel {
  background: #ffffff;
  border: 1px solid #5a8bb0;
  padding: 12px 14px;

  .panel-title {
    font-weight: 700;
    color: #5a8bb0;
    font-size: 13px;
    border-bottom: 1px dashed #b0cbdf;
    padding-bottom: 6px;
    margin-bottom: 10px;
  }
}

.buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;

  button {
    font-family: inherit;
    font-size: 12px;
    padding: 6px 10px;
    background: #e8f2fb;
    border: 1px solid #5a8bb0;
    color: #1a3a52;
    cursor: pointer;
    text-align: left;

    &:hover:not(:disabled) { background: #d4e7f7; }
    &:disabled { opacity: 0.4; cursor: not-allowed; }
  }
}

.last {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed #b0cbdf;
  font-size: 11px;

  &.err { color: #d32f2f; }

  .line { display: flex; gap: 8px; }
  .t { color: #90a8bc; margin-left: auto; }
  .detail { color: #6b8ca8; margin-top: 2px; word-break: break-all; }
}
</style>
