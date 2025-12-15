<template>
  <div class="config-container">
    <!-- 顶部导航栏 -->
    <header class="config-header">
      <div class="header-title">
        <h1>⚙️ 环境配置</h1>
        <span class="header-subtitle">Environment Configuration</span>
      </div>
      <div class="header-actions">
        <button
          class="btn-secondary danger"
          @click="restoreDefault"
          :disabled="isLoading"
          title="恢复默认设置"
        >
          <span>📋 恢复默认</span>
        </button>
        <button
          class="btn-secondary"
          @click="loadConfig"
          :disabled="isLoading"
          title="重新加载配置"
        >
          <span class="icon">🔄</span>
        </button>
        <button
          class="btn-primary"
          @click="saveConfig"
          :disabled="isLoading || changedKeys.length === 0"
        >
          <span v-if="isLoading" class="spinner"></span>
          <span v-else>💾 保存更改</span>
        </button>
      </div>
    </header>

    <!-- 未保存更改横幅 -->
    <transition name="slide-down">
      <div v-if="changedKeys.length > 0" class="unsaved-banner">
        <div class="banner-content">
          <span class="icon">⚠️</span>
          <span
            >您有 <strong>{{ changedKeys.length }}</strong> 项未保存的更改</span
          >
        </div>
        <div class="banner-actions">
          <button class="btn-text" @click="toggleChanges">
            {{ showChanges ? "收起详情" : "查看详情" }}
          </button>
          <button class="btn-text" @click="resetAllChanges">放弃更改</button>
        </div>
      </div>
    </transition>

    <!-- 未保存详情面板 -->
    <transition name="fade">
      <div v-if="changedKeys.length > 0 && showChanges" class="changes-panel">
        <div class="changes-list">
          <div v-for="k in changedKeys" :key="k" class="change-item">
            <span class="change-key">{{ k }}</span>
            <div class="change-values">
              <span class="val-old">{{ truncate(loadedConfig[k] || "(空)") }}</span>
              <span class="arrow">→</span>
              <span class="val-new">{{ truncate(configChanges[k] || "(空)") }}</span>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 成功/错误提示 (替代 Element Plus Message) -->
    <transition name="fade">
      <div v-if="message.text" class="toast-message" :class="message.type">
        {{ message.text }}
      </div>
    </transition>

    <div class="config-layout">
      <!-- 左侧边栏导航 -->
      <aside class="config-sidebar">
        <nav class="nav-menu">
          <button
            v-for="s in sections"
            :key="s.id"
            class="nav-item"
            :class="{ active: selectedSection === s.id }"
            @click="selectedSection = s.id"
          >
            <span class="nav-icon">{{ s.icon }}</span>
            <span class="nav-label">{{ s.label }}</span>
            <span v-if="getSectionChanges(s.id) > 0" class="change-badge">
              {{ getSectionChanges(s.id) }}
            </span>
          </button>
        </nav>
      </aside>

      <!-- 右侧内容区域 -->
      <main class="config-content">
        <!-- Persistent Status Header -->
        <div class="status-header fade-in">
          <div class="stats-grid">
            <div class="stat-card" :class="{ active: hasDashscopeKey }">
              <div class="stat-icon">🔑</div>
              <div class="stat-info">
                <div class="stat-label">DashScope Key</div>
                <div class="stat-value">{{ hasDashscopeKey ? "已配置" : "未配置" }}</div>
              </div>
              <div class="stat-status" :class="hasDashscopeKey ? 'status-ok' : 'status-err'"></div>
            </div>

            <div class="stat-card" :class="{ active: emailEnabled }">
              <div class="stat-icon">📧</div>
              <div class="stat-info">
                <div class="stat-label">邮件推送</div>
                <div class="stat-value">{{ emailEnabled ? "已启用" : "已禁用" }}</div>
              </div>
              <div class="stat-status" :class="emailEnabled ? 'status-ok' : 'status-warn'"></div>
            </div>

            <div class="stat-card" :class="{ active: !debugEnabled }">
              <div class="stat-icon">🚀</div>
              <div class="stat-info">
                <div class="stat-label">运行模式</div>
                <div class="stat-value">{{ debugEnabled ? "调试模式" : "生产模式" }}</div>
              </div>
              <div class="stat-status" :class="debugEnabled ? 'status-warn' : 'status-ok'"></div>
            </div>

            <div
              class="stat-card"
              :class="{ active: heavyProviderLabel && heavyProviderLabel !== 'Unknown' }"
            >
              <div class="stat-icon">🧠</div>
              <div class="stat-info">
                <div class="stat-label">主模型</div>
                <div class="stat-value">{{ heavyProviderLabel }}</div>
              </div>
              <div
                class="stat-status"
                :class="
                  heavyProviderLabel && heavyProviderLabel !== 'Unknown'
                    ? 'status-ok'
                    : 'status-err'
                "
              ></div>
            </div>
          </div>
        </div>

        <!-- 具体的配置面板 -->
        <div class="content-panel fade-in">
          <div class="panel-header">
            <div class="header-row">
              <h2>{{ currentSectionLabel }}</h2>
              <button
                v-if="getSectionChanges(selectedSection) > 0"
                class="btn-text-small"
                @click="resetSectionChanges"
              >
                ↩️ 重置本页更改
              </button>
            </div>
          </div>

          <!-- 模型与API配置 -->
          <div v-if="selectedSection === 'model'" class="form-container">
            <div class="form-card">
              <h3 class="card-title">DashScope (通义千问) 设置</h3>
              <div class="form-group">
                <label>API Key <span class="required">*</span></label>
                <div class="input-wrapper">
                  <input
                    :type="showDashscopeKey ? 'text' : 'password'"
                    v-model="configChanges.DASHSCOPE_API_KEY"
                    placeholder="sk-..."
                  />
                  <button class="icon-btn" @click="showDashscopeKey = !showDashscopeKey">
                    {{ showDashscopeKey ? "👁️" : "🔒" }}
                  </button>
                </div>
                <p class="help-text">用于访问通义千问服务的密钥。</p>
              </div>
              <div class="form-group">
                <label>Base URL</label>
                <input
                  type="text"
                  v-model="configChanges.DASHSCOPE_BASE_URL"
                  placeholder="默认地址"
                />
              </div>
            </div>

            <div class="form-card">
              <h3 class="card-title">分类匹配模型 (Light Model)</h3>
              <div class="form-group">
                <label>模型提供方</label>
                <select v-model="configChanges.LIGHT_MODEL_PROVIDER">
                  <option value="dashscope">dashscope</option>
                </select>
              </div>
              <template v-if="configChanges.LIGHT_MODEL_PROVIDER === 'dashscope'">
                <div class="form-row">
                  <div class="form-group">
                    <label>模型名称</label>
                    <input type="text" v-model="configChanges.QWEN_MODEL_LIGHT" />
                  </div>
                  <div class="form-group">
                    <label>Max Tokens</label>
                    <input type="number" v-model="configChanges.QWEN_MODEL_LIGHT_MAX_TOKENS" />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Temperature (只读)</label>
                    <input
                      type="number"
                      v-model="configChanges.QWEN_MODEL_LIGHT_TEMPERATURE"
                      disabled
                      class="disabled-input"
                    />
                  </div>
                  <div class="form-group">
                    <label>Top P</label>
                    <input
                      type="number"
                      step="0.05"
                      v-model="configChanges.QWEN_MODEL_LIGHT_TOP_P"
                    />
                  </div>
                </div>
              </template>
            </div>

            <div class="form-card">
              <h3 class="card-title">深度分析模型 (Heavy Model)</h3>
              <div class="form-group">
                <label>模型提供方</label>
                <select v-model="configChanges.HEAVY_MODEL_PROVIDER">
                  <option value="dashscope">dashscope</option>
                </select>
              </div>
              <template v-if="configChanges.HEAVY_MODEL_PROVIDER === 'dashscope'">
                <div class="form-row">
                  <div class="form-group">
                    <label>模型名称</label>
                    <input type="text" v-model="configChanges.QWEN_MODEL" />
                  </div>
                  <div class="form-group">
                    <label>Max Tokens</label>
                    <input type="number" v-model="configChanges.QWEN_MODEL_MAX_TOKENS" />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Temperature</label>
                    <input
                      type="number"
                      step="0.1"
                      v-model="configChanges.QWEN_MODEL_TEMPERATURE"
                    />
                  </div>
                  <div class="form-group">
                    <label>Top P</label>
                    <input type="number" step="0.05" v-model="configChanges.QWEN_MODEL_TOP_P" />
                  </div>
                </div>
              </template>
            </div>

            <div class="form-card">
              <h3 class="card-title">并发设置</h3>
              <div class="form-group">
                <label>最大工作线程数 (MAX_WORKERS)</label>
                <input type="number" v-model="configChanges.MAX_WORKERS" />
              </div>
            </div>
          </div>

          <!-- ArXiv 配置 -->
          <div v-if="selectedSection === 'arxiv'" class="form-container">
            <div class="form-card">
              <h3 class="card-title">API 请求设置</h3>
              <div class="form-group">
                <label>Base URL (只读)</label>
                <input
                  type="text"
                  v-model="configChanges.ARXIV_BASE_URL"
                  disabled
                  class="disabled-input"
                />
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>重试次数</label>
                  <input type="number" v-model="configChanges.ARXIV_RETRIES" />
                </div>
                <div class="form-group">
                  <label>请求间隔 (秒)</label>
                  <input type="number" v-model="configChanges.ARXIV_DELAY" />
                </div>
              </div>
            </div>

            <div class="form-card">
              <h3 class="card-title">筛选与生成策略</h3>
              <div class="form-group">
                <label>单次最大拉取数 (MAX_ENTRIES)</label>
                <input type="number" v-model="configChanges.MAX_ENTRIES" />
                <p class="help-text">每次从 ArXiv 获取的论文最大数量，建议不要超过 100。</p>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>详细解读数量</label>
                  <input type="number" v-model="configChanges.NUM_DETAILED_PAPERS" />
                </div>
                <div class="form-group">
                  <label>简要推荐数量</label>
                  <input type="number" v-model="configChanges.NUM_BRIEF_PAPERS" />
                </div>
              </div>
              <div class="form-group">
                <label>相关性阈值 (0-10)</label>
                <div class="range-wrapper">
                  <input
                    type="range"
                    min="0"
                    max="10"
                    step="1"
                    v-model="configChanges.RELEVANCE_FILTER_THRESHOLD"
                  />
                  <span class="range-value">{{ configChanges.RELEVANCE_FILTER_THRESHOLD }}</span>
                </div>
                <p class="help-text">低于此分数的论文将被自动过滤。推荐值: 6</p>
              </div>
            </div>
          </div>

          <!-- 文件路径 -->
          <div v-if="selectedSection === 'files'" class="form-container">
            <div class="form-card">
              <h3 class="card-title">输出设置</h3>
              <div class="form-group checkbox-group">
                <label class="switch">
                  <input
                    type="checkbox"
                    v-model="configChanges.SAVE_MARKDOWN"
                    true-value="true"
                    false-value="false"
                  />
                  <span class="slider round"></span>
                </label>
                <span class="label-text">保存 Markdown 文件</span>
              </div>
              <p class="help-text">除了生成 HTML 报告外，是否同时保存 Markdown 格式的源文件。</p>
            </div>
          </div>

          <!-- 邮件配置 -->
          <div v-if="selectedSection === 'email'" class="form-container">
            <div class="form-card">
              <h3 class="card-title">发送开关</h3>
              <div class="form-group checkbox-group">
                <label class="switch">
                  <input
                    type="checkbox"
                    v-model="configChanges.SEND_EMAIL"
                    true-value="true"
                    false-value="false"
                  />
                  <span class="slider round"></span>
                </label>
                <span class="label-text">启用邮件发送</span>
              </div>
            </div>

            <transition name="slide-fade">
              <div v-if="emailEnabled" class="email-settings">
                <div class="form-card">
                  <h3 class="card-title">发件人设置</h3>
                  <div class="form-row">
                    <div class="form-group">
                      <label>SMTP 服务器</label>
                      <input
                        type="text"
                        v-model="configChanges.SMTP_SERVER"
                        placeholder="smtp.example.com"
                      />
                    </div>
                    <div class="form-group">
                      <label>端口</label>
                      <input type="number" v-model="configChanges.SMTP_PORT" placeholder="465" />
                    </div>
                  </div>
                  <div class="form-group">
                    <label>发件人邮箱</label>
                    <input type="email" v-model="configChanges.SENDER_EMAIL" />
                  </div>
                  <div class="form-group">
                    <label>邮箱密码/授权码</label>
                    <div class="input-wrapper">
                      <input
                        :type="showEmailPassword ? 'text' : 'password'"
                        v-model="configChanges.EMAIL_PASSWORD"
                      />
                      <button class="icon-btn" @click="showEmailPassword = !showEmailPassword">
                        {{ showEmailPassword ? "👁️" : "🔒" }}
                      </button>
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-group checkbox-group">
                      <label class="checkbox-label">
                        <input
                          type="checkbox"
                          v-model="configChanges.USE_SSL"
                          true-value="true"
                          false-value="false"
                        />
                        SSL
                      </label>
                    </div>
                    <div class="form-group checkbox-group">
                      <label class="checkbox-label">
                        <input
                          type="checkbox"
                          v-model="configChanges.USE_TLS"
                          true-value="true"
                          false-value="false"
                        />
                        TLS
                      </label>
                    </div>
                  </div>
                </div>

                <div class="form-card">
                  <h3 class="card-title">收件人设置</h3>
                  <div class="form-group">
                    <label>收件人列表 (逗号分隔)</label>
                    <input type="text" v-model="configChanges.RECEIVER_EMAIL" />
                  </div>
                </div>
              </div>
            </transition>
          </div>

          <!-- 提示词配置 -->
          <div v-if="selectedSection === 'prompts'" class="form-container">
            <div class="form-card">
              <h3 class="card-title">提示词模板管理</h3>
              <div class="actions-row">
                <button class="btn-outlined" @click="resetAllPrompts" :disabled="promptsLoading">
                  🔄 重置所有提示词
                </button>
              </div>
            </div>

            <div v-if="promptsLoading" class="loading-state">
              <span class="spinner"></span> 正在加载提示词...
            </div>

            <div v-else class="prompts-list">
              <div v-for="prompt in prompts" :key="prompt.id" class="prompt-card">
                <div class="prompt-header">
                  <div class="prompt-title">
                    <h3>{{ prompt.name }}</h3>
                    <span class="prompt-id">{{ prompt.id }}</span>
                  </div>
                  <div class="prompt-actions">
                    <button class="btn-text" @click="resetPrompt(prompt.id)">重置默认</button>
                    <button
                      class="btn-primary-small"
                      @click="savePrompt(prompt.id)"
                      :disabled="!hasPromptChanged(prompt.id)"
                    >
                      保存
                    </button>
                  </div>
                </div>

                <div class="prompt-body">
                  <div class="prompt-vars">
                    <span class="label-text">可用变量:</span>
                    <span v-for="v in prompt.variables" :key="v" class="tag">{_{ v }_}</span>
                  </div>

                  <textarea
                    v-if="edits[prompt.id]"
                    class="code-editor"
                    v-model="edits[prompt.id]!.template"
                    rows="8"
                    placeholder="输入提示词模板..."
                  ></textarea>

                  <div v-if="promptErrors[prompt.id]" class="error-msg">
                    {{ promptErrors[prompt.id] }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { useArxivStore } from "@/stores/arxiv";
import * as api from "@/services/api";
import type { ConfigData, PromptItem } from "@/types";

const store = useArxivStore();

// UI State
const isLoading = ref(false);
const promptsLoading = ref(false);
const showDashscopeKey = ref(false);
const showEmailPassword = ref(false);
const showChanges = ref(false);
const selectedSection = ref("model");

// Data State
const loadedConfig = ref<ConfigData>({});
const configChanges = ref<ConfigData>({});
const prompts = ref<PromptItem[]>([]);
const edits = ref<Record<string, { name: string; template: string }>>({});
const promptErrors = ref<Record<string, string>>({});

// Toast State
const message = ref({ text: "", type: "success" });
const showMessage = (text: string, type: "success" | "error" = "success") => {
  message.value = { text, type };
  setTimeout(() => {
    message.value.text = "";
  }, 3000);
};

// Sections definition
const sections = [
  { id: "model", label: "模型与API", icon: "🤖" },
  { id: "arxiv", label: "ArXiv设置", icon: "🎓" },
  { id: "files", label: "文件输出", icon: "📂" },
  { id: "email", label: "邮件通知", icon: "📧" },
  { id: "prompts", label: "提示词模板", icon: "📝" },
];

// Computed
const changedKeys = computed(() => {
  const keys: string[] = [];
  for (const k in configChanges.value) {
    if (configChanges.value[k] !== loadedConfig.value[k]) {
      keys.push(k);
    }
  }
  return keys;
});

const hasDashscopeKey = computed(() => !!configChanges.value.DASHSCOPE_API_KEY);
const emailEnabled = computed(
  () => configChanges.value.SEND_EMAIL === "true" || configChanges.value.SEND_EMAIL === true
);
const debugEnabled = computed(
  () => configChanges.value.DEBUG_MODE === "true" || configChanges.value.DEBUG_MODE === true
);
const heavyProviderLabel = computed(() => configChanges.value.HEAVY_MODEL_PROVIDER || "Unknown");

const currentSectionLabel = computed(() => {
  const s = sections.find((x) => x.id === selectedSection.value);
  return s ? s.label : "配置";
});

// Helpers
const truncate = (val: unknown) => {
  const s = String(val);
  return s.length > 20 ? s.substring(0, 20) + "..." : s;
};

const getSectionChanges = (sectionId: string) => {
  // Define keys for each section
  const map: Record<string, string[]> = {
    model: [
      "DASHSCOPE_API_KEY",
      "DASHSCOPE_BASE_URL",
      "LIGHT_MODEL_PROVIDER",
      "QWEN_MODEL_LIGHT",
      "QWEN_MODEL_LIGHT_MAX_TOKENS",
      "QWEN_MODEL_LIGHT_TEMPERATURE",
      "QWEN_MODEL_LIGHT_TOP_P",
      "HEAVY_MODEL_PROVIDER",
      "QWEN_MODEL",
      "QWEN_MODEL_MAX_TOKENS",
      "QWEN_MODEL_TEMPERATURE",
      "QWEN_MODEL_TOP_P",
      "MAX_WORKERS",
    ],
    arxiv: [
      "ARXIV_BASE_URL",
      "ARXIV_RETRIES",
      "ARXIV_DELAY",
      "MAX_ENTRIES",
      "NUM_DETAILED_PAPERS",
      "NUM_BRIEF_PAPERS",
      "RELEVANCE_FILTER_THRESHOLD",
    ],
    files: ["SAVE_MARKDOWN"],
    email: [
      "SEND_EMAIL",
      "SMTP_SERVER",
      "SMTP_PORT",
      "SENDER_EMAIL",
      "EMAIL_PASSWORD",
      "USE_SSL",
      "USE_TLS",
      "RECEIVER_EMAIL",
    ],
  };

  if (!map[sectionId]) return 0;
  return map[sectionId].filter((k) => changedKeys.value.includes(k)).length;
};

const hasPromptChanged = (id: string) => {
  const original = prompts.value.find((p) => p.id === id);
  if (!original) return false;
  return edits.value[id]?.template !== original.template;
};

// Actions
const loadConfig = async () => {
  isLoading.value = true;
  store.clearError();
  try {
    const res = await api.getEnvConfig();
    if (res.success && res.data) {
      loadedConfig.value = JSON.parse(JSON.stringify(res.data));
      configChanges.value = JSON.parse(JSON.stringify(res.data));
    } else {
      store.setError("加载配置失败");
    }
  } catch {
    store.setError("加载配置发生错误");
  } finally {
    isLoading.value = false;
  }
};

const saveConfig = async () => {
  if (changedKeys.value.length === 0) return;

  isLoading.value = true;
  store.clearError();
  try {
    const res = await api.saveEnvConfig({ config: configChanges.value });
    if (res.success) {
      loadedConfig.value = JSON.parse(JSON.stringify(configChanges.value));
      showMessage("配置已保存", "success");
    } else {
      store.setError(res.message || "保存配置失败");
    }
  } catch {
    store.setError("保存配置发生错误");
  } finally {
    isLoading.value = false;
  }
};

const restoreDefault = async () => {
  if (!confirm("确定要恢复默认配置吗？这将覆盖当前的所有设置。")) return;

  isLoading.value = true;
  store.clearError();
  try {
    const res = await api.restoreDefaultEnvConfig();
    if (res.success && res.data) {
      loadedConfig.value = JSON.parse(JSON.stringify(res.data));
      configChanges.value = JSON.parse(JSON.stringify(res.data));
      showMessage("已恢复默认配置", "success");
    } else {
      store.setError("恢复默认配置失败");
    }
  } catch {
    store.setError("恢复默认配置错误");
  } finally {
    isLoading.value = false;
  }
};

const resetAllChanges = () => {
  if (!confirm("确定要放弃所有未保存的更改吗？")) return;
  configChanges.value = JSON.parse(JSON.stringify(loadedConfig.value));
};

const toggleChanges = () => {
  showChanges.value = !showChanges.value;
};

const resetSectionChanges = () => {
  const map: Record<string, string[]> = {
    model: [
      "DASHSCOPE_API_KEY",
      "DASHSCOPE_BASE_URL",
      "LIGHT_MODEL_PROVIDER",
      "QWEN_MODEL_LIGHT",
      "QWEN_MODEL_LIGHT_MAX_TOKENS",
      "QWEN_MODEL_LIGHT_TEMPERATURE",
      "QWEN_MODEL_LIGHT_TOP_P",
      "HEAVY_MODEL_PROVIDER",
      "QWEN_MODEL",
      "QWEN_MODEL_MAX_TOKENS",
      "QWEN_MODEL_TEMPERATURE",
      "QWEN_MODEL_TOP_P",
      "MAX_WORKERS",
    ],
    arxiv: [
      "ARXIV_BASE_URL",
      "ARXIV_RETRIES",
      "ARXIV_DELAY",
      "MAX_ENTRIES",
      "NUM_DETAILED_PAPERS",
      "NUM_BRIEF_PAPERS",
      "RELEVANCE_FILTER_THRESHOLD",
    ],
    files: ["SAVE_MARKDOWN"],
    email: [
      "SEND_EMAIL",
      "SMTP_SERVER",
      "SMTP_PORT",
      "SENDER_EMAIL",
      "EMAIL_PASSWORD",
      "USE_SSL",
      "USE_TLS",
      "RECEIVER_EMAIL",
    ],
  };

  const keys = map[selectedSection.value];
  if (!keys) return;

  keys.forEach((k) => {
    configChanges.value[k] = loadedConfig.value[k];
  });
};

const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (changedKeys.value.length > 0) {
    e.preventDefault();
    e.returnValue = "";
  }
};

