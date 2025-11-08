import axios from "axios";
import type {
  ApiResponse,
  UserProfile,
  RecommendationResult,
  ReportItem,
  Category,
  PromptItem,
  TemplateErrorDetail,
} from "@/types";

// 从环境变量读取后端 API 地址，避免硬编码
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// 管理未完成请求的 AbortController，用于取消与路由切换/重复请求
const pendingControllers = new Map<string, AbortController>();

export function cancelAllRequests() {
  for (const controller of pendingControllers.values()) {
    try {
      controller.abort();
    } catch {}
  }
  pendingControllers.clear();
}

function getAbortSignal(key: string) {
  const prev = pendingControllers.get(key);
  if (prev) {
    try {
      prev.abort();
    } catch {}
  }
  const controller = new AbortController();
  pendingControllers.set(key, controller);
  return controller.signal;
}

// 创建axios实例
const api = axios.create({
  baseURL: BASE_URL,
  // 生成推荐可能较耗时（涉及抓取与LLM），提高超时时间
  timeout: 300000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 统一输出更友好的错误信息
    if (
      error?.code === "ECONNABORTED" ||
      String(error?.message).toLowerCase().includes("timeout")
    ) {
      const msg = "API请求错误: 请求超时，服务正在处理或网络较慢。";
      console.error(msg);
    } else if (String(error?.message).includes("ERR_ABORTED") || error?.name === "CanceledError") {
      const msg = "API请求错误: 请求被取消（可能是页面刷新或路由切换）。";
      console.warn(msg);
    } else {
      // 模板错误（后端400）优先显示友好文案
      const detail = error?.response?.data?.detail as TemplateErrorDetail | undefined;
      if (error?.response?.status === 400 && detail) {
        console.error("API请求错误(模板)", detail);
      } else {
        const serverMsg = error?.response?.data?.message || error?.message || "API请求错误";
        console.error("API请求错误:", serverMsg);
      }
    }
    return Promise.reject(error);
  }
);

// 规范化后端 400 模板错误为统一结构
function normalizeTemplateError(e: unknown): TemplateErrorDetail | undefined {
  const err = e as {
    response?: { status?: number; data?: { detail?: unknown } };
    message?: string;
  };
  if (err?.response?.status === 400 && err?.response?.data?.detail) {
    const d = err.response.data.detail as TemplateErrorDetail;
    return {
      error_type: String(d?.error_type || "template_exception"),
      friendly_message: d?.friendly_message,
      fix_suggestions: Array.isArray(d?.fix_suggestions) ? d.fix_suggestions : undefined,
      details: d?.details,
    };
  }
  return undefined;
}

// API服务函数
export const initializeService = async (): Promise<ApiResponse<{ initialized: boolean }>> => {
  const response = await api.post("/api/initialize", undefined, {
    signal: getAbortSignal("POST /api/initialize"),
  });
  return response.data;
};

export const getConfig = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get("/api/config", { signal: getAbortSignal("GET /api/config") });
  return response.data;
};

export const getUserProfiles = async (): Promise<ApiResponse<UserProfile[]>> => {
  const response = await api.get("/api/user-profiles", {
    signal: getAbortSignal("GET /api/user-profiles"),
  });
  return response.data;
};

export const getResearchInterests = async (): Promise<ApiResponse<string[]>> => {
  const response = await api.get("/api/research-interests", {
    signal: getAbortSignal("GET /api/research-interests"),
  });
  return response.data;
};

export const updateResearchInterests = async (request: {
  interests: string[];
}): Promise<ApiResponse<{ interests: string[] }>> => {
  const response = await api.post("/api/research-interests", request, {
    signal: getAbortSignal("POST /api/research-interests"),
  });
  return response.data;
};

export const initializeComponents = async (request: {
  profile_name: string;
}): Promise<ApiResponse<{ initialized: boolean }>> => {
  const response = await api.post("/api/initialize-components", request, {
    signal: getAbortSignal("POST /api/initialize-components"),
  });
  return response.data;
};

export const runRecommendation = async (request: {
  profile_name: string;
  debug_mode: boolean;
  target_date?: string;
}): Promise<ApiResponse<RecommendationResult>> => {
  const payload: Record<string, unknown> = {
    profile_name: request.profile_name,
    debug_mode: request.debug_mode,
  };
  if (request.target_date) {
    payload.target_date = request.target_date;
  }
  try {
    const response = await api.post("/api/run-recommendation", payload, {
      timeout: 300000,
      signal: getAbortSignal("POST /api/run-recommendation"),
    });
    return response.data;
  } catch (e) {
    const tmpl = normalizeTemplateError(e);
    if (tmpl) {
      return {
        success: false,
        error: tmpl.friendly_message || "模板错误导致请求失败",
        message: tmpl.friendly_message,
        template_error: tmpl,
      } as ApiResponse<RecommendationResult>;
    }
    throw e;
  }
};

