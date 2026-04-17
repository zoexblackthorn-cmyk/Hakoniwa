<script setup lang="ts">
import { computed } from 'vue'
import { useUserProfileStore } from '@/stores/userProfile'
import { useSettingsStore } from '@/stores/settings'

const props = defineProps<{
  role: 'user' | 'assistant'
}>()

const userStore = useUserProfileStore()
const settingsStore = useSettingsStore()

const src = computed(() => {
  if (props.role === 'user') {
    return userStore.profile?.avatar_path || 'https://api.dicebear.com/7.x/notionists/svg?seed=Zoe'
  }
  return settingsStore.settings.character?.avatar_path || 'https://api.dicebear.com/7.x/notionists/svg?seed=Ansel'
})
</script>

<template>
  <div class="avatar" :class="role">
    <img :src="src" class="avatar-img" />
  </div>
</template>

<style scoped lang="scss">
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid #d0e6f4;
  background: #ffffff;
  overflow: hidden;

  &.assistant {
    background: #f5fbff;
    border-color: #b8d4e8;
  }

  &.user {
    background: #ffffff;
    border-color: #d0e6f4;
  }
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