// Prompts Logic
const loadPrompts = async () => {
  promptsLoading.value = true;
  try {
    const res = await api.listPrompts();
    if (res.success && res.data) {
      prompts.value = res.data;
      // Initialize edits
      const editMap: Record<string, { name: string; template: string }> = {};
      prompts.value.forEach((p) => {
        editMap[p.id] = { name: p.name, template: p.template };
      });
      edits.value = editMap;
    }
  } catch (err) {
    console.error(err);
  } finally {
    promptsLoading.value = false;
  }
};

const extractPlaceholders = (tpl: string): string[] => {
  const regex = /\{(.+?)\}/g;
  const matches = new Set<string>();
  let match;
  while ((match = regex.exec(tpl)) !== null) {
    if (match && match[1]) {
      matches.add(match[1].trim());
    }
  }
  return Array.from(matches);
};

const validateTemplateBeforeSave = (
  id: string
): { valid: boolean; unknown: string[]; allowed: string[] } => {
  const idx = prompts.value.findIndex((x) => x.id === id);
  const prompt = idx >= 0 ? prompts.value[idx] : undefined;
  const allowed = prompt && Array.isArray(prompt.variables) ? (prompt.variables as string[]) : [];
  const tpl = edits.value[id]?.template || "";
  const used = extractPlaceholders(tpl);
  const unknown = used.filter((x) => !allowed.includes(x));
  return { valid: unknown.length === 0, unknown, allowed };
};

