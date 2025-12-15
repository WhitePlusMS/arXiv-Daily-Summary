<template>
  <div class="ui-form-container">
    <div class="ui-card">
      <h3 class="ui-card-title">输出设置</h3>
      <div class="ui-form-group ui-checkbox-group">
        <label class="ui-switch">
          <input
            type="checkbox"
            v-model="config.SAVE_MARKDOWN"
            true-value="true"
            false-value="false"
          />
          <span class="ui-switch-slider round"></span>
        </label>
        <span class="label-text">保存 Markdown 文件</span>
      </div>
      <p class="ui-help-text">除了生成 HTML 报告外，是否同时保存 Markdown 格式的源文件。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ConfigData } from "@/types";

// Config model
const config = defineModel<ConfigData>("config", { required: true });
</script>
