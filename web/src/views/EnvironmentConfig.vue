<template>
  <div class="streamlit-dashboard">
    <!-- 页头 -->
    <div class="streamlit-header">
      <h1 class="streamlit-title">⚙️ ArXiv推荐系统 - 环境配置</h1>
      <div class="streamlit-divider"></div>
    </div>

    <!-- 未保存更改提示 -->
    <div class="streamlit-section">
      <div v-if="changedKeys.length > 0" class="streamlit-warning">
        ⚠️ 有 {{ changedKeys.length }} 项配置未保存到文件
        <div class="streamlit-expander">
          <div class="streamlit-expander-header" @click="toggleChanges">
            <span class="expander-icon">{{ showChanges ? '▼' : '▶' }}</span>
            📋 查看更改详情
          </div>
          <div v-if="showChanges" class="streamlit-expander-content">
            <ul class="changes-list">
              <li v-for="k in changedKeys" :key="k">
                <strong>{{ k }}</strong>：文件=`{{ truncate(loadedConfig[k]) }}` → 界面=`{{ truncate(configChanges[k]) }}`
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div v-else class="streamlit-success">
        ✅ 所有配置已同步，无未保存更改
      </div>
      <div class="streamlit-divider"></div>
    </div>

    <!-- 侧边栏导航 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">📑 配置分组</h2>
      <div class="streamlit-selectbox">
        <label>选择配置分组：</label>
        <select v-model="selectedSection" class="streamlit-select" :disabled="isLoading">
          <option v-for="s in sections" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <div class="streamlit-divider"></div>
    </div>

    <!-- 配置表单区域 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">{{ selectedSection }}</h2>

      <!-- 🔑 API配置 -->
      <div v-if="selectedSection === '🔑 API配置'" class="form-grid">
        <div class="form-item">
          <label>DASHSCOPE_API_KEY</label>
          <div class="password-field">
            <input :type="showDashscopeKey ? 'text' : 'password'" v-model="configChanges.DASHSCOPE_API_KEY" class="streamlit-input" autocomplete="new-password" />
            <button type="button" class="toggle-visibility" @click="showDashscopeKey = !showDashscopeKey">{{ showDashscopeKey ? '隐藏' : '显示' }}</button>
          </div>
        </div>
        <div class="form-item">
          <label>DASHSCOPE_BASE_URL</label>
          <input type="text" v-model="configChanges.DASHSCOPE_BASE_URL" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>QWEN_MODEL</label>
          <input type="text" v-model="configChanges.QWEN_MODEL" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>QWEN_MODEL_LIGHT</label>
          <input type="text" v-model="configChanges.QWEN_MODEL_LIGHT" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>OLLAMA_BASE_URL</label>
          <input type="text" v-model="configChanges.OLLAMA_BASE_URL" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>OLLAMA_MODEL_LIGHT</label>
          <input type="text" v-model="configChanges.OLLAMA_MODEL_LIGHT" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>LIGHT_MODEL_PROVIDER</label>
          <select v-model="configChanges.LIGHT_MODEL_PROVIDER" class="streamlit-select">
            <option value="qwen">qwen</option>
            <option value="ollama">ollama</option>
          </select>
        </div>
        <div class="form-item">
          <label>OLLAMA_MODEL_LIGHT_TEMPERATURE</label>
          <input type="number" step="0.1" v-model="configChanges.OLLAMA_MODEL_LIGHT_TEMPERATURE" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>OLLAMA_MODEL_LIGHT_TOP_P</label>
          <input type="number" step="0.1" v-model="configChanges.OLLAMA_MODEL_LIGHT_TOP_P" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>OLLAMA_MODEL_LIGHT_MAX_TOKENS</label>
          <input type="number" v-model="configChanges.OLLAMA_MODEL_LIGHT_MAX_TOKENS" class="streamlit-input" />
        </div>
      </div>

      <!-- 📚 ArXiv配置 -->
      <div v-if="selectedSection === '📚 ArXiv配置'" class="form-grid">
        <div class="form-item">
          <label>ARXIV_BASE_URL</label>
          <input type="text" v-model="configChanges.ARXIV_BASE_URL" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>ARXIV_RETRIES</label>
          <input type="number" v-model="configChanges.ARXIV_RETRIES" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>ARXIV_DELAY</label>
          <input type="number" v-model="configChanges.ARXIV_DELAY" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>ARXIV_CATEGORIES</label>
          <input type="text" v-model="configChanges.ARXIV_CATEGORIES" placeholder="cs.CL, cs.IR, cs.LG" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>MAX_ENTRIES</label>
          <input type="number" v-model="configChanges.MAX_ENTRIES" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>NUM_DETAILED_PAPERS</label>
          <input type="number" v-model="configChanges.NUM_DETAILED_PAPERS" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>NUM_BRIEF_PAPERS</label>
          <input type="number" v-model="configChanges.NUM_BRIEF_PAPERS" class="streamlit-input" />
        </div>
      </div>

      <!-- 🤖 LLM配置 -->
      <div v-if="selectedSection === '🤖 LLM配置'" class="form-grid">
        <div class="form-item">
          <label>MAX_WORKERS</label>
          <input type="number" v-model="configChanges.MAX_WORKERS" class="streamlit-input" />
        </div>
      </div>

      <!-- 📁 文件路径配置 -->
      <div v-if="selectedSection === '📁 文件路径配置'" class="form-grid">
        <div class="form-item">
          <label>USER_CATEGORIES_FILE</label>
          <input type="text" v-model="configChanges.USER_CATEGORIES_FILE" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>SAVE_DIRECTORY</label>
          <input type="text" v-model="configChanges.SAVE_DIRECTORY" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>SAVE_MARKDOWN</label>
          <select v-model="configChanges.SAVE_MARKDOWN" class="streamlit-select">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
      </div>

      <!-- 📧 邮件配置 -->
      <div v-if="selectedSection === '📧 邮件配置'" class="form-grid">
        <div class="form-item">
          <label>SEND_EMAIL</label>
          <select v-model="configChanges.SEND_EMAIL" class="streamlit-select">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
        <div class="form-item">
          <label>SENDER_EMAIL</label>
          <input type="email" v-model="configChanges.SENDER_EMAIL" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>RECEIVER_EMAIL</label>
          <input type="email" v-model="configChanges.RECEIVER_EMAIL" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>EMAIL_PASSWORD</label>
          <div class="password-field">
            <input :type="showEmailPassword ? 'text' : 'password'" v-model="configChanges.EMAIL_PASSWORD" class="streamlit-input" autocomplete="new-password" />
            <button type="button" class="toggle-visibility" @click="showEmailPassword = !showEmailPassword">{{ showEmailPassword ? '隐藏' : '显示' }}</button>
          </div>
        </div>
        <div class="form-item">
          <label>SMTP_SERVER</label>
          <input type="text" v-model="configChanges.SMTP_SERVER" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>SMTP_PORT</label>
          <input type="number" v-model="configChanges.SMTP_PORT" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>USE_SSL</label>
          <select v-model="configChanges.USE_SSL" class="streamlit-select">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
        <div class="form-item">
          <label>USE_TLS</label>
          <select v-model="configChanges.USE_TLS" class="streamlit-select">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
        <div class="form-item">
          <label>SUBJECT_PREFIX</label>
          <input type="text" v-model="configChanges.SUBJECT_PREFIX" class="streamlit-input" />
        </div>
      </div>

      <!-- 🕐 时区格式配置 -->
      <div v-if="selectedSection === '🕐 时区格式配置'" class="form-grid">
        <div class="form-item">
          <label>TIMEZONE</label>
          <input type="text" v-model="configChanges.TIMEZONE" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>DATE_FORMAT</label>
          <input type="text" v-model="configChanges.DATE_FORMAT" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>TIME_FORMAT</label>
          <input type="text" v-model="configChanges.TIME_FORMAT" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>ENABLE_MCP_TIME_SERVICE</label>
          <select v-model="configChanges.ENABLE_MCP_TIME_SERVICE" class="streamlit-select">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
        <div class="form-item">
          <label>DEBUG_MODE</label>
          <select v-model="configChanges.DEBUG_MODE" class="streamlit-select">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
      </div>

      <!-- 📝 日志配置 -->
      <div v-if="selectedSection === '📝 日志配置'" class="form-grid">
        <div class="form-item">
          <label>LOG_LEVEL</label>
          <input type="text" v-model="configChanges.LOG_LEVEL" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>LOG_FILE</label>
          <input type="text" v-model="configChanges.LOG_FILE" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>LOG_TO_CONSOLE</label>
          <select v-model="configChanges.LOG_TO_CONSOLE" class="streamlit-select">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
        <div class="form-item">
          <label>LOG_MAX_SIZE</label>
          <input type="number" v-model="configChanges.LOG_MAX_SIZE" class="streamlit-input" />
        </div>
        <div class="form-item">
          <label>LOG_BACKUP_COUNT</label>
          <input type="number" v-model="configChanges.LOG_BACKUP_COUNT" class="streamlit-input" />
        </div>
      </div>

      <div class="streamlit-divider"></div>
    </div>

    <!-- 底部操作按钮 -->
    <div class="streamlit-section">
      <div class="button-row">
        <button @click="saveConfig" :disabled="isLoading" class="streamlit-button streamlit-button-primary">💾 保存配置</button>
        <button @click="reloadConfig" :disabled="isLoading" class="streamlit-button">🔄 重新加载</button>
        <button @click="restoreDefault" :disabled="isLoading" class="streamlit-button">📋 恢复默认</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useArxivStore } from '@/stores/counter'
