<script setup lang="ts">
import { computed } from 'vue'
import type { EnnoiaState } from '@/services/debugApi'

const props = defineProps<{ state: EnnoiaState | null }>()

const fmt = (v: number) => v.toFixed(4)

function moodLabel(v: number, a: number): string {
  if (v >= 0.6) {
    if (a >= 0.55) return '兴奋 / excited'
    if (a >= 0.35) return '愉快 / pleasant'
    return '平静 / calm'
  } else if (v >= 0.4) {
    if (a >= 0.5) return '躁动 / restless'
    return '平淡 / neutral'
  } else {
    if (a >= 0.55) return '焦虑 / anxious'
    if (a >= 0.3) return '低落 / down'
    return '疲惫 / drained'
  }
}

const label = computed(() =>
  props.state ? moodLabel(props.state.mood.valence, props.state.mood.arousal) : '—'
)

function bar(v: number): string {
  const width = Math.round(v * 20)
  return '█'.repeat(width) + '░'.repeat(20 - width)
}
</script>

<template>
  <section class="panel">
    <div class="panel-title">Ennoia State</div>

    <div v-if="!state" class="empty">loading…</div>
    <div v-else class="content">

      <div class="section">
        <div class="label">needs</div>
        <div class="row"><span class="k">social      </span><span class="bar">{{ bar(state.needs.social) }}</span><span class="v">{{ fmt(state.needs.social) }}</span></div>
        <div class="row"><span class="k">stimulation </span><span class="bar">{{ bar(state.needs.stimulation) }}</span><span class="v">{{ fmt(state.needs.stimulation) }}</span></div>
        <div class="row"><span class="k">expression  </span><span class="bar">{{ bar(state.needs.expression) }}</span><span class="v">{{ fmt(state.needs.expression) }}</span></div>
      </div>

      <div class="section">
        <div class="label">mood <span class="mood-label">{{ label }}</span></div>
        <div class="row"><span class="k">valence     </span><span class="v">{{ fmt(state.mood.valence) }}</span></div>
        <div class="row"><span class="k">arousal     </span><span class="v">{{ fmt(state.mood.arousal) }}</span></div>
      </div>

      <div class="section">
        <div class="label">personality</div>
        <div class="row"><span class="k">social      </span><span class="v">{{ fmt(state.personality.social) }}</span></div>
        <div class="row"><span class="k">stimulation </span><span class="v">{{ fmt(state.personality.stimulation) }}</span></div>
        <div class="row"><span class="k">expression  </span><span class="v">{{ fmt(state.personality.expression) }}</span></div>
      </div>

      <div class="section">
        <div class="label">current activity</div>
        <div class="row"><span class="k">name        </span><span class="v">{{ state.current_activity.name }}</span></div>
        <div class="row"><span class="k">satisfies   </span><span class="v">{{ state.current_activity.satisfies || '—' }}</span></div>
        <div class="row"><span class="k">stim_rate   </span><span class="v">{{ fmt(state.current_activity.stim_rate) }}</span></div>
        <div class="row"><span class="k">ticks_on    </span><span class="v">{{ state.current_activity.ticks_on }}</span></div>
        <div class="row"><span class="k">started_at  </span><span class="v">{{ state.current_activity.started_at || '—' }}</span></div>
      </div>

      <div class="section">
        <div class="label">misc</div>
        <div class="row"><span class="k">closeness              </span><span class="v">{{ fmt(state.closeness) }}</span></div>
        <div class="row"><span class="k">unshared_experiences   </span><span class="v">{{ fmt(state.unshared_experiences) }}</span></div>
        <div class="row"><span class="k">last_user_interaction  </span><span class="v">{{ state.last_user_interaction_at || '—' }}</span></div>
        <div class="row"><span class="k">last_initiative        </span><span class="v">{{ state.last_initiative_at || '—' }}</span></div>
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

  .empty { color: #90a8bc; }
}

.section {
  margin-bottom: 10px;
  &:last-child { margin-bottom: 0; }

  .label {
    color: #5a8bb0;
    font-weight: 600;
    margin-bottom: 4px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .mood-label {
    color: #1a3a52;
    font-weight: normal;
    text-transform: none;
    letter-spacing: 0;
    margin-left: 8px;
  }

  .row {
    display: flex;
    gap: 8px;
    line-height: 1.6;

    .k { color: #6b8ca8; white-space: pre; }
    .bar { color: #5a8bb0; letter-spacing: -1px; }
    .v { color: #1a3a52; font-weight: 600; }
  }
}
</style>
