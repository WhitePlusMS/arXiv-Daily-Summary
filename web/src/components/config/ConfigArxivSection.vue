<template>
  <div class="form-container">
    <div class="form-card">
      <h3 class="card-title">API 请求设置</h3>
      <div class="form-group">
        <label>Base URL (只读)</label>
        <input type="text" v-model="config.ARXIV_BASE_URL" disabled class="disabled-input" />
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>重试次数</label>
          <input type="number" v-model="config.ARXIV_RETRIES" />
        </div>
        <div class="form-group">
          <label>请求间隔 (秒)</label>
          <input type="number" v-model="config.ARXIV_DELAY" />
        </div>
      </div>
    </div>

    <div class="form-card">
      <h3 class="card-title">筛选与生成策略</h3>
      <div class="form-group">
        <label>单次最大拉取数 (MAX_ENTRIES)</label>
        <input type="number" v-model="config.MAX_ENTRIES" />
        <p class="help-text">每次从 ArXiv 获取的论文最大数量，建议不要超过 100。</p>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>详细解读数量</label>
          <input type="number" v-model="config.NUM_DETAILED_PAPERS" />
        </div>
        <div class="form-group">
          <label>简要推荐数量</label>
          <input type="number" v-model="config.NUM_BRIEF_PAPERS" />
        </div>
      </div>
      <div class="form-group">
        <label>相关性阈值 (0-10)</label>
        <div class="range-wrapper">
          <input
            type="range"
            min="0"
            max="10"
            step="1"
            v-model="config.RELEVANCE_FILTER_THRESHOLD"
          />
          <span class="range-value">{{ config.RELEVANCE_FILTER_THRESHOLD }}</span>
        </div>
        <p class="help-text">低于此分数的论文将被自动过滤。推荐值: 6</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ConfigData } from "@/types";

// Config model
const config = defineModel<ConfigData>("config", { required: true });
</script>
