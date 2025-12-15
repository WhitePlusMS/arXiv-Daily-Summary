<template>
  <div class="ui-form-container">
    <div class="ui-card">
      <h3 class="ui-card-title">提示词模板管理</h3>
      <div class="actions-row">
        <button class="ui-button ui-button-outlined" @click="$emit('resetAll')" :disabled="loading">
          重置所有提示词
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state"><span class="spinner"></span> 正在加载提示词...</div>

    <div v-else class="prompts-list">
      <div v-for="prompt in prompts" :key="prompt.id" class="prompt-card">
        <div class="prompt-header">
          <div class="prompt-title">
            <h3>{{ prompt.name }}</h3>
            <span class="prompt-id">{{ prompt.id }}</span>
          </div>
          <div class="prompt-actions">
            <button class="ui-button ui-button-text" @click="$emit('reset', prompt.id)">
              重置默认
            </button>
            <button
              class="ui-button ui-button-primary ui-button-small"
              @click="$emit('save', prompt.id)"
              :disabled="!hasPromptChanged(prompt.id)"
            >
              保存
            </button>
          </div>
        </div>

        <div class="prompt-body">
          <div class="prompt-vars">
            <span class="label-text">可用变量:</span>
            <span v-for="v in prompt.variables" :key="v" class="tag">{{ v }}</span>
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
</template>

<script setup lang="ts">
import type { PromptItem } from "@/types";

const props = defineProps<{
  prompts: PromptItem[];
  promptErrors: Record<string, string>;
  loading: boolean;
}>();

// Edits model
const edits = defineModel<Record<string, { name: string; template: string }>>("edits", {
  required: true,
});

defineEmits<{
  (e: "resetAll"): void;
  (e: "reset", id: string): void;
  (e: "save", id: string): void;
}>();

const hasPromptChanged = (id: string) => {
  const original = props.prompts.find((p) => p.id === id);
  if (!original) return false;
  return edits.value[id]?.template !== original.template;
};
</script>

<style scoped>
/* Prompts */
.prompts-list {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.prompt-card {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--ui-radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.prompt-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary-border);
}

.prompt-header {
  padding: 20px 24px;
  background: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prompt-title h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: 12px;
}

.prompt-id {
  font-size: 0.75rem;
  color: var(--color-text-soft);
  font-family: monospace;
  background: var(--color-background-mute);
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
  background: var(--color-primary-bg);
  color: var(--color-primary);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-family: monospace;
  font-weight: 600;
  border: 1px solid var(--color-primary-border);
}

.code-editor {
  width: 100%;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--ui-radius);
  font-family: "Fira Code", "Menlo", "Monaco", monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  background-color: var(--color-background-soft);
  color: var(--color-text);
  transition: all 0.2s;
}

.code-editor:focus {
  background-color: var(--color-background);
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-bg);
}

.error-msg {
  margin-top: 12px;
  color: var(--color-error);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-error-bg);
  border-radius: 6px;
  font-weight: 500;
}
</style>
