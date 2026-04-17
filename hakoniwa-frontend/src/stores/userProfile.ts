import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getUserProfile, updateUserProfile, type UserProfile } from '@/services/user'

export const useUserProfileStore = defineStore('userProfile', () => {
  const profile = ref<UserProfile | null>(null)
  const loading = ref(false)
  const saving = ref(false)

  async function load() {
    loading.value = true
    try { profile.value = await getUserProfile() }
    finally { loading.value = false }
  }

  async function save(data: Partial<UserProfile>) {
    saving.value = true
    try { profile.value = await updateUserProfile(data) }
    finally { saving.value = false }
  }

  return { profile, loading, saving, load, save }
})
