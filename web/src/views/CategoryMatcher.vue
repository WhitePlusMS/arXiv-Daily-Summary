<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<template>
  <div class="ui-container">
    <!-- 页面头部 -->
    <CategoryMatcherHeader />

    <!-- 主要内容区域 - 单栏布局 -->
    <div class="dashboard-content">
      <!-- 研究信息输入和匹配 -->
      <CategoryMatcherForm
        v-model="formState"
        :isMatching="isMatching"
        :isOptimizing="isOptimizing"
        @optimize="optimizeDescription"
        @match="handleMatch"
      />
    </div>

    <!-- 结果展示区域 -->
    <CategoryMatcherResult
      :showProgress="showProgress"
      :currentProgress="currentProgress"
      :isMatching="isMatching"
      :matchCompleted="matchCompleted"
      :results="results"
      :runningMessage="runningMessage"
    />

    <!-- 用户数据管理 -->
    <CategoryMatcherHistory
      :stats="stats"
      :managementCollapsed="managementCollapsed"
      :searchTerm="searchTerm"
      :selectedIndices="selectedIndices"
      :editModes="editModes"
      :editDrafts="editDrafts"
      :filteredProfiles="filteredProfiles"
      :isLoading="isLoading"
      :tokenUsage="tokenUsage"
      :isMatching="isMatching"
      @toggle-collapse="toggleManagementCollapse"
      @refresh="refreshData"
      @update-search="searchTerm = $event"
      @select-all="selectAll"
      @clear-selection="clearSelection"
      @toggle-selection="toggleSelection"
      @batch-delete="batchDelete"
      @export="exportJSON"
      @toggle-edit="toggleEdit"
      @cancel-edit="cancelEdit"
      @delete-record="deleteRecord"
      @update-draft="updateDraftField"
    />
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, onMounted } from "vue";
import { useCategoryMatcher } from "@/composables/useCategoryMatcher";
import { useCategoryHistory } from "@/composables/useCategoryHistory";
import * as api from "@/services/api";

// 异步加载组件
const CategoryMatcherHeader = defineAsyncComponent(
  () => import("@/components/category-matcher/CategoryMatcherHeader.vue")
);
const CategoryMatcherForm = defineAsyncComponent(
  () => import("@/components/category-matcher/CategoryMatcherForm.vue")
);
const CategoryMatcherResult = defineAsyncComponent(
  () => import("@/components/category-matcher/CategoryMatcherResult.vue")
);
const CategoryMatcherHistory = defineAsyncComponent(
  () => import("@/components/category-matcher/CategoryMatcherHistory.vue")
);

// 使用 Composables
// History 逻辑提升到父组件
const {
  stats,
  managementCollapsed,
  searchTerm,
  selectedIndices,
  editModes,
  editDrafts,
  filteredProfiles,
  isLoading,
  toggleManagementCollapse,
  initManagementCollapse,
  refreshData,
  selectAll,
  clearSelection,
  toggleSelection,
  batchDelete,
  exportJSON,
  toggleEdit,
  cancelEdit,
  deleteRecord,
  updateDraftField,
} = useCategoryHistory();

// Matcher 逻辑
const {
  formState,
  isMatching,
  isOptimizing,
  runningMessage,
  matchCompleted,
  results,
  tokenUsage,
  currentProgress,
  showProgress,
  optimizeDescription,
  startMatching,
  restoreRunningTask,
} = useCategoryMatcher();

// 包装 startMatching 以传递 refreshData 回调
// 现在可以直接使用 refreshData，不再需要 ref
const handleMatch = () => startMatching(refreshData);

onMounted(async () => {
  // 初始化折叠状态
  initManagementCollapse();

  // 初始化服务
  try {
    await api.initializeService();
  } catch {}

  // 初始加载历史数据
  await refreshData();

  // 恢复运行中的任务（如果有）
  await restoreRunningTask(refreshData);
});
</script>
