<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay" @click="onClose">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>📄 报告预览</h3>
          <button @click="onClose" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <iframe
            v-if="iframeSrc"
            :src="iframeSrc"
            class="preview-iframe"
            sandbox="allow-same-origin allow-scripts"
            title="报告预览"
          ></iframe>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from "vue";

const props = defineProps<{
  show: boolean;
  content: string;
  onClose: () => void;
}>();

const iframeSrc = ref("");

// Create Blob URL for iframe content
watch(
  () => props.content,
  (newContent) => {
    if (iframeSrc.value) {
      URL.revokeObjectURL(iframeSrc.value);
      iframeSrc.value = "";
    }

    if (newContent) {
      // Inject basic styles for better preview experience
      const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #fff;
          }
          h1, h2, h3, h4, h5, h6 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
            color: #24292e;
          }
          h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
          h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
          p { margin-top: 0; margin-bottom: 16px; }
          code {
            font-family: source-code-pro, Menlo, Monaco, Consolas, "Courier New", monospace;
            padding: 0.2em 0.4em;
            margin: 0;
            font-size: 85%;
            background-color: rgba(27,31,35,0.05);
            border-radius: 3px;
          }
          pre {
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 3px;
          }
          pre code {
            display: inline;
            padding: 0;
            margin: 0;
            overflow: visible;
            line-height: inherit;
            word-wrap: normal;
            background-color: transparent;
            border: 0;
          }
          blockquote {
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
            margin: 0 0 16px 0;
          }
          ul, ol { padding-left: 2em; margin-bottom: 16px; }
          li { margin-bottom: 4px; }
          img { max-width: 100%; box-sizing: border-box; }
          a { color: #0366d6; text-decoration: none; }
          a:hover { text-decoration: underline; }
          table { border-collapse: collapse; width: 100%; margin-bottom: 16px; }
          th, td { border: 1px solid #dfe2e5; padding: 6px 13px; }
          th { background-color: #f6f8fa; font-weight: 600; }
          tr:nth-child(2n) { background-color: #f6f8fa; }
          
          /* Custom scrollbar for webkit */
          ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
          }
          ::-webkit-scrollbar-track {
            background: #f1f1f1; 
          }
          ::-webkit-scrollbar-thumb {
            background: #c1c1c1; 
            border-radius: 4px;
          }
          ::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8; 
          }
        </style>
      </head>
      <body>
        ${newContent}
      </body>
      </html>
    `;

      const blob = new Blob([htmlContent], { type: "text/html" });
      iframeSrc.value = URL.createObjectURL(blob);
    }
  },
  { immediate: true }
);

// Lock body scroll when modal is open
watch(
  () => props.show,
  (isShow) => {
    if (isShow) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
  }
);

// Cleanup
onUnmounted(() => {
  document.body.style.overflow = "";
  if (iframeSrc.value) {
    URL.revokeObjectURL(iframeSrc.value);
  }
});
</script>

<style scoped>
.modal-overlay {
  z-index: 9999 !important;
}

.preview-iframe {
  width: 100%;
  height: 75vh;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background-color: white;
  display: block;
}
</style>
