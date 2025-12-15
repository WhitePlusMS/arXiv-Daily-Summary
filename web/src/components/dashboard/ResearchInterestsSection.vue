<template>
  <div class="streamlit-section">
    <h2 class="streamlit-subheader">🎯 研究兴趣</h2>
    <div style="display: flex; gap: 16px; flex-wrap: wrap">
      <div class="streamlit-text-area" style="flex: 1; min-width: 300px">
        <label>（A）感兴趣的研究方向：</label>
        <textarea
          v-model="interestsText"
          placeholder="输入您感兴趣的研究方向，系统将基于这些方向推荐相关论文"
          :disabled="isLoading"
          class="streamlit-textarea"
        ></textarea>
      </div>
      <div class="streamlit-text-area" style="flex: 1; min-width: 300px">
        <label>（B）不感兴趣的研究方向（可选）：</label>
        <textarea
          v-model="negativeInterestsText"
          placeholder="输入您不太感兴趣的研究方向，系统会降低相关论文的推荐优先级"
          :disabled="isLoading"
          class="streamlit-textarea"
        ></textarea>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useProfile } from "@/composables/useProfile";

const { interestsText, negativeInterestsText, isLoading } = useProfile();
</script>
