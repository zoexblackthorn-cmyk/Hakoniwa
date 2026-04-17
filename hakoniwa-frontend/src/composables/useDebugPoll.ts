import { ref, onMounted, onUnmounted } from 'vue'
import { debugApi } from '@/services/debugApi'
import type { EnnoiaState, Desire, ActivityPoolItem, Insight, ChatError } from '@/services/debugApi'

export function useDebugPoll(intervalMs = 5000) {
  const state = ref<EnnoiaState | null>(null)
  const desires = ref<Desire[]>([])
  const activities = ref<ActivityPoolItem[]>([])
  const insights = ref<Insight[]>([])
  const lastError = ref<ChatError | null>(null)

  const lastUpdate = ref<Date | null>(null)
  const isPolling = ref(true)
  const fetchError = ref<string | null>(null)
  let timer: number | null = null

  async function refresh() {
    try {
      const [s, d, a, i, e] = await Promise.all([
        debugApi.getEnnoiaState(),
        debugApi.getDesires(),
        debugApi.getActivityPool(),
        debugApi.getInsights(0.3),
        debugApi.getLastChatError(),
      ])
      state.value = s
      desires.value = d.desires
      activities.value = a.activities
      insights.value = i.insights
      lastError.value = e.error
      lastUpdate.value = new Date()
      fetchError.value = null
    } catch (err: unknown) {
      fetchError.value = err instanceof Error ? err.message : String(err)
    }
  }

  function start() {
    if (timer) return
    isPolling.value = true
    refresh()
    timer = window.setInterval(refresh, intervalMs)
  }

  function stop() {
    if (timer) {
      window.clearInterval(timer)
      timer = null
    }
    isPolling.value = false
  }

  function toggle() {
    isPolling.value ? stop() : start()
  }

  onMounted(start)
  onUnmounted(stop)

  return { state, desires, activities, insights, lastError, lastUpdate, isPolling, fetchError, refresh, toggle }
}
