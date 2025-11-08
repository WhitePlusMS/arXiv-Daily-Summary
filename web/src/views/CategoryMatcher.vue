<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<template>
  <div class="streamlit-dashboard">
    <!-- 页面头部 -->
    <div class="streamlit-header">
      <h1 class="streamlit-title">📚 ArXiv 分类匹配器</h1>
      <div class="guide-card" style="margin-top: 8px">
        <div class="sub-desc">
          步骤：1）填写用户名与研究描述 → 2）可选AI优化 → 3）开始匹配 → 4）查看结果与使用统计 →
          5）管理与导出历史记录
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="streamlit-error">
      {{ error }}
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
    </div>

    <!-- 匹配操作 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">🚀 开始匹配</h2>
      <div class="streamlit-text-input" style="max-width: 600px; margin-bottom: 8px">
        <label>返回结果数量</label>
        <input type="range" min="1" max="10" v-model.number="topN" />
        <div class="streamlit-help">Top {{ topN }}</div>
      </div>
      <button
        class="streamlit-button streamlit-button-primary"
        :disabled="isMatching"
        @click="startMatching"
      >
        {{ isMatching ? "正在匹配中…" : "开始匹配分类" }}
      </button>
      <div class="streamlit-help">将根据研究描述匹配最相关的ArXiv分类</div>
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
          <div>
            <code>{{ r.id }}</code>
          </div>
          <div>{{ r.name }}</div>
          <div>{{ r.score }}</div>
        </div>
      </div>
    </div>

    <!-- 统计（置于页面下方，统一样式） -->
    <div class="streamlit-expander">
      <div class="streamlit-expander-header" @click="toggleStatsCollapse">
        <strong>📊 统计</strong>
        <span style="float: right; color: var(--color-text-soft)">{{
          statsCollapsed ? "展开" : "折叠"
        }}</span>
      </div>
      <div class="streamlit-expander-content" v-show="!statsCollapsed">
        <div v-if="tokenUsage.total_tokens > 0" style="margin-bottom: 12px">
          <div class="token-grid">
            <div class="token-item">
              <div class="token-value">{{ tokenUsage.input_tokens }}</div>
              <div class="token-label">输入Token</div>
            </div>
            <div class="token-item">
              <div class="token-value">{{ tokenUsage.output_tokens }}</div>
              <div class="token-label">输出Token</div>
            </div>
            <div class="token-item">
              <div class="token-value">{{ tokenUsage.total_tokens }}</div>
              <div class="token-label">总Token</div>
            </div>
          </div>
        </div>
        <div class="status-grid">
          <div v-if="stats" class="status-item">
            <div class="status-label">总记录数</div>
            <div class="status-value">{{ stats.total_records }}</div>
          </div>
          <div v-if="stats" class="status-item">
            <div class="status-label">用户数量</div>
            <div class="status-value">{{ stats.unique_users }}</div>
          </div>
          <button class="streamlit-button" :disabled="isLoading" @click="refreshData">
            🔄 刷新数据
          </button>
        </div>
      </div>
    </div>

    <!-- 用户数据管理（可折叠） -->
    <div class="streamlit-expander">
      <div class="streamlit-expander-header" @click="toggleManagementCollapse">
        <strong>👥 用户数据管理</strong>
        <span style="float: right; color: var(--color-text-soft)">{{
          managementCollapsed ? "展开" : "折叠"
        }}</span>
      </div>
      <div class="streamlit-expander-content" v-show="!managementCollapsed">
        <div class="streamlit-text-input" style="margin-bottom: 10px">
          <label>🔍 搜索用户或内容</label>
          <input
            type="text"
            v-model="searchTerm"
            :disabled="isMatching"
            class="streamlit-input"
            placeholder="输入用户名或研究内容关键词…"
          />
        </div>

        <div class="button-row" style="margin-bottom: 8px">
          <button class="streamlit-button" :disabled="isMatching" @click="selectAll">
            ✅ 全选
          </button>
          <button class="streamlit-button" :disabled="isMatching" @click="clearSelection">
            ❌ 取消全选
          </button>
          <button
            class="streamlit-button streamlit-button-danger"
            @click="batchDelete"
            :disabled="isMatching || selectedIndices.size === 0"
          >
            🗑️ 批量删除
          </button>
          <button class="streamlit-button" :disabled="isMatching" @click="exportJSON">
            📥 导出JSON
          </button>
        </div>

        <div class="streamlit-help" style="margin-top: 10px; margin-bottom: 10px">
          提示：当前前端仅展示与管理数据，编辑与删除需后端API支持。
        </div>

        <div class="records-list" v-if="filteredProfiles.length > 0">
          <div class="streamlit-expander">
            <div class="streamlit-expander-header" @click="toggleRecordsCollapse">
              <strong>📄 用户记录</strong>
              <span style="float: right; color: var(--color-text-soft)">{{
                recordsCollapsed ? "展开" : "折叠"
              }}</span>
            </div>
            <div class="streamlit-expander-content" v-show="!recordsCollapsed">
              <div v-for="(item, i) in filteredProfiles" :key="i" class="record-item">
                <div class="record-header">
                  <label>
                    <input
                      type="checkbox"
                      :disabled="isMatching"
                      :checked="selectedIndices.has(i)"
                      @change="toggleSelection(i, $event)"
                    />
                    记录 {{ i + 1 }}: {{ item.username || "Unknown" }}
                  </label>
                  <div class="record-actions">
                    <button
                      class="streamlit-button streamlit-button-small"
                      :disabled="isMatching"
                      @click="toggleEdit(i)"
                    >
                      {{ editModes.has(i) ? "💾 保存" : "✏️ 编辑" }}
                    </button>
                    <button
                      class="streamlit-button streamlit-button-small"
                      :disabled="isMatching || !editModes.has(i)"
                      @click="cancelEdit(i)"
                    >
                      ❌ 取消
                    </button>
                    <button
                      class="streamlit-button streamlit-button-small streamlit-button-danger"
                      :disabled="isMatching"
                      @click="deleteRecord(i)"
                    >
                      🗑️ 删除
                    </button>
                  </div>
                </div>
                <div class="record-body">
                  <template v-if="editModes.has(i)">
                    <div class="record-edit-grid">
                      <div class="edit-field">
                        <label>用户名</label>
                        <input
                          type="text"
                          class="streamlit-input"
                          v-model="editDrafts[i].username"
                        />
                      </div>
                      <div class="edit-field">
                        <label>分类ID</label>
                        <input
                          type="text"
                          class="streamlit-input"
                          v-model="editDrafts[i].category_id"
                        />
                      </div>
                      <div class="edit-field">
                        <label>研究内容描述</label>
                        <textarea
                          class="streamlit-textarea"
                          v-model="editDrafts[i].user_input"
                        ></textarea>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <div class="record-field">
                      <strong>分类标签：</strong><code>{{ item.category_id || "未设置" }}</code>
                    </div>
                    <div class="record-field">
                      <strong>研究兴趣：</strong>
                      <pre class="research-interests-code">{{ item.user_input || "未设置" }}</pre>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="streamlit-info">
          📝 暂无数据记录，请先进行分类匹配或在后端添加用户配置。
        </div>
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
const { isLoading, error, userProfiles } = storeToRefs(store);

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

