<template>
  <div class="streamlit-dashboard">
    <!-- 页头 -->
    <div class="streamlit-header">
      <h1 class="streamlit-title">⚙️ ArXiv推荐系统 - 环境配置</h1>
    </div>

    <!-- 顶部未保存更改横幅（置顶） -->
    <div v-if="changedKeys.length > 0" class="unsaved-banner">
      <span>⚠️ 未保存更改（{{ changedKeys.length }} 项）</span>
      <div class="banner-actions">
        <button class="streamlit-button streamlit-button-small" @click="toggleChanges">
          {{ showChanges ? "隐藏详情" : "查看详情" }}
        </button>
        <button
          class="streamlit-button streamlit-button-small streamlit-button-primary"
          :disabled="isLoading"
          @click="saveConfig"
        >
          立即保存
        </button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <!-- 概览状态卡片 -->
      <div class="streamlit-section">
        <h2 class="streamlit-subheader">📊 配置概览</h2>
        <div class="stats-card">
          <div class="stat-item">
            <div :class="['stat-value', hasDashscopeKey ? 'green' : 'red']">
              {{ hasDashscopeKey ? "已配置" : "未配置" }}
            </div>
            <div class="stat-label">DashScope API Key</div>
          </div>
          <div class="stat-item">
            <div :class="['stat-value', emailEnabled ? 'green' : 'red']">
              {{ emailEnabled ? "已启用" : "未启用" }}
            </div>
            <div class="stat-label">邮件发送</div>
          </div>
          <div class="stat-item">
            <div :class="['stat-value', debugEnabled ? 'green' : '']">
              {{ debugEnabled ? "调试模式" : "生产模式" }}
            </div>
            <div class="stat-label">运行模式</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">{{ lightProviderLabel }}</div>
            <div class="stat-label">轻量模型提供方</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ heavyProviderLabel }}</div>
            <div class="stat-label">主模型提供方</div>
          </div>
        </div>
      </div>

      <!-- 未保存更改提示 -->
      <div v-if="changedKeys.length > 0 && showChanges" class="streamlit-section">
        <div class="streamlit-warning">
          <strong>📋 更改详情（未保存）</strong>
          <div class="streamlit-expander-content" style="margin-top: 12px;">
            <ul class="changes-list">
              <li v-for="k in changedKeys" :key="k">
                <strong>{{ k }}</strong
                >：文件=`{{ truncate(loadedConfig[k]) }}` → 界面=`{{ truncate(configChanges[k]) }}`
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div v-else-if="changedKeys.length === 0" class="streamlit-success">✅ 所有配置已同步，无未保存更改</div>
    </div>

    <!-- 配置分组和表单区域 -->
    <div class="dashboard-content">
      <!-- 分组标签导航 -->
      <div class="streamlit-section">
        <h2 class="streamlit-subheader">📑 配置分组</h2>
        <div class="button-row">
          <button
            v-for="s in sections"
            :key="s"
            class="streamlit-button streamlit-button-small"
            :class="{ 'streamlit-button-primary': s === selectedSection }"
            :disabled="isLoading"
            @click="selectedSection = s"
          >
            {{ s }}
          </button>
        </div>
      </div>

      <!-- 配置表单区域 -->
      <div class="streamlit-section">
        <h2 class="streamlit-subheader">{{ selectedSection }}</h2>

      <!-- 🤖 模型与API配置（卡片布局重构） -->
      <div v-if="selectedSection === '🤖 模型与API配置'" class="form-grid">
        <!-- 卡片1：提供商基础配置（始终显示） -->
        <div class="form-subsection">
          <h3 class="form-subsection-title">提供商基础配置</h3>
          <div class="form-item">
            <label>DASHSCOPE_API_KEY</label>
            <div class="password-field">
              <input
                :type="showDashscopeKey ? 'text' : 'password'"
                v-model="configChanges.DASHSCOPE_API_KEY"
                class="streamlit-input"
                autocomplete="new-password"
              />
              <button
                type="button"
                class="toggle-visibility"
                @click="showDashscopeKey = !showDashscopeKey"
              >
                {{ showDashscopeKey ? "隐藏" : "显示" }}
              </button>
            </div>
            <div class="streamlit-help">用于访问通义千问的密钥；请妥善保管。</div>
          </div>
          <div class="form-item">
            <label>DASHSCOPE_BASE_URL</label>
            <input type="text" v-model="configChanges.DASHSCOPE_BASE_URL" class="streamlit-input" />
            <div class="streamlit-help">通义服务的基地址，通常保留默认即可。</div>
          </div>
          <!-- 已移除 Ollama 服务地址配置，统一使用 DashScope -->
        </div>

        <!-- 卡片2：分类匹配模型提供方与参数 -->
        <div class="form-subsection">
          <h3 class="form-subsection-title">分类匹配模型提供方与参数</h3>
          <div class="form-item">
            <label>分类匹配模型提供方</label>
            <select v-model="configChanges.LIGHT_MODEL_PROVIDER" class="streamlit-select">
              <option value="dashscope">dashscope</option>
            </select>
            <div class="streamlit-help">用于 Top-N 分类评分的分类匹配模型推理；dashscope=通义千问。</div>
          </div>

          <!-- DashScope 分类匹配参数，仅当提供方选择 dashscope 时显示 -->
          <div v-if="configChanges.LIGHT_MODEL_PROVIDER === 'dashscope'">
            <div class="form-item">
              <label>QWEN_MODEL_LIGHT</label>
              <input type="text" v-model="configChanges.QWEN_MODEL_LIGHT" class="streamlit-input" />
              <div class="streamlit-help">分类匹配模型（更快）。</div>
            </div>
            <div class="form-item">
              <label>QWEN_MODEL_LIGHT_TEMPERATURE</label>
              <input
                type="number"
                step="0.1"
                v-model="configChanges.QWEN_MODEL_LIGHT_TEMPERATURE"
                class="streamlit-input"
                readonly
                style="background-color: #f5f5f5; cursor: not-allowed;"
              />
              <div class="streamlit-help">分类匹配模型温度（适用于 DashScope）。此参数为只读，禁止手动修改。</div>
            </div>
            <div class="form-item">
              <label>QWEN_MODEL_LIGHT_TOP_P</label>
              <input
                type="number"
                step="0.05"
                v-model="configChanges.QWEN_MODEL_LIGHT_TOP_P"
                class="streamlit-input"
              />
              <div class="streamlit-help">分类匹配模型采样阈值 Top P。</div>
            </div>
            <div class="form-item">
              <label>QWEN_MODEL_LIGHT_MAX_TOKENS</label>
              <input
                type="number"
                v-model="configChanges.QWEN_MODEL_LIGHT_MAX_TOKENS"
                class="streamlit-input"
              />
              <div class="streamlit-help">分类匹配模型最大生成长度。</div>
            </div>
          </div>

          <!-- 已移除 Ollama 分类匹配参数配置 -->
        </div>

        <!-- 卡片3：正文分析与报告模型提供方与参数 -->
        <div class="form-subsection">
          <h3 class="form-subsection-title">正文分析与报告模型提供方与参数</h3>
          <div class="form-item">
            <label>正文分析与报告模型提供方</label>
            <select v-model="configChanges.HEAVY_MODEL_PROVIDER" class="streamlit-select">
              <option value="dashscope">dashscope</option>
            </select>
            <div class="streamlit-help">用于正文分析与报告生成的模型；仅支持 DashScope。</div>
          </div>

          <!-- DashScope 正文分析与报告参数，仅当提供方选择 dashscope 时显示 -->
          <div v-if="configChanges.HEAVY_MODEL_PROVIDER === 'dashscope'">
            <div class="form-item">
              <label>QWEN_MODEL</label>
              <input type="text" v-model="configChanges.QWEN_MODEL" class="streamlit-input" />
              <div class="streamlit-help">正文分析与报告模型。</div>
            </div>
            <div class="form-item">
              <label>QWEN_MODEL_TEMPERATURE</label>
              <input
                type="number"
                step="0.1"
                v-model="configChanges.QWEN_MODEL_TEMPERATURE"
                class="streamlit-input"
              />
              <div class="streamlit-help">正文分析与报告模型温度（越高越发散）。适用于 DashScope。</div>
            </div>
            <div class="form-item">
              <label>QWEN_MODEL_TOP_P</label>
              <input
                type="number"
                step="0.05"
                v-model="configChanges.QWEN_MODEL_TOP_P"
                class="streamlit-input"
              />
              <div class="streamlit-help">正文分析与报告模型采样阈值 Top P。适用于 DashScope。</div>
            </div>
            <div class="form-item">
              <label>QWEN_MODEL_MAX_TOKENS</label>
              <input
                type="number"
                v-model="configChanges.QWEN_MODEL_MAX_TOKENS"
                class="streamlit-input"
              />
              <div class="streamlit-help">正文分析与报告模型最大生成长度。适用于 DashScope。</div>
            </div>
          </div>

          <!-- 已移除 Ollama 正文分析与报告参数配置 -->
        </div>

        <!-- 通用线程/并发设置（保持原有键） -->
        <div class="form-item">
          <label>MAX_WORKERS</label>
          <input type="number" v-model="configChanges.MAX_WORKERS" class="streamlit-input" />
        </div>
      </div>

      <!-- 📚 ArXiv配置 -->
      <div v-if="selectedSection === '📚 ArXiv配置'" class="form-grid">
        <div class="form-item">
          <label>ARXIV_BASE_URL</label>
          <input
            type="text"
            v-model="configChanges.ARXIV_BASE_URL"
            class="streamlit-input"
            readonly
            style="background-color: #f5f5f5; cursor: not-allowed;"
          />
          <div class="streamlit-help">ArXiv API 基地址，通常保持默认。</div>
        </div>
        <div class="form-item">
          <label>ARXIV_RETRIES</label>
          <input type="number" v-model="configChanges.ARXIV_RETRIES" class="streamlit-input" />
          <div class="streamlit-help">网络或限流导致失败时的重试次数。</div>
        </div>
        <div class="form-item">
          <label>ARXIV_DELAY</label>
          <input type="number" v-model="configChanges.ARXIV_DELAY" class="streamlit-input" />
          <div class="streamlit-help">相邻请求之间的等待秒数，降低 API 压力。</div>
        </div>
        <div class="form-item">
          <label>MAX_ENTRIES</label>
          <input type="number" v-model="configChanges.MAX_ENTRIES" class="streamlit-input" />
          <div class="streamlit-help">每次拉取的最大论文数量（越大越慢）。</div>
        </div>
        <div class="form-item">
          <label>NUM_DETAILED_PAPERS</label>
          <input
            type="number"
            v-model="configChanges.NUM_DETAILED_PAPERS"
            class="streamlit-input"
          />
          <div class="streamlit-help">详细解读的论文数量。</div>
        </div>
        <div class="form-item">
          <label>NUM_BRIEF_PAPERS</label>
          <input type="number" v-model="configChanges.NUM_BRIEF_PAPERS" class="streamlit-input" />
          <div class="streamlit-help">简要推荐的论文数量。</div>
        </div>
        <div class="form-item">
          <label>RELEVANCE_FILTER_THRESHOLD</label>
          <input
            type="number"
            min="0"
            max="10"
            step="1"
            v-model="configChanges.RELEVANCE_FILTER_THRESHOLD"
            class="streamlit-input"
          />
          <div class="streamlit-help">相关性过滤阈值（0–10）：低于该分数的论文将被剔除。推荐值 6。</div>
        </div>
      </div>

      <!-- 📁 文件路径配置 -->
      <div v-if="selectedSection === '📁 文件路径配置'" class="form-grid">
        <div class="form-item">
          <label>SAVE_MARKDOWN</label>
          <select v-model="configChanges.SAVE_MARKDOWN" class="streamlit-select">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
          <div class="streamlit-help">是否保存 Markdown 版本（同时可生成 HTML）。</div>
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
          <div class="streamlit-help">启用后将自动发送报告到目标邮箱。</div>
        </div>
        <div class="form-item" v-if="emailEnabled">
          <label>SENDER_EMAIL</label>
          <input type="email" v-model="configChanges.SENDER_EMAIL" class="streamlit-input" />
          <div class="streamlit-help">发件人邮箱地址（建议使用独立邮箱）。</div>
        </div>
        <div class="form-item" v-if="emailEnabled">
          <label>RECEIVER_EMAIL</label>
          <input type="email" v-model="configChanges.RECEIVER_EMAIL" class="streamlit-input" />
          <div class="streamlit-help">收件人邮箱地址（多个用逗号分隔）。</div>
        </div>
        <div class="form-item" v-if="emailEnabled">
          <label>EMAIL_PASSWORD</label>
          <div class="password-field">
            <input
              :type="showEmailPassword ? 'text' : 'password'"
              v-model="configChanges.EMAIL_PASSWORD"
              class="streamlit-input"
              autocomplete="new-password"
            />
            <button
              type="button"
              class="toggle-visibility"
              @click="showEmailPassword = !showEmailPassword"
            >
              {{ showEmailPassword ? "隐藏" : "显示" }}
            </button>
          </div>
          <div class="streamlit-help">邮箱授权码/密码（不同服务商可能不同）。</div>
        </div>
        <div class="form-item" v-if="emailEnabled">
          <label>SMTP_SERVER</label>
          <input type="text" v-model="configChanges.SMTP_SERVER" class="streamlit-input" />
          <div class="streamlit-help">SMTP 服务地址，例如 `smtp.qq.com`。</div>
        </div>
        <div class="form-item" v-if="emailEnabled">
          <label>SMTP_PORT</label>
          <input type="number" v-model="configChanges.SMTP_PORT" class="streamlit-input" />
          <div class="streamlit-help">SMTP 服务端口（SSL 常用 465）。</div>
        </div>
        <div class="streamlit-expander" v-if="emailEnabled">
          <div class="streamlit-expander-header" @click="emailAdvancedOpen = !emailAdvancedOpen">
            <span class="expander-icon">{{ emailAdvancedOpen ? "▼" : "▶" }}</span>
            🔧 邮件高级设置
          </div>
          <div v-if="emailAdvancedOpen" class="streamlit-expander-content">
            <div class="form-grid">
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
            </div>
          </div>
        </div>
        <div class="form-item">
          <label>SUBJECT_PREFIX</label>
          <input type="text" v-model="configChanges.SUBJECT_PREFIX" class="streamlit-input" />
          <div class="streamlit-help">邮件标题前缀，用于区分不同来源。</div>
        </div>
      </div>

      <!-- 🕐 时区格式配置 -->
      <div v-if="selectedSection === '🕐 时区格式配置'" class="form-grid">
        <div class="form-item">
          <label>TIMEZONE</label>
          <input type="text" v-model="configChanges.TIMEZONE" class="streamlit-input" />
          <div class="streamlit-help">例如 `Asia/Shanghai`；用于展示时间与报告生成。</div>
        </div>
      </div>

      <!-- 📝 日志配置 -->
      <div v-if="selectedSection === '📝 日志配置'" class="form-grid">
        <div class="form-item">
          <label>是否打开日志</label>
          <select v-model="configChanges.LOG_TO_CONSOLE" class="streamlit-select">
            <option value="true">是</option>
            <option value="false">否</option>
          </select>
          <div class="streamlit-help">是否启用日志记录功能。</div>
        </div>
        <div class="form-item">
          <label>每个文件大小 (MB)</label>
          <input type="number" v-model="configChanges.LOG_MAX_SIZE" class="streamlit-input" min="1" />
          <div class="streamlit-help">单个日志文件的最大大小，单位为MB。</div>
        </div>
        <div class="form-item">
          <label>总体LOG区域大小 (MB)</label>
          <input 
            type="number" 
            v-model.number="totalLogSize" 
            class="streamlit-input" 
            min="1"
            @input="updateLogBackupCount"
          />
          <div class="streamlit-help">所有日志文件的总大小限制，单位为MB。系统会自动计算备份文件数量。</div>
        </div>
      </div>

      <!-- 🧠 高级配置（提示词） -->
      <div v-if="selectedSection === '🧠 高级配置（提示词）'" class="prompt-section">
        <div class="streamlit-info" style="margin-bottom: 12px;">
          该分组用于管理 LLM 提示词模板。每条提示词可单独保存或重置为默认值
        </div>
        <div class="button-row" style="margin-bottom: 12px;">
          <button @click="loadPrompts" :disabled="promptsLoading" class="streamlit-button">🔄 刷新列表</button>
          <button @click="resetAllPrompts" :disabled="promptsLoading" class="streamlit-button">♻️ 重置所有提示词</button>
        </div>
        <div v-if="promptsLoading" class="streamlit-warning">正在加载提示词...</div>
        <div v-else>
          <div v-if="prompts.length === 0" class="streamlit-info">暂无提示词可管理。</div>
          <div
            v-for="p in prompts"
            :key="p.id"
            class="prompt-card"
          >
            <h3 class="streamlit-subheader">
              {{ edits[p.id]?.name || p.name }}
              <small style="font-weight: normal; color: #666;">ID: {{ p.id }}</small>
            </h3>
            <div class="form-item">
              <label>可用变量</label>
              <pre class="var-block">{{ (p.variables && p.variables.length > 0) ? p.variables.join('\n') : '无' }}</pre>
            </div>
            <div class="form-item">
              <label>模板内容</label>
              <textarea v-model="edits[p.id].template" @input="clearPromptError(p.id)" class="streamlit-textarea template-textarea" rows="18" />
            </div>
            <div v-if="promptErrors[p.id]" class="streamlit-error" style="margin-bottom: 8px;">
              ❌ {{ promptErrors[p.id] }}
            </div>
            <div class="button-row prompt-actions">
              <button @click="savePrompt(p.id)" :disabled="promptsLoading" class="streamlit-button streamlit-button-primary">💾 保存该提示词</button>
              <button @click="resetPrompt(p.id)" :disabled="promptsLoading" class="streamlit-button">↩️ 重置为默认</button>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- 底部操作按钮（除提示词分组外显示） -->
    <div class="streamlit-section" v-if="selectedSection !== '🧠 高级配置（提示词）'">
      <div class="button-row">
        <button
          @click="saveConfig"
          :disabled="isLoading"
          class="streamlit-button streamlit-button-primary"
        >
          💾 保存配置
        </button>
        <button @click="reloadConfig" :disabled="isLoading" class="streamlit-button">
          🔄 重新加载
        </button>
        <button @click="restoreDefault" :disabled="isLoading" class="streamlit-button">
          📋 恢复默认
        </button>
        <button @click="resetSectionChanges" :disabled="isLoading" class="streamlit-button">
          ↩️ 重置当前分组
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
import { useArxivStore } from "@/stores/arxiv";
import * as api from "@/services/api";
import type { PromptItem } from "@/types";