const savePrompt = async (id: string) => {
  promptsLoading.value = true;
  store.clearError();
  try {
    const check = validateTemplateBeforeSave(id);
    if (!check.valid) {
      const unknownText = check.unknown.map((n) => `{${n}}`).join(", ");
      const allowedText = (check.allowed || []).join(", ") || "（无）";
      const msg = `模板占位符不匹配：${unknownText}；允许的变量：{${allowedText}}`;
      promptErrors.value[id] = msg;
      store.setError(msg);
      return;
    }
    const payload = edits.value[id];
    if (!payload) return;
    const res = await api.updatePrompt(id, payload);
    if (res.success && res.data) {
      const idx = prompts.value.findIndex((x) => x.id === id);
      if (idx >= 0)
        prompts.value[idx] = {
          ...(prompts.value[idx] || {}),
          ...(res.data as PromptItem),
        } as PromptItem;
      if (promptErrors.value[id]) delete promptErrors.value[id];
      showMessage("提示词已保存", "success");
    } else {
      store.setError(res.message || "保存提示词失败");
    }
  } catch {
    store.setError("保存提示词错误");
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
      if (idx >= 0) prompts.value[idx] = updated;
      edits.value[id] = { name: updated.name, template: updated.template };
      if (promptErrors.value[id]) delete promptErrors.value[id];
      showMessage("已重置该提示词", "success");
    } else {
      store.setError(res.message || "重置提示词失败");
    }
  } catch {
    store.setError("重置提示词错误");
  } finally {
    promptsLoading.value = false;
  }
};

