<template>
  <div v-if="(isRunning && !showProgress) || lastRecommendationResult" class="dashboard-results">
    <!-- 运行状态区域 -->
    <div v-if="isRunning && !showProgress" class="ui-card">
      <h2 class="ui-subheader">📋 运行状态</h2>
      <div class="ui-spinner">
        <div class="spinner"></div>
        <span>{{ runningMessage }}</span>
      </div>
    </div>

    <!-- 推荐结果 -->
    <div v-if="lastRecommendationResult" class="ui-card">
      <h2 class="ui-subheader">📊 推荐结果</h2>
      <div v-if="lastRecommendationResult.success" class="ui-alert-success">
        <strong>✅ {{ lastRecommendationResult.message }}</strong>
        <div v-if="lastRecommendationResult.report_path" class="result-details">
          <p><strong>报告路径：</strong>{{ lastRecommendationResult.report_path }}</p>
          <p v-if="lastRecommendationResult.execution_time">
            <strong>执行时间：</strong>{{ lastRecommendationResult.execution_time }}秒
          </p>
        </div>
      </div>
      <div v-else class="ui-alert-error">❌ {{ lastRecommendationResult.message }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";

defineProps<{
  isRunning: boolean;
  showProgress: boolean;
  runningMessage: string;
}>();

const store = useArxivStore();
const { lastRecommendationResult } = storeToRefs(store);
</script>

<style scoped>
.result-details {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
}
.result-details p {
  margin: 4px 0;
  font-size: var(--font-size-sm);
}
</style>
