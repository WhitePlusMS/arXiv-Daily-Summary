<template>
  <div class="streamlit-dashboard">
    <!-- 页面头部 - 优化布局 -->
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

    <!-- 错误提示 -->
    <div v-if="error" class="streamlit-error">
      {{ error }}
    </div>

    <!-- 主要内容区域 - 单栏布局，按逻辑顺序排列 -->
    <div class="dashboard-content">
      <!-- 用户配置区域 -->
      <div class="streamlit-section">
        <h2 class="streamlit-subheader">👤 用户配置</h2>
        <div class="streamlit-selectbox">
          <label>选择用户配置：</label>
          <select
            v-model="selectedProfileName"
            @change="handleProfileChange"
            :disabled="isLoading"
            class="streamlit-select"
          >
            <option value="自定义">自定义</option>
            <option v-for="profile in userProfiles" :key="profile.username" :value="profile.username">
              {{ profile.username }}
            </option>
          </select>
        </div>

        <!-- 用户配置成功信息 -->
        <div v-if="selectedProfile && selectedProfileName !== '自定义'" class="streamlit-success">
          <div class="success-content">
            <strong>✅ 已加载用户 {{ selectedProfileName }} 的配置</strong>
            <br /><br />
            <strong>分类标签</strong>: <code>{{ selectedProfile.category_id || "未设置" }}</code>
            <br /><br />
            <strong>研究兴趣</strong>:
            <pre class="research-interests-code">{{ selectedProfile.user_input || "未设置" }}</pre>
          </div>
        </div>
      </div>

      <!-- 研究兴趣区域 -->
      <div class="streamlit-section">
        <h2 class="streamlit-subheader">🎯 研究兴趣</h2>
        <div class="streamlit-text-area">
          <label>（A）感兴趣的研究方向：</label>
          <textarea
            v-model="interestsText"
            placeholder="输入您感兴趣的研究方向，系统将基于这些方向推荐相关论文"
            :disabled="isLoading"
            class="streamlit-textarea"
          ></textarea>
        </div>
        <div class="streamlit-text-area" style="margin-top: 1rem;">
          <label>（B）不感兴趣的研究方向（可选）：</label>
          <textarea
            v-model="negativeInterestsText"
            placeholder="输入您不太感兴趣的研究方向，系统会降低相关论文的推荐优先级"
            :disabled="isLoading"
            class="streamlit-textarea"
          ></textarea>
        </div>
      </div>

      <!-- 推荐系统区域 -->
      <div class="streamlit-section">
        <h2 class="streamlit-subheader">🚀 运行推荐系统</h2>

        <!-- 调试模式警告 -->
        <div v-if="isDebugMode" class="streamlit-warning">
          🔧 <strong>调试模式已启用</strong> - 系统将使用模拟数据，不会调用真实的ArXiv API和LLM服务
        </div>

        <!-- 主推荐按钮 -->
        <div class="button-group">
          <button
            @click="runMainRecommendation"
            :disabled="isLoading || !hasResearchInterests"
            class="streamlit-button streamlit-button-primary"
          >
            🔍 生成最新推荐报告
          </button>
          <div class="streamlit-help">将优先查询：{{ yesterdayStr }}，若无则：{{ prevStr }}</div>
        </div>
      </div>

      <!-- 高级选项 -->
      <div class="streamlit-section">
        <div
          class="streamlit-expander-header"
          @click="toggleAdvancedOptions"
          :class="{ expanded: showAdvancedOptions }"
        >
          <span class="expander-icon">{{ showAdvancedOptions ? "▼" : "▶" }}</span>
          🔧 高级选项：查询特定日期的报告
        </div>
        <div v-show="showAdvancedOptions" class="streamlit-expander-content">
          <div class="streamlit-markdown">
            <p>💡 <strong>提示：</strong> 如果您需要查看特定日期的论文推荐，可以在这里指定日期。</p>
            <p>
              ⚠️ <strong>注意：</strong> ArXiv通常在周日至周四发布论文，周五和周六不发布新论文。
            </p>
          </div>

          <div class="streamlit-date-input">
            <label>选择查询日期</label>
            <input type="date" v-model="selectedDate" :max="todayStr" class="streamlit-date" />
            <div class="streamlit-help">选择您想要查询论文的日期</div>
          </div>

          <button
            @click="runSpecificDateRecommendation"
            :disabled="isLoading"
            class="streamlit-button"
          >
            🔍 查询指定日期（{{ selectedDate }}）
          </button>
        </div>
      </div>
    </div>

    <!-- 进度显示区域 -->
    <div v-if="showProgress" class="dashboard-progress">
      <ProgressDisplay :progress="currentProgress" title="推荐系统运行进度" :show-logs="true" />
    </div>

    <!-- 运行状态和结果区域（兼容旧模式） -->
    <div v-if="(isRunning && !showProgress) || lastRecommendationResult" class="dashboard-results">
      <!-- 运行状态区域 -->
      <div v-if="isRunning && !showProgress" class="streamlit-section">
        <h2 class="streamlit-subheader">📋 运行状态</h2>
        <div class="streamlit-spinner">
          <div class="spinner"></div>
          <span>{{ runningMessage }}</span>
        </div>
      </div>

      <!-- 推荐结果 -->
      <div v-if="lastRecommendationResult" class="streamlit-section">
        <h2 class="streamlit-subheader">📊 推荐结果</h2>
        <div v-if="lastRecommendationResult.success" class="streamlit-success">
          <strong>✅ {{ lastRecommendationResult.message }}</strong>
          <div v-if="lastRecommendationResult.report_path" class="result-details">
            <p><strong>报告路径：</strong>{{ lastRecommendationResult.report_path }}</p>
            <p v-if="lastRecommendationResult.execution_time">
              <strong>执行时间：</strong>{{ lastRecommendationResult.execution_time }}秒
            </p>
          </div>
        </div>
        <div v-else class="streamlit-error">❌ {{ lastRecommendationResult.message }}</div>
      </div>
    </div>

    <!-- 历史报告区域 -->
    <div class="streamlit-section dashboard-history">
      <div
        class="streamlit-expander-header"
        @click="toggleHistorySection"
        :class="{ expanded: showHistorySection }"
      >
        <span class="expander-icon">{{ showHistorySection ? "▼" : "▶" }}</span>
        <h2 class="streamlit-subheader" style="margin: 0; flex: 1;">📁 历史报告管理</h2>
      </div>
      <div v-show="showHistorySection" class="streamlit-expander-content">
        <!-- 筛选和搜索控制区域 -->
        <div class="history-controls">
          <div class="streamlit-selectbox">
            <label>筛选用户：</label>
            <select
              v-model="selectedReportFilter"
              @change="loadRecentReports"
              :disabled="isLoading"
              class="streamlit-select"
            >
              <option value="">全部</option>
              <option v-for="profile in userProfiles" :key="profile.username" :value="profile.username">
                {{ profile.username }}
              </option>
            </select>
          </div>
          <div class="streamlit-text-input">
            <label>搜索报告：</label>
            <input
              v-model="reportSearchText"
              type="text"
              placeholder="输入关键词搜索..."
              :disabled="isLoading"
              class="streamlit-input"
            />
          </div>
          <div class="history-refresh-button">
            <button @click="loadRecentReports" :disabled="isLoading" class="streamlit-button streamlit-button-small">
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
                class="streamlit-button streamlit-button-small"
                title="下载Markdown版本"
              >
                📄 MD
              </button>
              <button
                @click="downloadReport(report, 'html')"
                class="streamlit-button streamlit-button-small"
                title="下载HTML版本"
              >
                🌐 HTML
              </button>
              <button
                @click="previewReport(report)"
                class="streamlit-button streamlit-button-small"
                title="预览报告"
              >
                👁️ 预览
              </button>
              <button
                @click="deleteReport(report)"
                class="streamlit-button streamlit-button-small streamlit-button-danger"
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
    </div>

    <!-- 预览模态框 -->
    <div v-if="showPreviewModal" class="modal-overlay" @click="closePreviewModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>📄 报告预览</h3>
          <button @click="closePreviewModal" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div v-html="previewContent" class="preview-content"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";
