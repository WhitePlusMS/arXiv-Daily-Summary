<template>
  <div class="streamlit-section">
    <h2 class="streamlit-subheader">📝 输入研究信息</h2>
    <div class="streamlit-text-input">
      <label>用户名</label>
      <input
        type="text"
        v-model="modelValue.username"
        :disabled="isMatching"
        class="streamlit-input"
        placeholder="请输入您的用户名"
      />
    </div>

    <div v-if="isMatching" class="streamlit-warning">
      ⚠️ 正在进行分类匹配，请等待完成后再修改输入内容
    </div>

    <div style="display: flex; gap: 16px; margin-bottom: 16px">
      <div class="streamlit-text-area" style="flex: 1">
        <label>研究内容描述（感兴趣的方向）</label>
        <textarea
          v-model="modelValue.researchDescription"
          :disabled="isMatching || isOptimizing"
          class="streamlit-textarea"
          placeholder="请详细描述您的研究方向和兴趣领域…"
        ></textarea>
        <div class="streamlit-help">支持Markdown格式，请尽可能详细地描述您的研究方向</div>
      </div>

      <div class="streamlit-text-area" style="flex: 1">
        <label>不感兴趣的方向（可选）</label>
        <textarea
          v-model="modelValue.negativeDescription"
          :disabled="isMatching || isOptimizing"
          class="streamlit-textarea"
          placeholder="请描述您不感兴趣或希望排除的研究方向…"
        ></textarea>
        <div class="streamlit-help">支持Markdown格式，描述您希望排除的研究领域或主题</div>
      </div>
    </div>

    <div class="form-actions">
      <div class="action-buttons">
        <button
          class="streamlit-button"
          :disabled="isMatching || isOptimizing || !modelValue.researchDescription.trim()"
          @click="$emit('optimize')"
        >
          {{ isOptimizing ? "正在优化中…" : "✨ AI优化描述（感兴趣方向）" }}
        </button>
      </div>

      <div class="match-config">
        <div class="streamlit-text-input">
          <label>返回结果数量</label>
          <input
            type="number"
            min="1"
            max="10"
            v-model.number="modelValue.topN"
            class="streamlit-input"
            style="width: 100px"
          />
        </div>
        <button
          class="streamlit-button streamlit-button-primary"
          :disabled="
            isMatching || !modelValue.username.trim() || !modelValue.researchDescription.trim()
          "
          @click="$emit('match')"
        >
          {{ isMatching ? "正在匹配中…" : "🔍 开始匹配分类" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: {
    username: string;
    researchDescription: string;
    negativeDescription: string;
    topN: number;
  };
  isMatching: boolean;
  isOptimizing: boolean;
}>();

defineEmits<{
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (e: "update:modelValue", value: any): void;
  (e: "optimize"): void;
  (e: "match"): void;
}>();
</script>