const resetAllPrompts = async () => {
  if (!confirm("确定要重置所有提示词吗？")) return;
  promptsLoading.value = true;
  store.clearError();
  try {
    const res = await api.resetAllPrompts();
    if (res.success) {
      await loadPrompts();
      showMessage("所有提示词已重置", "success");
    } else store.setError(res.message || "重置所有提示词失败");
  } catch {
    store.setError("重置所有提示词错误");
  } finally {
    promptsLoading.value = false;
  }
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
.config-container {
  /* Design Tokens - Refined Palette */
  --primary: #6366f1; /* Indigo 500 */
  --primary-hover: #4f46e5; /* Indigo 600 */
  --primary-light: #e0e7ff; /* Indigo 100 */
  --primary-fade: rgba(99, 102, 241, 0.1);

  --bg-color: #f8fafc; /* Slate 50 */
  --surface-color: #ffffff;

  --text-main: #1e293b; /* Slate 800 */
  --text-secondary: #475569; /* Slate 600 */
  --text-muted: #94a3b8; /* Slate 400 */

  --border-color: #e2e8f0; /* Slate 200 */
  --border-focus: #6366f1;

  --danger: #ef4444;
  --danger-bg: #fee2e2;
  --success: #10b981;
  --warning: #f59e0b;

  --shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;

  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-main);
  overflow: hidden;
  font-family: "Inter", system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Header */
.config-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
  z-index: 10;
  backdrop-filter: blur(8px);
  background-color: rgba(255, 255, 255, 0.95);
}