import * as api from "@/services/api";
import type { ReportItem, ProgressData } from "@/types";
import { progressService } from "@/services/progress";
import ProgressDisplay from "@/components/ProgressDisplay.vue";

// 使用store
const store = useArxivStore();

// 响应式数据
const localTime = ref("");
const arxivTime = ref("");
const localTimezone = ref("");
const arxivTimezone = ref("");
const interestsText = ref("");
const negativeInterestsText = ref("");
const selectedDate = ref("");
const todayStr = ref("");
const yesterdayStr = ref("");
const prevStr = ref("");
const showAdvancedOptions = ref(false);
const isRunning = ref(false);
const runningMessage = ref("");
// 使用 store 中的选中配置，避免本地重复状态
const showPreviewModal = ref(false);
const previewContent = ref("");
// 历史报告筛选
const selectedReportFilter = ref("");
// 历史报告搜索
const reportSearchText = ref("");
// 历史报告区域折叠状态
const showHistorySection = ref(true);

// 进度相关状态
const currentTaskId = ref<string | null>(null);
const currentProgress = ref<ProgressData | null>(null);
const showProgress = ref(false);

// 计算属性（使用 storeToRefs 保持响应性）
const {
  config,
  userProfiles,
  researchInterests,
  negativeInterests,
  selectedProfile,
  selectedProfileName,
  isLoading,
  error,
  lastRecommendationResult,
  recentReports,
  isDebugMode,
  hasValidConfig,
  hasResearchInterests,
} = storeToRefs(store);

