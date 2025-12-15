<template>
  <header class="config-header">
    <div class="header-title">
      <h1>⚙️ 环境配置</h1>
      <span class="header-subtitle">Environment Configuration</span>
    </div>
    <div class="header-actions">
      <button
        class="btn-secondary danger"
        @click="$emit('restore')"
        :disabled="isLoading"
        title="恢复默认设置"
      >
        <span>恢复默认</span>
      </button>
      <button
        class="btn-secondary"
        @click="$emit('load')"
        :disabled="isLoading"
        title="重新加载配置"
      >
        <span>重新加载</span>
      </button>
      <button
        class="btn-primary"
        @click="$emit('save')"
        :disabled="isLoading || !hasChanges"
      >
        <span v-if="isLoading" class="spinner"></span>
        <span v-else>保存更改</span>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  isLoading: boolean;
  hasChanges: boolean;
}>();

defineEmits<{
  (e: "restore"): void;
  (e: "load"): void;
  (e: "save"): void;
}>();
</script>

<style scoped>
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
</style>
