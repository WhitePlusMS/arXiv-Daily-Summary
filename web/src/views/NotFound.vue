<template>
  <div class="ui-container">
    <div class="ui-header">
      <h1 class="ui-title">🔎 页面未找到</h1>
      <div class="ui-caption">您访问的页面不存在或已被移动</div>
    </div>

    <div class="ui-card">
      <div class="ui-alert-info">您可以返回主面板或使用左侧导航访问其他功能。</div>
      <div class="button-row">
        <RouterLink to="/" class="ui-button">🏠 返回主面板</RouterLink>
        <RouterLink to="/categories" class="ui-button">📚 分类浏览</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<style scoped></style>
