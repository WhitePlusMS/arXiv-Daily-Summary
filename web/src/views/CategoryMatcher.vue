<template>
  <div class="streamlit-dashboard">
    <!-- 页面头部 -->
    <div class="streamlit-header">
      <h1 class="streamlit-title">📚 ArXiv 分类匹配器</h1>
      <div class="streamlit-divider"></div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="streamlit-error">
      {{ error }}
    </div>

    <!-- 配置与统计（参考Sidebar功能） -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">⚙️ 配置与统计</h2>
      <div v-if="hasValidConfig" class="streamlit-success">
        ✅ DashScope API 密钥已配置
      </div>
      <div v-else class="streamlit-error">
        ❌ DashScope API Key 未配置，请在后端 `.env` 中设置。
      </div>

      <div class="status-grid">
        <div class="status-item">
          <div class="status-label">返回结果数量</div>
          <input type="range" min="1" max="10" v-model.number="topN" />
          <div class="status-value">Top {{ topN }}</div>
        </div>

        <div v-if="stats" class="status-item">
          <div class="status-label">总记录数</div>
          <div class="status-value">{{ stats.total_records }}</div>
        </div>
        <div v-if="stats" class="status-item">
          <div class="status-label">用户数量</div>
          <div class="status-value">{{ stats.unique_users }}</div>
        </div>

        <button 
          class="streamlit-button"
          :disabled="isLoading"
          @click="refreshData"
        >
          🔄 刷新数据
        </button>
      </div>
      <div class="streamlit-divider"></div>
    </div>

    <!-- 研究信息输入 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">📝 输入研究信息</h2>
      <div class="streamlit-text-input">
        <label>用户名</label>
        <input 
          type="text" 
          v-model="username" 
          :disabled="isMatching" 
          class="streamlit-input"
          placeholder="请输入您的用户名"
        />
      </div>

      <div v-if="isMatching" class="streamlit-warning">
        ⚠️ 正在进行分类匹配，请等待完成后再修改输入内容
      </div>

      <div class="streamlit-text-area">
        <label>研究内容描述</label>
        <textarea
          v-model="researchDescription"
          :disabled="isMatching || isDescriptionLocked"
          class="streamlit-textarea"
          placeholder="请详细描述您的研究方向和兴趣领域…"
        ></textarea>
        <div class="streamlit-help">支持Markdown格式，请尽可能详细地描述您的研究方向</div>
      </div>

      <div class="action-row">
        <button 
          class="streamlit-button"
          :disabled="isMatching || !researchDescription.trim()"
          @click="optimizeDescription"
        >
          ✨ AI优化描述
        </button>
      </div>

      <div class="streamlit-divider"></div>
    </div>

    <!-- 匹配操作 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">🚀 开始匹配</h2>
      <button
        class="streamlit-button streamlit-button-primary"
        :disabled="isMatching"
        @click="startMatching"
      >
        {{ isMatching ? '正在匹配中…' : '开始匹配分类' }}
      </button>
      <div class="streamlit-help">将根据研究描述匹配最相关的ArXiv分类</div>
      <div class="streamlit-divider"></div>
    </div>

    <!-- 运行状态 -->
    <div v-if="isMatching" class="streamlit-section">
      <h2 class="streamlit-subheader">📋 运行状态</h2>
      <div class="streamlit-spinner">
        <div class="spinner"></div>
        <span>{{ runningMessage }}</span>
      </div>
    </div>

    <!-- 匹配完成提示 -->
    <div v-if="matchCompleted" class="streamlit-success">
      ✅ 匹配完成！结果已保存到数据库。<br />
      📊 全部115个分类的详细评分已保存到 data/users/detailed_scores/ 目录。
    </div>

    <!-- 匹配结果 -->
    <div v-if="results.length > 0" class="streamlit-section">
      <h2 class="streamlit-subheader">🎯 匹配结果</h2>
      <div class="results-table">
        <div class="table-header">
          <div>#</div>
          <div>分类ID</div>
          <div>分类名称</div>
          <div>匹配评分</div>
        </div>
        <div v-for="(r, idx) in results" :key="r.id" class="table-row">
          <div>{{ idx + 1 }}</div>
          <div><code>{{ r.id }}</code></div>
          <div>{{ r.name }}</div>
          <div>{{ r.score }}</div>
        </div>
      </div>
    </div>

    <!-- Token使用统计 -->
    <div v-if="tokenUsage.totalTokens > 0" class="streamlit-section">
      <h2 class="streamlit-subheader">💰 使用统计</h2>
      <div class="token-grid">
        <div class="token-item">
          <div class="token-value">{{ tokenUsage.inputTokens }}</div>
          <div class="token-label">输入Token</div>
        </div>
        <div class="token-item">
          <div class="token-value">{{ tokenUsage.outputTokens }}</div>
          <div class="token-label">输出Token</div>
        </div>
        <div class="token-item">
          <div class="token-value">{{ tokenUsage.totalTokens }}</div>
          <div class="token-label">总Token</div>
        </div>
      </div>
    </div>

    <!-- 用户数据管理 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">👥 用户数据管理</h2>
      <div class="streamlit-divider"></div>

      <div class="streamlit-text-input">
        <label>🔍 搜索用户或内容</label>
        <input 
          type="text" 
          v-model="searchTerm" 
          :disabled="isMatching"
          class="streamlit-input"
          placeholder="输入用户名或研究内容关键词…"
        />
      </div>

      <div class="action-row">
        <button class="streamlit-button" :disabled="isMatching" @click="selectAll">✅ 全选</button>
        <button class="streamlit-button" :disabled="isMatching" @click="clearSelection">❌ 取消全选</button>
        <button class="streamlit-button streamlit-button-danger" @click="batchDelete" :disabled="isMatching || selectedIndices.size === 0">🗑️ 批量删除</button>
        <button class="streamlit-button" :disabled="isMatching" @click="exportJSON">📥 导出JSON</button>
      </div>

      <div class="streamlit-help">提示：当前前端仅展示与管理数据，编辑与删除需后端API支持。</div>

      <div class="records-list" v-if="filteredProfiles.length > 0">
        <div class="records-header">
          <h3 class="streamlit-subheader">📄 用户记录</h3>
          <button class="streamlit-button streamlit-button-small" :disabled="isMatching" @click="toggleRecordsCollapse">
            {{ recordsCollapsed ? '展开' : '折叠' }}
          </button>
        </div>
        <div v-show="recordsCollapsed" class="records-collapsed-list">
          <div class="record-summary" v-for="(item, i) in filteredProfiles" :key="'summary-' + i">
            记录 {{ i + 1 }}: {{ item.username || 'Unknown' }}
          </div>
        </div>
        <div v-show="!recordsCollapsed">
        <div v-for="(item, i) in filteredProfiles" :key="i" class="record-item">
          <div class="record-header">
            <label>
              <input type="checkbox" :disabled="isMatching" :checked="selectedIndices.has(i)" @change="toggleSelection(i, $event)" />
              记录 {{ i + 1 }}: {{ item.username || 'Unknown' }}
            </label>
            <div class="record-actions">
              <button class="streamlit-button streamlit-button-small" :disabled="isMatching" @click="toggleEdit(i)">{{ editModes.has(i) ? '💾 保存' : '✏️ 编辑' }}</button>
              <button class="streamlit-button streamlit-button-small" :disabled="isMatching || !editModes.has(i)" @click="cancelEdit(i)">❌ 取消</button>
              <button class="streamlit-button streamlit-button-small streamlit-button-danger" :disabled="isMatching" @click="deleteRecord(i)">🗑️ 删除</button>
            </div>
          </div>
          <div class="record-body">
            <template v-if="editModes.has(i)">
              <div class="record-edit-grid">
                <div class="edit-field">
                  <label>用户名</label>
                  <input type="text" class="streamlit-input" v-model="editDrafts[i].username" />
                </div>
                <div class="edit-field">
                  <label>分类ID</label>
                  <input type="text" class="streamlit-input" v-model="editDrafts[i].category_id" />
                </div>
                <div class="edit-field">
                  <label>研究内容描述</label>
                  <textarea class="streamlit-textarea" v-model="editDrafts[i].user_input"></textarea>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="record-field"><strong>分类标签：</strong><code>{{ item.category_id || '未设置' }}</code></div>
              <div class="record-field"><strong>研究兴趣：</strong>
                <pre class="research-interests-code">{{ item.user_input || '未设置' }}</pre>
              </div>
            </template>
          </div>
        </div>
        </div>
      </div>
      <div v-else class="streamlit-info">📝 暂无数据记录，请先进行分类匹配或在后端添加用户配置。</div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useArxivStore } from '@/stores/counter'