.header-title h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 12px;
  letter-spacing: -0.025em;
}

.header-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  font-weight: 500;
  margin-left: 4px;
  letter-spacing: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* Layout */
.config-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebar */
.config-sidebar {
  width: 280px;
  background: var(--surface-color);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex-shrink: 0;
  padding: 24px 16px;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.95rem;
  font-weight: 500;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: left;
  position: relative;
  overflow: hidden;
}

.nav-item:hover {
  background-color: var(--bg-color);
  color: var(--text-main);
  transform: translateX(4px);
}

.nav-item.active {
  background-color: var(--primary-light);
  color: var(--primary);
  font-weight: 600;
}

.nav-item.active::before {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  height: 20px;
  width: 3px;
  background-color: var(--primary);
  border-radius: 0 4px 4px 0;
}

.nav-icon {
  margin-right: 12px;
  font-size: 1.25em;
  width: 24px;
  text-align: center;
  line-height: 1;
}

.nav-label {
  flex: 1;
}

.change-badge {
  background: var(--danger);
  color: white;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 700;
  min-width: 20px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
}

.sidebar-footer {
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

/* Content Area */
.config-content {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
  scroll-behavior: smooth;
  background-color: var(--bg-color);
}

.content-panel {
  max-width: 960px;
  margin: 0 auto;
  padding-bottom: 60px;
}

.panel-header {
  margin-bottom: 32px;
}

.panel-header h2 {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 8px 0;
  letter-spacing: -0.025em;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Cards & Forms */
.form-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.form-card {
  background: var(--surface-color);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  padding: 32px;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.form-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--primary-light);
  transform: translateY(-2px);
}

.card-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
  margin: 0 0 24px 0;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-row {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.form-row .form-group {
  flex: 1;
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.required {
  color: var(--danger);
  margin-left: 4px;
}

input[type="text"],
input[type="number"],
input[type="email"],
input[type="password"],
select,
textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  color: var(--text-main);
  background-color: #fff;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--primary-light);
}

input:hover,
select:hover,
textarea:hover {
  border-color: #cbd5e1;
}

input:disabled,
select:disabled,
textarea:disabled {
  background-color: var(--bg-color);
  color: var(--text-muted);
  cursor: not-allowed;
  border-color: var(--border-color);
  box-shadow: none;
}

.input-wrapper {
  position: relative;
  display: flex;
}

.input-wrapper input {
  padding-right: 48px;
}

.icon-btn {
  position: absolute;
  right: 6px;
  top: 6px;
  bottom: 6px;
  width: 36px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  opacity: 0.6;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.icon-btn:hover {
  opacity: 1;
  background-color: var(--bg-color);
}

.help-text {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 8px;
  line-height: 1.5;
}

/* Switch & Checkbox */
.checkbox-group {
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 42px;
  padding: 4px 0;
}

.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 28px;
  flex-shrink: 0;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #cbd5e1;
  transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 34px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

input:checked + .slider {
  background-color: var(--primary);
}

input:focus + .slider {
  box-shadow: 0 0 0 4px var(--primary-light);
}

input:checked + .slider:before {
  transform: translateX(22px);
}

.label-text {
  font-weight: 600;
  color: var(--text-main);
  cursor: pointer;
  font-size: 0.95rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  transition: background-color 0.2s;
}

.checkbox-label:hover {
  background-color: var(--bg-color);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--primary);
  margin: 0;
}

/* Range Slider */
.range-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

input[type="range"] {
  flex: 1;
  height: 6px;
  background: #e2e8f0;
  border-radius: 4px;
  appearance: none;
  cursor: pointer;
  padding: 0;
  border: none;
  box-shadow: none;
}

input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  background: var(--surface-color);
  border: 2px solid var(--primary);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: -7px; /* Align thumb with track */
}

input[type="range"]::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 4px;
  background: #e2e8f0;
}

