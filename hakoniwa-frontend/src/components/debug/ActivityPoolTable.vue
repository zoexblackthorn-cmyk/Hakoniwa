<script setup lang="ts">
import { computed } from 'vue'
import type { ActivityPoolItem } from '@/services/debugApi'

const props = defineProps<{ activities: ActivityPoolItem[] }>()

const sorted = computed(() => [...props.activities].sort((a, b) => b.affinity - a.affinity))
</script>

<template>
  <section class="panel">
    <div class="panel-title">Activity pool ({{ sorted.length }})</div>
    <div v-if="sorted.length === 0" class="empty">pool is empty — run "sync activity pool"</div>
    <table v-else>
      <thead>
        <tr>
          <th>name</th><th>satisfies</th><th>stim_rate</th><th>affinity</th><th>times_done</th><th>last_done_at</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="a in sorted" :key="a.name">
          <td>{{ a.name }}</td>
          <td>{{ a.satisfies }}</td>
          <td class="num">{{ a.stim_rate.toFixed(4) }}</td>
          <td class="num">{{ a.affinity.toFixed(4) }}</td>
          <td>{{ a.times_done }}</td>
          <td class="muted">{{ a.last_done_at || '—' }}</td>
        </tr>
      </tbody>
    </table>
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
  .empty { color: #90a8bc; font-size: 11px; }
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  th, td { text-align: left; padding: 4px 8px; border-bottom: 1px dashed #e0edf7; }
  th { color: #5a8bb0; font-weight: 600; text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px; }
  td.num { font-weight: 600; }
  td.muted { color: #90a8bc; }
}
</style>
