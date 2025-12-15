<template>
  <div class="streamlit-section">
    <div
      class="streamlit-expander-header"
      @click="$emit('toggle-collapse')"
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
        <button
          class="streamlit-button streamlit-button-small"
          :disabled="isLoading"
          @click="$emit('refresh')"
        >
          🔄 刷新数据
        </button>
      </div>

      <!-- Token使用统计（如果有） -->
      <div v-if="tokenUsage.total_tokens > 0" class="token-usage-section">
        <div class="streamlit-help" style="margin-bottom: 8px">
          📊 最近一次匹配的Token使用情况：
        </div>
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
          :value="searchTerm"
          @input="$emit('update-search', ($event.target as HTMLInputElement).value)"
          :disabled="isMatching"
          class="streamlit-input"
          placeholder="输入用户名或研究内容关键词…"
        />
      </div>

      <div class="button-row" style="margin-bottom: 8px">
        <button class="streamlit-button" :disabled="isMatching" @click="$emit('select-all')">
          ✅ 全选
        </button>
        <button class="streamlit-button" :disabled="isMatching" @click="$emit('clear-selection')">
          ❌ 取消全选
        </button>
        <button
          class="streamlit-button streamlit-button-danger"
          @click="$emit('batch-delete')"
          :disabled="isMatching || selectedIndices.size === 0"
        >
          🗑️ 批量删除
        </button>
        <button class="streamlit-button" :disabled="isMatching" @click="$emit('export')">
          📥 导出JSON
        </button>
      </div>

      <div class="records-list" v-if="filteredProfiles.length > 0">
        <h3 class="streamlit-subheader" style="margin-bottom: 8px">📄 用户记录</h3>
        <div v-for="(item, i) in filteredProfiles" :key="i" class="record-item">
          <div class="record-header">
            <label>
              <input
                type="checkbox"
                :disabled="isMatching"
                :checked="selectedIndices.has(i)"
                @change="$emit('toggle-selection', i, ($event.target as HTMLInputElement).checked)"
              />
              记录 {{ i + 1 }}: {{ item.username || "Unknown" }}
            </label>
            <div class="record-actions">
              <button
                class="streamlit-button streamlit-button-small"
                :disabled="isMatching"
                @click="$emit('toggle-edit', i)"
              >
                {{ editModes.has(i) ? "💾 保存" : "✏️ 编辑" }}
              </button>
              <button
                class="streamlit-button streamlit-button-small"
                :disabled="isMatching || !editModes.has(i)"
                @click="$emit('cancel-edit', i)"
              >
                ❌ 取消
              </button>
              <button
                class="streamlit-button streamlit-button-small streamlit-button-danger"
                :disabled="isMatching"
                @click="$emit('delete-record', i)"
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
                    :value="editDrafts[i]?.username"
                    @input="
                      $emit(
                        'update-draft',
                        i,
                        'username',
                        ($event.target as HTMLInputElement).value
                      )
                    "
                  />
                </div>
                <div class="edit-field">
                  <label>分类ID</label>
                  <input
                    type="text"
                    class="streamlit-input"
                    :value="editDrafts[i]?.category_id"
                    @input="
                      $emit(
                        'update-draft',
                        i,
                        'category_id',
                        ($event.target as HTMLInputElement).value
                      )
                    "
                  />
                </div>
                <div class="edit-field">
                  <label>研究内容描述（感兴趣的方向）</label>
                  <textarea
                    class="streamlit-textarea"
                    :value="editDrafts[i]?.user_input"
                    @input="
                      $emit(
                        'update-draft',
                        i,
                        'user_input',
                        ($event.target as HTMLTextAreaElement).value
                      )
                    "
                  ></textarea>
                </div>
                <div class="edit-field">
                  <label>不感兴趣的方向（可选）</label>
                  <textarea
                    class="streamlit-textarea"
                    :value="editDrafts[i]?.negative_query"
                    @input="
                      $emit(
                        'update-draft',
                        i,
                        'negative_query',
                        ($event.target as HTMLTextAreaElement).value
                      )
                    "
                  ></textarea>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="record-field">
                <strong>分类标签：</strong><code>{{ item.category_id || "未设置" }}</code>
              </div>
              <div class="record-field">
                <strong>研究兴趣（感兴趣的方向）：</strong>
                <pre class="research-interests-code">{{ item.user_input || "未设置" }}</pre>
              </div>
              <div class="record-field" v-if="item.negative_query">
                <strong>不感兴趣的方向：</strong>
                <pre class="research-interests-code">{{ item.negative_query }}</pre>
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
</template>

<script setup lang="ts">
import type { UserProfile } from "@/services/api";

defineProps<{
  stats: any;
  managementCollapsed: boolean;
  searchTerm: string;
  selectedIndices: Set<number>;
  editModes: Set<number>;
  editDrafts: Record<number, Partial<UserProfile>>;
  filteredProfiles: UserProfile[];
  isLoading: boolean;
  tokenUsage: { input_tokens: number; output_tokens: number; total_tokens: number };
  isMatching: boolean;
}>();

defineEmits<{
  (e: "toggle-collapse"): void;
  (e: "refresh"): void;
  (e: "update-search", value: string): void;
  (e: "select-all"): void;
  (e: "clear-selection"): void;
  (e: "toggle-selection", index: number, checked: boolean): void;
  (e: "batch-delete"): void;
  (e: "export"): void;
  (e: "toggle-edit", index: number): void;
  (e: "cancel-edit", index: number): void;
  (e: "delete-record", index: number): void;
  (e: "update-draft", index: number, field: string, value: string): void;
}>();
</script>