input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 0 0 4px var(--primary-light);
}

.range-value {
  font-weight: 700;
  color: var(--primary);
  min-width: 32px;
  text-align: center;
  background: var(--primary-light);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.9rem;
}

/* Stats Grid */
.status-header {
  max-width: 960px;
  margin: 0 auto 40px auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--surface-color);
  padding: 24px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-light);
}

.stat-icon {
  font-size: 2rem;
  background: linear-gradient(135deg, var(--bg-color), #fff);
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--border-color);
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-main);
}

.stat-status {
  position: absolute;
  top: 0;
  right: 0;
  width: 4px;
  height: 100%;
  background: var(--border-color);
  opacity: 0.5;
}

.stat-status.status-ok {
  background: var(--success);
  opacity: 1;
}
.stat-status.status-err {
  background: var(--danger);
  opacity: 1;
}
.stat-status.status-warn {
  background: var(--warning);
  opacity: 1;
}

.stat-card.active .stat-value {
  color: var(--primary);
}

/* Buttons */
button {
  font-family: inherit;
  outline: none;
}

.btn-primary {
  background: linear-gradient(135deg, var(--primary), var(--primary-hover));
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 4px rgba(79, 70, 229, 0.3);
  transition: all 0.2s;
  font-size: 0.95rem;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(79, 70, 229, 0.4);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.7;
}

