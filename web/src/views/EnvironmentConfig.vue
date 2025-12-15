<template>
  <div class="config-container">
    <!-- 顶部导航栏 -->
    <ConfigHeader
      :isLoading="isLoading"
      :hasChanges="changedKeys.length > 0"
      @restore="restoreDefault"
      @load="loadConfig"
      @save="saveConfig"
    />

    <!-- 未保存更改提示 -->
    <ConfigUnsavedChanges
      :changedKeys="changedKeys"
      :loadedConfig="loadedConfig"
      :configChanges="configChanges"
      @reset="resetAllChanges"
    />

    <!-- 全局消息提示 -->
    <ConfigToast :message="message" />

    <div class="config-layout">
      <!-- 左侧边栏导航 -->
      <ConfigSidebar
        :sections="sections"
        :selectedSection="selectedSection"
        :getSectionChanges="getSectionChanges"
        @select="(id) => (selectedSection = id)"
      />

      <!-- 右侧内容区域 -->
      <main class="config-content">
        <!-- Status Header -->
        <ConfigStatusHeader
          :hasDashscopeKey="hasDashscopeKey"
          :emailEnabled="emailEnabled"
          :debugEnabled="debugEnabled"
          :heavyProviderLabel="heavyProviderLabel"
        />

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
                重置本页更改
              </button>
            </div>
          </div>

          <!-- 动态异步组件渲染 -->
          <KeepAlive>
            <component
              v-if="currentSection"
              :is="currentSection.component"
              v-bind="currentSectionProps"
              :key="currentSection.id"
            />
          </KeepAlive>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, defineAsyncComponent } from "vue";
import { useToast } from "@/composables/useToast";
import { useConfig } from "@/composables/useConfig";
import { usePrompts } from "@/composables/usePrompts";

// Import Shared Components
import ConfigHeader from "@/components/config/ConfigHeader.vue";
import ConfigSidebar from "@/components/config/ConfigSidebar.vue";
import ConfigStatusHeader from "@/components/config/ConfigStatusHeader.vue";
import ConfigUnsavedChanges from "@/components/config/ConfigUnsavedChanges.vue";
import ConfigToast from "@/components/config/ConfigToast.vue";

// Async Import Section Components
const ConfigModelSection = defineAsyncComponent(
  () => import("@/components/config/ConfigModelSection.vue")
);
const ConfigArxivSection = defineAsyncComponent(
  () => import("@/components/config/ConfigArxivSection.vue")
);
const ConfigFilesSection = defineAsyncComponent(
  () => import("@/components/config/ConfigFilesSection.vue")
);
const ConfigEmailSection = defineAsyncComponent(
  () => import("@/components/config/ConfigEmailSection.vue")
);
const ConfigPromptsSection = defineAsyncComponent(
  () => import("@/components/config/ConfigPromptsSection.vue")
);

// Composables
const { message, showMessage } = useToast();

const {
  isLoading,
  loadedConfig,
  configChanges,
  changedKeys,
  hasDashscopeKey,
  emailEnabled,
  debugEnabled,
  heavyProviderLabel,
  loadConfig,
  saveConfig,
  restoreDefault,
  resetAllChanges,
  resetSectionChanges: resetSectionChangesAction,
  getSectionChanges,
} = useConfig(showMessage);

const {
  promptsLoading,
  prompts,
  edits,
  promptErrors,
  loadPrompts,
  savePrompt,
  resetPrompt,
  resetAllPrompts,
} = usePrompts(showMessage);

// UI State
const selectedSection = ref("model");

// Sections definition with Component mapping
const sections = [
  { id: "model", label: "模型与API", icon: "🤖", component: ConfigModelSection },
  { id: "arxiv", label: "ArXiv设置", icon: "🎓", component: ConfigArxivSection },
  { id: "files", label: "文件输出", icon: "📂", component: ConfigFilesSection },
  { id: "email", label: "邮件通知", icon: "📧", component: ConfigEmailSection },
  { id: "prompts", label: "提示词模板", icon: "📝", component: ConfigPromptsSection },
];

// Computed
const currentSection = computed(() => {
  return sections.find((x) => x.id === selectedSection.value) || sections[0];
});

const currentSectionLabel = computed(() => currentSection.value?.label || "配置");

// Dynamic Props Mapping
const currentSectionProps = computed(() => {
  const commonProps = {
    config: configChanges.value,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    "onUpdate:config": (val: any) => Object.assign(configChanges.value, val),
  };

  switch (selectedSection.value) {
    case "email":
      return { ...commonProps, emailEnabled: emailEnabled.value };
    case "prompts":
      return {
        prompts: prompts.value,
        edits: edits.value,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        "onUpdate:edits": (val: any) => (edits.value = val),
        promptErrors: promptErrors.value,
        loading: promptsLoading.value,
        onResetAll: resetAllPrompts,
        onReset: resetPrompt,
        onSave: savePrompt,
      };
    default:
      return commonProps;
  }
});

// Helpers
const resetSectionChanges = () => {
  resetSectionChangesAction(selectedSection.value);
};

const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (changedKeys.value.length > 0) {
    e.preventDefault();
    e.returnValue = "";
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

<style>
/* Global styles for config components */
@import "../components/config/ConfigShared.css";
</style>

<style scoped>
.config-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-main);
  overflow: hidden;
  font-family: "Inter", system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Layout */
.config-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
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

/* Animations */
.fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
