<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useShellStore } from '@/stores/shell'
import { useSettingsStore } from '@/stores/settings'
import { fetchEnnoiaState, fetchEnnoiaDesires, fetchEnnoiaActivities } from '@/services/ennoia'
import { X } from 'lucide-vue-next'

const props = defineProps<{
  zIndex?: number
}>()

const shell = useShellStore()
const settingsStore = useSettingsStore()

const state = ref<any>(null)
const desires = ref<any[]>([])
const activities = ref<any[]>([])

onMounted(() => {
  shell.bringToFront('notify')
  Promise.all([
    fetchEnnoiaState().then(d => state.value = d).catch(() => null),
    fetchEnnoiaDesires().then(d => desires.value = d).catch(() => []),
    fetchEnnoiaActivities().then(d => activities.value = d).catch(() => [])
  ])
})

const anselAvatar = computed(() =>
  settingsStore.settings.character?.avatar_path || 'https://api.dicebear.com/7.x/notionists/svg?seed=Ansel'
)

const bubbleTexts = computed(() => {
  const activityName = state.value?.current_activity?.name || 'idle'
  const topDesire = desires.value[0]
  const topActivity = activities.value[0]
  const unshared = state.value?.unshared_experiences || 0

  return {
    b1: activityName !== 'idle' ? `Ansel 正在${activityName}` : 'Ansel 正在发呆',
    b2: topDesire?.needs_user ? `他说：${topDesire.user_request || topDesire.activity_name}` : (topActivity?.name ? `他想${topActivity.name}` : '他说想给你看点东西'),
    b3: unshared > 2 ? '“有好多话想对你说”' : (topDesire?.activity_name ? `“${topDesire.activity_name}”` : '“今晚的月亮很亮”'),
    b5: topActivity?.name && topActivity.name !== topDesire?.activity_name ? `他${topActivity.name}` : '他收藏了一首新歌',
  }
})

const bubbles = computed(() => [
  { id: 1, text: bubbleTexts.value.b1, avatarSide: 'left', style: { top: '6%', left: '4%', width: '52%', height: '18%' } },
  { id: 2, text: bubbleTexts.value.b2, avatarSide: 'right', style: { top: '10%', right: '4%', width: '32%', height: '16%' } },
  { id: 3, text: bubbleTexts.value.b3, avatarSide: 'left', style: { top: '30%', left: '10%', width: '26%', height: '14%' } },
  { id: 4, text: '', avatarSide: 'right', style: { top: '48%', right: '6%', width: '48%', height: '26%' }, featured: true },
  { id: 5, text: bubbleTexts.value.b5, avatarSide: 'left', style: { top: '72%', left: '4%', width: '38%', height: '16%' } },
])
</script>

<template>
  <div class="notify-overlay" :style="{ zIndex: zIndex }">
    <div class="notify-backdrop" @click.self="shell.toggleNotify()" @click="shell.bringToFront('notify')">
      <button class="close-btn" @click="shell.toggleNotify()">
        <X :size="20" />
      </button>

      <div
        v-for="bubble in bubbles"
        :key="bubble.id"
        class="notify-bubble"
        :class="{ 'avatar-left': bubble.avatarSide === 'left', 'avatar-right': bubble.avatarSide === 'right' }"
        :style="bubble.style"
      >
        <div class="bubble-avatar">
          <img :src="anselAvatar" alt="Ansel" />
        </div>
        <div v-if="bubble.featured" class="bubble-featured">
          <span class="featured-icon">💭</span>
          <h3>Notify (coming soon)</h3>
          <p>这里将会有 Ansel 的 aspirations</p>
          <p>和他"做不到但想做"的事情</p>
        </div>
        <p v-else class="bubble-text">{{ bubble.text }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.notify-overlay {
  position: fixed;
  inset: 0;
  left: calc(clamp(80px, 10vw, 120px) + 16px);
  padding: 16px;
  overflow: hidden;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notify-backdrop {
  position: relative;
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
  border-radius: var(--radius-card);
  background: rgba(240, 248, 255, 0.72);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.85);
  box-shadow: 0 16px 48px rgba(90, 139, 176, 0.22);
  pointer-events: auto;
  overflow: hidden;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.5);
  color: var(--color-text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  z-index: 10;

  &:hover {
    background: rgba(255, 255, 255, 0.8);
  }
}

.notify-bubble {
  position: absolute;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 40px;
  box-shadow: 0 6px 24px rgba(90, 139, 176, 0.16);
  padding: 18px 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
  transition: transform 0.3s ease, box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 32px rgba(90, 139, 176, 0.22);
  }
}

.bubble-avatar {
  position: absolute;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid #ffffff;
  overflow: hidden;
  background: #f5fbff;
  z-index: 2;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.avatar-left .bubble-avatar {
  top: -14px;
  left: -14px;
}

.avatar-right .bubble-avatar {
  top: -14px;
  right: -14px;
}

.bubble-text {
  margin: 0;
  font-size: 13px;
  color: var(--color-text);
  text-align: center;
  font-weight: 500;
}

.bubble-featured {
  text-align: center;

  .featured-icon {
    font-size: 36px;
    display: block;
    margin-bottom: 8px;
  }

  h3 {
    font-size: 16px;
    font-weight: 600;
    margin: 0 0 6px;
    color: var(--color-text);
  }

  p {
    font-size: 12px;
    color: var(--color-text-muted);
    margin: 2px 0;
  }
}

@media (max-width: 899px) {
  .notify-overlay {
    left: 0;
    padding: 8px;
  }

  .notify-backdrop {
    border-radius: 20px;
  }

  .notify-bubble {
    border-radius: 28px;
    padding: 14px 18px;
  }

  .bubble-avatar {
    width: 36px;
    height: 36px;
  }

  .avatar-left .bubble-avatar {
    top: -10px;
    left: -10px;
  }

  .avatar-right .bubble-avatar {
    top: -10px;
    right: -10px;
  }
}
</style>