// 过滤后的报告列表（根据搜索文本进行模糊匹配）
const filteredReports = computed(() => {
  if (!reportSearchText.value.trim()) {
    return recentReports.value;
  }
  const searchLower = reportSearchText.value.toLowerCase().trim();
  return recentReports.value.filter((report: ReportItem) => {
    return report.name.toLowerCase().includes(searchLower);
  });
});

// 方法
const updateTime = () => {
  const now = new Date();

  // 本地时间
  localTime.value = now.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  // 获取本地时区
  const localTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  localTimezone.value = localTz;

  // ArXiv时间 (US/Eastern)
  const arxivDate = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  arxivTime.value = arxivDate.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  // 判断是否为夏令时
  const january = new Date(now.getFullYear(), 0, 1);
  const july = new Date(now.getFullYear(), 6, 1);
  const stdOffset = Math.max(january.getTimezoneOffset(), july.getTimezoneOffset());
  const isDST = now.getTimezoneOffset() < stdOffset;
  arxivTimezone.value = isDST ? "EDT" : "EST";
};

const updateDates = () => {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const prev = new Date(today);
  prev.setDate(today.getDate() - 2);

  todayStr.value = today.toISOString().split("T")[0];
  yesterdayStr.value = yesterday.toISOString().split("T")[0];
  prevStr.value = prev.toISOString().split("T")[0];
  selectedDate.value = yesterdayStr.value;
};

const handleProfileChange = () => {
  store.setSelectedProfile(selectedProfileName.value);
  // 当选择用户配置时，自动同步历史报告筛选
  if (selectedProfileName.value && selectedProfileName.value !== "自定义") {
    selectedReportFilter.value = selectedProfileName.value;
    // 自动刷新报告列表
    loadRecentReports();
  }
};

const toggleAdvancedOptions = () => {
  showAdvancedOptions.value = !showAdvancedOptions.value;
};

