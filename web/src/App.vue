<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted, onUnmounted, ref } from 'vue'
import SidebarNav from './components/SidebarNav.vue'
import Footer from './components/Footer.vue'
import Toast from './components/Toast.vue'
import type { ToastMessage } from '@/types'

const toasts = ref<ToastMessage[]>([])
let nextId = 1

function pushToast(type: ToastMessage['type'], text: string) {
  const id = nextId++
  const msg: ToastMessage = { id, type, text, createdAt: Date.now() }
  toasts.value = [msg, ...toasts.value].slice(0, 5)
  // 自动消失
  setTimeout(() => dismissToast(id), 6000)
}

function dismissToast(id: number) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

function onApiError(ev: Event) {
  const detail = (ev as CustomEvent<string>).detail || '发生未知错误'
  pushToast('error', detail)
}

onMounted(() => {
  window.addEventListener('api-error', onApiError as EventListener)
})
onUnmounted(() => {
  window.removeEventListener('api-error', onApiError as EventListener)
})
</script>

<template>
  <div id="app" class="app-layout">
    <SidebarNav />
    <main class="app-main">
      <Toast :messages="toasts" @dismiss="dismissToast" />
      <RouterView />
      <Footer />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  gap: 0;
  background: #ffffff;
  font-family: var(--font-family-base);
}
.app-main {
  flex: 1;
  padding: 1rem;
}
</style>