import * as api from '@/services/api'
import type { UserProfile } from '@/types'

// Store
const store = useArxivStore()
const { isLoading, error, userProfiles, hasValidConfig } = storeToRefs(store)

// 本地状态
const username = ref('')
const researchDescription = ref('')
const topN = ref(5)
const isMatching = ref(false)
const isDescriptionLocked = ref(false)
const runningMessage = ref('')
const matchCompleted = ref(false)
const results = ref<{ id: string; name: string; score: number }[]>([])
const tokenUsage = ref({ inputTokens: 0, outputTokens: 0, totalTokens: 0 })
const stats = ref<{ total_records?: number; unique_users?: number } | null>(null)
const recordsCollapsed = ref(true)
const toggleRecordsCollapse = () => {
  recordsCollapsed.value = !recordsCollapsed.value
  try {
    localStorage.setItem('matcher_records_collapsed', recordsCollapsed.value ? '1' : '0')
  } catch {}
}

// 计算属性（从 store 引用 hasValidConfig，避免使用 any）

// 用户数据管理
const searchTerm = ref('')
const selectedIndices = ref<Set<number>>(new Set())
const editModes = ref<Set<number>>(new Set())
const editDrafts = ref<Record<number, { username: string; category_id: string; user_input: string }>>({})
const filteredProfiles = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  if (!term) return userProfiles.value
  return userProfiles.value.filter(item => 
    (item.username || '').toLowerCase().includes(term) ||
    (item.user_input || '').toLowerCase().includes(term) ||
    (item.category_id || '').toLowerCase().includes(term)
  )
})

