<template>
  <div class="streamlit-dashboard">
    <!-- 页头 -->
    <div class="streamlit-header">
      <h1 class="streamlit-title">⚙️ ArXiv推荐系统 - 环境配置</h1>
      <div class="streamlit-divider"></div>
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

    <!-- 概览状态卡片 -->
    <div class="streamlit-section">
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
      </div>
    </div>

    <!-- 未保存更改提示（展开详情） -->
    <div class="streamlit-section">
      <div v-if="changedKeys.length > 0">
        <div v-if="showChanges" class="streamlit-warning">
          📋 更改详情（未保存）
          <div class="streamlit-expander-content">
            <ul class="changes-list">
              <li v-for="k in changedKeys" :key="k">
                <strong>{{ k }}</strong
                >：文件=`{{ truncate(loadedConfig[k]) }}` → 界面=`{{ truncate(configChanges[k]) }}`
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div v-else class="streamlit-success">✅ 所有配置已同步，无未保存更改</div>
      <div class="streamlit-divider"></div>
    </div>

    <!-- 分组标签导航（更直观） -->
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
      <div class="streamlit-help">提示：点击上方标签快速切换分组；保存操作集中在页面底部。</div>
      <div class="streamlit-divider"></div>
    </div>

    <!-- 配置表单区域 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">{{ selectedSection }}</h2>

      <!-- 推荐值与快速应用 -->
      <div class="action-row">
        <button
          class="streamlit-button streamlit-button-small"
          :disabled="isLoading"
          @click="applyPreset(selectedSection)"
        >
          ⚡ 应用推荐值
        </button>
        <div class="streamlit-help" v-if="recommendedSummary[selectedSection]">
          推荐摘要：{{ recommendedSummary[selectedSection] }}
        </div>
      </div>

      <!-- 🔑 API配置 -->
      <div v-if="selectedSection === '🔑 API配置'" class="form-grid">
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
        <div class="form-item" v-if="configChanges.LIGHT_MODEL_PROVIDER === 'qwen'">
          <label>QWEN_MODEL</label>
          <input type="text" v-model="configChanges.QWEN_MODEL" class="streamlit-input" />
          <div class="streamlit-help">主推荐使用的模型（重任务）。</div>
        </div>
        <div class="form-item" v-if="configChanges.LIGHT_MODEL_PROVIDER === 'qwen'">
          <label>QWEN_MODEL_LIGHT</label>
          <input type="text" v-model="configChanges.QWEN_MODEL_LIGHT" class="streamlit-input" />
          <div class="streamlit-help">轻量任务使用的模型（更快）。</div>
        </div>
        <div class="form-item">
          <label>OLLAMA_BASE_URL</label>
          <input type="text" v-model="configChanges.OLLAMA_BASE_URL" class="streamlit-input" />
          <div class="streamlit-help">本地/远程 Ollama 服务地址；仅在选择 ollama 时生效。</div>
        </div>
        <div class="form-item" v-if="configChanges.LIGHT_MODEL_PROVIDER === 'ollama'">
          <label>OLLAMA_MODEL_LIGHT</label>
          <input type="text" v-model="configChanges.OLLAMA_MODEL_LIGHT" class="streamlit-input" />
          <div class="streamlit-help">轻量模型名称，例如 `qwen2.5:7b`。</div>
        </div>
        <div class="form-item">
          <label>LIGHT_MODEL_PROVIDER</label>
          <select v-model="configChanges.LIGHT_MODEL_PROVIDER" class="streamlit-select">
            <option value="qwen">qwen</option>
            <option value="ollama">ollama</option>
          </select>
          <div class="streamlit-help">选择轻量推理的提供方（影响展示的参数项）。</div>
        </div>
        <div class="form-item" v-if="configChanges.LIGHT_MODEL_PROVIDER === 'ollama'">
          <label>OLLAMA_MODEL_LIGHT_TEMPERATURE</label>
          <input
            type="range"
            min="0"
            max="1.5"
            step="0.1"
            v-model.number="configChanges.OLLAMA_MODEL_LIGHT_TEMPERATURE"
          />
          <div class="streamlit-help">
            当前值：{{ configChanges.OLLAMA_MODEL_LIGHT_TEMPERATURE }}（更大更发散）
          </div>
        </div>
        <div class="form-item" v-if="configChanges.LIGHT_MODEL_PROVIDER === 'ollama'">
          <label>OLLAMA_MODEL_LIGHT_TOP_P</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            v-model.number="configChanges.OLLAMA_MODEL_LIGHT_TOP_P"
          />
          <div class="streamlit-help">
            当前值：{{ configChanges.OLLAMA_MODEL_LIGHT_TOP_P }}（采样概率阈值）
          </div>
        </div>
        <div class="form-item">
          <label>OLLAMA_MODEL_LIGHT_MAX_TOKENS</label>
          <input
            type="number"
            v-model="configChanges.OLLAMA_MODEL_LIGHT_MAX_TOKENS"
            class="streamlit-input"
          />
          <div class="streamlit-help">轻量模型的最大生成长度，过大将影响性能。</div>
        </div>
      </div>

      <!-- 📚 ArXiv配置 -->
      <div v-if="selectedSection === '📚 ArXiv配置'" class="form-grid">
        <div class="form-item">
          <label>ARXIV_BASE_URL</label>
          <input type="text" v-model="configChanges.ARXIV_BASE_URL" class="streamlit-input" />
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
          <label>ARXIV_CATEGORIES</label>
          <input
            type="text"
            v-model="configChanges.ARXIV_CATEGORIES"
            placeholder="cs.CL, cs.IR, cs.LG"
            class="streamlit-input"
          />
          <div class="streamlit-help">用逗号分隔的分类列表；支持多个学科标签。</div>
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
          <div class="streamlit-help">用户自定义分类文件路径（JSON）。</div>
        </div>
        <div class="form-item">
          <label>SAVE_DIRECTORY</label>
          <input type="text" v-model="configChanges.SAVE_DIRECTORY" class="streamlit-input" />
          <div class="streamlit-help">报告保存目录，例如 `output/reports`。</div>
        </div>
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
        <div class="form-item">
          <label>DATE_FORMAT</label>
          <input type="text" v-model="configChanges.DATE_FORMAT" class="streamlit-input" />
          <div class="streamlit-help">日期格式模板，例如 `YYYY-MM-DD`。</div>
        </div>
        <div class="form-item">
          <label>TIME_FORMAT</label>
          <input type="text" v-model="configChanges.TIME_FORMAT" class="streamlit-input" />
          <div class="streamlit-help">时间格式模板，例如 `HH:mm:ss`。</div>
        </div>
        <div class="form-item">
          <label>ENABLE_MCP_TIME_SERVICE</label>
          <select v-model="configChanges.ENABLE_MCP_TIME_SERVICE" class="streamlit-select">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
          <div class="streamlit-help">启用后可使用 MCP 时间服务进行更准确的时间处理。</div>
        </div>
        <div class="form-item">
          <label>DEBUG_MODE</label>
          <select v-model="configChanges.DEBUG_MODE" class="streamlit-select">
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
          <div class="streamlit-help">调试模式将使用模拟数据，便于快速验证流程。</div>
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

