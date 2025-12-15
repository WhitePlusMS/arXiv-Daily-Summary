<template>
  <div class="ui-container">
    <!-- 页面头部 -->
    <DashboardHeader />

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <!-- 用户配置区域 -->
      <UserProfileSection />

      <!-- 研究兴趣区域 -->
      <ResearchInterestsSection />

      <!-- 推荐系统区域 (包含高级选项) -->
      <RecommendationControls
        :isRunning="isRunning"
        @runMain="runMainRecommendation"
        @runDate="runSpecificDateRecommendation"
      />
    </div>

    <!-- 进度显示区域 -->
    <div v-if="showProgress" class="dashboard-progress">
      <ProgressDisplay :progress="currentProgress" title="推荐系统运行进度" :show-logs="true" />
    </div>

    <!-- 运行状态和结果区域 -->
    <StatusSection
      :isRunning="isRunning"
      :showProgress="showProgress"
      :runningMessage="runningMessage"
    />

    <!-- 历史报告区域 -->
    <ReportHistorySection />
  </div>
</template>

<script setup lang="ts">
import { onMounted, defineAsyncComponent } from "vue";
import { useArxivStore } from "@/stores/arxiv";
import ProgressDisplay from "@/components/ProgressDisplay.vue";

// Components
import DashboardHeader from "@/components/dashboard/DashboardHeader.vue";
import UserProfileSection from "@/components/dashboard/UserProfileSection.vue";
import ResearchInterestsSection from "@/components/dashboard/ResearchInterestsSection.vue";
import RecommendationControls from "@/components/dashboard/RecommendationControls.vue";
import StatusSection from "@/components/dashboard/StatusSection.vue";

// Async Components
const ReportHistorySection = defineAsyncComponent(
  () => import("@/components/dashboard/ReportHistorySection.vue")
);

// Composables
import { useRecommendation } from "@/composables/useRecommendation";

const store = useArxivStore();

const {
  isRunning,
  runningMessage,
  currentProgress,
  showProgress,
  runMainRecommendation,
  runSpecificDateRecommendation,
  restoreRunningTask,
} = useRecommendation();

onMounted(async () => {
  store.setLoading(true);
  try {
    await store.initializeData();
    await restoreRunningTask();
  } catch (err) {
    store.setError("初始化应用时发生错误");
    console.error("初始化错误:", err);
  } finally {
    store.setLoading(false);
  }
});
</script>
