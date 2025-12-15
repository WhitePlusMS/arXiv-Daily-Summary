<template>
  <div class="streamlit-header">
    <h1 class="streamlit-title">📚 ArXiv推荐系统 - 每日论文推荐</h1>
    <div class="streamlit-caption time-info">
      <span class="time-item">
        <span class="time-label">当前时间</span>
        <span class="time-value">{{ localTime }}</span>
        <span class="time-zone">({{ localTimezone }})</span>
      </span>
      <span class="time-separator">|</span>
      <span class="time-item">
        <span class="time-label">ArXiv时间</span>
        <span class="time-value">{{ arxivTime }}</span>
        <span class="time-zone">({{ arxivTimezone }})</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTime } from "@/composables/useTime";

const { localTime, arxivTime, localTimezone, arxivTimezone } = useTime();
</script>