const toggleHistorySection = () => {
  showHistorySection.value = !showHistorySection.value;
};

const initializeComponents = async () => {
  isRunning.value = true;
  runningMessage.value = "正在初始化系统组件...";

  try {
    const response = await api.initializeComponents({
      profile_name: selectedProfileName.value,
    });

    if (!response.success) {
      store.setError(response.message || "初始化组件失败");
      return false;
    }
    return true;
  } catch (err) {
    store.setError("初始化组件时发生错误");
    console.error("初始化组件错误:", err);
    return false;
  } finally {
    isRunning.value = false;
    runningMessage.value = "";
  }
};

const runMainRecommendation = async () => {
  if (!hasResearchInterests.value) {
    store.setError("请先输入研究兴趣！");
    return;
  }

  if (!hasValidConfig.value) {
    store.setError('DashScope API Key 未配置，请检查 .env 文件（或切换 正文分析与报告模型提供方）。')
    return;
  }

  // 先初始化组件
  const initSuccess = await initializeComponents();
  if (!initSuccess) return;

  // 运行推荐（异步模式）
  isRunning.value = true;
  runningMessage.value = "🚀 启动推荐系统...";

  try {
    const response = await api.runRecommendation({
      profile_name: selectedProfileName.value,
      debug_mode: isDebugMode.value,
    });

    // 检查是否返回了task_id（新的异步模式）
    if (response.success && response.data && (response.data as any).task_id) {
      const taskId = (response.data as any).task_id;
      currentTaskId.value = taskId;
      showProgress.value = true;
      
      // 开始轮询进度
      progressService.startPolling(
        taskId,
        (progress) => {
          // 更新进度
          currentProgress.value = progress;
        },
        async (progress) => {
          // 任务完成
          console.log("推荐任务完成", progress);
          showProgress.value = false;
          isRunning.value = false;
          
          // 刷新报告列表
          await loadRecentReports();
          
          // 显示成功消息
          store.setError("");  // 清除之前的错误
        },
        (error) => {
          // 任务失败
          console.error("推荐任务失败", error);
          showProgress.value = false;
          isRunning.value = false;
          store.setError(error);
        }
      );
    } else {
      // 兼容旧的同步模式或错误响应
      store.setLastRecommendationResult(response);

      if (!response.success) {
        // 模板错误友好提示（后端400）
        const tmpl = (response as any).template_error as {
          friendly_message?: string;
          fix_suggestions?: string[];
          details?: Record<string, unknown>;
        } | undefined;
        if (tmpl?.friendly_message) {
          const tips = Array.isArray(tmpl.fix_suggestions) && tmpl.fix_suggestions.length
            ? `\n修复建议：\n• ${tmpl.fix_suggestions.join("\n• ")}`
            : "";
          store.setError(`${tmpl.friendly_message}${tips}`);
        } else {
          store.setError(response.message || "推荐执行失败");
        }
      } else {
        // 推荐成功后，自动刷新历史报告列表
        await loadRecentReports();
      }
      isRunning.value = false;
    }
  } catch (err: unknown) {
    const getMsg = (e: unknown): string => {
      const obj = e as { code?: string; message?: string; name?: string };
      const msg = String(obj?.message || "");
      if (obj?.code === "ECONNABORTED" || msg.toLowerCase().includes("timeout")) {
        return "请求超时（生成报告可能较慢）。请稍后重试或启用调试模式。";
      }
      if (msg.includes("ERR_ABORTED") || obj?.name === "CanceledError") {
        return "请求被取消（页面刷新或HMR导致）。请重试。";
      }
      return "执行推荐时发生错误";
    };
    store.setError(getMsg(err));
    console.error("执行推荐错误:", err);
    isRunning.value = false;
    showProgress.value = false;
  } finally {
    runningMessage.value = "";
  }
};

