<template>
  <div class="streamlit-dashboard">
    <!-- 页面头部 - 完全复制Streamlit样式 -->
    <div class="streamlit-header">
      <h1 class="streamlit-title">📚 ArXiv 每日论文推荐系统</h1>
      <div class="streamlit-caption">
        当前时间: {{ localTime }} ({{ localTimezone }}) | ArXiv时间: {{ arxivTime }} ({{
          arxivTimezone
        }})
      </div>
    </div>

    <!-- 错误提示 - Streamlit样式 -->
    <div v-if="error" class="streamlit-error">
      {{ error }}
    </div>

    <!-- 用户配置区域 - 完全复制Streamlit布局 -->
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

    
      <!-- 分类标签显示 -->
      <div v-if="selectedProfile && selectedProfile.category_id" class="streamlit-section">
        <h2 class="streamlit-subheader">🏷️ 分类标签</h2>
        <div class="streamlit-info">
          <code>{{ selectedProfile.category_id.replace(",", " ") }}</code>
        </div>
      </div>
    </div>

    <!-- 研究兴趣区域 - 完全复制Streamlit样式 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">🎯 研究兴趣</h2>
      <div class="streamlit-text-area">
        <label>请输入您的研究方向，描述即可：</label>
        <textarea
          v-model="interestsText"
          placeholder="输入您的研究方向，系统将基于这些方向推荐相关论文"
          :disabled="isLoading"
          class="streamlit-textarea"
        ></textarea>
        <div class="streamlit-help">输入您的研究方向，系统将基于这些方向推荐相关论文</div>
      </div>
    </div>

    <!-- 推荐系统区域 - 完全复制Streamlit布局 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">🚀 运行推荐系统</h2>

      <!-- 调试模式警告 -->
      <div v-if="isDebugMode" class="streamlit-warning">
        🔧 <strong>调试模式已启用</strong> - 系统将使用模拟数据，不会调用真实的ArXiv API和LLM服务
      </div>

      <!-- 主推荐按钮 -->
      <button
        @click="runMainRecommendation"
        :disabled="isLoading || !hasResearchInterests"
        class="streamlit-button streamlit-button-primary"
      >
        🔍 生成最新推荐报告（将优先查询：{{ yesterdayStr }}，若无则：{{ prevStr }}）
      </button>
      <div class="streamlit-help">系统将自动查找最近可用的论文并生成推荐报告</div>

      <!-- 高级选项折叠区域 -->
      <div class="streamlit-expander">
        <div
          class="streamlit-expander-header"
          @click="toggleAdvancedOptions"
          :class="{ expanded: showAdvancedOptions }"
        >
          <span class="expander-icon">{{ showAdvancedOptions ? "▼" : "▶" }}</span>
          🔧 高级选项：查询特定日期的报告
        </div>

        <div v-if="showAdvancedOptions" class="streamlit-expander-content">
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

    <!-- 运行状态区域 -->
    <div v-if="isRunning" class="streamlit-section">
      <h2 class="streamlit-subheader">📋 运行状态</h2>
      <div class="streamlit-spinner">
        <div class="spinner"></div>
        <span>{{ runningMessage }}</span>
      </div>
    </div>

    <!-- 推荐tresultult -->
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

    <!-- 历史报告区域 - 完全复制Streamlit功能 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">📁 历史报告管理</h2>

      <button @click="loadRecentReports" :disabled="isLoading" class="streamlit-button">
        {{ isLoading ? "加载中..." : "🔄 刷新报告列表" }}
      </button>

      <!-- 报告列表 -->
      <div v-if="recentReports.length > 0" class="reports-section">
        <h3 class="streamlit-subheader">📋 最近报告：</h3>
        <div v-for="report in recentReports" :key="report.name" class="report-item">
          <div class="report-info">
            <div class="report-name">{{ report.name }}</div>
            <div class="report-date">{{ formatDate(report.date) }}</div>
            <div class="report-size">{{ formatFileSize(report.size) }}</div>
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
import { ref, onMounted, watch } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";
import * as api from "@/services/api";
import type { ReportItem } from "@/types";

// 使用store
const store = useArxivStore();

// 响应式数据
const localTime = ref("");
const arxivTime = ref("");
const localTimezone = ref("");
const arxivTimezone = ref("");
const interestsText = ref("");
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

// 计算属性（使用 storeToRefs 保持响应性）
const {
  config,
  userProfiles,
  researchInterests,
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
};

const toggleAdvancedOptions = () => {
  showAdvancedOptions.value = !showAdvancedOptions.value;
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
    const provider = (config.value?.heavy_model_provider || 'dashscope').toLowerCase()
    const msg = provider === 'ollama'
      ? 'Ollama 未配置，请设置 OLLAMA_BASE_URL 并确保服务可用（或切换 正文分析与报告模型提供方）。'
      : 'DashScope API Key 未配置，请检查 .env 文件（或切换 正文分析与报告模型提供方）。'
    store.setError(msg)
    return;
  }

  // 先初始化组件
  const initSuccess = await initializeComponents();
  if (!initSuccess) return;

  // 运行推荐
  isRunning.value = true;
  runningMessage.value = "🚀 开始运行推荐系统...";

  try {
    const response = await api.runRecommendation({
      profile_name: selectedProfileName.value,
      debug_mode: isDebugMode.value,
    });

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
  } finally {
    isRunning.value = false;
    runningMessage.value = "";
  }
};

const runSpecificDateRecommendation = async () => {
  if (!hasResearchInterests.value) {
    store.setError("请先输入研究兴趣！");
    return;
  }

  if (!hasValidConfig.value) {
    const provider = (config.value?.heavy_model_provider || 'dashscope').toLowerCase()
    const msg = provider === 'ollama'
      ? 'Ollama 未配置，请设置 OLLAMA_BASE_URL 并确保服务可用（或切换 正文分析与报告模型提供方）。'
      : 'DashScope API Key 未配置，请检查 .env 文件（或切换 正文分析与报告模型提供方）。'
    store.setError(msg)
    return;
  }

  // 先初始化组件
  const initSuccess = await initializeComponents();
  if (!initSuccess) return;

  // 运行特定日期推荐
  isRunning.value = true;
  runningMessage.value = `🚀 开始查询 ${selectedDate.value} 的论文...`;

  try {
    const response = await api.runRecommendation({
      profile_name: selectedProfileName.value,
      debug_mode: isDebugMode.value,
      target_date: selectedDate.value,
    });

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
  } finally {
    isRunning.value = false;
    runningMessage.value = "";
  }
};

const loadRecentReports = async () => {
  store.setLoading(true);
  store.clearError();

  try {
    const response = await api.getRecentReports();

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

// 监听文本框变化，自动更新研究兴趣
watch(interestsText, (newText) => {
  if (newText.trim()) {
    const interests = newText.split("\n").filter((line) => line.trim());
    store.setResearchInterests(interests);
  }
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