// 可折叠分区：配置与统计、用户数据管理
const statsCollapsed = ref(false);
const managementCollapsed = ref(false);
const toggleStatsCollapse = () => {
  statsCollapsed.value = !statsCollapsed.value;
  try {
    localStorage.setItem("matcher_stats_collapsed", statsCollapsed.value ? "1" : "0");
  } catch {}
};
const toggleManagementCollapse = () => {
  managementCollapsed.value = !managementCollapsed.value;
  try {
    localStorage.setItem("matcher_management_collapsed", managementCollapsed.value ? "1" : "0");
  } catch {}
};

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
      stats.value =
        (res as { stats?: { total_records?: number; unique_users?: number } }).stats || null;
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
      const tmpl = (resp as any).template_error as
        | {
            friendly_message?: string;
            fix_suggestions?: string[];
            details?: Record<string, unknown>;
          }
        | undefined;
      if (tmpl?.friendly_message) {
        const tips =
          Array.isArray(tmpl.fix_suggestions) && tmpl.fix_suggestions.length
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
      const tmpl = (resp as any).template_error as
        | {
            friendly_message?: string;
            fix_suggestions?: string[];
            details?: Record<string, unknown>;
          }
        | undefined;
      if (tmpl?.friendly_message) {
        const tips =
          Array.isArray(tmpl.fix_suggestions) && tmpl.fix_suggestions.length
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
    const s1 = localStorage.getItem("matcher_stats_collapsed");
    if (s1 === "1") statsCollapsed.value = true;
    else if (s1 === "0") statsCollapsed.value = false;
    const s2 = localStorage.getItem("matcher_management_collapsed");
    if (s2 === "1") managementCollapsed.value = true;
    else if (s2 === "0") managementCollapsed.value = false;
  } catch {}

  // 初始化服务与数据
  try {
    await api.initializeService();
  } catch {}
  await refreshData();
});
</script>