const store = useArxivStore();

// 分组列表
const sections = [
  // 将 API、功能映射与 LLM 合并为单一分组
  "🤖 模型与API配置",
  "📧 邮件配置",
  "📚 ArXiv配置",
  "📁 文件路径配置",
  "📝 日志配置",
  "🕐 时区格式配置",
  "🧠 高级配置（提示词）",
];

const selectedSection = ref(sections[0]);
const isLoading = ref(false);
const emailAdvancedOpen = ref(false);
const loadedConfig = ref<Record<string, string>>({});
const configChanges = ref<Record<string, string>>({});
const showChanges = ref(false);
// 密钥显隐切换（默认隐藏）
const showDashscopeKey = ref(false);
const showEmailPassword = ref(false);

// 概览状态
const hasDashscopeKey = computed(
  () => !!String(configChanges.value?.DASHSCOPE_API_KEY || "").trim()
);
const emailEnabled = computed(
  () => String(configChanges.value?.SEND_EMAIL || "").trim() === "true"
);
const lightProviderLabel = computed(
  () => String(configChanges.value?.LIGHT_MODEL_PROVIDER || "").trim() || "未设置"
);
const heavyProviderLabel = computed(
  () => String(configChanges.value?.HEAVY_MODEL_PROVIDER || "").trim() || "未设置"
);