import * as api from '@/services/api'

const store = useArxivStore()

// 分组列表
const sections = [
  '🔑 API配置',
  '📚 ArXiv配置',
  '🤖 LLM配置',
  '📁 文件路径配置',
  '📧 邮件配置',
  '🕐 时区格式配置',
  '📝 日志配置'
]

const selectedSection = ref(sections[0])
const isLoading = ref(false)
const loadedConfig = ref<Record<string, any>>({})
const configChanges = ref<Record<string, any>>({})
const showChanges = ref(false)
// 密钥显隐切换（默认隐藏）
const showDashscopeKey = ref(false)
const showEmailPassword = ref(false)

// 计算未保存更改
const changedKeys = computed(() => {
  const keys = new Set<string>([...Object.keys(loadedConfig.value), ...Object.keys(configChanges.value)])
  const changed: string[] = []
  keys.forEach(k => {
    const fileVal = String(loadedConfig.value?.[k] ?? '').trim()
    const uiVal = String(configChanges.value?.[k] ?? '').trim()
    if (fileVal !== uiVal) changed.push(k)
  })
  return changed
})

const truncate = (val: any) => {
  const s = String(val ?? '')
  return s.length > 30 ? s.slice(0, 30) + '...' : s
}

const toggleChanges = () => {
  showChanges.value = !showChanges.value
}

