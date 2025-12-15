<template>
  <div>
    <!-- 推荐系统区域 -->
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">🚀 运行推荐系统</h2>

      <!-- 主推荐按钮 -->
      <div class="button-group">
        <button
          @click="handleRunMain"
          :disabled="isLoading || isRunning || !hasResearchInterests"
          class="streamlit-button streamlit-button-primary"
        >
          🔍 生成最新推荐报告
        </button>
        <div class="streamlit-help">将优先查询：{{ yesterdayStr }}，若无则：{{ prevStr }}</div>
      </div>
    </div>

    <!-- 高级选项 -->
    <div class="streamlit-section">
      <div
        class="streamlit-expander-header"
        @click="toggleAdvancedOptions"
        :class="{ expanded: showAdvancedOptions }"
      >
        <span class="expander-icon">{{ showAdvancedOptions ? "▼" : "▶" }}</span>
        🔧 高级选项：查询特定日期的报告
      </div>
      <div v-show="showAdvancedOptions" class="streamlit-expander-content">
        <div class="streamlit-markdown">
          <p>💡 <strong>提示：</strong> 如果您需要查看特定日期的论文推荐，可以在这里指定日期。</p>
          <p>⚠️ <strong>注意：</strong> ArXiv通常在周日至周四发布论文，周五和周六不发布新论文。</p>
        </div>

        <div class="streamlit-date-input">
          <label>选择查询日期</label>
          <input type="date" v-model="selectedDate" :max="todayStr" class="streamlit-date" />
          <div class="streamlit-help">选择您想要查询论文的日期</div>
        </div>

        <button
          @click="handleRunSpecificDate"
          :disabled="isLoading || isRunning"
          class="streamlit-button"
        >
          🔍 查询指定日期（{{ selectedDate }}）
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";

const props = defineProps<{
  isRunning: boolean;
}>();

const emit = defineEmits<{
  (e: "runMain"): void;
  (e: "runDate", date: string): void;
}>();

const store = useArxivStore();
const { isLoading, hasResearchInterests } = storeToRefs(store);

const selectedDate = ref("");
const todayStr = ref("");
const yesterdayStr = ref("");
const prevStr = ref("");
const showAdvancedOptions = ref(false);

const updateDates = () => {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const prev = new Date(today);
  prev.setDate(today.getDate() - 2);

  const todayISO = today.toISOString().split("T")[0];
  const yesterdayISO = yesterday.toISOString().split("T")[0];
  const prevISO = prev.toISOString().split("T")[0];

  todayStr.value = todayISO || "";
  yesterdayStr.value = yesterdayISO || "";
  prevStr.value = prevISO || "";
  selectedDate.value = yesterdayStr.value;
};

const toggleAdvancedOptions = () => {
  showAdvancedOptions.value = !showAdvancedOptions.value;
};

const handleRunMain = () => {
  emit("runMain");
};

const handleRunSpecificDate = () => {
  emit("runDate", selectedDate.value);
};

onMounted(() => {
  updateDates();
});
</script>
