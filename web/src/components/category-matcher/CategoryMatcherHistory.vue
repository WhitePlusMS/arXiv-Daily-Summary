<template>
  <div class="ui-card">
    <div
      class="ui-expander-header"
      @click="$emit('toggle-collapse')"
      :class="{ expanded: !managementCollapsed }"
    >
      <span class="ui-expander-icon">{{ managementCollapsed ? "▶" : "▼" }}</span>
      <strong>👥 用户数据管理</strong>
    </div>
    <div class="ui-expander-content" v-show="!managementCollapsed">
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
        <button class="ui-button ui-button-small" :disabled="isLoading" @click="$emit('refresh')">
          🔄 刷新数据
        </button>
      </div>

      <!-- Token使用统计（如果有） -->
      <div v-if="tokenUsage.total_tokens > 0" class="token-usage-section">
        <div class="ui-help" style="margin-bottom: 8px">📊 最近一次匹配的Token使用情况：</div>
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

      <div class="ui-input-container" style="margin-top: 16px; margin-bottom: 10px">
        <label>🔍 搜索用户或内容</label>
        <input
          type="text"
          :value="searchTerm"
          @input="$emit('update-search', ($event.target as HTMLInputElement).value)"
          :disabled="isMatching"
          class="ui-input"
          placeholder="输入用户名或研究内容关键词…"
        />
      </div>

      <div class="button-row" style="margin-bottom: 8px">
        <button class="ui-button" :disabled="isMatching" @click="$emit('select-all')">
          ✅ 全选
        </button>
        <button class="ui-button" :disabled="isMatching" @click="$emit('clear-selection')">
          ❌ 取消全选
        </button>
        <button
          class="ui-button ui-button-danger"
          @click="$emit('batch-delete')"
          :disabled="isMatching || selectedIndices.size === 0"
        >
          🗑️ 批量删除
        </button>
        <button class="ui-button" :disabled="isMatching" @click="$emit('export')">
          📥 导出JSON
        </button>
      </div>

      <div class="records-list" v-if="filteredProfiles.length > 0">
        <h3 class="ui-subheader" style="margin-bottom: 8px">📄 用户记录</h3>
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
                class="ui-button ui-button-small"
                :disabled="isMatching"
                @click="$emit('toggle-edit', i)"
              >
                {{ editModes.has(i) ? "💾 保存" : "✏️ 编辑" }}
              </button>
              <button
                class="ui-button ui-button-small"
                :disabled="isMatching || !editModes.has(i)"
                @click="$emit('cancel-edit', i)"
              >
                ❌ 取消
              </button>
              <button
                class="ui-button ui-button-small ui-button-danger"
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
                    class="ui-input"
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
                    class="ui-input"
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
                    class="ui-textarea"
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
                    class="ui-textarea"
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
      <div v-else class="ui-alert-info">
        📝 暂无数据记录，请先进行分类匹配或在后端添加用户配置。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from "vue";

interface Stats {
  total_records: number;
  unique_users: number;
}
interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}
interface Profile {
  username: string;
  [key: string]: any;
}

const props = defineProps<{
  stats: Stats | null;
  managementCollapsed: boolean;
  searchTerm: string;
  selectedIndices: Set<number>;
  editModes: Record<number, boolean>;
  editDrafts: Record<number, Profile>;
  filteredProfiles: Profile[];
  isLoading: boolean;
  tokenUsage: TokenUsage;
  isMatching: boolean;
}>();

defineEmits([
  "toggle-collapse",
  "refresh",
  "update-search",
  "select-all",
  "clear-selection",
  "batch-delete",
  "export",
  "toggle-selection",
  "toggle-edit",
  "cancel-edit",
  "delete-record",
  "update-draft",
]);
</script>

<style scoped>
/* Management Header */
.management-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-background-soft);
  border-radius: var(--ui-radius);
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.stats-summary {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.stat-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--ui-radius);
}

.stat-badge-label {
  color: var(--color-text-soft);
  font-size: var(--font-size-sm);
}

.stat-badge-value {
  color: var(--color-text);
  font-weight: 600;
  font-size: var(--font-size-md);
}

@media (max-width: 768px) {
  .management-header {
    flex-direction: column;
    align-items: stretch;
  }

  .stats-summary {
    width: 100%;
    justify-content: space-between;
  }
}

/* Token Usage */
.token-usage-section {
  margin-top: 16px;
  padding: 16px;
  background: var(--color-background-soft);
  border-radius: var(--ui-radius);
  border: 1px solid var(--color-border);
}

.token-grid-compact {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.token-item-compact {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--ui-radius);
}

.token-label-compact {
  color: var(--color-text-soft);
  font-size: var(--font-size-sm);
}

.token-value-compact {
  color: var(--color-text);
  font-weight: 600;
  font-size: var(--font-size-base-rem);
}

/* Records List */
.records-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-item {
  border: 1px solid var(--color-border);
  border-radius: var(--ui-radius);
  padding: 16px;
  background: var(--color-background);
  transition: all 0.2s ease;
}

.record-item:hover {
  border-color: var(--color-border-hover);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.record-actions {
  display: flex;
  gap: 8px;
}

.record-body {
  margin-top: 8px;
}

.research-interests-code {
  background: var(--color-background-soft);
  padding: 4px 8px;
  border-radius: 6px;
  white-space: pre-wrap;
  font-family: var(--font-family-base);
  font-size: var(--font-size-base-rem);
}

.record-edit-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.edit-field label {
  display: block;
  margin-bottom: 4px;
  color: var(--color-text-soft);
}
</style>
