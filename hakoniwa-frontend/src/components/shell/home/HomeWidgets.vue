<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useTodoStore } from '@/stores/todo'

const todoStore = useTodoStore()
const isAdding = ref(false)
const newTodo = ref('')
const todoInputRef = ref<HTMLInputElement | null>(null)

const currentTime = ref(new Date())
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(() => {
    currentTime.value = new Date()
  }, 1000)
  todoStore.load()
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function startAdd() {
  isAdding.value = true
  nextTick(() => todoInputRef.value?.focus())
}

function confirmAdd() {
  const text = newTodo.value.trim()
  if (text) todoStore.add(text)
  newTodo.value = ''
  isAdding.value = false
}

function cancelAdd() {
  newTodo.value = ''
  isAdding.value = false
}

function pad(n: number) {
  return n.toString().padStart(2, '0')
}

const timeStr = computed(() => {
  const h = currentTime.value.getHours()
  const m = pad(currentTime.value.getMinutes())
  const s = pad(currentTime.value.getSeconds())
  const displayH = pad(h % 12 || 12)
  return `${displayH}:${m}:${s}`
})

const ampmStr = computed(() => (currentTime.value.getHours() >= 12 ? 'PM' : 'AM'))

// 简单的静态日历占位数据
const calendarDays = Array.from({ length: 30 }, (_, i) => i + 1)
</script>



<template>
  <div class="home-widgets">
    <!-- Calendar -->
    <div class="widget calendar-widget">
      <div class="widget-header">
        <span class="widget-title">Calendar</span>
      </div>
      <div class="calendar-body">
        <div class="calendar-month">2025年 4月</div>
        <div class="calendar-grid">
          <div v-for="d in ['日','一','二','三','四','五','六']" :key="d" class="weekday">{{ d }}</div>
          <div v-for="day in calendarDays" :key="day" class="day">{{ day }}</div>
        </div>
      </div>
    </div>

    <!-- Clock -->
    <div class="widget clock-widget">
      <div class="widget-header">
        <span class="widget-title">Clock</span>
      </div>
      <div class="clock-body">
        <div class="clock-time">{{ timeStr }}</div>
        <div class="clock-ampm">{{ ampmStr }}</div>
      </div>
    </div>

    <!-- Music Player -->
    <div class="widget music-widget">
      <div class="vinyl">
        <div class="vinyl-disc">
          <div class="vinyl-hole"></div>
        </div>
      </div>
      <div class="track-info">
        <p class="track-title">Placeholder - Demo</p>
        <p class="track-artist">Ansel</p>
      </div>
      <div class="music-controls">
        <button class="ctrl-btn" disabled>⏮</button>
        <button class="ctrl-btn play" disabled>▶</button>
        <button class="ctrl-btn" disabled>⏭</button>
      </div>
    </div>

    <!-- Todo List -->
    <div class="widget todo-widget">
      <div class="widget-header todo-header">
        <span class="widget-title">Todo List</span>
        <button class="todo-add-btn" @click="startAdd">+</button>
      </div>
      <div class="todo-list">
        <div v-if="isAdding" class="todo-item todo-input-row">
          <input
            ref="todoInputRef"
            v-model="newTodo"
            type="text"
            placeholder="添加新任务..."
            @keydown.enter="confirmAdd"
            @blur="cancelAdd"
          />
        </div>
        <div
          v-for="todo in todoStore.items"
          :key="todo.id"
          class="todo-item"
          :class="{ done: todo.completed }"
        >
          <span class="todo-text" @click="todoStore.toggle(todo.id)">{{ todo.content }}</span>
          <div class="todo-actions">
            <div
              class="todo-check"
              :class="{ checked: todo.completed }"
              @click="todoStore.toggle(todo.id)"
            ></div>
            <button class="todo-del" @click="todoStore.remove(todo.id)">×</button>
          </div>
        </div>
        <div v-if="todoStore.items.length === 0 && !isAdding" class="todo-empty">
          暂无待办，点击 + 添加
        </div>
      </div>
    </div>

    <!-- 添加组件按钮 -->
    <button class="add-widget-btn" disabled>
      + 添加组件
    </button>
  </div>
</template>

<style scoped lang="scss">
.home-widgets {
  position: fixed;
  left: calc(clamp(80px, 10vw, 120px) + 32px);
  right: 16px;
  top: 16px;
  bottom: 16px;
  z-index: var(--z-widgets);
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr auto;
  gap: 16px;
  padding: 8px;
  overflow-y: auto;
  pointer-events: none;
}

.home-widgets > * {
  pointer-events: auto;
}

.widget {
  background: var(--color-card-bg);
  backdrop-filter: blur(calc(var(--blur-strength) * var(--enable-blur)));
  -webkit-backdrop-filter: blur(calc(var(--blur-strength) * var(--enable-blur)));
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-card);
  padding: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(90, 139, 176, 0.1);
}

.widget-header {
  margin-bottom: 8px;
}

.widget-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

/* Calendar */
.calendar-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.calendar-month {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  text-align: center;
  font-size: 12px;
}

.weekday {
  color: var(--color-text-muted);
  font-weight: 500;
}

.day {
  padding: 4px;
  border-radius: 50%;
  color: var(--color-text);
}

/* Clock */
.clock-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.clock-time {
  font-size: 42px;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: 1px;
}

.clock-ampm {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-muted);
}

/* Music */
.music-widget {
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.vinyl {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: conic-gradient(#222 0%, #444 20%, #222 40%, #444 60%, #222 80%, #444 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.vinyl-disc {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #a8d0e6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vinyl-hole {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e0edf7;
}

.track-info {
  text-align: center;
}

.track-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
  margin: 0;
}

.track-artist {
  font-size: 11px;
  color: var(--color-text-muted);
  margin: 4px 0 0;
}

.music-controls {
  display: flex;
  gap: 12px;
}

.ctrl-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.3);
  color: var(--color-text);
  cursor: not-allowed;
  opacity: 0.6;
}

/* Todo */
.todo-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
}

.todo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.todo-add-btn {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.5);
  color: var(--color-text);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.2s;
}

.todo-add-btn:hover {
  background: rgba(255, 255, 255, 0.8);
}

.todo-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-input);
  font-size: 12px;
  color: var(--color-text);
  gap: 8px;
}

.todo-item.done .todo-text {
  text-decoration: line-through;
  opacity: 0.6;
}

.todo-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}

.todo-input-row input {
  width: 100%;
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--color-text);
  outline: none;
}

.todo-input-row input::placeholder {
  color: var(--color-text-weak);
}

.todo-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.todo-check {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-text-muted);
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.todo-check.checked {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.todo-del {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, color 0.2s;
}

.todo-item:hover .todo-del {
  opacity: 1;
}

.todo-del:hover {
  color: var(--color-danger);
}

.todo-empty {
  font-size: 12px;
  color: var(--color-text-muted);
  text-align: center;
  padding: 12px 0;
}

/* Add button */
.add-widget-btn {
  grid-column: 1 / -1;
  justify-self: start;
  padding: 10px 18px;
  border-radius: var(--radius-button);
  border: 1px solid rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.4);
  color: var(--color-text);
  font-size: 13px;
  cursor: not-allowed;
  opacity: 0.7;
}

@media (max-width: 899px) {
  .home-widgets {
    left: 16px;
    bottom: 80px;
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }
  .widget {
    min-height: 160px;
  }
}
</style>
