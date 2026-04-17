<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useShellStore } from '@/stores/shell'
import { useUserProfileStore } from '@/stores/userProfile'
import OverlayContainer from './OverlayContainer.vue'
import { X, ChevronLeft } from 'lucide-vue-next'

const shell = useShellStore()
const userStore = useUserProfileStore()

const view = ref<'profile' | 'edit'>('profile')

const localAvatar = ref<string | null>(userStore.profile?.avatar_path || null)

watch(() => userStore.profile?.avatar_path, (v) => {
  if (v) localAvatar.value = v
})

const displayName = computed(() => userStore.profile?.name || '未命名')
const displayStatus = computed(() => userStore.profile?.status_line || '')

const localForm = ref({
  mask: '',
  profession: '',
  personalization: ''
})

watch(() => userStore.profile, (p) => {
  if (p) {
    localForm.value = {
      mask: p.mask || '',
      profession: p.profession || '',
      personalization: p.personalization || ''
    }
  }
}, { immediate: true })

function onAvatarClick() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (ev) => {
        const result = ev.target?.result as string
        localAvatar.value = result
      }
      reader.readAsDataURL(file)
    }
  }
  input.click()
}

async function onSave() {
  await userStore.save({
    mask: localForm.value.mask,
    profession: localForm.value.profession,
    personalization: localForm.value.personalization,
    avatar_path: localAvatar.value || ''
  })
  view.value = 'profile'
}

const photoGrid = Array.from({ length: 7 }, (_, i) => i + 1)
</script>

<template>
  <OverlayContainer
    side="left"
    width="35%"
    offset="calc(16px + clamp(80px, 10vw, 120px) + 16px)"
  >
    <div class="user-card">
      <button class="close-btn" @click="shell.toggleUserCard()">
        <X :size="20" />
      </button>

      <Transition name="fade-slide" mode="out-in">
        <!-- 主页视图 -->
        <div v-if="view === 'profile'" key="profile" class="card-page profile-page">
          <div class="profile-header">
            <button class="avatar-btn" @click="onAvatarClick">
              <img
                :src="localAvatar || 'https://api.dicebear.com/7.x/notionists/svg?seed=Zoe'"
                alt="avatar"
              />
            </button>
            <div class="profile-meta">
              <h3 class="name">{{ displayName }}</h3>
              <div class="status-row">
                <span class="online-dot"></span>
                <span class="online-text">Online</span>
              </div>
              <p class="status-line">
                {{ displayStatus || 'Anything he wanna write here' }}
              </p>
            </div>
          </div>

          <div class="actions">
            <button class="action-btn primary" @click="view = 'edit'">编辑资料</button>
            <button class="action-btn" disabled>查看私人空间</button>
          </div>

          <div class="photo-grid">
            <div v-for="n in photoGrid" :key="n" class="photo-cell">
              <div class="photo-placeholder"></div>
            </div>
          </div>
        </div>

        <!-- 编辑视图 -->
        <div v-else key="edit" class="card-page edit-page">
          <button class="back-btn" @click="view = 'profile'">
            <ChevronLeft :size="18" />
            <span>返回主页</span>
          </button>

          <div class="edit-avatar-row">
            <button class="avatar-btn" @click="onAvatarClick">
              <img
                :src="localAvatar || 'https://api.dicebear.com/7.x/notionists/svg?seed=Zoe'"
                alt="avatar"
              />
            </button>
            <span class="edit-hint">点击头像更换</span>
          </div>

          <div class="form">
            <div class="field">
              <label>Mask</label>
              <textarea v-model="localForm.mask" rows="4" class="input-like" />
            </div>

            <div class="field">
              <label>Profession</label>
              <input v-model="localForm.profession" type="text" class="input-like" />
            </div>

            <div class="field">
              <label>Personalization</label>
              <textarea v-model="localForm.personalization" rows="4" class="input-like" />
            </div>

            <button class="save-btn" :disabled="userStore.saving" @click="onSave">
              {{ userStore.saving ? 'Saving...' : '保存' }}
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </OverlayContainer>
</template>

<style scoped lang="scss">
.user-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px 24px;
  overflow: hidden;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.4);
  color: var(--color-text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  z-index: 10;

  &:hover {
    background: rgba(255, 255, 255, 0.7);
  }
}

.card-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.avatar-btn {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 2px solid #ffffff;
  overflow: hidden;
  padding: 0;
  cursor: pointer;
  background: #f5fbff;
  flex-shrink: 0;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.edit-avatar-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.edit-hint {
  font-size: 12px;
  color: var(--color-text-muted);
}

.profile-meta {
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 4px;
  color: var(--color-text);
}

.status-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.online-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #7fd17f;
}

.online-text {
  font-size: 12px;
  color: var(--color-text-muted);
}

.status-line {
  font-size: 12px;
  color: var(--color-text-weak);
  margin: 0;
  font-style: italic;
}

.actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.action-btn {
  flex: 1;
  padding: 8px 12px;
  border-radius: var(--radius-button);
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.35);
  color: var(--color-text);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.6);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &.primary {
    background: rgba(168, 200, 232, 0.5);
    border-color: rgba(168, 200, 232, 0.6);

    &:hover {
      background: rgba(168, 200, 232, 0.7);
    }
  }
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.photo-cell {
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
}

.photo-placeholder {
  width: 100%;
  height: 100%;
  background: rgba(200, 220, 245, 0.5);
}

.back-btn {
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  margin-bottom: 12px;
  border-radius: var(--radius-button);
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.35);
  color: var(--color-text);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.6);
  }
}

.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;

  label {
    font-size: 12px;
    font-weight: 500;
    color: var(--color-text-muted);
  }
}

.input-like {
  padding: 10px 12px;
  border-radius: var(--radius-input);
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  color: var(--color-text);
  outline: none;
  resize: vertical;

  &:focus {
    border-color: rgba(90, 139, 176, 0.5);
    background: rgba(255, 255, 255, 0.55);
  }

  &::placeholder {
    color: var(--color-text-weak);
  }
}

.save-btn {
  align-self: flex-start;
  padding: 10px 24px;
  border-radius: var(--radius-button);
  border: none;
  background: #a8c8e8;
  color: #1a3a52;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 4px;

  &:hover:not(:disabled) {
    background: #98b8d8;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}
</style>
