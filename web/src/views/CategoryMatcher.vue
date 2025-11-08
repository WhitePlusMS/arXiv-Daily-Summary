<template>
  <div class="streamlit-dashboard">
    <!-- 页面头部 -->
    <div class="streamlit-header">
      <h1 class="streamlit-title">🎯 分类匹配</h1>
      <p class="streamlit-caption">输入研究兴趣 → AI推荐最相关ArXiv分类</p>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="streamlit-error">{{ error }}</div>

    <!-- 步骤① 配置与输入 -->
    <div class="streamlit-section">
      <div class="streamlit-expander">
        <div class="streamlit-expander-header" @click="toggleConfigExpand">
          <span class="expander-icon">{{ configExpanded ? '▼' : '▶' }}</span>
          <span>模型配置与统计</span>
          <span v-if="!hasValidLightProviderConfig" class="streamlit-error" style="margin-left:auto;font-size:12px;">❌ 未就绪</span>
        </div>
        <div v-show="configExpanded" class="streamlit-expander-content">
          <div v-if="hasValidLightProviderConfig" class="streamlit-success">✅ {{ lightProviderLabel }} 已配置</div>
          <div v-else class="streamlit-error">❌ {{ providerStatusMessage }}</div>
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
          </div>
          <div class="button-row">
            <button class="streamlit-button" :disabled="isLoading" @click="refreshData">🔄 刷新数据</button>
          </div>
        </div>
      </div>

      <!-- 用户名 & 研究描述 -->
      <div class="form-grid" style="margin-top:12px;">
        <div class="form-item">
          <label>用户名</label>
          <input type="text" v-model="username" :disabled="isMatching" class="streamlit-input" placeholder="请输入您的用户名" />
        </div>
        <div class="form-item">
          <label>研究内容描述</label>
          <textarea v-model="researchDescription" :disabled="isMatching || isDescriptionLocked" class="streamlit-textarea" placeholder="请尽可能详细地描述您的研究方向与兴趣领域…"></textarea>
          <div class="streamlit-help">支持Markdown格式；描述越具体，匹配越精准。</div>
        </div>
      </div>

      <div class="button-row">
        <button class="streamlit-button" :disabled="isMatching || !researchDescription.trim()" @click="optimizeDescription">✨ AI优化描述</button>
        <button class="streamlit-button streamlit-button-primary" :disabled="isMatching" @click="startMatching">{{ isMatching ? "匹配中…" : "开始匹配" }}</button>
      </div>

      <!-- 运行状态 -->
      <div v-if="isMatching" class="streamlit-spinner" style="margin-top:12px;">
        <div class="spinner"></div><span>{{ runningMessage }}</span>
      </div>
      <div v-if="matchCompleted" class="streamlit-success" style="margin-top:12px;">
        ✅ 匹配完成！结果已保存至数据库，详细评分见 <code>data/users/detailed_scores/</code>
      </div>
    </div>

    <!-- 步骤② 结果展示 -->
    <div v-if="results.length" class="streamlit-section">
      <h2 class="streamlit-subheader">🎯 推荐分类</h2>
      <div class="results-cards">
        <div v-for="(r, idx) in results" :key="r.id" class="result-card">
          <div class="result-header">
            <div class="result-rank">#{{ idx + 1 }}</div>
            <div class="result-score" :class="scoreClass(r.score)">{{ r.score }}</div>
          </div>
          <div class="result-body">
            <div class="result-id"><code>{{ r.id }}</code></div>
            <div class="result-name">{{ r.name }}</div>
            <div class="result-desc">{{ r.reason || '暂无推荐理由' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 步骤③ 用户记录管理 -->
    <div class="streamlit-section">
      <div class="streamlit-expander">
        <div class="streamlit-expander-header" @click="toggleRecordsExpand">
          <span class="expander-icon">{{ recordsExpanded ? '▼' : '▶' }}</span>
          <span>用户记录管理</span>
          <span style="margin-left:auto;font-size:12px;color:var(--color-text-soft);">共 {{ filteredProfiles.length }} 条</span>
        </div>
        <div v-show="recordsExpanded" class="streamlit-expander-content">
          <div class="streamlit-text-input">
            <input type="text" v-model="searchTerm" :disabled="isMatching" class="streamlit-input" placeholder="搜索用户名或研究内容…" />
          </div>
          <div class="button-row">
            <button class="streamlit-button" :disabled="isMatching" @click="selectAll">全选</button>
            <button class="streamlit-button" :disabled="isMatching" @click="clearSelection">取消</button>
            <button class="streamlit-button streamlit-button-danger" :disabled="isMatching || !selectedIndices.size" @click="batchDelete">删除</button>
            <button class="streamlit-button" :disabled="isMatching" @click="exportJSON">导出</button>
          </div>
          <div class="streamlit-help">提示：编辑/删除需后端API支持。</div>
          <div v-if="!filteredProfiles.length" class="streamlit-info">暂无记录，请先完成一次匹配。</div>
          <div v-else class="records-cards">
            <div v-for="(item, i) in filteredProfiles" :key="i" class="record-card">
              <div class="record-header">
                <label><input type="checkbox" :disabled="isMatching" :checked="selectedIndices.has(i)" @change="toggleSelection(i, $event)" />{{ item.username || 'Unknown' }}</label>
                <div class="record-actions">
                  <button class="streamlit-button streamlit-button-small" :disabled="isMatching" @click="toggleEdit(i)">{{ editModes.has(i) ? '保存' : '编辑' }}</button>
                  <button class="streamlit-button streamlit-button-small" :disabled="isMatching || !editModes.has(i)" @click="cancelEdit(i)">取消</button>
                  <button class="streamlit-button streamlit-button-small streamlit-button-danger" :disabled="isMatching" @click="deleteRecord(i)">删除</button>
                </div>
              </div>
              <div class="record-body">
                <div class="record-category"><strong>推荐分类：</strong><code>{{ item.category_id || '未设置' }}</code></div>
                <div class="record-interests"><strong>研究兴趣：</strong><pre>{{ item.user_input || '未设置' }}</pre></div>
              </div>
              <div v-if="editModes.has(i)" class="record-edit-panel">
                <div class="form-item"><label>用户名</label><input type="text" class="streamlit-input" v-model="editDrafts[i].username" /></div>
                <div class="form-item"><label>分类ID</label><input type="text" class="streamlit-input" v-model="editDrafts[i].category_id" /></div>
                <div class="form-item"><label>研究内容描述</label><textarea class="streamlit-textarea" v-model="editDrafts[i].user_input"></textarea></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Token使用统计 -->
    <div v-if="tokenUsage.total_tokens > 0" class="streamlit-section">
      <div class="token-grid">
        <div class="token-item"><div class="token-value">{{ tokenUsage.input_tokens }}</div><div class="token-label">输入Token</div></div>
        <div class="token-item"><div class="token-value">{{ tokenUsage.output_tokens }}</div><div class="token-label">输出Token</div></div>
        <div class="token-item"><div class="token-value">{{ tokenUsage.total_tokens }}</div><div class="token-label">总Token</div></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";
import * as api from "@/services/api";
import type { UserProfile } from "@/types";

// Store
const store = useArxivStore();
const { isLoading, error, userProfiles, config, hasValidLightProviderConfig } = storeToRefs(store);

// 本地状态
const username = ref("");
const researchDescription = ref("");
const topN = ref(5);
const isMatching = ref(false);
const isDescriptionLocked = ref(false);
const runningMessage = ref("");
const matchCompleted = ref(false);
const results = ref<{ id: string; name: string; score: number }[]>([]);
const tokenUsage = ref({ input_tokens: 0, output_tokens: 0, total_tokens: 0 });
const stats = ref<{ total_records?: number; unique_users?: number } | null>(null);
const recordsCollapsed = ref(true);
const toggleRecordsCollapse = () => {
  recordsCollapsed.value = !recordsCollapsed.value;
  try {
    localStorage.setItem("matcher_records_collapsed", recordsCollapsed.value ? "1" : "0");
  } catch {}
};

// 计算属性：轻模型提供方名称与动态文案
const lightProvider = computed(() => (config.value?.light_model_provider || 'dashscope').toLowerCase());
const lightProviderLabel = computed(() => lightProvider.value === 'ollama' ? 'Ollama 基础地址' : 'DashScope API Key');
const providerStatusMessage = computed(() => {
  const p = lightProvider.value;
  if (p === 'ollama') return 'Ollama 未配置，请设置 OLLAMA_BASE_URL 并确保服务可用（或切换 轻模型提供方）。';
  return 'DashScope API Key 未配置，请在后端 .env 中设置（或切换 轻模型提供方）。';
});

// 用户数据管理
const searchTerm = ref("");
const selectedIndices = ref<Set<number>>(new Set());
const editModes = ref<Set<number>>(new Set());
const editDrafts = ref<
  Record<number, { username: string; category_id: string; user_input: string }>
>({});
const filteredProfiles = computed(() => {
  const term = searchTerm.value.trim().toLowerCase();
  if (!term) return userProfiles.value;
  return userProfiles.value.filter(
    (item) =>
      (item.username || "").toLowerCase().includes(term) ||
      (item.user_input || "").toLowerCase().includes(term) ||
      (item.category_id || "").toLowerCase().includes(term)
  );
});

// 方法
const refreshData = async () => {
  store.setLoading(true);
  store.clearError();
  try {
    const configResponse = await api.getConfig();
    if (configResponse.success && configResponse.data) {
      store.setConfig(configResponse.data);
    }
    const res = await api.getMatcherDataOrProfiles();
    if (res.success && res.data) {
      store.setUserProfiles(res.data as UserProfile[]);
      stats.value = (res as any).stats || null;
    } else {
      stats.value = null;
    }
  } catch (err) {
    store.setError("刷新数据时发生错误");
    console.error("刷新数据错误:", err);
  } finally {
    store.setLoading(false);
  }
};

const optimizeDescription = async () => {
  if (!researchDescription.value.trim()) {
    store.setError("❌ 请先输入研究内容描述");
    return;
  }
  try {
    store.clearError();
    const resp = await api.optimizeMatcherDescription({
      user_input: researchDescription.value.trim(),
    });
    if (resp.success && resp.data?.optimized) {
      researchDescription.value = resp.data.optimized;
      // 优化后禁止再次编辑研究内容描述
      isDescriptionLocked.value = true;
    } else {
      // 模板错误友好提示
      const tmpl = (resp as any).template_error as {
        friendly_message?: string;
        fix_suggestions?: string[];
        details?: Record<string, unknown>;
      } | undefined;
      if (tmpl?.friendly_message) {
        const tips = Array.isArray(tmpl.fix_suggestions) && tmpl.fix_suggestions.length
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
  }
};

const startMatching = async () => {
  if (!username.value.trim()) {
    store.setError("❌ 请输入用户名");
    return;
  }
  if (!researchDescription.value.trim()) {
    store.setError("❌ 请输入研究内容描述");
    return;
  }
  isMatching.value = true;
  runningMessage.value = `🔄 正在处理匹配请求（Top ${topN.value}）...`;
  try {
    store.clearError();
    const resp = await api.runCategoryMatching({
      user_input: researchDescription.value.trim(),
      username: username.value.trim(),
      top_n: topN.value,
    });
    if (resp.success && resp.data) {
      const resList = Array.isArray(resp.data.results) ? resp.data.results : [];
      results.value = resList.map((r) => ({ id: r.id, name: r.name, score: r.score }));
      const tuRaw = resp.data.token_usage || {};
      const input_tokens = (tuRaw as any).input_tokens ?? 0;
      const output_tokens = (tuRaw as any).output_tokens ?? 0;
      const total_tokens = (tuRaw as any).total_tokens ?? 0;
      tokenUsage.value = { input_tokens, output_tokens, total_tokens };
      matchCompleted.value = true;
      // 匹配成功后刷新数据列表
      await refreshData();
    } else {
      // 模板错误友好提示
      const tmpl = (resp as any).template_error as {
        friendly_message?: string;
        fix_suggestions?: string[];
        details?: Record<string, unknown>;
      } | undefined;
      if (tmpl?.friendly_message) {
        const tips = Array.isArray(tmpl.fix_suggestions) && tmpl.fix_suggestions.length
          ? `\n修复建议：\n• ${tmpl.fix_suggestions.join("\n• ")}`
          : "";
        store.setError(`${tmpl.friendly_message}${tips}`);
      } else {
        store.setError("分类匹配失败");
      }
    }
  } catch (err) {
    store.setError("执行匹配时发生错误");
    console.error("匹配错误:", err);
  } finally {
    isMatching.value = false;
    runningMessage.value = "";
  }
};

const selectAll = () => {
  selectedIndices.value = new Set(filteredProfiles.value.map((_, i) => i));
};
const clearSelection = () => {
  selectedIndices.value.clear();
};
const toggleSelection = (i: number, ev: Event) => {
  const checked = (ev.target as HTMLInputElement).checked;
  if (checked) selectedIndices.value.add(i);
  else selectedIndices.value.delete(i);
};
const batchDelete = () => {
  if (selectedIndices.value.size === 0) return;
  // 将筛选列表索引映射回原始 userProfiles 索引
  const indices = Array.from(selectedIndices.value).map((i) =>
    userProfiles.value.indexOf(filteredProfiles.value[i])
  );
  const valid = indices.filter((i) => i >= 0);
  if (valid.length === 0) return;
  store.setLoading(true);
  api
    .batchDeleteMatcherRecords({ indices: valid })
    .then(async (resp) => {
      if (resp.success) {
        selectedIndices.value.clear();
        await refreshData();
      } else {
        store.setError("批量删除失败");
      }
    })
    .catch((err) => {
      store.setError("批量删除时发生错误");
      console.error("批量删除错误:", err);
    })
    .finally(() => {
      store.setLoading(false);
    });
};
const exportJSON = () => {
  const exportData = filteredProfiles.value;
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `user_categories_${new Date()
    .toISOString()
    .slice(0, 19)
    .replace(/[:T]/g, "-")}.json`;
  a.click();
  URL.revokeObjectURL(url);
};
const toggleEdit = (i: number) => {
  const item = filteredProfiles.value[i];
  if (!item) return;
  if (editModes.value.has(i)) {
    // 保存
    const originalIndex = userProfiles.value.indexOf(item);
    if (originalIndex < 0) return;
    const draft = editDrafts.value[i];
    store.setLoading(true);
    api
      .updateMatcherRecord({
        index: originalIndex,
        username: draft.username || "",
        category_id: draft.category_id || "",
        user_input: draft.user_input || "",
      })
      .then(async (resp) => {
        if (resp.success) {
          editModes.value.delete(i);
          delete editDrafts.value[i];
          await refreshData();
        } else {
          store.setError("更新记录失败");
        }
      })
      .catch((err) => {
        store.setError("更新记录时发生错误");
        console.error("更新记录错误:", err);
      })
      .finally(() => {
        store.setLoading(false);
      });
  } else {
    // 进入编辑模式
    editModes.value.add(i);
    editDrafts.value[i] = {
      username: item.username || "",
      category_id: item.category_id || "",
      user_input: item.user_input || "",
    };
  }
};
const cancelEdit = (i: number) => {
  editModes.value.delete(i);
  delete editDrafts.value[i];
};
const deleteRecord = (i: number) => {
  const item = filteredProfiles.value[i];
  if (!item) return;
  const originalIndex = userProfiles.value.indexOf(item);
  if (originalIndex < 0) return;
  if (!confirm("确认删除该记录？此操作不可撤销。")) return;
  store.setLoading(true);
  api
    .deleteMatcherRecord({ index: originalIndex })
    .then(async (resp) => {
      if (resp.success) {
        await refreshData();
      } else {
        store.setError("删除记录失败");
      }
    })
    .catch((err) => {
      store.setError("删除记录时发生错误");
      console.error("删除记录错误:", err);
    })
    .finally(() => {
      store.setLoading(false);
    });
};

onMounted(async () => {
  // 读取折叠状态持久化
  try {
    const saved = localStorage.getItem("matcher_records_collapsed");
    if (saved === "1") recordsCollapsed.value = true;
    else if (saved === "0") recordsCollapsed.value = false;
  } catch {}

  // 初始化服务与数据
  try {
    await api.initializeService();
  } catch {}
  await refreshData();
});
</script>