// 计算总体日志大小（MB）
const totalLogSize = computed({
  get: () => {
    const maxSize = Number(configChanges.value?.LOG_MAX_SIZE || 10);
    const backupCount = Number(configChanges.value?.LOG_BACKUP_COUNT || 5);
    return maxSize * backupCount;
  },
  set: (value: number) => {
    const maxSize = Number(configChanges.value?.LOG_MAX_SIZE || 10);
    if (maxSize > 0) {
      const backupCount = Math.max(1, Math.floor(value / maxSize));
      configChanges.value.LOG_BACKUP_COUNT = String(backupCount);
    }
  }
});

// 更新备份数量（当总体大小改变时）
const updateLogBackupCount = () => {
  const maxSize = Number(configChanges.value?.LOG_MAX_SIZE || 10);
  const totalSize = totalLogSize.value;
  if (maxSize > 0 && totalSize > 0) {
    const backupCount = Math.max(1, Math.floor(totalSize / maxSize));
    configChanges.value.LOG_BACKUP_COUNT = String(backupCount);
  }
};

// 监听每个文件大小的变化，自动更新备份数量以保持总体大小
watch(
  () => configChanges.value?.LOG_MAX_SIZE,
  (newSize, oldSize) => {
    if (newSize && oldSize && Number(newSize) !== Number(oldSize)) {
      const maxSize = Number(newSize);
      const totalSize = totalLogSize.value;
      if (maxSize > 0 && totalSize > 0) {
        const backupCount = Math.max(1, Math.floor(totalSize / maxSize));
        configChanges.value.LOG_BACKUP_COUNT = String(backupCount);
      }
    }
  }
);

