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
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// 模板错误详情（后端 400 返回 detail）
export interface TemplateErrorDetail {
  error_type: string
  friendly_message?: string
  fix_suggestions?: string[]
  details?: Record<string, unknown>
}

// 前端运行态配置（小写+语义化），与后端 .env 大写映射区分
export interface FrontendConfig {
  // API / LLM
  dashscope_api_key?: string
  dashscope_base_url?: string
  qwen_model?: string
  // Provider mapping
  heavy_model_provider?: string
  light_model_provider?: string
  ollama_base_url?: string
  ollama_model_heavy?: string
  ollama_model_light?: string
  qwen_model_light?: string

  // ArXiv
  arxiv_base_url?: string
  arxiv_retries?: number
  arxiv_delay?: number
  arxiv_categories?: string[]
  max_entries?: number
  num_brief_papers?: number
  num_detailed_papers?: number
  num_recommendations?: number

  // 运行控制
  debug_mode?: boolean

  // 邮件
  email_to?: string
  email_from?: string
  email_password?: string

  // 时间与日志
  timezone?: string
  date_format?: string
  log_level?: string
}

// Toast 消息类型
export interface ToastMessage {
  id: number
  type: 'success' | 'error' | 'warning' | 'info'
  text: string
  createdAt: number
}

// 分类与子分类接口
export interface Subcategory {
  id: string
  name: string
  description?: string
  name_cn?: string
  description_cn?: string
}

export interface Category {
  main_category: string
  subcategories: Subcategory[]
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

// 提示词条目
export interface PromptItem {
  id: string
  name: string
  template: string
  variables?: string[]
}