const store = useArxivStore();

// 分组列表
const sections = [
  // 连接优先（API 与邮件），再到数据抓取、推理、输出、时间
  "🔑 API配置",
  "📧 邮件配置",
  "📚 ArXiv配置",
  "🤖 LLM配置",
  "📁 文件路径配置",
  "📝 日志配置",
  "🕐 时区格式配置",
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
const debugEnabled = computed(
  () => String(configChanges.value?.DEBUG_MODE || "").trim() === "true"
);
const lightProviderLabel = computed(
  () => String(configChanges.value?.LIGHT_MODEL_PROVIDER || "").trim() || "未设置"
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
    const res = await api.saveEnvConfig({ config: configChanges.value });
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

// 推荐预设（按分组）
const recommendedPresets: Record<string, Record<string, string>> = {
  "🔑 API配置": {
    DASHSCOPE_BASE_URL: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    LIGHT_MODEL_PROVIDER: "qwen",
    QWEN_MODEL: "qwen-plus",
    QWEN_MODEL_LIGHT: "qwen3-30b-a3b-instruct-2507",
    OLLAMA_BASE_URL: "http://localhost:11434/v1",
    OLLAMA_MODEL_LIGHT: "llama3.2:3b",
    OLLAMA_MODEL_LIGHT_TEMPERATURE: "0.7",
    OLLAMA_MODEL_LIGHT_TOP_P: "0.9",
    OLLAMA_MODEL_LIGHT_MAX_TOKENS: "2000",
  },
  "📚 ArXiv配置": {
    ARXIV_BASE_URL: "http://export.arxiv.org/api/query",
    ARXIV_RETRIES: "3",
    ARXIV_DELAY: "5",
    ARXIV_CATEGORIES: "cs.CV,cs.LG",
    MAX_ENTRIES: "50",
    NUM_DETAILED_PAPERS: "3",
    NUM_BRIEF_PAPERS: "7",
  },
  "🤖 LLM配置": {
    MAX_WORKERS: "5",
  },
  "📁 文件路径配置": {
    USER_CATEGORIES_FILE: "data/users/user_categories.json",
    SAVE_DIRECTORY: "arxiv_history",
    SAVE_MARKDOWN: "true",
  },
  "📧 邮件配置": {
    SEND_EMAIL: "false",
    SMTP_PORT: "587",
    USE_SSL: "false",
    USE_TLS: "true",
    SUBJECT_PREFIX: "每日arXiv",
  },
  "🕐 时区格式配置": {
    TIMEZONE: "Asia/Shanghai",
    DATE_FORMAT: "%Y-%m-%d",
    TIME_FORMAT: "%H:%M:%S",
    ENABLE_MCP_TIME_SERVICE: "false",
    DEBUG_MODE: "false",
  },
  "📝 日志配置": {
    LOG_LEVEL: "INFO",
    LOG_FILE: "logs/arxiv_recommender.log",
    LOG_TO_CONSOLE: "true",
    LOG_MAX_SIZE: "10",
    LOG_BACKUP_COUNT: "5",
  },
};

// 推荐摘要文案（用于界面提示）
const recommendedSummary: Record<string, string> = {
  "🔑 API配置":
    "优先使用 DashScope；主模型 qwen-plus；轻量 qwen3-30b；Ollama 默认 http://localhost:11434/v1",
  "📚 ArXiv配置": "重试 3 次、延迟 5 秒；分类 cs.CV,cs.LG；每次最多 50 篇；详细 3、简要 7",
  "🤖 LLM配置": "并发工作线程 5",
  "📁 文件路径配置": "用户分类 data/users/user_categories.json；目录 arxiv_history；保存 Markdown",
  "📧 邮件配置": "默认不发送；端口 587；TLS 开启、SSL 关闭；标题前缀 每日arXiv",
  "🕐 时区格式配置": "Asia/Shanghai；日期 %Y-%m-%d；时间 %H:%M:%S；关闭 MCP 时间；关闭调试",
  "📝 日志配置": "INFO；logs/arxiv_recommender.log；开启控制台；滚动大小 10MB；保留 5 个",
};

const applyPreset = (section: string) => {
  const preset = recommendedPresets[section];
  if (!preset) return;
  Object.entries(preset).forEach(([k, v]) => {
    configChanges.value[k] = v;
  });
};

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

// 当前分组字段映射，用于分组重置
const sectionFields: Record<string, string[]> = {
  "🔑 API配置": [
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_BASE_URL",
    "QWEN_MODEL",
    "QWEN_MODEL_LIGHT",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL_LIGHT",
    "LIGHT_MODEL_PROVIDER",
    "OLLAMA_MODEL_LIGHT_TEMPERATURE",
    "OLLAMA_MODEL_LIGHT_TOP_P",
    "OLLAMA_MODEL_LIGHT_MAX_TOKENS",
  ],
  "📚 ArXiv配置": [
    "ARXIV_BASE_URL",
    "ARXIV_RETRIES",
    "ARXIV_DELAY",
    "ARXIV_CATEGORIES",
    "MAX_ENTRIES",
    "NUM_DETAILED_PAPERS",
    "NUM_BRIEF_PAPERS",
  ],
  "🤖 LLM配置": ["MAX_WORKERS"],
  "📁 文件路径配置": ["USER_CATEGORIES_FILE", "SAVE_DIRECTORY", "SAVE_MARKDOWN"],
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
    "DATE_FORMAT",
    "TIME_FORMAT",
    "ENABLE_MCP_TIME_SERVICE",
    "DEBUG_MODE",
  ],
  "📝 日志配置": ["LOG_LEVEL", "LOG_FILE", "LOG_TO_CONSOLE", "LOG_MAX_SIZE", "LOG_BACKUP_COUNT"],
};

const resetSectionChanges = () => {
  const fields = sectionFields[selectedSection.value] || [];
  fields.forEach((k) => {
    configChanges.value[k] = loadedConfig.value[k];
  });
};

onMounted(async () => {
  await loadConfig();
  window.addEventListener("beforeunload", handleBeforeUnload);
});

onBeforeUnmount(() => {
  window.removeEventListener("beforeunload", handleBeforeUnload);
});
</script>
