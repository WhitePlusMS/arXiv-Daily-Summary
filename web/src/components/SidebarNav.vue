<template>
  <nav :class="['sidebar', { collapsed }]" aria-label="主导航">
    <div class="sidebar-header">
      <button
        class="toggle-btn"
        @click="collapsed = !collapsed"
        :aria-expanded="!collapsed"
      >
        {{ collapsed ? "☰" : "☰ 导航" }}
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
        <RouterLink to="/matcher" class="nav-link" :class="{ active: route.name === 'matcher' }">
          <span class="icon">🎯</span>
          <span v-if="!collapsed">分类匹配</span>
        </RouterLink>
      </li>
      <li>
        <RouterLink
          to="/categories"
          class="nav-link"
          :class="{ active: route.name === 'categories' }"
        >
          <span class="icon">📚</span>
          <span v-if="!collapsed">分类浏览</span>
        </RouterLink>
      </li>
      <li>
        <RouterLink
          to="/env-config"
          class="nav-link"
          :class="{ active: route.name === 'env-config' }"
        >
          <span class="icon">⚙️</span>
          <span v-if="!collapsed">环境配置</span>
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, RouterLink } from "vue-router";

const collapsed = ref(false);
const route = useRoute();
</script>
