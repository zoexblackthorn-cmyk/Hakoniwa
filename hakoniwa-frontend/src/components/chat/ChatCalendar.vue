<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getConversationMessageDates } from '@/services/conversation'
import { useChatStore } from '@/stores/chat'

const emit = defineEmits<{
  select: [date: string]
}>()

const chatStore = useChatStore()
const dates = ref<string[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth())

onMounted(async () => {
  loading.value = true
  try {
    if (chatStore.conversationId) {
      dates.value = await getConversationMessageDates(chatStore.conversationId)
    } else {
      dates.value = []
    }
  } catch (e) {
    error.value = '加载日期失败'
  } finally {
    loading.value = false
  }
})

const monthNames = [
  '一月', '二月', '三月', '四月', '五月', '六月',
  '七月', '八月', '九月', '十月', '十一月', '十二月'
]

const currentMonthName = computed(() => monthNames[currentMonth.value])

const daysInMonth = computed(() => {
  return new Date(currentYear.value, currentMonth.value + 1, 0).getDate()
})

const firstDayOfMonth = computed(() => {
  return new Date(currentYear.value, currentMonth.value, 1).getDay()
})

const calendarDays = computed(() => {
  const days: { date: number; hasRecord: boolean; fullDate: string }[] = []
  const firstDay = firstDayOfMonth.value
  
  // 前面的空白天
  for (let i = 0; i < firstDay; i++) {
    days.push({ date: 0, hasRecord: false, fullDate: '' })
  }
  
  // 实际的日期
  for (let date = 1; date <= daysInMonth.value; date++) {
    const fullDate = `${currentYear.value}-${String(currentMonth.value + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`
    const hasRecord = dates.value.includes(fullDate)
    days.push({ date, hasRecord, fullDate })
  }
  
  return days
})

function prevMonth() {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

function selectDate(fullDate: string) {
  if (!fullDate) return
  emit('select', fullDate)
}
</script>

<template>
  <div class="calendar">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div class="calendar-header">
        <button class="nav-btn" @click="prevMonth">‹</button>
        <span class="month-year">{{ currentYear }}年 {{ currentMonthName }}</span>
        <button class="nav-btn" @click="nextMonth">›</button>
      </div>
      
      <div class="weekdays">
        <span v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day" class="weekday">
          {{ day }}
        </span>
      </div>
      
      <div class="days">
        <button
          v-for="(day, index) in calendarDays"
          :key="index"
          class="day"
          :class="{
            'empty': day.date === 0,
            'has-record': day.hasRecord
          }"
          :disabled="day.date === 0 || !day.hasRecord"
          @click="selectDate(day.fullDate)"
        >
          <span v-if="day.date > 0" class="day-number">{{ day.date }}</span>
          <span v-if="day.hasRecord" class="record-dot" />
        </button>
      </div>
      
      <div class="hint">
        <span class="dot-example" />
        <span class="hint-text">有聊天记录的日期</span>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.calendar {
  padding: 16px;
  flex: 1;
  overflow-y: auto;
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  color: #6a9ab8;
}

.error {
  color: #d97a7a;
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.nav-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f5fbff;
  cursor: pointer;
  font-size: 18px;
  color: #6a9ab8;
  transition: background 0.2s;

  &:hover {
    background: #e8f4fc;
  }
}

.month-year {
  font-size: 15px;
  font-weight: 500;
  color: #4a6a80;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 8px;
}

.weekday {
  text-align: center;
  font-size: 12px;
  color: #9bb8cc;
  padding: 8px 0;
}

.days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.day {
  aspect-ratio: 1;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  transition: background 0.2s;
  position: relative;

  &:hover:not(:disabled) {
    background: #f5fbff;
  }

  &:disabled {
    cursor: default;
  }

  &.empty {
    cursor: default;
  }

  &.has-record {
    .day-number {
      color: #6a9ab8;
      font-weight: 600;
    }
  }
}

.day-number {
  font-size: 14px;
  color: #4a6a80;
}

.record-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #6a9ab8;
}

.hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e8f4fc;
}

.dot-example {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #6a9ab8;
}

.hint-text {
  font-size: 12px;
  color: #9bb8cc;
}
</style>
