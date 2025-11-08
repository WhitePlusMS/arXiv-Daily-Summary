<template>
  <div class="streamlit-dashboard">
    <!-- 页面头部 -->
  <div class="streamlit-header">
    <h1 class="streamlit-title">📚 ArXiv 学术分类</h1>
    <div class="streamlit-caption">探索完整的 ArXiv 学术分类体系，发现你的研究领域</div>
  </div>

    <!-- 错误提示 -->
    <div v-if="error" class="streamlit-error">
      {{ error }}
    </div>

    <!-- 统计卡片 -->
    <div class="streamlit-section" v-if="categories.length">
      <h2 class="streamlit-subheader">📈 分类概览</h2>
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
    <div class="streamlit-section">
      <h2 class="streamlit-subheader">🔎 分类搜索</h2>
      <div class="streamlit-text-area">
        <label>输入关键词（ID/名称/描述，支持中英文）：</label>
        <input
          type="text"
          v-model="keyword"
          placeholder="例如：cs.AI、人工智能、quantum"
          class="streamlit-input"
        />
        <div class="streamlit-help">支持在分类ID、英文/中文名称、英文/中文描述中搜索</div>
      </div>
    </div>

    <!-- 分类区域 -->
    <div class="streamlit-section" v-if="filteredCategories.length">
      <h2 class="streamlit-subheader">📁 学术领域</h2>
      <div class="category-section" v-for="cat in filteredCategories" :key="cat.main_category">
        <div
          class="streamlit-expander-header"
          :class="{ expanded: expanded.has(cat.main_category) }"
          @click="toggle(cat.main_category)"
        >
          <span class="expander-icon">{{ expanded.has(cat.main_category) ? "▼" : "▶" }}</span>
          📁 <strong>{{ cat.main_category }}</strong
          >（{{ cat.subcategories.length }} 个研究方向）
        </div>
        <div v-if="expanded.has(cat.main_category)" class="streamlit-expander-content">
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
    <div class="streamlit-section">
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
