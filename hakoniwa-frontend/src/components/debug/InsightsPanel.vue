<script setup lang="ts">
import { computed } from 'vue'
import type { Insight } from '@/services/debugApi'

const props = defineProps<{ insights: Insight[] }>()

const grouped = computed(() => {
  const g: Record<string, Insight[]> = {}
  for (const i of props.insights) {
    if (!g[i.category]) g[i.category] = []
    g[i.category].push(i)
  }
  for (const k of Object.keys(g)) {
    g[k].sort((a, b) => b.confidence - a.confidence)
  }
  return g
})
</script>

<template>
  <section class="panel">
    <div class="panel-title">Insights ({{ insights.length }})</div>
    <div v-if="insights.length === 0" class="empty">no insights (min_confidence=0.3)</div>
    <div v-else class="groups">
      <div v-for="(items, category) in grouped" :key="category" class="group">
        <div class="group-header">[{{ category }}] ({{ items.length }})</div>
        <div v-for="i in items" :key="i.id" class="insight">
          <div class="line">
            <span class="conf">{{ i.confidence.toFixed(4) }}</span>
            <span class="content">{{ i.content }}</span>
          </div>
          <div class="meta">#{{ i.id }} · created {{ i.created_at }} · updated {{ i.updated_at }}</div>
        </div>
      </div>
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
  .empty { color: #90a8bc; font-size: 11px; }
}

.group {
  margin-bottom: 12px;
  &:last-child { margin-bottom: 0; }

  .group-header {
    color: #5a8bb0;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }
}

.insight {
  padding: 6px 8px;
  border-left: 2px solid #b0cbdf;
  margin-bottom: 4px;
  font-size: 11px;

  .line {
    display: flex;
    gap: 8px;
    line-height: 1.5;

    .conf { color: #5a8bb0; font-weight: 600; min-width: 50px; }
    .content { color: #1a3a52; }
  }

  .meta {
    color: #90a8bc;
    font-size: 10px;
    margin-top: 2px;
  }
}
</style>
