<template>
  <transition name="fade">
    <div v-if="message.text" class="toast-message" :class="message.type">
      {{ message.text }}
    </div>
  </transition>
</template>

<script setup lang="ts">
defineProps<{
  message: {
    text: string;
    type: "success" | "error";
  };
}>();
</script>

<style scoped>
.toast-message {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 8px;
}

.toast-message.success {
  background-color: var(--color-success);
}

.toast-message.error {
  background-color: var(--color-error);
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
