<template>
  <div class="ui-card dashboard-history">
    <div
      class="ui-expander-header"
      @click="toggleHistorySection"
      :class="{ expanded: showHistorySection }"
    >
      <span class="ui-expander-icon">{{ showHistorySection ? "▼" : "▶" }}</span>
      <h2 class="ui-subheader" style="margin: 0; flex: 1">📁 历史报告管理</h2>
    </div>
    <div v-show="showHistorySection" class="ui-expander-content">
      <!-- 筛选和搜索控制区域 -->
      <div class="history-controls">
        <div class="ui-form-group">
          <label>筛选用户：</label>
          <select
            v-model="selectedReportFilter"
            @change="loadRecentReports"
            :disabled="isLoading"
            class="ui-select"
          >
            <option value="">全部</option>
            <option
              v-for="profile in userProfiles"
              :key="profile.username"
              :value="profile.username"
            >
              {{ profile.username }}
            </option>
          </select>
        </div>
        <div class="ui-form-group">
          <label>搜索报告：</label>
          <input
            v-model="reportSearchText"
            type="text"
            placeholder="输入关键词搜索..."
            :disabled="isLoading"
            class="ui-input"
          />
        </div>
        <div class="history-refresh-button">
          <button
            @click="loadRecentReports"
            :disabled="isLoading"
            class="ui-button ui-button-small"
          >
            {{ isLoading ? "加载中..." : "🔄 刷新" }}
          </button>
        </div>
      </div>

      <!-- 报告列表 -->
      <div v-if="filteredReports.length > 0" class="reports-section">
        <div v-for="report in filteredReports" :key="report.name" class="report-item">
          <div class="report-info">
            <div class="report-name">{{ report.name }}</div>
            <div class="report-meta">
              <span class="report-date">{{ formatDate(report.date) }}</span>
              <span class="report-size">{{ formatFileSize(report.size) }}</span>
            </div>
          </div>
          <div class="report-actions">
            <button
              @click="downloadReport(report, 'md')"
              class="ui-button ui-button-small"
              title="下载Markdown版本"
            >
              📄 MD
            </button>
            <button
              @click="downloadReport(report, 'html')"
              class="ui-button ui-button-small"
              title="下载HTML版本"
            >
              🌐 HTML
            </button>
            <button
              @click="previewReport(report)"
              class="ui-button ui-button-small"
              title="预览报告"
            >
              👁️ 预览
            </button>
            <button
              @click="deleteReport(report)"
              class="ui-button ui-button-small ui-button-danger"
              title="删除报告"
            >
              🗑️ 删除
            </button>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <p v-if="reportSearchText">未找到匹配的报告</p>
        <p v-else>暂无历史报告</p>
      </div>
    </div>

    <!-- 预览模态框 (Moved inside) -->
    <ReportPreviewModal
      :show="showPreviewModal"
      :content="previewContent"
      :onClose="closePreviewModal"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";
import { useReports } from "@/composables/useReports";
import ReportPreviewModal from "@/components/dashboard/ReportPreviewModal.vue";

const store = useArxivStore();
const { userProfiles, isLoading, selectedProfileName } = storeToRefs(store);

const {
  selectedReportFilter,
  reportSearchText,
  showHistorySection,
  filteredReports,
  showPreviewModal,
  previewContent,
  toggleHistorySection,
  loadRecentReports,
  downloadReport,
  previewReport,
  deleteReport,
  closePreviewModal,
  formatDate,
  formatFileSize,
} = useReports();

// Sync selected profile filter when global profile changes
watch(selectedProfileName, (newVal) => {
  if (newVal && newVal !== "自定义") {
    selectedReportFilter.value = newVal;
    loadRecentReports();
  }
});

// Initial load
onMounted(() => {
  loadRecentReports();
});
</script>
