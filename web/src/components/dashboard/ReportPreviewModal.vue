<template>
  <div v-if="show" class="modal-overlay" @click="onClose">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>📄 报告预览</h3>
        <button @click="onClose" class="modal-close">×</button>
      </div>
      <div class="modal-body">
        <div v-html="content" class="preview-content"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean;
  content: string;
  onClose: () => void;
}>();
</script>