// 计算未保存更改
const changedKeys = computed(() => {
  const keys = new Set<string>([
    ...Object.keys(loadedConfig.value),
    ...Object.keys(configChanges.value),
  ]);
  const changed: string[] = [];
  keys.forEach((k) => {
    const fileVal = String(loadedConfig.value?.[k] ?? "").trim();
    const uiVal = String(configChanges.value?.[k] ?? "").trim();
    if (fileVal !== uiVal) changed.push(k);
  });
  return changed;
});

const truncate = (val: string) => {
  return val.length > 30 ? val.slice(0, 30) + "..." : val;
};

const toggleChanges = () => {
  showChanges.value = !showChanges.value;
};

// 离开页拦截：存在未保存更改时给出系统提示
const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (changedKeys.value.length > 0) {
    e.preventDefault();
    e.returnValue = "";
  }
};

const normalizeConfig = (cfg: Record<string, string>) => {
  // 将布尔/数值保持字符串形式以与 .env 一致
  const out: Record<string, string> = {};
  Object.entries(cfg || {}).forEach(([k, v]) => {
    if (v === "true") out[k] = "true";
    else if (v === "false") out[k] = "false";
    else out[k] = v;
  });
  return out;
};

// 将字符串数值裁剪为指定整数范围（返回字符串以匹配 .env 格式）
const clampIntString = (val: string | number | undefined, min: number, max: number): string => {
  let n = 0;
  try {
    n = Math.trunc(Number(val));
  } catch {
    n = min;
  }
  if (!Number.isFinite(n)) n = min;
  const clamped = Math.min(max, Math.max(min, n));
  return String(clamped);
};

