<template>
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
            heavyProviderLabel && heavyProviderLabel !== 'Unknown' ? 'status-ok' : 'status-err'
          "
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  hasDashscopeKey: boolean;
  emailEnabled: boolean;
  debugEnabled: boolean;
  heavyProviderLabel: string;
}>();
</script>
<style scoped>
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
  background: var(--color-background);
  padding: 24px;
  border-radius: var(--ui-radius-lg);
  border: 1px solid var(--color-border);
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
  border-color: var(--color-primary-border);
}

.stat-icon {
  font-size: 2rem;
  background: linear-gradient(135deg, var(--color-background-soft), var(--color-background));
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-soft);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
}

.stat-status {
  position: absolute;
  top: 0;
  right: 0;
  width: 4px;
  height: 100%;
  background: var(--color-border);
  opacity: 0.5;
}

.stat-status.status-ok {
  background: var(--color-success);
  opacity: 1;
}
.stat-status.status-err {
  background: var(--color-error);
  opacity: 1;
}
.stat-status.status-warn {
  background: var(--color-warning);
  opacity: 1;
}

.stat-card.active .stat-value {
  color: var(--color-primary);
}
</style>
