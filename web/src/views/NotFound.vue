<template>
  <div class="streamlit-dashboard">
    <div class="streamlit-header">
      <h1 class="streamlit-title">🔎 页面未找到</h1>
      <div class="streamlit-caption">您访问的页面不存在或已被移动</div>
      <div class="streamlit-divider"></div>
    </div>

    <div class="streamlit-section">
      <div class="streamlit-info">您可以返回主面板或使用左侧导航访问其他功能。</div>
      <div class="button-row">
        <RouterLink to="/" class="streamlit-button">🏠 返回主面板</RouterLink>
        <RouterLink to="/categories" class="streamlit-button">📚 分类浏览</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<style scoped></style>
