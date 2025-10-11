<template>
  <div class="streamlit-dashboard">
    <!-- 页面头部 -->
    <div class="streamlit-header">
      <h1 class="streamlit-title">📚 ArXiv 学术分类</h1>
      <div class="streamlit-caption">探索完整的 ArXiv 学术分类体系，发现你的研究领域</div>
      <div class="streamlit-divider"></div>
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
      <div class="streamlit-divider"></div>
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
          class="search-input"
        />
        <div class="streamlit-help">支持在分类ID、英文/中文名称、英文/中文描述中搜索</div>
      </div>
      <div class="streamlit-divider"></div>
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

    <!-- 页面底部 -->
    <div class="streamlit-footer">
      <div class="streamlit-divider"></div>
      <div class="footer-content">
        <p>ArXiv 学术分类浏览器 - Vue3 版本</p>
        <p>基于 Streamlit 界面设计 | 作者: WhitePlusMS</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useArxivStore } from "@/stores/counter";
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
.stats-card {
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  padding: 1.5rem;
  border-radius: 20px;
  margin: 0.5rem 0 1rem 0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-around;
  text-align: center;
  gap: 2rem;
  max-width: 800px;
}
.stat-item {
  flex: 1;
}
.stat-value {
  font-size: 2.2rem;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 0.5rem;
}
.stat-value.green {
  color: #059669;
}
.stat-label {
  color: #4b5563;
  font-size: 1.05rem;
  font-weight: 500;
}
.stat-divider {
  width: 1px;
  background: #d1d5db;
}

.category-section {
  margin-bottom: 1rem;
}
.main-desc {
  background: #f8fafc;
  padding: 0.8rem;
  border-radius: 12px;
  margin-bottom: 0.8rem;
  color: #4b5563;
}
.sub-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.sub-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
.sub-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.8rem;
}
.sub-id {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #1e40af;
  padding: 0.4rem 0.8rem;
  border-radius: 8px;
  font-family: "Monaco", "Menlo", monospace;
  font-size: 1rem;
  font-weight: 700;
  min-width: 70px;
  text-align: center;
}
.sub-title {
  font-weight: 700;
  color: #111827;
  font-size: 1.1rem;
}
.sub-desc {
  color: #374151;
  line-height: 1.6;
  font-size: 1.05rem;
}
.sub-desc-cn {
  color: #4b5563;
  line-height: 1.6;
  font-size: 1rem;
  margin-top: 0.4rem;
  border-top: 1px solid #e5e7eb;
  padding-top: 0.4rem;
}

.guide-card {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  padding: 1.2rem;
  border-radius: 16px;
  max-width: 800px;
}

/* 复用部分Streamlit样式 */
.streamlit-header {
  margin-bottom: 0.5rem;
}
.streamlit-title {
  font-size: 2rem;
}
.streamlit-caption {
  color: #4b5563;
}
.streamlit-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 1rem 0;
}
.streamlit-section {
  margin: 1rem 0;
}
.streamlit-subheader {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
}
.streamlit-error {
  background: #fee2e2;
  color: #b91c1c;
  padding: 0.75rem;
  border-radius: 8px;
}
.streamlit-text-area label {
  display: block;
  margin-bottom: 0.5rem;
  color: #374151;
}
.search-input {
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  width: 300px;
}
.search-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}
.streamlit-textarea {
  width: 60%;
  max-width: 500px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}
.streamlit-help {
  color: #6b7280;
  font-size: 0.9rem;
  margin-top: 0.35rem;
}
.streamlit-expander-header {
  cursor: pointer;
  padding: 0.6rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f9fafb;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.streamlit-expander-header.expanded {
  background: #eef2ff;
  border-color: #c7d2fe;
}
.streamlit-expander-content {
  padding: 0.75rem;
}
.expander-icon {
  font-weight: 700;
  color: #374151;
}
.streamlit-footer {
  margin-top: 2rem;
}
.footer-content {
  color: #6b7280;
  text-align: center;
}
</style>
