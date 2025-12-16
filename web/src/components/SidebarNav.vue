<template>
  <nav :class="['ui-sidebar', { collapsed }]" aria-label="主导航">
    <div class="ui-sidebar-header">
      <button class="ui-sidebar-toggle" @click="collapsed = !collapsed" :aria-expanded="!collapsed">
        {{ collapsed ? "☰" : "☰ 导航" }}
      </button>
    </div>
    <ul class="ui-nav-list">
      <li>
        <RouterLink to="/" class="ui-nav-link" :class="{ active: route.name === 'dashboard' }">
          <span class="ui-nav-icon">🏠</span>
          <span v-if="!collapsed">主面板</span>
        </RouterLink>
      </li>
      <li>
        <RouterLink to="/matcher" class="ui-nav-link" :class="{ active: route.name === 'matcher' }">
          <span class="ui-nav-icon">🎯</span>
          <span v-if="!collapsed">分类匹配</span>
        </RouterLink>
      </li>
      <li>
        <RouterLink
          to="/categories"
          class="ui-nav-link"
          :class="{ active: route.name === 'categories' }"
        >
          <span class="ui-nav-icon">📚</span>
          <span v-if="!collapsed">分类浏览</span>
        </RouterLink>
      </li>
      <li>
        <RouterLink
          to="/env-config"
          class="ui-nav-link"
          :class="{ active: route.name === 'env-config' }"
        >
          <span class="ui-nav-icon">⚙️</span>
          <span v-if="!collapsed">环境配置</span>
        </RouterLink>
      </li>
    </ul>

    <div class="ui-sidebar-footer">
      <div class="project-logo" :class="{ collapsed }">
        <img :src="logoSrc" alt="Arxiv Daily" class="logo-image" />
        <span v-if="!collapsed" class="logo-text">arxiv Daily</span>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, RouterLink } from "vue-router";
import logoSrc from "@/assets/logo.png";

const collapsed = ref(false);
const route = useRoute();
</script>