export const getRecentReports = async (): Promise<ApiResponse<ReportItem[]>> => {
  const response = await api.get("/api/recent-reports", {
    signal: getAbortSignal("GET /api/recent-reports"),
  });
  return response.data;
};

// 获取分类数据
export const getCategories = async (): Promise<ApiResponse<Category[]>> => {
  const response = await api.get("/api/categories", {
    signal: getAbortSignal("GET /api/categories"),
  });
  return response.data;
};

// 预览报告内容（返回文本/HTML）
export const previewReport = async (params: {
  name: string;
  format: "md" | "html";
}): Promise<ApiResponse<{ content: string }>> => {
  const response = await api.get("/api/reports/preview", {
    params: { name: params.name, format: params.format },
    signal: getAbortSignal("GET /api/reports/preview"),
  });
  return response.data;
};

// 获取报告下载链接（也可直接使用 axios 下载 blob）
export const getReportDownloadUrl = (params: { name: string; format: "md" | "html" }): string => {
  const fmt = params.format || "md";
  const url = new URL("/api/reports/download", BASE_URL);
  url.searchParams.set("name", params.name);
  url.searchParams.set("format", fmt);
  return url.toString();
};

// 删除报告文件
export const deleteReportFile = async (params: {
  name: string;
  format: "md" | "html";
}): Promise<ApiResponse<{ deleted: boolean }>> => {
  const response = await api.delete("/api/reports/file", {
    params: { name: params.name, format: params.format },
    signal: getAbortSignal("DELETE /api/reports/file"),
  });
  return response.data;
};

// =====================
// 环境配置相关 API
// =====================

export const getEnvConfig = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get("/api/env-config", {
    signal: getAbortSignal("GET /api/env-config"),
  });
  return response.data;
};

export const saveEnvConfig = async (request: {
  config: Record<string, unknown>;
}): Promise<ApiResponse<{ saved: boolean }>> => {
  const response = await api.post("/api/env-config/save", request, {
    signal: getAbortSignal("POST /api/env-config/save"),
  });
  return response.data;
};

export const reloadEnvConfig = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.post("/api/env-config/reload", undefined, {
    signal: getAbortSignal("POST /api/env-config/reload"),
  });
  return response.data;
};

export const restoreDefaultEnvConfig = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.post("/api/env-config/restore-default", undefined, {
    signal: getAbortSignal("POST /api/env-config/restore-default"),
  });
  return response.data;
};

// =====================
// 提示词管理相关 API
// =====================

// 列出所有提示词
export const listPrompts = async (): Promise<ApiResponse<PromptItem[]>> => {
  const response = await api.get("/api/prompts", {
    signal: getAbortSignal("GET /api/prompts"),
  });
  return response.data;
};

// 获取单个提示词
export const getPrompt = async (prompt_id: string): Promise<ApiResponse<PromptItem>> => {
  const response = await api.get(`/api/prompts/${encodeURIComponent(prompt_id)}`, {
    signal: getAbortSignal(`GET /api/prompts/${prompt_id}`),
  });
  return response.data;
};

// 更新提示词（允许更新 name/template）
export const updatePrompt = async (
  prompt_id: string,
  updates: Partial<Pick<PromptItem, "name" | "template">>
): Promise<ApiResponse<PromptItem>> => {
  try {
    const response = await api.put(`/api/prompts/${encodeURIComponent(prompt_id)}`, updates, {
      signal: getAbortSignal(`PUT /api/prompts/${prompt_id}`),
    });
    return response.data;
  } catch (e) {
    const tmpl = normalizeTemplateError(e);
    if (tmpl) {
      return {
        success: false,
        error: tmpl.friendly_message || "模板错误导致保存失败",
        message: tmpl.friendly_message,
        template_error: tmpl,
      } as ApiResponse<PromptItem>;
    }
    throw e;
  }
};

// 重置单个提示词
export const resetPrompt = async (prompt_id: string): Promise<ApiResponse<PromptItem>> => {
  const response = await api.post(
    `/api/prompts/${encodeURIComponent(prompt_id)}/reset`,
    undefined,
    {
      signal: getAbortSignal(`POST /api/prompts/${prompt_id}/reset`),
    }
  );
  return response.data;
};

// 重置所有提示词
export const resetAllPrompts = async (): Promise<ApiResponse<null>> => {
  const response = await api.post("/api/prompts/reset", undefined, {
    signal: getAbortSignal("POST /api/prompts/reset"),
  });
  return response.data;
};

// =====================
// 分类匹配器相关 API
// =====================

