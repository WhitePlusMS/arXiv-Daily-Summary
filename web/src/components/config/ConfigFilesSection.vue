<template>
  <div class="form-container">
    <div class="form-card">
      <h3 class="card-title">输出设置</h3>
      <div class="form-group checkbox-group">
        <label class="switch">
          <input
            type="checkbox"
            v-model="config.SAVE_MARKDOWN"
            true-value="true"
            false-value="false"
          />
          <span class="slider round"></span>
        </label>
        <span class="label-text">保存 Markdown 文件</span>
      </div>
      <p class="help-text">除了生成 HTML 报告外，是否同时保存 Markdown 格式的源文件。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ConfigData } from "@/types";

// Config model
const config = defineModel<ConfigData>("config", { required: true });
</script>
