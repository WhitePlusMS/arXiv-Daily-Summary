<template>
  <div v-if="showProgress" class="dashboard-progress">
    <ProgressDisplay :progress="currentProgress" title="分类匹配运行进度" :show-logs="true" />
  </div>

  <div
    v-if="(isMatching && !showProgress) || matchCompleted || results.length > 0"
    class="dashboard-results"
  >
    <!-- 运行状态 -->
    <div v-if="isMatching && !showProgress" class="streamlit-section">
      <h2 class="streamlit-subheader">📋 运行状态</h2>
      <div class="streamlit-spinner">
        <div class="spinner"></div>
        <span>{{ runningMessage }}</span>
      </div>
    </div>

    <!-- 匹配完成提示 -->
    <div v-if="matchCompleted" class="streamlit-success">
      ✅ 匹配完成！结果已保存到数据库。<br />
      📊 全部115个分类的详细评分已保存到 data/users/detailed_scores/ 目录。
    </div>

    <!-- 匹配结果 -->
    <div v-if="results.length > 0" class="streamlit-section">
      <h2 class="streamlit-subheader">🎯 匹配结果</h2>
      <div class="results-table">
        <div class="table-header">
          <div>#</div>
          <div>分类ID</div>
          <div>分类名称</div>
          <div>匹配评分</div>
        </div>
        <div v-for="(r, idx) in results" :key="r.id" class="table-row">
          <div>{{ idx + 1 }}</div>
          <div>
            <code>{{ r.id }}</code>
          </div>
          <div>{{ r.name }}</div>
          <div>{{ r.score }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ProgressDisplay from "@/components/ProgressDisplay.vue";
import type { ProgressData } from "@/types";

defineProps<{
  showProgress: boolean;
  currentProgress: ProgressData | null;
  isMatching: boolean;
  matchCompleted: boolean;
  results: { id: string; name: string; score: number }[];
  runningMessage: string;
}>();
</script>