// 获取匹配器提供商配置
export const getMatcherProviderConfig = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get("/api/matcher/provider", {
    signal: getAbortSignal("GET /api/matcher/provider"),
  });
  return response.data;
};

// 获取用户匹配数据与统计（返回形如 { success, data: UserProfile[], stats }）
export const getMatcherData = async (): Promise<
  ApiResponse<UserProfile[]> & { stats?: Record<string, unknown> }
> => {
  const response = await api.get("/api/matcher/data", {
    signal: getAbortSignal("GET /api/matcher/data"),
  });
  return response.data;
};

// 优化研究描述
export const optimizeMatcherDescription = async (request: {
  user_input: string;
}): Promise<ApiResponse<{ optimized: string }>> => {
  try {
    const response = await api.post("/api/matcher/optimize", request, {
      signal: getAbortSignal("POST /api/matcher/optimize"),
    });
    return response.data;
  } catch (e) {
    const tmpl = normalizeTemplateError(e);
    if (tmpl) {
      return {
        success: false,
        error: tmpl.friendly_message || "模板错误导致优化失败",
        message: tmpl.friendly_message,
        template_error: tmpl,
      } as ApiResponse<{ optimized: string }>;
    }
    throw e;
  }
};

// 执行分类匹配
export const runCategoryMatching = async (request: {
  user_input: string;
  username: string;
  top_n: number;
}): Promise<
  ApiResponse<{
    results: { id: string; name: string; score: number }[];
    token_usage: { input_tokens: number; output_tokens: number; total_tokens: number };
  }>
> => {
  try {
    const response = await api.post("/api/matcher/run", request, {
      timeout: 300000,
      signal: getAbortSignal("POST /api/matcher/run"),
    });
    return response.data;
  } catch (e) {
    const tmpl = normalizeTemplateError(e);
    if (tmpl) {
      return {
        success: false,
        error: tmpl.friendly_message || "模板错误导致分类匹配失败",
        message: tmpl.friendly_message,
        template_error: tmpl,
      } as ApiResponse<{
        results: { id: string; name: string; score: number }[];
        token_usage: { input_tokens: number; output_tokens: number; total_tokens: number };
      }>;
    }
    throw e;
  }
};

// 更新单条匹配记录
export const updateMatcherRecord = async (request: {
  index: number;
  username: string;
  category_id: string;
  user_input: string;
}): Promise<ApiResponse<{ updated: boolean }>> => {
  const response = await api.put("/api/matcher/record", request, {
    signal: getAbortSignal("PUT /api/matcher/record"),
  });
  return response.data;
};

// 删除单条匹配记录
export const deleteMatcherRecord = async (params: {
  index: number;
}): Promise<ApiResponse<{ deleted: boolean }>> => {
  const response = await api.delete("/api/matcher/record", {
    params: { index: params.index },
    signal: getAbortSignal("DELETE /api/matcher/record"),
  });
  return response.data;
};

// 批量删除匹配记录
export const batchDeleteMatcherRecords = async (request: {
  indices: number[];
}): Promise<ApiResponse<{ deleted: number }>> => {
  const response = await api.delete("/api/matcher/records", {
    data: request,
    signal: getAbortSignal("DELETE /api/matcher/records"),
  });
  return response.data;
};

// 列出评分文件
export const listMatcherScoreFiles = async (): Promise<ApiResponse<string[]>> => {
  const response = await api.get("/api/matcher/scores", {
    signal: getAbortSignal("GET /api/matcher/scores"),
  });
  return response.data;
};

// 读取评分文件内容
export const readMatcherScoreFileContent = async (params: {
  name: string;
}): Promise<ApiResponse<{ name: string; content: string }>> => {
  const response = await api.get("/api/matcher/scores/content", {
    params,
    signal: getAbortSignal("GET /api/matcher/scores/content"),
  });
  return response.data;
};

// 删除评分文件（统一使用 /api/matcher/scores）
export const deleteMatcherScoreFile = async (params: {
  name: string;
}): Promise<ApiResponse<{ deleted: boolean }>> => {
  const response = await api.delete("/api/matcher/scores", {
    params,
    signal: getAbortSignal("DELETE /api/matcher/scores"),
  });
  return response.data;
};

// 聚合：获取匹配数据（优先 /api/matcher/data，失败则回退 /api/user-profiles）
export const getMatcherDataOrProfiles = async (): Promise<
  ApiResponse<UserProfile[]> & { stats?: Record<string, unknown> }
> => {
  try {
    const res = await getMatcherData();
    if (res?.success) return res;
  } catch {}
  const fallback = await getUserProfiles();
  return { ...fallback, stats: undefined } as ApiResponse<UserProfile[]> & {
    stats?: Record<string, unknown>;
  };
};

export default api;
