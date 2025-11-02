import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { UserProfile, RecommendationResult, FrontendConfig, ReportItem } from '@/types'

export const useArxivStore = defineStore('arxiv', () => {
  // 状态
  const config = ref<FrontendConfig | null>(null)
  const userProfiles = ref<UserProfile[]>([])
  const researchInterests = ref<string[]>([])
  const selectedProfile = ref<UserProfile | null>(null)
  const selectedProfileName = ref<string>('自定义')
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastRecommendationResult = ref<RecommendationResult | null>(null)
  const recentReports = ref<ReportItem[]>([])

  // 计算属性
  const isDebugMode = computed(() => config.value?.debug_mode || false)
  const hasValidConfig = computed(() => config.value && config.value.dashscope_api_key)
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
    selectedProfile,
    selectedProfileName,
    isLoading,
    error,
    lastRecommendationResult,
    recentReports,
    
    // 计算属性
    isDebugMode,
    hasValidConfig,
    hasResearchInterests,
    
    // 方法
    setConfig,
    setUserProfiles,
    setResearchInterests,
    setSelectedProfile,
    setLoading,
    setError,
    setLastRecommendationResult,
    setRecentReports,
    clearError
  }
})
