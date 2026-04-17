import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type DrawerType = 'chat' | 'settings' | null

const BASE_Z: Record<string, number> = {
  chat: 300,
  settings: 300,
  userCard: 400,
  characterCard: 410,
  notify: 500,
}

export const useShellStore = defineStore('shell', () => {
  const activeDrawer = ref<DrawerType>(null)
  const userCardOpen = ref(false)
  const characterCardOpen = ref(false)
  const notifyOpen = ref(false)
  const notifyCount = ref(0)
  const widgetsVisible = ref(false)

  // 动态 z-index 管理：最后打开的永远在最上层
  const overlayZ = ref<Record<string, number>>({})
  let zCounter = 600

  function bringToFront(key: string) {
    overlayZ.value[key] = ++zCounter
  }

  const anyOverlayOpen = computed(() =>
    activeDrawer.value !== null || userCardOpen.value || characterCardOpen.value || notifyOpen.value
  )

  function toggleDrawer(drawer: 'chat' | 'settings') {
    const wasOpen = activeDrawer.value === drawer
    activeDrawer.value = wasOpen ? null : drawer
    if (!wasOpen) bringToFront(drawer)
  }

  function toggleUserCard() {
    userCardOpen.value = !userCardOpen.value
    if (userCardOpen.value) bringToFront('userCard')
  }

  function toggleCharacterCard() {
    characterCardOpen.value = !characterCardOpen.value
    if (characterCardOpen.value) bringToFront('characterCard')
  }

  function toggleNotify() {
    notifyOpen.value = !notifyOpen.value
    if (notifyOpen.value) bringToFront('notify')
  }

  function setNotifyCount(count: number) {
    notifyCount.value = count
  }

  function goHome() {
    activeDrawer.value = null
    userCardOpen.value = false
    characterCardOpen.value = false
    notifyOpen.value = false
    widgetsVisible.value = true
  }

  function toggleHome() {
    if (!anyOverlayOpen.value && widgetsVisible.value) {
      widgetsVisible.value = false
    } else {
      goHome()
    }
  }

  // ESC 关闭最顶层
  function closeTop() {
    if (characterCardOpen.value) { characterCardOpen.value = false; return }
    if (userCardOpen.value) { userCardOpen.value = false; return }
    if (notifyOpen.value) { notifyOpen.value = false; return }
    if (activeDrawer.value) { activeDrawer.value = null; return }
  }

  function getZ(key: string) {
    return overlayZ.value[key] ?? BASE_Z[key]
  }

  return {
    activeDrawer, userCardOpen, characterCardOpen, notifyOpen, notifyCount,
    anyOverlayOpen, widgetsVisible, overlayZ,
    toggleDrawer, toggleUserCard, toggleCharacterCard, toggleNotify, setNotifyCount,
    goHome, toggleHome, closeTop, bringToFront, getZ,
  }
})