const runSpecificDateRecommendation = async () => {
  if (!hasResearchInterests.value) {
    store.setError("请先输入研究兴趣！");
    return;
  }

  if (!hasValidConfig.value) {
    store.setError('DashScope API Key 未配置，请检查 .env 文件（或切换 正文分析与报告模型提供方）。')
    return;
  }

  // 先初始化组件
  const initSuccess = await initializeComponents();
  if (!initSuccess) return;

  // 运行特定日期推荐（异步模式）
  isRunning.value = true;
  runningMessage.value = `🚀 启动查询 ${selectedDate.value} 的论文...`;

  try {
    const response = await api.runRecommendation({
      profile_name: selectedProfileName.value,
      debug_mode: isDebugMode.value,
      target_date: selectedDate.value,
    });

    // 检查是否返回了task_id（新的异步模式）
    if (response.success && response.data && (response.data as any).task_id) {
      const taskId = (response.data as any).task_id;
      currentTaskId.value = taskId;
      showProgress.value = true;
      
      // 开始轮询进度
      progressService.startPolling(
        taskId,
        (progress) => {
          // 更新进度
          currentProgress.value = progress;
        },
        async (progress) => {
          // 任务完成
          console.log("推荐任务完成", progress);
          showProgress.value = false;
          isRunning.value = false;
          
          // 刷新报告列表
          await loadRecentReports();
          
          // 显示成功消息
          store.setError("");  // 清除之前的错误
        },
        (error) => {
          // 任务失败
          console.error("推荐任务失败", error);
          showProgress.value = false;
          isRunning.value = false;
          store.setError(error);
        }
      );
    } else {
      // 兼容旧的同步模式或错误响应
      store.setLastRecommendationResult(response);

      if (!response.success) {
        const tmpl = (response as any).template_error as {
          friendly_message?: string;
          fix_suggestions?: string[];
          details?: Record<string, unknown>;
        } | undefined;
        if (tmpl?.friendly_message) {
          const tips = Array.isArray(tmpl.fix_suggestions) && tmpl.fix_suggestions.length
            ? `\n修复建议：\n• ${tmpl.fix_suggestions.join("\n• ")}`
            : "";
          store.setError(`${tmpl.friendly_message}${tips}`);
        } else {
          store.setError(response.message || "推荐执行失败");
        }
      } else {
        // 推荐成功后，自动刷新历史报告列表
        await loadRecentReports();
      }
      isRunning.value = false;
    }
  } catch (err: unknown) {
    const getMsg = (e: unknown): string => {
      const obj = e as { code?: string; message?: string; name?: string };
      const msg = String(obj?.message || "");
      if (obj?.code === "ECONNABORTED" || msg.toLowerCase().includes("timeout")) {
        return `请求超时（生成 ${selectedDate.value} 的报告可能较慢）。请稍后重试或启用调试模式。`;
      }
      if (msg.includes("ERR_ABORTED") || obj?.name === "CanceledError") {
        return "请求被取消（页面刷新或HMR导致）。请重试。";
      }
      return "执行推荐时发生错误";
    };
    store.setError(getMsg(err));
    console.error("执行推荐错误:", err);
    isRunning.value = false;
    showProgress.value = false;
  } finally {
    runningMessage.value = "";
  }
};

const loadRecentReports = async () => {
  store.setLoading(true);
  store.clearError();

  try {
    // 根据筛选条件调用 API，如果选择"全部"则传入 undefined
    const username = selectedReportFilter.value || undefined;
    const response = await api.getRecentReports(username);

    if (response.success && response.data) {
      store.setRecentReports(response.data);
    } else {
      store.setError(response.message || "加载报告失败");
    }
  } catch (err) {
    store.setError("加载报告时发生错误");
    console.error("加载报告错误:", err);
  } finally {
    store.setLoading(false);
  }
};