// 方法
const refreshData = async () => {
  store.setLoading(true)
  store.clearError()
  try {
    const configResponse = await api.getConfig()
    if (configResponse.success && configResponse.data) {
      store.setConfig(configResponse.data)
    }
    const matcherData = await api.getMatcherData()
    const matcherList: UserProfile[] | undefined = matcherData.data as UserProfile[] | undefined
    if (matcherData.success && matcherList && matcherList.length > 0) {
      // 后端返回 { success, data: UserProfile[], stats }
      store.setUserProfiles(matcherList)
      // 保存统计信息
      if ('stats' in matcherData && matcherData.stats) {
        stats.value = matcherData.stats as any
      }
    } else {
      // 兜底：使用传统用户配置列表接口
      const profilesResponse = await api.getUserProfiles()
      if (profilesResponse.success && profilesResponse.data) {
        store.setUserProfiles(profilesResponse.data)
        stats.value = null
      }
    }
  } catch (err) {
    store.setError('刷新数据时发生错误')
    console.error('刷新数据错误:', err)
  } finally {
    store.setLoading(false)
  }
}

const optimizeDescription = async () => {
  if (!researchDescription.value.trim()) {
    store.setError('❌ 请先输入研究内容描述')
    return
  }
  try {
    store.clearError()
    const resp = await api.optimizeMatcherDescription({ user_input: researchDescription.value.trim() })
    if (resp.success && resp.data?.optimized) {
      researchDescription.value = resp.data.optimized
      // 优化后禁止再次编辑研究内容描述
      isDescriptionLocked.value = true
    } else {
      store.setError('优化描述失败')
    }
  } catch (err) {
    store.setError('优化描述时发生错误')
    console.error('优化错误:', err)
  }
}

const startMatching = async () => {
  if (!username.value.trim()) {
    store.setError('❌ 请输入用户名')
    return
  }
  if (!researchDescription.value.trim()) {
    store.setError('❌ 请输入研究内容描述')
    return
  }
  isMatching.value = true
  runningMessage.value = `🔄 正在处理匹配请求（Top ${topN.value}）...`
  try {
    store.clearError()
    const resp = await api.runCategoryMatching({
      user_input: researchDescription.value.trim(),
      username: username.value.trim(),
      top_n: topN.value
    })
    if (resp.success && resp.data) {
      results.value = resp.data.results.map((r) => ({ id: r.id, name: r.name, score: r.score }))
      const tu = resp.data.token_usage
      tokenUsage.value = {
        inputTokens: tu.input_tokens,
        outputTokens: tu.output_tokens,
        totalTokens: tu.total_tokens,
      }
      matchCompleted.value = true
      // 匹配成功后刷新数据列表
      await refreshData()
    } else {
      store.setError('分类匹配失败')
    }
  } catch (err) {
    store.setError('执行匹配时发生错误')
    console.error('匹配错误:', err)
  } finally {
    isMatching.value = false
    runningMessage.value = ''
  }
}

