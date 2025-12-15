import { ref, computed } from "vue";
import * as api from "@/services/api";
import type { ConfigData } from "@/types";
import { useArxivStore } from "@/stores/arxiv";

export function useConfig(showMessage: (text: string, type: "success" | "error") => void) {
  const store = useArxivStore();
  const isLoading = ref(false);

  // Data State
  const loadedConfig = ref<ConfigData>({});
  const configChanges = ref<ConfigData>({});

  // Computed Properties
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
  
  const heavyProviderLabel = computed(() =>
    String(configChanges.value.HEAVY_MODEL_PROVIDER || "Unknown")
  );

  // Helpers
  const getSectionChanges = (sectionId: string) => {
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

  const resetSectionChanges = (sectionId: string) => {
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

    const keys = map[sectionId];
    if (!keys) return;

    keys.forEach((k) => {
      configChanges.value[k] = loadedConfig.value[k];
    });
  };

  return {
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
    resetSectionChanges,
    getSectionChanges,
  };
}
