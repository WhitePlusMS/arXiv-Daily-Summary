import { ref } from "vue";
import * as api from "@/services/api";
import type { PromptItem } from "@/types";
import { useArxivStore } from "@/stores/arxiv";

export function usePrompts(showMessage: (text: string, type: "success" | "error") => void) {
  const store = useArxivStore();
  const promptsLoading = ref(false);
  const prompts = ref<PromptItem[]>([]);
  const edits = ref<Record<string, { name: string; template: string }>>({});
  const promptErrors = ref<Record<string, string>>({});

  // Logic
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

  // Actions
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

  return {
    promptsLoading,
    prompts,
    edits,
    promptErrors,
    loadPrompts,
    savePrompt,
    resetPrompt,
    resetAllPrompts,
  };
}
