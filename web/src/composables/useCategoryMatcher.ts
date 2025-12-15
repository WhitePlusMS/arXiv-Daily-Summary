import { ref } from "vue";
import { useArxivStore } from "@/stores/arxiv";
import * as api from "@/services/api";
import { progressService } from "@/services/progress";
import type { ProgressData, TemplateErrorDetail } from "@/types";

const RUNNING_TASK_KEY = "arxiv_category_matcher_task_id";

export function useCategoryMatcher() {
  const store = useArxivStore();

  // State
  const formState = ref({
    username: "",
    researchDescription: "",
    negativeDescription: "",
    topN: 5,
  });

  const isMatching = ref(false);
  const isOptimizing = ref(false);
  const runningMessage = ref("");
  const matchCompleted = ref(false);
  const results = ref<{ id: string; name: string; score: number }[]>([]);
  const tokenUsage = ref({ input_tokens: 0, output_tokens: 0, total_tokens: 0 });

  // Progress State
  const currentTaskId = ref<string | null>(null);
  const currentProgress = ref<ProgressData | null>(null);
  const showProgress = ref(false);

  // Methods
  const optimizeDescription = async () => {
    if (!formState.value.researchDescription.trim()) {
      store.setError("❌ 请先输入研究内容描述");
      return;
    }
    isOptimizing.value = true;
    try {
      store.clearError();
      const resp = await api.optimizeMatcherDescription({
        user_input: formState.value.researchDescription.trim(),
      });
      if (resp.success && resp.data?.optimized) {
        formState.value.researchDescription = resp.data.optimized;
      } else {
        const tmpl = (resp as unknown as { template_error?: TemplateErrorDetail }).template_error;
        if (tmpl?.friendly_message) {
          const tips =
            Array.isArray(tmpl.fix_suggestions) && tmpl.fix_suggestions.length
              ? `\n修复建议：\n• ${tmpl.fix_suggestions.join("\n• ")}`
              : "";
          store.setError(`${tmpl.friendly_message}${tips}`);
        } else {
          store.setError("优化描述失败");
        }
      }
    } catch (err) {
      store.setError("优化描述时发生错误");
      console.error("优化错误:", err);
    } finally {
      isOptimizing.value = false;
    }
  };

  const startMatching = async (refreshDataCallback: () => Promise<void>) => {
    if (!formState.value.username.trim()) {
      store.setError("❌ 请输入用户名");
      return;
    }
    if (!formState.value.researchDescription.trim()) {
      store.setError("❌ 请输入研究内容描述");
      return;
    }
    isMatching.value = true;
    runningMessage.value = `🔄 启动分类匹配（Top ${formState.value.topN}）...`;
    try {
      store.clearError();
      const resp = await api.runCategoryMatching({
        user_input: formState.value.researchDescription.trim(),
        negative_query: formState.value.negativeDescription.trim(),
        username: formState.value.username.trim(),
        top_n: formState.value.topN,
      });

      const respData = resp.data as Record<string, unknown>;
      if (resp.success && respData && typeof respData.task_id === "string") {
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
            console.log("分类匹配完成", progress);
            isMatching.value = false;
            matchCompleted.value = true;

            // 从任务结果中提取数据
            if (progress.result) {
              const resList = (
                Array.isArray(progress.result.results) ? progress.result.results : []
              ) as Array<{
                id: string;
                name: string;
                score: number;
              }>;
              results.value = resList.map((r) => ({ id: r.id, name: r.name, score: r.score }));

              if (progress.result.token_usage) {
                const tuRaw = progress.result.token_usage as Record<string, number>;
                const input_tokens = tuRaw.input_tokens ?? 0;
                const output_tokens = tuRaw.output_tokens ?? 0;
                const total_tokens = tuRaw.total_tokens ?? 0;
                tokenUsage.value = { input_tokens, output_tokens, total_tokens };
              }
            }

            try {
              localStorage.removeItem(RUNNING_TASK_KEY);
            } catch (e) {
              console.warn("无法清除localStorage:", e);
            }

            await refreshDataCallback();
            store.setError("");
          },
          (error) => {
            console.error("分类匹配失败", error);
            isMatching.value = false;
            try {
              localStorage.removeItem(RUNNING_TASK_KEY);
            } catch (e) {
              console.warn("无法清除localStorage:", e);
            }
            store.setError(error);
          }
        );
      } else {
        if (resp.success && resp.data) {
          const resList = (Array.isArray(resp.data.results) ? resp.data.results : []) as Array<{
            id: string;
            name: string;
            score: number;
          }>;
          results.value = resList.map((r) => ({ id: r.id, name: r.name, score: r.score }));
          const tuRaw = (resp.data.token_usage || {}) as Record<string, number>;
          const input_tokens = tuRaw.input_tokens ?? 0;
          const output_tokens = tuRaw.output_tokens ?? 0;
          const total_tokens = tuRaw.total_tokens ?? 0;
          tokenUsage.value = { input_tokens, output_tokens, total_tokens };
          matchCompleted.value = true;
          await refreshDataCallback();
        } else {
          const tmpl = (resp as unknown as { template_error?: TemplateErrorDetail }).template_error;
          if (tmpl?.friendly_message) {
            const tips =
              Array.isArray(tmpl.fix_suggestions) && tmpl.fix_suggestions.length
                ? `\n修复建议：\n• ${tmpl.fix_suggestions.join("\n• ")}`
                : "";
            store.setError(`${tmpl.friendly_message}${tips}`);
          } else {
            store.setError("分类匹配失败");
          }
        }
        isMatching.value = false;
      }
    } catch (err) {
      store.setError("执行匹配时发生错误");
      console.error("匹配错误:", err);
      isMatching.value = false;
    } finally {
      runningMessage.value = "";
    }
  };

  const restoreRunningTask = async (refreshDataCallback: () => Promise<void>) => {
    try {
      const savedTaskId = localStorage.getItem(RUNNING_TASK_KEY);
      if (!savedTaskId) return;

      const progressResponse = await api.getTaskProgress(savedTaskId);
      if (progressResponse.success && progressResponse.data) {
        const progress = progressResponse.data as ProgressData;

        if (progress.status === "running") {
          console.log("恢复运行中的匹配任务:", savedTaskId);
          currentTaskId.value = savedTaskId;
          currentProgress.value = progress;
          showProgress.value = true;
          isMatching.value = true;

          progressService.startPolling(
            savedTaskId,
            (updatedProgress) => {
              currentProgress.value = updatedProgress;
            },
            async (finalProgress) => {
              console.log("恢复的匹配任务已完成", finalProgress);
              isMatching.value = false;
              matchCompleted.value = true;

              // 从任务结果中提取数据
              if (finalProgress.result) {
                const resList = (
                  Array.isArray(finalProgress.result.results) ? finalProgress.result.results : []
                ) as Array<{
                  id: string;
                  name: string;
                  score: number;
                }>;
                results.value = resList.map((r) => ({ id: r.id, name: r.name, score: r.score }));

                if (finalProgress.result.token_usage) {
                  const tuRaw = finalProgress.result.token_usage as Record<string, number>;
                  const input_tokens = tuRaw.input_tokens ?? 0;
                  const output_tokens = tuRaw.output_tokens ?? 0;
                  const total_tokens = tuRaw.total_tokens ?? 0;
                  tokenUsage.value = { input_tokens, output_tokens, total_tokens };
                }
              }

              localStorage.removeItem(RUNNING_TASK_KEY);
              await refreshDataCallback();
              store.setError("");
            },
            (error) => {
              console.error("恢复的匹配任务失败", error);
              isMatching.value = false;
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
      console.warn("恢复匹配任务失败:", err);
      localStorage.removeItem(RUNNING_TASK_KEY);
    }
  };

  return {
    formState,
    isMatching,
    isOptimizing,
    runningMessage,
    matchCompleted,
    results,
    tokenUsage,
    currentTaskId,
    currentProgress,
    showProgress,
    optimizeDescription,
    startMatching,
    restoreRunningTask,
  };
}