const loadConfig = async () => {
  isLoading.value = true;
  store.clearError();
  try {
    // 优先使用专用环境配置接口
    const res = await api.getEnvConfig();
    const cfg = res?.data || {};
    loadedConfig.value = normalizeConfig(cfg);
    configChanges.value = { ...loadedConfig.value };
  } catch {
    // 兜底：使用通用配置接口
    try {
      const res2 = await api.getConfig();
      const cfg2 = res2?.data || {};
      loadedConfig.value = normalizeConfig(cfg2);
      configChanges.value = { ...loadedConfig.value };
    } catch (err2) {
      store.setError("加载配置失败");
      console.error("加载配置失败:", err2);
    }
  } finally {
    isLoading.value = false;
  }
};

const saveConfig = async () => {
  isLoading.value = true;
  store.clearError();
  try {
    // 保存前对关键数值进行前端规范化
    const payload: Record<string, string> = { ...configChanges.value };
    if (Object.prototype.hasOwnProperty.call(payload, "RELEVANCE_FILTER_THRESHOLD")) {
      payload.RELEVANCE_FILTER_THRESHOLD = clampIntString(
        payload.RELEVANCE_FILTER_THRESHOLD,
        0,
        10
      );
    }
    const res = await api.saveEnvConfig({ config: payload });
    if (res.success) {
      await loadConfig();
    } else {
      store.setError(res.message || "保存配置失败");
    }
  } catch (err) {
    store.setError("保存配置时发生错误");
    console.error("保存配置错误:", err);
  } finally {
    isLoading.value = false;
  }
};

