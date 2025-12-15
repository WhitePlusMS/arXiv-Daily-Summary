<template>
  <div class="ui-container">
    <!-- 页面头部 -->
    <div class="ui-header">
      <h1 class="ui-title">📚 ArXiv推荐系统 - 学术分类</h1>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="ui-alert-error">
      {{ error }}
    </div>

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <!-- 统计卡片 -->
      <div class="ui-card" v-if="categories.length">
        <h2 class="ui-subheader">📈 分类概览</h2>
        <div class="stats-card">
          <div class="stat-item">
            <div class="stat-value">{{ totalMain }}</div>
            <div class="stat-label">主要学术领域</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value green">{{ totalSub }}</div>
            <div class="stat-label">具体研究方向</div>
          </div>
        </div>
      </div>

      <!-- 搜索框 -->
      <div class="ui-card">
        <h2 class="ui-subheader">🔎 分类搜索</h2>
        <div class="ui-input-container">
          <label>输入关键词（ID/名称/描述，支持中英文）：</label>
          <input
            type="text"
            v-model="keyword"
            placeholder="例如：cs.AI、人工智能、quantum"
            class="ui-input"
          />
          <div class="ui-help">支持在分类ID、英文/中文名称、英文/中文描述中搜索</div>
        </div>
      </div>
    </div>

    <!-- 分类区域 -->
    <div class="ui-card" v-if="filteredCategories.length">
      <h2 class="ui-subheader">📁 学术领域</h2>
      <div class="category-section" v-for="cat in filteredCategories" :key="cat.main_category">
        <div
          class="ui-expander-header"
          :class="{ expanded: expanded.has(cat.main_category) }"
          @click="toggle(cat.main_category)"
        >
          <span class="ui-expander-icon">{{ expanded.has(cat.main_category) ? "▼" : "▶" }}</span>
          📁 <strong>{{ cat.main_category }}</strong
          >（{{ cat.subcategories.length }} 个研究方向）
        </div>
        <div v-if="expanded.has(cat.main_category)" class="ui-expander-content">
          <div class="main-desc">
            该领域包含 {{ cat.subcategories.length }} 个具体研究方向，涵盖相关学科的主要研究领域。
          </div>
          <div class="sub-list">
            <div class="sub-card" v-for="sub in cat.subcategories" :key="sub.id">
              <div class="sub-header">
                <div class="sub-id">{{ sub.id }}</div>
                <div class="sub-title">
                  {{ sub.name }} <span v-if="sub.name_cn">（{{ sub.name_cn }}）</span>
                </div>
              </div>
              <div class="sub-desc">{{ sub.description }}</div>
              <div class="sub-desc-cn" v-if="sub.description_cn">{{ sub.description_cn }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 使用指南 -->
    <div class="ui-card">
      <div class="guide-card">
        <h3>💡 使用指南</h3>
        <p>
          点击上方的 📁 展开按钮查看每个学术领域的详细分类信息。支持使用浏览器的
          <kbd>Ctrl+F</kbd> 或
          <kbd>Cmd+F</kbd> 进行页面内搜索，快速定位你感兴趣的研究方向。<br /><br />
          原文详见
          <a href="https://arxiv.org/category_taxonomy" target="_blank"
            >https://arxiv.org/category_taxonomy</a
          >
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/arxiv";
import * as api from "@/services/api";

const store = useArxivStore();
const { error } = storeToRefs(store);

interface Subcategory {
  id: string;
  name: string;
  description?: string;
  name_cn?: string;
  description_cn?: string;
}

interface Category {
  main_category: string;
  subcategories: Subcategory[];
}

const categories = ref<Category[]>([]);
const keyword = ref("");
const expanded = ref<Set<string>>(new Set());

const totalMain = computed(() => categories.value.length);
const totalSub = computed(() =>
  categories.value.reduce((sum, c) => sum + (c.subcategories?.length || 0), 0)
);

const filteredCategories = computed<Category[]>(() => {
  const kw = keyword.value.trim().toLowerCase();
  if (!kw) return categories.value;
  // 过滤：主分类保留含有匹配子分类的
  return categories.value
    .map((cat) => ({
      ...cat,
      subcategories: (cat.subcategories || []).filter((sub: Subcategory) => {
        const fields = [
          sub.id,
          sub.name,
          sub.description ?? "",
          sub.name_cn ?? "",
          sub.description_cn ?? "",
        ];
        return fields.some((f) => String(f).toLowerCase().includes(kw));
      }),
    }))
    .filter((cat) => cat.subcategories.length > 0);
});

const toggle = (main: string) => {
  const s = new Set(expanded.value);
  if (s.has(main)) s.delete(main);
  else s.add(main);
  expanded.value = s;
};

onMounted(async () => {
  store.setLoading(true);
  store.clearError();
  try {
    const res = await api.getCategories();
    if (res.success && res.data) {
      categories.value = res.data;
    } else {
      store.setError(res.message || "加载分类数据失败");
    }
  } catch (e) {
    store.setError("加载分类数据时发生错误");
    console.error("分类数据加载错误:", e);
  } finally {
    store.setLoading(false);
  }
});
</script>

<style scoped>
/* =====================
   Category Browser Styles
   ===================== */
.stats-card {
  background: linear-gradient(135deg, var(--color-background-soft), var(--color-background-mute));
  padding: 24px;
  border-radius: 20px;
  margin: 8px 0 16px 0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  text-align: center;
  gap: 32px;
  width: 100%;
  box-sizing: border-box;
}

.stat-item {
  flex: 1;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-info);
  margin-bottom: 8px;
}