.btn-secondary {
  background-color: white;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  padding: 9px 16px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--bg-color);
  border-color: #cbd5e1;
  color: var(--text-main);
}

.btn-secondary.danger {
  color: var(--danger);
  border-color: #fecaca;
  background-color: #fff;
}

.btn-secondary.danger:hover:not(:disabled) {
  background-color: var(--danger-bg);
  border-color: var(--danger);
  color: #b91c1c;
}

.btn-outlined {
  background-color: transparent;
  color: var(--primary);
  border: 1px solid var(--primary);
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
}

.btn-outlined:hover {
  background-color: var(--primary-light);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

.btn-text {
  background: none;
  border: none;
  color: var(--primary);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  transition: background-color 0.2s;
}

.btn-text:hover {
  background-color: var(--primary-light);
}

.btn-text-danger {
  background: none;
  border: none;
  color: var(--danger);
  cursor: pointer;
  font-size: 0.9rem;
  width: 100%;
  text-align: left;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  transition: background-color 0.2s;
  font-weight: 500;
}

.btn-text-danger:hover {
  background-color: var(--danger-bg);
}

.btn-primary-small {
  padding: 6px 14px;
  font-size: 0.85rem;
  background-color: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.2s;
  font-weight: 600;
}

.btn-primary-small:hover:not(:disabled) {
  background-color: var(--primary-hover);
}

.btn-primary-small:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-text-small {
  background: none;
  border: none;
  color: var(--primary);
  cursor: pointer;
  font-size: 0.85rem;
  padding: 6px 10px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.2s;
  font-weight: 600;
}

.btn-text-small:hover {
  background-color: var(--primary-light);
}

.email-settings {
  display: flex;
  flex-direction: column;
  gap: 32px;
  margin-top: 32px;
}

/* Banner */
.unsaved-banner {
  background-color: #fffbeb;
  border-bottom: 1px solid #fcd34d;
  padding: 16px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 6px -1px rgba(245, 158, 11, 0.1);
  z-index: 5;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #92400e;
  font-size: 0.95rem;
  font-weight: 500;
}

.banner-actions {
  display: flex;
  gap: 12px;
}

.changes-panel {
  background: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
  padding: 24px 32px;
  max-height: 300px;
  overflow-y: auto;
  box-shadow: inset 0 -4px 6px -4px rgba(0, 0, 0, 0.05);
}

.change-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}

