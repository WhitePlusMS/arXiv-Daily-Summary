<script setup lang="ts">
import { RouterView } from 'vue-router'
import SidebarNav from './components/SidebarNav.vue'
</script>

<template>
  <div id="app" class="app-layout">
    <SidebarNav />
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  gap: 0;
  background: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.app-main {
  flex: 1;
  padding: 1rem;
}
</style>
