<script setup lang="ts">
import { computed } from 'vue'
import type { ToastMessage } from '@/types'

const props = defineProps<{ messages: ToastMessage[] }>()
const emit = defineEmits<{ (e: 'dismiss', id: number): void }>()

const items = computed(() => props.messages)

function onDismiss(id: number) {
  emit('dismiss', id)
}
</script>

<template>
  <div class="toast-container" aria-live="polite" aria-atomic="true">
    <div v-for="m in items" :key="m.id" class="toast" :class="`ui-alert-${m.type}`">
      <div class="toast-content">
        <span class="toast-text">{{ m.text }}</span>
        <button class="toast-close" @click="onDismiss(m.id)" aria-label="关闭">×</button>
      </div>
    </div>
  </div>
  
</template>