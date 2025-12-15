<template>
  <div class="ui-card">
    <h2 class="ui-subheader">👤 用户配置</h2>
    <div class="ui-select-container">
      <label>选择用户配置：</label>
      <select
        v-model="selectedProfileName"
        @change="handleProfileChange"
        :disabled="isLoading"
        class="ui-select"
      >
        <option value="自定义">自定义</option>
        <option v-for="profile in userProfiles" :key="profile.username" :value="profile.username">
          {{ profile.username }}
        </option>
      </select>
    </div>

    <!-- 用户配置成功信息 -->
    <div v-if="selectedProfile && selectedProfileName !== '自定义'" class="ui-alert-success">
      <div class="success-content">
        <strong>✅ 已加载用户 {{ selectedProfileName }} 的配置</strong>
        <br /><br />
        <strong>分类标签</strong>: <code>{{ selectedProfile.category_id || "未设置" }}</code>
        <br /><br />
        <strong>研究兴趣</strong>:
        <pre class="research-interests-code">{{ selectedProfile.user_input || "未设置" }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useProfile } from "@/composables/useProfile";

const { selectedProfileName, userProfiles, selectedProfile, isLoading, handleProfileChange } =
  useProfile();
</script>
