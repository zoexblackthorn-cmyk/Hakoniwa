import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchTodos, createTodo, deleteTodo, toggleTodo, type TodoItem } from '@/services/todo'

export const useTodoStore = defineStore('todo', () => {
  const items = ref<TodoItem[]>([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      items.value = await fetchTodos()
    } finally {
      loading.value = false
    }
  }

  async function add(content: string) {
    const todo = await createTodo(content)
    items.value.unshift(todo)
  }

  async function remove(id: number) {
    const res = await deleteTodo(id)
    if (res.success) {
      items.value = items.value.filter(t => t.id !== id)
    }
  }

  async function toggle(id: number) {
    const idx = items.value.findIndex(t => t.id === id)
    if (idx === -1) return
    const next = !items.value[idx].completed
    const updated = await toggleTodo(id, next)
    items.value[idx] = updated
  }

  return { items, loading, load, add, remove, toggle }
})
