import axios from 'axios'
import type { ApiResponse, UserProfile, RecommendationResult, ReportItem, Category } from '@/types'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  // 生成推荐可能较耗时（涉及抓取与LLM），提高超时时间
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 统一输出更友好的错误信息
    if (error?.code === 'ECONNABORTED' || String(error?.message).toLowerCase().includes('timeout')) {
      console.error('API请求错误: 请求超时，服务正在处理或网络较慢。')
    } else if (String(error?.message).includes('ERR_ABORTED') || error?.name === 'CanceledError') {
      console.error('API请求错误: 请求被取消（可能是页面刷新或HMR）。')
    } else {
      console.error('API请求错误:', error)
    }
    return Promise.reject(error)
  }
)

// API服务函数
export const initializeService = async (): Promise<ApiResponse<{ initialized: boolean }>> => {
  const response = await api.post('/api/initialize')
  return response.data
}

export const getConfig = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get('/api/config')
  return response.data
}

export const getUserProfiles = async (): Promise<ApiResponse<UserProfile[]>> => {
  const response = await api.get('/api/user-profiles')
  return response.data
}

export const getResearchInterests = async (): Promise<ApiResponse<string[]>> => {
  const response = await api.get('/api/research-interests')
  return response.data
}

export const updateResearchInterests = async (request: { interests: string[] }): Promise<ApiResponse<{ interests: string[] }>> => {
  const response = await api.post('/api/research-interests', request)
  return response.data
}

export const initializeComponents = async (request: { profile_name: string }): Promise<ApiResponse<{ initialized: boolean }>> => {
  const response = await api.post('/api/initialize-components', request)
  return response.data
}

export const runRecommendation = async (request: { profile_name: string, debug_mode: boolean }): Promise<ApiResponse<RecommendationResult>> => {
  const response = await api.post('/api/run-recommendation', request)
  return response.data
}

export const getRecentReports = async (): Promise<ApiResponse<ReportItem[]>> => {
  const response = await api.get('/api/recent-reports')
  return response.data
}

// 获取分类数据
export const getCategories = async (): Promise<ApiResponse<Category[]>> => {
  const response = await api.get('/api/categories')
  return response.data
}

// 预览报告内容（返回文本/HTML）
export const previewReport = async (params: { name: string, format: 'md' | 'html' }): Promise<ApiResponse<{ content: string }>> => {
  const response = await api.get('/api/reports/preview', {
    params: { name: params.name, format: params.format }
  })
  return response.data
}

// 获取报告下载链接（也可直接使用 axios 下载 blob）
export const getReportDownloadUrl = (params: { name: string, format: 'md' | 'html' }): string => {
  const fmt = params.format || 'md'
  const url = new URL('/api/reports/download', 'http://localhost:8000')
  url.searchParams.set('name', params.name)
  url.searchParams.set('format', fmt)
  return url.toString()
}

// 删除报告文件
export const deleteReportFile = async (params: { name: string, format: 'md' | 'html' }): Promise<ApiResponse<{ deleted: boolean }>> => {
  const response = await api.delete('/api/reports/file', {
    params: { name: params.name, format: params.format }
  })
  return response.data
}

// =====================
// 环境配置相关 API
// =====================

export const getEnvConfig = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get('/api/env-config')
  return response.data
}

export const saveEnvConfig = async (request: { config: Record<string, unknown> }): Promise<ApiResponse<{ saved: boolean }>> => {
  const response = await api.post('/api/env-config/save', request)
  return response.data
}

export const reloadEnvConfig = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.post('/api/env-config/reload')
  return response.data
}

export const restoreDefaultEnvConfig = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.post('/api/env-config/restore-default')
  return response.data
}

// =====================
// 分类匹配器相关 API
// =====================

// 获取匹配器提供商配置
export const getMatcherProviderConfig = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get('/api/matcher/provider')
  return response.data
}

// 获取用户匹配数据与统计（返回形如 { success, data: UserProfile[], stats }）
export const getMatcherData = async (): Promise<ApiResponse<UserProfile[]> & { stats?: Record<string, unknown> }> => {
  const response = await api.get('/api/matcher/data')
  return response.data
}

// 优化研究描述
export const optimizeMatcherDescription = async (request: { user_input: string }): Promise<ApiResponse<{ optimized: string }>> => {
  const response = await api.post('/api/matcher/optimize', request)
  return response.data
}

// 执行分类匹配
export const runCategoryMatching = async (request: { user_input: string, username: string, top_n: number }): Promise<ApiResponse<{ results: { id: string, name: string, score: number }[], token_usage: { input_tokens: number, output_tokens: number, total_tokens: number } }>> => {
  const response = await api.post('/api/matcher/run', request)
  return response.data
}

// 更新单条匹配记录
export const updateMatcherRecord = async (request: { index: number, username: string, category_id: string, user_input: string }): Promise<ApiResponse<{ updated: boolean }>> => {
  const response = await api.put('/api/matcher/record', request)
  return response.data
}

// 删除单条匹配记录
export const deleteMatcherRecord = async (params: { index: number }): Promise<ApiResponse<{ deleted: boolean }>> => {
  const response = await api.delete('/api/matcher/record', { params: { index: params.index } })
  return response.data
}

// 批量删除匹配记录
export const batchDeleteMatcherRecords = async (request: { indices: number[] }): Promise<ApiResponse<{ deleted: number }>> => {
  const response = await api.delete('/api/matcher/records', { data: request })
  return response.data
}

// 列出评分文件
export const listMatcherScoreFiles = async (): Promise<ApiResponse<string[]>> => {
  const response = await api.get('/api/matcher/scores')
  return response.data
}

// 读取评分文件内容
export const readMatcherScoreFileContent = async (params: { name: string }): Promise<ApiResponse<{ name: string, content: string }>> => {
  const response = await api.get('/api/matcher/scores/content', { params })
  return response.data
}

// 删除评分文件（统一使用 /api/matcher/scores）
export const deleteMatcherScoreFile = async (params: { name: string }): Promise<ApiResponse<{ deleted: boolean }>> => {
  const response = await api.delete('/api/matcher/scores', { params })
  return response.data
}

export default api