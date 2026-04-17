<script setup lang="ts">
import { useDebugPoll } from '@/composables/useDebugPoll'
import EnnoiaStatePanel from './EnnoiaStatePanel.vue'
import ActionsPanel from './ActionsPanel.vue'
import LastErrorPanel from './LastErrorPanel.vue'
import DesiresTable from './DesiresTable.vue'
import ActivityPoolTable from './ActivityPoolTable.vue'
import InsightsPanel from './InsightsPanel.vue'

const poll = useDebugPoll(5000)

function formatTime(d: Date | null): string {
  if (!d) return '—'
  return d.toTimeString().slice(0, 8)
}
</script>

<template>
  <div class="debug-panel">
    <header class="debug-header">
      <div class="title">/debug</div>
      <div class="status">
        <span class="indicator" :class="{ live: poll.isPolling.value }">●</span>
        <span>{{ poll.isPolling.value ? 'polling' : 'paused' }}</span>
        <span class="sep">·</span>
        <span>last update: {{ formatTime(poll.lastUpdate.value) }}</span>
        <span v-if="poll.fetchError.value" class="err">· ERR: {{ poll.fetchError.value }}</span>
      </div>
      <div class="controls">
        <button @click="poll.toggle">{{ poll.isPolling.value ? 'pause' : 'resume' }}</button>
        <button @click="poll.refresh">refresh now</button>
      </div>
    </header>

    <div class="top-row">
      <EnnoiaStatePanel :state="poll.state.value" />
      <div class="right-column">
        <ActionsPanel @after-action="poll.refresh" />
        <LastErrorPanel :error="poll.lastError.value" @cleared="poll.refresh" />
      </div>
    </div>

    <DesiresTable :desires="poll.desires.value" />
    <ActivityPoolTable :activities="poll.activities.value" />
    <InsightsPanel :insights="poll.insights.value" />
  </div>
</template>

<style scoped lang="scss">
.debug-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-family: 'JetBrains Mono', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  color: #1a3a52;
}

.debug-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 14px;
  background: #ffffff;
  border: 1px solid #5a8bb0;

  .title {
    font-weight: 700;
    font-size: 14px;
    color: #5a8bb0;
  }

  .status {
    flex: 1;
    display: flex;
    gap: 8px;
    align-items: center;

    .indicator {
      color: #b0b0b0;
      &.live { color: #4caf50; animation: pulse 2s infinite; }
    }
    .sep { color: #b0b0b0; }
    .err { color: #d32f2f; font-weight: 600; }
  }

  .controls {
    display: flex;
    gap: 8px;
    button {
      font-family: inherit;
      font-size: 11px;
      padding: 4px 10px;
      background: #ffffff;
      border: 1px solid #5a8bb0;
      color: #5a8bb0;
      cursor: pointer;
      &:hover { background: #e8f2fb; }
    }
  }
}

.top-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
}

.right-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (max-width: 900px) {
  .top-row { grid-template-columns: 1fr; }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