const normalizeConfig = (cfg: Record<string, any>) => {
  // 将布尔/数值保持字符串形式以与 .env 一致
  const out: Record<string, any> = {}
  Object.entries(cfg || {}).forEach(([k, v]) => {
    if (v === true) out[k] = 'true'
    else if (v === false) out[k] = 'false'
    else out[k] = v
  })
  return out
}

const loadConfig = async () => {
  isLoading.value = true
  store.clearError()
  try {
    // 优先使用专用环境配置接口
    const res = await api.getEnvConfig()
    const cfg = res?.data || {}
    loadedConfig.value = normalizeConfig(cfg)
    configChanges.value = { ...loadedConfig.value }
  } catch (err) {
    // 兜底：使用通用配置接口
    try {
      const res2 = await api.getConfig()
      const cfg2 = res2?.data || {}
      loadedConfig.value = normalizeConfig(cfg2)
      configChanges.value = { ...loadedConfig.value }
    } catch (err2) {
      store.setError('加载配置失败')
      console.error('加载配置失败:', err2)
    }
  } finally {
    isLoading.value = false
  }
}

const saveConfig = async () => {
  isLoading.value = true
  store.clearError()
  try {
    const res = await api.saveEnvConfig({ config: configChanges.value })
    if (res.success) {
      await loadConfig()
    } else {
      store.setError(res.message || '保存配置失败')
    }
  } catch (err) {
    store.setError('保存配置时发生错误')
    console.error('保存配置错误:', err)
  } finally {
    isLoading.value = false
  }
}

