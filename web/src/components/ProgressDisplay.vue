<template>
  <div class="progress-display">
    <!-- 标题 -->
    <div class="progress-header">
      <h3 class="progress-title">{{ title }}</h3>
      <span v-if="progress" class="progress-status" :class="`status-${progress.status}`">
        {{ getStatusText(progress.status) }}
      </span>
    </div>

    <!-- 当前步骤 -->
    <div v-if="progress" class="progress-step">
      <div class="step-text">{{ progress.step }}</div>
    </div>

    <!-- 进度条 -->
    <div v-if="progress" class="progress-bar-container">
      <div class="progress-bar">
        <div
          class="progress-bar-fill"
          :style="{ width: progress.percentage + '%' }"
          :class="{ 'progress-error': progress.status === 'failed' }"
        ></div>
      </div>
      <div class="progress-percentage">{{ progress.percentage }}%</div>
    </div>

    <!-- 错误信息 -->
    <div v-if="progress && progress.error" class="progress-error-message">
      <strong>错误：</strong>{{ progress.error }}
    </div>

    <!-- 日志流 -->
    <div v-if="showLogs && progress && progress.logs.length > 0" class="progress-logs">
      <div class="logs-header">
        <span class="logs-title">📋 日志信息</span>
        <button class="logs-toggle" @click="toggleLogsExpanded">
          {{ logsExpanded ? "收起" : "展开" }}
        </button>
      </div>
      <div v-show="logsExpanded" class="logs-content" ref="logsContainer">
        <div
          v-for="(log, index) in displayLogs"
          :key="index"
          class="log-entry"
          :class="`log-level-${log.level}`"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-level">{{ getLevelIcon(log.level) }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import type { ProgressData } from "@/types";

interface Props {
  progress: ProgressData | null;
  title?: string;
  showLogs?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: "任务进度",
  showLogs: true,
});

const logsExpanded = ref(true);
const logsContainer = ref<HTMLElement | null>(null);

// 显示所有日志（不截断）
const displayLogs = computed(() => {
  if (!props.progress || !props.progress.logs) return [];
  return props.progress.logs;
});

// 获取状态文本
const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    running: "运行中",
    completed: "已完成",
    failed: "失败",
  };
  return statusMap[status] || status;
};

// 获取日志级别图标
const getLevelIcon = (level: string): string => {
  const iconMap: Record<string, string> = {
    info: "ℹ️",
    warning: "⚠️",
    error: "❌",
    success: "✅",
    debug: "🔍",
  };
  return iconMap[level] || "•";
};

// 格式化时间
const formatTime = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return timestamp;
  }
};

// 切换日志展开/收起
const toggleLogsExpanded = () => {
  logsExpanded.value = !logsExpanded.value;
};

// 自动滚动到最新日志
watch(
  () => props.progress?.logs,
  async () => {
    if (logsExpanded.value && logsContainer.value) {
      await nextTick();
      logsContainer.value.scrollTop = logsContainer.value.scrollHeight;
    }
  },
  { deep: true }
);
</script>

<style scoped>
.progress-display {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--ui-radius);
  padding: 20px;
  margin: 16px 0;
  box-shadow: var(--shadow-sm);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.progress-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-heading);
}

.progress-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

.status-running {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.status-completed {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-failed {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.progress-step {
  margin-bottom: 12px;
}

.step-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-soft);
  font-weight: 500;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--color-background-mute);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--color-info);
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-bar-fill.progress-error {
  background: var(--color-error);
}

.progress-percentage {
  min-width: 45px;
  text-align: right;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-info);
}

.progress-error-message {
  padding: 12px;
  background: var(--color-error-bg);
  border-left: 4px solid var(--color-error);
  border-radius: 4px;
  margin-bottom: 16px;
  color: var(--color-error);
  font-size: var(--font-size-sm);
}

.progress-logs {
  border-top: 1px solid var(--color-border);
  padding-top: 16px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.logs-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-heading);
}

.logs-toggle {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 4px 12px;
  cursor: pointer;
  font-size: var(--font-size-xs);
  color: var(--color-text-soft);
  transition: all 0.2s;
}

.logs-toggle:hover {
  background: var(--color-background-soft);
  border-color: var(--color-border-hover);
}

.logs-content {
  max-height: 300px;
  overflow-y: auto;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 12px;
  font-family: var(--font-family-mono);
}

.log-entry {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  font-size: var(--font-size-sm);
  line-height: 1.4;
}

.log-time {
  color: var(--color-text-soft);
  min-width: 70px;
}

.log-level {
  min-width: 20px;
}

.log-message {
  color: var(--color-text);
  flex: 1;
  word-break: break-word;
}

.log-level-error .log-message {
  color: var(--color-error);
}

.log-level-warning .log-message {
  color: var(--color-warning);
}

.log-level-success .log-message {
  color: var(--color-success);
}

.log-level-info .log-message {
  color: var(--color-info);
}

/* 滚动条样式 */
.logs-content::-webkit-scrollbar {
  width: 8px;
}

.logs-content::-webkit-scrollbar-track {
  background: var(--color-background-mute);
  border-radius: 4px;
}

.logs-content::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 4px;
}

.logs-content::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-soft);
}
</style>