.change-item:last-child {
  border-bottom: none;
}

.change-key {
  font-family: "Fira Code", "Menlo", monospace;
  font-size: 0.85rem;
  font-weight: 600;
  width: 260px;
  color: var(--text-secondary);
}

.change-values {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 20px;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.val-old {
  color: var(--danger);
  text-decoration: line-through;
  background: var(--danger-bg);
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
}

.val-new {
  color: var(--success);
  font-weight: 600;
  background: #ecfdf5;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
}

/* Prompts */
.prompts-list {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.prompt-card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.prompt-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--primary-light);
}

.prompt-header {
  padding: 20px 24px;
  background: #f8fafc;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prompt-title h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 12px;
}

.prompt-id {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-family: monospace;
  background: #e2e8f0;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
}

.prompt-body {
  padding: 24px;
}

.prompt-vars {
  margin-bottom: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.tag {
  background: var(--primary-light);
  color: var(--primary);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-family: monospace;
  font-weight: 600;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.code-editor {
  width: 100%;
  padding: 20px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-family: "Fira Code", "Menlo", "Monaco", monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  background-color: #fafafa;
  color: var(--text-main);
  transition: all 0.2s;
}

.code-editor:focus {
  background-color: #fff;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px var(--primary-light);
}

.error-msg {
  margin-top: 12px;
  color: var(--danger);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--danger-bg);
  border-radius: 6px;
  font-weight: 500;
}

/* Toast */
.toast-message {
  position: fixed;
  top: 32px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 50px;
  color: white;
  font-weight: 600;
  z-index: 2000;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  gap: 10px;
  backdrop-filter: blur(4px);
}

.toast-message.success {
  background-color: rgba(16, 185, 129, 0.95);
}

.toast-message.error {
  background-color: rgba(239, 68, 68, 0.95);
}

/* Animations */
.fade-in {
  animation: fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-fade-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-15px);
  opacity: 0;
}

/* Spinner */
.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px;
  color: var(--text-muted);
  font-weight: 500;
}

.loading-state .spinner {
  border-color: #e2e8f0;
  border-top-color: var(--primary);
  width: 28px;
  height: 28px;
  border-width: 3px;
}

/* Scrollbar Customization */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
  border: 2px solid transparent;
  background-clip: content-box;
}

::-webkit-scrollbar-thumb:hover {
  background-color: #94a3b8;
}
</style>