.stat-value.green {
  color: var(--color-success);
}

.stat-value.red {
  color: var(--color-error);
}

.stat-label {
  color: var(--color-text-soft);
  font-size: var(--font-size-base-rem);
  font-weight: 500;
}

.stat-divider {
  width: 1px;
  background: var(--color-border);
}

.category-section {
  margin-bottom: 16px;
}

.main-desc {
  background: var(--color-background-soft);
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 12px;
  color: var(--color-text-soft);
}

.sub-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sub-card {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.sub-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.sub-id {
  background: var(--color-info-bg);
  color: var(--color-info);
  padding: 6px 12px;
  border-radius: 8px;
  font-family: var(--font-family-mono);
  font-size: var(--font-size-base-rem);
  font-weight: 700;
  min-width: 70px;
  text-align: center;
}

.sub-title {
  font-weight: 700;
  color: var(--color-heading);
  font-size: var(--font-size-md);
}

.sub-desc {
  color: var(--color-text);
  line-height: 1.6;
  font-size: var(--font-size-base-rem);
}

.sub-desc-cn {
  color: var(--color-text-soft);
  line-height: 1.6;
  font-size: var(--font-size-base-rem);
  margin-top: 6px;
  border-top: 1px solid var(--color-border);
  padding-top: 6px;
}

.guide-card {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  padding: 16px;
  border-radius: var(--ui-radius);
}

.guide-card h3 {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-heading);
  margin: 0 0 12px 0;
}

.guide-card p {
  color: var(--color-text);
  font-size: var(--font-size-base-rem);
  line-height: 1.6;
  margin: 0;
}

.guide-card a {
  color: var(--color-primary);
  text-decoration: none;
}

.guide-card a:hover {
  text-decoration: underline;
}

.guide-card kbd {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 2px 6px;
  font-family: var(--font-family-mono);
  font-size: var(--font-size-xs);
  color: var(--color-text);
}

.guide-card .sub-desc {
  color: var(--color-text);
  font-size: var(--font-size-sm);
  line-height: 1.6;
  margin: 0;
}

.expander-icon {
  font-weight: 600;
  color: var(--color-text);
  font-size: var(--font-size-sm);
  transition: transform 0.2s;
}

.footer-content {
  color: var(--color-text-soft);
  text-align: center;
}
</style>