// 前端实时输入限制：阈值始终维持在 0–10 的整数
watch(
  () => configChanges.value?.RELEVANCE_FILTER_THRESHOLD,
  (nv) => {
    if (nv === undefined || nv === null) return;
    const current = String(nv);
    const clamped = clampIntString(current, 0, 10);
    if (clamped !== current) {
      configChanges.value.RELEVANCE_FILTER_THRESHOLD = clamped;
    }
  }
);

// 推荐预设（按分组）

const reloadConfig = async () => {
  isLoading.value = true;
  store.clearError();
  try {
    const res = await api.reloadEnvConfig();
    if (res.success && res.data) {
      loadedConfig.value = normalizeConfig(res.data);
      configChanges.value = { ...loadedConfig.value };
    } else {
      store.setError(res.message || "重新加载失败");
    }
  } catch (err) {
    store.setError("重新加载时发生错误");
    console.error("重新加载错误:", err);
  } finally {
    isLoading.value = false;
  }
};

const restoreDefault = async () => {
  isLoading.value = true;
  store.clearError();
  try {
    const res = await api.restoreDefaultEnvConfig();
    if (res.success && res.data) {
      loadedConfig.value = normalizeConfig(res.data);
      configChanges.value = { ...loadedConfig.value };
    } else {
      store.setError(res.message || "恢复默认失败");
    }
  } catch (err) {
    store.setError("恢复默认时发生错误");
    console.error("恢复默认错误:", err);
  } finally {
    isLoading.value = false;
  }
};

