import axios from 'axios'
import type { ApiResponse } from '@/types'

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
export const initializeService = async (): Promise<ApiResponse<any>> => {
  const response = await api.post('/api/initialize')
  return response.data
}

export const getConfig = async (): Promise<ApiResponse<any>> => {
  const response = await api.get('/api/config')
  return response.data
}

export const getUserProfiles = async (): Promise<ApiResponse<any>> => {
  const response = await api.get('/api/user-profiles')
  return response.data
}

export const getResearchInterests = async (): Promise<ApiResponse<string[]>> => {
  const response = await api.get('/api/research-interests')
  return response.data
}

export const updateResearchInterests = async (request: { interests: string[] }): Promise<ApiResponse<any>> => {
  const response = await api.post('/api/research-interests', request)
  return response.data
}

export const initializeComponents = async (request: { profile_name: string }): Promise<ApiResponse<any>> => {
  const response = await api.post('/api/initialize-components', request)
  return response.data
}

export const runRecommendation = async (request: { profile_name: string, debug_mode: boolean }): Promise<any> => {
  const response = await api.post('/api/run-recommendation', request)
  return response.data
}

export const getRecentReports = async (): Promise<ApiResponse<any[]>> => {
  const response = await api.get('/api/recent-reports')
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
export const deleteReportFile = async (params: { name: string, format: 'md' | 'html' }): Promise<ApiResponse<any>> => {
  const response = await api.delete('/api/reports/file', {
    params: { name: params.name, format: params.format }
  })
  return response.data
}

export default api