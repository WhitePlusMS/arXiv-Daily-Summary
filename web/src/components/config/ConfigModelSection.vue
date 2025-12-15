<template>
  <div class="form-container">
    <div class="form-card">
      <h3 class="card-title">DashScope (通义千问) 设置</h3>
      <div class="form-group">
        <label>API Key <span class="required">*</span></label>
        <div class="input-wrapper">
          <input
            :type="showDashscopeKey ? 'text' : 'password'"
            v-model="config.DASHSCOPE_API_KEY"
            placeholder="sk-..."
          />
          <button class="icon-btn" @click="showDashscopeKey = !showDashscopeKey">
            {{ showDashscopeKey ? "👁️" : "🔒" }}
          </button>
        </div>
        <p class="help-text">用于访问通义千问服务的密钥。</p>
      </div>
      <div class="form-group">
        <label>Base URL</label>
        <input type="text" v-model="config.DASHSCOPE_BASE_URL" placeholder="默认地址" />
      </div>
    </div>

    <div class="form-card">
      <h3 class="card-title">分类匹配模型 (Light Model)</h3>
      <div class="form-group">
        <label>模型提供方</label>
        <select v-model="config.LIGHT_MODEL_PROVIDER">
          <option value="dashscope">dashscope</option>
        </select>
      </div>
      <template v-if="config.LIGHT_MODEL_PROVIDER === 'dashscope'">
        <div class="form-row">
          <div class="form-group">
            <label>模型名称</label>
            <input type="text" v-model="config.QWEN_MODEL_LIGHT" />
          </div>
          <div class="form-group">
            <label>Max Tokens</label>
            <input type="number" v-model="config.QWEN_MODEL_LIGHT_MAX_TOKENS" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Temperature (只读)</label>
            <input
              type="number"
              v-model="config.QWEN_MODEL_LIGHT_TEMPERATURE"
              disabled
              class="disabled-input"
            />
          </div>
          <div class="form-group">
            <label>Top P</label>
            <input type="number" step="0.05" v-model="config.QWEN_MODEL_LIGHT_TOP_P" />
          </div>
        </div>
      </template>
    </div>

    <div class="form-card">
      <h3 class="card-title">深度分析模型 (Heavy Model)</h3>
      <div class="form-group">
        <label>模型提供方</label>
        <select v-model="config.HEAVY_MODEL_PROVIDER">
          <option value="dashscope">dashscope</option>
        </select>
      </div>
      <template v-if="config.HEAVY_MODEL_PROVIDER === 'dashscope'">
        <div class="form-row">
          <div class="form-group">
            <label>模型名称</label>
            <input type="text" v-model="config.QWEN_MODEL" />
          </div>
          <div class="form-group">
            <label>Max Tokens</label>
            <input type="number" v-model="config.QWEN_MODEL_MAX_TOKENS" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Temperature</label>
            <input type="number" step="0.1" v-model="config.QWEN_MODEL_TEMPERATURE" />
          </div>
          <div class="form-group">
            <label>Top P</label>
            <input type="number" step="0.05" v-model="config.QWEN_MODEL_TOP_P" />
          </div>
        </div>
      </template>
    </div>

    <div class="form-card">
      <h3 class="card-title">并发设置</h3>
      <div class="form-group">
        <label>最大工作线程数 (MAX_WORKERS)</label>
        <input type="number" v-model="config.MAX_WORKERS" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { ConfigData } from "@/types";

// Config model
const config = defineModel<ConfigData>("config", { required: true });

const showDashscopeKey = ref(false);
</script>
