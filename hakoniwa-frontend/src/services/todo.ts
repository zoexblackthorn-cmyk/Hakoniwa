const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'

export interface TodoItem {
  id: number
  content: string
  completed: number | boolean
  created_at: string
}

export async function fetchTodos(): Promise<TodoItem[]> {
  const res = await fetch(`${API_BASE}/api/todos`)
  if (!res.ok) throw new Error(`GET /api/todos -> ${res.status}`)
  const data = await res.json()
  return data.todos
}

export async function createTodo(content: string): Promise<TodoItem> {
  const res = await fetch(`${API_BASE}/api/todos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content })
  })
  if (!res.ok) throw new Error(`POST /api/todos -> ${res.status}`)
  return res.json()
}

export async function deleteTodo(id: number): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/api/todos/${id}`, {
    method: 'DELETE'
  })
  if (!res.ok) throw new Error(`DELETE /api/todos/${id} -> ${res.status}`)
  return res.json()
}

export async function toggleTodo(id: number, completed: boolean): Promise<TodoItem> {
  const res = await fetch(`${API_BASE}/api/todos/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ completed })
  })
  if (!res.ok) throw new Error(`PATCH /api/todos/${id} -> ${res.status}`)
  return res.json()
}
