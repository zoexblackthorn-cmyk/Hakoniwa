<script setup lang="ts"></script>

<template>
  <div class="lace-border">
    <div class="lace-dots">
      <span v-for="n in 20" :key="n" class="dot">◆</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.lace-border {
  width: 100%;
  overflow: hidden;
  line-height: 1;
}

.lace-dots {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 8px;
}

.dot {
  font-size: 8px;
  color: #c8dff0;
  user-select: none;
}
</style>
