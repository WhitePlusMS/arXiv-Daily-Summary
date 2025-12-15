<template>
  <aside class="config-sidebar">
    <nav class="nav-menu">
      <button
        v-for="s in sections"
        :key="s.id"
        class="nav-item"
        :class="{ active: selectedSection === s.id }"
        @click="$emit('select', s.id)"
      >
        <span class="nav-icon">{{ s.icon }}</span>
        <span class="nav-label">{{ s.label }}</span>
        <span v-if="getSectionChanges(s.id) > 0" class="change-badge">
          {{ getSectionChanges(s.id) }}
        </span>
      </button>
    </nav>
  </aside>
</template>

<script setup lang="ts">
export interface Section {
  id: string;
  label: string;
  icon: string;
}

defineProps<{
  sections: Section[];
  selectedSection: string;
  getSectionChanges: (id: string) => number;
}>();

defineEmits<{
  (e: "select", id: string): void;
}>();
</script>

<style scoped>
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
  overflow-x: hidden;
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
</style>