// 提示词管理状态与方法
const prompts = ref<PromptItem[]>([]);
const promptsLoading = ref(false);
const promptErrors = ref<Record<string, string>>({});
const edits = ref<Record<string, { name: string; template: string }>>({});

const loadPrompts = async () => {
  promptsLoading.value = true;
  store.clearError();
  try {
    const res = await api.listPrompts();
    const list = (res?.data || []) as PromptItem[];
    prompts.value = list;
    const map: Record<string, { name: string; template: string }> = {};
    list.forEach((p) => {
      map[p.id] = {
        name: p.name,
        template: p.template,
      };
    });
    edits.value = map;
  } catch (err) {
    store.setError("加载提示词失败");
    console.error("加载提示词失败:", err);
  } finally {
    promptsLoading.value = false;
  }
};

const clearPromptError = (id: string) => {
  if (promptErrors.value[id]) {
    delete promptErrors.value[id];
  }
  // 同步清理全局错误，避免重复提示
  store.clearError();
};

// 提取模板中的占位符名称（更通用）：如 {user_description}、{0}、{名称}
const extractPlaceholders = (tpl: string): string[] => {
  if (!tpl) return [];
  const tokens: string[] = [];
  let match: RegExpExecArray | null;
  const re = /\{([^{}]+)\}/g;
  while ((match = re.exec(tpl)) !== null) {
    tokens.push(match[1]);
  }
  const names = tokens
    .map((t) => t.split(/[!:\.\[]/)[0].trim())
    .filter((x) => !!x);
  return Array.from(new Set(names));
};

// 校验：占位符是否都在允许的变量列表中
const validateTemplateBeforeSave = (id: string): { valid: boolean; unknown: string[]; allowed: string[] } => {
  const idx = prompts.value.findIndex((x) => x.id === id);
  const allowed = (idx >= 0 && Array.isArray(prompts.value[idx].variables)) ? (prompts.value[idx].variables as string[]) : [];
  const tpl = edits.value[id]?.template || "";
  const used = extractPlaceholders(tpl);
  const unknown = used.filter((x) => !allowed.includes(x));
  return { valid: unknown.length === 0, unknown, allowed };
};

const savePrompt = async (id: string) => {
  promptsLoading.value = true;
  store.clearError();
  try {
    // 保存前校验模板占位符
    const check = validateTemplateBeforeSave(id);
    if (!check.valid) {
      const unknownText = check.unknown.map((n) => `{${n}}`).join(", ");
      const allowedText = (check.allowed || []).join(", ") || "（无）";
      const msg = `模板占位符不匹配：${unknownText}；允许的变量：{${allowedText}}。修复建议：检查占位符是否与变量列表一致`;
      promptErrors.value[id] = msg;
      store.setError(msg);
      return;
    }
    const payload = edits.value[id];
    const res = await api.updatePrompt(id, payload);
    if (res.success && res.data) {
      // 更新当前列表项
      const idx = prompts.value.findIndex((x) => x.id === id);
      if (idx >= 0) {
        prompts.value[idx] = { ...(prompts.value[idx] || {}), ...(res.data as PromptItem) } as PromptItem;
      }
      // 保存成功后清理就地错误
      if (promptErrors.value[id]) {
        delete promptErrors.value[id];
      }
    } else {
      const msg = res?.message || res?.error || "保存提示词失败";
      promptErrors.value[id] = msg;
      store.setError(msg);
    }
  } catch (err) {
    const anyErr = err as any;
    const detailObj = anyErr?.response?.data?.detail;
    const detailStr = typeof detailObj === 'string' ? detailObj : undefined;
    const msg = (detailObj?.friendly_message)
      || anyErr?.response?.data?.message
      || detailStr
      || anyErr?.message
      || "保存提示词时发生错误";
    promptErrors.value[id] = msg;
    store.setError(msg);
    console.error("保存提示词错误:", err);
  } finally {
    promptsLoading.value = false;
  }
};

const resetPrompt = async (id: string) => {
  promptsLoading.value = true;
  store.clearError();
  try {
    const res = await api.resetPrompt(id);
    if (res.success && res.data) {
      const updated = res.data as PromptItem;
      const idx = prompts.value.findIndex((x) => x.id === id);
      if (idx >= 0) {
        prompts.value[idx] = updated;
      }
      edits.value[id] = {
        name: updated.name,
        template: updated.template,
      };
      // 重置为默认后清理就地错误
      if (promptErrors.value[id]) {
        delete promptErrors.value[id];
      }
    } else {
      store.setError(res.message || "重置提示词失败");
    }
  } catch (err) {
    store.setError("重置提示词时发生错误");
    console.error("重置提示词错误:", err);
  } finally {
    promptsLoading.value = false;
  }
};

const resetAllPrompts = async () => {
  promptsLoading.value = true;
  store.clearError();
  try {
    const res = await api.resetAllPrompts();
    if (res.success) {
      await loadPrompts();
    } else {
      store.setError(res.message || "重置所有提示词失败");
    }
  } catch (err) {
    store.setError("重置所有提示词时发生错误");
    console.error("重置所有提示词错误:", err);
  } finally {
    promptsLoading.value = false;
  }
};

// 当前分组字段映射，用于分组重置
const sectionFields: Record<string, string[]> = {
  "🤖 模型与API配置": [
    // 功能映射
    "LIGHT_MODEL_PROVIDER",
    "HEAVY_MODEL_PROVIDER",
    // DashScope API 与模型
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_BASE_URL",
    "QWEN_MODEL",
    "QWEN_MODEL_LIGHT",
    // LLM 常用参数（DashScope）
    "MAX_WORKERS",
    "QWEN_MODEL_TEMPERATURE",
    "QWEN_MODEL_TOP_P",
    "QWEN_MODEL_MAX_TOKENS",
    "QWEN_MODEL_LIGHT_TEMPERATURE",
    "QWEN_MODEL_LIGHT_TOP_P",
    "QWEN_MODEL_LIGHT_MAX_TOKENS",
  ],
  "📚 ArXiv配置": [
    "ARXIV_BASE_URL",
    "ARXIV_RETRIES",
    "ARXIV_DELAY",
    "MAX_ENTRIES",
    "NUM_DETAILED_PAPERS",
    "NUM_BRIEF_PAPERS",
    "RELEVANCE_FILTER_THRESHOLD",
  ],
  "📁 文件路径配置": ["SAVE_MARKDOWN"],
  "📧 邮件配置": [
    "SEND_EMAIL",
    "SENDER_EMAIL",
    "RECEIVER_EMAIL",
    "EMAIL_PASSWORD",
    "SMTP_SERVER",
    "SMTP_PORT",
    "USE_SSL",
    "USE_TLS",
    "SUBJECT_PREFIX",
  ],
  "🕐 时区格式配置": [
    "TIMEZONE",
  ],
  "📝 日志配置": ["LOG_TO_CONSOLE", "LOG_MAX_SIZE", "LOG_BACKUP_COUNT"],
};

const resetSectionChanges = () => {
  const fields = sectionFields[selectedSection.value] || [];
  fields.forEach((k) => {
    configChanges.value[k] = loadedConfig.value[k];
  });
};

onMounted(async () => {
  await loadConfig();
  await loadPrompts();
  window.addEventListener("beforeunload", handleBeforeUnload);
});

onBeforeUnmount(() => {
  window.removeEventListener("beforeunload", handleBeforeUnload);
});
</script>

<style scoped>
.prompt-section {
  width: 100%;
}

.prompt-card {
  width: 100%;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #ffffff;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
}

.var-block {
  white-space: pre-wrap;
  background: #f6f8fa;
  border: 1px solid #eaecef;
  border-radius: 4px;
  padding: 8px 12px;
  font-family: var(--font-family-mono);
  line-height: 1.6;
}

.prompt-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.template-textarea {
  width: 100%;
  min-height: 360px;
  resize: vertical;
  box-sizing: border-box;
  font-family: var(--font-family-mono);
}
</style>
