<script setup lang="ts">
import { computed } from 'vue'
import type { Desire } from '@/services/debugApi'

const props = defineProps<{ desires: Desire[] }>()

const sorted = computed(() => [...props.desires].sort((a, b) => b.intensity - a.intensity))
</script>

<template>
  <section class="panel">
    <div class="panel-title">Desires ({{ sorted.length }})</div>
    <div v-if="sorted.length === 0" class="empty">no pending desires</div>
    <table v-else>
      <thead>
        <tr>
          <th>#</th><th>intensity</th><th>need</th><th>activity</th>
          <th>origin</th><th>status</th><th>needs_user</th><th>created_at</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in sorted" :key="d.id">
          <td>{{ d.id }}</td>
          <td class="num">{{ d.intensity.toFixed(4) }}</td>
          <td>{{ d.need }}</td>
          <td>{{ d.activity_name }}</td>
          <td class="muted">{{ d.origin }}</td>
          <td :class="{ 'status-pending': d.status === 'pending' }">{{ d.status }}</td>
          <td>{{ d.needs_user ? 'yes' : '' }}</td>
          <td class="muted">{{ d.created_at }}</td>
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

  th, td {
    text-align: left;
    padding: 4px 8px;
    border-bottom: 1px dashed #e0edf7;
  }

  th {
    color: #5a8bb0;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 10px;
    letter-spacing: 0.5px;
  }

  td.num { font-weight: 600; }
  td.muted { color: #90a8bc; }
  td.status-pending { color: #ff9800; font-weight: 600; }
}
</style>