const downloadReport = async (report: ReportItem, format: "md" | "html") => {
  // 后端要求 name 不含扩展名；最近报告返回的 name 含扩展名，需去掉
  const baseName = report.name.replace(/\.(md|html)$/i, "");
  const url = api.getReportDownloadUrl({ name: baseName, format });
  const link = document.createElement("a");
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener";
  link.click();
};

const previewReport = async (report: ReportItem) => {
  try {
    const fmt: "md" | "html" = "html";
    const baseName = report.name.replace(/\.(md|html)$/i, "");
    const res = await api.previewReport({ name: baseName, format: fmt });
    if (res.success && res.data?.content) {
      // HTML 直接渲染；Markdown 简单包裹在 <pre>
      previewContent.value = fmt === "html" ? res.data.content : `<pre>${res.data.content}</pre>`;
      showPreviewModal.value = true;
    } else {
      store.setError(res.message || "预览失败");
    }
  } catch (err) {
    store.setError("预览报告时发生错误");
    console.error("预览错误:", err);
  }
};

const deleteReport = async (report: ReportItem) => {
  if (confirm(`确定要删除报告 "${report.name}" 的 MD 文件吗？`)) {
    try {
      const baseName = report.name.replace(/\.(md|html)$/i, "");
      const resMd = await api.deleteReportFile({ name: baseName, format: "md" });
      const resHtml = await api.deleteReportFile({ name: baseName, format: "html" });
      if (resMd.success || resHtml.success) {
        await loadRecentReports();
      } else {
        store.setError("删除报告失败");
      }
    } catch (err) {
      store.setError("删除报告时发生错误");
      console.error("删除错误:", err);
    }
  }
};

const closePreviewModal = () => {
  showPreviewModal.value = false;
  previewContent.value = "";
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString("zh-CN");
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// 监听研究兴趣变化，更新文本框
watch(
  researchInterests,
  (newInterests) => {
    interestsText.value = newInterests.join("\n");
  },
  { immediate: true }
);

// 监听负面偏好变化，更新文本框
watch(
  negativeInterests,
  (newInterests) => {
    negativeInterestsText.value = newInterests.join("\n");
  },
  { immediate: true }
);

// 监听文本框变化，自动更新研究兴趣
watch(interestsText, (newText) => {
  if (newText.trim()) {
    const interests = newText.split("\n").filter((line) => line.trim());
    store.setResearchInterests(interests);
  }
});

// 监听负面偏好文本框变化，自动更新负面偏好
watch(negativeInterestsText, (newText) => {
  const interests = newText.trim() ? newText.split("\n").filter((line) => line.trim()) : [];
  store.setNegativeInterests(interests);
});

// 初始化
onMounted(async () => {
  // 更新时间和日期
  updateTime();
  updateDates();
  setInterval(updateTime, 1000);

  // 初始化服务
  store.setLoading(true);

  try {
    // 初始化服务
    await api.initializeService();

    // 加载配置
    const configResponse = await api.getConfig();
    if (configResponse.success && configResponse.data) {
      store.setConfig(configResponse.data);
    }

    // 加载用户配置
    const profilesResponse = await api.getUserProfiles();
    if (profilesResponse.success && profilesResponse.data) {
      store.setUserProfiles(profilesResponse.data);
      // 若当前未选择任何配置，默认设为“自定义”，避免下拉框出现空白
      if (!selectedProfileName.value) {
        selectedProfileName.value = "自定义";
      }
      // 同步选中配置（默认“自定义”不加载具体配置）
      handleProfileChange();
    }

    // 加载研究兴趣
    const interestsResponse = await api.getResearchInterests();
    if (interestsResponse.success && interestsResponse.data) {
      store.setResearchInterests(interestsResponse.data);
    }

    // 页面初始化完成后，加载最近报告列表
    await loadRecentReports();
  } catch (err) {
    store.setError("初始化应用时发生错误");
    console.error("初始化错误:", err);
  } finally {
    store.setLoading(false);
  }
});
</script>
