<template>
  <nav :class="['sidebar', { collapsed }]" aria-label="主导航">
    <div class="sidebar-header">
      <button class="toggle-btn" @click="collapsed = !collapsed" :aria-expanded="(!collapsed).toString()">
        {{ collapsed ? '☰' : '☰ 导航' }}
      </button>
    </div>
    <ul class="nav-list">
      <li>
        <RouterLink to="/" class="nav-link" :class="{ active: route.name === 'dashboard' }">
          <span class="icon">🏠</span>
          <span v-if="!collapsed">主面板</span>
        </RouterLink>
      </li>
      <li>
        <RouterLink to="/categories" class="nav-link" :class="{ active: route.name === 'categories' }">
          <span class="icon">📚</span>
          <span v-if="!collapsed">分类浏览</span>
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

const collapsed = ref(false)
const route = useRoute()
</script>

<style scoped>
.sidebar {
  width: 240px;
  min-width: 240px;
  background: #f8fafc;
  border-right: 1px solid #e5e7eb;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.sidebar.collapsed {
  width: 64px;
  min-width: 64px;
  padding: 0.5rem;
}
.sidebar-header { display: flex; justify-content: center; }
.toggle-btn {
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  border-radius: 8px;
  padding: 0.4rem 0.6rem;
  cursor: pointer;
  font-weight: 600;
}
.nav-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.25rem; }
.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.6rem;
  border-radius: 8px;
  color: #374151;
  text-decoration: none;
}
.nav-link:hover { background: #eef2ff; }
.nav-link.active { background: #e0e7ff; color: #111827; font-weight: 600; }
.icon { font-size: 1rem; }
</style>