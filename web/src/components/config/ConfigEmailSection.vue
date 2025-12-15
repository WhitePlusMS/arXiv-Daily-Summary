<template>
  <div class="form-container">
    <div class="form-card">
      <h3 class="card-title">发送开关</h3>
      <div class="form-group checkbox-group">
        <label class="switch">
          <input
            type="checkbox"
            v-model="config.SEND_EMAIL"
            true-value="true"
            false-value="false"
          />
          <span class="slider round"></span>
        </label>
        <span class="label-text">启用邮件发送</span>
      </div>
    </div>

    <transition name="slide-fade">
      <div v-if="emailEnabled" class="email-settings">
        <div class="form-card">
          <h3 class="card-title">发件人设置</h3>
          <div class="form-row">
            <div class="form-group">
              <label>SMTP 服务器</label>
              <input type="text" v-model="config.SMTP_SERVER" placeholder="smtp.example.com" />
            </div>
            <div class="form-group">
              <label>端口</label>
              <input type="number" v-model="config.SMTP_PORT" placeholder="465" />
            </div>
          </div>
          <div class="form-group">
            <label>发件人邮箱</label>
            <input type="email" v-model="config.SENDER_EMAIL" />
          </div>
          <div class="form-group">
            <label>邮箱密码/授权码</label>
            <div class="input-wrapper">
              <input
                :type="showEmailPassword ? 'text' : 'password'"
                v-model="config.EMAIL_PASSWORD"
              />
              <button class="icon-btn" @click="showEmailPassword = !showEmailPassword">
                {{ showEmailPassword ? "👁️" : "🔒" }}
              </button>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  v-model="config.USE_SSL"
                  true-value="true"
                  false-value="false"
                />
                SSL
              </label>
            </div>
            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  v-model="config.USE_TLS"
                  true-value="true"
                  false-value="false"
                />
                TLS
              </label>
            </div>
          </div>
        </div>

        <div class="form-card">
          <h3 class="card-title">收件人设置</h3>
          <div class="form-group">
            <label>收件人列表 (逗号分隔)</label>
            <input type="text" v-model="config.RECEIVER_EMAIL" />
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { ConfigData } from "@/types";

// Config model
const config = defineModel<ConfigData>("config", { required: true });

defineProps<{
  emailEnabled: boolean;
}>();

const showEmailPassword = ref(false);
</script>

<style scoped>
.email-settings {
  display: flex;
  flex-direction: column;
  gap: 32px;
  margin-top: 32px;
}
</style>