const reloadConfig = async () => {
  isLoading.value = true
  store.clearError()
  try {
    const res = await api.reloadEnvConfig()
    if (res.success && res.data) {
      loadedConfig.value = normalizeConfig(res.data)
      configChanges.value = { ...loadedConfig.value }
    } else {
      store.setError(res.message || '重新加载失败')
    }
  } catch (err) {
    store.setError('重新加载时发生错误')
    console.error('重新加载错误:', err)
  } finally {
    isLoading.value = false
  }
}

const restoreDefault = async () => {
  isLoading.value = true
  store.clearError()
  try {
    const res = await api.restoreDefaultEnvConfig()
    if (res.success && res.data) {
      loadedConfig.value = normalizeConfig(res.data)
      configChanges.value = { ...loadedConfig.value }
    } else {
      store.setError(res.message || '恢复默认失败')
    }
  } catch (err) {
    store.setError('恢复默认时发生错误')
    console.error('恢复默认错误:', err)
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  await loadConfig()
})
</script>

<style scoped>
.streamlit-dashboard { max-width: 1080px; margin: 0 auto; padding: 1rem 1.25rem; }
.streamlit-header { margin-bottom: 0.75rem; }
.streamlit-title { font-size: 1.5rem; margin: 0; }
.streamlit-divider { height: 1px; background-color: #e9ecef; margin: 0.75rem 0; }
.streamlit-section { margin-bottom: 1rem; }
.streamlit-subheader { font-size: 1.125rem; margin-bottom: 0.5rem; }
.streamlit-warning { background: #fff3cd; border: 1px solid #ffeeba; padding: 0.75rem; border-radius: 0.375rem; }
.streamlit-success { background: #d4edda; border: 1px solid #c3e6cb; padding: 0.75rem; border-radius: 0.375rem; }
.streamlit-selectbox label { display: block; margin-bottom: 0.25rem; font-weight: 600; }
.streamlit-select, .streamlit-input { width: 100%; padding: 0.5rem; border: 1px solid #ced4da; border-radius: 0.375rem; }
.streamlit-expander { margin-top: 0.5rem; }
.streamlit-expander-header { cursor: pointer; padding: 0.5rem; border: 1px solid #dee2e6; border-radius: 0.375rem; background: #f8f9fa; }
.streamlit-expander-content { padding: 0.5rem; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 0.375rem 0.375rem; }
.expander-icon { margin-right: 0.5rem; }
.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; }
.form-item label { display: block; margin-bottom: 0.25rem; font-weight: 600; }
.button-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
.streamlit-button { padding: 0.5rem 0.75rem; border: 1px solid #dee2e6; background: #f8f9fa; border-radius: 0.375rem; cursor: pointer; }
.streamlit-button-primary { background: #0d6efd; color: white; border-color: #0d6efd; }
.changes-list { padding-left: 1rem; }
/* 密码输入显隐图标样式（内嵌到输入框内） */
.password-field { position: relative; }
.password-field .streamlit-input { padding-right: 2rem; }
.toggle-visibility { position: absolute; right: 0.5rem; top: 50%; transform: translateY(-50%); background: transparent; border: none; cursor: pointer; font-size: 0.875rem; color: #6c757d; }
.toggle-visibility:focus { outline: none; }
</style>