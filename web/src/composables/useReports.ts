import { ref, computed } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";
import * as api from "@/services/api";
import type { ReportItem } from "@/types";

export function useReports() {
  const store = useArxivStore();
  const { recentReports, isLoading } = storeToRefs(store);

  // 历史报告筛选
  const selectedReportFilter = ref("");
  // 历史报告搜索
  const reportSearchText = ref("");
  // 历史报告区域折叠状态
  const showHistorySection = ref(true);
  
  // 预览相关
  const showPreviewModal = ref(false);
  const previewContent = ref("");

  // 过滤后的报告列表
  const filteredReports = computed(() => {
    if (!reportSearchText.value.trim()) {
      return recentReports.value;
    }
    const searchLower = reportSearchText.value.toLowerCase().trim();
    return recentReports.value.filter((report: ReportItem) => {
      return report.name.toLowerCase().includes(searchLower);
    });
  });

  const toggleHistorySection = () => {
    showHistorySection.value = !showHistorySection.value;
  };

  const loadRecentReports = async () => {
    store.setLoading(true);
    store.clearError();

    try {
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

  return {
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
  };
}