const selectAll = () => {
  selectedIndices.value = new Set(filteredProfiles.value.map((_, i) => i))
}
const clearSelection = () => {
  selectedIndices.value.clear()
}
const toggleSelection = (i: number, ev: Event) => {
  const checked = (ev.target as HTMLInputElement).checked
  if (checked) selectedIndices.value.add(i)
  else selectedIndices.value.delete(i)
}
const batchDelete = () => {
  if (selectedIndices.value.size === 0) return
  // 将筛选列表索引映射回原始 userProfiles 索引
  const indices = Array.from(selectedIndices.value).map(i => userProfiles.value.indexOf(filteredProfiles.value[i]))
  const valid = indices.filter(i => i >= 0)
  if (valid.length === 0) return
  store.setLoading(true)
  api.batchDeleteMatcherRecords({ indices: valid })
    .then(async (resp) => {
      if (resp.success) {
        selectedIndices.value.clear()
        await refreshData()
      } else {
        store.setError('批量删除失败')
      }
    })
    .catch(err => {
      store.setError('批量删除时发生错误')
      console.error('批量删除错误:', err)
    })
    .finally(() => {
      store.setLoading(false)
    })
}
const exportJSON = () => {
  const exportData = filteredProfiles.value
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `user_categories_${new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')}.json`
  a.click()
  URL.revokeObjectURL(url)
}
const toggleEdit = (i: number) => {
  const item = filteredProfiles.value[i]
  if (!item) return
  if (editModes.value.has(i)) {
    // 保存
    const originalIndex = userProfiles.value.indexOf(item)
    if (originalIndex < 0) return
    const draft = editDrafts.value[i]
    store.setLoading(true)
    api.updateMatcherRecord({ index: originalIndex, username: draft.username || '', category_id: draft.category_id || '', user_input: draft.user_input || '' })
      .then(async (resp) => {
        if (resp.success) {
          editModes.value.delete(i)
          delete editDrafts.value[i]
          await refreshData()
        } else {
          store.setError('更新记录失败')
        }
      })
      .catch(err => {
        store.setError('更新记录时发生错误')
        console.error('更新记录错误:', err)
      })
      .finally(() => {
        store.setLoading(false)
      })
  } else {
    // 进入编辑模式
    editModes.value.add(i)
    editDrafts.value[i] = {
      username: item.username || '',
      category_id: item.category_id || '',
      user_input: item.user_input || '',
    }
  }
}
const cancelEdit = (i: number) => {
  editModes.value.delete(i)
  delete editDrafts.value[i]
}
const deleteRecord = (i: number) => {
  const item = filteredProfiles.value[i]
  if (!item) return
  const originalIndex = userProfiles.value.indexOf(item)
  if (originalIndex < 0) return
  if (!confirm('确认删除该记录？此操作不可撤销。')) return
  store.setLoading(true)
  api.deleteMatcherRecord({ index: originalIndex })
    .then(async (resp) => {
      if (resp.success) {
        await refreshData()
      } else {
        store.setError('删除记录失败')
      }
    })
    .catch(err => {
      store.setError('删除记录时发生错误')
      console.error('删除记录错误:', err)
    })
    .finally(() => {
      store.setLoading(false)
    })
}


onMounted(async () => {
  // 读取折叠状态持久化
  try {
    const saved = localStorage.getItem('matcher_records_collapsed')
    if (saved === '1') recordsCollapsed.value = true
    else if (saved === '0') recordsCollapsed.value = false
  } catch {}

  // 初始化服务与数据
  try {
    await api.initializeService()
  } catch {}
  await refreshData()
})
</script>

<style scoped>
.action-row { display: flex; gap: 0.5rem; align-items: center; }
.spinner { width: 16px; height: 16px; border-radius: 50%; border: 2px solid #c7d2fe; border-top-color: #4f46e5; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.status-grid { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; }
.status-item { display: flex; flex-direction: column; gap: 0.25rem; }
.status-label { color: #374151; font-size: 0.9rem; }
.status-value { color: #111827; font-weight: 600; }

.results-table { border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.table-header, .table-row { display: grid; grid-template-columns: 60px 180px 1fr 120px; gap: 0.5rem; padding: 0.5rem; }
.table-header { background: #f3f4f6; font-weight: 600; }
.table-row:nth-child(odd) { background: #fafafa; }

.token-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
.token-item { background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 8px; padding: 0.5rem; text-align: center; }
.token-value { font-size: 1.2rem; font-weight: 700; color: #1f2937; }
.token-label { font-size: 0.85rem; color: #6b7280; }

.records-list { margin-top: 0.5rem; }
.record-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.5rem; margin-bottom: 0.5rem; }
.record-header { display: flex; justify-content: space-between; align-items: center; }
.record-actions { display: flex; gap: 0.5rem; }
.record-body { margin-top: 0.5rem; }
.research-interests-code { background: #f1f3f4; padding: 0.25rem 0.5rem; border-radius: 6px; white-space: pre-wrap; }
.footer-content { color: #6b7280; font-size: 0.9rem; text-align: center; }
.record-edit-grid { display: grid; grid-template-columns: 1fr; gap: 0.5rem; }
.edit-field label { display: block; margin-bottom: 4px; color: #374151; }
.records-header { display: flex; justify-content: space-between; align-items: center; }
.records-collapsed-list { border: 1px dashed #e5e7eb; border-radius: 8px; padding: 0.5rem; background: #fafafa; }
.record-summary { padding: 0.25rem 0; color: #374151; }
</style>