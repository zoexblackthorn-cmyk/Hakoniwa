import { ref, onMounted, onUnmounted } from 'vue'

export function useBreakpoint(width = 900) {
  const isDesktop = ref(window.innerWidth >= width)

  function onResize() {
    isDesktop.value = window.innerWidth >= width
  }

  onMounted(() => window.addEventListener('resize', onResize))
  onUnmounted(() => window.removeEventListener('resize', onResize))

  return { isDesktop }
}
