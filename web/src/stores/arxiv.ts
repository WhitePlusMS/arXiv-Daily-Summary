import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { UserProfile, RecommendationResult, FrontendConfig, ReportItem } from '@/types'

export const useArxivStore = defineStore('arxiv', () => {
  // 状态
  const config = ref<FrontendConfig | null>(null)
  const userProfiles = ref<UserProfile[]>([])
  const researchInterests = ref<string[]>([])
  const negativeInterests = ref<string[]>([])
  const selectedProfile = ref<UserProfile | null>(null)
  const selectedProfileName = ref<string>('自定义')
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastRecommendationResult = ref<RecommendationResult | null>(null)
  const recentReports = ref<ReportItem[]>([])

  // 计算属性
  const isDebugMode = computed(() => config.value?.debug_mode || false)
  // 轻模型提供方有效性（用于分类匹配页、优化等）
  const hasValidLightProviderConfig = computed(() => {
    const cfg = config.value
    if (!cfg) return false
    const provider = (cfg.light_model_provider || 'dashscope').toLowerCase()
    if (provider === 'ollama') return !!cfg.ollama_base_url
    return !!cfg.dashscope_api_key
  })
  // 重模型提供方有效性（用于摘要/推荐等重任务）
  const hasValidHeavyProviderConfig = computed(() => {
    const cfg = config.value
    if (!cfg) return false
    const provider = (cfg.heavy_model_provider || 'dashscope').toLowerCase()
    if (provider === 'ollama') return !!cfg.ollama_base_url
    return !!cfg.dashscope_api_key
  })
  // 保持向后兼容：原 hasValidConfig 等同于重模型配置有效性
  const hasValidConfig = hasValidHeavyProviderConfig
  const hasResearchInterests = computed(() => researchInterests.value.length > 0)

  // 方法
  function setConfig(newConfig: FrontendConfig) {
    config.value = newConfig
  }

  function setUserProfiles(profiles: UserProfile[]) {
    userProfiles.value = profiles
  }

  function setResearchInterests(interests: string[]) {
    researchInterests.value = interests
  }

  function setNegativeInterests(interests: string[]) {
    negativeInterests.value = interests
  }

  function setSelectedProfile(profileName: string) {
    selectedProfileName.value = profileName
    if (profileName === '自定义') {
      selectedProfile.value = null
    } else {
      selectedProfile.value = userProfiles.value.find(p => p.username === profileName) || null
      if (selectedProfile.value) {
        // 更新研究兴趣
        const interests = selectedProfile.value.user_input.split('\n').filter(line => line.trim())
        setResearchInterests(interests)
        
        // 更新负面偏好
        const negativeQuery = selectedProfile.value.negative_query || ''
        const negativeInterestsList = negativeQuery.split('\n').filter(line => line.trim())
        setNegativeInterests(negativeInterestsList)
        
        // 更新配置中的分类
        if (config.value) {
          config.value.arxiv_categories = selectedProfile.value.category_id.split(',')
        }
      }
    }
  }

  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  function setError(errorMsg: string | null) {
    error.value = errorMsg
  }

  function setLastRecommendationResult(result: RecommendationResult | null) {
    lastRecommendationResult.value = result
  }

  function setRecentReports(reports: ReportItem[]) {
    recentReports.value = reports
  }

  function clearError() {
    error.value = null
  }

  return {
    // 状态
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
    
    // 计算属性
    isDebugMode,
    hasValidLightProviderConfig,
    hasValidHeavyProviderConfig,
    hasValidConfig,
    hasResearchInterests,
    
    // 方法
    setConfig,
    setUserProfiles,
    setResearchInterests,
    setNegativeInterests,
    setSelectedProfile,
    setLoading,
    setError,
    setLastRecommendationResult,
    setRecentReports,
    clearError
  }
})
