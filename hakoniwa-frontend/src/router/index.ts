import { createRouter, createWebHistory } from 'vue-router'
import AppShell from '@/components/shell/AppShell.vue'
import DebugView from '@/views/DebugView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: AppShell },
    { path: '/debug', component: DebugView },
    // 兼容旧链接，全部重定向到 /
    { path: '/chat', redirect: '/' },
    { path: '/profile', redirect: '/' },
    { path: '/settings', redirect: '/' },
  ]
})

export default router
