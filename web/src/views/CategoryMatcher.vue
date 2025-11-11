<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<template>
  <div class="streamlit-dashboard">
    <!-- 页面头部 -->
    <div class="streamlit-header">
      <h1 class="streamlit-title">📚 ArXiv推荐系统 - 分类匹配器</h1>
      <div class="guide-card">
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

    <!-- 主要内容区域 - 单栏布局 -->
    <div class="dashboard-content">
      <!-- 研究信息输入和匹配 -->
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

        <div class="form-actions">
          <div class="action-buttons">
            <button
              class="streamlit-button"
              :disabled="isMatching || !researchDescription.trim()"
              @click="optimizeDescription"
            >
              ✨ AI优化描述
            </button>
          </div>
          
          <div class="match-config">
            <div class="streamlit-text-input">
              <label>返回结果数量</label>
              <input 
                type="number" 
                min="1" 
                max="10" 
                v-model.number="topN" 
                class="streamlit-input"
                style="width: 100px;"
              />
            </div>
            <button
              class="streamlit-button streamlit-button-primary"
              :disabled="isMatching || !username.trim() || !researchDescription.trim()"
              @click="startMatching"
            >
              {{ isMatching ? "正在匹配中…" : "🔍 开始匹配分类" }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 进度显示区域 -->
    <div v-if="showProgress" class="dashboard-progress">
      <ProgressDisplay :progress="currentProgress" title="分类匹配运行进度" :show-logs="true" />
    </div>

    <!-- 运行状态和结果区域（兼容旧模式） -->
    <div v-if="(isMatching && !showProgress) || matchCompleted || results.length > 0" class="dashboard-results">
      <!-- 运行状态 -->
      <div v-if="isMatching && !showProgress" class="streamlit-section">
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
    </div>

    <!-- 用户数据管理（整合统计信息） -->
    <div class="streamlit-section">
      <div
        class="streamlit-expander-header"
        @click="toggleManagementCollapse"
        :class="{ expanded: !managementCollapsed }"
      >
        <span class="expander-icon">{{ managementCollapsed ? "▶" : "▼" }}</span>
        <strong>👥 用户数据管理</strong>
      </div>
      <div class="streamlit-expander-content" v-show="!managementCollapsed">
        <!-- 统计信息 -->
        <div class="management-header">
          <div class="stats-summary">
            <div v-if="stats" class="stat-badge">
              <span class="stat-badge-label">总记录数：</span>
              <span class="stat-badge-value">{{ stats.total_records || 0 }}</span>
            </div>
            <div v-if="stats" class="stat-badge">
              <span class="stat-badge-label">用户数量：</span>
              <span class="stat-badge-value">{{ stats.unique_users || 0 }}</span>
            </div>
          </div>
          <button class="streamlit-button streamlit-button-small" :disabled="isLoading" @click="refreshData">
            🔄 刷新数据
          </button>
        </div>

        <!-- Token使用统计（如果有） -->
        <div v-if="tokenUsage.total_tokens > 0" class="token-usage-section">
          <div class="streamlit-help" style="margin-bottom: 8px;">📊 最近一次匹配的Token使用情况：</div>
          <div class="token-grid-compact">
            <div class="token-item-compact">
              <span class="token-label-compact">输入：</span>
              <span class="token-value-compact">{{ tokenUsage.input_tokens }}</span>
            </div>
            <div class="token-item-compact">
              <span class="token-label-compact">输出：</span>
              <span class="token-value-compact">{{ tokenUsage.output_tokens }}</span>
            </div>
            <div class="token-item-compact">
              <span class="token-label-compact">总计：</span>
              <span class="token-value-compact">{{ tokenUsage.total_tokens }}</span>
            </div>
          </div>
        </div>

        <div class="streamlit-text-input" style="margin-top: 16px; margin-bottom: 10px">
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

        <div class="records-list" v-if="filteredProfiles.length > 0">
          <h3 class="streamlit-subheader" style="margin-bottom:8px;">📄 用户记录</h3>
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
import type { UserProfile, ProgressData } from "@/types";
import { progressService } from "@/services/progress";
import ProgressDisplay from "@/components/ProgressDisplay.vue";

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
// 用户记录列表不再使用内部折叠，保持主面板简洁

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

// 进度相关状态
const currentTaskId = ref<string | null>(null);
const currentProgress = ref<ProgressData | null>(null);
const showProgress = ref(false);

// localStorage key，用于保存运行中的task_id
const RUNNING_TASK_KEY = "arxiv_category_matcher_task_id";

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
  runningMessage.value = `🔄 启动分类匹配（Top ${topN.value}）...`;
  try {
    store.clearError();
    const resp = await api.runCategoryMatching({
      user_input: researchDescription.value.trim(),
      username: username.value.trim(),
      top_n: topN.value,
    });
    
    // 检查是否返回了task_id（新的异步模式）
    if (resp.success && resp.data && (resp.data as any).task_id) {
      const taskId = (resp.data as any).task_id;
      currentTaskId.value = taskId;
      showProgress.value = true;
      
      // 保存task_id到localStorage，用于页面刷新后恢复
      try {
        localStorage.setItem(RUNNING_TASK_KEY, taskId);
      } catch (e) {
        console.warn("无法保存task_id到localStorage:", e);
      }
      
      // 开始轮询进度
      progressService.startPolling(
        taskId,
        (progress) => {
          // 更新进度
          currentProgress.value = progress;
        },
        async (progress) => {
          // 任务完成
          console.log("分类匹配完成", progress);
          showProgress.value = false;
          isMatching.value = false;
          matchCompleted.value = true;
          
          // 清除localStorage中的task_id
          try {
            localStorage.removeItem(RUNNING_TASK_KEY);
          } catch (e) {
            console.warn("无法清除localStorage:", e);
          }
          
          // 刷新数据列表
          await refreshData();
          
          // 清除错误
          store.setError("");
        },
        (error) => {
          // 任务失败
          console.error("分类匹配失败", error);
          showProgress.value = false;
          isMatching.value = false;
          
          // 清除localStorage中的task_id
          try {
            localStorage.removeItem(RUNNING_TASK_KEY);
          } catch (e) {
            console.warn("无法清除localStorage:", e);
          }
          
          store.setError(error);
        }
      );
    } else {
      // 兼容旧的同步模式或错误响应
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
      isMatching.value = false;
    }
  } catch (err) {
    store.setError("执行匹配时发生错误");
    console.error("匹配错误:", err);
    isMatching.value = false;
    showProgress.value = false;
  } finally {
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

// 恢复运行中的任务进度
const restoreRunningTask = async () => {
  try {
    const savedTaskId = localStorage.getItem(RUNNING_TASK_KEY);
    if (!savedTaskId) return;
    
    // 检查任务是否还在运行
    const progressResponse = await api.getTaskProgress(savedTaskId);
    if (progressResponse.success && progressResponse.data) {
      const progress = progressResponse.data as ProgressData;
      
      // 如果任务还在运行，恢复进度显示
      if (progress.status === "running") {
        console.log("恢复运行中的匹配任务:", savedTaskId);
        currentTaskId.value = savedTaskId;
        currentProgress.value = progress;
        showProgress.value = true;
        isMatching.value = true;
        
        // 继续轮询进度
        progressService.startPolling(
          savedTaskId,
          (updatedProgress) => {
            currentProgress.value = updatedProgress;
          },
          async (finalProgress) => {
            // 任务完成
            console.log("恢复的匹配任务已完成", finalProgress);
            showProgress.value = false;
            isMatching.value = false;
            matchCompleted.value = true;
            localStorage.removeItem(RUNNING_TASK_KEY);
            await refreshData();
            store.setError("");
          },
          (error) => {
            // 任务失败
            console.error("恢复的匹配任务失败", error);
            showProgress.value = false;
            isMatching.value = false;
            localStorage.removeItem(RUNNING_TASK_KEY);
            store.setError(error);
          }
        );
      } else {
        // 任务已完成或失败，清除localStorage
        localStorage.removeItem(RUNNING_TASK_KEY);
      }
    } else {
      // 任务不存在或已过期，清除localStorage
      localStorage.removeItem(RUNNING_TASK_KEY);
    }
  } catch (err) {
    console.warn("恢复匹配任务失败:", err);
    localStorage.removeItem(RUNNING_TASK_KEY);
  }
};

onMounted(async () => {
  // 读取折叠状态持久化
  try {
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
  
  // 恢复运行中的任务（如果有）
  await restoreRunningTask();
});
</script>
