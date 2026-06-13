import { ref } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";
import * as api from "@/services/api";
import { progressService } from "@/services/progress";
import type { ProgressData, TemplateErrorDetail } from "@/types";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function useRecommendation() {
  const store = useArxivStore();
  const { selectedProfileName, hasValidConfig, hasResearchInterests } = storeToRefs(store);

  const isRunning = ref(false);
  const runningMessage = ref("");

  const currentTaskId = ref<string | null>(null);
  const currentProgress = ref<ProgressData | null>(null);
  const showProgress = ref(false);

  const RUNNING_TASK_KEY = "arxiv_running_task_id";

  // Helper to refresh reports in store
  const refreshStoreReports = async () => {
    const username = selectedProfileName.value === "自定义" ? undefined : selectedProfileName.value;
    await store.fetchRecentReports(username);
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

  const handleRecommendationResponse = async (response: {
    success: boolean;
    data?: unknown;
    message?: string;
    template_error?: TemplateErrorDetail;
  }) => {
    // 检查是否返回了task_id（新的异步模式）
    const respData = isRecord(response.data) ? response.data : undefined;
    if (response.success && typeof respData?.task_id === "string") {
      const taskId = respData.task_id;
      currentTaskId.value = taskId;
      showProgress.value = true;

      try {
        localStorage.setItem(RUNNING_TASK_KEY, taskId);
      } catch (e) {
        console.warn("无法保存task_id到localStorage:", e);
      }

      progressService.startPolling(
        taskId,
        (progress) => {
          currentProgress.value = progress;
        },
        async (progress) => {
          console.log("推荐任务完成", progress);
          isRunning.value = false;
          try {
            localStorage.removeItem(RUNNING_TASK_KEY);
          } catch (e) {
            console.warn("无法清除localStorage:", e);
          }
          await refreshStoreReports();
          store.setError("");
        },
        (error) => {
          console.error("推荐任务失败", error);
          isRunning.value = false;
          try {
            localStorage.removeItem(RUNNING_TASK_KEY);
          } catch (e) {
            console.warn("无法清除localStorage:", e);
          }
          store.setError(error);
        }
      );
    } else {
      store.setLastRecommendationResult(response);

      if (!response.success) {
        const tmpl = response.template_error;
        if (tmpl?.friendly_message) {
          const tips =
            Array.isArray(tmpl.fix_suggestions) && tmpl.fix_suggestions.length
              ? `\n修复建议：\n• ${tmpl.fix_suggestions.join("\n• ")}`
              : "";
          store.setError(`${tmpl.friendly_message}${tips}`);
        } else {
          store.setError(response.message || "推荐执行失败");
        }
      } else {
        await refreshStoreReports();
      }
      isRunning.value = false;
    }
  };

  const runMainRecommendation = async () => {
    if (!hasResearchInterests.value) {
      store.setError("请先输入研究兴趣！");
      return;
    }

    if (!hasValidConfig.value) {
      store.setError(
        "DashScope API Key 未配置，请检查 .env 文件（或切换 正文分析与报告模型提供方）。"
      );
      return;
    }

    const initSuccess = await initializeComponents();
    if (!initSuccess) return;

    isRunning.value = true;
    runningMessage.value = "🚀 启动推荐系统...";

    try {
      const response = await api.runRecommendation({
        profile_name: selectedProfileName.value,
      });
      await handleRecommendationResponse(response);
    } catch (err: unknown) {
      handleError(err);
    } finally {
      runningMessage.value = "";
    }
  };

  const runSpecificDateRecommendation = async (targetDate: string) => {
    if (!hasResearchInterests.value) {
      store.setError("请先输入研究兴趣！");
      return;
    }

    if (!hasValidConfig.value) {
      store.setError(
        "DashScope API Key 未配置，请检查 .env 文件（或切换 正文分析与报告模型提供方）。"
      );
      return;
    }

    const initSuccess = await initializeComponents();
    if (!initSuccess) return;

    isRunning.value = true;
    runningMessage.value = `🚀 启动查询 ${targetDate} 的论文...`;

    try {
      const response = await api.runRecommendation({
        profile_name: selectedProfileName.value,
        target_date: targetDate,
      });
      await handleRecommendationResponse(response);
    } catch (err: unknown) {
      handleError(err);
    } finally {
      runningMessage.value = "";
    }
  };

  const handleError = (err: unknown) => {
    const getMsg = (e: unknown): string => {
      const obj = e as { code?: string; message?: string; name?: string };
      const msg = String(obj?.message || "");
      if (obj?.code === "ECONNABORTED" || msg.toLowerCase().includes("timeout")) {
        return "请求超时（生成报告可能较慢）。请稍后重试。";
      }
      if (msg.includes("ERR_ABORTED") || obj?.name === "CanceledError") {
        return "请求被取消（页面刷新或HMR导致）。请重试。";
      }
      return "执行推荐时发生错误";
    };
    store.setError(getMsg(err));
    console.error("执行推荐错误:", err);
    isRunning.value = false;
  };

  const restoreRunningTask = async () => {
    try {
      const savedTaskId = localStorage.getItem(RUNNING_TASK_KEY);
      if (!savedTaskId) return;

      const progressResponse = await api.getTaskProgress(savedTaskId);
      if (progressResponse.success && progressResponse.data) {
        const progress = progressResponse.data as ProgressData;

        if (progress.status === "running") {
          console.log("恢复运行中的任务:", savedTaskId);
          currentTaskId.value = savedTaskId;
          currentProgress.value = progress;
          showProgress.value = true;
          isRunning.value = true;

          progressService.startPolling(
            savedTaskId,
            (updatedProgress) => {
              currentProgress.value = updatedProgress;
            },
            async (finalProgress) => {
              console.log("恢复的任务已完成", finalProgress);
              isRunning.value = false;
              localStorage.removeItem(RUNNING_TASK_KEY);
              await refreshStoreReports();
              store.setError("");
            },
            (error) => {
              console.error("恢复的任务失败", error);
              isRunning.value = false;
              localStorage.removeItem(RUNNING_TASK_KEY);
              store.setError(error);
            }
          );
        } else {
          localStorage.removeItem(RUNNING_TASK_KEY);
        }
      } else {
        localStorage.removeItem(RUNNING_TASK_KEY);
      }
    } catch (err) {
      console.warn("恢复任务失败:", err);
      localStorage.removeItem(RUNNING_TASK_KEY);
    }
  };

  return {
    isRunning,
    runningMessage,
    currentTaskId,
    currentProgress,
    showProgress,
    runMainRecommendation,
    runSpecificDateRecommendation,
    restoreRunningTask,
  };
}
