<template>
  <div class="unsaved-wrapper">
    <!-- 未保存更改横幅 -->
    <transition name="slide-down">
      <div v-if="changedKeys.length > 0" class="unsaved-banner">
        <div class="banner-content">
          <span class="icon">⚠️</span>
          <span>
            您有 <strong>{{ changedKeys.length }}</strong> 项未保存的更改
          </span>
        </div>
        <div class="banner-actions">
          <button class="ui-button ui-button-text" @click="toggleChanges">
            {{ showChanges ? "收起详情" : "查看详情" }}
          </button>
          <button class="ui-button ui-button-text" @click="$emit('reset')">放弃更改</button>
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
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { ConfigData } from "@/types";

defineProps<{
  changedKeys: string[];
  loadedConfig: ConfigData;
  configChanges: ConfigData;
}>();

defineEmits<{
  (e: "reset"): void;
}>();

const showChanges = ref(false);

const toggleChanges = () => {
  showChanges.value = !showChanges.value;
};

const truncate = (val: unknown) => {
  const s = String(val);
  return s.length > 20 ? s.substring(0, 20) + "..." : s;
};
</script>

<style scoped>
.unsaved-wrapper {
  position: relative;
  z-index: 5;
}

.unsaved-banner {
  background-color: var(--color-warning-bg);
  border-bottom: 1px solid var(--color-warning-border);
  padding: 16px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 6px -1px rgba(217, 119, 6, 0.1);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 16px;
  color: var(--color-warning);
  font-size: 0.95rem;
  font-weight: 500;
}

.banner-actions {
  display: flex;
  gap: 12px;
}

.changes-panel {
  background: var(--color-background);
  border-bottom: 1px solid var(--color-border);
  padding: 24px 32px;
  max-height: 300px;
  overflow-y: auto;
  box-shadow: inset 0 -4px 6px -4px rgba(0, 0, 0, 0.05);
}

.changes-list {
  display: flex;
  flex-direction: column;
}

.change-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
}

.change-item:last-child {
  border-bottom: none;
}

.change-key {
  font-family: "Fira Code", "Menlo", monospace;
  font-size: 0.85rem;
  font-weight: 600;
  width: 260px;
  color: var(--color-text);
}

.change-values {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 20px;
  color: var(--color-text-soft);
  font-size: 0.9rem;
}

.val-old {
  color: var(--color-error);
  text-decoration: line-through;
  opacity: 0.7;
}

.arrow {
  color: var(--color-text-soft);
  font-weight: bold;
}

.val-new {
  color: var(--color-success);
  font-weight: 600;
}

/* Animations */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
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
</style>
