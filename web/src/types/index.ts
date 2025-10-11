// 用户配置接口
export interface UserProfile {
  username: string
  user_input: string
  category_id: string
}

// 推荐结果接口
export interface RecommendationResult {
  success: boolean
  report?: string
  summary_content?: string
  detailed_analysis?: string
  brief_analysis?: string
  html_content?: string
  html_filepath?: string
  filename?: string
  target_date?: string
  debug_mode?: boolean
  error?: string
  warning?: string
  show_weekend_tip?: boolean
  traceback?: string
}

// API响应接口
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// 报告文件接口
export interface ReportFile {
  filename: string
  filepath: string
  date: string
  size: number
}

// 前端界面使用的报告项（最小字段集）
export interface ReportItem {
  name: string
  date: string
  size: number
}